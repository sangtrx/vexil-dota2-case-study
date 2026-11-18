#!/usr/bin/env python3
"""Separate correction for early NO_DATA rows in the 137-game TRAIN-forward stale study.

The prior 137-game output is retained unchanged; this is a separate
post-result causal-availability correction, not another model selection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

from conditional_gold_forward import FROZEN_CUTS
from disagreement_reliability import guard_delivery
from rich_feature_models import MODELS,create_pipeline,load_train,proper
from stale_feed_reliability import (lagged_views,paired_cluster_ci,SEED,DRAWS,LAGS,M1)
from train_time_effect_ci import cluster_ids

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"research/STRICT_NODATA_TRAIN_FORWARD_REPAIR_PROTOCOL_20261118.md"
PRIOR=ROOT/"research/STALE_FEED_RECEIPT.json"
OUT=ROOT/"research/STRICT_NODATA_TRAIN_FORWARD_REPAIR_RECEIPT.json"
READOUT=ROOT/"research/STRICT_NODATA_TRAIN_FORWARD_REPAIR_READOUT.md"


def fixed_lag_predictions(fitted,ev:pd.DataFrame,fresh:np.ndarray,lag:int):
    if lag not in LAGS:
        raise ValueError("Only registered 1/3 minute delay")
    frame,old_hold,old_prefix_count=lagged_views(ev,fresh,lag)
    n=len(ev)
    ready=ev.minute.to_numpy(int)>=lag
    if int((~ready).sum())!=old_prefix_count:
        raise AssertionError("Old source's unavailable prefix count shifted")
    clock=np.full(n,.5,dtype=float)
    hold=np.full(n,.5,dtype=float)
    if not ready.any():
        raise AssertionError("No usable source ever arrived")
    # Important: model.predict_proba() is never invoked for unavailable rows.
    clock[ready]=fitted.predict_proba(frame.loc[ready,MODELS[M1]])[:,1]
    hold[ready]=old_hold[ready]
    if not np.array_equal(clock[~ready],np.full((~ready).sum(),.5)):
        raise AssertionError("Unseen snapshot entered clock model")
    if not np.array_equal(hold[~ready],np.full((~ready).sum(),.5)):
        raise AssertionError("Unseen snapshot entered held previous forecast")
    if not (np.isfinite(clock).all() and np.isfinite(hold).all()
            and (clock>0).all() and (clock<1).all()
            and (hold>0).all() and (hold<1).all()):
        raise AssertionError("Invalid corrected stream")
    return clock,hold,int((~ready).sum())


def evaluate()->dict:
    if not PROTOCOL.exists():
        raise AssertionError("Correction protocol was not committed")
    old=json.loads(PRIOR.read_text())
    orig_artifacts=guard_delivery()
    frame,train_source=load_train()
    meta=(frame[["match_id","start_time","duration","series_id"]]
        .drop_duplicates().sort_values(["start_time","match_id"],kind="stable")
        .reset_index(drop=True))
    if len(meta)!=291 or tuple(FROZEN_CUTS)!=(154,176,220,252,291):
        raise AssertionError("Original TRAIN fold contract changed")
    folds=[]
    all_parts=[]
    for fold,(left,right) in enumerate(zip(FROZEN_CUTS[:-1],FROZEN_CUTS[1:]),start=1):
        older,current=meta.iloc[:left],meta.iloc[left:right]
        split_ts=int(current.iloc[0].start_time)
        mature=older[older.start_time+older.duration<=split_ts]
        if set(cluster_ids(mature))&set(cluster_ids(current)):
            raise AssertionError("Train/eval series group contamination")
        f=frame[frame.match_id.isin(mature.match_id)]
        ev=(frame[frame.match_id.isin(current.match_id)]
            .sort_values(["match_id","minute"],kind="stable").reset_index(drop=True))
        if set(f.match_id)&set(ev.match_id):
            raise AssertionError("Fit/eval match ID intersection")
        fitted=create_pipeline(M1).fit(f[MODELS[M1]],f.radiant_win.astype(int))
        y=ev.radiant_win.to_numpy(int)
        fresh=fitted.predict_proba(ev[MODELS[M1]])[:,1]
        ll,br=proper(y,fresh)
        old_fold=old["folds"][fold-1]
        if not (abs(float(ll.mean())-old_fold["score"]["FRESH"]["logloss"])<1e-10
                and abs(float(br.mean())-old_fold["score"]["FRESH"]["brier"])<1e-10):
            raise AssertionError("Old TRAIN-forward original fresh score parity failed")
        part=ev[["match_id","series_id","minute"]].copy()
        part["ll_FRESH"]=ll
        part["br_FRESH"]=br
        fold_values={"fold":fold,"games":len(current),"minute_rows":len(ev),
                     "no_data_rows":{},"metrics":{"FRESH":{"logloss":float(ll.mean()),"brier":float(br.mean())}}}
        for lag in LAGS:
            clock,hold,ndata=fixed_lag_predictions(fitted,ev,fresh,lag)
            fold_values["no_data_rows"][str(lag)]=ndata
            for name,p in (("CLOCK"+str(lag),clock),("HOLD"+str(lag),hold)):
                l,b=proper(y,p)
                part["ll_"+name]=l
                part["br_"+name]=b
                fold_values["metrics"][name]={"logloss":float(l.mean()),
                      "brier":float(b.mean()),"late30_brier":float(b[ev.minute.to_numpy(int)>=30].mean())}
        folds.append(fold_values)
        all_parts.append(part)
    whole=pd.concat(all_parts,ignore_index=True)
    if len(whole)!=5081 or whole.match_id.nunique()!=137 or len(set(cluster_ids(whole)))!=70:
        raise AssertionError("TRAIN forward 137/5081/70 source scope changed")
    late=whole.minute.to_numpy(int)>=30
    output={}
    policies=("FRESH","CLOCK1","HOLD1","CLOCK3","HOLD3")
    for name in policies:
        ll=whole["ll_"+name].to_numpy()
        br=whole["br_"+name].to_numpy()
        prev=old["overall_metrics"][name]
        output[name]={
           "logloss":float(ll.mean()),"old_logloss":float(prev["logloss"]),
           "delta_ll_corrected_minus_old":float(ll.mean()-prev["logloss"]),
           "brier":float(br.mean()),"old_brier":float(prev["brier"]),
           "delta_brier_corrected_minus_old":float(br.mean()-prev["brier"]),
           "late30_brier":float(br[late].mean()),
           "old_late30_brier":float(prev["late30_brier"]),
        }
        if not np.isclose(output[name]["late30_brier"],prev["late30_brier"],atol=1e-11,rtol=0):
            raise AssertionError("Late30 should not change: lag<=3")
        if name=="FRESH" and not np.isclose(output[name]["logloss"],prev["logloss"],
                                             atol=1e-11,rtol=0):
            raise AssertionError("Original fresh historical result changed")
    ci={str(lag):paired_cluster_ci(whole,lag) for lag in LAGS}
    if guard_delivery()!=orig_artifacts:
        raise AssertionError("Employer original source package changed")
    return {
        "status":"Corrective post-result retrospective TRAIN-only; not live measurement",
        "protocol_sha256":hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "old_bug":"t<lag was clamped to gold[0],p[0] before valid availability",
        "original_old_receipt_sha256":hashlib.sha256(PRIOR.read_bytes()).hexdigest(),
        "original_train_source_sha256":train_source["source_train_sha256"],
        "models_fitted":"M1 original C1 logistic, mature March TRAIN folds only",
        "games_oof":137,"minute_rows":5081,"independent_series":70,
        "input_received_at_known":False,
        "no_data_state_policy":"p=0.5 before snapshot arrives; no model inference at t<lag",
        "total_no_data_rows":{str(lag):sum(z["no_data_rows"][str(lag)] for z in folds)
                              for lag in LAGS},
        "scores_old_vs_fixed":output,
        "paired_grouped_series_corrected":ci,
        "folds":folds,
        "preserved_original_applicant_sha":orig_artifacts,
        "previous_submitted_report_unchanged":True,
        "repeated_model_search_corrected":False,
    }


def report(r:dict)->str:
    lines=[
       "# Corrective early-NO_DATA simulation on original 137 TRAIN-forward games",
       "",
       "**Post-result corrective sensitivity**, not independent confirmation or measured live latency. "
       "Old frozen receipt retained. The old function's earliest-lag source substitution was wrong.",
       "",
       f"Source: {r['games_oof']} games, {r['minute_rows']} minute forecasts, "
       f"{r['independent_series']} professional groups. "
       "NO_DATA rows: "+", ".join(f"lag{lag}={r['total_no_data_rows'][str(lag)]}" for lag in LAGS)+".",
       "",
       "| Stream | Old LL | Corrected LL | Change | Old Brier | Corrected Brier | 30+ Brier check |",
       "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name,v in r["scores_old_vs_fixed"].items():
        lines.append(f"| {name} | {v['old_logloss']:.6f} | {v['logloss']:.6f} | "
                     f"{v['delta_ll_corrected_minus_old']:+.6f} | "
                     f"{v['old_brier']:.6f} | {v['brier']:.6f} | {v['late30_brier']:.6f} |")
    lines+=["",
       "## Corrected HOLD - CLOCK (negative means holding wins)",
       "",
       "| Lag | Corrected LL delta | Corrected 95% series CI | 97.5% two-lag CI | "
       "Corrected Brier delta | Corrected 30+ Brier delta |",
       "| --- | ---: | --- | --- | ---: | ---: |",
    ]
    for lag,v in r["paired_grouped_series_corrected"].items():
        a,b=v["series_bootstrap_95_ll"]
        c,d=v["series_bootstrap_975_ll_two_lags"]
        lines.append(f"| {lag} minute(s) | {v['hold_minus_clock_delta_logloss']:+.6f} | "
         f"[{a:+.6f},{b:+.6f}] | [{c:+.6f},{d:+.6f}] | "
         f"{v['hold_minus_clock_delta_brier']:+.6f} | "
         f"{v['late30_hold_minus_clock_delta_brier']:+.6f} |")
    lines+=["",
        "Old and corrected 30+ Brier is identical: all delayed states t<lag are early.",
        "No ability to verify actual event received_at; neither retrospective simulation "
        "can establish production service latency. No original applicant change.",
        ""]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    a=ap.parse_args()
    r=evaluate()
    print(report(r))
    if a.write:
        if OUT.exists() or READOUT.exists():
            raise FileExistsError("Correction receipt immutability")
        OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
        READOUT.write_text(report(r))


if __name__=="__main__":
    main()
