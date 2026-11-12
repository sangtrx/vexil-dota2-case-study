#!/usr/bin/env python3
"""Outcome-blind third cohort, after the prior 500+200. One frozen rule."""
from __future__ import annotations
import gzip
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions

N=load_definitions()
BASE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
PREV=Path("/home/ai-agent/.cache/vexil-edge-v2-20261113")
OUT=Path("/home/ai-agent/.cache/vexil-edge-v3-20261113")
OUT.mkdir(parents=True,exist_ok=True)
history=json.loads((BASE/"manifest_metadata.json").read_text())
forward=json.loads((PREV/"forward_holdout_manifest.json").read_text())
before=history+forward
ids_before={int(x["match_id"]) for x in before}
series_before={int(x["series_id"]) for x in before if int(x["series_id"])>0}
end=max(int(x["start_time"]) for x in forward)
pool={}
for path in (BASE/"api-cache").glob("*.json.gz"):
    try:
        with gzip.open(path,"rt",encoding="utf8") as f: payload=json.load(f)
    except (OSError,EOFError,ValueError):continue
    if not isinstance(payload,list):continue
    for rec in payload:
        if not isinstance(rec,dict):continue
        try:
            mid=int(rec["match_id"])
            start=int(rec["start_time"])
            sid=int(rec.get("series_id") or 0)
        except (ValueError,KeyError,TypeError):continue
        if mid in ids_before or start<=end or (sid>0 and sid in series_before):
            continue
        pool[mid]={"match_id":mid,"start_time":start,"series_id":sid}
ordered=sorted(pool.values(),key=lambda x:(x["start_time"],x["match_id"]))
assert len(ordered)>=250,"insufficient chronological candidates"
print("THIRD_COHORT_METADATA_CANDIDATES",len(ordered),flush=True)

api=N["OpenDota"](cache_dir=BASE/"api-cache",interval=1.65,max_retries=7)
selected=[]
excluded=Counter()
for rec in ordered:
    match=api.get("/matches/"+str(rec["match_id"]))
    if not N["usable"](match):
        excluded["unparsed_or_short"]+=1
        continue
    if str(match.get("patch"))!="60":
        excluded["different_patch"]+=1
        continue
    sid=int(match.get("series_id") or 0)
    if sid>0 and sid in series_before:
        excluded["earlier_series_overlap"]+=1
        continue
    if sid>0 and rec["series_id"]>0 and sid!=rec["series_id"]:
        raise RuntimeError("inconsistent series metadata")
    if int(match["start_time"])!=rec["start_time"]:
        raise RuntimeError("inconsistent start time")
    selected.append({"match_id":rec["match_id"],"start_time":rec["start_time"],
                     "series_id":sid,"patch":"60","duration":int(match["duration"])})
    if len(selected)%25==0:
        print("THIRD_COHORT_SELECTED",len(selected),"calls",api.calls,
              "cache_hits",api.cache_hits,"excluded",dict(excluded),flush=True)
    if len(selected)==200:break
assert len(selected)==200 and len({x["match_id"] for x in selected})==200
assert all(x["start_time"]>end for x in selected)
assert not {x["series_id"] for x in selected if x["series_id"]>0} & series_before
ids=[x["match_id"] for x in selected]
digest=hashlib.sha256(json.dumps(ids,separators=(",",":")).encode()).hexdigest()
(OUT/"gate_confirmation_manifest.json").write_text(json.dumps(selected,indent=2)+"\n")
receipt={
    "cohort_size":200,"after_start":end,"patch":"60",
    "first_time_utc":datetime.fromtimestamp(selected[0]["start_time"],timezone.utc).isoformat(),
    "last_time_utc":datetime.fromtimestamp(selected[-1]["start_time"],timezone.utc).isoformat(),
    "ordered_id_sha256":digest,"calls":api.calls,"cache_hits":api.cache_hits,
    "excluded_by_reason":dict(excluded),
    "selection":"first 200 eligible parsed patch60 professional games strictly after previous 200, excluding all earlier positive series"
}
(OUT/"gate_confirmation_manifest_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("THIRD_COHORT_FROZEN",json.dumps(receipt,sort_keys=True),flush=True)
