#!/usr/bin/env python3
"""Render the post-result TRAIN-only stronger-null falsification, no refitting.

Reads only the existing frozen TRAIN OOF comparison receipt. Does not touch
VAL/TEST rows or select a model from held-out evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json"
OUTPUT = ROOT / "docs/figures/train_interaction_vs_additive_null.png"


def audited_values() -> tuple[list[dict], float, tuple[float, float], int]:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    folds = data["folds"]
    overall = data["interaction_null_bootstrap"]["M1_minus_gold_time_null_logloss"]
    if (
        len(folds) != 4
        or sum(int(f["eval_games"]) for f in folds) != 137
        or data["oof_games"] != 137
        or data["interaction_null_bootstrap"]["groups"] != 70
        or data["null_model"] != ["gold_k", "minute10"]
        or data["comparison_model"] != ["gold_k", "minute10", "gold_x_time"]
        or data["model_promotion_permitted"]
        or data["original_validation_or_test_outcomes_read"]
    ):
        raise ValueError("TRAIN-only stronger-null receipt changed")
    value = float(overall["point"])
    lo, hi = map(float, overall["percentile_ci_95"])
    if not lo < value < 0 < hi or sum(f["delta_logloss"] < 0 for f in folds) != 1:
        raise ValueError("The non-confirmatory interaction comparison changed")
    return folds, value, (lo, hi), 70


def render(path: Path = OUTPUT) -> None:
    folds, point, (lo, hi), series_count = audited_values()
    navy = "#18354d"
    orange = "#b57542"
    blue = "#427b96"
    gray = "#7a8691"

    fig, ax = plt.subplots(figsize=(8.6, 3.10), dpi=190)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axvline(0.0, color=gray, linewidth=1.1, linestyle="--", zorder=1)
    ys = [4, 3, 2, 1]
    for i, (y, fold) in enumerate(zip(ys, folds), start=1):
        delta = float(fold["delta_logloss"])
        color = blue if delta < 0 else orange
        ax.plot([0, delta], [y, y], linewidth=2.0, color=color, alpha=0.55)
        ax.scatter([delta], [y], s=44, color=color, zorder=4)
        ax.text(delta + (0.001 if delta >= 0 else -0.001),
                y + 0.18, f"{delta:+.4f}", color=color, fontsize=8.3,
                ha="left" if delta >= 0 else "right", va="bottom")
    # Pairwise series-percentile CI is reported only for all four folds
    # combined. Individual dots have NO CI; do not imply otherwise.
    ax.hlines(0, lo, hi, color=navy, linewidth=3.0, zorder=2)
    ax.scatter([point], [0], marker="D", s=55, color=navy, zorder=5)
    ax.text(hi + 0.001, 0.0, "95% CI includes 0",
            fontsize=8.4, va="center", ha="left", color=navy)

    names = [f"Fold {i}  ·  {int(f['eval_games'])} games"
             for i, f in enumerate(folds, 1)]
    names.append(f"All folds · {series_count} series")
    ax.set_yticks(ys + [0], names)
    ax.set_ylim(-0.55, 4.75)
    ax.set_xlim(-0.025, 0.023)
    ax.set_xticks([-0.02, -0.01, 0.0, 0.01, 0.02])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{value:+.3f}" if value else "0"))
    ax.set_xlabel("M1 − additive gold+time log loss (negative favors M1)", fontsize=9.0, labelpad=6)
    ax.tick_params(axis="y", length=0, labelsize=9.2)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.grid(axis="x", alpha=0.12, color=gray, zorder=0)
    for edge in ("top", "right", "left"):
        ax.spines[edge].set_visible(False)
    ax.spines["bottom"].set_color("#b2bec9")
    fig.text(0.52, 0.035,
             "TRAIN-only forward evaluation | post-result analysis, not a fresh holdout",
             fontsize=8.1, ha="center", color="#566373")
    fig.subplots_adjust(left=0.23, right=0.98, top=0.96, bottom=0.37)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", pad_inches=0.10,
                metadata={"Software": "TRAIN-only frozen receipt visualization"})
    plt.close(fig)


if __name__ == "__main__":
    render()
    print(f"Figure generated strictly from frozen TRAIN receipt: {OUTPUT}")
