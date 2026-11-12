#!/usr/bin/env python3
"""Outcome-blind Roshan/Aegis/buyback/purchase time audit for 900 cached games.

Checks plausibility and independent match-level first-blood summary agreement.
Does NOT prove that event and gold clocks are universally synchronized.
"""
from __future__ import annotations
import json
import math
import sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions

BASE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
OUT=Path('/home/ai-agent/.cache/vexil-option-novelty-20261113')
SOURCES=[
('original500',BASE/'manifest_metadata.json'),
('first_forward200',Path('/home/ai-agent/.cache/vexil-edge-v2-20261113/forward_holdout_manifest.json')),
('second_forward200',Path('/home/ai-agent/.cache/vexil-edge-v3-20261113/gate_confirmation_manifest.json'))
]
MIN_EVENT_TIME=-120
MAX_POSTGAME_PAD=120

def clock(event):
    value=event.get('time') if isinstance(event,dict) else None
    return float(value) if type(value) in (int,float) and math.isfinite(value) else None

def main():
    n=load_definitions()
    api=n['OpenDota'](cache_dir=BASE/'api-cache')
    out={}
    for label,path in SOURCES:
        meta=json.loads(path.read_text())
        counts=Counter(); examples=[]
        lags=[]
        firstblood_diffs=[]
        for row in meta:
            game=api.get('/matches/'+str(row['match_id']))
            duration=int(game['duration'])
            objs=game.get('objectives')
            counts['matches']+=1
            if not isinstance(objs,list):
                counts['missing_objectives']+=1
                continue
            rosh=[]
            aegis=[]
            first=[]
            for ev in objs:
                kind=ev.get('type','<none>') if isinstance(ev,dict) else '<invalid>'
                ts=clock(ev)
                counts['objective_events']+=1
                if ts is None:
                    counts['nonfinite_event_time']+=1
                    examples.append((row['match_id'],'invalid_objective_time',ev))
                    continue
                if ts<MIN_EVENT_TIME or ts>duration+MAX_POSTGAME_PAD:
                    counts['out_of_bound_objectives']+=1
                    examples.append((row['match_id'],'objective_time_out_of_bounds',kind,ts,duration))
                if kind=='CHAT_MESSAGE_ROSHAN_KILL':
                    rosh.append(ts)
                    counts['roshan_events']+=1
                if kind=='CHAT_MESSAGE_AEGIS':
                    aegis.append(ts)
                    counts['aegis_claim_events']+=1
                    slot=ev.get('player_slot')
                    if type(slot) is not int or not (0<=slot<5 or 128<=slot<133):
                        counts['aegis_missing_player_side']+=1
                if kind=='CHAT_MESSAGE_FIRSTBLOOD':
                    first.append(ts)
            for at in aegis:
                before=[rt for rt in rosh if rt<=at]
                if not before:
                    counts['aegis_without_prior_roshan']+=1
                    examples.append((row['match_id'],'aegis_without_prior_roshan',at))
                else:
                    lag=at-max(before)
                    lags.append(lag)
                    if lag>60:
                        counts['aegis_more_than_60sec_after_roshan']+=1
                        if len(examples)<30:examples.append((row['match_id'],'aegis_lag_gt60',at,lag))
            if first:
                fb=game.get('first_blood_time')
                if type(fb) in (int,float) and math.isfinite(fb):
                    expected=max(0.,min(first))
                    diff=float(fb)-expected
                    firstblood_diffs.append(diff)
                    if abs(diff)>5:
                        counts['firstblood_summary_mismatch_gt5sec']+=1
                        if len(examples)<30:examples.append((row['match_id'],'firstblood_mismatch',fb,first,expected))
                else:
                    counts['firstblood_summary_missing']+=1
            players=game.get('players') or []
            for p in players:
                for log in ('buyback_log','purchase_log','kills_log'):
                    vals=p.get(log)
                    if not isinstance(vals,list):
                        counts['missing_'+log]+=1
                        continue
                    counts[log+'_events']+=len(vals)
                    for ev in vals:
                        ts=clock(ev)
                        if ts is None:
                            counts['nonfinite_'+log+'_time']+=1
                            continue
                        if ts<MIN_EVENT_TIME or ts>duration+MAX_POSTGAME_PAD:
                            counts['out_of_bound_'+log]+=1
                            if len(examples)<30:examples.append((row['match_id'],log,'out_of_bounds',ts,duration))
        report=dict(
           games=counts['matches'],counts=dict(counts),
           aegis_after_roshan_lags_seconds={
             'N':len(lags),
             'p50':float(np.median(lags)) if lags else None,
             'p95':float(np.quantile(lags,.95)) if lags else None,
             'p99':float(np.quantile(lags,.99)) if lags else None,
             'max':max(lags) if lags else None},
           firstblood_summary_diffs_seconds={
             'N':len(firstblood_diffs),
             'p50_abs':float(np.median(np.abs(firstblood_diffs))) if firstblood_diffs else None,
             'max_abs':max(map(abs,firstblood_diffs)) if firstblood_diffs else None},
           anomaly_examples=examples[:30])
        out[label]=report
        print('OUTCOME_BLIND_EVENT_CLOCK_AUDIT',label,json.dumps(report,sort_keys=True))
    assert api.calls==0
    summary=dict(datasets=out,total_matches=900,http_calls=api.calls,
                 caveat='Finite Roshan/Aegis/firstblood clock comparisons, not proof of wall-clock streaming arrival or complete event capture.')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'event_clock_audit_receipt.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print('EVENT_CLOCK_AUDIT_COMPLETE')

if __name__=='__main__':main()
