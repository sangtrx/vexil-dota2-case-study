#!/usr/bin/env python3
"""Post-result audit correcting false strict-chronology assumptions.

Read-only cached original 103 validation match payloads. No model fits,
new test labels, OpenDota network or deployment claims.
Start time + game duration is only an APPROXIMATE wall-clock end;
pause/disconnect effects can merge otherwise disjoint components.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research/bible/results"
CACHE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions

MODEL_IDS=["M1_time_value"]+[f"P{i:02d}" for i in range(1,29)]
EPS=1e-15

def load_intervals():
    info=pd.read_csv(CACHE/"vexil_takehome_outputs/match_manifest.csv")
    val=info[info.partition=="validation"].copy()
    assert len(val)==103 and val.match_id.nunique()==103
    api=load_definitions()["OpenDota"](cache_dir=CACHE/"api-cache")
    rows=[]
    for m in val.itertuples():
        game=api.get("/matches/"+str(int(m.match_id)))
        start=int(m.start_time)
        duration=int(game["duration"])
        assert duration>0
        rows.append({
            "match_id":int(m.match_id),"series_id":int(m.series_id),
            "start_time":start,"approx_end":start+duration,
            "game_duration_s":duration,"patch":str(m.patch)
        })
    assert api.calls==0
    return pd.DataFrame(rows)

def interval_components(matches):
    x=matches.copy()
    x["key"]=np.where(x.series_id.astype(int)>0,"s"+x.series_id.astype(str),
                      "m"+x.match_id.astype(str))
    s=x.groupby("key").agg(
        first_start=("start_time","min"),
        last_approx_end=("approx_end","max"),
        games=("match_id","size")).reset_index()
    s=s.sort_values(["first_start","key"],kind="mergesort").reset_index(drop=True)
    components=[]
    ids=[]
    for rec in s.itertuples():
        if not components or rec.first_start>components[-1]["last_approx_end"]:
            components.append({"component":len(components)+1,
                               "first_start":int(rec.first_start),
                               "last_approx_end":int(rec.last_approx_end),
                               "series_groups":1,"games":int(rec.games)})
        else:
            components[-1]["last_approx_end"]=max(
                components[-1]["last_approx_end"],int(rec.last_approx_end))
            components[-1]["series_groups"]+=1
            components[-1]["games"]+=int(rec.games)
        ids.append(components[-1]["component"])
    s["component"]=ids
    assert sum(c["games"] for c in components)==103
    return x,s,pd.DataFrame(components)

def check_old_six_buckets(s):
    old=pd.read_csv(OUT/"time_blocks.csv")
    assert len(old)==53
    a=s.merge(old[["key","block"]],on="key",validate="one_to_one")
    rows=[]
    for k in range(1,6):
        prev=a[a.block==k]
        nxt=a[a.block==k+1]
        prev_end=int(prev.last_approx_end.max())
        next_start=int(nxt.first_start.min())
        rows.append({
            "boundary":k,
            "prev_latest_approx_end":prev_end,
            "next_earliest_start":next_start,
            "overlap_seconds_lower_bound":max(0,prev_end-next_start),
            "intervals_overlap":prev_end>next_start
        })
    return pd.DataFrame(rows)

def eval_components(matches,series,components):
    data=pd.read_csv(ROOT/"research/results/dev_validation_predictions_28.csv")
    assert data.match_id.nunique()==103
    x=data.merge(matches[["match_id","key"]],on="match_id",validate="many_to_one")
    x=x.merge(series[["key","component"]],on="key",validate="many_to_one")
    assert len(x)==3784
    y=x.radiant_win.to_numpy(int)
    p=np.clip(x[["p_"+i for i in MODEL_IDS]].to_numpy(float),EPS,1-EPS)
    losses=-(y[:,None]*np.log(p)+(1-y[:,None])*np.log1p(-p))
    rows=[]
    for comp in components.component:
        mask=x.component.to_numpy(int)==comp
        ll=losses[mask].mean(axis=0)
        order=np.argsort(ll,kind="stable")
        best=MODEL_IDS[int(order[0])]
        for i,m in enumerate(MODEL_IDS):
            rows.append({
                "component":int(comp),"model":m,
                "games":int(x.loc[mask,"match_id"].nunique()),
                "minute_rows":int(mask.sum()),
                "logloss":float(ll[i]),
                "delta_vs_m1":float(ll[i]-ll[0]),
                "best_model_in_component":best
            })
    return pd.DataFrame(rows)

def main():
    matches=load_intervals()
    matches,series,components=interval_components(matches)
    overlap=check_old_six_buckets(series)
    scores=eval_components(matches,series,components)
    # Exactly four approximate non-overlapping components from this data.
    assert len(components)==4 and components.games.tolist()==[62,2,3,36]
    assert int(overlap.intervals_overlap.sum())>=4
    for i in range(1,len(components)):
        prev=components.iloc[i-1];now=components.iloc[i]
        assert prev.last_approx_end<now.first_start
    assert len(scores)==29*4
    OUT.mkdir(exist_ok=True,parents=True)
    files={
        "validation_approx_intervals.csv":matches,
        "series_approx_intervals.csv":series,
        "chronology_components.csv":components,
        "old_six_bucket_overlap_audit.csv":overlap,
        "chronology_4component_scores.csv":scores
    }
    for name,frame in files.items():frame.to_csv(OUT/name,index=False)
    d=scores[scores.model.isin(["M1_time_value","P20"])]
    result={
        "audit_kind":"POSTHOC_DURATION_AWARE_CHRONOLOGY_CORRECTION",
        "result":"old six buckets cannot be called strictly chronological",
        "validation_matches":103,
        "series_groups":53,
        "old_six_bucket_overlapping_boundaries":int(overlap.intervals_overlap.sum()),
        "old_six_bucket_total_boundaries":5,
        "approx_disjoint_component_count":len(components),
        "approx_component_match_counts":components.games.astype(int).tolist(),
        "approx_component_series_counts":components.series_groups.astype(int).tolist(),
        "no_new_test_labels":True,
        "no_model_fit":True,
        "no_network_calls":True,
        "duration_caveat":"start_time+game.duration omits pauses and is NOT a network receive-time or exact physical end timestamp; true overlap can be worse",
        "note":"No valid 6-block strict chronological CSCV is supportable with these 103 games/53 series under duration-aware grouping."
    }
    (OUT/"chronology_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("CHRONOLOGY_CAVEAT_DISCOVERED",json.dumps(result,sort_keys=True))
    print("FOUR_DISJOINT_COMPONENT_P20_M1",d.sort_values(["component","model"]).round(6).to_string(index=False))
    print("SIX_BUCKET_OLD_OVERLAP",overlap.to_string(index=False))

if __name__=="__main__":main()
