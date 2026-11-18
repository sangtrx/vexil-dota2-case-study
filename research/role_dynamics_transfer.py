#!/usr/bin/env python3
"""Exactly 3 new fixed fitted player-role models + fixed 50:50 forecast pool.

Previously seen October and November cohorts are used only for an exploratory
transfer/falsification, not employer promotion, no refitting to outcomes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from all_family_features import build_frozen_train
from all_family_models import INPUTS, verify_original_artifacts
from oct_nov_feature_transfer import SCOPE, load_raw_octnov
from rich_feature_models import create_pipeline,load_train,proper
from role_dynamics_features import (
    ALL6,RANK3,COUPLING3,asof_role_rows,add_train_role_features,
)
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"research/ROLE_DYNAMICS_PROTOCOL_20261118.md"
OUT=ROOT/"research/ROLE_DYNAMICS_TRANSFER_RECEIPT.json"
READOUT=ROOT/"research/ROLE_DYNAMICS_TRANSFER_READOUT.md"
EXISTING=ROOT/"research/OCT_NOV_FEATURE_TRANSFER_RECEIPT.json"

BASES=("M0_gold","M1_interaction","Q1_path","ALL")
NEW=("RANK3","COUPLING3","RANK_COUPLING6","CONSENSUS")
INPUTS_NEW={
    "RANK3":INPUTS["M1_interaction"]+list(RANK3),
    "COUPLING3":INPUTS["M1_interaction"]+list(COUPLING3),
    "RANK_COUPLING6":INPUTS["M1_interaction"]+list(ALL6),
}
FITTED=BASES+tuple(INPUTS_NEW)
ALL_MODELS=FITTED+("CONSENSUS",)
DRAWS=5000
SEED=20261118


def later_role_rows(spec:dict,frame:pd.DataFrame)->tuple[pd.DataFrame,dict]:
    root=spec["root"]
    all_rows=[]
    match_count=0
    for match,part in frame.groupby("match_id",sort=False):
        match_id=int(match)
        raw=json.loads(gzip.decompress(
            (root/"accepted_raw"/(str(match_id)+".json.gz")).read_bytes()))
        minutes=sorted(int(x) for x in part.minute)
        all_rows.extend(asof_role_rows(match_id,raw,minutes))
        match_count+=1
    later=pd.DataFrame(all_rows)
    if (later[["match_id","minute"]].duplicated().any()
        or len(later)!=len(frame) or match_count!=spec["n_games"]):
        raise AssertionError("Later-player sources incomplete or duplicated")
    merged=frame.merge(later,on=["match_id","minute"],
                       how="left",sort=False,validate="one_to_one")
    if len(merged)!=len(frame) or merged[list(ALL6)].isna().any().any():
        raise AssertionError("Later-player features missing")
    return merged,{
       "matches_checked":match_count,
       "asof_minute_rows":len(later),
       "side_mirror_checks":len(later),
       "no_new_network_calls":True,
    }


def proper_for_prob(y,p)->tuple[np.ndarray,np.ndarray]:
    pred=np.asarray(p,dtype=float)
    if not np.isfinite(pred).all() or (pred<=0).any() or (pred>=1).any():
        raise AssertionError("Out-of-bounds probability")
    return proper(np.asarray(y,dtype=int),pred)


def paired_series(rows:pd.DataFrame,left:str,right:str,indices:np.ndarray)->dict:
    delta=(rows["ll_"+left]-rows["ll_"+right]).to_numpy(float)
    d_brier=(rows["br_"+left]-rows["br_"+right]).to_numpy(float)
    buckets=pd.DataFrame({
        "group":cluster_ids(rows[["match_id","series_id"]]),
        "n":np.ones(len(rows),dtype=float),
        "sl":delta,"sb":d_brier})
    grouped=buckets.groupby("group",sort=True)[["n","sl","sb"]].sum().to_numpy(dtype=float)
    groups=len(grouped)
    if indices.shape!=(DRAWS,groups):
        raise AssertionError("Cluster bootstrap shape drift")
    chosen=grouped[indices].sum(axis=1)
    samples=chosen[:,1:]/chosen[:,0,None]
    if not np.isfinite(samples).all():
        raise AssertionError("Paired bootstrap invalid")
    leave=np.asarray([
        (grouped[:,1].sum()-v[1])/(grouped[:,0].sum()-v[0])
        for v in grouped],dtype=float)
    late=rows.minute.to_numpy(int)>=30
    if not late.any():
        raise AssertionError("Missing 30+ phase")
    p=(pd.DataFrame({"match":rows.match_id,"delta":delta})
       .groupby("match",sort=True).delta.mean())
    positive=np.clip(-grouped[:,1],0,None)
    total_positive=-delta.sum()
    return {
        "minute_mean_delta_logloss":float(delta.mean()),
        "minute_mean_delta_brier":float(d_brier.mean()),
        "late30_delta_brier":float(d_brier[late].mean()),
        "equal_match_delta_logloss":float(p.mean()),
        "series_bootstrap_95_ll":np.quantile(samples[:,0],[.025,.975]).tolist(),
        "series_bootstrap_99375_ll":np.quantile(samples[:,0],[.003125,.996875]).tolist(),
        "leave_one_series_out_range": [float(leave.min()),float(leave.max())],
        "largest_positive_series_share":
             float(positive.max()/total_positive) if total_positive>0 else None,
    }


def evaluate()->dict:
    if not PROTO.exists():
        raise AssertionError("Frozen pre-scoring protocol missing")
    original_files=verify_original_artifacts()
    march,prov=load_train()
    enriched,old_features=build_frozen_train(march)
    enriched,new_source=add_train_role_features(enriched)
    saved=json.loads(EXISTING.read_text())
    if len(FITTED)!=7 or len(ALL_MODELS)!=8 or tuple(ALL6)!=RANK3+COUPLING3:
        raise AssertionError("Unregistered model family variant")
    models={}
    for name in FITTED:
        columns=INPUTS_NEW.get(name,INPUTS.get(name))
        models[name]=create_pipeline(name)
        models[name].fit(enriched[columns],enriched.radiant_win.astype(int))

    result={}
    ids=[]
    for cohort,spec in SCOPE.items():
        later,previous,source=load_raw_octnov(cohort,spec)
        later,side= later_role_rows(spec,later)
        source.update(side)
        ids.append(set(later.match_id.astype(int)))
        y=later.radiant_win.to_numpy(dtype=int)
        scores={}
        pred={}
        for name in FITTED:
            cols=INPUTS_NEW.get(name,INPUTS.get(name))
            p=models[name].predict_proba(later[cols])[:,1]
            pred[name]=p
        pred["CONSENSUS"]=0.5*pred["M1_interaction"]+0.5*pred["Q1_path"]
        if not np.allclose(pred["CONSENSUS"],
                           0.5*(pred["M1_interaction"]+pred["Q1_path"]),
                           rtol=0,atol=0):
            raise AssertionError("Unfitted 50-50 pool mutated")
        for name in ALL_MODELS:
            ll,br=proper_for_prob(y,pred[name])
            later["ll_"+name]=ll
            later["br_"+name]=br
            late=later.minute.to_numpy(int)>=30
            scores[name]={
               "logloss":float(ll.mean()),
               "brier":float(br.mean()),
               "late30_brier":float(br[late].mean()),
               "equal_match_logloss":float(
                   pd.DataFrame({"match":later.match_id,"ll":ll})
                   .groupby("match").ll.mean().mean()),
            }
            if name in BASES:
                was=saved["cohorts"][cohort]["period_scoring"][name]
                for score in ("logloss","brier","late30_brier","equal_match_logloss"):
                    if not np.isclose(scores[name][score],was[score],rtol=0,atol=1e-10):
                        raise AssertionError("Previously verified "+cohort+" "+name+" "+score+" parity failed")

        for name,previous_field in (("M0_gold","p_M0"),("M1_interaction","p_M1")):
            if float(np.max(np.abs(pred[name]-previous[previous_field].to_numpy(float))))>1e-7:
                raise AssertionError("Original prior saved probability parity failed")

        groups=len(set(cluster_ids(later[["match_id","series_id"]])))
        if groups!=spec["n_series"]:
            raise AssertionError("Original professional-series groups changed")
        indices=np.random.default_rng(SEED).integers(0,groups,size=(DRAWS,groups))
        compared={}
        for name in NEW:
            compared[name]={}
            for rival in ("Q1_path","M1_interaction"):
                compared[name][rival]=paired_series(later,name,rival,indices)

        cohort_test={}
        for name in NEW:
            cohort_test[name]=bool(all(
                compared[name][r]["minute_mean_delta_logloss"]<=-.005
                and compared[name][r]["series_bootstrap_99375_ll"][1]<0
                and compared[name][r]["minute_mean_delta_brier"]<=0
                and compared[name][r]["late30_delta_brier"]<=0
                for r in ("Q1_path","M1_interaction")
            ))
        result[cohort]={
            "source_checks":source,
            "scores":scores,
            "paired_comparisons":compared,
            "per_cohort_strict_research_gate":cohort_test,
            "n_independent_series":groups,
        }
    if ids[0]&ids[1] or ids[0]&set(enriched.match_id.astype(int)) or ids[1]&set(enriched.match_id.astype(int)):
        raise AssertionError("Study cohorts overlapping fitted March data")
    gate={k:all(result[period]["per_cohort_strict_research_gate"][k] for period in SCOPE)
          for k in NEW}
    if verify_original_artifacts()!=original_files:
        raise AssertionError("Employer source data changed")
    return {
        "scientific_class":"historical after extensive model search; not blind",
        "models":{k:INPUTS_NEW[k] for k in INPUTS_NEW}|{"CONSENSUS":"0.5 M1 + 0.5 Q1 (unfitted)"},
        "march_original_train_sha256":prov["source_train_sha256"],
        "march_prior_source":old_features,
        "march_new_role_source":new_source,
        "protocol_sha256":hashlib.sha256(PROTO.read_bytes()).hexdigest(),
        "cohorts":result,
        "strict_future_research_gate_both_periods":gate,
        "bootstrap_draws":DRAWS,
        "bootstrap_seed":SEED,
        "candidate_count":4,
        "comparisons_per_period":8,
        "never_inspected_test":False,
        "received_at_verified":False,
        "no_external_api_calls":True,
        "employer_submission_unchanged":True,
        "protected_file_hashes":original_files,
    }


def report(res:dict)->str:
    lines=[
     "# Role redistribution, gold-XP coupling and forecast consensus",
     "",
     "**Post-result, nonblind historical research. Four fixed challengers scored without reselecting, "
     "one fitting on March TRAIN only. Negative findings retained.**",
     "",
     "| Cohort | Model | Minute LL | Brier | 30+ Brier | Equal-game LL |",
     "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for cohort in ("October","November"):
        r=res["cohorts"][cohort]
        for name in ALL_MODELS:
            row=r["scores"][name]
            lines.append(f"| {cohort} | {name} | {row['logloss']:.6f} | "
                         f"{row['brier']:.6f} | {row['late30_brier']:.6f} | "
                         f"{row['equal_match_logloss']:.6f} |")
    lines+=["",
       "## Comparisons: negative logloss difference is better than comparator",
       "",
       "| Cohort | Candidate | vs | Delta LL | 95% series CI | 99.375% series CI | "
       "Equal-game LL delta | Brier delta | 30+ Brier delta | Leave-one-series-out LL range |",
       "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |"]
    for cohort in ("October","November"):
        r=res["cohorts"][cohort]
        for name in NEW:
            for comp in ("Q1_path","M1_interaction"):
                v=r["paired_comparisons"][name][comp]
                x,y=v["series_bootstrap_95_ll"]
                a,b=v["series_bootstrap_99375_ll"]
                l,h=v["leave_one_series_out_range"]
                lines.append(f"| {cohort} | {name} | {comp} | "
                 f"{v['minute_mean_delta_logloss']:+.6f} | [{x:+.6f},{y:+.6f}] | "
                 f"[{a:+.6f},{b:+.6f}] | {v['equal_match_delta_logloss']:+.6f} | "
                 f"{v['minute_mean_delta_brier']:+.6f} | "
                 f"{v['late30_delta_brier']:+.6f} | [{l:+.6f},{h:+.6f}] |")
    lines+=["",
      "## Results gating / source constraints",
      "",
      "- Strict dual-period gate (requires >=0.005 logloss gain versus M1 and Q1, "
      "paired 99.375% series bootstrap upper<0, no Brier/30+ regression, in BOTH later cohorts): "
      +str(res["strict_future_research_gate_both_periods"])+".",
      "- These are previously read October/November cohorts; per-screen Bonferroni 99.375% intervals "
      "do NOT correct earlier repeated screens and do not constitute prospective validation.",
      "- All 291 March TRAIN matches used to fit each fixed logistic model. "
      "October and November outcomes never used in feature fitting, scaling or calibration. "
      "CONSENSUS is a fixed 0.5/0.5 probability average, no fitted gate.",
      "- Per-player earned-gold and XP arrays must be source-aligned, as-of current minute, "
      "roster/side symmetric, group-invariant. They are NOT actual current item net worth.",
      "- The two later cohorts and raw source manifest were previously verified; no new HTTP. "
      "True feature receipt timestamp is not available. No claims of live model reliability.",
      "- The employer notebook, 4-page report, reviewer ZIP, original March TEST and Draft PR #9 "
      "were not changed.",
      "",
      "**Decision:** These additional mechanisms may inform later prospective science; "
      "no changes to the employer-ready required gold-only baseline or prior model decisions.",
      ""]
    return "\n".join(lines)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    result=evaluate()
    print(report(result))
    if args.write:
        OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        READOUT.write_text(report(result))
