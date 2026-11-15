#!/usr/bin/env python3
"""Post-hoc, read-only value-of-freshness audit on frozen Vexil predictions.

No data/API fetch, training, model selection, or notebook mutation. The
originally opened TEST cannot become a second independent validation set.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
FORECAST_SHA = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
SERIES_SHA = "472db6781f6e6ad210120a07c4fb291583b75557841bbf2fa9448bafe6662383"
LAGS = (1, 2, 5)
MODELS = {"M0": "p_baseline", "M1": "p_model"}
METRICS = ("brier_value", "logloss_value", "innovation_energy", "calibration_term", "probability_drift")
DEFAULT_DRAW_COUNT = 10000
SEED = 20261115


def phase(minute):
    if minute < 10:
        return "00-09"
    if minute < 20:
        return "10-19"
    if minute < 30:
        return "20-29"
    return "30+"


def score(probability, outcome):
    assert 0.0 < probability < 1.0
    logloss = -(outcome * math.log(probability) + (1 - outcome) * math.log1p(-probability))
    brier = (probability - outcome) ** 2
    return logloss, brier


def load_data(predictions, series_path, expected_sha=FORECAST_SHA, fixed_cohort=True):
    source_bytes = predictions.read_bytes()
    checksum = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha is not None and checksum != expected_sha:
        raise ValueError(f"Frozen TEST prediction hash mismatch: {checksum}")
    metadata_bytes = series_path.read_bytes()
    metadata_sha = hashlib.sha256(metadata_bytes).hexdigest()
    if fixed_cohort and metadata_sha != SERIES_SHA:
        raise ValueError("Frozen series grouping hash mismatch")
    meta = json.loads(metadata_bytes)
    if not isinstance(meta, dict):
        raise ValueError("Series metadata must be a match-id object")
    games = defaultdict(dict)
    outcome_by_game = {}
    with io.StringIO(source_bytes.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["match_id", "minute", "p_model", "p_baseline", "radiant_win"]:
            raise ValueError("Prediction schema has changed")
        for item in reader:
            match_id = int(item["match_id"])
            minute = int(item["minute"])
            outcome = int(item["radiant_win"])
            if minute < 0 or outcome not in (0, 1):
                raise ValueError("Invalid minute or terminal outcome")
            if match_id not in outcome_by_game:
                outcome_by_game[match_id] = outcome
            elif outcome_by_game[match_id] != outcome:
                raise ValueError("Outcome changes within the same game")
            probabilities = {}
            for model, col in MODELS.items():
                p = float(item[col])
                if not math.isfinite(p) or not 0.0 < p < 1.0:
                    raise ValueError("Nonfinite, zero or one forecast")
                probabilities[model] = p
            if minute in games[match_id]:
                raise ValueError("Duplicate (game, minute) forecast")
            games[match_id][minute] = (outcome, probabilities)
    if set(str(k) for k in games) != set(meta):
        raise ValueError("Series metadata and forecast games differ")
    series_ids = {}
    for match_id in games:
        series_id = meta[str(match_id)]["series_id"]
        if isinstance(series_id, bool) or not isinstance(series_id, int) or series_id <= 0:
            raise ValueError("Invalid series ID")
        series_ids[match_id] = series_id
    n_rows = sum(len(m) for m in games.values())
    n_series = len(set(series_ids.values()))
    if fixed_cohort and (len(games), n_rows, n_series) != (106, 3836, 54):
        raise ValueError(f"Frozen TEST dimensions changed: {(len(games), n_rows, n_series)}")
    return games, series_ids, {"sha256": checksum, "series_metadata_sha256": metadata_sha, "games": len(games), "minute_rows": n_rows, "series": n_series}


def paired_observations(games, series_ids, lag):
    output = {"M0": [], "M1": []}
    for match_id in sorted(games):
        history = games[match_id]
        for minute in sorted(history):
            prev = history.get(minute - lag)
            if prev is None:
                continue
            outcome, current = history[minute]
            past_outcome, previous = prev
            if outcome != past_outcome:
                raise ValueError("Terminal outcomes inconsistent")
            for model in MODELS:
                old, now = previous[model], current[model]
                loss_old, brier_old = score(old, outcome)
                loss_now, brier_now = score(now, outcome)
                innovation = (now - old) ** 2
                calibration = 2 * (outcome - now) * (now - old)
                gain = brier_old - brier_now
                if not math.isclose(gain, innovation + calibration, rel_tol=0, abs_tol=1e-12):
                    raise AssertionError("Brier innovation identity failure")
                output[model].append({
                    "match_id": match_id, "series_id": series_ids[match_id],
                    "minute": minute, "phase": phase(minute),
                    "brier_value": gain,
                    "logloss_value": loss_old - loss_now,
                    "innovation_energy": innovation,
                    "calibration_term": calibration,
                    "probability_drift": now - old,
                })
    if len(output["M0"]) != len(output["M1"]):
        raise AssertionError("Unpaired models")
    return output


def arithmetic_summary(entries):
    n = len(entries)
    if not n:
        return {"n": 0}
    out = {"n": n}
    for metric in METRICS:
        out[metric] = sum(e[metric] for e in entries) / n
    by_game = defaultdict(list)
    for e in entries:
        by_game[e["match_id"]].append(e)
    out["games"] = len(by_game)
    out["equal_game_brier_value"] = sum(
        sum(x["brier_value"] for x in es) / len(es) for es in by_game.values()
    ) / len(by_game)
    return out


def series_bootstrap(entries, draws, seed, metrics=METRICS):
    if draws <= 0:
        raise ValueError("Positive bootstrap draw count required")
    groups = defaultdict(list)
    for entry in entries:
        groups[entry["series_id"]].append(entry)
    keys = sorted(groups)
    totals = []
    for key in keys:
        subset = groups[key]
        totals.append((len(subset), tuple(sum(e[m] for e in subset) for m in metrics)))
    n = len(keys)
    rng = random.Random(seed)
    samples = {m: [] for m in metrics}
    for _ in range(draws):
        count = 0
        summed = [0.0] * len(metrics)
        for _ in range(n):
            k = rng.randrange(n)
            c, sums = totals[k]
            count += c
            for i, item in enumerate(sums):
                summed[i] += item
        if count == 0:
            raise AssertionError("Empty bootstrap")
        for i, metric in enumerate(metrics):
            samples[metric].append(summed[i] / count)
    intervals = {}
    for metric, values in samples.items():
        values.sort()
        lo = values[int(0.025 * draws)]
        hi = values[min(draws - 1, int(0.975 * draws))]
        intervals[metric] = [lo, hi]
    return intervals



def influence_sensitivity(entries):
    """Leave-one-series-out robustness and match-level sign diagnostics."""
    if not entries:
        raise ValueError("No lagged rows")
    games = defaultdict(list)
    series = defaultdict(list)
    for e in entries:
        games[e["match_id"]].append(e["brier_value"])
        series[e["series_id"]].append(e["brier_value"])
    total_n = len(entries)
    total_sum = sum(e["brier_value"] for e in entries)
    loo = [
        (total_sum - sum(vals)) / (total_n - len(vals))
        for vals in series.values() if total_n != len(vals)
    ]
    if not loo:
        raise ValueError("At least two series required for influence check")
    return {
        "games_positive": sum(sum(vals) > 0 for vals in games.values()),
        "games_total": len(games),
        "series_positive": sum(sum(vals) > 0 for vals in series.values()),
        "series_total": len(series),
        "leave_one_series_out_brier_min": min(loo),
        "leave_one_series_out_brier_max": max(loo),
        "max_series_row_share": max(map(len, series.values())) / total_n,
    }

COMPARISON_METRICS = ("m1_fresh_gain_over_m0_brier", "m1_stale_disadvantage_to_m0_fresh_brier",
                      "m1_fresh_gain_over_m0_logloss", "m1_stale_disadvantage_to_m0_fresh_logloss")


def compare_models_on_same_rows(games, series_ids, lag, draws):
    """Descriptive operational contrast: both fresh vs challenger stale."""
    entries = []
    for match_id in sorted(games):
        history = games[match_id]
        for minute in sorted(history):
            previous = history.get(minute - lag)
            if previous is None:
                continue
            outcome, current = history[minute]
            m0_ll, m0_br = score(current["M0"], outcome)
            m1_ll, m1_br = score(current["M1"], outcome)
            stale_ll, stale_br = score(previous[1]["M1"], outcome)
            entries.append({
                "match_id": match_id, "series_id": series_ids[match_id],
                "m1_fresh_gain_over_m0_brier": m0_br - m1_br,
                "m1_stale_disadvantage_to_m0_fresh_brier": stale_br - m0_br,
                "m1_fresh_gain_over_m0_logloss": m0_ll - m1_ll,
                "m1_stale_disadvantage_to_m0_fresh_logloss": stale_ll - m0_ll,
            })
    out = {"n": len(entries), "games": len({e["match_id"] for e in entries})}
    for metric in COMPARISON_METRICS:
        out[metric] = sum(e[metric] for e in entries) / len(entries)
    out["series_bootstrap_95ci"] = series_bootstrap(
        entries, draws, SEED + lag, metrics=COMPARISON_METRICS
    )
    return out


def analyze(predictions, series_path, *, expected_sha=FORECAST_SHA, fixed_cohort=True, draws=DEFAULT_DRAW_COUNT):
    games, series_ids, cohort = load_data(
        predictions, series_path, expected_sha=expected_sha, fixed_cohort=fixed_cohort
    )
    result = {
        "evidence_class": "POST_HOC_OPENED_TEST_NOT_INDEPENDENT",
        "protocol": "docs/FRESHNESS_PROTOCOL.md",
        "seed": SEED,
        "bootstrap_draws": draws,
        "cohort": cohort,
        "lags": {},
        "immutable_model": True,
        "immutable_forecasts": True,
        "source_received_at_observed": False,
    }
    for lag in LAGS:
        pairs = paired_observations(games, series_ids, lag)
        summary = {}
        for model in MODELS:
            observations = pairs[model]
            s = arithmetic_summary(observations)
            s["series_bootstrap_95ci"] = series_bootstrap(observations, draws, SEED + lag)
            if lag == 1 and model == "M1":
                s["influence"] = influence_sensitivity(observations)
            s["by_phase"] = {
                name: arithmetic_summary([x for x in observations if x["phase"] == name])
                for name in ("00-09", "10-19", "20-29", "30+")
            }
            summary[model] = s
        if [e["match_id"] for e in pairs["M0"]] != [e["match_id"] for e in pairs["M1"]]:
            raise AssertionError("M0 and M1 were evaluated on different games")
        summary["same_row_model_comparison"] = compare_models_on_same_rows(games, series_ids, lag, draws)
        result["lags"][str(lag)] = summary
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write deterministic receipt")
    parser.add_argument("--check", action="store_true", help="verify committed receipt")
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAW_COUNT)
    parser.add_argument("--predictions", type=Path, default=ROOT / "artifacts/heldout_predictions.csv")
    parser.add_argument("--series", type=Path, default=ROOT / "docs/SERIES_GROUPS_TEST.json")
    parser.add_argument("--receipt", type=Path, default=ROOT / "docs/FRESHNESS_RECEIPT.json")
    options = parser.parse_args()
    if options.write and options.check:
        parser.error("Choose only one of --write or --check")
    result = analyze(options.predictions, options.series, draws=options.draws)
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if options.check:
        if options.receipt.read_text(encoding="utf-8") != payload:
            raise SystemExit("FAIL: committed freshness receipt does not match frozen inputs")
        print("PASS: post-hoc freshness receipt reproducible")
    elif options.write:
        options.receipt.write_text(payload, encoding="utf-8")
        print(f"WROTE {options.receipt}")
    for lag, models in result["lags"].items():
        for name in MODELS:
            values = models[name]
            print(f"lag={lag} model={name} n={values['n']} series={result['cohort']['series']} "
                  f"Brier(freshness)={values['brier_value']:+.6f} "
                  f"CI={values['series_bootstrap_95ci']['brier_value']} "
                  f"LL(freshness)={values['logloss_value']:+.6f} "
                  f"innovation={values['innovation_energy']:.6f} "
                  f"calibration={values['calibration_term']:+.6f}")


if __name__ == "__main__":
    main()
