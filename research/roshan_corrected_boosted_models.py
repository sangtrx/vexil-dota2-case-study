#!/usr/bin/env python3
"""Post-result Roshan-corrected sensitivity for four fixed XGB/LGBM models on March TRAIN-forward folds.

The candidate families, inputs, hyperparameters and inference plan are frozen in
BOOSTED_TREES_LOCKED_PROTOCOL_20261118.md + its explicit pre-score amendment.
This is POST-SELECTION TRAIN-only research, not a newly blind test or live PIT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import lightgbm
import narwhals
import numpy as np
import pandas as pd
import sklearn
import xgboost
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from conditional_gold_forward import FROZEN_CUTS
from rich_feature_engineering import BASE, RICH
from roshan_corrected_rich_models import (
    MODELS as OLD_MODELS, create_pipeline as old_pipeline,
    load_train, proper,
)
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"research/BOOSTED_TREES_LOCKED_PROTOCOL_20261118.md"
AMEND=ROOT/"research/BOOSTED_TREES_PRE_SCORE_DEPENDENCY_AMENDMENT_20261118.md"
PRIOR=ROOT/"research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_RECEIPT.json"
RECEIPT=ROOT/"research/ROSHAN_CORRECTED_BOOSTED_RECEIPT.json"
READOUT=ROOT/"research/ROSHAN_CORRECTED_BOOSTED_READOUT.md"

INPUTS={
    "XGB3":tuple(BASE),
    "XGB84":tuple(BASE+RICH),
    "LGB3":tuple(BASE),
    "LGB84":tuple(BASE+RICH),
}
CANDIDATES=tuple(INPUTS)
REFS=("M0_gold","A_additive","M1_interaction","Q1_path","Q3_tree","M1_MATCH_EQUAL")
CONTROLS=("M1_interaction","Q1_path")
DRAWS=5000
SEED=20261118
ALPHA=0.05
SCREEN_SIZE=8
PARAMS={
    "XGB":{
        "objective":"binary:logistic", "n_estimators":90, "max_depth":2,
        "learning_rate":0.04, "min_child_weight":35, "reg_lambda":25,
        "gamma":0.2, "subsample":0.85, "tree_method":"hist",
        "max_bin":128, "n_jobs":2, "random_state":SEED,
        "eval_metric":"logloss", "verbosity":0,
    },
    "LGB":{
        "objective":"binary", "n_estimators":90,"max_depth":3,
        "num_leaves":5, "learning_rate":0.04,"min_child_samples":175,
        "min_child_weight":25,"reg_lambda":25, "min_split_gain":0.2,
        "subsample":1.0,"subsample_freq":0,"max_bin":128,"verbosity":-1,
        "deterministic":True,"force_col_wise":True,"n_jobs":2,
        "random_state":SEED,
    },
}


def sha_file(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_original_artifacts()->dict:
    # The optional historical 16 November ZIP is not part of the reviewer
    # package. Verify only the two frozen, included applicant artifacts.
    frozen={
        "live_dota2_win_probability.ipynb":
            "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f",
        "artifacts/heldout_predictions.csv":
            "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441",
    }
    for name, expected in frozen.items():
        if sha_file(ROOT/name)!=expected:
            raise ValueError("Frozen original applicant asset drift: "+name)
    return frozen



def check_environment()->dict:
    versions={
        "xgboost":xgboost.__version__,
        "lightgbm":lightgbm.__version__,
        "narwhals":narwhals.__version__,
        "sklearn":sklearn.__version__,
        "numpy":np.__version__,
        "pandas":pd.__version__,
        "python":sys.version.split()[0],
        "platform":platform.platform(),
    }
    if (versions["xgboost"],versions["lightgbm"],versions["narwhals"]) != (
        "3.4.1","4.7.0","2.21.2"
    ):
        raise AssertionError("Pinned isolated boosting package versions drift")
    if not PROTO.exists() or not AMEND.exists():
        raise AssertionError("Version amendment/protocol absent before scoring")
    return versions


def candidate_model(name:str)->Pipeline:
    if name not in INPUTS:
        raise ValueError("Unregistered boosted candidate: "+str(name))
    family="XGB" if name.startswith("XGB") else "LGB"
    args=PARAMS[family].copy()
    args["colsample_bytree"]=1.0 if name.endswith("3") else 0.8
    classifier=XGBClassifier(**args) if family=="XGB" else LGBMClassifier(**args)
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median",keep_empty_features=True)),
        ("model",classifier),
    ])


def match_equal_fit_weights(fit:pd.DataFrame)->np.ndarray:
    """Every historical FIT match contributes the SAME total loss weight.

    This training-only function never sees evaluation game duration, full future
    game length as a model input, original TEST or an evaluated label.
    """
    if len(fit)==0 or fit[["match_id","minute"]].duplicated().any():
        raise ValueError("Invalid completed-game training frame")
    n=len(fit)
    groups=int(fit.match_id.nunique())
    counts=fit.groupby("match_id").match_id.transform("size").to_numpy(dtype=float)
    if np.any(counts<=0):
        raise AssertionError("Empty game")
    weights=n/(groups*counts)
    total_by_match=pd.DataFrame({"m":fit.match_id.to_numpy(),"w":weights}).groupby("m").w.sum()
    if not np.allclose(total_by_match,total_by_match.iloc[0],atol=1e-10,rtol=0):
        raise AssertionError("Unequal fit-game weight mass")
    if not np.isclose(weights.sum(),n,atol=1e-9,rtol=0):
        raise AssertionError("Weights don't sum to historical rows")
    return weights


def binned_calibration(y:np.ndarray,p:np.ndarray)->dict:
    y=np.asarray(y,dtype=int)
    p=np.asarray(p,dtype=float)
    if (len(y)!=len(p) or len(y)==0 or not np.isfinite(p).all()
        or np.any(p<=0) or np.any(p>=1)):
        raise ValueError("Nonfinite/out-of-range model probabilities")
    idx=np.minimum((p*10).astype(int),9)
    bins=[]
    ece=0.
    for i in range(10):
        mask=idx==i
        count=int(mask.sum())
        pred=float(p[mask].mean()) if count else None
        obs=float(y[mask].mean()) if count else None
        if count:
            ece+=count/len(y)*abs(pred-obs)
        bins.append({"bin":i,"n_rows":count,"pred_mean":pred,"actual_mean":obs})
    if sum(item["n_rows"] for item in bins)!=len(y):
        raise AssertionError("Calibration denominator mismatch")
    return {
        "calibration_in_the_large":float(p.mean()-y.mean()),
        "ece_10_minute_rows_descriptive":float(ece),
        "bins":bins,
    }


def folded_source(df:pd.DataFrame):
    meta=df[["match_id","start_time","duration","series_id"]].drop_duplicates()
    meta=meta.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("Frozen temporal fold shape changed")
    for k,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        previous=meta.iloc[:left]
        current=meta.iloc[left:right]
        first_time=int(current.iloc[0].start_time)
        mature=previous[previous.start_time+previous.duration<=first_time]
        if len(mature)==0 or (set(cluster_ids(previous)) & set(cluster_ids(current))):
            raise AssertionError("Professional series overlaps boundary")
        if set(cluster_ids(mature)) & set(cluster_ids(current)):
            raise AssertionError("Train/eval group overlap")
        fit=df[df.match_id.isin(mature.match_id)]
        ev=df[df.match_id.isin(current.match_id)]
        if (len(fit)==0 or len(ev)==0 or
            set(fit.match_id)&set(ev.match_id) or
            int(ev.match_id.nunique())!=len(current) or
            (fit.start_time+fit.duration>first_time).any()):
            raise AssertionError("Label maturity or chronological fold breach")
        if (fit[["match_id","minute"]].duplicated().any()
            or ev[["match_id","minute"]].duplicated().any()
            or (ev.minute*60>=ev.duration).any()
            or not np.isfinite(ev[list(BASE+RICH)].to_numpy(dtype=float)).all()):
            raise AssertionError("PIT/duplicate/raw feature validity failed")
        yield k,fit,ev,len(previous)-len(mature)


def paired_series_ci(oof:pd.DataFrame,candidate:str,baseline:str,draws:int=DRAWS)->dict:
    d_ll=(oof["ll_"+candidate]-oof["ll_"+baseline]).to_numpy(float)
    d_br=(oof["br_"+candidate]-oof["br_"+baseline]).to_numpy(float)
    g=pd.DataFrame({
        "cluster":cluster_ids(oof[["match_id","series_id"]]),
        "n":1, "sum_ll":d_ll,"sum_br":d_br,
    }).groupby("cluster",sort=True).sum()
    if len(g)!=70:
        raise AssertionError("Whole series bootstrap must contain exactly 70 units")
    a=g[["n","sum_ll","sum_br"]].to_numpy(float)
    indices=np.random.default_rng(SEED).integers(0,len(a),size=(draws,len(a)))
    sums=a[indices].sum(axis=1)
    boot=sums[:,1:]/sums[:,0,None]
    overall_gain=-float(d_ll.sum())
    positive=(-g.sum_ll).clip(lower=0)
    frac=float(positive.max()/overall_gain) if overall_gain>0 else None
    late=oof.minute.to_numpy(int)>=30
    game=pd.DataFrame({"m":oof.match_id,"delta":d_ll}).groupby("m").delta.mean()
    return {
        "delta_logloss_minute":float(d_ll.mean()),
        "delta_logloss_equal_game":float(game.mean()),
        "delta_brier":float(d_br.mean()),
        "delta_brier_late30":float(d_br[late].mean()),
        "ci95_minute":np.quantile(boot[:,0],[0.025,0.975]).tolist(),
        "ci99375_minute":np.quantile(
            boot[:,0],[ALPHA/(SCREEN_SIZE*2),1-ALPHA/(SCREEN_SIZE*2)]
        ).tolist(),
        "max_positive_series_gain_share":frac,
        "series_groups":len(g),
    }


def pooled_scores(oof:pd.DataFrame,name:str)->dict:
    y=oof.y.to_numpy(int)
    p=oof["p_"+name].to_numpy(float)
    late=oof.minute.to_numpy(int)>=30
    early=oof.minute.to_numpy(int)<10
    a=oof["ll_"+name].to_numpy(float)
    b=oof["br_"+name].to_numpy(float)
    return {
        "logloss_minute":float(a.mean()),
        "logloss_equal_game":float(pd.DataFrame({"m":oof.match_id,"ll":a}).groupby("m").ll.mean().mean()),
        "brier":float(b.mean()),
        "brier_late30":float(b[late].mean()),
        "brier_early9":float(b[early].mean()),
        "p_range":[float(p.min()),float(p.max())],
        "calibration":binned_calibration(y,p),
    }


def evaluate()->dict:
    versions=check_environment()
    old=json.loads(PRIOR.read_text())
    original_files=verify_original_artifacts()
    df,source=load_train()
    if len(df)!=10675 or df.match_id.nunique()!=291 or set(df.partition)!={"train"}:
        raise AssertionError("Source already departed from March TRAIN")
    if len(BASE)!=3 or len(RICH)!=81 or len(BASE+RICH)!=84:
        raise AssertionError("Frozen rich feature family changed")
    names=REFS+CANDIDATES
    folds=[]
    parts=[]
    for k,fit,ev,unmature in folded_source(df):
        y=ev.radiant_win.astype(int).to_numpy()
        table=ev[["match_id","minute","series_id"]].copy()
        table["y"]=y
        fold={
            "number":k,"mature_fit_games":int(fit.match_id.nunique()),
            "unmature_fit_games_excluded":unmature,
            "eval_games":int(ev.match_id.nunique()),"eval_rows":len(ev),
            "models":{},
        }
        for name in names:
            if name in CANDIDATES:
                model=candidate_model(name)
                columns=list(INPUTS[name])
                model.fit(fit[columns],fit.radiant_win.astype(int))
            else:
                base_name="M1_interaction" if name=="M1_MATCH_EQUAL" else name
                model=old_pipeline(base_name)
                columns=list(OLD_MODELS[base_name])
                if name=="M1_MATCH_EQUAL":
                    weights=match_equal_fit_weights(fit)
                    model.fit(fit[columns],fit.radiant_win.astype(int),
                              logistic__sample_weight=weights)
                else:
                    model.fit(fit[columns],fit.radiant_win.astype(int))
            p=model.predict_proba(ev[columns])[:,1]
            if (len(p)!=len(ev) or not np.isfinite(p).all()
                or np.any(p<=0) or np.any(p>=1)):
                raise AssertionError("Invalid model probability "+name)
            ll,br=proper(y,p)
            table["p_"+name]=p
            table["ll_"+name]=ll
            table["br_"+name]=br
            entry={
                "logloss":float(ll.mean()),
                "brier":float(br.mean()),
                "equal_match_logloss":float(
                    pd.DataFrame({"m":ev.match_id,"ll":ll}).groupby("m").ll.mean().mean()
                ),
            }
            if name in ("M0_gold","A_additive","M1_interaction","Q1_path","Q3_tree"):
                for metric in ("logloss","brier"):
                    prior=float(old["folds"][k-1][name][metric])
                    if not math.isclose(entry[metric],prior,rel_tol=0,abs_tol=1e-9):
                        raise AssertionError("Historical prior "+name+" failed exact fold parity")
            fold["models"][name]=entry
        parts.append(table)
        folds.append(fold)
    oof=pd.concat(parts,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
        or len(set(cluster_ids(oof[["match_id","series_id"]])))!=70
        or oof[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Original complete TRAIN OOF geometry violated")
    scores={name:pooled_scores(oof,name) for name in names}
    contrasts={}
    gate={}
    for name in CANDIDATES:
        contrasts[name]={}
        for ctrl in CONTROLS:
            x=paired_series_ci(oof,name,ctrl)
            fold_wins=sum(f["models"][name]["logloss"]<f["models"][ctrl]["logloss"]
                           for f in folds)
            x["fold_wins"]=fold_wins
            contrasts[name][ctrl]=x
        gate[name]=all(
            x["delta_logloss_minute"]<=-.005
            and x["ci99375_minute"][1]<0
            and x["delta_brier"]<=0
            and x["delta_brier_late30"]<=0
            and x["fold_wins"]>=3
            for x in contrasts[name].values()
        )
    if verify_original_artifacts()!=original_files:
        raise AssertionError("Applicant source artifacts modified by experiment")
    return {
        "scope":"POST_SEARCH_MARCH_TRAIN_ONLY_FOUR_FIXED_BOOSTERS_NOT_BLIND",
        "prospective_new_cohort":False,
        "original_val_or_test_loaded":False,
        "protocol_sha256":sha_file(PROTO),
        "pre_score_package_amendment_sha256":sha_file(AMEND),
        "original_rich_prior_receipt_sha256":sha_file(PRIOR),
        "source_rich_train_sha256":source["frozen_feature_csv_sha256"],
        "source_291_raw_payload_hash":source["source_payload_bytes_sha256"],
        "packages":versions,
        "frozen_hyperparameters":PARAMS,
        "candidate_features":{name:list(cols) for name,cols in INPUTS.items()},
        "data_geometry":{"train_games":291,"train_minute_rows":10675,
                         "out_of_fold_games":137,"out_of_fold_minutes":5081,
                         "independent_series_or_singletons":70,
                         "num_folds":len(folds)},
        "folds":folds,
        "scores":scores,
        "comparisons":contrasts,
        "future_candidate_gate_only":gate,
        "new_candidate_boosting_test_count":len(CANDIDATES),
        "screen_local_comparisons":SCREEN_SIZE,
        "bootstrap_draws":DRAWS,
        "bootstrap_seed":SEED,
        "multiple_past_searches_corrected":False,
        "original_applicant_files":original_files,
        "original_notebook_and_test_predictions_changed":False,
        "report_and_zip_rebuilt_after_correction":True,
        "employer_promotion_authorized":False,
    }


def readout(r:dict)->str:
    lines=[
        "# Roshan-corrected XGBoost/LightGBM: TRAIN-only sensitivity",
        "",
        "**Post-selection exploratory model family test. Original March TEST and VAL "
        "are not accessed. No new blinded evidence or real-live receipt timestamps.**",
        "",
        "Data: 291 TRAIN games / 10,675 minute rows; four mature-label chronological "
        "series-disjoint evaluation blocks, 137 games, 5,081 rows and 70 groups.",
        "",
        f"Versions: XGBoost {r['packages']['xgboost']}, LightGBM {r['packages']['lightgbm']}, "
        f"Narwhals {r['packages']['narwhals']}, sklearn {r['packages']['sklearn']}. "
        "All trees exactly 90 rounds with conservative fixed leaf constraints.",
        "",
        "| Model | Inputs | Minute LL | Equal-game LL | Brier | Late30 Brier | Early9 Brier | ECE10 (descriptive) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in REFS+CANDIDATES:
        x=r["scores"][name]
        n=(len(INPUTS[name]) if name in CANDIDATES
           else len(OLD_MODELS["M1_interaction"] if name=="M1_MATCH_EQUAL" else OLD_MODELS[name]))
        lines.append(f"| {name} | {n} | {x['logloss_minute']:.6f} | "
          f"{x['logloss_equal_game']:.6f} | {x['brier']:.6f} | "
          f"{x['brier_late30']:.6f} | {x['brier_early9']:.6f} | "
          f"{x['calibration']['ece_10_minute_rows_descriptive']:.6f} |")
    lines+=["", "## All four frozen forward folds", "",
      "| Fold | Eval games | Fit completed games | M1 LL | Q1 LL | MATCH_EQUAL LL | "
      "Q3 sklearn LL | XGB3 LL | XGB84 LL | LGB3 LL | LGB84 LL |",
      "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in r["folds"]:
        m=f["models"]
        lines.append(f"| {f['number']} | {f['eval_games']} | {f['mature_fit_games']} | "
          +" | ".join(f"{m[n]['logloss']:.6f}" for n in (
          "M1_interaction","Q1_path","M1_MATCH_EQUAL","Q3_tree",
          "XGB3","XGB84","LGB3","LGB84"))+" |")
    lines+=["","## Paired whole-series uncertainty (negative delta favors boosted model)","",
      "| Boosted | vs control | Minute LL delta | 95% cluster CI | 99.375% screen-local CI | "
      "Brier delta | 30+ Brier delta | Winning folds |",
      "| --- | --- | ---: | --- | --- | ---: | ---: | ---: |"]
    for name in CANDIDATES:
        for ctrl,cmp in r["comparisons"][name].items():
            c=cmp["ci95_minute"]
            d=cmp["ci99375_minute"]
            lines.append(f"| {name} | {ctrl} | {cmp['delta_logloss_minute']:+.6f} | "
               f"[{c[0]:+.6f},{c[1]:+.6f}] | "
               f"[{d[0]:+.6f},{d[1]:+.6f}] | "
               f"{cmp['delta_brier']:+.6f} | "
               f"{cmp['delta_brier_late30']:+.6f} | {cmp['fold_wins']}/4 |")
    lines+=["",
       "## Frozen research-only decision gate",
       ""]
    for name,passed in r["future_candidate_gate_only"].items():
        lines.append(f"- {name}: **{'PROMISING FOR NEW FUTURE COHORT' if passed else 'FAIL / NO-GO'}**")
    lines+=["",
       "Each simultaneous interval only corrects eight comparisons within THIS screen; "
       "earlier many candidate searches and viewed March VALIDATION/TEST, Oct/Nov labels "
       "make all winner claims exploratory. 70 series are the meaningful independent units, "
       "not 5,081 IID observations. No source receive_at means no actual real-time PIT proof.",
       "The apparent feature importances and ECE are descriptive; no automated "
       "post-TEST calibration or tuned model selection.",
       "The original notebook and 3,836 TEST predictions were unchanged; the report and reviewer ZIP were rebuilt to disclose the parser correction.",
       ""]
    return "\n".join(lines)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write",action="store_true")
    mode.add_argument("--check",action="store_true")
    args=ap.parse_args()
    receipt=evaluate()
    text=readout(receipt)
    if args.write:
        if RECEIPT.exists() or READOUT.exists():
            raise FileExistsError("Do not overwrite original scoring receipt")
        RECEIPT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n")
        READOUT.write_text(text)
        print(text)
    else:
        if RECEIPT.read_text()!=json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n":
            raise AssertionError("Fresh rerun differs from frozen boosting receipt")
        if READOUT.read_text()!=text:
            raise AssertionError("Fresh readout differs from frozen boosting report")
        print("BYTE_EXACT_BOOSTED_REPLAY_PASS")
