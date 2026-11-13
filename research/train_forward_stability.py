"""Audit M0 vs M1 in chronological, completed-label TRAIN-only forward folds.

This is a post-hoc diagnostic, never a model-selection step.
It does not read validation or held-out predictions, and never calls OpenDota.
Use the exact frozen source match payload cache created during local Run All.

Example:
python research/train_forward_stability.py --manifest path/to/match_manifest.csv \
 --cache path/to/api-cache --receipt path/to/development_stability.json
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = {"M0_gold_only": ("gold_k",),
            "M1_time_value": ("gold_k", "minute10", "gold_x_time")}
FRACTIONS = (0.45, 0.58, 0.71, 0.84, 0.96)
# Reuse the exact chronological boundaries from the existing notebook's
# development item experiment, instead of claiming this schedule was new.
PREEXISTING_FRACTIONS = (0.52, 0.60, 0.75, 0.92)
SEED = 20261113


def safe_boundaries(train: pd.DataFrame, fractions=FRACTIONS):
    """Series-safe contiguous, chronological boundaries from TRAIN metadata."""
    if not fractions or list(fractions) != sorted(set(fractions)):
        raise ValueError("Fractions must be distinct and ordered")
    if any(not 0 < x < 1 for x in fractions):
        raise ValueError("Fractions must be within (0,1)")
    info = train.sort_values(["start_time", "match_id"], kind="stable")
    spans = {}
    for i, row in enumerate(info.itertuples(index=False)):
        cluster = ("s", int(row.series_id)) if int(row.series_id)>0 else ("m",int(row.match_id))
        if cluster not in spans:
            spans[cluster]=[i,i]
        else:
            spans[cluster][1]=i
    cuts = [i for i in range(1,len(info))
            if all(not(lo<i<=hi) for lo,hi in spans.values())]
    if len(cuts)<len(fractions):
        raise ValueError("No sufficient series-safe cuts")
    boundaries = [min(cuts, key=lambda i: (abs(i-f*len(info)),i)) for f in fractions]
    if sorted(set(boundaries)) != boundaries:
        raise ValueError("Repeated or unordered split boundaries")
    return boundaries


def load_snapshot_function(root: Path):
    path=root/"tests/test_notebook_contracts.py"
    spec=importlib.util.spec_from_file_location("_train_only_contracts",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing source-contract definitions")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module.N["snapshot_features"]


def cache_path(cache: Path, match_id: int):
    key=hashlib.sha256(json.dumps(["/matches/"+str(match_id),{}],
                                 sort_keys=True).encode()).hexdigest()
    return cache/(key+".json.gz")


def build_training_rows(info: pd.DataFrame, cache: Path, snapshot_fn):
    if info.empty or not (info.partition=="train").all():
        raise ValueError("Only frozen TRAIN partition metadata allowed")
    rows=[]
    for item in info.itertuples(index=False):
        path=cache_path(cache,int(item.match_id))
        with gzip.open(path,"rt",encoding="utf8") as f:
            game=json.load(f)
        if (type(game.get("match_id")) is not int or
            int(game["match_id"]) != int(item.match_id) or
            int(game.get("start_time") or -1) != int(item.start_time) or
            int(game.get("patch") or -1) != int(item.patch) or
            int(game.get("series_id") or 0) != int(item.series_id) or
            type(game.get("radiant_win")) is not bool):
            raise ValueError("TRAIN source metadata or winner mismatched")
        for minute in range(int(game["duration"])//60+1):
            x=snapshot_fn(game,minute)
            rows.append({
                "match_id":int(item.match_id),
                "minute":minute,
                # For the chronology audit only, never a predictor input:
                "source_duration":int(game["duration"]),
                "radiant_win":int(game["radiant_win"]),
                **{k:x[k] for k in FEATURES["M1_time_value"]}
            })
    table=pd.DataFrame(rows)
    if table[["match_id","minute"]].duplicated().any():
        raise ValueError("Duplicate forecast key in TRAIN")
    return table


def fit(cols, table):
    pipeline=Pipeline([
        ("impute",SimpleImputer(strategy="median",keep_empty_features=True)),
        ("scale",StandardScaler()),
        ("logit",LogisticRegression(C=1.0,max_iter=1000,random_state=SEED))
    ])
    pipeline.fit(table[list(cols)],table.radiant_win)
    return pipeline


def compare_folds(info: pd.DataFrame, rows: pd.DataFrame,
                  fractions=FRACTIONS) -> dict:
    if not (info.partition=="train").all():
        raise ValueError("Non-train partition cannot be used in forward sensitivity")
    info=info.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
    per_game_duration=rows.groupby("match_id").source_duration.agg(["min","max"])
    if not (per_game_duration["min"]==per_game_duration["max"]).all():
        raise ValueError("A game's source duration changed between minutes")
    if set(per_game_duration.index)!=set(info.match_id):
        raise ValueError("TRAIN source games do not match frozen manifest")
    info["source_duration"]=info.match_id.map(per_game_duration["min"])
    bounds=safe_boundaries(info, fractions)
    result=[]
    for fold,(a,b) in enumerate(zip(bounds[:-1],bounds[1:]),1):
        evaluation_info=info.iloc[a:b]
        prior_info=info.iloc[:a]
        first_evaluation_start=int(evaluation_info.start_time.min())
        # Only use prior games that have approximately finished by eval start.
        # This is a stricter timing condition than a start-time-only split,
        # though pause/non-game telemetry is unavailable.
        completed_info=prior_info[
            prior_info.start_time+prior_info.source_duration<=first_evaluation_start]
        earlier=rows[rows.match_id.isin(completed_info.match_id)]
        next_block=rows[rows.match_id.isin(evaluation_info.match_id)]
        if earlier.empty or next_block.empty:
            raise RuntimeError("Empty training/evaluation block")
        if set(completed_info.series_id[completed_info.series_id>0]) & set(
                evaluation_info.series_id[evaluation_info.series_id>0]):
            raise RuntimeError("Series overlaps chronological forward fold")
        record={
            "fold":fold,
            "prior_games":len(prior_info),
            "completed_prior_games":len(completed_info),
            "embargoed_prior_games":len(prior_info)-len(completed_info),
            "evaluation_games":len(evaluation_info),
            "evaluation_minutes":len(next_block),
            "evaluation_patch_counts":{str(k):int(v)
                for k,v in evaluation_info.patch.value_counts().to_dict().items()},
            "evaluation_radiant_rate_per_minute":float(next_block.radiant_win.mean()),
            "evaluation_radiant_rate_per_match":float(
                next_block.groupby("match_id").radiant_win.first().mean()),
        }
        for name,cols in FEATURES.items():
            model=fit(cols,earlier)
            pred=model.predict_proba(next_block[list(cols)])[:,1]
            record[name+"_logloss"]=float(log_loss(next_block.radiant_win,pred,labels=[0,1]))
            record[name+"_brier"]=float(brier_score_loss(next_block.radiant_win,pred))
            if name=="M1_time_value":
                record["M1_time_interaction_standardized_coefficient"]=float(
                    model.named_steps["logit"].coef_[0][-1])
        record["M1_minus_M0_logloss"]=(record["M1_time_value_logloss"]-
                                      record["M0_gold_only_logloss"])
        record["M1_minus_M0_brier"]=(record["M1_time_value_brier"]-
                                    record["M0_gold_only_brier"])
        result.append(record)
    eval_total_minutes=sum(x["evaluation_minutes"] for x in result)
    return {
        "scope":"TRAIN partition only, series-safe chronological evaluation blocks",
        "boundary_fractions":[float(x) for x in fractions],
        "total_evaluation_games":sum(x["evaluation_games"] for x in result),
        "total_evaluation_minutes":eval_total_minutes,
        "pooled_minute_weighted_delta_logloss":sum(
            x["M1_minus_M0_logloss"]*x["evaluation_minutes"] for x in result
        )/eval_total_minutes,
        "pooled_minute_weighted_delta_brier":sum(
            x["M1_minus_M0_brier"]*x["evaluation_minutes"] for x in result
        )/eval_total_minutes,
        "interpretation":"Post-hoc exploratory stability, not new model selection or blind test",
        "training_games":int(info.match_id.nunique()),
        "training_rows":len(rows),
        "folds":result,
        "logloss_favorable_folds":sum(x["M1_minus_M0_logloss"]<0 for x in result),
        "brier_favorable_folds":sum(x["M1_minus_M0_brier"]<0 for x in result),
        "time_interaction_negative_folds":sum(
            x["M1_time_interaction_standardized_coefficient"]<0 for x in result),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--cache",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    info=pd.read_csv(a.manifest)
    info=info[info.partition=="train"].copy()
    root=Path(__file__).resolve().parents[1]
    rows=build_training_rows(info,a.cache,load_snapshot_function(root))
    result={
        "scope":"Post-hoc TRAIN-only model stability, not a new model-selection or blind-test procedure",
        "notebook_source_sha256":hashlib.sha256(
            (root/"live_dota2_win_probability.ipynb").read_bytes()).hexdigest(),
        "manifest_file_sha256":hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
        "train_match_ids_sha256":hashlib.sha256(
            json.dumps(sorted(info.match_id.astype(int).tolist())).encode()).hexdigest(),
        "preexisting_three_fold_schedule":compare_folds(info,rows,PREEXISTING_FRACTIONS),
        "alternate_four_fold_schedule":compare_folds(info,rows,FRACTIONS),
        "scope_caveats":[
            "The original final model and held-out predictions are unchanged.",
            "Train/evaluation blocks are chronology-ordered; repeated training blocks overlap.",
            "Estimated label completion uses match start_time plus game duration; actual pauses unavailable.",
            "Multiple post-hoc schedules were inspected. Neither is a confirmatory significance test."
        ],
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("TRAIN_ONLY_FORWARD_STABILITY",json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
