#!/usr/bin/env python3
"""Exploratory TRAIN-only lead-size x elapsed-time reliability audit.

Scientific scope:
- Exactly the original 291 TRAIN games / 10,675 minute snapshots. Never
  reads TEST forecasts, validation rows, raw future match payloads, or API.
- Fixed descriptive cells: |Radiant gold lead| in [2,4)k / [5,7)k,
  minutes 10,20,30. At most one row per game per cell. Sign-align to the
  *currently leading* team (NOT doubling or creating independent games).
- Show observed eventual leader-win fraction, naive Wilson intervals and
  cluster-resampled series intervals, alongside original M0/M1 FITTED-TRAIN
  probabilities on identical rows (in-sample; not evaluation).
- This is post-hoc exploratory insight, not a new blind validation, evidence
  of causal time effects, a new model, or a promotion gate.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TRAIN_ARCHIVE = ROOT / "research/frozen_original_train_features.csv.gz"
FIGURE = ROOT / "docs/figures/train_leader_state_empirical.png"
RECEIPT = ROOT / "docs/TRAIN_LEADER_STATE_EMPIRICAL_RECEIPT.json"
GOLD_BINS = ((2.0, 4.0), (5.0, 7.0))
MINUTES = (10, 20, 30)
SEED = 20261113
BOOTSTRAP_SEED = 20261116
N_BOOT = 5000
Z95 = 1.959963984540054
FEATURES = {
    "M0_gold_only": ("gold_k",),
    "M1_time_value": ("gold_k", "minute10", "gold_x_time"),
}
MODEL_SOURCE_SHA256 = "466dce5d64adf081fb20642df210f903794745714675e225415c0aa8770f8304"


def source_hash(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


def load_train() -> pd.DataFrame:
    train = pd.read_csv(TRAIN_ARCHIVE).sort_values(
        ["match_id", "minute"], kind="mergesort"
    ).reset_index(drop=True)
    required = {"match_id", "minute", "radiant_win", "gold_k", "minute10",
                "gold_x_time", "partition", "series_id"}
    assert required <= set(train), "Frozen TRAIN feature columns changed"
    assert train.shape[0] == 10675, "Wrong original TRAIN minute rows"
    assert train["partition"].eq("train").all(), "Non-TRAIN outcome would leak"
    assert train.match_id.nunique() == 291, "Wrong original TRAIN games"
    assert set(train.radiant_win.unique()) == {0, 1}, "Unexpected target labels"
    assert not train.duplicated(["match_id", "minute"]).any()
    assert all((g["minute"].to_numpy() == np.arange(len(g))).all()
               for _, g in train.groupby("match_id"))
    assert source_hash(ROOT / "live_dota2_win_probability.ipynb") == MODEL_SOURCE_SHA256, \
        "Original frozen scientific notebook changed; re-audit model provenance"
    return train


def original_train_fits(train: pd.DataFrame) -> dict[str, Pipeline]:
    """Use the original notebook's specified preprocessing and regression."""
    results = {}
    for name, columns in FEATURES.items():
        estimator = Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("logistic", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)),
        ])
        estimator.fit(train[list(columns)], train.radiant_win)
        results[name] = estimator
    return results


def wilson_interval(k: int, n: int) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("Cannot report a zero-denominator cell")
    p = k / n
    den = 1 + (Z95 ** 2) / n
    ctr = (p + (Z95 ** 2) / (2*n)) / den
    rad = Z95 * np.sqrt(p*(1-p)/n + (Z95**2)/(4*n*n)) / den
    return float(ctr-rad), float(ctr+rad)


def series_cluster_intervals(cell: pd.DataFrame, seed: int) -> tuple[float, float, int]:
    """Series/singleton resampling of whole game outcomes, not minute rows."""
    aggregate = cell.groupby("bootstrap_group", sort=True).agg(
        wins=("leader_won", "sum"), games=("leader_won", "size")
    ).to_numpy(dtype=float)
    if len(aggregate) < 2:
        raise ValueError("Too few groups for cluster sensitivity")
    rng = np.random.default_rng(seed)
    drawn = rng.integers(0, len(aggregate), size=(N_BOOT, len(aggregate)))
    draws = aggregate[drawn].sum(axis=1)
    rates = draws[:, 0]/draws[:, 1]
    return (*[float(x) for x in np.quantile(rates, [0.025, 0.975])], len(aggregate))


