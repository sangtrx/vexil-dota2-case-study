#!/usr/bin/env python3
"""All original forecast minutes: point-in-time feature metamorphic audit.

Requires the author's historical 500 gzipped /matches JSONs. No new API calls,
model fit, rescore, selection or TEST label use. The emitted fixed receipt is
author-controlled evidence: portable rerun requires original raw cache.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.posttest_temporal.collect_and_score import frozen_functions, sha

ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/"research/frozen_original_notebook_source.json"
SPLIT=ROOT/"research/frozen_original_split_manifest.csv"
RECEIPT=ROOT/"docs/FULL_500_PREFIX_AUDIT_RECEIPT.json"
SCIENCE_SHA="5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
SPLIT_SHA="8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"

def feature_only_prefix(m,t):
    gold=m.get("radiant_gold_adv")
    xp=m.get("radiant_xp_adv")
    objects=m.get("objectives")
    players=m.get("players")
    def events(log):
        if not isinstance(log,list):return log
        return [e for e in log if isinstance(e,dict) and
                type(e.get("time")) in (int,float) and
                math.isfinite(e["time"]) and e["time"]<=60*t]
    return {
        "radiant_gold_adv":gold[:t+1] if isinstance(gold,list) else gold,
        "radiant_xp_adv":xp[:t+1] if isinstance(xp,list) else xp,
        "objectives":events(objects),
        "players":[{"player_slot":p.get("player_slot"),
                    "kills_log":events(p.get("kills_log"))}
                   for p in players] if isinstance(players,list) else players,
        "radiant_win":not bool(m.get("radiant_win")),
        "duration":-999999,
    }

def compare_features(first,second,mid,t):
    if first.keys()!=second.keys():
        raise ValueError(f"Feature key drift {mid} minute {t}")
    for k in first:
        x,y=first[k],second[k]
        try:
            if math.isnan(x) and math.isnan(y):continue
        except TypeError:
            pass
        if x!=y:
            raise ValueError(f"Future feature leak {mid} minute {t}: {k} {x} != {y}")

def run(cache:Path,output:Path):
    import pandas as pd
    if sha(NB.read_bytes())!=SCIENCE_SHA or sha(SPLIT.read_bytes())!=SPLIT_SHA:
        raise ValueError("Frozen source notebook/partition drift")
    source=json.loads(NB.read_text())
    import ast
    code=ast.parse("".join(source["cells"][4]["source"]))
    frozen_ids=[ast.literal_eval(n.value) for n in code.body
                if isinstance(n,ast.Assign) and any(
                    isinstance(x,ast.Name) and x.id=="FROZEN_MATCH_IDS" for x in n.targets)]
    assert len(frozen_ids)==1 and len(frozen_ids[0])==500
    groups=pd.read_csv(SPLIT).set_index("match_id")
    if set(frozen_ids[0]) != set(groups.index):
        raise ValueError("Frozen 500 game IDs or split changed")
    methods=frozen_functions()
    checks=0
    by_split={"train":0,"validation":0,"test":0}
    early_nonfull_window=0
    per_match_sha={}
    for mid in frozen_ids[0]:
        key=sha(json.dumps(["/matches/"+str(mid),{}],sort_keys=True).encode())
        file=cache/(key+".json.gz")
        if not file.is_file():
            raise FileNotFoundError(str(mid))
        with gzip.open(file,"rt",encoding="utf8") as stream:
            m=json.load(stream)
        if m.get("match_id")!=mid:raise ValueError("Raw match ID drift")
        methods["validate_minute_alignment"](m)
        split=groups.loc[mid,"partition"]
        n=(int(m["duration"])-1)//60+1
        for t in range(n):
            original=methods["snapshot_features"](m,t)
            corrupted=feature_only_prefix(m,t)
            clipped=methods["snapshot_features"](corrupted,t)
            compare_features(original,clipped,mid,t)
            if t<5:early_nonfull_window+=1
            checks+=1
            by_split[split]+=1
        per_match_sha[str(mid)]=sha(json.dumps(m,sort_keys=True,
            separators=(",",":"),ensure_ascii=True).encode("utf8"))
    if (checks!=18292 or
        by_split!={"train":10675,"validation":3781,"test":3836}
        or early_nonfull_window!=2500):
        raise ValueError("Expected frozen cohort coverage not met")
    r={
        "status":"AUTHOR_CONTROLLED_ORIGINAL_500_FULL_MINUTE_PIT_AUDIT",
        "notebook_sha256":SCIENCE_SHA,
        "split_sha256":SPLIT_SHA,
        "match_count":500,
        "source_500_canonical_hash":sha(json.dumps(per_match_sha,sort_keys=True,separators=(",",":")).encode()),
        "original_minute_forecasts_checked":checks,
        "checks_by_partition":by_split,
        "eligible_minutes_with_shorter_than_five_minute_velocity_window":early_nonfull_window,
        "feature_names":sorted(original.keys()),
        "future_deleted_fields":["post_cutoff_team_gold","post_cutoff_team_xp",
            "post_cutoff_objectives","post_cutoff_kills","final_winner","final_duration"],
        "original_player_minute_clocks_validated_for_all_matches":True,
        "any_difference":False,
        "scored_original_test_labels":False,
        "trained_or_selected_any_model":False,
        "received_at_time_verified":False,
        "original_raw_json_in_reviewer_zip":False,
        "note":"Author-controlled post-result test of fixed source; no new blind or live event-time proof",
    }
    if output.exists():
        recorded=json.loads(output.read_text())
        if recorded!=r:
            raise ValueError("Existing immutable 500-game PIT audit receipt changed")
    else:
        output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    return r

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-cache",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,default=RECEIPT)
    args=ap.parse_args()
    r=run(args.raw_cache,args.receipt)
    print(json.dumps({k:r[k] for k in ("match_count","original_minute_forecasts_checked",
        "checks_by_partition","eligible_minutes_with_shorter_than_five_minute_velocity_window",
        "any_difference")},indent=2))
