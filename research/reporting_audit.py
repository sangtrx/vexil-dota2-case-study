#!/usr/bin/env python3
"""POST-OUTCOME reporting only, never refits or reselects models.

This script may be rerun to verify report arithmetic, but the one-shot
confirmatory evaluator (consumed/locked) must never be rerun or modified
to optimize the now-seen third cohort.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.evaluate_regime_gate import two_way_simultaneous_interval

ROOT=Path("/home/ai-agent/.cache/vexil-edge-v3-20261113")
SEED=20261113
BOOTS=10000

def direct_interval(frame,metric,group="series"):
    keys=(frame.match_id.astype(str) if group=="match"
          else np.where(frame.series_id.astype(int)>0,
                        "s"+frame.series_id.astype(str),
                        "m"+frame.match_id.astype(str)))
    a=frame.assign(group=keys).groupby("group",sort=True).agg(
        n=("minute","size"),m=(metric+"_m1","sum"),b=(metric+"_base","sum")
    )[["n","m","b"]].to_numpy(float)
    delta=(a[:,1].sum()-a[:,2].sum())/a[:,0].sum()
    rng=np.random.default_rng(SEED)
    draws=a[rng.integers(0,len(a),size=(BOOTS,len(a)))].sum(axis=1)
    boot=(draws[:,1]-draws[:,2])/draws[:,0]
    lo,hi=np.quantile(boot,[.025,.975])
    return dict(metric=metric,cluster=group,groups=len(a),
                difference=float(delta),lower=float(lo),upper=float(hi),
                reps=BOOTS,seed=SEED)

def main():
    assert (ROOT/"gate_confirmation_evaluation_receipt.json").exists()
    assert (ROOT/"gate_confirmation_consumed.lock.json").exists()
    p=pd.read_csv(ROOT/"gate_confirmation_predictions.csv")
    receipt=json.loads((ROOT/"gate_confirmation_evaluation_receipt.json").read_text())
    assert receipt["third_holdout_games"]==p.match_id.nunique()==200
    assert receipt["third_holdout_minute_rows"]==len(p)==6827

    portions=[("overall",p),("0-9",p[p.minute<=9]),
              ("10-19",p[(p.minute>=10)&(p.minute<=19)]),
              ("20-29",p[(p.minute>=20)&(p.minute<=29)]),
              ("30+",p[p.minute>=30])]
    phase_ci=[]
    calibration=[]
    bins=[]
    for label,frame in portions:
        ci=two_way_simultaneous_interval(frame,group="match")
        for r in ci.to_dict("records"):
            phase_ci.append({"phase":label,**r})
        for model in ("base","m1","gate"):
            probs=frame["p_"+model].to_numpy(float)
            labels=frame.radiant_win.to_numpy(int)
            index=np.clip(np.searchsorted(np.linspace(0,1,11),probs,
                                           side="right")-1,0,9)
            ece=0.
            for b in range(10):
                keep=index==b
                if not keep.any():continue
                predmean=float(probs[keep].mean())
                observed=float(labels[keep].mean())
                n=int(keep.sum())
                ece+=n/len(frame)*abs(observed-predmean)
                bins.append({"phase":label,"model":model,"bin":b,
                             "minute_rows":n,
                             "distinct_matches":int(frame.loc[keep,"match_id"].nunique()),
                             "mean_prediction":predmean,
                             "observed_win_frequency":observed})
            calibration.append({"phase":label,"model":model,
                                "minute_rows":len(frame),
                                "matches":frame.match_id.nunique(),
                                "descriptive_ece_10_bins":ece,
                                "mean_prediction":float(probs.mean()),
                                "mean_outcome_row_weighted":float(labels.mean())})
    extra=[direct_interval(p,metric,group)
           for metric in ("ll","brier") for group in ("match","series")]
    files={
        "gate_confirmation_phase_match_ci_exploratory.csv":pd.DataFrame(phase_ci),
        "gate_confirmation_calibration_by_phase.csv":pd.DataFrame(calibration),
        "gate_confirmation_reliability_bins.csv":pd.DataFrame(bins),
        "m1_vs_m0_secondary_unadjusted_ci.csv":pd.DataFrame(extra)
    }
    for name,table in files.items():
        table.to_csv(ROOT/name,index=False)
        print("REPORT_QA_DERIVED_CSV",name,"rows",len(table))
    print("PHASE_ECE_10_FIXED_BINS")
    print(pd.DataFrame(calibration).pivot(index="phase",columns="model",
                                         values="descriptive_ece_10_bins").round(5).to_string())
    print("SECONDARY_M1_M0_CI_UNADJUSTED_NOT_GATE_SELECTION")
    print(pd.DataFrame(extra).round(6).to_string(index=False))
    print("REPORTING_ONLY_COMPLETE: no model fitted and gate decision unchanged")

if __name__=="__main__":
    main()
