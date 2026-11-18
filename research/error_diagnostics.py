"""Read-only error audit for frozen Vexil per-minute probabilities.

This script must never fit models, retrieve data, change decision thresholds,
choose new features, or promote a model using inspected held-out outcomes.

Usage:
    python research/error_diagnostics.py
    python research/error_diagnostics.py --json docs/ERROR_AUDIT_RECEIPT.json --check
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "heldout_predictions.csv"
EXPECTED_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
PHASES = ("0-9", "10-19", "20-29", "30+")
REQUIRED_COLUMNS = {"match_id", "minute", "p_model", "p_baseline", "radiant_win"}


def load_rows(path: Path = SOURCE) -> list[dict]:
    with path.open(encoding="utf8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED_COLUMNS.issubset(reader.fieldnames or ()):
            raise ValueError("Missing required frozen forecast columns")
        rows = []
        keys = set()
        labels = {}
        for source in reader:
            mid, t = int(source["match_id"]), int(source["minute"])
            if mid <= 0 or t < 0 or (mid, t) in keys:
                raise ValueError("Invalid/duplicate match-minute row")
            keys.add((mid, t))
            y = int(source["radiant_win"])
            if y not in (0, 1) or (mid in labels and labels[mid] != y):
                raise ValueError("Invalid or time-varying outcome")
            labels[mid] = y
            p0, p1 = float(source["p_baseline"]), float(source["p_model"])
            if not (math.isfinite(p0) and math.isfinite(p1) and
                    0 < p0 < 1 and 0 < p1 < 1):
                raise ValueError("Probability outside (0,1)")
            rows.append({
                "match_id": mid, "minute": t, "radiant_win": y,
                "p0": p0, "p1": p1,
                "ll0": -y * math.log(p0) - (1-y) * math.log1p(-p0),
                "ll1": -y * math.log(p1) - (1-y) * math.log1p(-p1),
                "brier0": (p0-y)**2, "brier1": (p1-y)**2,
            })
    if not rows:
        raise ValueError("No forecasts")
    return rows


def phase(t: int) -> str:
    return "0-9" if t <= 9 else "10-19" if t <= 19 else "20-29" if t <= 29 else "30+"


def ece10(rows: list[dict], pkey: str) -> float:
    """Fixed equal-width descriptive ECE; rows in a match are correlated."""
    by_bin = [[0., 0., 0] for _ in range(10)]
    for r in rows:
        p = r[pkey]
        b = min(int(10 * p), 9)
        by_bin[b][0] += p
        by_bin[b][1] += r["radiant_win"]
        by_bin[b][2] += 1
    return sum(abs(actual - predicted) for predicted, actual, _ in by_bin) / len(rows)


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    mean = lambda name: sum(r[name] for r in rows) / n
    return {
        "minute_rows": n,
        "matches": len({r["match_id"] for r in rows}),
        "mean_predicted_M0": mean("p0"),
        "mean_predicted_M1": mean("p1"),
        "observed_radiant_win_rate_rows": mean("radiant_win"),
        "M0_log_loss": mean("ll0"),
        "M1_log_loss": mean("ll1"),
        "delta_log_loss_M1_minus_M0": mean("ll1") - mean("ll0"),
        "M0_brier": mean("brier0"),
        "M1_brier": mean("brier1"),
        "delta_brier_M1_minus_M0": mean("brier1") - mean("brier0"),
        "M0_10bin_ECE": ece10(rows, "p0"),
        "M1_10bin_ECE": ece10(rows, "p1"),
    }


def audit(rows: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[row["match_id"]].append(row)
    influence = []
    overall_diff_sum = sum(r["ll1"] - r["ll0"] for r in rows)
    for mid, subset in groups.items():
        contrib = sum(r["ll1"]-r["ll0"] for r in subset)
        remaining = (overall_diff_sum - contrib)/(len(rows)-len(subset))
        influence.append({
            "match_id": mid, "forecast_minutes": len(subset),
            "match_mean_delta_ll": contrib/len(subset),
            "fraction_of_total_signed_gain": contrib/overall_diff_sum if overall_diff_sum else None,
            "all_other_matches_delta_ll": remaining,
            "absolute_difference_from_full_sample": abs(remaining-overall_diff_sum/len(rows)),
        })
    influence.sort(key=lambda item: item["absolute_difference_from_full_sample"], reverse=True)
    # Diagnose the effect of one influential whole match, never delete it from
    # the original TEST, refit, or select a model on this post-hoc slice.
    top_mid = influence[0]["match_id"]
    late30 = [r for r in rows if r["minute"] >= 30]
    remaining_late30 = [r for r in late30 if r["match_id"] != top_mid]
    late30_all = summarize(late30)
    late30_without = summarize(remaining_late30)
    late30_influence = {
        "scope": "POST_HOC_INFLUENCE_ONLY_NO_MODEL_SELECTION",
        "excluded_match_id": top_mid,
        "removed_late30_rows": len(late30) - len(remaining_late30),
        "all_late30_rows": late30_all["minute_rows"],
        "remaining_late30_rows": late30_without["minute_rows"],
        "all_delta_logloss_M1_minus_M0": late30_all["delta_log_loss_M1_minus_M0"],
        "without_match_delta_logloss_M1_minus_M0": late30_without["delta_log_loss_M1_minus_M0"],
        "all_delta_brier_M1_minus_M0": late30_all["delta_brier_M1_minus_M0"],
        "without_match_delta_brier_M1_minus_M0": late30_without["delta_brier_M1_minus_M0"],
    }
    return {
        "source_forecasts_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "science_boundary": (
            "Post-hoc descriptive analysis of the already inspected held-out "
            "forecasts. No training, model selection, or new significance claims."
        ),
        "overall": summarize(rows),
        "by_phase": {name: summarize([r for r in rows if phase(r["minute"]) == name])
                     for name in PHASES},
        "most_influential_5_matches": influence[:5],
        "late30_top_match_leave_one_out": late30_influence,
        "minute_zero": summarize([r for r in rows if r["minute"] == 0]),
        "caveats": [
            "Minute rows are correlated within a game and can share professional series/teams.",
            "10-bin ECE is an unstable descriptive statistic, not population calibration proof.",
            "Post-hoc slice and leave-one-out analysis cannot set deployment thresholds.",
            "This CSV does not contain full match/league/patch provenance or real source receive times.",
        ],
    }


def acceptance(result: dict) -> None:
    if result["source_forecasts_sha256"] != EXPECTED_SHA256:
        raise ValueError("Frozen employer held-out predictions have changed")
    o = result["overall"]
    if (o["minute_rows"], o["matches"]) != (3836, 106):
        raise ValueError("Incorrect frozen prediction dimensions")
    expected = {
        "M0_log_loss": .5164444241748873,
        "M1_log_loss": .504014697253528,
        "M0_brier": .1719121780368728,
        "M1_brier": .1683528340689237,
        "M0_10bin_ECE": .08948284614037452,
        "M1_10bin_ECE": .07501877151942367,
    }
    for key, value in expected.items():
        if not math.isclose(o[key], value, rel_tol=0, abs_tol=1e-10):
            raise ValueError(f"Parity failure in {key}: {o[key]} != {value}")
    top = result["most_influential_5_matches"][0]
    if top["match_id"] != 8744971178 or top["forecast_minutes"] != 55:
        raise ValueError("Original influential test match changed")
    if not math.isclose(top["fraction_of_total_signed_gain"], .5492191868375483,
                        rel_tol=0, abs_tol=1e-10):
        raise ValueError("Match-level influence fraction changed")
    if not math.isclose(top["all_other_matches_delta_ll"], -.005684587178237208,
                        rel_tol=0, abs_tol=1e-10):
        raise ValueError("Leave-one-match-out log loss changed")
    late = result["late30_top_match_leave_one_out"]
    if (late["excluded_match_id"] != 8744971178
            or late["removed_late30_rows"] != 25
            or (late["all_late30_rows"],late["remaining_late30_rows"]) != (719,694)
            or late["scope"] != "POST_HOC_INFLUENCE_ONLY_NO_MODEL_SELECTION"):
        raise ValueError("Frozen late30 leave-one-match-out grouping changed")
    for key,expected in (
        ("all_delta_logloss_M1_minus_M0",-.006782677223144962),
        ("without_match_delta_logloss_M1_minus_M0",.031390678),
        ("all_delta_brier_M1_minus_M0",.004548550147138952),
        ("without_match_delta_brier_M1_minus_M0",.00747672),
    ):
        if not math.isclose(late[key],expected,rel_tol=0,abs_tol=1e-7):
            raise ValueError("Frozen late30 leave-one-out statistic changed: "+key)
    if result["by_phase"]["30+"]["M1_brier"] <= result["by_phase"]["30+"]["M0_brier"]:
        raise ValueError("Unexpected late-game Brier ordering")
    if result["by_phase"]["30+"]["M1_10bin_ECE"] <= result["by_phase"]["30+"]["M0_10bin_ECE"]:
        raise ValueError("Unexpected late-game ECE ordering")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json",type=Path)
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    result=audit(load_rows())
    if args.check:
        acceptance(result)
    if args.json is not None:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "overall":result["overall"],
        "phases":{p:{k:v for k,v in item.items() if k in
                  ("matches","minute_rows","delta_log_loss_M1_minus_M0","delta_brier_M1_minus_M0","M0_10bin_ECE","M1_10bin_ECE")}
                  for p,item in result["by_phase"].items()},
        "most_influential_match":result["most_influential_5_matches"][0],
        "result":"PASS" if args.check else "DESCRIPTIVE",
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
