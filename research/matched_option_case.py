#!/usr/bin/env python3
"""Outcome-blind descriptive case pair from original TRAIN games only.

Find a fixed-minute (25) same-patch pair where gold advantages are
similar but the recent Aegis claim state differs. Matching uses only
gold, XP, patch and Aegis signal, NEVER the final outcome.
This is a case illustration, NOT causal identification or evaluation.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.strategic_option_value import option_snapshot
from tests.test_notebook_contracts import load_definitions

N=load_definitions()
BASE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
OUT=Path('/home/ai-agent/.cache/vexil-option-novelty-20261113')
MINUTE=25
# Predeclared nested tolerance ladder (gold in units, XP in units).
LEVELS=((300,1200),(600,2000),(1000,3000),(1600,4500))

def choices():
    manifest=pd.read_csv(BASE/'vexil_takehome_outputs/match_manifest.csv')
    rows=manifest[manifest.partition=='train'].copy()
    assert len(rows)==291
    api=N['OpenDota'](cache_dir=BASE/'api-cache')
    snapshots=[];games={}
    for record in rows.itertuples(index=False):
        mid=int(record.match_id)
        game=api.get('/matches/'+str(mid))
        games[mid]=game
        if int(game['duration'])//60 < MINUTE:continue
        info=option_snapshot(game,MINUTE)
        gold=N['last_observed'](game.get('radiant_gold_adv'),MINUTE)
        xp=N['last_observed'](game.get('radiant_xp_adv'),MINUTE)
        if not np.isfinite(gold) or not np.isfinite(xp):continue
        if not all(np.isfinite(x) for x in info.values()):continue
        snapshots.append(dict(match_id=mid,patch=str(record.patch),series_id=int(record.series_id),
                              start_time=int(record.start_time),gold=float(gold),xp=float(xp),
                              **info))
    assert api.calls==0,'Only cached original 500 data allowed'
    # Outcome-blind: only compares gold same side, XP and Aegis claim state.
    candidates=[]
    for a in snapshots:
        if a['aegis_claim5']<=.2:continue
        if a['gold']<1000 or a['gold']>5000:continue
        for b in snapshots:
            if b['match_id']==a['match_id'] or b['patch']!=a['patch']:continue
            if a['series_id']>0 and a['series_id']==b['series_id']:continue
            if abs(b['aegis_claim5'])>1e-10:continue
            if b['gold']<=0:continue
            gold_gap=abs(a['gold']-b['gold']);xp_gap=abs(a['xp']-b['xp'])
            candidates.append((a,b,gold_gap,xp_gap))
    for level,(gmax,xmax) in enumerate(LEVELS,1):
        eligible=[(a,b,g,x) for a,b,g,x in candidates if g<=gmax and x<=xmax]
        if eligible:
            a,b,g,x=min(eligible,key=lambda z:(z[2]/gmax+z[3]/xmax,
                                                 z[2],z[3],z[0]['match_id'],
                                                 z[1]['match_id']))
            return (a,b,level,g,x),games,api.calls
    raise RuntimeError('No outcome-blind matched strategic-state pair in fixed tolerance ladder')

def main():
    (a,b,level,gd,xd),games,calls=choices()
    pair=[]
    for tag,item in [('recent_radiant_aegis_claim',a),('no_recent_claim',b)]:
        game=games[item['match_id']]
        # Final labels are intentionally read only AFTER the pair was selected.
        pair.append(dict(case=tag,**item,
                         observed_radiant_win=bool(game['radiant_win'])))
    receipt=dict(
        method='Fixed minute25, same patch, same gold-lead sign; distinct match and series; latest Aegis claim contrast; closest gold/XP under preset tolerance ladder',
        outcome_used_in_selection=False,
        selected_tolerance_tier=level,gold_diff=gd,xp_diff=xd,
        minute=MINUTE,cohort='original TRAIN games only',
        games=pair,
        caveat='Descriptive in-sample pair. Aegis claim is not evidence of unconsumed possession. No causal or independent predictive claim.'
    )
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'matched_option_case_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    data=[]
    for record in pair:
        match=games[record['match_id']]
        for t in range(0,int(match['duration'])//60+1):
            o=option_snapshot(match,t)
            data.append({
                'case':record['case'],
                'match_id':record['match_id'],'minute':t,
                'gold_lead':N['last_observed'](match.get('radiant_gold_adv'),t),
                'xp_lead':N['last_observed'](match.get('radiant_xp_adv'),t),
                **o,
                'outcome_radiant_win':int(match['radiant_win']),
            })
    pd.DataFrame(data).to_csv(OUT/'matched_option_case_timeline.csv',index=False)
    print('OUTCOME_BLIND_MATCHED_CASE_SELECTION',json.dumps(receipt,sort_keys=True))
    print('NO_EXTRA_API_REQUESTS',calls)

if __name__=='__main__':main()
