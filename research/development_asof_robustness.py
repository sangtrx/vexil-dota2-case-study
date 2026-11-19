#!/usr/bin/env python3
"""Post-result, development-only label-arrival and regime sensitivity.

FROZEN source: 394 TRAIN/VALIDATION games from the original 500-game study.
Only metadata start_time for TEST is read, never TEST labels or predictions.
Outputs cannot be used to replace M1, which was selected using VALIDATION before TEST inspection.
Usage:
  python research/development_asof_robustness.py --write
  python research/development_asof_robustness.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import scipy
import sklearn

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs" / "DEVELOPMENT_ASOF_ROBUSTNESS_RECEIPT.json"
INPUTS = {
    "research/frozen_original_development_features.csv.gz":
        "d4f91431d2c373eb772093bbf26ecb9c37c62714f95e89e0500e30b7700bd628",
    "research/frozen_original_train_features.csv.gz":
        "066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915",
    "research/frozen_original_split_manifest.csv":
        "8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216",
}
SETS = {
    "M0_gold_only": ["gold_k"],
    "M1_time_value": ["gold_k", "minute10", "gold_x_time"],
    "M2_lead_fragility": ["gold_k", "minute10", "gold_x_time",
                          "xp_k", "gold_velocity5_k", "xp_velocity5_k"],
    "M3_objective_conversion": ["gold_k", "minute10", "gold_x_time",
                                "xp_k", "gold_velocity5_k", "xp_velocity5_k",
                                "tower_delta", "barracks_delta", "roshan_delta",
                                "kill_delta"],
}
BUFFERS_MINUTES = (0, 3, 15, 30, 60, 120)
CUTS = (154, 176, 220, 252, 291)


def fit(train: pd.DataFrame, cols: list[str]):
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("logistic", LogisticRegression(C=1., max_iter=1000, random_state=20261113)),
    ])
    model.fit(train[cols], train["radiant_win"])
    return model


def scores(train: pd.DataFrame, val: pd.DataFrame) -> dict:
    if train["match_id"].nunique() < 200 or val["match_id"].nunique() < 20:
        raise ValueError("Insufficient development cohort")
    out = {}
    for name, cols in SETS.items():
        p = fit(train, cols).predict_proba(val[cols])[:, 1]
        out[name] = {
            "logloss": float(log_loss(val.radiant_win, p, labels=[0, 1])),
            "brier": float(brier_score_loss(val.radiant_win, p)),
        }
    return out


def compute() -> dict:
    for rel, expected in INPUTS.items():
        got = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if got != expected:
            raise ValueError("Source digest drift: " + rel)
    dev = pd.read_csv(ROOT / "research/frozen_original_development_features.csv.gz")
    train_full = pd.read_csv(ROOT / "research/frozen_original_train_features.csv.gz")
    # Import only allowed metadata columns; never TEST outcomes, TEST features or TEST probabilities.
    meta = pd.read_csv(ROOT / "research/frozen_original_split_manifest.csv")
    if set(meta.columns) != {"match_id", "start_time", "patch", "series_id", "partition"}:
        raise ValueError("Unexpected manifest metadata")
    if (len(dev) != 14456 or dev.match_id.nunique() != 394
            or len(train_full) != 10675 or train_full.match_id.nunique() != 291
            or meta.partition.value_counts().to_dict()
            != {"train": 291, "validation": 103, "test": 106}):
        raise ValueError("Frozen cohort changed")
    train = dev.loc[dev.partition == "train"].copy()
    val = dev.loc[dev.partition == "validation"].copy()
    match_tr = train[["match_id", "start_time", "duration"]].drop_duplicates()
    match_va = val[["match_id", "start_time", "duration"]].drop_duplicates()
    if (len(match_tr) != 291 or len(match_va) != 103
            or set(train.match_id) != set(train_full.match_id)
            or set(train.match_id) & set(val.match_id)):
        raise ValueError("Development partition invalid")
    first_val = int(meta.loc[meta.partition == "validation", "start_time"].min())
    first_test = int(meta.loc[meta.partition == "test", "start_time"].min())

    asof = []
    for mins in BUFFERS_MINUTES:
        lag = 60 * mins
        tid = set(match_tr.loc[
            match_tr.start_time + match_tr.duration + lag <= first_val,
            "match_id",
        ].astype(int))
        vid = set(match_va.loc[
            match_va.start_time + match_va.duration + lag <= first_test,
            "match_id",
        ].astype(int))
        fitted = train[train.match_id.isin(tid)]
        all_val = scores(fitted, val)
        mature_val = scores(fitted, val[val.match_id.isin(vid)])
        selected = min(mature_val, key=lambda n: mature_val[n]["logloss"])
        asof.append({
            "assumed_extra_label_lag_minutes": mins,
            "mature_train_games": len(tid),
            "mature_val_games_at_first_test": len(vid),
            "mature_val_minute_rows": int(val.match_id.isin(vid).sum()),
            "validation_103_scores_with_mature_train_only": all_val,
            "label_mature_val_subset_scores": mature_val,
            "lowest_loss_on_mature_val_subset": selected,
            "selection_is_post_result_sensitivity_not_new_model": True,
        })

    # Forward-fold context: older maturing games only, never the held-out TEST.
    info = train_full[["match_id", "start_time", "duration", "series_id"]].drop_duplicates()
    info = info.sort_values(["start_time", "match_id"], kind="stable").reset_index(drop=True)
    if len(info) != 291:
        raise ValueError("Incorrect original TRAIN forward cohort")
    patch_lookup = dict(zip(meta.match_id.astype(int), meta.patch.astype(int)))
    folds = []
    for left, right in zip(CUTS[:-1], CUTS[1:]):
        first = int(info.iloc[left].start_time)
        past = info.iloc[:left]
        eligible = set(past.loc[past.start_time + past.duration <= first,
                                "match_id"].astype(int))
        future = set(info.iloc[left:right].match_id.astype(int))
        # Explicit whole-series isolation, in addition to chronological rows.
        past_groups = {("s", int(r.series_id)) if int(r.series_id) > 0
                       else ("m", int(r.match_id))
                       for r in past.itertuples() if int(r.match_id) in eligible}
        future_groups = {("s", int(r.series_id)) if int(r.series_id) > 0
                         else ("m", int(r.match_id))
                         for r in info.iloc[left:right].itertuples()}
        if past_groups & future_groups:
            raise ValueError("Series leak in frozen TRAIN fold")
        older = train_full[train_full.match_id.isin(eligible)]
        newer = train_full[train_full.match_id.isin(future)]
        if len(newer) == 0 or not set(older.match_id).isdisjoint(set(newer.match_id)):
            raise ValueError("Bad forward fold")
        p0 = fit(older, SETS["M0_gold_only"]).predict_proba(
            newer[SETS["M0_gold_only"]])[:, 1]
        p1 = fit(older, SETS["M1_time_value"]).predict_proba(
            newer[SETS["M1_time_value"]])[:, 1]
        y = newer.radiant_win.to_numpy(int)
        prevalence = float(older.radiant_win.mean())
        cst = np.full(len(newer), prevalence, dtype=float)
        folds.append({
            "fit_games": len(eligible),
            "later_eval_games": len(future),
            "later_eval_minute_rows": len(newer),
            "fit_patch60_games": sum(patch_lookup[x] == 60 for x in eligible),
            "eval_patch60_games": sum(patch_lookup[x] == 60 for x in future),
            "fit_minute_win_fraction": prevalence,
            "eval_minute_win_fraction": float(y.mean()),
            "constant_train_prevalence_logloss": float(log_loss(y, cst, labels=[0, 1])),
            "M0_logloss": float(log_loss(y, p0, labels=[0, 1])),
            "M1_logloss": float(log_loss(y, p1, labels=[0, 1])),
        })
    if ([f["later_eval_games"] for f in folds] != [22, 44, 32, 39]
            or [f["later_eval_minute_rows"] for f in folds] != [771, 1649, 1228, 1433]):
        raise ValueError("TRAIN forward cohort changed")
    pooled_n = sum(f["later_eval_minute_rows"] for f in folds)
    return {
        "evidence_class": "POST_RESULT_DEVELOPMENT_ONLY_SENSITIVITY",
        "sources_sha256": INPUTS,
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "verified_environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "sklearn": sklearn.__version__,
        },
        "source_access_manifest": list(INPUTS),
        "forecast_test_records_read": False,
        "original_model_or_test_scores_changed": False,
        "live_received_at_verified": False,
        "label_end_proxy_note":
            "start_time+game_duration omits pause/pregame/postgame and real arrival time; lag values are hypothetical, not measured",
        "lag_grid_minutes": list(BUFFERS_MINUTES),
        "asof": asof,
        "forward_fold_cuts": list(CUTS),
        "forward_fold_context": folds,
        "forward_pooled": {
            "minute_rows": pooled_n,
            "M0_logloss": float(sum(f["M0_logloss"] * f["later_eval_minute_rows"] for f in folds) / pooled_n),
            "M1_logloss": float(sum(f["M1_logloss"] * f["later_eval_minute_rows"] for f in folds) / pooled_n),
            "constant_logloss": float(sum(f["constant_train_prevalence_logloss"] * f["later_eval_minute_rows"] for f in folds) / pooled_n),
        },
    }


def _same_evidence(actual, expected, path="root") -> None:
    # Hashes, identifiers, flags, labels, group counts and source versions
    # must match EXACTLY. Numeric float outputs may vary at 1e-9 across
    # equivalent pinned BLAS implementations; do not require bitwise parity.
    if type(actual) is not type(expected):
        raise ValueError("Type drift at " + path)
    if path == "root.verified_environment.python":
        # Preserve the exact executing interpreter in the receipt, but allow
        # compatible Python 3.12 patch versions. Reject minor/major changes.
        def minor_version(value):
            parts = value.split(".")
            if len(parts) != 3 or not all(part.isdecimal() for part in parts):
                raise ValueError("Malformed Python version at " + path)
            return tuple(map(int, parts[:2]))
        if minor_version(actual) != minor_version(expected):
            raise ValueError("Python major/minor version mismatch at " + path)
        return
    if isinstance(actual, float):
        if not math.isfinite(actual) or not math.isclose(
            actual, expected, rel_tol=0.0, abs_tol=1e-9
        ):
            raise ValueError("Float drift at " + path)
    elif isinstance(actual, dict):
        if set(actual) != set(expected):
            raise ValueError("Receipt key drift at " + path)
        for key in actual:
            _same_evidence(actual[key], expected[key], path + "." + key)
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            raise ValueError("Receipt length drift at " + path)
        for index, (left, right) in enumerate(zip(actual, expected)):
            _same_evidence(left, right, path + "[" + str(index) + "]")
    elif actual != expected:
        raise ValueError("Receipt drift at " + path)


def verify(result: dict) -> None:
    saved = json.loads(RECEIPT.read_text())
    _same_evidence(result, saved)
    if result["forecast_test_records_read"] is not False:
        raise ValueError("Forbidden TEST access declaration")
    if result["original_model_or_test_scores_changed"] is not False:
        raise ValueError("Forbidden original model change declaration")
    if result["live_received_at_verified"] is not False:
        raise ValueError("Unobserved live arrival incorrectly claimed")

    if ([x["mature_train_games"] for x in result["asof"]]
            != [286, 285, 283, 282, 277, 272]):
        raise ValueError("Mature TRAIN count mismatch")
    if ([x["mature_val_games_at_first_test"] for x in result["asof"]]
            != [103, 102, 101, 100, 96, 90]):
        raise ValueError("Mature VAL count mismatch")
    if result["asof"][4]["lowest_loss_on_mature_val_subset"] != "M2_lead_fragility":
        raise ValueError("Expected 60-minute negative-sensitivity finding missing")
    if not abs(result["forward_pooled"]["M0_logloss"] - 0.612312) < 2e-5:
        raise ValueError("TRAIN-forward pooled M0 drift")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    if args.write:
        RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    else:
        verify(result)
    print(json.dumps({
        "status": "DEVELOPMENT_ONLY_" + ("RECEIPT_WRITTEN" if args.write else "PASS"),
        "mature_train_counts": [x["mature_train_games"] for x in result["asof"]],
        "mature_val_counts": [x["mature_val_games_at_first_test"] for x in result["asof"]],
        "lowest_loss_by_lag": [x["lowest_loss_on_mature_val_subset"] for x in result["asof"]],
        "forward_pooled": result["forward_pooled"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
