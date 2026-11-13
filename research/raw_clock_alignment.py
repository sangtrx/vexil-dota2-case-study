"""Cached OpenDota as-of-minute gold/XP clock alignment.

Read-only QA of the fixed 500 match source payloads. No model fitting,
new holdout selection, external APIs, or trade profitability claims.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from research.robustness_study import defs,CACHE,OUT

def main():
    ns=defs()
    api=ns['OpenDota'](cache_dir=CACHE/'api-cache')
    manifest=pd.read_csv(CACHE/'vexil_takehome_outputs/match_manifest.csv')
    assert len(manifest)==500 and manifest.match_id.nunique()==500
    checks=defaultdict(int)
    offenders=[]
    for record in manifest.itertuples():
        game=api.get('/matches/'+str(int(record.match_id)))
        assert int(game['match_id'])==int(record.match_id)
        duration=int(game['duration'])
        assert duration>0
        n=duration//60+1
        players=game.get('players')
        if not isinstance(players,list) or len(players)!=10:
            offenders.append((record.match_id,'player_count'))
            continue
        if any(not isinstance(p.get('gold_t'),list) or
               not isinstance(p.get('xp_t'),list) for p in players):
            offenders.append((record.match_id,'player_time_series_missing'))
            continue
        if any(len(p['gold_t'])<n or len(p['xp_t'])<n for p in players):
            offenders.append((record.match_id,'player_time_series_short'))
            continue
        gold=game.get('radiant_gold_adv')
        xp=game.get('radiant_xp_adv')
        if not isinstance(gold,list) or not isinstance(xp,list) or len(gold)<n or len(xp)<n:
            offenders.append((record.match_id,'summary_time_series_short'))
            continue
        slots=[p.get('player_slot') for p in players]
        if set(slots)!=set(range(5))|set(range(128,133)):
            offenders.append((record.match_id,'player_slot_invalid'))
            continue
        for t in range(n):
            rg=sum(int(p['gold_t'][t]) for p in players if p['player_slot']<128)
            dg=sum(int(p['gold_t'][t]) for p in players if p['player_slot']>=128)
            rx=sum(int(p['xp_t'][t]) for p in players if p['player_slot']<128)
            dx=sum(int(p['xp_t'][t]) for p in players if p['player_slot']>=128)
            if not np.isclose(float(gold[t]),rg-dg,rtol=0,atol=1e-7):
                offenders.append((record.match_id,t,'gold_diff',float(gold[t]),rg-dg))
            if not np.isclose(float(xp[t]),rx-dx,rtol=0,atol=1e-7):
                offenders.append((record.match_id,t,'xp_diff',float(xp[t]),rx-dx))
            checks['match_minutes']+=1
            checks['gold_summary_vs_player_sums']+=1
            checks['xp_summary_vs_player_sums']+=1
        checks['matches']+=1
        for p in players:
            for name in ('purchase_log','kills_log'):
                if isinstance(p.get(name),list):
                    checks[name+'_player_streams_present']+=1
                else:
                    checks[name+'_player_streams_missing']+=1
    assert api.calls==0
    report=dict(checks,failures=len(offenders),
      first_five_offenders=offenders[:5],
      source='cached original 500 OpenDota match payloads',
      no_network_calls=True,
      original_heldout_outcomes_used_for_model_selection=False,
      timestamp_contract='player gold_t/xp_t array index t vs aggregate at minute t')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'raw_clock_alignment_receipt.json').write_text(
        json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('SOURCE_TIMELINE_ALIGNMENT',json.dumps(report,sort_keys=True),flush=True)
    assert not offenders,'OpenDota clock data misalignment: '+repr(offenders[:5])
    assert checks['match_minutes']==18304
    print('ALL_500_OPEN_DOTA_CLOCKS_ALIGNED_PASS',flush=True)

if __name__=='__main__':main()
