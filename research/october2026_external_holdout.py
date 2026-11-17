#!/usr/bin/env python3
"""Locked historical October 2026 external holdout, assessed 17 Nov 2026.

Discover -> commit sanitized listing -> collect -> score. Use only two Vexil
permitted endpoints. Do not fit, tune, replace notebook, or promote any model.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from research.posttest_temporal import collect_and_score as frozen

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/OCTOBER_2026_EXTERNAL_HOLDOUT_PROTOCOL.md"
LISTING = ROOT / "docs/OCTOBER_2026_EXTERNAL_LISTING.json"
PAGE_DIR = ROOT / "research/october2026_pro_match_pages"
LOWER = int(dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc).timestamp())
UPPER = int(dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc).timestamp())
MAX_PAGES = 20
MAX_DETAILS = 180
SEED = 20261117
BOOTSTRAPS = 10000
FINGERPRINTS = {
    "M0": "c7ca7c9fa28cfee258f37bc482f23f8d1d4e7b8df30f7c2dcb20384a2d4f9558",
    "M1": "33c458955f3fe512b985c3d983c9349a433c97bd44b769d8897a7cc15f21d91a",
}


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def unique_old_ids_and_series() -> tuple[set[int], set[int]]:
    import csv
    mids: set[int] = set()
    series: set[int] = set()
    for rel in (
        "research/frozen_original_split_manifest.csv",
        "artifacts/forward_100_metadata.csv",
        "research/november_120_candidate_manifest.csv",
    ):
        with (ROOT / rel).open(newline="") as stream:
            for row in csv.DictReader(stream):
                mids.add(int(row["match_id"]))
                sid = int(row.get("series_id") or 0)
                if sid > 0:
                    series.add(sid)
    assert len(mids) == 652, "Prior 500+100+120 cohort union changed"
    return mids, series


def selection_from_pages(pages: list[list[dict]]) -> tuple[list[dict], dict]:
    """Identity and date only. Do NOT access radiant_win or winner-related keys."""
    old_ids, old_series = unique_old_ids_and_series()
    seen: set[int] = set()
    filtered: list[dict] = []
    counts: collections.Counter[str] = collections.Counter()
    last_mid: int | None = None
    for page in pages:
        for row in page:
            if not isinstance(row, dict) or type(row.get("match_id")) is not int:
                raise ValueError("Invalid /proMatches identity")
            mid = row["match_id"]
            if mid in seen or (last_mid is not None and mid >= last_mid):
                raise ValueError("Non-descending or duplicate proMatches cursor")
            last_mid = mid
            seen.add(mid)
            start = row.get("start_time")
            if type(start) is not int:
                counts["missing_start"] += 1
                continue
            if not LOWER <= start < UPPER:
                counts["outside_window"] += 1
                continue
            sid = row.get("series_id")
            if sid is None:
                sid = 0
            if type(sid) is not int:
                counts["bad_series_id"] += 1
                continue
            if mid in old_ids or (sid > 0 and sid in old_series):
                counts["historical_overlap"] += 1
                continue
            filtered.append({"match_id": mid, "start_time": start, "series_id": sid})
    if len(filtered) > MAX_DETAILS:
        counts["beyond_fixed_detail_cap"] = len(filtered) - MAX_DETAILS
        filtered = filtered[:MAX_DETAILS]
    return filtered, dict(counts)


def discover() -> None:
    if LISTING.exists() or PAGE_DIR.exists():
        raise FileExistsError("Discovery was already frozen, refuse overwrite")
    if not PROTOCOL.is_file():
        raise FileNotFoundError("Predeclared science protocol missing")
    PAGE_DIR.mkdir(parents=True)
    pages: list[list[dict]] = []
    receipts = []
    cursor: int | None = None
    session = requests.Session()
    session.headers["User-Agent"] = "vexil-scientific-external-holdout/1.0"
    try:
        for page_idx in range(1, MAX_PAGES + 1):
            params = {} if cursor is None else {"less_than_match_id": cursor}
            url = "https://api.opendota.com/api/proMatches"
            r = session.get(url, params=params, timeout=(8, 35))
            if r.status_code == 429:
                raise RuntimeError("HTTP 429 during discovery. STOP; no silent page skips")
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                raise ValueError("Expected a list from /proMatches")
            raw = canonical(data)
            zipped = gzip.compress(raw, compresslevel=6, mtime=0)
            rel = f"page_{page_idx:02d}.json.gz"
            (PAGE_DIR / rel).write_bytes(zipped)
            pages.append(data)
            starts = [int(z["start_time"]) for z in data if type(z.get("start_time")) is int]
            ids = [z["match_id"] for z in data]
            receipts.append({"page": page_idx, "entries": len(data),
                             "first_id": ids[0] if ids else None,
                             "last_id": ids[-1] if ids else None,
                             "canonical_sha256": sha(raw), "archive_sha256": sha(zipped),
                             "archive": f"research/october2026_pro_match_pages/{rel}"})
            print("DISCOVERY_PAGE", page_idx, "ITEMS", len(data),
                  "START_GT_LOWER", sum(x >= LOWER for x in starts), flush=True)
            if not ids:
                break
            new_cursor = min(ids)
            if cursor is not None and new_cursor >= cursor:
                raise ValueError("Invalid proMatches pagination")
            cursor = new_cursor
            # The sorted pro-match ID cursor is the ordering contract.
            if starts and max(starts) < LOWER:
                break
            if len(data) < 100:
                break
            time.sleep(1.7)
    finally:
        session.close()
    selected, counts = selection_from_pages(pages)
    listing = {
        "protocol_sha256": sha(PROTOCOL.read_bytes()),
        "source_commit_before_discovery": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source": "OpenDota /proMatches, descending match ID",
        "lower_utc_inclusive": "2026-10-01T00:00:00Z",
        "upper_utc_exclusive": "2026-11-01T00:00:00Z",
        "raw_page_receipts": receipts,
        "page_count": len(pages),
        "selection_uses_winner_fields": False,
        "prior_500_100_120_union_game_count": 652,
        "selection_exclusion_counts": counts,
        "candidate_ids_start_times_and_series": selected,
        "detail_candidate_count": len(selected),
        "max_detail_requests": MAX_DETAILS,
        "bootstrap_seed": SEED,
        "bootstrap_draws": BOOTSTRAPS,
        "model_fingerprints": FINGERPRINTS,
        "outcome_scores_viewed_by_selection": False,
    }
    LISTING.write_bytes(json.dumps(listing, indent=2, sort_keys=True).encode() + b"\n")
    print("FROZEN_OCTOBER_LISTING", LISTING, "CANDIDATES", len(selected),
          "SHA", sha(LISTING.read_bytes()), flush=True)


def verify_listing(listing: dict) -> None:
    if listing["protocol_sha256"] != sha(PROTOCOL.read_bytes()):
        raise ValueError("Protocol changed since initial discovery")
    if listing["model_fingerprints"] != FINGERPRINTS:
        raise ValueError("Model identity changed")
    pages = []
    for rec in listing["raw_page_receipts"]:
        path = ROOT / rec["archive"]
        if sha(path.read_bytes()) != rec["archive_sha256"]:
            raise ValueError("Archived /proMatches page changed")
        raw = gzip.decompress(path.read_bytes())
        if sha(raw) != rec["canonical_sha256"]:
            raise ValueError("Pro-match page content changed")
        pages.append(json.loads(raw))
    selected, counts = selection_from_pages(pages)
    if selected != listing["candidate_ids_start_times_and_series"]:
        raise ValueError("Candidate selection differs from frozen pages")
    if counts != listing["selection_exclusion_counts"]:
        raise ValueError("Selection exclusion counts drifted")
    if not listing["detail_candidate_count"]:
        raise ValueError("No eligible-age candidate to inspect")


def eligible_detail(payload: dict, candidate: dict, features: dict) -> str | None:
    """Reuse original Vexil strict clock checks, new fixed window only."""
    if not isinstance(payload, dict):
        return "bad_payload"
    if int(payload.get("series_id") or 0) != int(candidate["series_id"]):
        return "series_mismatch"
    # Original helper encodes the *earlier* 2026-Oct/Nov range in globals.
    # This isolated process switches only eligibility window, never features.
    old_low, old_high = frozen.MIN_START, frozen.MAX_START
    try:
        frozen.MIN_START, frozen.MAX_START = LOWER, UPPER
        return frozen.eligible(payload, candidate["match_id"],
                               candidate["start_time"], features)
    finally:
        frozen.MIN_START, frozen.MAX_START = old_low, old_high


def collect(out: Path) -> None:
    listing = json.loads(LISTING.read_text())
    verify_listing(listing)
    if out.exists():
        raise FileExistsError("Previously collected holdout is immutable")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("Commit the metadata listing BEFORE fetching outcomes")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == listing["source_commit_before_discovery"]:
        raise RuntimeError("No frozen-listing commit exists; STOP")
    features = frozen.frozen_functions()
    out.mkdir(parents=True)
    raw_dir = out / "accepted_raw"
    raw_dir.mkdir()
    accepted: list[dict] = []
    audit: list[dict] = []
    last_call = 0.0
    calls = 0
    session = requests.Session()
    session.headers["User-Agent"] = "vexil-scientific-external-holdout/1.0"
    try:
        for ix, c in enumerate(listing["candidate_ids_start_times_and_series"], 1):
            result, last_call, attempts, err = frozen.get_payload(
                session, int(c["match_id"]), last_call)
            calls += attempts
            reason = err if err is not None else eligible_detail(result, c, features)
            audit.append({"match_id": c["match_id"], "reason": reason or "eligible"})
            if reason is None:
                raw = canonical(result)
                zipped = gzip.compress(raw, compresslevel=6, mtime=0)
                (raw_dir / f'{c["match_id"]}.json.gz').write_bytes(zipped)
                accepted.append({
                    "match_id": int(c["match_id"]),
                    "start_time": int(c["start_time"]),
                    "series_id": int(c["series_id"]),
                    "patch": str(result["patch"]),
                    "duration": int(result["duration"]),
                    "raw_json_sha256": sha(raw),
                    "raw_gzip_sha256": sha(zipped),
                })
            if ix % 15 == 0:
                print("DETAIL", ix, "ACCEPTED", len(accepted),
                      "EXCLUDED", ix-len(accepted), flush=True)
    finally:
        session.close()
        receipt = {
            "frozen_listing_sha256": sha(LISTING.read_bytes()),
            "source_model_fingerprints": FINGERPRINTS,
            "candidate_count": len(listing["candidate_ids_start_times_and_series"]),
            "requested_count": len(audit), "http_attempts": calls,
            "accepted_count": len(accepted), "accepted": accepted,
            "exclusions": dict(collections.Counter(
                x["reason"] for x in audit if x["reason"] != "eligible")),
            "audit": audit,
            "complete": len(audit) == listing["detail_candidate_count"],
            "no_model_fitting_or_scoring_in_collection": True,
        }
        (out / "collection_receipt.json").write_bytes(
            json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n")
        print("COLLECTION", len(accepted), "OF", len(audit),
              "COMPLETE", receipt["complete"], flush=True)
    if len(audit) != listing["detail_candidate_count"]:
        raise RuntimeError("Incomplete frozen cohort - DO NOT SCORE")


def clustered_interval(frame: pd.DataFrame, by: str, metric: str) -> list[float]:
    df = frame.copy()
    if by == "match":
        df["cluster"] = df.match_id.astype(str)
    else:
        df["cluster"] = df.series_id.where(df.series_id > 0, -df.match_id).astype(str)
    df["d"] = df[f"d_{metric}"]
    grouped = df.groupby("cluster").agg(rows=("d", "size"), total=("d", "sum"))
    count = len(grouped)
    rng = np.random.default_rng(SEED)
    ix = rng.integers(0, count, size=(BOOTSTRAPS, count))
    totals = grouped.total.to_numpy()[ix].sum(axis=1)
    sizes = grouped.rows.to_numpy()[ix].sum(axis=1)
    return [float(v) for v in np.quantile(totals/sizes, [0.025, 0.975])]


def score(out: Path) -> None:
    listing = json.loads(LISTING.read_text())
    verify_listing(listing)
    receipt = json.loads((out / "collection_receipt.json").read_text())
    if not receipt["complete"] or receipt["frozen_listing_sha256"] != sha(LISTING.read_bytes()):
        raise ValueError("Unfinished or refrozen external cohort")
    if (out / "score_receipt.json").exists():
        raise FileExistsError("Score already opened; do not overwrite")
    if not receipt["accepted"]:
        raise RuntimeError("No eligible match to score; NO-GO")
    functions = frozen.frozen_functions()
    models, specs, fingerprints = frozen.models_from_frozen_train()
    if fingerprints != FINGERPRINTS:
        raise ValueError("Model coefficients altered since pre-declared plan")
    raw = []
    for row in receipt["accepted"]:
        path = out/"accepted_raw"/f'{row["match_id"]}.json.gz'
        if sha(path.read_bytes()) != row["raw_gzip_sha256"]:
            raise ValueError("Raw payload byte hash mismatch")
        data = gzip.decompress(path.read_bytes())
        if sha(data) != row["raw_json_sha256"]:
            raise ValueError("Raw payload content hash mismatch")
        value = json.loads(data)
        if eligible_detail(value,row,functions) is not None:
            raise ValueError("Payload eligibility changed after collection")
        raw.append(value)
    frame = functions["make_minute_table"](raw)
    metadata = pd.DataFrame([{"match_id":int(m["match_id"]),
       "start_time":int(m["start_time"]),
       "series_id":int(m.get("series_id") or 0),
       "patch":str(m["patch"]), "league_id":int(m.get("leagueid") or m.get("league_id") or 0),
       "radiant_team_id":int(m.get("radiant_team_id") or 0),
       "dire_team_id":int(m.get("dire_team_id") or 0),
       "radiant_win":int(m["radiant_win"])} for m in raw])
    assert frame.match_id.nunique() == len(raw)
    assert not frame.duplicated(["match_id","minute"]).any()
    expected_ids=set(int(z["match_id"]) for z in receipt["accepted"])
    assert set(frame.match_id.unique()) == expected_ids
    for name,model in models.items():
        frame["p_"+name] = model.predict_proba(frame[specs[name]])[:,1]
    joined=frame.merge(metadata[["match_id","series_id"]],on="match_id",
                       validate="many_to_one")
    y=joined.radiant_win.to_numpy(int)
    p0=joined.p_M0.to_numpy(float)
    p1=joined.p_M1.to_numpy(float)
    joined["d_ll"]=frozen.ll(y,p1)-frozen.ll(y,p0)
    joined["d_brier"]=(p1-y)**2-(p0-y)**2
    if not (np.isfinite(joined[["p_M0","p_M1","d_ll","d_brier"]]).to_numpy().all()):
        raise ValueError("Nonfinite probability, loss or delta")
    series_clusters={("s"+str(int(z.series_id)) if z.series_id>0 else "m"+str(int(z.match_id))) for z in metadata.itertuples()}
    inferential = len(raw)>=50 and len(series_clusters)>=30
    phases={}
    for name,lower,upper in [("0-9",0,10),("10-19",10,20),("20-29",20,30),("30+",30,100000)]:
        sub=joined[(joined.minute>=lower)&(joined.minute<upper)]
        if sub.empty:
            phases[name]={"rows":0,"games":0}
            continue
        yy=sub.radiant_win.to_numpy(int)
        pp0=sub.p_M0.to_numpy(float);pp1=sub.p_M1.to_numpy(float)
        phases[name]={"rows":len(sub),"games":int(sub.match_id.nunique()),
            "logloss_M0":float(frozen.ll(yy,pp0).mean()),
            "logloss_M1":float(frozen.ll(yy,pp1).mean()),
            "brier_M0":float(((yy-pp0)**2).mean()),
            "brier_M1":float(((yy-pp1)**2).mean()),
            "ece10_M0":frozen.ece(yy,pp0),
            "ece10_M1":frozen.ece(yy,pp1)}
    delta_ll=float(joined.d_ll.mean())
    delta_brier=float(joined.d_brier.mean())
    losses=joined.groupby("match_id")[["d_ll","d_brier"]].sum()
    influential=int(losses.d_ll.abs().idxmax())
    total=float(losses.d_ll.sum())
    old_ids,old_series=unique_old_ids_and_series()
    assert not (expected_ids & old_ids)
    assert not (set(z for z in metadata.series_id if z>0) & old_series)
    result={
        "status":"EXTERNAL_HOLDOUT_REPORTED_REGARDLESS_OF_DIRECTION",
        "evidence_class":"POST_ORIGINAL_TEST_LOCKED_OCTOBER_HISTORICAL_MATCH_SAMPLE; NOT LIVE RECEIVED_AT",
        "protocol_sha256":listing["protocol_sha256"],
        "listing_sha256":sha(LISTING.read_bytes()),
        "collection_receipt_sha256":sha((out/"collection_receipt.json").read_bytes()),
        "original_500_and_previous_100_overlap":0,
        "dates_utc":[dt.datetime.fromtimestamp(int(metadata.start_time.min()),dt.timezone.utc).isoformat(),
                     dt.datetime.fromtimestamp(int(metadata.start_time.max()),dt.timezone.utc).isoformat()],
        "games":len(raw),"series_or_singleton_clusters":len(series_clusters),
        "minute_rows":len(joined),
        "underpowered_or_descriptive_only":not inferential,
        "source_model_coeff_fingerprints":fingerprints,
        "source_train_sha256":frozen.DATA_SHA,
        "source_notebook_code_sha256":frozen.CODE_SHA,
        "patch_counts":{str(k):int(v) for k,v in metadata.patch.value_counts().items()},
        "league_counts":{str(k):int(v) for k,v in metadata.league_id.value_counts().items()},
        "M0":{"logloss":float(frozen.ll(y,p0).mean()),"brier":float(((y-p0)**2).mean()),"ece10":frozen.ece(y,p0)},
        "M1":{"logloss":float(frozen.ll(y,p1).mean()),"brier":float(((y-p1)**2).mean()),"ece10":frozen.ece(y,p1)},
        "M1_minus_M0":{"logloss":delta_ll,"brier":delta_brier,
              "logloss_ci_95_series":clustered_interval(joined,"series","ll"),
              "logloss_ci_95_match":clustered_interval(joined,"match","ll"),
              "brier_ci_95_series":clustered_interval(joined,"series","brier"),
              "brier_ci_95_match":clustered_interval(joined,"match","brier"),
              "equal_game_mean_logloss_delta":float(joined.groupby("match_id").d_ll.mean().mean()),
              "equal_game_mean_brier_delta":float(joined.groupby("match_id").d_brier.mean().mean())},
        "phase_descriptive":phases,
        "most_influential_game_id":influential,
        "most_influential_ll_abs_share": (abs(float(losses.at[influential,"d_ll"]))/abs(total)) if total else None,
        "no_forward_training":True,
        "no_recalibration":True,
        "no_model_promotion_authorized":True,
        "received_at_unverified":True,
        "original_march_test_predictions_unchanged":True,
        "bootstrap":{"draws":BOOTSTRAPS,"seed":SEED,"groups":"both series/singleton and match","paired":True},
    }
    out.joinpath("score_receipt.json").write_bytes(
         json.dumps(result,indent=2,sort_keys=True).encode()+b"\n")
    joined[["match_id","minute","radiant_win","p_M0","p_M1"]].to_csv(out/"predictions.csv",index=False)
    metadata.to_csv(out/"metadata.csv",index=False)
    print("SCORE_RECEIPT",json.dumps({k:result[k] for k in ("games","minute_rows","underpowered_or_descriptive_only","M0","M1","M1_minus_M0")}),flush=True)
    print("NO MODEL PROMOTION",flush=True)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["discover","collect","score","verify"])
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.action=="discover":
        discover()
    elif args.action=="verify":
        verify_listing(json.loads(LISTING.read_text()))
        print("SOURCE_LISTING_OK",sha(LISTING.read_bytes()))
    elif args.action=="collect":
        if args.out is None:
            parser.error("--out is required for collect")
        collect(args.out)
    elif args.action=="score":
        if args.out is None:
            parser.error("--out is required for score")
        score(args.out)


if __name__=="__main__":
    main()
