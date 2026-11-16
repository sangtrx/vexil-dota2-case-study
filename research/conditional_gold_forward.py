#!/usr/bin/env python3
"""Chronological OOF M0-vs-M1 sensitivity on original TRAIN only (post-hoc)."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from conditional_gold_value import (
    compare as compare_receipt,
    contrast_rows, evaluate_fit,
)
from train_time_effect_ci import (
    FEATURES, MANIFEST_SHA, TRAIN_SHA, cluster_ids, model, require_data,
)

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/CONDITIONAL_GOLD_FORWARD_RECEIPT.json"
FROZEN_CUTS=(154,176,220,252,291)
DRAWS=5000
SEED=20261115


def loss(y,p):
    p=np.clip(p,1e-15,1-1e-15)
    return -(y*np.log(p)+(1-y)*np.log1p(-p)),(p-y)**2


def build_oof(df:pd.DataFrame):
    info=df[["match_id","start_time","series_id","duration"]].drop_duplicates()
    info=info.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
    if len(info)!=291:
        raise ValueError("Frozen TRAIN 291-game chronology violated")
    row_keys=np.where(info.series_id.to_numpy(int)>0,
        "s"+info.series_id.astype(str),"m"+info.match_id.astype(str))
    if (info.match_id.duplicated().any() or len(set(info.match_id))!=291
            or set(info.match_id)!=set(df.match_id)):
        raise ValueError("TRAIN metadata does not identify exactly 291 matches")

    result=[]
    receipt=[]
    eval_ids_seen=set()
    for left,right in zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]):
        old=info.iloc[:left].copy()
        target=info.iloc[left:right].copy()
        if len(target)<15:
            raise ValueError("Forward block too short")
        t0=int(target.iloc[0].start_time)
        eligible=old[old.start_time+old.duration<=t0]
        older_ids=set(eligible.match_id)
        new_ids=set(target.match_id)
        if not older_ids.isdisjoint(new_ids):
            raise ValueError("Potential self-leakage")
        if not new_ids.isdisjoint(eval_ids_seen):
            raise ValueError("Forward block repeated")
        eval_ids_seen.update(new_ids)
        keys_older=set(np.where(eligible.series_id.to_numpy(int)>0,
                              "s"+eligible.series_id.astype(str),
                              "m"+eligible.match_id.astype(str)))
        keys_new=set(np.where(target.series_id.to_numpy(int)>0,
                            "s"+target.series_id.astype(str),
                            "m"+target.match_id.astype(str)))
        if not keys_older.isdisjoint(keys_new):
            raise ValueError("Series crosses earlier TRAIN fit and future OOF")
        if not set(row_keys[left:right]).isdisjoint(set(row_keys[:left])):
            raise ValueError("Series crosses nominal TRAIN boundary")
        older=df[df.match_id.isin(older_ids)]
        newer=df[df.match_id.isin(new_ids)]
        if older.radiant_win.nunique()!=2 or len(newer)==0:
            raise ValueError("Invalid chronology fold")
        m0=model().fit(older[["gold_k"]],older.radiant_win.astype(int))
        m1=model().fit(older[FEATURES],older.radiant_win.astype(int))
        p0=m0.predict_proba(newer[["gold_k"]])[:,1]
        p1=m1.predict_proba(newer[FEATURES])[:,1]
        if not (np.isfinite(p0).all() and np.isfinite(p1).all()
                and (p0>0).all() and (p1>0).all()
                and (p0<1).all() and (p1<1).all()):
            raise ValueError("Invalid probabilities in OOF")
        y=newer.radiant_win.to_numpy(float)
        ll0,b0=loss(y,p0);ll1,b1=loss(y,p1)
        logits=m1.decision_function(contrast_rows())
        gold_effect=float((logits[1]-logits[0])-(logits[3]-logits[2]))
        # Compare independent original model fit implementation exactly.
        check=evaluate_fit(older)["logodds_difference_t10_minus_t30"]
        if not math.isclose(check,gold_effect,abs_tol=1e-12):
            raise ValueError("Conditional logit calculation drift")
        receipt.append({
            "training_completed_games":len(older_ids),
            "old_nominal_games":left,
            "embargoed_old_games":left-len(older_ids),
            "eval_games":len(new_ids),
            "eval_rows":len(newer),
            "first_eval_start":t0,
            "M0_logloss":float(ll0.mean()),
            "M1_logloss":float(ll1.mean()),
            "M0_brier":float(b0.mean()),
            "M1_brier":float(b1.mean()),
            "M1_conditional_gold_logodds_delta_t10_minus_t30":gold_effect,
        })
        result.append(pd.DataFrame({
            "match_id":newer.match_id.to_numpy(),
            "series_id":newer.series_id.to_numpy(),
            "minute":newer.minute.to_numpy(),
            "y":newer.radiant_win.to_numpy(int),
            "delta_logloss":ll1-ll0,
            "delta_brier":b1-b0,
        }))
    out=pd.concat(result,ignore_index=True)
    if (out.match_id.nunique()!=137 or len(out)!=5081
            or out[["match_id","minute"]].duplicated().any()
            or not set(out.match_id).issubset(set(df.match_id))):
        raise ValueError("Original forward OOF evaluation scope differs")
    return out,receipt


def series_bootstrap(oof:pd.DataFrame,draws=DRAWS):
    x=oof.copy()
    x["g"]=cluster_ids(x)
    s=x.groupby("g",sort=True).agg(
        n=("match_id","size"),
        dlog=("delta_logloss","sum"),
        dbrier=("delta_brier","sum"))
    if len(s)!=70:
        raise ValueError("Unexpected OOF series/singleton count")
    stats=s[["n","dlog","dbrier"]].to_numpy(float)
    rng=np.random.default_rng(SEED)
    ids=rng.integers(0,len(s),size=(draws,len(s)))
    draws_sum=stats[ids].sum(axis=1)
    effects=draws_sum[:,1:]/draws_sum[:,0,None]
    if not np.isfinite(effects).all():
        raise ValueError("Invalid bootstrap scores")
    ci=np.quantile(effects,[0.025,0.975],axis=0)
    means=x[["delta_logloss","delta_brier"]].mean()
    equal=x.groupby("match_id")[["delta_logloss","delta_brier"]].mean().mean()
    return {
        "groups":len(s),"draws":draws,"seed":SEED,
        "M1_minus_M0_logloss":{
            "point":float(means.delta_logloss),
            "percentile_ci_95":ci[:,0].tolist(),
            "equal_match_point":float(equal.delta_logloss),
        },
        "M1_minus_M0_brier":{
            "point":float(means.delta_brier),
            "percentile_ci_95":ci[:,1].tolist(),
            "equal_match_point":float(equal.delta_brier),
        },
    }


def study():
    df=require_data()
    preds,folds=build_oof(df)
    if [v["eval_games"] for v in folds] != [22,44,32,39]:
        raise AssertionError("Forward cutoff game counts changed")
    if [v["embargoed_old_games"] for v in folds] != [0,0,2,0]:
        raise AssertionError("Forward label maturity exclusions changed")
    r=series_bootstrap(preds)
    return {
        "scope":"POST_RESULT_TRAIN_ONLY_FORWARD_OOF_NOT_INDEPENDENT_TEST",
        "source_train_sha256":TRAIN_SHA,"source_manifest_sha256":MANIFEST_SHA,
        "training_match_count":291,"forward_eval_games":137,
        "forward_eval_rows":5081,
        "frozen_nominal_cutpoints":list(FROZEN_CUTS),
        "original_test_or_val_labels_read":False,
        "no_model_promotion":True,
        "folds":folds,
        "cluster_bootstrap":r,
    }


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    receipt=study()
    if args.write:
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True,
                                      allow_nan=False)+"\n")
        print("WROTE",RECEIPT)
    else:
        compare_receipt(receipt,json.loads(RECEIPT.read_text()))
        print("PASS frozen forward OOF sensitivity")
    print("FOLDS",[(r["eval_games"],r["eval_rows"],
                     round(r["M1_conditional_gold_logodds_delta_t10_minus_t30"],5))
                  for r in receipt["folds"]])
    print("BOOTSTRAP",receipt["cluster_bootstrap"])


if __name__=="__main__":
    main()
