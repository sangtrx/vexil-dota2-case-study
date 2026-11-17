#!/usr/bin/env python3
"""One fixed Quant Bible path-dependent predictor; post-result TRAIN ONLY.

Protocol committed first at research/QUANT_BIBLE_PATH_PROTOCOL.md.
Original VAL and TEST rows are never read, so this cannot claim a fresh TEST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from conditional_gold_forward import FROZEN_CUTS, loss, series_bootstrap
from train_time_effect_ci import (
    FEATURES, MANIFEST_SHA, TRAIN_SHA, cluster_ids, model, require_data,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/QUANT_BIBLE_PATH_PROTOCOL.md"
RESULT = ROOT / "research/QUANT_BIBLE_PATH_RECEIPT.json"
REPORT = ROOT / "research/QUANT_BIBLE_PATH_READOUT.md"
BIBLE_SHA = "a9e2a4fcee068bff3956bba2066e3848b5bfe4c1"
SEED = 20261113
ADDITIVE = ["gold_k", "minute10"]
PATH = ADDITIVE + [
    "adverse_excursion10_k", "signed_realized_vol10_k",
    "directional_efficiency10",
]
MODELS = {"M0_gold": ["gold_k"], "A_additive": ADDITIVE,
          "M1_interaction": FEATURES, "Q1_path": PATH}


def prefix_path_features(prefix: np.ndarray) -> np.ndarray:
    """Evaluate features at current prefix end, with fixed past-10 horizon."""
    a = np.asarray(prefix, dtype=np.float64)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError("Prefix must be finite 1-D gold path")
    window = a[max(0, len(a) - 11):]
    current = float(window[-1])
    side = float(np.sign(current))
    increments = np.diff(window)
    excursion = side * max(0.0, float(np.max(side * window)) - abs(current))
    rv = side * float(np.sqrt(np.mean(np.square(increments)))) if len(increments) else 0.0
    efficiency = (current - float(window[0])) / (float(np.abs(increments).sum()) + 1e-6)
    if not len(increments):
        efficiency = 0.0
    value = np.asarray([excursion, rv, efficiency], dtype=float)
    if not np.isfinite(value).all() or abs(efficiency) > 1 + 1e-9:
        raise ValueError("Invalid prefix feature")
    return value


def construct_path_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required = {"match_id", "minute", "gold_k", "partition"}
    if not required.issubset(frame) or set(frame.partition) != {"train"}:
        raise ValueError("Attempted access outside locked TRAIN or missing input")
    if frame[["match_id", "minute"]].duplicated().any():
        raise ValueError("Duplicate forecast opportunity")
    df = frame.sort_values(["match_id", "minute"], kind="stable").copy()
    vals = np.empty((len(df), 3), dtype=float)
    audited = 0
    for _, sub in df.groupby("match_id", sort=False):
        minute = sub.minute.to_numpy(int)
        if not np.array_equal(minute, np.arange(len(minute))):
            raise ValueError("Per-match minute series has gaps or nonzero origin")
        gold = sub.gold_k.to_numpy(dtype=float)
        chunk = np.empty((len(gold), 3), dtype=float)
        for t in range(len(gold)):
            prefix = gold[:t+1]
            v = prefix_path_features(prefix)
            # An independent causal-prefix check: arbitrary changes to the
            # suffix do not change the current feature value. Tested on
            # every original TRAIN match/minute, including the last row.
            poison = gold.copy()
            if t + 1 < len(gold):
                poison[t+1:] = np.arange(1, len(gold)-t, dtype=float) * 1e6
            if not np.allclose(v, prefix_path_features(poison[:t+1]), rtol=0, atol=1e-12):
                raise AssertionError("Future suffix changed feature")
            mirror = prefix_path_features(-prefix)
            if not np.allclose(mirror, -v, rtol=0, atol=1e-12):
                raise AssertionError("Team-sign symmetry failed")
            chunk[t] = v
            audited += 1
        vals[df.index.get_indexer(sub.index)] = chunk
    for idx, name in enumerate(PATH[2:]):
        df[name] = vals[:, idx]
    if audited != 10675 or len(df) != 10675 or df.match_id.nunique() != 291:
        raise ValueError("Original TRAIN size changed")
    return df, {"audited_prefixes": audited, "mirror_symmetry_pass": audited,
                "feature_names": PATH[2:], "window": "last 10 past minute increments"}


def train_only_forward(df: pd.DataFrame) -> dict:
    meta = df[["match_id", "start_time", "duration", "series_id"]].drop_duplicates()
    meta = meta.sort_values(["start_time", "match_id"], kind="stable").reset_index(drop=True)
    if len(meta) != 291 or tuple(FROZEN_CUTS) != (154, 176, 220, 252, 291):
        raise ValueError("Frozen TRAIN forward design changed")
    pred = []
    folds = []
    for fold_id, (left, right) in enumerate(zip(FROZEN_CUTS[:-1], FROZEN_CUTS[1:]), 1):
        older = meta.iloc[:left]
        eval_meta = meta.iloc[left:right]
        t0 = int(eval_meta.iloc[0].start_time)
        eligible = older[older.start_time + older.duration <= t0]
        train_ids = set(eligible.match_id)
        eval_ids = set(eval_meta.match_id)
        if set(cluster_ids(older)) & set(cluster_ids(eval_meta)):
            raise ValueError("Nominal series crosses forward split")
        if set(cluster_ids(eligible)) & set(cluster_ids(eval_meta)):
            raise ValueError("Mature TRAIN series crosses forward split")
        if not train_ids.isdisjoint(eval_ids) or not len(eval_ids):
            raise ValueError("TRAIN/EVAL mismatch")
        train = df[df.match_id.isin(train_ids)]
        ev = df[df.match_id.isin(eval_ids)]
        y = ev.radiant_win.to_numpy(dtype=float)
        record = ev[["match_id", "series_id", "minute"]].copy()
        fold_result = {
            "fold": fold_id, "fit_completed_games": len(train_ids),
            "eval_games": len(eval_ids), "eval_rows": len(ev),
            "embargoed_unfinished_labels": len(older)-len(eligible),
            "patch": "train-only original chronology"
        }
        for name, columns in MODELS.items():
            fitted = model().fit(train[columns], train.radiant_win.astype(int))
            prob = fitted.predict_proba(ev[columns])[:, 1]
            if not (np.isfinite(prob).all() and (prob > 0).all() and (prob < 1).all()):
                raise AssertionError("Invalid probability for " + name)
            ll, br = loss(y, prob)
            record["ll_" + name] = ll
            record["br_" + name] = br
            fold_result[name] = {
                "logloss": float(ll.mean()), "brier": float(br.mean()),
                "late30_brier": float(br[ev.minute.to_numpy() >= 30].mean())
                 if (ev.minute >= 30).any() else None,
            }
        for other in ("M0_gold", "A_additive", "M1_interaction"):
            fold_result["Q1_minus_" + other + "_logloss"] = float(
                (record.ll_Q1_path - record["ll_" + other]).mean())
            fold_result["Q1_minus_" + other + "_brier"] = float(
                (record.br_Q1_path - record["br_" + other]).mean())
        folds.append(fold_result)
        pred.append(record)

    out = pd.concat(pred, ignore_index=True)
    if len(out) != 5081 or out.match_id.nunique() != 137:
        raise ValueError("Expected 5,081 rows / 137 TRAIN OOF games")
    if out[["match_id", "minute"]].duplicated().any() or len(set(cluster_ids(out))) != 70:
        raise ValueError("Forward group identity drift")
    comparison = {}
    for other in ("M0_gold", "A_additive", "M1_interaction"):
        delta_ll = out.ll_Q1_path - out["ll_" + other]
        delta_br = out.br_Q1_path - out["br_" + other]
        pair = out[["match_id", "series_id", "minute"]].copy()
        pair["delta_logloss"] = delta_ll
        pair["delta_brier"] = delta_br
        boot = series_bootstrap(pair, draws=5000)
        late = out.minute >= 30
        grouped = pair.copy()
        grouped["group"] = cluster_ids(grouped)
        sums = grouped.groupby("group", sort=True)["delta_logloss"].sum()
        gain = -float(sums.sum())
        concentration = float((-sums).clip(lower=0).max() / gain) if gain > 0 else None
        fold_wins = sum(d["Q1_minus_" + other + "_logloss"] < 0 for d in folds)
        comparison[other] = {
            "logloss": boot["M1_minus_M0_logloss"],
            "brier": boot["M1_minus_M0_brier"],
            "late30_delta_brier": float(delta_br[late].mean()),
            "forward_fold_wins": fold_wins,
            "max_positive_group_gain_share": concentration,
        }
    # Regression oracle: the stronger gold+time null and existing M1 must
    # reproduce the earlier independently executed TRAIN-only fixed cuts.
    prior = json.loads((ROOT / "research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json").read_text())
    for old, new in zip(prior["folds"], folds):
        observed = new["M1_interaction"]["logloss"] - new["A_additive"]["logloss"]
        if not np.isclose(observed, old["delta_logloss"], rtol=0, atol=1e-12):
            raise AssertionError("Baseline TRAIN-forward oracle differs")
    qA = comparison["A_additive"]
    qM = comparison["M1_interaction"]
    def passes(row):
        return (row["logloss"]["point"] <= -0.0025
                and row["logloss"]["percentile_ci_95"][1] < 0
                and row["forward_fold_wins"] >= 3
                and row["brier"]["point"] <= 0
                and row["late30_delta_brier"] <= 0)
    qualifies = (passes(qA) and passes(qM)
        and qA["max_positive_group_gain_share"] is not None
        and qA["max_positive_group_gain_share"] < 0.5)
    return {
        "folds": folds,
        "oof_games": int(out.match_id.nunique()),
        "oof_rows": int(len(out)),
        "oof_series_or_singletons": int(len(set(cluster_ids(out)))),
        "models": MODELS,
        "q1_comparison": comparison,
        "predeclared_gate_met": bool(qualifies),
        "promote_into_original_submission": False,
    }


def result_object() -> dict:
    src = ROOT / "research/frozen_original_train_features.csv.gz"
    if hashlib.sha256(src.read_bytes()).hexdigest() != TRAIN_SHA:
        raise ValueError("Frozen source hash drift")
    df = require_data()  # validates manifest/hash; reads TRAIN only
    enriched, audit = construct_path_features(df)
    result = train_only_forward(enriched)
    return {
        "scope": "POST_RESULT_TRAIN_ONLY_EXPLORATORY_NONBLIND",
        "original_VAL_or_TEST_loaded": False,
        "no_new_model_selected_on_TEST": True,
        "source_train_sha256": TRAIN_SHA,
        "source_manifest_sha256": MANIFEST_SHA,
        "quant_bible_git_commit": BIBLE_SHA,
        "protocol": "research/QUANT_BIBLE_PATH_PROTOCOL.md",
        "feature_prefix_audit": audit,
        **result,
    }


def markdown_receipt(data: dict) -> str:
    c = data["q1_comparison"]
    def info(name):
        a = c[name]
        ci = a["logloss"]["percentile_ci_95"]
        return (f"{a['logloss']['point']:+.6f} [{ci[0]:+.6f},{ci[1]:+.6f}]",
                f"{a['brier']['point']:+.6f}",
                str(a["forward_fold_wins"]))
    cols = [(n, *info(n)) for n in ("M0_gold", "A_additive", "M1_interaction")]
    table = "\n".join(
        f"| {n} | {ll} | {br} | {wins}/4 |" for n, ll, br, wins in cols)
    fold_rows = "\n".join(
        f"| {f['fold']} | {f['eval_games']} | {f['Q1_minus_A_additive_logloss']:+.6f} | "
        f"{f['Q1_minus_M1_interaction_logloss']:+.6f} |"
        for f in data["folds"])
    risks = "\n".join(
        f"| {name} | {c[name]['brier']['point']:+.6f} | "
        f"{c[name]['late30_delta_brier']:+.6f} | "
        f"{c[name]['max_positive_group_gain_share']:.1%} |"
        if c[name]['max_positive_group_gain_share'] is not None
        else f"| {name} | {c[name]['brier']['point']:+.6f} | "
             f"{c[name]['late30_delta_brier']:+.6f} | n/a |"
        for name in ("M0_gold", "A_additive", "M1_interaction"))
    return f"""# One Quant Bible path-dependence idea — actually tested on TRAIN

