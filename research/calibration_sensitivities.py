#!/usr/bin/env python3
"""Posthoc group/cut/maturity sensitivity on reused TRAIN+VAL only.

This was added in response to Fable hostile review, AFTER first calibration
results. Never treat any sensitivity as a predeclared model-selection gate.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit, logit
from sklearn.metrics import log_loss,brier_score_loss

from forward_oof_calibration import (ROOT, COLS, make_model, forward_oof,
    find_intercept_offset, verify_split_manifest_bytes, DEV_FEATURE_FILE_SHA)

MANIFEST=ROOT/"research/calibration_frozen_manifest.csv"
FEATURES=ROOT/"research/calibration_development_features.csv.gz"
OUT=ROOT/"research/CALIBRATION_SENSITIVITY_RECEIPT.json"
SEED=20261115


def prepare():
    import hashlib
    verify_split_manifest_bytes(MANIFEST)
    if hashlib.sha256(FEATURES.read_bytes()).hexdigest()!=DEV_FEATURE_FILE_SHA:
        raise AssertionError("Features drift")
    m=pd.read_csv(MANIFEST)
    df=pd.read_csv(FEATURES,float_precision="round_trip")
    return m,df.loc[df.partition=="train"].copy(),df.loc[df.partition=="validation"].copy()


def evaluate_variant(train,val,manifest,fractions,buffer_seconds=0,final_train_embargo=False):
    oof,blocks=forward_oof(train,manifest,fractions=fractions,
                           maturity_buffer_seconds=buffer_seconds)
    offset=find_intercept_offset(oof.p,oof.y)
    final_train=train
    removed=0
    if final_train_embargo:
        start=int(val.start_time.min())
        matured=train[["match_id","start_time","duration"]].drop_duplicates()
        incomplete=set(matured.loc[matured.start_time+matured.duration>start,"match_id"])
        removed=len(incomplete)
        final_train=train.loc[~train.match_id.isin(incomplete)]
    model=make_model().fit(final_train[COLS],final_train.radiant_win)
    base=model.predict_proba(val[COLS])[:,1]
    adjusted=expit(logit(base)+offset)
    y=val.radiant_win.to_numpy(dtype=int)
    return {
        "oof_games":int(oof.match_id.nunique()),"oof_rows":int(len(oof)),
        "offset":offset,"folds":blocks,"excluded_incomplete_train_games":removed,
        "original_val_logloss":float(log_loss(y,base)),
        "offset_val_logloss":float(log_loss(y,adjusted)),
        "delta_val_logloss":float(log_loss(y,adjusted)-log_loss(y,base)),
        "original_val_brier":float(brier_score_loss(y,base)),
        "offset_val_brier":float(brier_score_loss(y,adjusted)),
        "delta_val_brier":float(brier_score_loss(y,adjusted)-brier_score_loss(y,base)),
    },oof


def grouped_offset_bootstrap(oof,draws=1000):
    ids=np.where(oof.series_id.astype(int)>0,
                 "s"+oof.series_id.astype(str),"m"+oof.match_id.astype(str))
    group, labels=pd.factorize(ids,sort=True)
    z=logit(oof.p.to_numpy(dtype=float))
    y=oof.y.to_numpy(dtype=int)
    G=len(labels)
    rng=np.random.default_rng(SEED)
    values=[]
    for _ in range(draws):
        picks=rng.integers(0,G,size=G)
        multiplicity=np.bincount(picks,minlength=G)
        weights=multiplicity[group]
        f=lambda b: float(np.dot(weights,expit(z+b)-y))
        if f(-20)>=0 or f(20)<=0:
            raise ValueError("Bootstrap offset root not bracketed")
        values.append(brentq(f,-20,20,xtol=1e-10))
    return {
        "groups":G,"draws":draws,
        "offset_95ci":np.quantile(values,[.025,.975]).tolist(),
        "fraction_positive":float(np.mean(np.asarray(values)>0)),
    }


def per_fold_summary(oof,blocks,manifest):
    out=[]
    ptr=0
    info=manifest.set_index("match_id")
    for i,b in enumerate(blocks,1):
        part=oof.iloc[ptr:ptr+b["new_rows"]]
        ptr+=b["new_rows"]
        games=part[["match_id"]].drop_duplicates()
        patches=info.loc[games.match_id].patch
        out.append({
            "fold":i, "games":int(len(games)),
            "minute_rows":int(len(part)),
            "mean_p_minus_y":float((part.p-part.y).mean()),
            "mean_y":float(part.y.mean()),
            "patch_game_counts":{str(k):int(v) for k,v in patches.value_counts().items()},
        })
    if ptr!=len(oof):
        raise AssertionError("Fold row allocation mismatch")
    return out


def study():
    manifest,train,val=prepare()
    recipes=[
        ("original_executed_grid",(0.45,0.65,0.75,0.88),0,False),
        ("retain_original_fourth_cut",(0.45,0.65,0.75,0.84),0,False),
        ("maturity_buffer_15m",(0.45,0.65,0.75,0.88),900,False),
        ("maturity_buffer_60m",(0.45,0.65,0.75,0.88),3600,False),
        ("exclude_5_train_overlaps_at_val",(0.45,0.65,0.75,0.88),0,True),
    ]
    results={}
    for name,cuts,buffer,exclude in recipes:
        result,oof=evaluate_variant(train,val,manifest,cuts,buffer,exclude)
        results[name]=result
        if name=="original_executed_grid":
            results[name]["fold_bias"]=per_fold_summary(oof,result["folds"],manifest)
            results[name]["series_bootstrap_offset"]=grouped_offset_bootstrap(oof)
    return {
        "evidence_class":"POST_HOC_SENSITIVITY_REUSED_VAL_NOT_INDEPENDENT",
        "original_test_games_read":0,
        "do_not_select_best_variant":True,
        "reanalysis_occurred_after_first_val_results":True,
        "variations":results,
    }


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    if args.write==args.check:ap.error("Choose one of --write or --check")
    result=study()
    payload=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.write:
        OUT.write_text(payload)
        print("WROTE",OUT)
    elif OUT.read_text()!=payload:
        raise SystemExit("Sensitivity receipt mismatch")
    for name,v in result["variations"].items():
        print(name,"OOF games",v["oof_games"],"offset",round(v["offset"],5),
              "VAL delta LL",round(v["delta_val_logloss"],6),
              "VAL delta Brier",round(v["delta_val_brier"],6),
              "excluded train",v["excluded_incomplete_train_games"])
    print("OFFSET CI",result["variations"]["original_executed_grid"]["series_bootstrap_offset"]["offset_95ci"])


if __name__=="__main__":
    main()
