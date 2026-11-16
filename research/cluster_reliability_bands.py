#!/usr/bin/env python3
"""Post-hoc fixed 10-bin reliability intervals via paired series resampling.

No calibration fit, tuning, changed forecasts, reweighting, or new TEST.
Uses only original frozen held-out forecasts and series ID source receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PRED=ROOT/"artifacts/heldout_predictions.csv"
GROUPS=ROOT/"docs/SERIES_GROUPS_TEST.json"
RECEIPT=ROOT/"docs/CALIBRATION_FIXED_BIN_GROUPED_CI_RECEIPT.json"
EXPECTED_PRED_SHA="03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
SEED=20261116
DRAWS=5000
BINS=10


def h(raw:bytes):
    return hashlib.sha256(raw).hexdigest()


def compute():
    if h(PRED.read_bytes())!=EXPECTED_PRED_SHA:
        raise ValueError("Frozen original TEST forecasts changed")
    records=pd.read_csv(PRED)
    groups=json.loads(GROUPS.read_text())
    if len(records)!=3836 or records.match_id.nunique()!=106:
        raise ValueError("Original TEST opportunity count drift")
    if set(str(x) for x in records.match_id.unique())!=set(groups):
        raise ValueError("Missing series map from frozen TEST")
    key_for={
        int(mid):"s"+str(g["series_id"]) if int(g["series_id"])>0 else "m"+str(mid)
        for mid,g in groups.items()
    }
    keys=records.match_id.map(key_for)
    unique,group_index=np.unique(keys.to_numpy(),return_inverse=True)
    if len(unique)!=54:raise ValueError("Original TEST series group count drift")
    n=len(records)
    outcome=records.radiant_win.to_numpy(float)
    np.random.default_rng(SEED)
    rng=np.random.default_rng(SEED)
    draws=rng.integers(0,len(unique),size=(DRAWS,len(unique)))
    models={}
    for model,col in (("M0","p_baseline"),("M1","p_model")):
        p=records[col].to_numpy(float)
        if not (np.isfinite(p).all() and ((p>=0)&(p<=1)).all()):
            raise ValueError("Invalid fixed model probabilities")
        b=np.minimum(np.floor(p*BINS).astype(int),BINS-1)
        cluster_bins=np.zeros((len(unique),BINS,3),float)
        np.add.at(cluster_bins,(group_index,b,0),1.)
        np.add.at(cluster_bins,(group_index,b,1),outcome)
        np.add.at(cluster_bins,(group_index,b,2),p)
        n_by=cluster_bins.sum(axis=0)
        resampled=cluster_bins[draws].sum(axis=1)
        report=[]
        for i in range(BINS):
            observed_n, observed_wins, observed_prob=n_by[i]
            where=resampled[:,i,0]>0
            valid=resampled[where,i]
            supported_frac=float(where.mean())
            if observed_n:
                observed_mean=float(observed_wins/observed_n)
                predicted_mean=float(observed_prob/observed_n)
                error=observed_mean-predicted_mean
            else:
                observed_mean=predicted_mean=error=None
            if valid.size:
                obs_boot=valid[:,1]/valid[:,0]
                err_boot=(valid[:,1]-valid[:,2])/valid[:,0]
                obs_ci=[float(x) for x in np.quantile(obs_boot,[.025,.975])]
                err_ci=[float(x) for x in np.quantile(err_boot,[.025,.975])]
            else:
                obs_ci=err_ci=None
            report.append({
                "bin":i,
                "forecast_interval":[i/BINS,(i+1)/BINS],
                "forecast_rows":int(observed_n),
                "games":int(records.loc[b==i,"match_id"].nunique()),
                "series_or_singletons":int(len(set(keys[b==i]))),
                "mean_p":predicted_mean,
                "win_fraction":observed_mean,
                "observed_minus_predicted":error,
                "observed_win_fraction_ci_95_series":obs_ci,
                "observed_minus_predicted_ci_95_series":err_ci,
                "fraction_bootstrap_draws_with_nonempty_bin":supported_frac,
                "thin_support_below_10_original_groups":int(len(set(keys[b==i])))<10,
            })
        point_ece=float(sum(abs(i["observed_minus_predicted"])*i["forecast_rows"]/n
                            for i in report if i["forecast_rows"]>0))
        models[model]={"ece_10bin_descriptive":point_ece,"bins":report}
    if (abs(models["M0"]["ece_10bin_descriptive"]-0.08948284614037452)>1e-12 or
        abs(models["M1"]["ece_10bin_descriptive"]-0.07501877151942367)>1e-12):
        raise ValueError("Original ECE10 calculation changed")
    return {
        "status":"FIXED_BIN_GROUPED_RELIABILITY_POSTHOC_NO_FIT",
        "original_test_prediction_sha256":EXPECTED_PRED_SHA,
        "original_test_series_map_sha256":h(GROUPS.read_bytes()),
        "games":106,
        "minute_rows":3836,
        "series_or_singletons":54,
        "seed":SEED,
        "draws":DRAWS,
        "fixed_bins":BINS,
        "cluster_unit":"positive professional series, else single game",
        "test_is_already_opened":True,
        "any_test_calibration_fit":False,
        "any_model_or_forecast_update":False,
        "conditional_ci_when_bin_unsupported_in_bootstrap":True,
        "models":models,
    }


def check():
    expected=json.loads(RECEIPT.read_text())
    actual=compute()
    if json.dumps(actual,sort_keys=True)!=json.dumps(expected,sort_keys=True):
        raise ValueError("Frozen reliability-bin uncertainty receipt drift")
    return actual


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write-first-receipt",action="store_true")
    args=ap.parse_args()
    if args.write_first_receipt:
        if RECEIPT.exists():raise FileExistsError("Never overwrite prior signed-off audit")
        r=compute()
        RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    else:
        r=check()
    print(json.dumps({"status":"PASS","games":r["games"],
        "clusters":r["series_or_singletons"],
        "draws":r["draws"],
        "M0_ECE":r["models"]["M0"]["ece_10bin_descriptive"],
        "M1_ECE":r["models"]["M1"]["ece_10bin_descriptive"],
        "thin_M0_bins":sum(b["thin_support_below_10_original_groups"] for b in r["models"]["M0"]["bins"]),
        "thin_M1_bins":sum(b["thin_support_below_10_original_groups"] for b in r["models"]["M1"]["bins"])},indent=2))
