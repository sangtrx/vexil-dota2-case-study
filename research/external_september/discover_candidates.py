#!/usr/bin/env python3
"""Outcome-blind September candidate selection from /proMatches metadata only."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).with_name("selected_metadata.json")
START=int(dt.datetime(2026,9,1,tzinfo=dt.timezone.utc).timestamp())
STOP=int(dt.datetime(2026,10,1,tzinfo=dt.timezone.utc).timestamp())
TARGET=200
MAX_PAGES=70
FIELDS=("match_id","start_time","duration","series_id","leagueid")

def canonical_digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def clean_meta(row):
    # NEVER preserve radiant_win, scores or completed-game results in a selection manifest.
    mid=row.get("match_id")
    start=row.get("start_time")
    duration=row.get("duration")
    if type(mid) is not int or type(start) is not int or type(duration) is not int: return None
    if not (START<=start<STOP and duration>=600): return None
    return {"match_id":mid,"start_time":start,"duration":duration,
            "series_id":int(row.get("series_id") or 0),
            "leagueid":int(row.get("leagueid") or 0)}

def select_metadata(all_rows, orig_ids):
    grouped={}
    for row in all_rows:
        m=clean_meta(row)
        if m is not None and m["match_id"] not in orig_ids:
            # deterministic handling of pagination repeats
            grouped[m["match_id"]]=m
    return sorted(grouped.values(),key=lambda row:(-row["start_time"],-row["match_id"]))[:TARGET]

def discover():
    seen=set(); all_rows=[]; older_streak=0
    s=requests.Session()
    s.headers["User-Agent"]="vexil-external-sept-research/1.0"
    pages=[]
    cursor=None
    for page in range(MAX_PAGES):
        params={} if cursor is None else {"less_than_match_id":cursor}
        for retry in range(6):
            try:
                r=s.get("https://api.opendota.com/api/proMatches",params=params,timeout=25)
                if r.status_code in (429,500,502,503,504):
                    time.sleep(min(3*(retry+1),20));continue
                r.raise_for_status();data=r.json()
                if not isinstance(data,list):raise ValueError("Non-list /proMatches")
                break
            except (requests.RequestException,ValueError):
                if retry==5:raise
                time.sleep(2*(retry+1))
        if not data:raise RuntimeError("Pagination exhausted before September lower boundary")
        ids=[x["match_id"] for x in data if isinstance(x,dict) and type(x.get("match_id")) is int]
        if len(ids)<len(data):raise RuntimeError("Invalid match ID on /proMatches page")
        if len(ids)!=len(set(ids)):raise RuntimeError("Duplicate IDs within page")
        new_cursor=min(ids)
        if cursor is not None and new_cursor>=cursor:raise RuntimeError("Nonprogressing pagination cursor")
        if any(x in seen for x in ids):
            raise RuntimeError("Unexpected overlapping proMatches pages: abort before selection")
        seen.update(ids)
        # Outcome fields are dropped immediately and never written/logged.
        all_rows.extend([{k:row.get(k) for k in FIELDS} for row in data])
        starts=[int(row["start_time"]) for row in data if type(row.get("start_time")) is int]
        if not starts: raise RuntimeError("Invalid timestamps")
        if max(starts)<START:older_streak+=1
        else:older_streak=0
        pages.append({"cursor_before":cursor,"cursor_after":new_cursor,
                      "rows":len(data),"min_start":min(starts),"max_start":max(starts)})
        cursor=new_cursor
        # Wait for two full out-of-window pages to guard against minor paging disorder.
        if older_streak>=2:break
        time.sleep(1.6)
    else:
        raise RuntimeError("MAX_PAGES exhausted before September lower boundary")

    original=set(pd.read_csv(ROOT/"research/frozen_original_split_manifest.csv").match_id.astype(int))
    candidates=select_metadata(all_rows,orig_ids=original)
    if not candidates:raise RuntimeError("No September pro games; no post-hoc replacement")
    if any(v["match_id"] in original for v in candidates):raise AssertionError("Original 500 overlap")
    result={
      "study":"sept2026_external_200", "eligibility_preoutcome":"metadata_only",
      "start_utc":"2026-09-01T00:00:00+00:00",
      "end_exclusive_utc":"2026-10-01T00:00:00+00:00",
      "target":TARGET,"selected_count":len(candidates),
      "selection":"latest by (start_time, match_id), duration >=600, no outcome filtering",
      "pages_scanned":len(pages),"page_provenance":pages,
      "original500_id_overlap":0,"matches":candidates,
      "selected_metadata_sha256":canonical_digest(candidates),
    }
    if OUT.exists():raise FileExistsError("Selection already frozen: do not reselect")
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("OUTCOME_BLIND_SELECTION",json.dumps({"selected_count":len(candidates),
        "page_count":len(pages),"selected_sha256":result["selected_metadata_sha256"],
        "start_time_min":min(x["start_time"] for x in candidates),
        "start_time_max":max(x["start_time"] for x in candidates)}))

if __name__=="__main__":discover()
