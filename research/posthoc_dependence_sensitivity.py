#!/usr/bin/env python3
"""Post-result descriptive cluster sensitivity for P20, never a selection gate.

Compares original series-or-singleton grouping to same two-team matchup/day
and same league/day, without model refitting or changing preregistered rule.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.test_notebook_contracts import load_definitions

DATA=ROOT/'research/results'
BASE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
SEED=20261113
REPS=5000

def boot(frame,cluster):
    y=frame.radiant_win.to_numpy(int)
    p0=np.clip(frame.p_M1_time_value.to_numpy(float),1e-15,1-1e-15)
    p1=np.clip(frame.p_P20.to_numpy(float),1e-15,1-1e-15)
    d0=-(y*np.log(p0)+(1-y)*np.log1p(-p0))
    d1=-(y*np.log(p1)+(1-y)*np.log1p(-p1))
    temp=pd.DataFrame({'cluster':cluster,'n':1.,'d':d1-d0})
    a=temp.groupby('cluster',sort=True).agg(n=('n','sum'),d=('d','sum'))
    v=a[['n','d']].to_numpy(float)
    observed=v[:,1].sum()/v[:,0].sum()
    rng=np.random.default_rng(SEED)
    idx=rng.integers(0,len(v),size=(REPS,len(v)))
    q=v[idx].sum(axis=1)
    dist=q[:,1]/q[:,0]
    lo,hi=np.quantile(dist,[.025,.975])
    return {'group_count':len(v),'delta_ll_P20_minus_M1':float(observed),
            'posthoc_percentile95_low':float(lo),
            'posthoc_percentile95_high':float(hi),
            'draws':REPS,'seed':SEED}

def main():
    df=pd.read_csv(DATA/'dev_validation_predictions_28.csv')
    assert df.match_id.nunique()==103
    original=pd.read_csv(DATA/'all_28_candidate_scores.csv')
    expected=float(original.loc[original.model=='P20','delta_ll_vs_M1'].iloc[0])
    vals=json.loads((DATA/'posthoc_provenance_audit.json').read_text())['validation_match_teams']
    meta={int(r['match_id']):r for r in vals}
    api=load_definitions()['OpenDota'](cache_dir=BASE/'api-cache')
    leagues={}
    for mid in meta:
        game=api.get('/matches/'+str(mid))
        leagues[mid]=int(game.get('leagueid') or 0)
    assert api.calls==0
    cluster_strings={}
    for mid in df.match_id.unique():
        m=meta[int(mid)]
        r=int(m['radiant_team_id']);d=int(m['dire_team_id'])
        pair=tuple(sorted((r,d)))
        league=leagues[int(mid)]
        sid=int(m['series_id'])
        date=m['date']
        cluster_strings[int(mid)]={
            'series':('series',sid) if sid>0 else ('match',int(mid)),
            'team_pair_day':('pairday',date,*pair),
            'team_pair':('pair',*pair),
            'league_day':('league_day',date,league),
        }
    output=[]
    for name in ('series','team_pair_day','team_pair','league_day'):
        group=[cluster_strings[int(mid)][name] for mid in df.match_id]
        result=boot(df,[str(x) for x in group])
        result['cluster_scheme']=name
        result['claim_level']='POSTHOC_DESCRIPTIVE_ONLY'
        output.append(result)
        assert abs(result['delta_ll_P20_minus_M1']-expected)<1e-12
    result=pd.DataFrame(output)
    result.to_csv(DATA/'posthoc_P20_dependence_sensitivity.csv',index=False)
    print('ADDITIONAL_CLUSTER_SENSITIVITY_NO_MODEL_FIT')
    print(result.to_string(index=False,float_format=lambda x:f'{x:.6f}'))
    print('NOTE: league-day clusters can be too few to justify percentile coverage; post-hoc, not used for promotion.')

if __name__=='__main__':main()
