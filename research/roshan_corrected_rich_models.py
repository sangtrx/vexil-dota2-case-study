#!/usr/bin/env python3
"""Post-result re-evaluation of the historical fixed 84-input models after repairing Roshan team attribution.

Uses only original TRAIN folds, not original VALIDATION or TEST. Earlier scores remain archived separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from conditional_gold_forward import FROZEN_CUTS
from train_time_effect_ci import cluster_ids, model as original_model, require_data
from quant_bible_path_risk_train_only import prefix_path_features
from rich_feature_engineering import BASE, FEATURES, FAMILIES, PROVENANCE, RICH

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_RECEIPT.json"
READOUT = ROOT / "research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_READOUT.md"
PRIOR = ROOT / "research/QUANT_BIBLE_PATH_RECEIPT.json"
MODELS = {
    "M0_gold": ["gold_k"],
    "A_additive": ["gold_k","minute10"],
    "M1_interaction": BASE,
    "Q1_path": ["gold_k","minute10","adverse_excursion10_k",
                "signed_realized_vol10_k","directional_efficiency10"],
    "Q2_sparse": BASE + RICH,
    "Q3_tree": BASE + RICH,
}
CANDIDATES = ("Q2_sparse", "Q3_tree")
CONTROLS = ("M1_interaction", "Q1_path")
DRAWS = 5000
SEED = 20261115


def attach_q1(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.sort_values(["match_id","minute"], kind="stable").copy()
    vals = np.empty((len(ordered),3), dtype=float)
    for _, subset in ordered.groupby("match_id", sort=False):
        mins = subset.minute.to_numpy(int)
        if not np.array_equal(mins, np.arange(len(subset))):
            raise ValueError("Original Q1 minute grid changed")
        g = subset.gold_k.to_numpy(float)
        for idx,t in zip(subset.index,mins):
            vals[ordered.index.get_loc(idx)] = prefix_path_features(g[:t+1])
    for j,col in enumerate(MODELS["Q1_path"][2:]):
        ordered[col] = vals[:,j]
    return ordered


def load_train() -> tuple[pd.DataFrame, dict]:
    provenance = json.loads(PROVENANCE.read_text())
    if hashlib.sha256(FEATURES.read_bytes()).hexdigest() != provenance["frozen_feature_csv_sha256"]:
        raise ValueError("81-feature frozen training CSV hash drift")
    if provenance["raw_games_read"]!=291 or provenance["minute_prefixes_checked"]!=10675:
        raise ValueError("Source as-of evidence absent")
    if provenance["families"] != {n:len(v) for n,v in FAMILIES.items()}:
        raise ValueError("Feature-family registry altered")
    df = pd.read_csv(FEATURES, float_precision="round_trip")
    frozen = require_data()
    if len(df)!=10675 or df.match_id.nunique()!=291 or set(df.partition)!={"train"}:
        raise ValueError("Training scope expanded")
    keys = ["match_id","minute","radiant_win","gold_k","minute10",
            "gold_x_time","partition","series_id","start_time","duration"]
    a = df[keys].sort_values(["match_id","minute"]).reset_index(drop=True)
    b = frozen[keys].sort_values(["match_id","minute"]).reset_index(drop=True)
    if not a[["match_id","minute","radiant_win","partition","series_id","start_time","duration"]].equals(
            b[["match_id","minute","radiant_win","partition","series_id","start_time","duration"]]):
        raise ValueError("Frozen training keys or labels changed")
    if not np.allclose(a[BASE],b[BASE],rtol=0,atol=1e-12):
        raise ValueError("Original baseline inputs differ")
    if not set(RICH).issubset(df):
        raise ValueError("Engineered features missing")
    if not np.isfinite(df[RICH].to_numpy(dtype=float)).all():
        raise ValueError("NaN in engineered inputs")
    return attach_q1(df), provenance


def create_pipeline(name: str) -> Pipeline:
    if name=="Q2_sparse":
        return Pipeline([
            ("imputer",SimpleImputer(strategy="median",keep_empty_features=True)),
            ("scale",StandardScaler()),
            ("model",LogisticRegression(
                penalty="elasticnet", solver="saga", C=0.08, l1_ratio=0.70,
                max_iter=3000, tol=0.001, random_state=20261113)),
        ])
    if name=="Q3_tree":
        return Pipeline([
            ("imputer",SimpleImputer(strategy="median",keep_empty_features=True)),
            ("model",HistGradientBoostingClassifier(
                max_iter=70, max_leaf_nodes=7, learning_rate=0.04,
                min_samples_leaf=250, l2_regularization=30,
                early_stopping=False, random_state=20261113)),
        ])
    return original_model()


def proper(y,p):
    if not (np.isfinite(p).all() and np.all((p>0)&(p<1))):
        raise ValueError("Nonfinite or boundary probability")
    return -(y*np.log(p)+(1-y)*np.log1p(-p)), (p-y)**2


def cluster_bootstrap(rows: pd.DataFrame, candidate: str, comparator: str) -> dict:
    delta_ll = rows["ll_"+candidate].to_numpy()-rows["ll_"+comparator].to_numpy()
    delta_br = rows["br_"+candidate].to_numpy()-rows["br_"+comparator].to_numpy()
    group = rows[["match_id","series_id"]].copy()
    group["key"] = cluster_ids(group)
    group["ll"] = delta_ll
    group["br"] = delta_br
    groups = group.groupby("key",sort=True).agg(
        n=("match_id","size"), ll=("ll","sum"), br=("br","sum"))
    if len(groups)!=70:
        raise ValueError("Expected 70 series or singletons")
    a = groups[["n","ll","br"]].to_numpy(float)
    rng = np.random.default_rng(SEED)
    ids = rng.integers(0,len(a),size=(DRAWS,len(a)))
    sums = a[ids].sum(axis=1)
    estimates=sums[:,1:]/sums[:,0,None]
    if not np.isfinite(estimates).all():
        raise ValueError("Invalid group bootstrap")
    lo95=np.quantile(estimates,[.025,.975],axis=0)
    bonf=np.quantile(estimates,[.0125,.9875],axis=0)
    late=(rows.minute.to_numpy(int)>=30)
    overall_gain=-float(delta_ll.sum())
    positive=(-groups.ll).clip(lower=0)
    concentration=float(positive.max()/overall_gain) if overall_gain>0 else None
    return {
        "delta_logloss":float(delta_ll.mean()),
        "delta_brier":float(delta_br.mean()),
        "late30_delta_brier":float(delta_br[late].mean()),
        "ll_ci95_series":lo95[:,0].tolist(),
        "ll_ci975_two_candidates":bonf[:,0].tolist(),
        "brier_ci95_series":lo95[:,1].tolist(),
        "largest_positive_series_share":concentration,
    }


def evaluate() -> dict:
    df,provenance=load_train()
    meta=df[["match_id","start_time","duration","series_id"]].drop_duplicates()
    meta=meta.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
    old=json.loads(PRIOR.read_text())
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise ValueError("Train-forward geometry drift")
    if old["oof_games"]!=137 or len(old["folds"])!=4:
        raise ValueError("Q1 original evidence missing")
    folds=[]
    reports=[]
    for k,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        before=meta.iloc[:left]
        current=meta.iloc[left:right]
        cutoff=int(current.iloc[0].start_time)
        fit_meta=before[before.start_time+before.duration<=cutoff]
        if set(cluster_ids(before)) & set(cluster_ids(current)):
            raise ValueError("Series crosses nominal temporal boundary")
        if set(cluster_ids(fit_meta)) & set(cluster_ids(current)):
            raise ValueError("Mature labels cross series boundary")
        past=df[df.match_id.isin(set(fit_meta.match_id))]
        ev=df[df.match_id.isin(set(current.match_id))]
        if not len(past) or not len(ev) or set(past.match_id)&set(ev.match_id):
            raise ValueError("Forward evaluation overlap")
        y=ev.radiant_win.to_numpy(float)
        saved=ev[["match_id","series_id","minute"]].copy()
        fold={
            "fold":k,"completed_fit_games":len(fit_meta),
            "eval_games":len(current),"eval_rows":len(ev),
            "maturity_embargo_games":len(before)-len(fit_meta),
        }
        for name,cols in MODELS.items():
            with warnings.catch_warnings():
                warnings.simplefilter("error",ConvergenceWarning)
                fitted=create_pipeline(name).fit(past[cols],past.radiant_win.astype(int))
            prob=fitted.predict_proba(ev[cols])[:,1]
            ll,br=proper(y,prob)
            saved["ll_"+name]=ll
            saved["br_"+name]=br
            fold[name]={"logloss":float(ll.mean()),"brier":float(br.mean())}
            if name=="Q2_sparse":
                weights=fitted.named_steps["model"].coef_[0]
                active={col for col,v in zip(cols,weights) if abs(v)>1e-8}
                fold[name]["nonzero_features"]=len(active)
                fold[name]["nonzero_families"]={
                    group:len(active.intersection(features))
                    for group,features in FAMILIES.items()}
        previous=old["folds"][k-1]
        for control in ("M0_gold","A_additive","M1_interaction","Q1_path"):
            for metric in ("logloss","brier"):
                if not math.isclose(
                    fold[control][metric],previous[control][metric],
                    abs_tol=1e-10,rel_tol=0):
                    raise AssertionError("Historical "+control+" parity failed")
        folds.append(fold)
        reports.append(saved)
    oof=pd.concat(reports,ignore_index=True)
    if (len(oof)!=5081 or oof.match_id.nunique()!=137
        or len(set(cluster_ids(oof)))!=70
        or oof[["match_id","minute"]].duplicated().any()):
        raise ValueError("Historical TRAIN OOF geometry drift")
    comparative={}
    for name in CANDIDATES:
        comparative[name]={}
        for rival in ("M0_gold","A_additive","M1_interaction","Q1_path"):
            score=cluster_bootstrap(oof,name,rival)
            score["better_forward_folds"]=sum(
                f[name]["logloss"]<f[rival]["logloss"] for f in folds)
            comparative[name][rival]=score
    def gate(name):
        for rival in CONTROLS:
            x=comparative[name][rival]
            if not (x["delta_logloss"]<=-0.003
                    and x["ll_ci975_two_candidates"][1]<0
                    and x["better_forward_folds"]>=3
                    and x["delta_brier"]<=0
                    and x["late30_delta_brier"]<=0):
                return False
        share=comparative[name]["M1_interaction"]["largest_positive_series_share"]
        return share is not None and share<.50
    return {
        "scope":"POST_RESULT_TRAIN_ONLY_NOT_FRESH_TEST",
        "original_VAL_or_TEST_labels_loaded":False,
        "original_notebook_and_test_predictions_changed":False,
        "report_and_zip_rebuilt_after_correction":True,
        "raw_payload_manifest_sha256":provenance["source_payload_bytes_sha256"],
        "engineered_train_sha256":provenance["frozen_feature_csv_sha256"],
        "feature_family_sizes":provenance["families"],
        "new_feature_count":len(RICH),
        "wide_input_count":len(BASE+RICH),
        "models":MODELS,
        "folds":folds,
        "rows_evaluated":len(oof),
        "games_evaluated":oof.match_id.nunique(),
        "group_count":len(set(cluster_ids(oof))),
        "bootstrap_draws":DRAWS,
        "bootstrap_seed":SEED,
        "comparisons":comparative,
        "future_candidate_gate":{name:gate(name) for name in CANDIDATES},
    }


def make_readout(receipt:dict)->str:
    lines=[
        "# Roshan-corrected 84-input models: TRAIN-only sensitivity",
        "",
        "**Scope:** Post-result TRAIN-only exploration. Already-viewed original"
        " TEST and VALIDATION results never enter this evaluation. The"
        " predeclared two-model correction does NOT correct the previous"
        " 28+ research-model screens.",
        "",
        "291 TRAIN games supplied 10,675 minute snapshots; the frozen"
        " forward evaluation uses 137 games, 5,081 rows and 70"
        " professional series/singleton groups.",
        "",
        "## Implemented feature families",
        "",
        "| Family | Columns |",
        "| --- | ---: |",
    ]
    lines += [f"| {k} | {v} |" for k,v in receipt["feature_family_sizes"].items()]
    lines += [
        "",
        "Two fixed 84-input candidates: Q2 elastic-net logistic and"
        " Q3 shallow gradient-boosted trees. Baselines M0, additive,"
        " original M1 and earlier Q1 are re-fitted without tuning.",
        "",
        "## Out-of-fold (historical TRAIN) score comparisons",
        "",
        "Negative Q-minus-baseline score means candidate wins."
        " All intervals are paired bootstrap over 70 professional"
        " series/singletons; 97.5% interval is a narrowly two-candidate"
        " Bonferroni adjustment only.",
        "",
        "| Candidate | Baseline | LL delta | LL 95% CI | LL 97.5% CI | Brier delta | 30+ Brier delta | Winning folds |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    def interval(xs):return "["+",".join(f"{v:+.6f}" for v in xs)+"]"
    for name,comp in receipt["comparisons"].items():
        for rival,x in comp.items():
            lines.append(
                f"| {name} | {rival} | {x['delta_logloss']:+.6f} |"
                f" {interval(x['ll_ci95_series'])} |"
                f" {interval(x['ll_ci975_two_candidates'])} |"
                f" {x['delta_brier']:+.6f} |"
                f" {x['late30_delta_brier']:+.6f} |"
                f" {x['better_forward_folds']}/4 |")
    lines.extend([
        "",
        "## Every forward block (not cherry-picked)",
        "",
        "| Fold | Games | Q2 LL | Q3 LL | M1 LL | Q1 LL | Q2 active / 84 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for f in receipt["folds"]:
        lines.append(
            f"| {f['fold']} | {f['eval_games']} |"
            f" {f['Q2_sparse']['logloss']:.6f} |"
            f" {f['Q3_tree']['logloss']:.6f} |"
            f" {f['M1_interaction']['logloss']:.6f} |"
            f" {f['Q1_path']['logloss']:.6f} |"
            f" {f['Q2_sparse']['nonzero_features']} |")
    lines.extend([
        "",
        "## Locked outcome",
        "",
        "| Model | Future-candidate gate | Largest favorable group / total M1 LL gain |",
        "| --- | --- | ---: |",
    ])
    for name,passed in receipt["future_candidate_gate"].items():
        share=receipt["comparisons"][name]["M1_interaction"]["largest_positive_series_share"]
        lines.append(f"| {name} | {'MET' if passed else 'FAILED'} | "
                     + (f"{share:.1%} |" if share is not None else "n/a |"))
    lines.extend([
        "",
        "Important: model feature importance is diagnostic only."
        " Correlated engineered signals are not evidence of causal"
        " influence. The real-time feed receipt timestamp is unknown;"
        " a historical replay cannot establish true received-at time.",
        "",
        "The submitted notebook and original 3,836 TEST predictions were"
        " unchanged. The report and reviewer ZIP were rebuilt on 19 November"
        " to disclose this parser correction; no newly blind TEST is claimed.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--write",action="store_true")
    opts.add_argument("--check",action="store_true")
    args=parser.parse_args()
    data=evaluate()
    text=make_readout(data)
    if args.write:
        RECEIPT.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+"\n")
        READOUT.write_text(text)
        print("WROTE",RECEIPT.name,READOUT.name)
    else:
        if data!=json.loads(RECEIPT.read_text()) or text!=READOUT.read_text():
            raise AssertionError("Rich model evaluation receipt not reproducible")
        print("PASS: 84-input fixed models and historical baseline oracles")
    for name in CANDIDATES:
        print("MODEL",name,"FUTURE_CANDIDATE_GATE",data["future_candidate_gate"][name])
        for rival in CONTROLS:
            x=data["comparisons"][name][rival]
            print(" VS",rival,"LL",round(x["delta_logloss"],6),
                "CI97.5",x["ll_ci975_two_candidates"],
                "BRIER",round(x["delta_brier"],6),
                "FOLDS",x["better_forward_folds"])


if __name__=="__main__":
    main()