**Verdict:** {"MET exploratory predeclared gate (still no new blind TEST)" if data["predeclared_gate_met"] else "FAILED predeclared gate; do not add Q1 to Vexil employer notebook"}.

This is a **post-original-TEST, 291-game TRAIN-only** sensitivity,
not an independent replication. The required notebook, M0/M1 selection,
TEST predictions and user-owned disclosure are unchanged.
The motivating question is whether recent drawdown, volatility and
directionality of gold lead add information after controlling for the
current lead and elapsed game time. Section 8 of the Quant Research
Bible treats transforms as additional models subject to selection risk.

**Predefined model:** five-feature Q1 = gold, time, signed ten-minute
adverse excursion, signed ten-minute lead realized volatility and
ten-minute directional path efficiency. No hyperparameter/window
search. All **{data["feature_prefix_audit"]["audited_prefixes"]}**
source TRAIN forecasts passed causal-prefix and team-symmetry checks.

## Original TRAIN-only chronological forward scores

Rows are Q1 minus the named comparator; negative means Q1 wins.
**Unadjusted percentile 95% CI uses 5,000 paired resamples of
{data["oof_series_or_singletons"]} professional series/singletons.**
It is descriptive after historical model searches, not a new p-value.

| Comparator | Mean Δ log loss [95% CI] | Mean Δ Brier | Q1 better folds |
| --- | ---: | ---: | ---: |
{table}

