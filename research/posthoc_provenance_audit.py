#!/usr/bin/env python3
"""Label-free input provenance audit after one-shot factory score; NO refitting."""
from __future__ import annotations
import hashlib
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
BASE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
DEST=ROOT/'research/results/posthoc_provenance_audit.json'

def main():
    manifest=pd.read_csv(BASE/'vexil_takehome_outputs/match_manifest.csv',
                         usecols=['match_id','start_time','patch','series_id','partition'])
    assert len(manifest)==500
    subsets={name:manifest[manifest.partition==name].copy() for name in ('train','validation','test')}
    assert [len(subsets[x]) for x in subsets]==[291,103,106]
    original=pd.read_csv(BASE/'vexil_takehome_outputs/validation_ablations.csv')
    m1=float(original.loc[original.model=='M1_time_value','log_loss'].iloc[0])
    m0=float(original.loc[original.model=='M0_gold_only','log_loss'].iloc[0])
    scores=pd.read_csv(ROOT/'research/results/all_28_candidate_scores.csv')
    observed_m1=float(scores.loc[scores.model=='M1_time_value','logloss'].iloc[0])
    assert abs(m1-observed_m1)<1e-12,('M1 not numerically reproducible',m1,observed_m1)
    seen={name:set(d.match_id.astype(int)) for name,d in subsets.items()}
    assert all(not (seen[a]&seen[b]) for i,a in enumerate(seen) for b in list(seen)[i+1:])
    bounds={}
    for name,data in subsets.items():
        positive_sids={int(i) for i in data.series_id if int(i)>0}
        bounds[name]={
            'matches':len(data),
            'start_time_min':int(data.start_time.min()),
            'start_time_max':int(data.start_time.max()),
            'positive_series':len(positive_sids),
            'series0_games':int((data.series_id<=0).sum()),
            'patch_counts':{str(k):int(v) for k,v in data.patch.value_counts().items()}
        }
    assert bounds['train']['start_time_max']<=bounds['validation']['start_time_min']
    assert bounds['validation']['start_time_max']<=bounds['test']['start_time_min']
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        assert not ({int(x) for x in subsets[a].series_id if int(x)>0}
                    & {int(x) for x in subsets[b].series_id if int(x)>0}),(
                        'series overlap',a,b)
    # Sample-specific hero/item coverage. All calls cache-hit and no score labels used.
    api=load_definitions()['OpenDota'](cache_dir=BASE/'api-cache')
    hero_ids=Counter()
    missing=Counter()
    item_keys=Counter()
    val_teams=[]
    byday=Counter()
    dev=manifest[manifest.partition.isin(('train','validation'))]
    from research.proposal_factory_features import MAJOR_ITEM_KEYS
    for row in dev.itertuples():
        game=api.get('/matches/'+str(int(row.match_id)))
        if game.get('players') is None:missing['missing_players']+=1;continue
        for p in game['players']:
            hid=p.get('hero_id')
            if isinstance(hid,int):hero_ids[hid]+=1
            else:missing['missing_hero_id']+=1
            for event in p.get('purchase_log') or []:
                if event.get('key') in MAJOR_ITEM_KEYS:
                    item_keys[event['key']]+=1
        if row.partition=='validation':
            date=datetime.fromtimestamp(int(row.start_time),timezone.utc).strftime('%Y-%m-%d')
            byday[date]+=1
            # Team identity is retrieved only for a descriptive grouping audit.
            rt=game.get('radiant_team_id')
            dt=game.get('dire_team_id')
            val_teams.append({'match_id':int(row.match_id),'date':date,
                              'radiant_team_id':rt,'dire_team_id':dt,
                              'series_id':int(row.series_id)})
    assert api.calls==0
    assert max(hero_ids)<=160,('hero out of predefined 160',max(hero_ids))
    assert min(hero_ids)>=1
    assert sum(hero_ids.values())==394*10
    assert missing['missing_hero_id']==0
    result={
        'audit_type':'descriptive posthoc; no scoring, model fits or unconsumed test payloads',
        'source_input_manifest_has_labels':False,
        'manifest_header':list(manifest.columns),
        'input_split':bounds,
        'original_validation_M0_logloss':m0,
        'original_validation_M1_logloss':m1,
        'factory_M1_logloss':observed_m1,
        'M1_parity_abs_error':abs(m1-observed_m1),
        'no_positive_series_split':True,
        'chronological_split':True,
        'hero_id_min':min(hero_ids),'hero_id_max':max(hero_ids),
        'hero_id_count':sum(hero_ids.values()),
        'hero_ids_over160':sum(n for hid,n in hero_ids.items() if hid>160),
        'major_purchase_event_count':sum(item_keys.values()),
        'top_major_keys':item_keys.most_common(30),
        'validation_games_per_utc_day':dict(byday),
        'validation_team_id_availability':{
            'total':len(val_teams),
            'both_team_ids_nonzero':sum(bool(x['radiant_team_id']) and bool(x['dire_team_id']) for x in val_teams)
        },
        'validation_match_teams':val_teams,
        'http_calls':api.calls
    }
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('POSTHOC_LABEL_FREE_SOURCE_AUDIT_PASS',json.dumps({
      k:v for k,v in result.items() if k not in ('validation_match_teams','top_major_keys')
    },sort_keys=True))
    print('TOP_PURCHASE_EVENTS',item_keys.most_common(12))

if __name__=='__main__':main()
