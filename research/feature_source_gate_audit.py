#!/usr/bin/env python3
"""Feasibility audit for timestamp-poor hero ability and pro-match chat sources."""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path

from rich_feature_engineering import PROVENANCE, source_key
from train_time_effect_ci import require_data

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/FEATURE_SOURCE_GATE_RECEIPT.json"
READOUT=ROOT/"research/FEATURE_SOURCE_GATE_READOUT.md"
DEFAULT_CACHE=Path("/home/ai-agent/.cache/vexil-real-data-20261113/api-cache")


def audit(cache_dir:Path)->dict:
    df=require_data()
    ids=sorted(df.match_id.unique())
    prior=json.loads(PROVENANCE.read_text())
    p_sha=[]
    count=collections.Counter()
    chattypes=collections.Counter()
    for mid in ids:
        blob=(cache_dir/(source_key(int(mid))+".json.gz")).read_bytes()
        p_sha.append([int(mid),hashlib.sha256(blob).hexdigest()])
        raw=json.loads(gzip.decompress(blob))
        if int(raw["match_id"])!=int(mid):
            raise AssertionError("TRAIN source ID drift")
        duration=float(raw["duration"])
        chat=raw.get("chat") or []
        count["chat_events"]+=len(chat)
        count["games_with_chat"]+=bool(chat)
        for entry in chat:
            if not isinstance(entry,dict):continue
            chattypes[str(entry.get("type"))]+=1
            tm=entry.get("time")
            if isinstance(tm,(int,float)):
                count["chat_events_before_game"]+=tm<0
                count["chat_events_after_duration"]+=tm>duration
        for player in raw.get("players") or []:
            upgrade=player.get("ability_upgrades_arr") or []
            count["upgrade_entries"]+=len(upgrade)
            count["upgrade_entries_with_timestamps"]+=sum(
                isinstance(x,dict) and ("time" in x or "timestamp" in x)
                for x in upgrade)
    payload=hashlib.sha256(json.dumps(p_sha,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if payload!=prior["source_payload_bytes_sha256"] or len(ids)!=291:
        raise AssertionError("Raw 291-source cache and prior SHA drift")
    return {
       "scope":"existing 291 original TRAIN match payloads only; no chat content retained",
       "source_payload_sha256":payload,
       "games":len(ids),"chat_type_counts":dict(sorted(chattypes.items())),
       "chat_event_counts":dict(sorted(count.items())),
       "hero_level_up_exact_asof_timestamps_available":False,
       "chat_actual_received_at_verified":False,
       "chat_as_of_new_candidate_evaluation":"BLOCKED: no independent real-time arrival; some pregame/postgame events; risk of near-terminal outcome announcements",
       "hero_upgrade_candidate_evaluation":"BLOCKED: upgrade array entries are ability identifiers, not timestamped level-up events",
       "item_milestone_candidate":"historical purchase_log event time proxy tested separately in precommitted I family, but live arrival unverified",
       "no_original_val_test_read":True,
    }


def report(r:dict)->str:
    counts=r["chat_event_counts"]
    return "\n".join([
      "# Other proposed feature inputs: eligibility, not leaderboard scores",
      "",
      "Examined exact SHA-matched 291 TRAIN cached OpenDota payloads. "
      "Never recorded message texts, players' names or IDs in this receipt.",
      "",
      f"- Chat events {counts['chat_events']}, in {counts['games_with_chat']} games. "
      f"Types: {r['chat_type_counts']}.",
      f"- Pregame chat events: {counts['chat_events_before_game']}; "
      f"post-duration chat events: {counts['chat_events_after_duration']}.",
      f"- Hero ability-upgrade entries: {counts['upgrade_entries']}; "
      f"entries bearing exact timestamps: {counts['upgrade_entries_with_timestamps']}.",
      "",
      "**Decision:** Do not treat terminal hero upgrade arrays as a time-known "
      "level-up feature. Live chat availability also cannot be inferred "
      "from post-replay parse timestamps, and postgame/near-terminal "
      "announcements can give misleading outcome signals. These two "
      "source families are BLOCKED for honest live claims. "
      "They are **not** reported as experimentally underperforming models.",
      "",
      "The separately scored BKB/Blink candidate is purchase-log first-event "
      "proxy only; it does not solve hero upgrade or live receipt provenance.",
      ""
    ])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache-dir",type=Path,default=DEFAULT_CACHE)
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    result=audit(args.cache_dir)
    print(report(result))
    if args.write:
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        READOUT.write_text(report(result))
