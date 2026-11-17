#!/usr/bin/env python3
"""Strong but *internal* Dota minute-array consistency audit.

All fields may be produced by the same postmatch parser. Passing this audit
does not establish true observation or arrival time; avoid claiming live PIT.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from rich_feature_engineering import PROVENANCE, side_from_slot, source_key
from train_time_effect_ci import require_data

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/CROSS_ARRAY_TIME_ALIGNMENT_RECEIPT.json"
READOUT=ROOT/"research/CROSS_ARRAY_TIME_ALIGNMENT_READOUT.md"
CACHE=Path("/home/ai-agent/.cache/vexil-real-data-20261113/api-cache")


def check_single_game(raw:dict)->dict:
    duration=raw.get("duration")
    if not isinstance(duration,(float,int)) or duration<=0:
        raise ValueError("Missing game duration")
    g=raw.get("radiant_gold_adv")
    x=raw.get("radiant_xp_adv")
    players=raw.get("players")
    if not isinstance(g,list) or not isinstance(x,list) or not isinstance(players,list) or len(players)!=10:
        raise ValueError("Missing original game telemetry")
    n=len(g)
    if n==0 or len(x)!=n:
        raise AssertionError("Gold/XP team arrays have different lengths")
    pg={};px={}
    for p in players:
        side=side_from_slot(p.get("player_slot"))
        if not side:
            raise AssertionError("Unassigned player side")
        raw_times=p.get("times")
        if not isinstance(raw_times,list):
            raise AssertionError("Player has no sampling timeline")
        expected=np.arange(n,dtype=np.int64)*60
        times=np.asarray(raw_times,dtype=np.float64)
        if times.ndim!=1 or len(times)!=n or not np.array_equal(times,expected):
            raise AssertionError("Wrong sample timestamp grid or missing offset")
        gold=np.asarray(p.get("gold_t"),dtype=float)
        xp=np.asarray(p.get("xp_t"),dtype=float)
        if (gold.shape!=(n,) or xp.shape!=(n,)
            or not np.isfinite(gold).all() or not np.isfinite(xp).all()):
            raise AssertionError("Player gold/XP arrays missing or invalid")
        pg.setdefault(side,[]).append(gold)
        px.setdefault(side,[]).append(xp)
    if any(len(pg.get(side,[]))!=5 for side in (1,-1)):
        raise AssertionError("Not five players on each side")
    reconstructed_g=np.sum(pg[1],axis=0)-np.sum(pg[-1],axis=0)
    reconstructed_x=np.sum(px[1],axis=0)-np.sum(px[-1],axis=0)
    if not np.array_equal(np.asarray(g,float),reconstructed_g):
        raise AssertionError("Original team gold advantage inconsistent with player array index")
    if not np.array_equal(np.asarray(x,float),reconstructed_x):
        raise AssertionError("Original team XP advantage inconsistent with player array index")
    overshoot=int(np.sum(expected>=float(duration)))
    return {"players":10,"raw_snapshots":n,
            "per_player_time_vectors":10,
            "verified_team_gold_array_slots":n,
            "verified_team_xp_array_slots":n,
            "terminal_or_postterminal_array_slots":overshoot}


def evaluate(cache:Path=CACHE)->dict:
    frame=require_data()
    ids=sorted(frame.match_id.unique())
    prior=json.loads(PROVENANCE.read_text())
    counts=collections.Counter()
    manifest=[]
    for mid in ids:
        data=(cache/(source_key(int(mid))+".json.gz")).read_bytes()
        manifest.append([int(mid),hashlib.sha256(data).hexdigest()])
        raw=json.loads(gzip.decompress(data))
        if int(raw.get("match_id",-1))!=int(mid):
            raise AssertionError("Source original match ID mismatch")
        checked=check_single_game(raw)
        counts.update(checked)
    raw_sha=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if raw_sha!=prior["source_payload_bytes_sha256"] or len(ids)!=291:
        raise AssertionError("Original 291 raw game provenance failed")
    if counts["raw_snapshots"]<len(frame):
        raise AssertionError("Raw sample count shorter than original TRAIN")
    return {
        "scope":"291 original TRAIN payloads only; no outcomes, VAL, TEST or new downloads",
        "input_aggregate_sha256":raw_sha,
        "match_count":291,
        **dict(counts),
        "all_player_times_are_exact_grid_0_60_120":True,
        "all_teams_exact_sum_of_player_gold_and_xp_at_same_index":True,
        "independent_timestamp_witness_available":False,
        "actual_ingest_received_at_known":False,
        "scientific_interpretation":"PASS internal parser/array consistency, NOT PROVEN actual independent event-clock/packet arrival timing",
    }


def report(r:dict)->str:
    return "\n".join([
        "# Cross-array time-axis check on the original 291 TRAIN matches",
        "",
        f"- Player minute vectors: **{r['per_player_time_vectors']}** checked, "
        "all exactly [0,60,120,...] by index.",
        f"- Historical game snapshots: **{r['raw_snapshots']}**.",
        f"- Team gold and XP advantages equal their respective five-player "
        f"Radiant-minus-Dire sums at all {r['verified_team_gold_array_slots']} "
        "raw sampled indices, with zero mismatches.",
        f"- Raw slots at or beyond stated terminal duration: "
        f"{r['terminal_or_postterminal_array_slots']}; original TRAIN 10,675 "
        "decision rows were already filtered before termination.",
        "",
        "**Scope limit:** Same OpenDota replay parser can generate both "
        "player times and gold arrays. Thus exact agreement is a strong "
        "internal invariance and catches a shifted one-array index or "
        "inconsistent team sum, but is not an independent proof that each "
        "raw time was actually observed and delivered at exactly that minute. "
        "Received-at is still unavailable. Do not extrapolate to "
        "a different Zenodo cohort's excluded matches.",
        "",
        "No model fitting, TEST/VAL outcomes, applicant submission or raw mutation.",
        ""
    ])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache-dir",type=Path,default=CACHE)
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    result=evaluate(args.cache_dir)
    print(report(result))
    if args.write:
        OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        READOUT.write_text(report(result))
