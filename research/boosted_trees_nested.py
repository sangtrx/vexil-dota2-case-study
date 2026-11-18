#!/usr/bin/env python3
"""Two-inner-fold, four-outer-fold predeclared XGB/LGBM fairness sensitivity.

Designed after prior fixed-configuration failure. Evaluates ONLY original 291
March TRAIN matches, so not a fresh blind comparison or recruiter model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from all_family_models import verify_original_artifacts
from boosted_trees_direct import (
    CANDIDATES, CONTROLS, INPUTS, PARAMS, ROOT, binned_calibration,
    candidate_model, check_environment, folded_source,
    match_equal_fit_weights, paired_series_ci, pooled_scores, sha_file,
)
from rich_feature_models import MODELS as OLD_MODELS, create_pipeline as original_pipeline
from rich_feature_models import load_train, proper
from train_time_effect_ci import cluster_ids

PROTO=ROOT/"research/BOOSTED_NESTED_FAIRNESS_PROTOCOL_20261118.md"
FIXED=ROOT/"research/BOOSTED_TREES_DIRECT_RECEIPT.json"
RECEIPT=ROOT/"research/BOOSTED_NESTED_FAIRNESS_RECEIPT.json"
READOUT=ROOT/"research/BOOSTED_NESTED_FAIRNESS_READOUT.md"
PROFILE_NAMES=("conservative","moderate","flexible")
PROFILES={
    "XGB":{
        "conservative":{
            "n_estimators":90,"max_depth":2,"learning_rate":0.04,
            "min_child_weight":35,"reg_lambda":25,"gamma":0.2,"subsample":0.85,
        },
        "moderate":{
            "n_estimators":150,"max_depth":2,"learning_rate":0.05,
            "min_child_weight":15,"reg_lambda":12,"gamma":0.05,"subsample":0.85,
        },
        "flexible":{
            "n_estimators":180,"max_depth":3,"learning_rate":0.04,
            "min_child_weight":8,"reg_lambda":8,"gamma":0.0,"subsample":0.90,
        },
    },
    "LGB":{
        "conservative":{
            "n_estimators":90,"max_depth":3,"num_leaves":5,"learning_rate":0.04,
            "min_child_samples":175,"min_child_weight":25,"reg_lambda":25,
            "min_split_gain":0.2,
        },
        "moderate":{
            "n_estimators":150,"max_depth":3,"num_leaves":7,"learning_rate":0.05,
            "min_child_samples":85,"min_child_weight":10,"reg_lambda":12,
            "min_split_gain":0.05,
        },
        "flexible":{
            "n_estimators":180,"max_depth":4,"num_leaves":9,"learning_rate":0.04,
            "min_child_samples":50,"min_child_weight":5,"reg_lambda":8,
            "min_split_gain":0.0,
        },
    },
}


def tuned_model(name:str,profile:str)->Pipeline:
    if name not in INPUTS or profile not in PROFILE_NAMES:
        raise ValueError("Unregistered model or hyperparameter profile")
    family="XGB" if name.startswith("XGB") else "LGB"
    args=PARAMS[family].copy()
    args.update(PROFILES[family][profile])
    args["colsample_bytree"]=1.0 if name.endswith("3") else 0.8
    estimator=XGBClassifier(**args) if family=="XGB" else LGBMClassifier(**args)
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median",keep_empty_features=True)),
        ("model",estimator),
    ])


def inner_fold_slices(outer_fit:pd.DataFrame):
    """Deterministic group ranks; no target/score inspection in split choice."""
    meta=outer_fit[["match_id","start_time","duration","series_id"]].drop_duplicates().copy()
    if len(meta)!=outer_fit.match_id.nunique():
        raise AssertionError("Duplicates in outer TRAIN identity")
    meta["cluster"]=cluster_ids(meta)
    first=meta.groupby("cluster",sort=True).start_time.min().sort_values(kind="stable")
    order=sorted(first.index.tolist(),key=lambda key:(int(first.loc[key]),str(key)))
    N=len(order)
    a=int(np.floor(0.55*N))
    b=int(np.floor(0.78*N))
    if a<8 or b-a<5 or N-b<5:
        raise AssertionError("Insufficient inner series/singleton groups")
    for j,(train_keys,val_keys) in enumerate(((order[:a],order[a:b]),
                                             (order[:b],order[b:])),start=1):
        train_meta=meta[meta.cluster.isin(train_keys)]
        val_meta=meta[meta.cluster.isin(val_keys)]
        first_eval=int(val_meta.start_time.min())
        mature=train_meta[train_meta.start_time+train_meta.duration<=first_eval]
        fit=outer_fit[outer_fit.match_id.isin(mature.match_id)]
        ev=outer_fit[outer_fit.match_id.isin(val_meta.match_id)]
        if (len(fit)==0 or len(ev)==0 or
            set(fit.match_id)&set(ev.match_id) or
            (fit.start_time+fit.duration>first_eval).any()):
            raise AssertionError("Inner chronological train/validation breached")
        if (set(cluster_ids(fit[["match_id","series_id"]]))
            & set(cluster_ids(ev[["match_id","series_id"]]))):
            raise AssertionError("Professional series crosses inner split")
        if len(fit)<500 or len(ev)<100:
            raise AssertionError("Not enough inner observations to assess models")
        yield j,fit,ev,{
            "inner_index":j,
            "fit_games":int(fit.match_id.nunique()),
            "fit_minutes":len(fit),
            "val_games":int(ev.match_id.nunique()),
            "val_minutes":len(ev),
            "fit_professional_groups":len(set(cluster_ids(fit[["match_id","series_id"]]))),
            "val_professional_groups":len(set(cluster_ids(ev[["match_id","series_id"]]))),
            "immature_games_excluded":int(len(train_meta)-len(mature)),
        }


def best_profile(scores:dict[str,float])->str:
    if set(scores)!=set(PROFILE_NAMES) or not all(np.isfinite(v) for v in scores.values()):
        raise ValueError("Missing/wrong inner candidate grid results")
    return min(PROFILE_NAMES,key=lambda profile:(scores[profile],PROFILE_NAMES.index(profile)))


def fit_and_predict(model:Pipeline,fit:pd.DataFrame,ev:pd.DataFrame,
                    cols:list[str])->np.ndarray:
    y=fit.radiant_win.astype(int)
    if y.nunique()<2 or len(fit)<500 or len(ev)==0:
        raise AssertionError("Invalid fold train positives")
    model.fit(fit[cols],y)
    p=model.predict_proba(ev[cols])[:,1]
    if len(p)!=len(ev) or not np.isfinite(p).all() or (p<=0).any() or (p>=1).any():
        raise AssertionError("Probabilities out of strict proper score domain")
    return p


def evaluate()->dict:
    versions=check_environment()
    if not PROTO.exists() or not FIXED.exists():
        raise AssertionError("Nested protocol/fixed prior results not committed")
    old=json.loads(FIXED.read_text())
    df,source=load_train()
    if (source["frozen_feature_csv_sha256"]!=old["source_rich_train_sha256"]
        or source["source_payload_bytes_sha256"]!=old["source_291_raw_payload_hash"]
        or len(df)!=10675 or df.match_id.nunique()!=291 or set(df.partition)!={"train"}):
        raise AssertionError("Original TRAIN or as-of source changed")
    protected=verify_original_artifacts()
    if protected!=old["original_applicant_files"]:
        raise AssertionError("Applicant files changed since fixed experiment")

    names=("M1_interaction","Q1_path","M1_MATCH_EQUAL")+tuple(name+"_TUNED" for name in CANDIDATES)
    fold_records=[]
    parts=[]
    for k,fit,ev,unmature in folded_source(df):
        y=ev.radiant_win.astype(int).to_numpy()
        table=ev[["match_id","minute","series_id"]].copy()
        table["y"]=y
        inner=list(inner_fold_slices(fit))
        if len(inner)!=2:
            raise AssertionError("Exactly two nested inner folds required")
        info={
            "outer_fold":k,"outer_fit_games":int(fit.match_id.nunique()),
            "outer_eval_games":int(ev.match_id.nunique()),
            "outer_eval_minutes":len(ev),
            "outer_immature_games_excluded":int(unmature),
            "inner_splits":[obj[3] for obj in inner],
            "candidate_selection":{},
            "outer_scores":{},
        }
        for base_name in ("M1_interaction","Q1_path","M1_MATCH_EQUAL"):
            model=original_pipeline("M1_interaction" if base_name=="M1_MATCH_EQUAL" else base_name)
            cols=list(OLD_MODELS["M1_interaction" if base_name=="M1_MATCH_EQUAL" else base_name])
            kw={"logistic__sample_weight":match_equal_fit_weights(fit)} if base_name=="M1_MATCH_EQUAL" else {}
            model.fit(fit[cols],fit.radiant_win.astype(int),**kw)
            p=model.predict_proba(ev[cols])[:,1]
            if not np.isfinite(p).all() or (p<=0).any() or (p>=1).any():
                raise AssertionError("Invalid reference probability")
            ll,br=proper(y,p)
            table["p_"+base_name]=p
            table["ll_"+base_name]=ll
            table["br_"+base_name]=br
            entry={"logloss":float(ll.mean()),"brier":float(br.mean())}
            prior=old["folds"][k-1]["models"][base_name]
            for metric in ("logloss","brier"):
                if not math.isclose(entry[metric],float(prior[metric]),rel_tol=0,abs_tol=1e-9):
                    raise AssertionError("Original fixed baseline parity failed "+base_name)
            info["outer_scores"][base_name]=entry

        for name in CANDIDATES:
            cols=list(INPUTS[name])
            inner_totals={}
            inner_details={}
            for profile in PROFILE_NAMES:
                tot_ll=0.0
                count=0
                fold_m=[]
                for j,train_inner,eval_inner,meta in inner:
                    m=tuned_model(name,profile)
                    p=fit_and_predict(m,train_inner,eval_inner,cols)
                    loss,_=proper(eval_inner.radiant_win.astype(int).to_numpy(),p)
                    n=len(loss)
                    tot_ll+=float(loss.sum())
                    count+=n
                    fold_m.append({"inner_fold":j,"val_minutes":n,
                                   "logloss":float(loss.mean())})
                if count!=sum(z[3]["val_minutes"] for z in inner):
                    raise AssertionError("Inner score denominator not aligned")
                inner_totals[profile]=tot_ll/count
                inner_details[profile]=fold_m
            winner=best_profile(inner_totals)
            final_model=tuned_model(name,winner)
            p=fit_and_predict(final_model,fit,ev,cols)
            ll,br=proper(y,p)
            key=name+"_TUNED"
            table["p_"+key]=p
            table["ll_"+key]=ll
            table["br_"+key]=br
            info["candidate_selection"][name]={
                "selected_profile":winner,
                "inner_minute_ll":{p:float(v) for p,v in inner_totals.items()},
                "inner_parts":inner_details,
            }
            info["outer_scores"][key]={
                "logloss":float(ll.mean()),
                "brier":float(br.mean()),
                "selected_profile":winner,
            }
        fold_records.append(info)
        parts.append(table)
    oof=pd.concat(parts,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
        or len(set(cluster_ids(oof[["match_id","series_id"]])))!=70
        or oof[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Outer TRAIN forward 137/5081/70 geometry failed")
    scores={name:pooled_scores(oof,name) for name in names}
    for baseline in ("M1_interaction","Q1_path","M1_MATCH_EQUAL"):
        for metric in ("logloss_minute","brier","logloss_equal_game"):
            if not math.isclose(scores[baseline][metric],
                                old["scores"][baseline][metric],
                                rel_tol=0,abs_tol=1e-9):
                raise AssertionError("Pooled baseline mismatch "+baseline+"/"+metric)
    comparisons={}
    gate={}
    for name in CANDIDATES:
        key=name+"_TUNED"
        comparisons[name]={}
        for ctrl in CONTROLS:
            s=paired_series_ci(oof,key,ctrl)
            s["forward_fold_wins"]=sum(
                f["outer_scores"][key]["logloss"]<f["outer_scores"][ctrl]["logloss"]
                for f in fold_records
            )
            comparisons[name][ctrl]=s
        gate[name]=all(
            x["delta_logloss_minute"]<=-0.005
            and x["ci99375_minute"][1]<0
            and x["delta_brier"]<=0
            and x["delta_brier_late30"]<=0
            and x["forward_fold_wins"]>=3
            for x in comparisons[name].values()
        )
    if verify_original_artifacts()!=protected:
        raise AssertionError("Applicant files altered during nested model experiment")
    return {
        "scope":"RETROSPECTIVE_POST_RESULT_NESTED_SENSITIVITY_MARCH_TRAIN_ONLY",
        "not_an_original_test_or_fresh_prospective_dataset":True,
        "protocol_sha256":sha_file(PROTO),
        "fixed_prior_receipt_sha256":sha_file(FIXED),
        "versions":versions,
        "parameter_profiles":PROFILES,
        "model_families":list(CANDIDATES),
        "source_sha256":source["frozen_feature_csv_sha256"],
        "outer_folds":fold_records,
        "geometry":{
            "original_train_matches":291,
            "original_train_minutes":10675,
            "outer_eval_games":137,
            "outer_eval_minutes":5081,
            "outer_professional_groups":70,
            "inner_folds_per_outer":2,
            "frozen_mature_label_rule":True,
        },
        "scores":scores,
        "frozen_direct_scores":{name:old["scores"][name] for name in CANDIDATES},
        "comparisons":comparisons,
        "future_candidate_gate_only":gate,
        "bootstrap_draws":5000,
        "bootstrap_seed":20261118,
        "hypothesis_search_adjustment_covers_past_experiments":False,
        "original_applicant_artifact_hashes":protected,
        "employer_notebook_or_report_changed":False,
        "live_received_at_unavailable":True,
        "model_promotion_allowed":False,
    }


def make_readout(r:dict)->str:
    a=[
        "# Nested XGB/LightGBM sensitivity — honest post-result, TRAIN-only",
        "",
        "**Designed after frozen 4 candidate outer-fold failure; this is a fairness "
        "stress test, NOT a new blind model comparison.** Two series-group chronological "
        "inner folds select one of three fixed hyperparameter profiles per model family "
        "inside each original outer fit; no outer/eval label enters tuning.",
        "",
        "March original TRAIN: 291 games / 10,675 minutes. Nested outer checks: "
        "137 matches, 5,081 decisions, 70 professional groups, four existing outer folds.",
        "",
        "| Family | Fixed config LL | Nested tuned LL | Tuned equal-game LL | "
        "Tuned Brier | Tuned late30 Brier | Fold choices |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for model in CANDIDATES:
        s=r["scores"][model+"_TUNED"]
        original=r["frozen_direct_scores"][model]
        selected=[f["candidate_selection"][model]["selected_profile"]
                  for f in r["outer_folds"]]
        a.append(f"| {model} | {original['logloss_minute']:.6f} | "
                 f"{s['logloss_minute']:.6f} | {s['logloss_equal_game']:.6f} | "
                 f"{s['brier']:.6f} | {s['brier_late30']:.6f} | "
                 f"{', '.join(selected)} |")
    a+=["",
        "## Strong frozen controls",
        "",
        "| Control | Minute LL | Equal-game LL | Brier | Late30 Brier |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for model in ("M1_interaction","Q1_path","M1_MATCH_EQUAL"):
        s=r["scores"][model]
        a.append(f"| {model} | {s['logloss_minute']:.6f} | "
                 f"{s['logloss_equal_game']:.6f} | {s['brier']:.6f} | "
                 f"{s['brier_late30']:.6f} |")
    a+=["","## Actual out-of-fold performance by outer fold","",
        "| Outer | Eval games | M1 LL | Q1 LL | XGB3 LL | XGB84 LL | LGB3 LL | LGB84 LL |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for f in r["outer_folds"]:
        s=f["outer_scores"]
        a.append(f"| {f['outer_fold']} | {f['outer_eval_games']} | "
              +" | ".join(f"{s[k]['logloss']:.6f}" for k in (
                 "M1_interaction","Q1_path","XGB3_TUNED","XGB84_TUNED",
                 "LGB3_TUNED","LGB84_TUNED"
              ))+" |")
    a+=["","## Whole-professional-series bootstrap comparisons (negative favors nested tree)", "",
        "| Family | vs | Delta LL | 95% grouped CI | 99.375% 8-contrast CI | "
        "Brier delta | Late30 Brier delta | Forward fold wins |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for model in CANDIDATES:
        for ctrl,x in r["comparisons"][model].items():
            c,d=x["ci95_minute"],x["ci99375_minute"]
            a.append(f"| {model} | {ctrl} | {x['delta_logloss_minute']:+.6f} | "
                     f"[{c[0]:+.6f},{c[1]:+.6f}] | "
                     f"[{d[0]:+.6f},{d[1]:+.6f}] | "
                     f"{x['delta_brier']:+.6f} | "
                     f"{x['delta_brier_late30']:+.6f} | "
                     f"{x['forward_fold_wins']}/4 |")
    a+=["",
        "## Research-only gate; never employer release",
        ""]
    for model in CANDIDATES:
        a.append(f"- {model}: **{'PROMISING FOR NEW UNSEEN COHORT' if r['future_candidate_gate_only'][model] else 'FAILED'}**")
    a+=["",
        "Nested tuning avoids consuming the same outer fold for parameter choice, "
        "but experiment design followed inspection of prior screens, and 70 outer groups "
        "are correlated by league/time; no familywise adjustment covers those prior searches. "
        "Bootstrap CIs are descriptive and real received_at is unavailable.",
        "The employer notebook, report, TEST and reviewer ZIP are still unchanged. "
        "No tree can be promoted merely from a winning reused-fold experiment.",
        ""]
    return "\n".join(a)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write",action="store_true")
    mode.add_argument("--check",action="store_true")
    o=ap.parse_args()
    receipt=evaluate()
    text=make_readout(receipt)
    if o.write:
        if RECEIPT.exists() or READOUT.exists():
            raise FileExistsError("First scored nested result is immutable")
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
        READOUT.write_text(text)
        print(text)
    else:
        if RECEIPT.read_text()!=json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n":
            raise AssertionError("Independent nested scoring receipt changed")
        if READOUT.read_text()!=text:
            raise AssertionError("Nested readout changed")
        print("BYTE_EXACT_NESTED_REPLAY_PASS")
