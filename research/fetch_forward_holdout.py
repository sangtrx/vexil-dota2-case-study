#!/usr/bin/env python3
# Finite, outcome-blind external-cohort selection. Protocol was committed at 335abf1.
import gzip
import json
import hashlib
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_notebook_contracts import load_definitions

NS = load_definitions()
BASE = Path("/home/ai-agent/.cache/vexil-real-data-20261113")
OUT = Path("/home/ai-agent/.cache/vexil-edge-v2-20261113")
OUT.mkdir(parents=True, exist_ok=True)

SOURCE_MANIFEST = json.loads((BASE / "manifest_metadata.json").read_text())
ORIGINAL_IDS = {int(m["match_id"]) for m in SOURCE_MANIFEST}
ORIGINAL_SERIES = {int(m["series_id"]) for m in SOURCE_MANIFEST if int(m["series_id"]) > 0}
AFTER_START = max(int(m["start_time"]) for m in SOURCE_MANIFEST)
N_HOLDOUT = 200
TARGET_PATCH = "60"

# We only read proMatches metadata during selection. No labels are inspected
# or used to include/exclude individual records.
rows = {}
for path in (BASE / "api-cache").glob("*.json.gz"):
    try:
        with gzip.open(path, "rt", encoding="utf8") as handle:
            data = json.load(handle)
    except (OSError, EOFError, ValueError):
        continue
    if not isinstance(data, list):
        continue
    for record in data:
        if not isinstance(record, dict):
            continue
        try:
            mid = int(record["match_id"])
            start = int(record["start_time"])
            sid = int(record.get("series_id") or 0)
        except (ValueError, TypeError, KeyError):
            continue
        if mid in ORIGINAL_IDS or start <= AFTER_START or (sid > 0 and sid in ORIGINAL_SERIES):
            continue
        rows[mid] = dict(match_id=mid, start_time=start, series_id=sid)
pool = sorted(rows.values(), key=lambda m: (m["start_time"], m["match_id"]))
if len(pool) < N_HOLDOUT + 50:
    raise RuntimeError("Insufficient proMatches future metadata; refused to change selection rule")
print("FORWARD_COHORT_SEARCH", len(pool), "future candidate IDs", flush=True)

api = NS["OpenDota"](cache_dir=BASE/"api-cache", interval=1.65, max_retries=7)
selected = []
excluded = Counter()
accepted_series = set()

for rank, rec in enumerate(pool):
    match = api.get("/matches/" + str(rec["match_id"]))
    if not NS["usable"](match):
        excluded["unparsed_or_short"] += 1
        continue
    if str(match.get("patch")) != TARGET_PATCH:
        excluded["different_patch"] += 1
        continue
    if int(match.get("start_time") or 0) != rec["start_time"]:
        raise RuntimeError("Metadata and detail start time disagree for match " + str(rec["match_id"]))
    series_id = int(match.get("series_id") or 0)
    if series_id > 0 and series_id in ORIGINAL_SERIES:
        excluded["original_series_overlap"] += 1
        continue
    if series_id > 0 and rec["series_id"] > 0 and series_id != rec["series_id"]:
        raise RuntimeError("Metadata/detail series mismatch for match "+str(rec["match_id"]))
    selected.append({
        "match_id":rec["match_id"],
        "start_time":rec["start_time"],
        "series_id":series_id,
        "patch":str(match["patch"]),
        "duration":int(match["duration"])
    })
    if len(selected)%25 == 0:
        print("FORWARD_ELIGIBLE_COUNT",len(selected),"api_calls",api.calls,"cache_hits",api.cache_hits,
              "exclusions",dict(excluded),flush=True)
    if len(selected)==N_HOLDOUT:break

if len(selected)!=N_HOLDOUT:
    raise RuntimeError("Only "+str(len(selected))+" usable forward games: no silent resampling")
assert len({x["match_id"] for x in selected})==N_HOLDOUT
assert all(x["patch"]==TARGET_PATCH and x["start_time"]>AFTER_START for x in selected)
assert not {x["match_id"] for x in selected} & ORIGINAL_IDS
assert not {x["series_id"] for x in selected if x["series_id"]>0} & ORIGINAL_SERIES
assert all(selected[i]["start_time"]<=selected[i+1]["start_time"] for i in range(N_HOLDOUT-1))
ids=[x["match_id"] for x in selected]
digest=hashlib.sha256(json.dumps(ids,separators=(",",":")).encode()).hexdigest()
manifest=OUT/"forward_holdout_manifest.json"
receipt=OUT/"forward_holdout_receipt.json"
manifest.write_text(json.dumps(selected,indent=2)+"\n")
receipt.write_text(json.dumps({
    "cohort_size":N_HOLDOUT,"patch":TARGET_PATCH,
    "after_original_last_start":AFTER_START,
    "first_start":selected[0]["start_time"],"last_start":selected[-1]["start_time"],
    "first_time_utc":datetime.fromtimestamp(selected[0]["start_time"],timezone.utc).isoformat(),
    "last_time_utc":datetime.fromtimestamp(selected[-1]["start_time"],timezone.utc).isoformat(),
    "ordered_id_sha256":digest,"api_calls":api.calls,"cache_hits":api.cache_hits,
    "excluded_by_reason":dict(excluded),
    "selection_rule":"first 200 parsed patch-60 proMatches strictly after original 500 max start, no original series overlap, no label selection",
},sort_keys=True,indent=2)+"\n")
print("FORWARD_HOLDOUT_IDS_FROZEN",digest,"api_calls",api.calls,
      "excluded",dict(excluded),flush=True)
