#!/usr/bin/env python3
"""Recompute historical preterminal vs corrected TEST metrics, without refitting.

Both frozen forecast CSVs are included in the reviewer ZIP for offline audit.
This is post-inspection historical disclosure, not a second blind experiment.
Usage:
  python research/verify_terminal_correction_history.py --write
  python research/verify_terminal_correction_history.py --check
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"research/preterminal_TEST_predictions_3837.csv"
NEW=ROOT/"artifacts/heldout_predictions.csv"
RECEIPT=ROOT/"docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json"
SHA_OLD="e3b2c843172fdde029f5f5ec05536ea837ec023b8b860543cadedf028bb3cb32"
SHA_NEW="03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"


def read(path, sha):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
        raise ValueError("Frozen forecast file digest mismatch: "+str(path))
    with path.open(newline="",encoding="utf-8") as fh:
        rows=list(csv.DictReader(fh))
    keys=[(int(r["match_id"]),int(r["minute"])) for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError("Duplicate match-minute rows")
    for r in rows:
        if int(r["radiant_win"]) not in (0,1):
            raise ValueError("Invalid outcome")
        for col in ("p_model","p_baseline"):
            v=float(r[col])
            if not (math.isfinite(v) and 0<v<1):
                raise ValueError("Invalid forecast probability")
    return rows


def score(rows, col):
    n=len(rows)
    return {
        "logloss":sum(
            -math.log(float(r[col])) if int(r["radiant_win"])
            else -math.log1p(-float(r[col])) for r in rows
        )/n,
        "brier":sum(
            (float(r[col])-int(r["radiant_win"]))**2 for r in rows
        )/n,
    }


def compute():
    old,new=read(OLD,SHA_OLD),read(NEW,SHA_NEW)
    old_map={(int(r["match_id"]),int(r["minute"])):int(r["radiant_win"]) for r in old}
    new_map={(int(r["match_id"]),int(r["minute"])):int(r["radiant_win"]) for r in new}
    if (len(old)!=3837 or len(new)!=3836
            or len({m for m,t in old_map})!=106
            or len({m for m,t in new_map})!=106
            or len(set(old_map)-set(new_map))!=1
            or set(new_map)-set(old_map)
            or any(old_map[k]!=v for k,v in new_map.items())):
        raise ValueError("Preterminal/corrected identity or outcome drift")
    removed=next(iter(set(old_map)-set(new_map)))
    return {
        "evidence_class":"POST_TEST_TERMINAL_CORRECTION_HISTORICAL_COMPARISON",
        "historical_git_commit":"009f54d",
        "correction_git_commit":"4a77ae5",
        "preterminal_file_sha256":SHA_OLD,
        "corrected_file_sha256":SHA_NEW,
        "preterminal_forecasts":len(old),
        "corrected_forecasts":len(new),
        "test_games":106,
        "only_removed_test_forecast_key":list(removed),
        "previous": {"M0":score(old,"p_baseline"),"M1":score(old,"p_model")},
        "corrected":{"M0":score(new,"p_baseline"),"M1":score(new,"p_model")},
        "core_model_refit_after_test_inspection":True,
        "new_blind_test_claimed":False,
        "note":"TEST had already been viewed before the source fix. One TEST boundary forecast was removed; TRAIN also lost eight terminal rows and was refit, so shared predictions may change.",
    }


def compare(actual,expected,path="root"):
    if type(actual) is not type(expected):
        raise ValueError("Type mismatch: "+path)
    if isinstance(actual,float):
        if not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-12):
            raise ValueError("Historical metric mismatch: "+path)
    elif isinstance(actual,dict):
        if set(actual)!=set(expected):
            raise ValueError("Receipt keys changed: "+path)
        for k in actual:
            compare(actual[k],expected[k],path+"."+k)
    elif isinstance(actual,list):
        if len(actual)!=len(expected):
            raise ValueError("Receipt length changed: "+path)
        for i,(v,w) in enumerate(zip(actual,expected)):
            compare(v,w,path+"["+str(i)+"]")
    elif actual!=expected:
        raise ValueError("Receipt drift: "+path)


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    args=ap.parse_args()
    result=compute()
    if args.write:
        RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    else:
        compare(result,json.loads(RECEIPT.read_text()))
    print(json.dumps({"status":"PASS","before_rows":result["preterminal_forecasts"],
                      "after_rows":result["corrected_forecasts"],
                      "before_M1_LL":result["previous"]["M1"]["logloss"],
                      "after_M1_LL":result["corrected"]["M1"]["logloss"]},sort_keys=True))


if __name__=="__main__":
    main()
