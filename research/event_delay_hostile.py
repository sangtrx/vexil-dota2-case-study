#!/usr/bin/env python3
"""Replaying the original fixed ALL model with strictly delayed event visibility.

This is a falsification/stress test on reused TRAIN, NOT new model selection.
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

from all_family_features import (CACHE, COLS, FAMILY, PROTO as OLD_PROTO,
                                 build_frozen_train, mirror, one_snapshot,
                                 parse_item_milestones, parse_objectives)
from all_family_models import (BASE, CANDIDATES, INPUTS, OTHER,
                               verify_original_artifacts)
from conditional_gold_forward import FROZEN_CUTS
from rich_feature_engineering import source_key
from rich_feature_models import create_pipeline,load_train,proper
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"research/EVENT_DELAY_HOSTILE_PROTOCOL.md"
RECEIPT=ROOT/"research/EVENT_DELAY_HOSTILE_RECEIPT.json"
READOUT=ROOT/"research/EVENT_DELAY_HOSTILE_READOUT.md"
PRIOR=ROOT/"research/ALL_FAMILY_RESULTS.json"
DRAWS,SEED=5000,20261118
AFFECTED=tuple(FAMILY["C"])+tuple(FAMILY["I"])
STATIC=tuple(FAMILY["R"])+tuple(FAMILY["O"])
ALL="ALL"
LAGGED="ALL_60"


def visible_events(objectives:list,purchases:list,minute:int,delay:int)->tuple[list,list]:
    """Real minute t, source events only through t*60-delay; no inferred arrival."""
    if not isinstance(minute,int) or minute<0 or delay not in (0,60):
        raise ValueError("Only fixed 0/60 second lag on nonnegative integer minute")
    limit=minute*60-delay
    if limit<0:
        return [],[]
    return ([e for e in objectives if 0<=e[0]<=limit],
            [e for e in purchases if 0<=e[0]<=limit])


def delayed_frame(df:pd.DataFrame,cache:Path=CACHE)->tuple[pd.DataFrame,dict]:
    if not isinstance(df,pd.DataFrame) or len(df)!=10675 or df.match_id.nunique()!=291:
        raise AssertionError("Original TRAIN scope required")
    out=df.copy()
    count=0
    mirror_validated=0
    for match,part in out.groupby("match_id",sort=False):
        raw=json.loads(gzip.decompress(
            (cache/(source_key(int(match))+".json.gz")).read_bytes()))
        if int(raw.get("match_id",-1))!=int(match):
            raise AssertionError("Wrong original raw match")
        mins=part.minute.to_numpy(dtype=int)
        if not np.array_equal(mins,np.arange(len(part))):
            raise AssertionError("Missing or out-of-order game minute")
        gold=part.gold_k.to_numpy(dtype=float)
        all_objective=parse_objectives(raw)
        all_purchase=parse_item_milestones(raw)
        for i,t in zip(part.index.to_numpy(dtype=int),mins):
            obj,pur=visible_events(all_objective,all_purchase,int(t),60)
            values=one_snapshot(gold,int(t),obj,pur)
            mirrored_obj,mirrored_purchase=mirror(obj,pur)
            reflect=one_snapshot(-gold,int(t),mirrored_obj,mirrored_purchase)
            if any(abs(values[k]+reflect[k])>1e-10 for k in COLS):
                raise AssertionError("Delay changed Radiant/Dire team mirror")
            for name in AFFECTED:
                out.at[i,name]=values[name]
            for name in STATIC:
                if not math.isclose(values[name],out.at[i,name],rel_tol=0,abs_tol=1e-12):
                    raise AssertionError("Event delay changed gold-only R/O feature")
            if t==0 and any(values[name]!=0 for name in AFFECTED):
                raise AssertionError("t=0 event availability under one-minute delay")
            count+=1
            mirror_validated+=1
    if (count!=10675 or mirror_validated!=count
        or out[["match_id","minute"]].duplicated().any()):
        raise AssertionError("Delay feature frame incomplete")
    if not np.array_equal(df[list(STATIC)].to_numpy(),
                          out[list(STATIC)].to_numpy()):
        raise AssertionError("Lag-only perturbation unexpectedly changes static family")
    return out,{
        "minutes":count,
        "mirrors":mirror_validated,
        "changed_features":list(AFFECTED),
        "unchanged_features":list(STATIC),
        "delay_seconds":60,
        "actual_source_delay_measured":False,
    }


def grouped_ci(rows:pd.DataFrame,left:str,right:str,replicate:np.ndarray)->dict:
    ll=rows["ll_"+left].to_numpy(float)-rows["ll_"+right].to_numpy(float)
    br=rows["br_"+left].to_numpy(float)-rows["br_"+right].to_numpy(float)
    group=cluster_ids(rows[["match_id","series_id"]])
    frame=pd.DataFrame({"cluster":group,"n":np.ones(len(ll),dtype=int),"ll":ll,"br":br})
    g=frame.groupby("cluster",sort=True).agg({"n":"sum","ll":"sum","br":"sum"})
    if len(g)!=70 or replicate.shape!=(DRAWS,70):
        raise AssertionError("Expected original 70 independent professional groups")
    a=g[["n","ll","br"]].to_numpy(float)
    z=a[replicate].sum(axis=1)
    x=z[:,1:]/z[:,0,None]
    if not np.isfinite(x).all():
        raise AssertionError("Bootstrap not finite")
    late=rows.minute.to_numpy(int)>=30
    per_match=float(pd.DataFrame({"match":rows.match_id,"ll":ll})
                    .groupby("match",sort=True).ll.mean().mean())
    influence=[]
    for idx in range(len(g)):
        remaining=np.delete(a,idx,axis=0)
        influence.append(float(remaining[:,1].sum()/remaining[:,0].sum()))
    gains=(-g.ll).clip(lower=0)
    totalgain=-ll.sum()
    return {
        "delta_ll":float(ll.mean()),
        "delta_brier":float(br.mean()),
        "delta_brier_after30":float(br[late].mean()),
        "equal_match_delta_ll":per_match,
        "series_bootstrap_95_ll":np.quantile(x[:,0],[.025,.975]).tolist(),
        "series_bootstrap_975_ll_two_primary":np.quantile(x[:,0],[.0125,.9875]).tolist(),
        "leave_one_series_out_min_ll":min(influence),
        "leave_one_series_out_max_ll":max(influence),
        "series_improvement_count":int((g.ll<0).sum()),
        "largest_positive_series_share":float(gains.max()/totalgain) if totalgain>0 else None,
    }


def evaluate()->dict:
    if not PROTO.exists():
        raise AssertionError("Predeclared stress protocol missing")
    protected=verify_original_artifacts()
    original,provenance=load_train()
    existing,metadata=build_frozen_train(original)
    deferred,stress=delayed_frame(existing)
    prior=json.loads(PRIOR.read_text())
    if prior["n_oof_rows"]!=5081 or prior["n_oof_games"]!=137:
        raise AssertionError("Saved five-family comparators changed")
    meta=(existing[["match_id","start_time","duration","series_id"]]
          .drop_duplicates()
          .sort_values(["start_time","match_id"],kind="stable")
          .reset_index(drop=True))
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("Frozen TRAIN-forward cutpoints drifted")
    folds=[]
    per_rows=[]
    names=(BASE,OTHER,ALL,LAGGED)
    for i,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),1):
        older,current=meta.iloc[:left],meta.iloc[left:right]
        asof=int(current.iloc[0].start_time)
        eligible=older[older.start_time+older.duration<=asof]
        if (set(cluster_ids(older))&set(cluster_ids(current))
            or set(cluster_ids(eligible))&set(cluster_ids(current))):
            raise AssertionError("Series crossed TRAIN-forward boundary")
        fit=existing[existing.match_id.isin(eligible.match_id)]
        ev=existing[existing.match_id.isin(current.match_id)]
        lag_fit=deferred[deferred.match_id.isin(eligible.match_id)]
        lag_ev=deferred[deferred.match_id.isin(current.match_id)]
        if not np.array_equal(fit[["match_id","minute"]],lag_fit[["match_id","minute"]]):
            raise AssertionError("Lag-training row order mismatch")
        if not np.array_equal(ev[["match_id","minute"]],lag_ev[["match_id","minute"]]):
            raise AssertionError("Lag-validation row order mismatch")
        y=ev.radiant_win.to_numpy(int)
        saved=ev[["match_id","minute","series_id"]].copy()
        stats={"fold":i,"games":len(current),"completed_fit_games":len(eligible)}
        for name in names:
            dataset_fit=lag_fit if name==LAGGED else fit
            dataset_ev=lag_ev if name==LAGGED else ev
            col=INPUTS[ALL] if name==LAGGED else INPUTS[name]
            predictor=create_pipeline(BASE)
            predictor.fit(dataset_fit[col],dataset_fit.radiant_win.astype(int))
            p=predictor.predict_proba(dataset_ev[col])[:,1]
            ll,br=proper(y,p)
            saved["ll_"+name]=ll
            saved["br_"+name]=br
            stats[name]={"logloss":float(ll.mean()),"brier":float(br.mean())}
            if name!=LAGGED:
                expected=prior["folds"][i-1][name]
                for measure in ("logloss","brier"):
                    if not math.isclose(stats[name][measure],expected[measure],abs_tol=1e-10,rel_tol=0):
                        raise AssertionError("Historic "+name+" baseline parity failed")
        folds.append(stats)
        per_rows.append(saved)
    rows=pd.concat(per_rows,ignore_index=True)
    if (len(rows)!=5081 or rows.match_id.nunique()!=137 or
        len(set(cluster_ids(rows)))!=70 or
        rows[["match_id","minute"]].duplicated().any()):
        raise AssertionError("OOF unit count changed")
    rng=np.random.default_rng(SEED)
    draws=rng.integers(0,70,size=(DRAWS,70))
    comparisons={name:grouped_ci(rows,LAGGED,name,draws)
                 for name in (ALL,OTHER,BASE)}
    fold_wins={name:sum(f[LAGGED]["logloss"]<f[name]["logloss"] for f in folds)
               for name in (ALL,OTHER,BASE)}
    allzero_vs_q1=grouped_ci(rows,ALL,OTHER,draws)
    a=comparisons[ALL]
    q=comparisons[OTHER]
    valid_gate=bool(a["delta_ll"]<=.002
                    and q["delta_ll"]<=-.0025
                    and q["series_bootstrap_975_ll_two_primary"][1]<0
                    and fold_wins[OTHER]>=3
                    and q["delta_brier"]<=0
                    and q["delta_brier_after30"]<=0)
    if verify_original_artifacts()!=protected:
        raise AssertionError("Applicant source files changed")
    return {
      "status":"post-result historical TRAIN-only hostile stress / not independent",
      "original_train_sha256":provenance["source_train_sha256"],
      "protocol_sha256":hashlib.sha256(PROTO.read_bytes()).hexdigest(),
      "protected_submission_sha256":protected,
      "feature_source":metadata,"lag_stress":stress,
      "n_oof_games":137,"n_oof_minutes":5081,
      "n_professional_series":70,"bootstrap_seed":SEED,"bootstrap_draws":DRAWS,
      "folds":folds,"comparisons_all60_minus":comparisons,
      "original_all0_minus_q1":allzero_vs_q1,
      "all60_fold_wins":fold_wins,
      "synthetic_lag_stability_gate":valid_gate,
      "source_real_ingress_time_verified":False,
      "employer_submission_promoted":False,
    }


def report(r:dict)->str:
    out=[
      "# Hostile stress: What if tower/item events arrive 60 seconds late?",
      "",
      "Only original 291 TRAIN games, unchanged four chronological, series-disjoint "
      "137-game / 5,081-minute OOF split; this is **not** an unseen independent test.",
      "Original feature code and applicant deliverable untouched.",
      "",
      "| Comparison (ALL60 minus ...) | Δ LL | 95% grouped CI | "
      "97.5% two-primary CI | Δ Brier | 30+ Δ Brier | "
      "Equal-match Δ LL | Fold wins |",
      "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name in (ALL,OTHER,BASE):
        c=r["comparisons_all60_minus"][name]
        lo,hi=c["series_bootstrap_95_ll"]
        zlo,zhi=c["series_bootstrap_975_ll_two_primary"]
        out.append(f"| {name} | {c['delta_ll']:+.6f} | [{lo:+.6f},{hi:+.6f}] | "
                   f"[{zlo:+.6f},{zhi:+.6f}] | {c['delta_brier']:+.6f} | "
                   f"{c['delta_brier_after30']:+.6f} | "
                   f"{c['equal_match_delta_ll']:+.6f} | {r['all60_fold_wins'][name]}/4 |")
    out+=["",
      "## Four chronological TRAIN-forward folds",
      "",
      "| Fold | Games | Q1 LL | M1 LL | ALL0 LL | ALL60 LL |",
      "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for f in r["folds"]:
        out.append(f"| {f['fold']} | {f['games']} | "
                   f"{f[OTHER]['logloss']:.6f} | {f[BASE]['logloss']:.6f} | "
                   f"{f[ALL]['logloss']:.6f} | {f[LAGGED]['logloss']:.6f} |")
    out+=["",
      "## Sensitivity and decision",
      "",
      f"- ALL60−Q1 delete-one-series LL range: "
      f"[{r['comparisons_all60_minus'][OTHER]['leave_one_series_out_min_ll']:+.6f},"
      f"{r['comparisons_all60_minus'][OTHER]['leave_one_series_out_max_ll']:+.6f}]. "
      "No re-fitting or model selection from deletions.",
      f"- Original ALL0−Q1 LL: {r['original_all0_minus_q1']['delta_ll']:+.6f}; "
      "the previously registered ALL0 score is reconstructed from scratch.",
      f"- Frozen event-lag stability gate: "
      f"{'PASS FOR FURTHER RESEARCH ONLY' if r['synthetic_lag_stability_gate'] else 'FAIL / NO-GO'}.",
      "",
      "This is simulated event source delay. Live timestamp arrival has NOT "
      "been measured. The user-owned 4-page submission, notebook, original TEST "
      "predictions, ZIP, original draft PR and main are unchanged. "
      "This historical 4-day TRAIN-window result cannot establish cross-patch "
      "or cross-league transport; original TEST is not blind anymore.",
      ""
    ]
    return "\n".join(out)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    receipt=evaluate()
    print(report(receipt))
    if args.write:
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        READOUT.write_text(report(receipt))
