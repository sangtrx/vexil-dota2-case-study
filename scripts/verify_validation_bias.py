#!/usr/bin/env python3
"""Offline reviewer verification of already selected VAL forecasts, never a new test.

Reproduces validation proper scores, overall and equal-game bias, series-
bootstrap intervals, source fingerprints and sample identities from the
bundled 3,781-row CSV. The original 500-match raw cache is not needed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"artifacts/validation_m0_m1_predictions.csv"
RECEIPT=ROOT/"docs/VALIDATION_BIAS_RECEIPT.json"
TRAIN_PARITY=ROOT/"research/posttest_temporal/TRAIN_PARITY_RECEIPT.json"

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(got,want,key,tol=1e-11):
    if abs(float(got)-float(want))>tol or not np.isfinite(got):
        raise ValueError("Validation "+key+" numeric mismatch: "+str(got)+" vs "+str(want))

def prop(y,p):
    p=np.clip(np.asarray(p,float),1e-15,1.-1e-15)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def ece(y,p):
    buckets=np.minimum((np.asarray(p,float)*10).astype(int),9)
    return float(sum((buckets==k).mean()*
                    abs(float(y[buckets==k].mean()-p[buckets==k].mean()))
                    for k in range(10) if np.any(buckets==k)))

def check()->dict:
    r=json.loads(RECEIPT.read_text())
    f=pd.read_csv(SOURCE)
    expected_cols=["match_id","minute","radiant_win","series_id","patch","p_M0","p_M1"]
    if list(f.columns)!=expected_cols:
        raise ValueError("Validation data schema changed")
    if sha(SOURCE)!=r["validation_forecasts_sha256"]:
        raise ValueError("Validation frozen forecast SHA changed")
    parity=json.loads(TRAIN_PARITY.read_text())
    if (r["model_fingerprints"]!=parity["model_coefficient_sha256"]
            or not parity["same_train_model_coefficients"]
            or parity["original_test_forecast_rows_checked"]!=3836):
        raise ValueError("VALIDATION models differ from original frozen TRAIN model fingerprints")
    if (len(f)!=3781 or f.match_id.nunique()!=103 or len(r["source_validation_ids"])!=103
            or sorted(f.match_id.unique().astype(int).tolist())!=r["source_validation_ids"]
            or f[["match_id","minute"]].duplicated().any()
            or not f.notna().all().all()
            or not set(f.patch.astype(int))=={60}
            or not set(f.radiant_win.astype(int)).issubset({0,1})):
        raise ValueError("Original VALIDATION cohort/sample identity changed")
    for _,grp in f.groupby("match_id",sort=False):
        if (not np.array_equal(np.sort(grp.minute.to_numpy(dtype=int)),
                               np.arange(len(grp))) or
                grp.radiant_win.nunique()!=1 or
                grp.series_id.nunique()!=1):
            raise ValueError("Validation minute clock, series or labels corrupt")
    for name in ("M0","M1"):
        if not ((f["p_"+name]>0)&(f["p_"+name]<1)).all():
            raise ValueError("Invalid frozen validation probability "+name)
    y=f.radiant_win.to_numpy(dtype=int)
    p0=f.p_M0.to_numpy(dtype=float)
    p1=f.p_M1.to_numpy(dtype=float)
    close(y.mean(),r["win_rate_per_minute_row"],"observed minute win rate")
    close(f.groupby("match_id").radiant_win.first().mean(),r["win_rate_per_game"],"game winner rate")
    close(r["train_game_win_rate_from_frozen_csv"],149/291,"TRAIN prior")
    original_expected={"M0":(.532490,.181075),"M1":(.519714,.175902)}
    for name,probs in (("M0",p0),("M1",p1)):
        m=r["models"][name]
        ll=prop(y,probs).mean()
        br=((y-probs)**2).mean()
        if abs(ll-original_expected[name][0])>5e-7 or abs(br-original_expected[name][1])>5e-7:
            raise ValueError("Notebook-saved VALIDATION score no longer reproduced")
        for label,val in (
            ("logloss",ll),("brier",br),
            ("ece_10bin_descriptive",ece(y,probs)),
            ("mean_predicted_minute_weighted",float(probs.mean())),
            ("bias_predicted_minus_observed_minute",float((probs-y).mean())),
            ("bias_predicted_minus_observed_equal_game",
                float(f.assign(res=probs-y).groupby("match_id").res.mean().mean()))
        ):
            close(val,m[label],name+"_"+label)
    group_id=np.where(f.series_id.to_numpy(dtype=int)>0,
                      "s"+f.series_id.astype(str).to_numpy(),
                      "m"+f.match_id.astype(str).to_numpy())
    clusters,index=np.unique(group_id,return_inverse=True)
    if len(clusters)!=53 or r["validation_series_or_singletons"]!=53:
        raise ValueError("Unexpected original validation cluster structure")
    counts=np.bincount(index,minlength=len(clusters)).astype(float)
    totals=[np.bincount(index,weights=probs-y,minlength=len(clusters))
            for probs in (p0,p1)]
    per_match=f.assign(res0=p0-y,res1=p1-y).groupby("match_id",sort=True)[["res0","res1"]].mean()
    ids=f.groupby("match_id",sort=True).series_id.first()
    key2=["s"+str(sid) if sid>0 else "m"+str(mid) for mid,sid in ids.items()]
    indices={key:i for i,key in enumerate(clusters)}
    game_index=np.array([indices[k] for k in key2],dtype=int)
    game_counts=np.bincount(game_index,minlength=len(clusters)).astype(float)
    game_totals=[np.bincount(game_index,weights=per_match[name],minlength=len(clusters))
                 for name in ("res0","res1")]
    draws=np.random.default_rng(20261116).integers(0,len(clusters),
                                                    size=(10000,len(clusters)))
    if r["bootstrap_draws"]!=10000 or r["bootstrap_seed"]!=20261116:
        raise ValueError("Frozen validation uncertainty design changed")
    for i,name in enumerate(("M0","M1")):
        minute=totals[i][draws].sum(axis=1)/counts[draws].sum(axis=1)
        game=game_totals[i][draws].sum(axis=1)/game_counts[draws].sum(axis=1)
        for key,arr in (("bias_minute_ci_95_series",minute),
                        ("bias_equal_game_ci_95_series",game)):
            for idx,val in enumerate(np.quantile(arr,[.025,.975])):
                close(val,r["models"][name][key][idx],name+"_"+key,tol=1e-11)
    if not (r["analysis_is_post_selection_and_descriptive"] is True
            and r["no_TEST_recalibration_or_score"] is True
            and r["raw_cache_required_only_for_source_reconstruction"] is True
            and r["original_frozen_500_raw_matches"]==500
            and r["original_test_games_not_scored"]==106):
        raise ValueError("Scientific caveats not preserved")
    return {"status":"PASS_FROZEN_VALIDATION_BIAS_OFFLINE",
            "validation_games":103,"validation_minutes":3781,
            "series_or_singletons":len(clusters),
            "validation_m1_bias":r["models"]["M1"]["bias_predicted_minus_observed_minute"],
            "validation_m1_bias_95ci":r["models"]["M1"]["bias_minute_ci_95_series"],
            "source_reconstruction_from_author_cache_not_repeated_by_offline_verifier":True,
            "never_a_new_blind_test":True}

if __name__=="__main__":
    print(json.dumps(check(),indent=2,sort_keys=True))