def evaluate() -> dict:
    train = load_train()
    fits = original_train_fits(train)
    one_row_per_time = train.loc[train.minute.isin(MINUTES)].copy()
    assert one_row_per_time.match_id.nunique() == 291
    # Exactly one team leads unless tied; ties cannot enter positive gold bins.
    one_row_per_time["radiant_leading"] = one_row_per_time.gold_k.gt(0)
    one_row_per_time["abs_gold_k"] = one_row_per_time.gold_k.abs()
    one_row_per_time["leader_won"] = np.where(
        one_row_per_time.radiant_leading,
        one_row_per_time.radiant_win,
        1 - one_row_per_time.radiant_win
    )
    one_row_per_time["bootstrap_group"] = [
        f"series_{int(s)}" if pd.notna(s) and int(s) > 0 else f"singleton_{int(m)}"
        for s, m in zip(one_row_per_time.series_id, one_row_per_time.match_id)
    ]
    for name, columns in FEATURES.items():
        p_radiant = fits[name].predict_proba(one_row_per_time[list(columns)])[:, 1]
        one_row_per_time[f"{name}_p_leader"] = np.where(
            one_row_per_time.radiant_leading, p_radiant, 1 - p_radiant
        )
    records = []
    for magnitude_idx, (lower, upper) in enumerate(GOLD_BINS):
        for minute_idx, minute in enumerate(MINUTES):
            cell = one_row_per_time.loc[
                (one_row_per_time.minute == minute)
                & (one_row_per_time.abs_gold_k >= lower)
                & (one_row_per_time.abs_gold_k < upper)
            ]
            assert not cell.empty, "Prespecified cell unsupported"
            assert not cell.duplicated("match_id").any()
            assert (cell.partition == "train").all()
            k, n = int(cell.leader_won.sum()), int(len(cell))
            wi = wilson_interval(k, n)
            grouped = series_cluster_intervals(
                cell, BOOTSTRAP_SEED + 10*magnitude_idx + minute_idx
            )
            records.append({
                "minute": minute,
                "abs_lead_lower_k": lower,
                "abs_lead_upper_exclusive_k": upper,
                "games": n,
                "eventual_leader_wins": k,
                "observed_leader_win_fraction": k/n,
                "wilson_95_by_game_descriptive": list(wi),
                "series_groups": grouped[2],
                "series_cluster_percentile_95_exploratory": list(grouped[:2]),
                "M0_training_fitted_mean_p_leader": float(
                    cell["M0_gold_only_p_leader"].mean()
                ),
                "M1_training_fitted_mean_p_leader": float(
                    cell["M1_time_value_p_leader"].mean()
                )
            })
    return {
        "analysis_type": "POST_HOC_EXPLORATORY_TRAIN_ONLY_DESCRIPTIVE",
        "selection_or_refit_using_TEST": False,
        "any_validation_rows_read": False,
        "any_TEST_rows_read": False,
        "not_causal": True,
        "not_a_model_selection_gate": True,
        "cohort": {
            "original_train_games": 291,
            "original_train_minute_rows": 10675,
            "patch_scope": "original TRAIN patches 59 and 60; cannot claim patch-invariant effect",
        },
        "fixed_grid": {
            "minutes": list(MINUTES),
            "absolute_gold_lead_k_half_open_bins": [list(x) for x in GOLD_BINS],
            "counting_unit": "one match at a specific minute/bin, never duplicated per team",
            "outcome": "eventual winner is the team that led at that minute",
        },
        "source": {
            "train_features_sha256": source_hash(TRAIN_ARCHIVE),
            "original_science_notebook_sha256": MODEL_SOURCE_SHA256,
            "original_model_fit": "TRAIN-only sklearn Pipeline median imputer, StandardScaler, logistic C=1",
            "bootstrap_series_or_singleton_seed": BOOTSTRAP_SEED,
            "bootstrap_draws_per_cell": N_BOOT
        },
        "limitations": [
            "Post-hoc chart design and original TRAIN in-sample model forecasts, not validation.",
            "Conditional on still playing at minute t; late survivors differ from early games.",
            "Cells differ in match makeup, patch balance and lead distribution within each bin.",
            "Wilson game intervals ignore series dependence; grouped intervals still ignore cross-series team/league dependence.",
            "Small cells, especially |gold| in [5k,7k) at minute 10, are unstable.",
            "No causal time effect, no confirmed mechanism or predictive lift; no new TEST inference.",
        ],
        "cells": records,
    }


