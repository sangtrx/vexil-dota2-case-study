#!/usr/bin/env python3
"""Non-selecting, post-TEST dependence audit on the ORIGINAL 500-game cohort.

The default audit needs only bundled source-frozen metadata and immutable
3,836 TEST probabilities, not private author caches or HTTP requests.

The optional --build-metadata-from-cache step extracts *only* public match,
league and team identifiers from the author's 500 cached OpenDota match JSONs;
it does not train, fit, tune, or alter model outputs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/frozen_original_split_manifest.csv"
FORECASTS = ROOT / "artifacts/heldout_predictions.csv"
METADATA = ROOT / "research/frozen_cohort_group_metadata.csv"
RECEIPT = ROOT / "docs/TEAM_LEAGUE_DEPENDENCE_RECEIPT.json"
FORECAST_SHA = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
COLS = ("match_id", "start_time", "patch", "series_id", "partition",
        "league_id", "radiant_team_id", "dire_team_id")
SEED = 20261116
DRAWS = 30000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def optional_positive_id(value: object) -> str:
    if value in (None, "", 0, "0"):
        return ""
    if isinstance(value, bool):
        raise ValueError("Boolean where team/league ID was expected")
    n = int(value)
    if n <= 0 or str(n) != str(value):
        raise ValueError("Malformed positive integer identifier")
    return str(n)


def get_manifest() -> dict[int, dict[str, str]]:
    rows = read_csv(MANIFEST)
    ids = [int(r["match_id"]) for r in rows]
    assert len(rows) == 500 and len(set(ids)) == 500
    assert Counter(r["partition"] for r in rows) == {
        "train": 291, "validation": 103, "test": 106
    }
    return {int(r["match_id"]): r for r in rows}


def generate_metadata(cache: Path, output: Path = METADATA) -> None:
    """Author-side ONLY: one-pass extraction from cached OpenDota /matches."""
    manifest = get_manifest()
    result: dict[int, dict[str, str]] = {}
    for archive in sorted(cache.glob("*.json.gz")):
        with gzip.open(archive, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict) or payload.get("match_id") is None:
            continue
        match_id = int(payload["match_id"])
        if match_id not in manifest:
            continue
        if match_id in result:
            raise ValueError("Duplicate cached match ID")
        canonical = manifest[match_id]
        for field in ("start_time", "patch", "series_id"):
            actual = payload.get(field)
            # Original frozen manifest normalizes missing OpenDota series_id
            # to 0 ("unassigned series"), preserving its same match-level split.
            if field == "series_id" and actual is None:
                actual = 0
            if str(actual) != canonical[field]:
                raise ValueError(f"Source drift for {match_id}: {field}")
        league = optional_positive_id(payload.get("leagueid"))
        if not league:
            raise ValueError("Missing league identity in source cache")
        result[match_id] = {
            **{f: canonical[f] for f in COLS[:5]},
            "league_id": league,
            "radiant_team_id": optional_positive_id(payload.get("radiant_team_id")),
            "dire_team_id": optional_positive_id(payload.get("dire_team_id"))
        }
    if set(result) != set(manifest):
        raise ValueError("Author cache does not contain exactly the original 500 matches")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(result[mid] for mid in sorted(result))


def load_metadata() -> dict[int, dict[str, str]]:
    rows = read_csv(METADATA)
    manifest = get_manifest()
    if len(rows) != 500:
        raise ValueError("Expected 500 frozen group-metadata records")
    result = {}
    for row in rows:
        mid = int(row["match_id"])
        if mid in result or mid not in manifest:
            raise ValueError("Missing, extra or duplicate group-metadata match ID")
        if any(row[k] != manifest[mid][k] for k in COLS[:5]):
            raise ValueError("Group metadata disagrees with original manifest")
        if not optional_positive_id(row["league_id"]):
            raise ValueError("Unknown league prevents leave-league-out audit")
        for k in ("radiant_team_id", "dire_team_id"):
            optional_positive_id(row[k])
        if row["radiant_team_id"] and row["radiant_team_id"] == row["dire_team_id"]:
            raise ValueError("Self-play team ID is invalid")
        result[mid] = row
    if set(result) != set(manifest):
        raise ValueError("Incomplete group-metadata mapping")
    return result


def load_frozen_predictions(meta: dict[int, dict[str, str]]) -> list[dict]:
    if digest(FORECASTS) != FORECAST_SHA:
        raise ValueError("Frozen TEST forecast SHA changed; refuse to audit")
    data = read_csv(FORECASTS)
    if len(data) != 3836:
        raise ValueError("TEST minute-row count drifted")
    rows = []
    unique: set[tuple[int, int]] = set()
    per_match: dict[int, list[int]] = defaultdict(list)
    per_game_outcome: dict[int, int] = {}
    for record in data:
        mid = int(record["match_id"])
        if mid not in meta or meta[mid]["partition"] != "test":
            raise ValueError("Unexpected match in frozen TEST")
        t = int(record["minute"])
        if (mid, t) in unique:
            raise ValueError("Repeated forecast minute")
        unique.add((mid, t))
        per_match[mid].append(t)
        y = int(record["radiant_win"])
        if y not in (0, 1) or (mid in per_game_outcome and y != per_game_outcome[mid]):
            raise ValueError("Invalid or inconsistent TEST label")
        per_game_outcome[mid] = y
        baseline, proposed = float(record["p_baseline"]), float(record["p_model"])
        if not (0. < baseline < 1. and 0. < proposed < 1.):
            raise ValueError("Non-probability forecast")
        def logloss(prob: float) -> float:
            return -(y * math.log(prob) + (1-y) * math.log1p(-prob))
        rows.append({
            "match_id": mid, "minute": t,
            "series": meta[mid]["series_id"] if int(meta[mid]["series_id"]) > 0 else f"singleton_{mid}",
            "league": meta[mid]["league_id"],
            "delta_ll": logloss(proposed) - logloss(baseline),
            "delta_brier": (proposed-y)**2 - (baseline-y)**2
        })
    if len(per_match) != 106:
        raise ValueError("TEST games no longer 106")
    for mid, times in per_match.items():
        if sorted(times) != list(range(max(times)+1)):
            raise ValueError(f"Missing/extra within-game forecast minute: {mid}")
    return rows


def mean_delta(rows: list[dict], field: str) -> float:
    if not rows:
        raise ValueError("No rows remain")
    return sum(r[field] for r in rows) / len(rows)


def grouped_interval(rows: list[dict], field: str, group: str,
                     draws: int = DRAWS, seed: int = SEED) -> dict:
    """Paired percentile resampling of summed loss and row counts per group.

    The unit is a whole game or series, NOT individual minutes. Retrospective
    sensitivity only; dependency between leagues/teams can persist across series.
    """
    groups = defaultdict(lambda: [0., 0., 0.])
    for r in rows:
        key = str(r[group])
        cell = groups[key]
        cell[0] += 1.
        cell[1] += r["delta_ll"]
        cell[2] += r["delta_brier"]
    vector = np.array([groups[k] for k in sorted(groups)], dtype=float)
    n = len(vector)
    if n < 2:
        raise ValueError("Insufficient groups for bootstrap")
    rng = np.random.default_rng(seed)
    picked = rng.integers(0, n, size=(draws, n))
    sums = vector[picked].sum(axis=1)
    ratio = sums[:, 1 if field == "delta_ll" else 2] / sums[:, 0]
    lo, hi = np.quantile(ratio, (0.025, 0.975))
    return {
        "grouping": group,
        "clusters": n,
        "draws": draws,
        "seed": seed,
        "interval_95": [float(lo), float(hi)],
        "both_sides_of_zero": bool(lo <= 0 <= hi)
    }


def audit() -> dict:
    meta = load_metadata()
    rows = load_frozen_predictions(meta)
    by_split = {part: [m for m in meta.values() if m["partition"] == part]
                for part in ("train", "validation", "test")}
    def team_set(part: str) -> set[str]:
        return {m[f] for m in by_split[part]
                for f in ("radiant_team_id", "dire_team_id") if m[f]}
    train_teams, val_teams, test_teams = (team_set(k) for k in ("train", "validation", "test"))
    leagues = Counter(m["league_id"] for m in by_split["test"])
    series = {r["series"] for r in rows}
    match_ids = {r["match_id"] for r in rows}
    leave_out = []
    for league in sorted(leagues):
        remaining = [r for r in rows if r["league"] != league]
        within = [r for r in rows if r["league"] == league]
        leave_out.append({
            "excluded_league_id": league,
            "excluded_games": leagues[league],
            "excluded_rows": len(within),
            "within_league_delta_logloss": mean_delta(within, "delta_ll"),
            "within_league_delta_brier": mean_delta(within, "delta_brier"),
            "remaining_games": len({r["match_id"] for r in remaining}),
            "delta_logloss": mean_delta(remaining, "delta_ll"),
            "delta_brier": mean_delta(remaining, "delta_brier")
        })
    result = {
        "purpose": "POST_HOC_NONSELECTING_DEPENDENCE_DIAGNOSTIC",
        "not_new_blind_test": True,
        "does_not_fit_or_select_models": True,
        "do_not_use_to_promote_model": True,
        "raw_match_json_included": False,
        "metadata_source": "500 original author-cached /matches/{id} JSON records",
        "provenance_limitation": "Raw HTTP payloads omitted from reviewer ZIP; frozen match/league/team ID metadata is an author-derived extract.",
        "source": {
            "manifest_sha256": digest(MANIFEST),
            "test_predictions_sha256": digest(FORECASTS),
            "group_metadata_sha256": digest(METADATA)
        },
        "cohort": {
            "matches_total": 500,
            "split_matches": {k: len(v) for k, v in by_split.items()},
            "test_games": len(match_ids),
            "test_minute_rows": len(rows),
            "test_positive_series_or_singletons": len(series),
            "test_distinct_leagues": len(leagues),
            "test_distinct_known_team_ids": len(test_teams),
            "known_test_teams_also_in_train": len(test_teams & train_teams),
            "known_test_teams_also_in_validation": len(test_teams & val_teams),
            "known_test_team_id_overlap_train_fraction": len(test_teams & train_teams) / len(test_teams),
            "known_test_team_id_overlap_validation_fraction": len(test_teams & val_teams) / len(test_teams),
            "test_top_two_league_game_count": sum(n for _, n in leagues.most_common(2)),
            "test_top_two_league_game_fraction": sum(n for _, n in leagues.most_common(2)) / len(match_ids),
            "test_games_by_league_id": dict(sorted(leagues.items()))
        },
        "frozen_test_differences": {
            "M1_minus_M0_minute_weighted_logloss": mean_delta(rows, "delta_ll"),
            "M1_minus_M0_minute_weighted_brier": mean_delta(rows, "delta_brier")
        },
        "post_hoc_resampling": {
            "note": "Match/series resampling assumes independent clusters, potentially violated by overlapping teams/leagues; none is a fresh validation. Not a new model-selection gate.",
            "match_logloss": grouped_interval(rows, "delta_ll", "match_id"),
            "match_brier": grouped_interval(rows, "delta_brier", "match_id"),
            "series_logloss": grouped_interval(rows, "delta_ll", "series"),
            "series_brier": grouped_interval(rows, "delta_brier", "series")
        },
        "post_hoc_leave_one_league_out": leave_out,
        "limitations": [
            "Cross-series team/league dependence remains.",
            "Only nine selected, unbalanced leagues: no league-cluster confidence interval is treated as reliable.",
            "Overlapping teams are expected under chronological evaluation and are not proof of leakage.",
            "The M1 gold-by-time interaction still has no verified incremental skill over gold plus time additive control.",
            "Model/predictions were previously evaluated on this TEST; no fresh blind inference."
        ]
    }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--build-metadata-from-cache", type=Path)
    p.add_argument("--write-receipt", action="store_true")
    args = p.parse_args()
    if args.build_metadata_from_cache:
        generate_metadata(args.build_metadata_from_cache)
        print("Extracted fixed public group IDs from author raw cache:", METADATA)
    receipt = audit()
    text = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write_receipt:
        RECEIPT.write_text(text, encoding="utf-8")
        print("Saved non-selecting dependence receipt:", RECEIPT)
    print(json.dumps({
        "splits": receipt["cohort"]["split_matches"],
        "TEST_groups": [receipt["cohort"][k] for k in (
            "test_games", "test_positive_series_or_singletons",
            "test_distinct_leagues", "test_distinct_known_team_ids")],
        "team_overlap_train": receipt["cohort"]["known_test_teams_also_in_train"],
        "M1_minus_M0": receipt["frozen_test_differences"],
        "match_LL_95": receipt["post_hoc_resampling"]["match_logloss"]["interval_95"],
        "series_LL_95": receipt["post_hoc_resampling"]["series_logloss"]["interval_95"]
    }, indent=2))


if __name__ == "__main__":
    main()
