#!/usr/bin/env python3
"""Portable, no-network independent replication using frozen TRAIN+VAL features.

The derived CSV does not contain any original TEST outcomes or features.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit

from forward_oof_calibration import (COLS, ROOT, RECEIPT_PATH, DEV_FEATURE_FILE_SHA,
    verify_split_manifest_bytes, make_model,
    forward_oof, find_intercept_offset, metric_summary, paired_bootstrap)
from sklearn.metrics import log_loss

FEATURES = ROOT / "research/calibration_development_features.csv.gz"
MANIFEST = ROOT / "research/calibration_frozen_manifest.csv"
FEATURE_SHA = ROOT / "research/calibration_development_features.sha256"


def audit():
    data = FEATURES.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != FEATURE_SHA.read_text().strip() or digest != DEV_FEATURE_FILE_SHA:
        raise ValueError("Frozen development features SHA256 mismatch")
    df = pd.read_csv(FEATURES, float_precision="round_trip")
    verify_split_manifest_bytes(MANIFEST)
    manifest = pd.read_csv(MANIFEST)
    identities=manifest.set_index("match_id")[["partition","start_time","series_id"]]
    if not set(df.match_id).issubset(set(identities.index)):
        raise ValueError("Feature dataset has unknown match ID")
    observed=df[["match_id","partition","start_time","series_id"]].drop_duplicates().set_index("match_id").sort_index()
    expected=identities.loc[observed.index].sort_index()
    if not observed.equals(expected):
        raise ValueError("Development feature match/series/partition binding changed")
    if set(df.partition) != {"train", "validation"}:
        raise ValueError("Only TRAIN/VAL features allowed")
    if set(df.match_id).intersection(set(manifest.loc[manifest.partition=="test","match_id"])):
        raise ValueError("TEST match ID in development features")
    counts = df.groupby("partition").agg(games=("match_id","nunique"),rows=("minute","size"))
    if (counts.loc["train","games"],counts.loc["validation","games"],
            counts.loc["train","rows"],counts.loc["validation","rows"]) != (291,103,10675,3781):
        raise ValueError("Development data dimensions differ")
    train=df.loc[df.partition=="train"]
    val=df.loc[df.partition=="validation"]
    oof, blocks=forward_oof(train,manifest)
    b=find_intercept_offset(oof.p.to_numpy(),oof.y.to_numpy())
    original=make_model().fit(train[COLS],train.radiant_win)
    base=make_model().fit(train[["gold_k"]],train.radiant_win)
    p=original.predict_proba(val[COLS])[:,1]
    pb=base.predict_proba(val[["gold_k"]])[:,1]
    vv=pd.DataFrame({
        "match_id":val.match_id.to_numpy(),"series_id":val.series_id.to_numpy(),
        "minute":val.minute.to_numpy(),"y":val.radiant_win.to_numpy(dtype=int),
        "p_uncal":p,"p_offset":expit(logit(p)+b)})
    return {"offset":b,"oof_rows":len(oof),"folds":blocks,
            "M0_logloss":float(log_loss(val.radiant_win,pb)),
            "M1":metric_summary(vv,"p_uncal"),
            "offset_model":metric_summary(vv,"p_offset"),
            "paired":paired_bootstrap(vv)}


def main():
    result=audit()
    frozen=json.loads(RECEIPT_PATH.read_text())
    comparisons=[
        (result["offset"],frozen["selection"]["offset"]),
        (result["M0_logloss"],frozen["reused_validation"]["baseline_M0_logloss"]),
    ]
    for key,fkey in [("M1","M1_original"),("offset_model","M1_offset")]:
        for metric in ("logloss","brier","ece10","signed_mean_prediction_minus_outcome"):
            comparisons.append((result[key][metric],frozen["reused_validation"][fkey][metric]))
    for metric in ("difference_cal_minus_original_brier",
                   "difference_cal_minus_original_logloss",
                   "equal_game_mean_difference_logloss",
                   "equal_game_mean_difference_brier"):
        comparisons.append((result["paired"][metric],frozen["reused_validation"]["paired_comparison"][metric]))
    if result["oof_rows"] != frozen["selection"]["oof_rows"] or result["folds"] != frozen["selection"]["folds"]:
        raise AssertionError("OOF chronology changed")
    if any(abs(x-y)>1e-10 for x,y in comparisons):
        raise AssertionError("Portable feature audit differs from frozen full-data receipt")
    if not result["paired"]["groups"]==53:
        raise AssertionError("Series cluster count changed")
    if not result["M1"]["ece10"] < result["offset_model"]["ece10"]:
        raise AssertionError("Expected calibration ECE negative result changed")
    print("PASS: portable TRAIN-only OOF calibration verified; 103 reused VAL games; no TEST labels")
    print("M1 raw LL/Brier",result["M1"]["logloss"],result["M1"]["brier"])
    print("Offset LL/Brier",result["offset_model"]["logloss"],result["offset_model"]["brier"])
    print("Warning: reused VAL, ECE worse, CI crosses zero. DO NOT PROMOTE.")


if __name__=="__main__":
    main()
