#!/usr/bin/env python3
"""TRAIN-only local gold slopes, survivor bias and discrimination (post-hoc)."""
from __future__ import annotations
import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning

from conditional_gold_value import compare
from train_time_effect_ci import TRAIN_SHA, MANIFEST_SHA, cluster_ids, model, require_data

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/GOLD_LOCAL_WINDOW_SURVIVOR_RECEIPT.json"
SEED=20261115
DRAWS=1000
EARLY=(8,12)
LATE=(28,32)


def window_measures(group:pd.DataFrame)->dict:
    if not group.radiant_win.isin((0,1)).all() or group.radiant_win.nunique()!=2:
        raise ValueError("Invalid winner labels")
    x=group[["gold_k"]]
    y=group.radiant_win.astype(int)
    if not np.isfinite(x.to_numpy(float)).all():
        raise ValueError("Nonfinite gold")
    with warnings.catch_warnings():
        warnings.simplefilter("error",ConvergenceWarning)
        pipe=model().fit(x,y)
    beta=float(pipe.named_steps["logistic"].coef_[0][0])
    std=float(pipe.named_steps["scale"].scale_[0])
    if std<=0:raise ValueError("Degenerate gold scale")
    # Logistic slope on the raw per-1000-gold scale vs standardized gold.
    return {
        "logodds_per_plus_2k_gold":float(2*beta/std),
        "logodds_per_one_gold_SD":beta,
        "auc_gold_vs_winner":float(roc_auc_score(y,group.gold_k)),
        "observed_gold_SD_thousands":float(group.gold_k.std(ddof=0)),
        "games":int(group.match_id.nunique()),
        "rows":len(group),
    }


def panel(data:pd.DataFrame, *, balanced:bool):
    a=data.copy()
    a=a[(a.minute.between(*EARLY)) | (a.minute.between(*LATE))]
    if balanced:
        count=a.groupby("match_id").minute.agg(
            early=lambda s:int(s.between(*EARLY).sum()),
            late=lambda s:int(s.between(*LATE).sum()))
        games=set(count.index[(count.early==5)&(count.late==5)])
        # A minute-32 snapshot exists only for duration>1920 seconds
        # under the original strictly-preterminal, contiguous minute grid.
        # Checking this equivalence guards unexpected missing parse rows.
        eligible=set(data.loc[data.duration>32*60,"match_id"])
        if games!=eligible:
            raise ValueError("Balanced survivor panel diverges from complete strict-minute grid")
        a=a[a.match_id.isin(games)]
    a=a.copy()
    a["resample_group"]=cluster_ids(a)
    e=a[a.minute.between(*EARLY)]
    l=a[a.minute.between(*LATE)]
    if len(e)==0 or len(l)==0 or e.match_id.nunique()<50 or l.match_id.nunique()<50:
        raise ValueError("Insufficient window data")
    if balanced and (e.match_id.nunique()!=l.match_id.nunique()
                     or set(e.match_id)!=set(l.match_id)):
        raise AssertionError("Survivor panel games do not match exactly")
    return a, e, l


def calculate(data:pd.DataFrame,draws=DRAWS):
    output={}
    for name,balanced in (("all_available_games",False),
                          ("balanced_survivors_to_minute_32",True)):
        a,e,l=panel(data,balanced=balanced)
        point1=window_measures(e)
        point2=window_measures(l)
        group_frames={k:g for k,g in a.groupby("resample_group",sort=True)}
        names=sorted(group_frames)
        if len(names)<50:raise ValueError("Too few resampling groups")
        rng=np.random.default_rng(SEED)
        keys=("logodds_per_plus_2k_gold",
              "logodds_per_one_gold_SD","auc_gold_vs_winner")
        samples=np.empty((draws,len(keys)))
        for j in range(draws):
            picks=rng.integers(0,len(names),size=len(names))
            b=pd.concat([group_frames[names[int(z)]] for z in picks],ignore_index=True)
            eb=b[b.minute.between(*EARLY)]
            lb=b[b.minute.between(*LATE)]
            left=window_measures(eb)
            right=window_measures(lb)
            samples[j]=[left[k]-right[k] for k in keys]
            if (j+1)%250==0:
                print(name,"BOOTSTRAP",j+1,draws,flush=True)
        q=np.quantile(samples,[.025,.975],axis=0)
        output[name]={
            "balanced_on_future_survival_NOT_an_online_feature":balanced,
            "cluster_count":len(names),
            "early":point1,"late":point2,
            "differences_early_minus_late":{
                k:{"point":float(point1[k]-point2[k]),
                   "percentile_ci_95":q[:,i].tolist()}
                for i,k in enumerate(keys)
            },
        }
    return {
        "scope":"TRAIN_ONLY_POST_SELECTION_LOCAL_WINDOW_AND_SURVIVOR_FALSIFICATION",
        "source_train_sha256":TRAIN_SHA,
        "source_manifest_sha256":MANIFEST_SHA,
        "seed":SEED,"draws":draws,
        "minute_windows":{"early":[8,12],"late":[28,32]},
        "test_or_validation_outcomes_read":False,
        "model_promotion":False,
        "panels":output,
    }


def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    args=parser.parse_args()
    r=calculate(require_data())
    if args.write:
        RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+"\n")
        print("WROTE",RECEIPT)
    else:
        compare(r,json.loads(RECEIPT.read_text()))
        print("PASS: local-window and survivor-sensitivity receipt")
    for name,p in r["panels"].items():
        print(name,{"games_early":p["early"]["games"],
                    "games_late":p["late"]["games"],
                    "differences":p["differences_early_minus_late"]})


if __name__=="__main__":
    main()
