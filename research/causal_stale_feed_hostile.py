#!/usr/bin/env python3
"""Honest NO_DATA prefix handling under hypothetical 1/3 minute packet delay.

WARNING: This is a post-result diagnostic on the ALREADY SCORED Nov17 cohort.
No raw receive timestamps or live ingress latency were measured. No model fit
on Nov17 and no employer deliverable/PR edit.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from all_family_models import verify_original_artifacts
from fresh_nov17_external import (
    DATA,LOCK,MODELS,ROOT,SEED,DRAWS,
    frame_for_score,freeze_models,
    metrics_and_ci,
)
from minimal_economy_scoring import INPUTS
from quant_bible_path_risk_train_only import prefix_path_features
from rich_feature_models import proper
from train_time_effect_ci import cluster_ids

PROTOCOL=ROOT/"research/CAUSAL_STALE_FEED_HOSTILE_PROTOCOL_20261118.md"
OLD=ROOT/"research/FRESH_NOV17_EXTERNAL_RECEIPT.json"
FROZEN_SOURCE=ROOT/"research/FRESH_NOV17_SOURCE_RECEIPT.json"
RESULT=ROOT/"research/CAUSAL_STALE_FEED_HOSTILE_RECEIPT.json"
READOUT=ROOT/"research/CAUSAL_STALE_FEED_HOSTILE_READOUT.md"
LAGS=(1,3)
POLICIES=("FRESH","CLOCK1","HOLD1","CLOCK3","HOLD3")
REVIEW=ROOT/"research/CAUSAL_STALE_FEED_HOSTILE_REVIEW.md"


def sha_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def staleness_frame(frame:pd.DataFrame,lag:int)->tuple[pd.DataFrame,np.ndarray,np.ndarray]:
    """At time t only full snapshots <=t-lag are available.

    All t<lag are NO_DATA: returned feature fill zeros are sentinel placeholders
    and MUST NOT be passed to the model. Caller selects only available rows.
    old_index = -1 specifically means unavailable; never clamped to zero.
    """
    if not isinstance(lag,int) or lag<0 or lag not in (0,1,3):
        raise ValueError("Only registered fixed lags 0, 1, 3 supported")
    required={"match_id","minute","minute10","gold_k","gold_x_time"}
    if not required.issubset(frame) or len(frame)==0 or frame[["match_id","minute"]].duplicated().any():
        raise ValueError("Invalid duplicate or incomplete source frame")
    if not np.array_equal(frame.index.to_numpy(),np.arange(len(frame))):
        raise AssertionError("Require continuous integer index for old-row mapping")
    x=frame[["match_id","minute","minute10","gold_k","gold_x_time"]].copy()
    for k in INPUTS["Q1_path"][2:]:
        x[k]=0.0
    x["gold_k"]=0.0
    x["gold_x_time"]=0.0
    old_index=np.full(len(frame),-1,dtype=int)
    available=np.zeros(len(frame),dtype=bool)
    for _,grp in frame.groupby("match_id",sort=False):
        idx=grp.index.to_numpy(int)
        minute=grp.minute.to_numpy(int)
        if not np.array_equal(minute,np.arange(len(grp))):
            raise AssertionError("Per-game minute history has gaps/reorder")
        g=grp.gold_k.to_numpy(float)
        clock=grp.minute10.to_numpy(float)
        if (not np.isfinite(g).all() or not np.isfinite(clock).all()
            or not np.allclose(clock,minute/10,rtol=0,atol=1e-12)
            or not np.allclose(grp.gold_x_time.to_numpy(float),
                               g*np.log1p(clock),rtol=0,atol=1e-12)):
            raise AssertionError("Invalid original gold/interaction prefix")
        for i,t in enumerate(minute):
            target=idx[i]
            s=int(t-lag)
            if s<0:
                continue
            source_index=idx[s]
            old_index[target]=source_index
            available[target]=True
            gold_old=float(g[s])
            x.loc[target,"gold_k"]=gold_old
            x.loc[target,"gold_x_time"]=gold_old*math.log1p(float(clock[i]))
            q=prefix_path_features(g[:s+1])
            for j,k in enumerate(INPUTS["Q1_path"][2:]):
                x.loc[target,k]=float(q[j])
            if s>t-lag or s>t or source_index not in idx:
                raise AssertionError("Stale source crossed availability or game boundary")
    if int((~available).sum())!=sum(min(lag,len(part)) for _,part in frame.groupby("match_id")):
        raise AssertionError("NO_DATA state count changed")
    if not np.array_equal(old_index>=0,available):
        raise AssertionError("Available records and old-pointer states disagree")
    if lag==0:
        if not available.all() or not np.array_equal(old_index,np.arange(len(frame))):
            raise AssertionError("Zero-lag freshness parity missing")
        for k in INPUTS["M1_interaction"]+INPUTS["Q1_path"][2:]:
            if not np.allclose(x[k].to_numpy(float),frame[k].to_numpy(float),
                               atol=1e-12,rtol=0):
                raise AssertionError("FRESH duplicate source differs for column "+k)
    return x,old_index,available


def impossible_future_one(frame:pd.DataFrame,m)->dict:
    """Deliberately INVALID +1 minute future-gold negative control."""
    x,_,available=staleness_frame(frame,0)
    candidate=np.zeros(len(frame),dtype=bool)
    for _,grp in frame.groupby("match_id",sort=False):
        idx=grp.index.to_numpy(int)
        g=grp.gold_k.to_numpy(float)
        clock=grp.minute10.to_numpy(float)
        for t in range(len(idx)-1):
            i=idx[t]
            later=float(g[t+1])
            candidate[i]=True
            x.loc[i,"gold_k"]=later
            x.loc[i,"gold_x_time"]=later*math.log1p(float(clock[t]))
    if not np.array_equal(available,np.ones(len(frame),dtype=bool)):
        raise AssertionError("Negative control expected complete unlagged history")
    if int(candidate.sum())!=len(frame)-frame.match_id.nunique():
        raise AssertionError("Future sentinel includes illegal terminal next sample")
    y=frame.radiant_win.to_numpy(int)
    current=m.predict_proba(frame[list(INPUTS["MATCH_EQUAL"])])[:,1]
    impossible=m.predict_proba(x.loc[candidate,list(INPUTS["MATCH_EQUAL"])])[:,1]
    current_ll,_=proper(y[candidate],current[candidate])
    impossible_ll,_=proper(y[candidate],impossible)
    return {
        "label":"IMPOSSIBLE future minute snapshot, deliberately invalid, diagnostic only",
        "valid_nonterminal_rows":int(candidate.sum()),
        "future_minus_fresh_logloss":float((impossible_ll-current_ll).mean()),
        "future_logloss":float(impossible_ll.mean()),
        "fresh_same_rows_logloss":float(current_ll.mean()),
        "never_a_candidate":True,
    }


def eval_all()->dict:
    for file in (PROTOCOL,LOCK,OLD,FROZEN_SOURCE,DATA/"source_receipt.json"):
        if not file.exists():
            raise FileNotFoundError("Missing preregistered source "+str(file))
    if sha_file(FROZEN_SOURCE)!=sha_file(DATA/"source_receipt.json"):
        raise AssertionError("GitHub archived source receipt changed")
    source=json.loads(FROZEN_SOURCE.read_text())
    previous=json.loads(OLD.read_text())
    old_lock=json.loads(LOCK.read_text())
    models,lock=freeze_models()
    if lock["models"]!=old_lock["models"] or lock["employer_artifacts"]!=old_lock["employer_artifacts"]:
        raise AssertionError("Frozen March model changed")
    if verify_original_artifacts()!=old_lock["employer_artifacts"]:
        raise AssertionError("Original employer files mutated")
    frame=frame_for_score(source)
    if (len(frame)!=711 or frame.match_id.nunique()!=17
        or len(set(cluster_ids(frame[["match_id","series_id"]])))!=10
        or frame.leagueid.nunique()!=4):
        raise AssertionError("Frozen post-selection Nov17 cohort changed")
    y=frame.radiant_win.to_numpy(int)
    late=frame.minute.to_numpy(int)>=30
    views={}
    old_index={}
    available={}
    for lag in (0,)+LAGS:
        views[lag],old_index[lag],available[lag]=staleness_frame(frame,lag)
    table=frame[["match_id","series_id","minute"]].copy()
    rows={}
    probs={}
    for name in MODELS:
        model=models[name]
        reference=model.predict_proba(frame[list(INPUTS[name])])[:,1]
        x=probs[name]={"FRESH":reference}
        for lag in LAGS:
            use=available[lag]
            clock=np.full(len(frame),.5,dtype=float)
            hold=np.full(len(frame),.5,dtype=float)
            clock[use]=model.predict_proba(views[lag].loc[use,list(INPUTS[name])])[:,1]
            hold[use]=reference[old_index[lag][use]]
            if not np.array_equal(clock[~use],np.full((~use).sum(),.5)) or not np.array_equal(hold[~use],np.full((~use).sum(),.5)):
                raise AssertionError("Data unavailable but model output was read")
            if np.any(old_index[lag][use]<0):
                raise AssertionError("Prediction holding referenced unobserved source")
            x["CLOCK"+str(lag)]=clock
            x["HOLD"+str(lag)]=hold
        # Verify fully vectorized fresh equals explicit lag-0 pipeline (strict).
        lag0=model.predict_proba(views[0][list(INPUTS[name])])[:,1]
        if not np.allclose(reference,lag0,atol=1e-12,rtol=0):
            raise AssertionError("Fresh 0-minute lag model probability parity failed")
        rows[name]={}
        for policy in POLICIES:
            p=x[policy]
            ll,br=proper(y,p)
            table["ll_"+name+"_"+policy]=ll
            table["br_"+name+"_"+policy]=br
            row={
                "logloss":float(ll.mean()),
                "equal_match_logloss":float(pd.DataFrame({"match":frame.match_id,"ll":ll}).groupby("match").ll.mean().mean()),
                "brier":float(br.mean()),
                "brier_late30":float(br[late].mean()),
                "no_data_rows":(
                    0 if policy=="FRESH"
                    else int((~available[int(policy[-1])]).sum())
                ),
            }
            rows[name][policy]=row
            if policy=="FRESH":
                old=previous["model_scores"][name]
                for metric,field in (("logloss","minute_logloss"),
                                     ("equal_match_logloss","equal_match_logloss"),
                                     ("brier","minute_brier"),("brier_late30","late30_brier")):
                    if not np.isclose(row[metric],old[field],rtol=0,atol=1e-11):
                        raise AssertionError("Nov17 prior fresh score differs: "+name+"/"+metric)
    contrasts={}
    for policy in POLICIES:
        contrasts[policy]={}
        for ctrl in ("M1_interaction","Q1_path"):
            # Old paired-series routine preserves per-match/series units.
            mname="MATCH_EQUAL_"+policy
            cname=ctrl+"_"+policy
            res=metrics_and_ci(table,mname,cname)
            contrasts[policy][ctrl]=res
        if policy=="FRESH":
            old=previous["paired_match_equal_comparisons"]
            for rival in old:
                for metric in ("equal_match_delta_logloss","minute_delta_logloss","delta_brier","late30_delta_brier"):
                    if not np.isclose(contrasts[policy][rival][metric],old[rival][metric],
                                      atol=1e-11,rtol=0):
                        raise AssertionError("Prior paired series result changed")
    regret={}
    for name in MODELS:
        fresh=rows[name]["FRESH"]
        regret[name]={}
        for policy in POLICIES[1:]:
            x=rows[name][policy]
            regret[name][policy]={
                "delta_logloss_from_fresh":x["logloss"]-fresh["logloss"],
                "delta_equal_match_from_fresh":x["equal_match_logloss"]-fresh["equal_match_logloss"],
                "delta_brier_from_fresh":x["brier"]-fresh["brier"],
                "delta_late30_brier_from_fresh":x["brier_late30"]-fresh["brier_late30"],
            }
    negative=impossible_future_one(frame,models["MATCH_EQUAL"])
    if verify_original_artifacts()!=old_lock["employer_artifacts"]:
        raise AssertionError("Protected applicant files changed during research")
    return {
        "status":"Causal no-data fixes for hypothetical stale feed, post-NOV17 outcome exploratory only",
        "protocol_sha256":sha_file(PROTOCOL),
        "previous_stale_feed_bug":"The old research/stale_feed_reliability.lagged_views reads history[0] at t<lag; not available under delayed source hypothesis",
        "nov17_previously_scored":True,
        "source_hash":sha_file(FROZEN_SOURCE),
        "model_sha":sha_file(LOCK),
        "models":list(MODELS),"lags":list(LAGS),"policies":list(POLICIES),
        "source_scope":{"games":17,"rows":711,"independent_series":10,"leagues":4},
        "state_counts":{
            str(lag):{"NO_DATA":int((~available[lag]).sum()),
                      "DATA_AVAILABLE":int(available[lag].sum())}
            for lag in (0,)+LAGS
        },
        "source_lag_reference_rule":"s=t-lag, never clamped; no data when s<0; current game time t known in CLOCK; HOLD previous forecast at source time s",
        "scores":rows,"match_equal_paired_vs":contrasts,
        "policy_regret_from_fresh":regret,
        "deliberately_impossible_future_one_control":negative,
        "original_high_gate_still_fails":True,
        "true_receipt_timestamp_verified":False,
        "prior_multiple_hypothesis_exploration_corrected":False,
        "employer_artifact_hashes":old_lock["employer_artifacts"],
        "submission_unchanged":True,
    }


def report(r:dict)->str:
    lines=[
        "# Hostile review: missing live snapshot at first minutes, and lag stress",
        "",
        "**Hypothetical stale-gold counterfactual on an ALREADY SCORED 17-game Nov17 cohort.** "
        "Not a live latency measurement or independent candidate confirmation.",
        "",
        "## Correctness repair: do not cheat at minute t < lag",
        "",
        "The existing TRAIN-only stale-feed study used max(0,t-lag), supplying gold[0]/p[0] "
        "before it could have arrived. This research uses **NO_DATA => p=0.5** until t>=lag; "
        "after that CLOCK recomputes at known game clock t with only data through s=t-lag, "
        "while HOLD retains the forecast actually available from s. Old receipt kept intact.",
        "",
        "NO_DATA rows: "+", ".join(
            f"lag {lag}: {r['state_counts'][str(lag)]['NO_DATA']}"
            for lag in (0,)+LAGS)+".",
        "",
        "| Model | Stream | Minute LL | Equal-match LL | Brier | 30+ Brier |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for m in MODELS:
        for policy in POLICIES:
            d=r["scores"][m][policy]
            lines.append(f"| {m} | {policy} | {d['logloss']:.6f} | "
                f"{d['equal_match_logloss']:.6f} | {d['brier']:.6f} | "
                f"{d['brier_late30']:.6f} |")
    lines+=["",
        "## Post-result paired contrasts: MATCH_EQUAL minus control (negative is better)",
        "",
        "| Policy | vs | Equal-match LL delta | 95% series CI | 98.75% series CI | "
        "Minute LL delta | 30+ Brier delta |",
        "| --- | --- | ---: | --- | --- | ---: | ---: |"]
    for policy in POLICIES:
        for control, d in r["match_equal_paired_vs"][policy].items():
            a,b=d["equal_match_95_ci"]
            c,e=d["equal_match_9875_ci"]
            lines.append(f"| {policy} | {control} | "
                         f"{d['equal_match_delta_logloss']:+.6f} | "
                         f"[{a:+.6f},{b:+.6f}] | [{c:+.6f},{e:+.6f}] | "
                         f"{d['minute_delta_logloss']:+.6f} | "
                         f"{d['late30_delta_brier']:+.6f} |")
    lines+=["",
        "## Model regret relative to its own fresh forecasts",
        "",
        "| Model | Delayed stream | LL increase (negative improves) | Late30 Brier change |",
        "| --- | --- | ---: | ---: |"]
    for m in MODELS:
        for policy in POLICIES[1:]:
            d=r["policy_regret_from_fresh"][m][policy]
            lines.append(f"| {m} | {policy} | {d['delta_logloss_from_fresh']:+.6f} | "
                         f"{d['delta_late30_brier_from_fresh']:+.6f} |")
    f=r["deliberately_impossible_future_one_control"]
    lines+=["",
        "## Deliberately impossible future-data sentinel — never use",
        "",
        f"One-minute **future** MATCH_EQUAL economic lead on {f['valid_nonterminal_rows']} "
        f"nonterminal rows changed log loss vs proper fresh predictor by "
        f"**{f['future_minus_fresh_logloss']:+.6f}**. This is a leakage sensitivity "
        "diagnostic, not a valid prediction technique or live advantage.",
        "",
        "## Hostile decision",
        "",
        "- Previous frozen research superiority gate remains **FAIL**, regardless of simulated delay. "
        "This cohort has 17 games/10 independent clusters, less than 30/15 required.",
        "- All four March-trained models fixed; no new winner selection or model refit on Nov17.",
        "- The original 137-game delayed-gold study's early-minute availability assumption was "
        "not valid; preserve prior receipt but avoid using it to assert real live performance.",
        "- Historical raw replay arrays are internally aligned; no independently observed "
        "received_at or serving-feed net-worth/earned-gold parity. Real-time GO is blocked.",
        "- This cohort's labels have already been used in previous model research. All new CIs "
        "are descriptive and do NOT adjust for previous model searching.",
        "- Original applicant report, notebook, TEST predictions, ZIP and draft PR unchanged.",
        ""]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    r=eval_all()
    print(report(r))
    if args.write:
        if RESULT.exists() or READOUT.exists():
            raise FileExistsError("Immutable first-scored stress results cannot be overwritten")
        RESULT.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
        READOUT.write_text(report(r))


if __name__=="__main__":
    main()
