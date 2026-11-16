#!/usr/bin/env python3
"""Post-hoc calibration-in-the-large sensitivity on frozen original TEST.

No refitting, recalibration, feature change, thresholding or new validation.
Paired professional-series-or-singleton bootstrap preserves all within-match
minute labels and within-series match dependence. This is descriptive.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "artifacts/heldout_predictions.csv"
GROUPS = ROOT / "docs/SERIES_GROUPS_TEST.json"
FORECAST_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
GROUPS_SHA256 = "472db6781f6e6ad210120a07c4fb291583b75557841bbf2fa9448bafe6662383"
DRAWS = 10000
SEED = 20261116

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pct_ci(draws: np.ndarray) -> list[float]:
    return [float(v) for v in np.quantile(draws, (.025,.975))]

def evaluate() -> dict:
    if sha(PRED)!=FORECAST_SHA256 or sha(GROUPS)!=GROUPS_SHA256:
        raise ValueError("Original frozen predictions or series metadata changed")
    info=json.loads(GROUPS.read_text(encoding="utf8"))
    games=defaultdict(list)
    with PRED.open(newline="",encoding="utf8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=["match_id","minute","p_model","p_baseline","radiant_win"]:
            raise ValueError("Unexpected original TEST prediction columns")
        for row in reader:
            mid=int(row["match_id"])
            minute=int(row["minute"])
            y=int(row["radiant_win"])
            p0=float(row["p_baseline"])
            p1=float(row["p_model"])
            if y not in (0,1) or minute <0 or not np.isfinite((p0,p1)).all() or not 0<p0<1 or not 0<p1<1:
                raise ValueError("Non-finite/bad original TEST row")
            games[mid].append((minute,y,p0,p1))
    if len(games)!=106 or set(map(str,games))!=set(info):
        raise ValueError("Unexpected 106-game original TEST identity/metadata")
    by_series=defaultdict(list)
    total_rows=0
    for mid,rows in games.items():
        rows=sorted(rows,key=lambda x:x[0])
        if [x[0] for x in rows]!=list(range(len(rows))) or len({x[1] for x in rows})!=1:
            raise ValueError("TEST time order or fixed outcome changed")
        sid=int(info[str(mid)]["series_id"])
        key="s"+str(sid) if sid>0 else "m"+str(mid)
        # [minute count, M0 row bias total, M1 row bias total,
        #  game count, game-mean M0 bias total, game-mean M1 bias total, win count]
        n=len(rows)
        y=rows[0][1]
        res0=sum(x[2]-x[1] for x in rows)
        res1=sum(x[3]-x[1] for x in rows)
        by_series[key].append((n,res0,res1,1,res0/n,res1/n,y))
        total_rows+=n
    if total_rows!=3836 or len(by_series)!=54:
        raise ValueError("Original forecast rows or dependence groups changed")
    keys=sorted(by_series)
    sums=np.array([[sum(v[i] for v in by_series[k]) for i in range(7)]
                   for k in keys],dtype=np.float64)
    totals=sums.sum(axis=0)
    if int(totals[0])!=3836 or int(totals[3])!=106 or int(totals[6])!=63:
        raise ValueError("Original source totals do not match frozen TEST")
    draw=np.random.default_rng(SEED).integers(0,len(keys),(DRAWS,len(keys)))
    selected=sums[draw].sum(axis=1)
    if np.any(selected[:,0]<=0) or np.any(selected[:,3]<=0):
        raise ValueError("Invalid resampled cluster weights")
    # Each drawn series is a unit. Ratio statistic preserves intact games,
    # but total sampled minute rows and game counts vary across draws.
    result={
        "study_status":"POSTHOC_DESCRIPTIVE_CALIBRATION_NO_MODEL_FIT",
        "source_forecast_sha256":FORECAST_SHA256,
        "source_series_groups_sha256":GROUPS_SHA256,
        "games":106, "minute_forecasts":3836,
        "series_or_singletons":54,
        "bootstrap_draws":DRAWS,
        "bootstrap_seed":SEED,
        "observed_win_rate_game_weighted":float(totals[6]/totals[3]),
        "observed_win_rate_minute_weighted":float(sum(rows[0][1]*len(rows) for rows in games.values())/totals[0]),
        "observed_win_rate_game_95ci_series":pct_ci(selected[:,6]/selected[:,3]),
        "M0_mean_prediction_minus_outcome_minute":float(totals[1]/totals[0]),
        "M1_mean_prediction_minus_outcome_minute":float(totals[2]/totals[0]),
        "M0_mean_prediction_minus_outcome_minute_95ci_series":pct_ci(selected[:,1]/selected[:,0]),
        "M1_mean_prediction_minus_outcome_minute_95ci_series":pct_ci(selected[:,2]/selected[:,0]),
        "M0_mean_prediction_minus_outcome_equal_game":float(totals[4]/totals[3]),
        "M1_mean_prediction_minus_outcome_equal_game":float(totals[5]/totals[3]),
        "M0_mean_prediction_minus_outcome_equal_game_95ci_series":pct_ci(selected[:,4]/selected[:,3]),
        "M1_mean_prediction_minus_outcome_equal_game_95ci_series":pct_ci(selected[:,5]/selected[:,3]),
        "calibration_on_inspected_test_only":True,
        "no_calibration_fit_or_model_selection":True,
        "ci_interpretation":"Descriptive series-cluster bootstrap on inspected TEST; not a paired model contrast, live feed, or deployment calibration proof.",
    }
    return result

def check(receipt:dict, actual:dict) -> None:
    if receipt.keys()!=actual.keys():
        raise ValueError("Calibration receipt key drift")
    for key, observed in actual.items():
        saved=receipt[key]
        if isinstance(observed,list):
            if not isinstance(saved,list) or len(saved)!=len(observed) or any(abs(a-b)>1e-12 for a,b in zip(observed,saved)):
                raise ValueError("Calibration numerical receipt changed: "+key)
        elif isinstance(observed,float):
            if not isinstance(saved,(float,int)) or abs(saved-observed)>1e-12:
                raise ValueError("Calibration numerical receipt changed: "+key)
        elif saved!=observed:
            raise ValueError("Calibration metadata receipt changed: "+key)

if __name__=="__main__":
    result=evaluate()
    source=ROOT/"docs/CALIBRATION_BIAS_RECEIPT.json"
    if source.is_file():
        check(json.loads(source.read_text(encoding="utf8")),result)
    print(json.dumps(result,indent=2,sort_keys=True))
