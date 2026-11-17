"""Offline reproduction of the October point-in-time prefix/label-poison receipt.

Never fit, score/select a model, modify raw matches, or use network access.
Every admissible minute is checked against the original frozen feature builder.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path

from research.posttest_temporal import collect_and_score as original

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research/october2026_accepted_raw"
COLLECTION = ROOT / "docs/OCTOBER_2026_COLLECTION_RECEIPT.json"
LISTING = ROOT / "docs/OCTOBER_2026_EXTERNAL_LISTING.json"
RECEIPT = ROOT / "docs/OCTOBER_2026_PIT_RECEIPT.json"


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def prefix_only(match: dict, minute: int) -> dict:
    """Delete only future information relevant to the original ten features."""
    cutoff = 60 * minute

    def earlier(events):
        if not isinstance(events, list):
            return events
        return [
            event for event in events if isinstance(event, dict)
            and type(event.get("time")) in (int, float)
            and math.isfinite(event["time"]) and event["time"] <= cutoff
        ]

    return {
        "radiant_gold_adv": match["radiant_gold_adv"][:minute + 1],
        "radiant_xp_adv": match["radiant_xp_adv"][:minute + 1],
        "objectives": earlier(match.get("objectives")),
        "players": [
            {"player_slot": player.get("player_slot"),
             "kills_log": earlier(player.get("kills_log"))}
            for player in match.get("players", [])
        ],
        "radiant_win": not bool(match.get("radiant_win")),
        "duration": -999999,
    }


def identical_features(original_features: dict, projected_features: dict) -> bool:
    if original_features.keys() != projected_features.keys():
        return False
    for field in original_features:
        left, right = original_features[field], projected_features[field]
        try:
            a, b = float(left), float(right)
        except (ValueError, TypeError):
            if left != right:
                return False
        else:
            if not ((math.isnan(a) and math.isnan(b)) or a == b):
                return False
    return True


def audit() -> dict:
    collection = json.loads(COLLECTION.read_bytes())
    listing = LISTING.read_bytes()
    if not collection.get("complete") or collection.get("accepted_count") != 180:
        raise ValueError("October source collection is incomplete")
    if collection["frozen_listing_sha256"] != _sha(listing):
        raise ValueError("October listing no longer matches frozen collection")
    expected_ids = [
        row["match_id"]
        for row in json.loads(listing)["candidate_ids_start_times_and_series"]
    ]
    if [row["match_id"] for row in collection["accepted"]] != expected_ids:
        raise ValueError("October accepted match selection drifted")
    functions = original.frozen_functions()
    snapshot = functions["snapshot_features"]
    field_counts: dict[str, int] = {}
    forecast_count = 0
    for row in collection["accepted"]:
        path = RAW / f'{row["match_id"]}.json.gz'
        blob = path.read_bytes()
        if _sha(blob) != row["raw_gzip_sha256"]:
            raise ValueError(f'Raw payload archive changed: {row["match_id"]}')
        raw = gzip.decompress(blob)
        if _sha(raw) != row["raw_json_sha256"]:
            raise ValueError(f'Raw JSON content changed: {row["match_id"]}')
        game = json.loads(raw)
        if int(game["match_id"]) != row["match_id"]:
            raise ValueError("Payload match ID drifted")
        for minute in range((int(game["duration"]) - 1) // 60 + 1):
            actual = snapshot(game, minute)
            reduced = snapshot(prefix_only(game, minute), minute)
            if not identical_features(actual, reduced):
                raise AssertionError(
                    f'Post-time feature/label leakage: match {row["match_id"]} minute {minute}'
                )
            for key in actual:
                field_counts[key] = field_counts.get(key, 0) + 1
            forecast_count += 1
    if len(collection["accepted"]) != 180 or forecast_count != 7346:
        raise AssertionError("October forecast grid changed")
    return {
        "duration_deliberately_poisoned": True,
        "feature_comparisons": sum(field_counts.values()),
        "fields_checked": sorted(field_counts),
        "future_economy_objectives_kills_clipped": True,
        "matches": len(collection["accepted"]),
        "not_a_live_received_at_proof": True,
        "prefix_checked_forecasts": forecast_count,
        "result_labels_deliberately_poisoned": True,
        "source_october_listing_sha256": _sha(listing),
        "source_original_feature_code_sha256": original.CODE_SHA,
        "status": "PASS_ALL_OCTOBER_FORECASTS_PREFIX_TRUNCATION_AND_LABEL_POISON",
    }


if __name__ == "__main__":
    reproduced = audit()
    saved = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if reproduced != saved:
        raise SystemExit("PIT receipt no longer matches 180 frozen matches")
    print("OCTOBER_PIT_REPLAY_PASS", reproduced["prefix_checked_forecasts"],
          "feature_pairs", reproduced["feature_comparisons"])
