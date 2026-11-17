#!/usr/bin/env python3
"""Read-only structural OpenDota time-array audit against the 291-TRAIN manifest.

Duration/array length compatibility is NOT proof of exact sample timestamps
or real-world packet arrival. This script does not use or expose winner labels.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from rich_feature_engineering import PROVENANCE, SOURCE, TRAIN_SHA, source_key

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/QUANT_PATH_RAW_TIME_AUDIT.json"
DOC=ROOT/"research/QUANT_PATH_RAW_TIME_AUDIT.md"
NAMES=("gold_t","xp_t","lh_t","dn_t")
ADV=("radiant_gold_adv","radiant_xp_adv")


def inspect_array_lengths(raw:dict)->dict:
    """Positive control: short and extra arrays must both be reported."""
    d=raw.get("duration")
    if isinstance(d,bool) or not isinstance(d,(int,float)) or d<0 or int(d)!=d:
        raise ValueError("Invalid game duration")
    expected=int(d)//60+1
    players=raw.get("players")
    if not isinstance(players,list) or len(players)!=10:
        raise ValueError("Expected exactly 10 player data streams")
    arr={}
    for key in ADV:
        v=raw.get(key)
        if not isinstance(v,list):
            raise ValueError("Missing team array "+key)
        arr[key]=len(v)-expected
    for key in NAMES:
        for i,p in enumerate(players):
            v=p.get(key)
            if not isinstance(v,list):
                raise ValueError("Missing player array "+key)
            arr[f"p{i}_{key}"]=len(v)-expected
    return arr


def run(cache_dir:Path)->dict:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=TRAIN_SHA:
        raise AssertionError("Original 291-TRAIN source hash changed")
    original=pd.read_csv(SOURCE,usecols=["match_id","duration","partition"])
    if set(original.partition)!={"train"}:
        raise AssertionError("Non-TRAIN source")
    games=original[["match_id","duration"]].drop_duplicates().sort_values("match_id")
    if len(games)!=291:
        raise AssertionError("Expected 291 original TRAIN matches")
    prior=json.loads(PROVENANCE.read_text())
    deltas=collections.Counter()
    first=collections.Counter()
    payload_hashes=[]
    mismatches=0
    for mid,dur in games.itertuples(index=False):
        path=cache_dir/(source_key(int(mid))+".json.gz")
        blob=path.read_bytes()
        raw=json.loads(gzip.decompress(blob))
        if int(raw.get("match_id",-1))!=int(mid) or int(raw.get("duration",-1))!=int(dur):
            mismatches+=1
        payload_hashes.append([int(mid),hashlib.sha256(blob).hexdigest()])
        arrays=inspect_array_lengths(raw)
        for key,diff in arrays.items():
            group=key if key in ADV else "player_"+key.split("_",1)[1]
            deltas[f"{group}_delta_{diff}"]+=1
        for key in ADV:
            first[f"{key}_nonzero_first"]+=int(len(raw[key])>0 and raw[key][0]!=0)
            first[f"{key}_over_1000_first"]+=int(len(raw[key])>0 and abs(raw[key][0])>1000)
        for p in raw["players"]:
            for key in ("xp_t","lh_t"):
                first[f"player_{key}_nonzero_first"]+=int(len(p[key])>0 and p[key][0]!=0)
    h=hashlib.sha256(json.dumps(payload_hashes,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    if h!=prior["source_payload_bytes_sha256"] or mismatches:
        raise AssertionError("Original raw-cache provenance mismatch")
    short=sum(count for k,count in deltas.items() if "_delta_-" in k)
    extra=sum(count for k,count in deltas.items() if "_delta_" in k and
              not k.endswith("_delta_0") and "_delta_-" not in k)
    return {
        "scope":"original 291 TRAIN matches; NO label or original VAL/TEST read",
        "raw_source_manifest_sha256":h,
        "train_csv_sha256":TRAIN_SHA,
        "matches_checked":291,"player_streams_checked":2910,
        "per_match_team_arrays":2,"per_match_player_arrays":40,
        "arrays_shorter_than_duration_minute_grid":short,
        "arrays_longer_than_duration_minute_grid":extra,
        "array_length_deltas":dict(sorted(deltas.items())),
        "first_values_diagnostics":dict(sorted(first.items())),
        "duration_id_mismatches":mismatches,
        "all_samples_have_individual_verified_timestamps":False,
        "arrival_time_verified":False,
        "scientific_judgment":"INDETERMINATE: array lengths compatible with duration; no proof that array index t denotes exact observation/arrival time t",
        "external_context":"2026 Zenodo v3 DOI 10.5281/zenodo.23166182 removed 1849 other matches because time-axis indexing was not always reliable",
    }


def report(r:dict)->str:
    arr=r["array_length_deltas"]
    return "\n".join([
        "# OpenDota array time-axis audit: structural compatibility only",
        "",
        "Read the exact existing 291 TRAIN raw payloads, requiring the previously "
        "committed aggregate payload SHA256. No outcomes, VAL, TEST or employer "
        "artifacts enter the audit.",
        "",
        f"- Raw games: {r['matches_checked']}; player streams: {r['player_streams_checked']}.",
        f"- Arrays shorter than duration-derived minute grid: "
        f"{r['arrays_shorter_than_duration_minute_grid']}.",
        f"- Arrays longer than duration-derived minute grid: "
        f"{r['arrays_longer_than_duration_minute_grid']} "
        "(two matches each with two team and 40 per-player extra terminal slots).",
        f"- Mismatched match IDs or durations: {r['duration_id_mismatches']}.",
        f"- Team arrays exactly matching duration grid: "
        f"gold={arr.get('radiant_gold_adv_delta_0',0)}/291; "
        f"XP={arr.get('radiant_xp_adv_delta_0',0)}/291.",
        "",
        "**Scientific status: INDETERMINATE for actual sample timestamps and feed arrival.** "
        "Duration matching cannot prove actual array index-to-minute alignment. "
        "Some arrays contain additional trailing sample slots and source does "
        "not supply trustworthy per-sample arrival timestamps. This audit "
        "neither detects an OpenDota leak nor certifies the live PIT model.",
        "",
        "Motivation: a separate 2026 professional Dota dataset, Zenodo DOI "
        "10.5281/zenodo.23166182, removed 1,849 different matches because "
        "per-minute arrays could be shifted or sampled irregularly. "
        "Do not copy that count to this sample.",
        "",
        "Read-only QA; no original TEST, notebook, ZIP or report change.",
        ""
    ])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache-dir",required=True,type=Path)
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    result=run(args.cache_dir)
    print(report(result))
    if args.write:
        OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        DOC.write_text(report(result))