| Fold | Eval games | ΔLL vs additive | ΔLL vs M1 |
| --- | ---: | ---: | ---: |
{fold_rows}

| Comparator | Q1 Δ overall Brier | Q1 Δ Brier at minute 30+ | Largest favorable cluster / total LL gain |
| --- | ---: | ---: | ---: |
{risks}

The largest favorable cluster's percentage is a concentration
**diagnostic**, not a probability. The uncertainty intervals in the
first table are **not adjusted for previous searches of 28+ features**;
the original TEST was opened before this idea was introduced.

**Design:** four existing forward TRAIN blocks, **{data["oof_games"]} games /
{data["oof_rows"]} minute forecasts**. A training label is admitted only
when the professional match ended before the next evaluation block
starts, *not* when true source `received_at` was observed (unavailable).
No original VALIDATION/TEST feature or outcome rows were loaded;
only the fixed split manifest of match IDs was inspected.
Q1 was tested once using the frozen window/features and regularization.

**Decision:** {"Q1 earns only a future, genuinely blind replication test." if data["predeclared_gate_met"] else "Q1 passes the directional and Brier point-estimate checks but fails the predeclared superiority condition versus M1: the 95% log-loss CI still includes zero. Do not promote it."} A discarded
hypothesis with a clear negative control is evidence of scientific
creativity, not proof of predictive improvement or 10/10 from Vexil.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = result_object()
    txt = markdown_receipt(data)
    if args.write:
        RESULT.write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n")
        REPORT.write_text(txt)
        print("WROTE", RESULT.name, REPORT.name)
    else:
        if data != json.loads(RESULT.read_text()) or txt != REPORT.read_text():
            raise AssertionError("Fixed-model scientific receipt is not reproducible")
        print("PASS: candidate and receipt reproduce without VAL/TEST")
    print("Q1_PROMOTION_GATE", data["predeclared_gate_met"])
    for other, vals in data["q1_comparison"].items():
        print(other, vals["logloss"], vals["brier"],
              "wins", vals["forward_fold_wins"],
              "lateBrier", vals["late30_delta_brier"])


if __name__ == "__main__":
    main()
