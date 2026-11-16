"""Reproduce the fixed TRAIN-only gold/XP-matched game-state illustration.

Uses only the source-frozen development feature archive (never TEST).
The pair was identified during the historical research; this script does
NOT select fresh match IDs, compare winners to choose pairs, or claim lift.
"""
from __future__ import annotations

import argparse
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
SOURCE = ROOT / "research" / "frozen_original_development_features.csv.gz"
DEFAULT_OUT = ROOT / "docs" / "figures" / "train_matched_state_aliasing.png"
MATCH_A, MATCH_B = 8739246794, 8739992397
COLUMNS = ("gold_k", "minute10", "gold_x_time")


def evidence():
    """Return original fixed-game evidence and model predictions, TRAIN only."""
    source = pd.read_csv(SOURCE)
    assert len(source) == 14456, "Frozen development archive changed size"
    train = source.loc[source["partition"] == "train"].copy()
    assert len(train) == 10675 and train.match_id.nunique() == 291
    assert set(train["partition"]) == {"train"}
    rows = train.loc[
        (train.match_id.isin([MATCH_A, MATCH_B])) & (train.minute == 25)
    ].sort_values("match_id")
    assert list(rows["match_id"]) == [MATCH_A, MATCH_B]
    assert list(rows["patch"]) == [59, 59]
    assert all(rows["radiant_win"] == 1)
    assert abs(float(rows.iloc[0].gold_k - rows.iloc[1].gold_k)) < 0.03
    assert abs(float(rows.iloc[0].xp_k - rows.iloc[1].xp_k)) < 0.11
    assert tuple(rows["tower_delta"].astype(int)) == (0, -1)
    assert tuple(rows["roshan_delta"].astype(int)) == (2, -1)

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("logistic", LogisticRegression(C=1., max_iter=1000, random_state=2026)),
    ])
    model.fit(train[list(COLUMNS)], train.radiant_win)
    probs = model.predict_proba(rows[list(COLUMNS)])[:, 1]
    np.testing.assert_allclose(probs, [0.603123, 0.604641], rtol=0, atol=0.00003)
    return train, rows.reset_index(drop=True), probs


def render(output: Path = DEFAULT_OUT) -> Path:
    train, rows, probs = evidence()
    fig = plt.figure(figsize=(9.4, 3.05), dpi=190)
    gs = fig.add_gridspec(1, 2, width_ratios=(1.02, 1.08), wspace=0.21)
    ax = fig.add_subplot(gs[0])
    colors = ["#176b86", "#cc703e"]
    for mid, color, label in zip((MATCH_A, MATCH_B), colors, ("A (TRAIN)", "B (TRAIN)")):
        series = train.loc[
            (train.match_id == mid) & (train.minute.between(19, 28))
        ].sort_values("minute")
        ax.plot(series.minute, series.gold_k, lw=1.85, c=color, label=label)
        at25 = rows.loc[rows.match_id == mid].iloc[0]
        ax.scatter([25], [at25.gold_k], s=39, zorder=6, c=color,
                   edgecolors="white", linewidths=0.65)
    ax.axvline(25, ls="--", lw=0.95, color="#536175", alpha=0.8)
    ax.axhline(0, lw=0.7, color="#96a0ad")
    ax.set_xlim(19, 28)
    ax.set_xticks([19, 21, 23, 25, 27])
    ax.set_xlabel("Match minute", fontsize=9)
    ax.set_ylabel("Radiant gold lead (thousands)", fontsize=9)
    ax.set_title("Economic trajectories", fontsize=10.5, weight="semibold", pad=7)
    ax.grid(alpha=0.17)
    ax.tick_params(labelsize=8.5)
    ax.legend(frameon=False, fontsize=8.2, loc="upper left")
    for s in ("top", "right"): ax.spines[s].set_visible(False)

    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    a, b = rows.iloc[0], rows.iloc[1]
    data = [
        ["Gold lead", f"+{int(a.gold_k*1000):,}", f"+{int(b.gold_k*1000):,}"],
        ["XP lead", f"+{int(a.xp_k*1000):,}", f"+{int(b.xp_k*1000):,}"],
        ["Tower delta", f"{int(a.tower_delta):+d}", f"{int(b.tower_delta):+d}"],
        ["Roshan kill delta", f"{int(a.roshan_delta):+d}", f"{int(b.roshan_delta):+d}"],
        ["M1 P(Radiant wins)", f"{probs[0]:.1%}", f"{probs[1]:.1%}"],
    ]
    table = ax2.table(cellText=data,
                      colLabels=["Available at 25:00", "A", "B"],
                      colWidths=[0.53, 0.23, 0.23],
                      cellLoc="center", loc="center",
                      bbox=[0, 0.14, 1.0, 0.76])
    table.auto_set_font_size(False)
    table.set_fontsize(8.7)
    for (i, j), cell in table.get_celld().items():
        cell.set_edgecolor("#d2d8df")
        cell.set_linewidth(0.4)
        if i == 0:
            cell.set_facecolor("#e8edf2")
            cell.set_text_props(weight="bold", color="#18273b")
        elif i % 2 == 1:
            cell.set_facecolor("#f7f9fb")
        if j == 0:
            cell.get_text().set_ha("left")
            cell.PAD = 0.08
    ax2.set_title("Matched economic state, unmatched objectives",
                  fontsize=10.2, weight="semibold", pad=7)
    ax2.text(0.5, 0.035, "Both Radiant teams won. No causal or predictive-lift claim.",
             ha="center", va="center", transform=ax2.transAxes,
             fontsize=8.2, color="#546273")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=190, facecolor="white",
                metadata={"Software": "Matplotlib; original TRAIN-only features"})
    plt.close(fig)
    return output


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    result = render(args.output)
    print(f"TRAIN-only matched-state figure: {result}")
    _, rows, probs = evidence()
    for i in range(2):
        r = rows.iloc[i]
        print(f"TRAIN match {int(r.match_id)}: gold={r.gold_k*1000:.0f}, "
              f"xp={r.xp_k*1000:.0f}, tower={int(r.tower_delta)}, "
              f"roshan={int(r.roshan_delta)}, p={probs[i]:.6f}")
