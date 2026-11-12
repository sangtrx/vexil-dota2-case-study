#!/usr/bin/env python3
"""Read-only 900-match clock and gold-sum integrity audit.

Audit does not touch outcome labels or fit models. It is not a live-feed
latency audit and cannot establish receipt-time information availability.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tests.test_notebook_contracts import load_definitions

BASE = Path("/home/ai-agent/.cache/vexil-real-data-20261113")
DATASETS = [
    ("original500", BASE / "manifest_metadata.json", 500),
    ("first_forward200", Path("/home/ai-agent/.cache/vexil-edge-v2-20261113/forward_holdout_manifest.json"), 200),
    ("second_forward200", Path("/home/ai-agent/.cache/vexil-edge-v3-20261113/gate_confirmation_manifest.json"), 200),
]
DEST = Path("/home/ai-agent/.cache/vexil-option-novelty-20261113/pit_axis_audit_receipt.json")

def main():
    ns = load_definitions()
    api = ns["OpenDota"](cache_dir=BASE/"api-cache")
    results = {}
    for name, manifest_path, expected in DATASETS:
        manifest_text=manifest_path.read_bytes()
        rows=json.loads(manifest_text)
        assert len(rows) == expected
        assert len({int(r["match_id"]) for r in rows}) == expected
        checked_players = checked_minutes = 0
        for row in rows:
            game = api.get("/matches/"+str(int(row["match_id"])))
            players = game.get("players")
            adv = game.get("radiant_gold_adv")
            assert isinstance(players,list) and len(players)==10
            assert isinstance(adv,list) and adv
            checked_players += len(players)
            for p in players:
                times=p.get("times"); gold=p.get("gold_t")
                xp=p.get("xp_t"); lh=p.get("lh_t")
                assert all(isinstance(x,list) for x in (times,gold,xp,lh))
                assert len(times)==len(gold)==len(xp)==len(lh)==len(adv)
                assert all(times[t]==60*t for t in range(len(times)))
            assert len({int(p["player_slot"]) for p in players})==10
            assert sum(p["player_slot"]<128 for p in players)==5
            assert sum(p["player_slot"]>=128 for p in players)==5
            for t in range(len(adv)):
                r=sum(p["gold_t"][t] for p in players if p["player_slot"]<128)
                d=sum(p["gold_t"][t] for p in players if p["player_slot"]>=128)
                assert r-d == adv[t],("future/clock/data drift",row["match_id"],t)
                checked_minutes+=1
        results[name]={
            "games":expected,"players_checked":checked_players,
            "minute_gold_sum_and_actual_clock_checks":checked_minutes,
            "all_time_axes_start_at_zero_and_step60":True,
            "all_gold_xp_lh_lengths_match":True,
            "all_gold_advantages_equal_player_gold_sums":True,
            "manifest_sha256":hashlib.sha256(manifest_text).hexdigest(),
        }
        print("FULL_TIME_AXIS_AUDIT_PASS",name,json.dumps(results[name],sort_keys=True))
    assert api.calls==0,"Only frozen cached match payloads permitted"
    assert sum(r["minute_gold_sum_and_actual_clock_checks"] for r in results.values())==32106
    DEST.parent.mkdir(parents=True,exist_ok=True)
    receipt={
        "scope":"historically parsed OpenDota match-clock integrity, not wall-clock receipt latency",
        "datasets":results,
        "network_requests":api.calls,
        "total_matches":900,
        "total_minute_checks":sum(r["minute_gold_sum_and_actual_clock_checks"] for r in results.values()),
        "point_in_time_caveat":"retrospective parse not evidence of physical streaming availability",
    }
    DEST.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("FULL_900_MATCH_AUDIT_RECEIPT_WRITTEN",DEST)

if __name__=="__main__":
    main()
