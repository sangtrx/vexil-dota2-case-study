"""OpenDota source-drift canary for frozen Vexil matches.

By design this is NOT a new test cohort, model fitting or cloud acceptance.
Fetches only /matches/{id} for a small patch-balanced deterministic subset.
No authentication, no new endpoints and no writes to the notebook input cache.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import pandas as pd
import requests

BASE = "https://api.opendota.com/api"


def _load_features(test_path: Path):
    spec = importlib.util.spec_from_file_location("_vexil_source_contracts", test_path)
    if not spec or not spec.loader:
        raise RuntimeError("Cannot load local source tests")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.N


def _cache_file(path: Path, match_id: int) -> Path:
    key = hashlib.sha256(json.dumps(
        ["/matches/" + str(int(match_id)), {}], sort_keys=True
    ).encode()).hexdigest()
    return path/(key+".json.gz")


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, separators=(",", ":"), sort_keys=True
    ).encode()).hexdigest()


def _equal_number(a, b):
    if isinstance(a, (bool, str, dict, list)) or isinstance(b, (bool, str, dict, list)):
        return a == b
    if a is None or b is None:
        return a is b
    if math.isnan(float(a)) and math.isnan(float(b)):
        return True
    return math.isclose(float(a), float(b), abs_tol=1e-9, rel_tol=0)


def compare_payloads(before: dict, fresh: dict, n: dict) -> dict:
    for field in ("match_id", "start_time", "patch", "duration", "series_id", "radiant_win"):
        if before.get(field) != fresh.get(field):
            raise ValueError("OpenDota match metadata/target drift: "+field)
    for d in (before, fresh):
        n["validate_minute_alignment"](d)
    mismatches = {}
    checked = 0
    cutoff = int(before["duration"])//60
    for t in range(cutoff+1):
        a=n["snapshot_features"](before,t)
        b=n["snapshot_features"](fresh,t)
        for col in n["FEATURE_COLUMNS"]:
            if not _equal_number(a[col], b[col]):
                mismatches[col]=mismatches.get(col,0)+1
        old_item=n["item_purchase_snapshot"](before,t)
        fresh_item=n["item_purchase_snapshot"](fresh,t)
        for i, col in enumerate(n["ITEM_ADDED_COLUMNS"]):
            if not _equal_number(old_item[i],fresh_item[i]):
                mismatches[col]=mismatches.get(col,0)+1
        checked+=1
    return {
        "match_id":int(before["match_id"]), "patch":int(before["patch"]),
        "minute_rows_compared":checked,
        "raw_digest_unchanged":_digest(before)==_digest(fresh),
        "feature_mismatches":mismatches,
        "source_gate_pass":True,
    }


def sample(manifest: pd.DataFrame, per_patch: int=5) -> list[int]:
    patches=sorted(manifest.patch.unique().tolist())
    if len(patches)!=2 or per_patch<1:
        raise ValueError("Expected exactly two patches and at least one canary each")
    ids=[]
    for patch in patches:
        frame=manifest[manifest.patch==patch].sort_values(
            ["start_time","match_id"],kind="stable")
        if len(frame)<per_patch:
            raise ValueError("Not enough patch cohort matches")
        positions=[round(i*(len(frame)-1)/(per_patch-1)) for i in range(per_patch)] if per_patch>1 else [0]
        ids.extend(frame.iloc[positions].match_id.astype(int).tolist())
    if len(set(ids))!=len(ids):
        raise AssertionError("Duplicate canary identity")
    return ids


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--tests-file",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--per-patch",type=int,default=5)
    parser.add_argument("--interval",type=float,default=1.7)
    args=parser.parse_args()
    if not 1<=args.per_patch<=6 or args.interval<1.6:
        raise ValueError("Bound canary size and respect the OpenDota request interval")
    m=pd.read_csv(args.manifest)
    ids=sample(m,args.per_patch)
    n=_load_features(args.tests_file)
    session=requests.Session()
    session.headers.update({"User-Agent":"vexil-research-source-drift-canary/1.0"})
    results=[]
    errors=[]
    t0=time.monotonic()
    for i,mid in enumerate(ids):
        if i:
            time.sleep(args.interval)
        path=_cache_file(args.cache,mid)
        with gzip.open(path,"rt",encoding="utf8") as h:before=json.load(h)
        try:
            response=session.get(BASE+"/matches/"+str(mid),timeout=(8,30))
            if response.status_code!=200:
                raise RuntimeError("OpenDota status "+str(response.status_code))
            data=response.json()
            if not isinstance(data,dict):
                raise ValueError("Non-object OpenDota response")
            receipt=compare_payloads(before,data,n)
            results.append(receipt)
            print("CANARY_MATCH",mid,"patch",receipt["patch"],"minutes",receipt["minute_rows_compared"],
                  "semantic_mismatches",receipt["feature_mismatches"],
                  "raw_same",receipt["raw_digest_unchanged"],flush=True)
        except (requests.RequestException, ValueError, RuntimeError, KeyError, TypeError) as exc:
            errors.append({"match_id":mid,"error_type":type(exc).__name__,
                           "description":str(exc)[:230]})
            print("CANARY_ERROR",mid,type(exc).__name__,str(exc)[:140],flush=True)
            if isinstance(exc,requests.RequestException):
                break
    out={
        "scope":"Small current OpenDota /matches/{id} response check, not full cold run or new blind dataset",
        "elapsed_s":round(time.monotonic()-t0,2),
        "requested":len(ids),"completed":len(results),"errors":errors,
        "total_minute_rows_checked":sum(x["minute_rows_compared"] for x in results),
        "raw_payload_drift_count":sum(not x["raw_digest_unchanged"] for x in results),
        "semantic_mismatch_matches":sum(bool(x["feature_mismatches"]) for x in results),
        "records":results,
        "no_data_cache_written":True,
    }
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("CANARY_SUMMARY",json.dumps({k:v for k,v in out.items() if k!="records"},sort_keys=True),flush=True)
    if len(results)!=len(ids) or errors or any(x["feature_mismatches"] for x in results):
        raise SystemExit(2)


if __name__=="__main__":
    main()
