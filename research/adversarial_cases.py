"""High-volume deterministic red team. Uses only the original 291 TRAIN
matches + synthetic fixtures and fake HTTP responses. No real network,
no original val/test labels, no candidate fitting outside TRAIN.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import random
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import requests

from research.robustness_study import build_data, CACHE, OUT
from tests.test_notebook_contracts import match_fixture

SEED=20261113
GEN=random.Random(SEED)
CATEGORIES={}
NOTES={}
def tick(category,num=1):CATEGORIES[category]=CATEGORIES.get(category,0)+num
def equivalent(a,b):
    assert set(a)==set(b),(set(a),set(b))
    for k in a:
        v,w=a[k],b[k]
        assert (pd.isna(v) and pd.isna(w)) or math.isclose(v,w,abs_tol=1e-10,rel_tol=0),(k,v,w)

def dev_games(ns):
    api=ns['OpenDota'](cache_dir=CACHE/'api-cache')
    manifest=pd.read_csv(CACHE/'vexil_takehome_outputs/match_manifest.csv')
    manifest=manifest.loc[manifest.partition=='train']
    games=[api.get('/matches/'+str(int(mid))) for mid in manifest.match_id]
    assert len(games)==291 and api.calls==0
    return games

def train_prefix_cases(ns,games):
    for game in games:
        last=int(game['duration'])//60
        chosen=sorted({0,1,2,5,9,10,15,20,30,last})
        for t in chosen:
            if t>last:continue
            truncated=ns['prefix_truncated'](game,t)
            equivalent(ns['snapshot_features'](game,t),
                       ns['snapshot_features'](truncated,t))
            a=ns['item_purchase_snapshot'](game,t)
            b=ns['item_purchase_snapshot'](truncated,t)
            assert all((pd.isna(x) and pd.isna(y)) or x==y for x,y in zip(a,b))
            tick('real_train_prefix_proofs')

def future_poison_cases(ns,games,count=1050):
    for _ in range(count):
        game=GEN.choice(games)
        t=GEN.randint(0,int(game['duration'])//60)
        original=ns['snapshot_features'](game,t)
        purchase=ns['item_purchase_snapshot'](game,t)
        bad=copy.deepcopy(game)
        bad['radiant_win']=not bool(game['radiant_win'])
        bad['duration']=99999999
        for k in ('radiant_gold_adv','radiant_xp_adv'):
            if isinstance(bad.get(k),list):
                n=len(bad[k])
                if t+1<n:bad[k][t+1:]=[10**9]*(n-t-1)
                bad[k].extend([10**9,10**9])
        bad['players'][0]['net_worth']=10**9
        bad['players'][0]['kills']=10**9
        if isinstance(bad.get('objectives'),list):
            bad['objectives'].append({
                'time':t*60+1,'type':'building_kill',
                'key':'npc_dota_badguys_tower2_top'})
        if isinstance(bad['players'][0].get('kills_log'),list):
            bad['players'][0]['kills_log'].append({'time':t*60+1,'key':'enemy'})
        if isinstance(bad['players'][0].get('purchase_log'),list):
            bad['players'][0]['purchase_log'].append({'time':t*60+1,'key':'blink'})
        equivalent(original,ns['snapshot_features'](bad,t))
        x=ns['item_purchase_snapshot'](bad,t)
        assert all((pd.isna(v) and pd.isna(w)) or v==w for v,w in zip(purchase,x))
        tick('full_future_poison_proofs')

def empty_fixture():
    m=match_fixture()
    m['objectives']=[]
    for p in m['players']:
        p['kills_log']=[]
        p['purchase_log']=[]
    return m

def event_boundary_cases(ns,count_per_family=300):
    families=[
      ('tower_radiant','tower_delta',1),
      ('tower_dire','tower_delta',-1),
      ('rax_radiant','barracks_delta',1),
      ('roshan_radiant','roshan_delta',1),
      ('roshan_dire','roshan_delta',-1),
      ('kill_radiant','kill_delta',1),
      ('kill_dire','kill_delta',-1),
      ('purchase_blink_radiant','major',1),
      ('purchase_bkb_dire','impact',-1)]
    for family,field,signed in families:
        for _ in range(count_per_family):
            t=GEN.randint(0,30)
            offset=GEN.choice((-1,0,1))
            when=t*60+offset
            m=empty_fixture()
            if family.startswith('tower') or family.startswith('rax'):
                key=(
                    'npc_dota_goodguys_tower1_top' if family=='tower_dire'
                    else 'npc_dota_badguys_melee_rax_mid' if family=='rax_radiant'
                    else 'npc_dota_badguys_tower1_top')
                m['objectives']=[{'time':when,'type':'building_kill','key':key}]
            elif family.startswith('roshan'):
                team=2 if family=='roshan_radiant' else 3
                m['objectives']=[{'time':when,'type':'CHAT_MESSAGE_ROSHAN_KILL','team':team}]
            elif family.startswith('kill'):
                idx=0 if family=='kill_radiant' else 5
                m['players'][idx]['kills_log']=[{'time':when,'key':'enemy'}]
            else:
                idx=0 if family=='purchase_blink_radiant' else 5
                key='blink' if idx==0 else 'black_king_bar'
                m['players'][idx]['purchase_log']=[{'time':when,'key':key}]
            expected=signed if offset<=0 else 0
            if family.startswith('purchase'):
                major,impact=ns['item_purchase_snapshot'](m,t)
                result=major if field=='major' else impact
            else:
                result=ns['snapshot_features'](m,t)[field]
            assert result==expected,(family,field,t,offset,result,expected)
            tick('event_exact_minute_boundary_oracle')

def invalid_clock_cases(ns):
    invalids=[float('nan'),float('inf'),float('-inf'),
              None,True,False,'1200','nan',[],{},complex(10,0)]
    families=['tower','roshan','kill','purchase','gold','xp']
    for value in invalids:
        for family in families:
            for repetition in range(30):
                m=empty_fixture()
                t=GEN.randint(1,30)
                if family=='tower':
                    m['objectives']=[{'time':value,'type':'building_kill',
                                      'key':'npc_dota_badguys_tower1_top'}]
                elif family=='roshan':
                    m['objectives']=[{'time':value,'type':'CHAT_MESSAGE_ROSHAN_KILL','team':2}]
                elif family=='kill':
                    m['players'][0]['kills_log']=[{'time':value,'key':'enemy'}]
                elif family=='purchase':
                    m['players'][0]['purchase_log']=[{'time':value,'key':'blink'}]
                elif family=='gold':
                    m['radiant_gold_adv'][t]=value
                else:
                    m['radiant_xp_adv'][t]=value
                if family=='purchase':
                    v=ns['item_purchase_snapshot'](m,t)
                    assert all(math.isnan(x) for x in v),(family,value,v)
                else:
                    # Fail closed or skip invalid; never use NaN/Inf/boolean
                    # as if it were a legitimate clock or measured numeric.
                    x=ns['snapshot_features'](m,t)
                    if family=='tower':assert x['tower_delta']==0
                    elif family=='roshan':assert x['roshan_delta']==0
                    elif family=='kill':assert x['kill_delta']==0
                    elif family=='gold':
                        assert math.isfinite(x['gold_k'])
                        assert x['gold_k']==m['radiant_gold_adv'][t-1]/1000
                    else:
                        assert math.isfinite(x['xp_k'])
                        assert x['xp_k']==m['radiant_xp_adv'][t-1]/1000
                tick('malformed_clock_and_observation_rejection')

def monotonicity_cases(ns,train,random_pairs=3000):
    cols=ns['SETS']['M1_time_value']
    model=ns['fit_model'](train,cols)
    time_max=int(train.minute.max())
    rows=[]
    for _ in range(random_pairs):
        minute=GEN.randint(0,time_max)
        gold_a=GEN.uniform(-40,39)
        gold_b=gold_a+GEN.uniform(.001,3.5)
        for g in (gold_a,gold_b):
            rows.append({'gold_k':g,'minute10':minute/10,
                         'gold_x_time':g*math.log1p(minute/10)})
    p=model.predict_proba(pd.DataFrame(rows)[cols])[:,1]
    assert np.isfinite(p).all() and np.logical_and(p>=0,p<=1).all()
    assert np.all(p[1::2]>p[0::2]),'gold monotonicity failed on training support'
    tick('M1_train_horizon_gold_monotonic_pairs',random_pairs)
    # Never extrapolate live behavior from training: a negative
    # outside-support slope is an alert, not a new model choice.
    late=[]
    for minute in range(time_max+1,131):
        g1,g2=2,3
        x=pd.DataFrame([{'gold_k':g,'minute10':minute/10,
                         'gold_x_time':g*math.log1p(minute/10)} for g in (g1,g2)])
        q=model.predict_proba(x[cols])[:,1]
        late.append((minute,bool(q[1]<q[0])))
    first_bad=next((t for t,bad in late if bad),None)
    assert first_bad is not None and first_bad>time_max
    NOTES.update(dict(max_train_minute=time_max,
                      first_negative_gold_slope_minute=first_bad,
                      negative_slope_minute_count=sum(int(b) for _,b in late)))
    tick('M1_out_of_support_horizon_warning_checks',len(late))

def fake_http_cases(ns):
    scenarios=('success','not_found','unauthorized','forbidden',
               '429_then_success','503_then_success','503_permanent',
               'malformed_json_then_success','timeout_then_success')
    class FakeResponse:
        def __init__(self,code,payload=None):
            self.status_code=code;self.headers={'Retry-After':'12'} if code==429 else {}
            self.payload=payload
        def json(self):
            if self.payload=='broken':raise ValueError('bad JSON')
            return self.payload
        def raise_for_status(self):
            if self.status_code>=400:
                raise requests.HTTPError(f'STATUS {self.status_code}')
    for scenario in scenarios:
        for iteration in range(25):
            with tempfile.TemporaryDirectory() as tmp:
                api=ns['OpenDota'](cache_dir=tmp,interval=0,max_retries=3)
                n=[0]
                def fake(url,params,timeout):
                    n[0]+=1
                    if scenario=='success':return FakeResponse(200,{'radiant_gold_adv':[0]})
                    if scenario=='not_found':return FakeResponse(404)
                    if scenario=='unauthorized':return FakeResponse(401)
                    if scenario=='forbidden':return FakeResponse(403)
                    if scenario=='429_then_success':
                        return FakeResponse(429) if n[0]==1 else FakeResponse(200,{'radiant_gold_adv':[0]})
                    if scenario=='503_then_success':
                        return FakeResponse(503) if n[0]==1 else FakeResponse(200,{'radiant_gold_adv':[0]})
                    if scenario=='503_permanent':return FakeResponse(503)
                    if scenario=='malformed_json_then_success':
                        return FakeResponse(200,'broken') if n[0]==1 else FakeResponse(200,{'radiant_gold_adv':[0]})
                    if scenario=='timeout_then_success':
                        if n[0]==1:raise requests.Timeout('synthetic')
                        return FakeResponse(200,{'radiant_gold_adv':[0]})
                    raise AssertionError('unknown scenario')
                api.session.get=fake
                with patch.object(ns['time'],'sleep',return_value=None):
                    try:result=api.get('/matches/123')
                    except Exception as exc:
                        assert scenario in ('not_found','unauthorized','forbidden','503_permanent'),scenario
                        if scenario=='not_found':assert type(exc).__name__=='MatchNotFound'
                        elif scenario=='503_permanent':assert isinstance(exc,RuntimeError)
                        else:assert isinstance(exc,requests.HTTPError)
                    else:
                        assert scenario not in ('not_found','unauthorized','forbidden','503_permanent')
                        assert result=={'radiant_gold_adv':[0]}
                assert 1<=n[0]<=3
                tick('fake_api_http_fail_closed_or_retry')

def statistic_cases(ns):
    for iteration in range(250):
        n=GEN.randint(6,30)
        rows=[]
        for mid in range(n):
            length=GEN.randint(2,12)
            a=GEN.uniform(.01,2);b=GEN.uniform(.01,2)
            for t in range(length):
                rows.append(dict(match_id=mid,minute=t,
                                 logloss_model=a+t*.002,
                                 logloss_baseline=b+t*.002))
        df=pd.DataFrame(rows)
        m=ns['match_bootstrap'](df,'logloss',n_boot=200,seed=SEED+iteration)
        assert m['matches']==n and m['rows']==len(df)
        assert math.isclose(m['model'],df.logloss_model.mean(),abs_tol=1e-12)
        assert math.isclose(m['baseline'],df.logloss_baseline.mean(),abs_tol=1e-12)
        assert math.isclose(m['difference'],m['model']-m['baseline'],abs_tol=1e-12)
        assert m['difference_lo']<=m['difference_hi']
        tick('grouped_bootstrap_arithmetic_identity')

def main():
    ns,manifest,train=build_data()
    games=dev_games(ns)
    train_prefix_cases(ns,games)
    future_poison_cases(ns,games)
    event_boundary_cases(ns)
    invalid_clock_cases(ns)
    monotonicity_cases(ns,train)
    fake_http_cases(ns)
    statistic_cases(ns)
    counts=sum(CATEGORIES.values())
    assert counts>=11000,counts
    OUT.mkdir(parents=True,exist_ok=True)
    receipt=dict(
      source='291 original train games + seeded synthetic/adversarial cases',
      seed=SEED,total_case_assertions=counts,categories=CATEGORIES,
      diagnostic_notes=NOTES,real_http_calls=0,
      validation_103_labels_scored=0,heldout_106_labels_scored=0,
      candidate_fitting_uses_only_291_train=True,
      intended_use='redteam correctness/stability, NOT evidence of model lift')
    (OUT/'adversarial_qa_receipt.json').write_text(
       json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('ADVERSARIAL_QA_FINAL_PASS',json.dumps(receipt,sort_keys=True),flush=True)

if __name__=='__main__':main()
