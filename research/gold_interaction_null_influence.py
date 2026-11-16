#!/usr/bin/env python3
"""Hostile TRAIN-only correct-null, patch and influence checks (post-result)."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from conditional_gold_value import compare, evaluate_fit
from conditional_gold_forward import FROZEN_CUTS, loss, series_bootstrap
from train_time_effect_ci import (
    FEATURES, MANIFEST, MANIFEST_SHA, TRAIN_SHA, cluster_ids,
    model, require_data,
)

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json"
SEED=20261115
NULL_FEATURES=["gold_k","minute10"]


def forward_interaction_only(df):
    info=df[["match_id","start_time","duration","series_id"]].drop_duplicates()
    info=info.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
    pred=[]
    folds=[]
    for left,right in zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]):
        first=int(info.iloc[left].start_time)
        older=info.iloc[:left]
        old_ids=set(older.loc[older.start_time+older.duration<=first,"match_id"])
        eval_ids=set(info.iloc[left:right].match_id)
        train=df[df.match_id.isin(old_ids)]
        newer=df[df.match_id.isin(eval_ids)]
        if len(train)<500 or len(newer)<200 or not old_ids.isdisjoint(eval_ids):
            raise ValueError("Invalid source chronology")
        # Guarantee that no known professional series can span either
        # the chronological nominal cutoff or actual maturity-embargoed fit.
        candidate=info.iloc[:left]
        relevant=info.iloc[left:right]
        if not set(cluster_ids(candidate)).isdisjoint(set(cluster_ids(relevant))):
            raise ValueError("Series crosses the frozen TRAIN forward boundary")
        if not set(cluster_ids(candidate[candidate.match_id.isin(old_ids)])).isdisjoint(
                set(cluster_ids(relevant))):
            raise ValueError("Series crosses the maturity-filtered forward fit")
        # Strong null: gold + clock main effects without gold*clock.
        null=model().fit(train[NULL_FEATURES],train.radiant_win.astype(int))
        alt=model().fit(train[FEATURES],train.radiant_win.astype(int))
        pnull=null.predict_proba(newer[NULL_FEATURES])[:,1]
        palt=alt.predict_proba(newer[FEATURES])[:,1]
        y=newer.radiant_win.to_numpy(float)
        ln,bn=loss(y,pnull)
        la,ba=loss(y,palt)
        pred.append(pd.DataFrame({
            "match_id":newer.match_id.to_numpy(),
            "series_id":newer.series_id.to_numpy(),
            "minute":newer.minute.to_numpy(),
            "delta_logloss":la-ln,
            "delta_brier":ba-bn,
        }))
        folds.append({"train_games":int(len(old_ids)),
                      "eval_games":int(len(eval_ids)),
                      "eval_rows":int(len(newer)),
                      "embargo":int(left-len(old_ids)),
                      "delta_logloss":float(np.mean(la-ln)),
                      "delta_brier":float(np.mean(ba-bn))})
    oof=pd.concat(pred,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
            or oof[["match_id","minute"]].duplicated().any()):
        raise ValueError("Original TRAIN OOF scope drifted")
    return oof,folds


def patch_and_influence(df):
    manifest=pd.read_csv(MANIFEST)
    pairs=manifest.loc[manifest.partition=="train",["match_id","patch"]]
    if (pairs.match_id.duplicated().any() or len(pairs)!=291
            or set(pairs.match_id)!=set(df.match_id)):
        raise ValueError("Patch mapping/partition contract failed")
    patch=dict(zip(pairs.match_id,pairs.patch))
    counts={}
    for code in (59,60):
        games={i for i,p in patch.items() if int(p)==code}
        sub=df[df.match_id.isin(games)]
        if sub.radiant_win.nunique()!=2:raise ValueError("Only one outcome class")
        counts[str(code)]={"games":int(len(games)),"rows":int(len(sub)),
                           "fit_D":float(evaluate_fit(sub)["logodds_difference_t10_minus_t30"])}
    if (counts["59"]["games"],counts["60"]["games"])!=(250,41):
        raise ValueError("TRAIN patch composition drift")
    full=float(evaluate_fit(df)["logodds_difference_t10_minus_t30"])
    ids=cluster_ids(df)
    uniq=sorted(set(ids))
    if len(uniq)!=171:raise ValueError("Expected 171 TRAIN clusters")
    records=[]
    for k in uniq:
        subset=df[ids!=k]
        d=float(evaluate_fit(subset)["logodds_difference_t10_minus_t30"])
        records.append({"group":k,"omit_one_D":d,"absolute_impact":abs(d-full)})
    top=sorted(records,key=lambda d:d["absolute_impact"],reverse=True)[:5]
    five={x["group"] for x in top}
    without5=df[~np.isin(ids,list(five))]
    return {
        "patch_subfit":counts,
        "all_train_D":full,
        "leave_one_cluster":{
            "clusters":171,"minimum_D":float(min(r["omit_one_D"] for r in records)),
            "maximum_D":float(max(r["omit_one_D"] for r in records)),
            "negative_D_count":int(sum(r["omit_one_D"]<=0 for r in records)),
            "top_five_by_absolute_impact":top,
            "without_top5_games":int(without5.match_id.nunique()),
            "without_top5_D":float(evaluate_fit(without5)["logodds_difference_t10_minus_t30"]),
        },
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    df=require_data()
    out,folds=forward_interaction_only(df)
    bootstrap=series_bootstrap(out,draws=5000)
    # Existing helper labels its comparison M0; rename explicitly because
    # here the null includes minute, not the required gold-only baseline.
    bootstrap["M1_minus_gold_time_null_logloss"]=bootstrap.pop("M1_minus_M0_logloss")
    bootstrap["M1_minus_gold_time_null_brier"]=bootstrap.pop("M1_minus_M0_brier")
    sub=patch_and_influence(df)
    result={
        "scope":"TRAIN_ONLY_POST_RESULT_HOSTILE_CORRECT_INTERACTION_NULL",
        "source_train_sha256":TRAIN_SHA,"source_manifest_sha256":MANIFEST_SHA,
        "original_validation_or_test_outcomes_read":False,
        "null_model":NULL_FEATURES,
        "comparison_model":FEATURES,
        "folds":folds,
        "oof_games":137,"oof_rows":5081,
        "interaction_null_bootstrap":bootstrap,
        "patch_and_cluster_influence":sub,
        "model_promotion_permitted":False,
    }
    if args.write:
        RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
        print("WROTE",RECEIPT)
    else:
        compare(result,json.loads(RECEIPT.read_text()))
        print("PASS: correct-null and patch influence receipt")
    print("INTERACTION_NULL",bootstrap)
    print("PATCH",sub["patch_subfit"])
    print("JACKKNIFE",sub["leave_one_cluster"]["minimum_D"],
          sub["leave_one_cluster"]["maximum_D"],
          "top5_removed",sub["leave_one_cluster"]["without_top5_D"])


if __name__=="__main__":
    main()
