#!/usr/bin/env python3
"""Descriptive after-the-fact influence analysis; does not alter locked gate."""
from __future__ import annotations
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
RAW=Path('/srv/ai/tmp/vexil-september-raw-20261118')
CSV=HERE/'external_september_predictions.csv'
OUT=HERE/'posthoc_influence_receipt.json'
SEED=20261118

def paired_delta_and_ci(df,count=5000):
    if len(df)==0:raise ValueError('no rows')
    groups=np.asarray([(len(x),float(x.delta.sum())) for _,x in df.groupby('series_group',sort=True)])
    rng=np.random.default_rng(SEED)
    draws=rng.integers(0,len(groups),size=(count,len(groups)))
    g=groups[draws]
    vals=g[:,:,1].sum(1)/g[:,:,0].sum(1)
    return {'games':int(df.match_id.nunique()),'minutes':len(df),
        'groups':len(groups),'delta_logloss':float(df.delta.mean()),
        'cluster_CI95':[float(a) for a in np.quantile(vals,[.025,.975])]}

def analyze():
    d=pd.read_csv(CSV)
    y=d.radiant_win.to_numpy()
    for model in ('m0','m1'):
        p=np.clip(d['p_'+model].to_numpy(),1e-12,1-1e-12)
        d['log_'+model]=-(y*np.log(p)+(1-y)*np.log1p(-p))
    d['delta']=d.log_m1-d.log_m0
    sums=d.groupby('match_id').delta.sum().sort_values()
    base=paired_delta_and_ci(d)
    assert len(sums)==199
    influence={}
    for k in (1,2,5,10):
        excluded=set(sums.index[:k])
        influence[str(k)]=paired_delta_and_ci(d[~d.match_id.isin(excluded)])
    leagues={}
    for lid in sorted(d.league_id.unique()):
        excluded=d[d.league_id==lid]
        remain=d[d.league_id!=lid]
        leagues[str(int(lid))]={
            'excluded_games':int(excluded.match_id.nunique()),
            'own_delta':float(excluded.delta.mean()),
            'leave_out':paired_delta_and_ci(remain)
        }
    teams=defaultdict(set)
    parent={}
    league_teams=defaultdict(set)
    for mid in sums.index:
        file=RAW/(str(int(mid))+'.json.gz')
        with gzip.open(file,'rt') as f:
            m=json.load(f)
        a,b=m.get('radiant_team_id'),m.get('dire_team_id')
        lid=int(m.get('leagueid') or 0)
        if type(a) is not int or type(b) is not int or not a or not b:
            raise ValueError('team identifiers unavailable for match '+str(mid))
        for team in (a,b):
            teams[team].add(int(mid))
            league_teams[lid].add(team)
            parent.setdefault(team,team)
        def find(x):
            while parent[x]!=x:
                parent[x]=parent[parent[x]]
                x=parent[x]
            return x
        pa,pb=find(a),find(b)
        if pa!=pb:parent[pb]=pa
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    comps=Counter(find(x) for x in teams)
    out=[]
    for team,matches in teams.items():
        x=d[~d.match_id.isin(matches)]
        out.append((len(matches),float(x.delta.mean())))
    report={
        'scope':'post-hoc influence diagnostics, NOT any precommitted model selection or new blind test',
        'original_september_results_unchanged':True,
        'predictions_sha256':hashlib.sha256(CSV.read_bytes()).hexdigest(),
        'original':base,
        'contribution_of_most_favorable_match':float(sums.iloc[0]/d.delta.sum()),
        'matches_where_m1_better':int((sums<0).sum()),
        'matches_where_m0_better':int((sums>0).sum()),
        'remove_most_favorable_matches':influence,
        'leave_one_league':leagues,
        'teams':{
            'distinct_teams':len(teams),
            'max_games_same_team':max(map(len,teams.values())),
            'team_match_graph_components':len(comps),
            'team_component_sizes':sorted(comps.values(),reverse=True),
            'leave_one_team_delta_range':[min(x[1] for x in out),max(x[1] for x in out)],
            'all_leave_one_team_deltas_negative':all(x[1]<0 for x in out),
            'league_team_overlap_counts':{
                str(a)+'_'+str(b):len(league_teams[a]&league_teams[b])
                for a in sorted(league_teams) for b in sorted(league_teams) if a<b
            },
        },
        'interpretation':'Series bootstrap conditions on within-series dependence; shared teams and only 3 leagues prevent broader independent-tournament inference. Top-5 favorable-match deletion crosses zero; this is a stress test, not a revised primary gate.'
    }
    if abs(report['original']['delta_logloss']-(-0.039628322370206526))>1e-10:
        raise RuntimeError('Original result drifted')
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('POSTHOC_INFLUENCE_RECEIPT',json.dumps({
        'source_matches':base['games'],'primary_delta':base['delta_logloss'],
        'after_5_best':influence['5']['delta_logloss'],
        'after_5_best_ci':influence['5']['cluster_CI95'],
        'teams':len(teams),'connected_components':sorted(comps.values(),reverse=True),
        'all_loo_teams_negative':report['teams']['all_leave_one_team_deltas_negative']
    },sort_keys=True))
if __name__=='__main__':analyze()
