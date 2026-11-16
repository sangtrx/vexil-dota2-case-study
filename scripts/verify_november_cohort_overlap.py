#!/usr/bin/env python3
"""Check non-independence of two November research cohorts from bundle only.

This checks identity overlap, NOT performance, code provenance, experiment
pre-registration, or model generalization. Never combine score intervals.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_100 = ROOT / "artifacts/forward_100_metadata.csv"
OLD_120 = ROOT / "docs/NOVEMBER_120_RESEARCH_MANIFEST.csv"
EXPECTED_100_SHA256 = "b99b22c3dc1b160da1441e0a9856aee97586517646a6e30dfaa7332cb926f0fa"
EXPECTED_120_SHA256 = "7f0d24c94fc899935b9d05a1c56444ae4a3aba1530ee2857cc7ccb8dbe70a825"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ids(path: Path) -> list[int]:
    with path.open(newline="", encoding="utf-8") as stream:
        lines = list(csv.DictReader(stream))
    if not lines or "match_id" not in lines[0]:
        raise ValueError("Missing match IDs from cohort audit")
    ids = [int(row["match_id"]) for row in lines]
    if len(ids) != len(set(ids)) or min(ids) <= 0:
        raise ValueError("Duplicate/invalid match ID in cohort audit")
    return ids


def verify() -> dict:
    if sha(MAIN_100) != EXPECTED_100_SHA256:
        raise ValueError("Immutable 100-game metadata SHA differs")
    if sha(OLD_120) != EXPECTED_120_SHA256:
        raise ValueError("Archived 120-game research manifest SHA differs")
    m100 = read_ids(MAIN_100)
    m120 = read_ids(OLD_120)
    if len(m100) != 100 or len(m120) != 120:
        raise ValueError("Expected cohort sizes 100/120")
    common = sorted(set(m100) & set(m120), reverse=True)
    only100 = sorted(set(m100) - set(m120), reverse=True)
    only120 = sorted(set(m120) - set(m100), reverse=True)
    if (len(common), len(only100), len(only120)) != (68, 32, 52):
        raise ValueError("Observed cohort overlap differs from frozen archive")
    return {
        "status": "PASS_COHORTS_NOT_INDEPENDENT",
        "new_100_games": len(m100),
        "archived_120_games": len(m120),
        "shared_games": len(common),
        "new_100_only_games": len(only100),
        "archived_120_only_games": len(only120),
        "fraction_new_100_reused": len(common) / len(m100),
        "fraction_archived_120_reused": len(common) / len(m120),
        "shared_match_ids": common,
        "original_100_manifest_sha256": sha(MAIN_100),
        "original_120_manifest_sha256": sha(OLD_120),
        "original_120_source": "sangtrx/dota2-live-win-probability Draft PR #3 research/frozen-november-cohort-20261115",
        "archived_120_source_git_commit": "476e7b9",
        "no_new_model_fit_or_scoring": True,
        "no_independent_replication_claim": True,
        "do_not_pool_100_and_120_scores": True,
        "audit_date_local": "2026-11-16",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