def draw(receipt: dict, output: Path = FIGURE) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
    })
    fig, axes = plt.subplots(1, 2, figsize=(9.7, 3.25), dpi=190, sharey=True)
    ink, blue, ochre = "#152c43", "#1c6987", "#d28b4d"
    fig.patch.set_facecolor("white")
    for idx, ((lower, upper), ax) in enumerate(zip(GOLD_BINS, axes)):
        cells = sorted(
            [r for r in receipt["cells"] if r["abs_lead_lower_k"] == lower],
            key=lambda r: r["minute"]
        )
        x = np.array([r["minute"] for r in cells], dtype=float)
        observed = np.array([r["observed_leader_win_fraction"] for r in cells])
        ci = np.array([r["series_cluster_percentile_95_exploratory"] for r in cells])
        ax.errorbar(
            x, observed, yerr=np.vstack((observed-ci[:,0],ci[:,1]-observed)),
            fmt="o-", lw=2.0, markersize=6.2, capsize=3.8,
            color=ink, ecolor=ink, elinewidth=1.05, label="Observed (TRAIN)"
        )
        ax.plot(x, [r["M0_training_fitted_mean_p_leader"] for r in cells],
                linestyle="--", linewidth=1.5, color=blue,
                marker="s", markersize=4.0, label="M0 fitted (TRAIN)")
        ax.plot(x, [r["M1_training_fitted_mean_p_leader"] for r in cells],
                linestyle="--", linewidth=1.5, color=ochre,
                marker="^", markersize=4.0, label="M1 fitted (TRAIN)")
        for r in cells:
            y = r["observed_leader_win_fraction"]
            # Place sample counts above the grouped uncertainty whiskers.
            upper_y = r["series_cluster_percentile_95_exploratory"][1]
            ax.annotate(
                f"n={r['games']}",
                (r["minute"], min(0.995, upper_y+0.065)), ha="center",
                fontsize=8, color=ink
            )
        ax.set_title(f"|Gold lead| {int(lower)}–{int(upper)}k", pad=9)
        ax.set_xlabel("Game minute")
        ax.set_xticks(MINUTES)
        ax.set_xlim(7, 33)
        ax.set_ylim(0, 1.1)
        ax.set_yticks([0, .2, .4, .6, .8, 1.])
        ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
        ax.grid(axis="y", alpha=.14)
        for s in ("top","right"):
            ax.spines[s].set_visible(False)
        if idx == 0:
            ax.set_ylabel("Eventual leader win fraction")
    axes[1].legend(frameon=False, fontsize=7.7,
                   loc="lower left", bbox_to_anchor=(.01, -.035))
    fig.text(.5, .025, "Grouped CI by series  •  in-sample fitted probabilities  •  conditional on game survival",
             ha="center", va="bottom", fontsize=8.1, color="#526273")
    fig.subplots_adjust(left=.065,right=.985,bottom=.2,top=.88,wspace=.16)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=190, facecolor="white",
                bbox_inches="tight", pad_inches=.11,
                metadata={"Software": "Original TRAIN-only exploratory outcome audit"})
    plt.close(fig)


def main() -> None:
    receipt = evaluate()
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)+"\n",
        encoding="utf-8"
    )
    draw(receipt)
    for r in receipt["cells"]:
        print(f"|gold| [{r['abs_lead_lower_k']:.0f},{r['abs_lead_upper_exclusive_k']:.0f})k "
              f"minute {r['minute']}: {r['eventual_leader_wins']}/{r['games']} "
              f"={r['observed_leader_win_fraction']:.3%}; "
              f"series CI {r['series_cluster_percentile_95_exploratory']}; "
              f"TRAIN-fitted M0/M1 "
              f"{r['M0_training_fitted_mean_p_leader']:.3f}/"
              f"{r['M1_training_fitted_mean_p_leader']:.3f}")
    print("NONSELECTING_POST_HOC_TRAIN_ONLY:", RECEIPT, FIGURE)


if __name__ == "__main__":
    main()
