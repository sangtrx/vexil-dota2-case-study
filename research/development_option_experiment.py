#!/usr/bin/env python3
"""Exploratory ONLY on previously inspected 291 train / 103 validation games.

No use of the already-consumed 106+200+200 held-out outcome sets.
Model specifications were registered in docs and committed before this run.
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
from tests.test_notebook_contracts import load_definitions
from research.strategic_option_value import option_snapshot,option_prefix_truncated,FEATURES

N=load_definitions()
BASE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
OUT=Path('/home/ai-agent/.cache/vexil-option-novelty-20261113')
SEED=20261113
BOOTS=5000
SPEC={
    'M1_gold_time':('gold_k','minute10','gold_x_time'),
    'M1_ephemeral':('gold_k','minute10','gold_x_time','aegis_claim5','buyback_commitment5'),
    'M1_structural':('gold_k','minute10','gold_x_time','unconverted_gold_k'),
    'M4_option_value':('gold_k','minute10','gold_x_time',*FEATURES),
    'M3_original':tuple(N['SETS']['M3_objective_conversion']),
}


def value_equal(a,b):
    return all((pd.isna(a[k]) and pd.isna(b[k])) or
               abs(a[k]-b[k])<1e-12 for k in a)


def load_development():
    meta=pd.read_csv(BASE/'vexil_takehome_outputs/match_manifest.csv')
    assert len(meta)==500 and meta.match_id.nunique()==500
    dev=meta.loc[meta.partition.isin(['train','validation'])].copy()
    assert dev.partition.value_counts().to_dict()=={'train':291,'validation':103}
    api=N['OpenDota'](cache_dir=BASE/'api-cache',interval=1.65)
    games=[api.get('/matches/'+str(int(mid))) for mid in dev.match_id]
    assert api.calls==0, 'Cache-only exploratory experiment; no API calls permitted'
    records=[];checks=0
    for game in games:
        for minute in range(int(game['duration'])//60+1):
            b=N['snapshot_features'](game,minute)
            a=option_snapshot(game,minute)
            records.append({'match_id':int(game['match_id']),'minute':minute,
                            'radiant_win':int(game['radiant_win']),**b,**a})
        for minute in sorted({0,1,9,10,15,20,min(30,int(game['duration'])//60)}):
            a=option_snapshot(game,minute)
            b=option_snapshot(option_prefix_truncated(game,minute),minute)
            assert value_equal(a,b),(game['match_id'],minute,a,b)
            checks+=1
    frame=pd.DataFrame(records).merge(
        dev[['match_id','partition','start_time','series_id','patch']],
        on='match_id',validate='many_to_one')
    assert len(frame)==sum(int(m['duration'])//60+1 for m in games)
    assert frame[['match_id','minute']].duplicated().sum()==0
    return dev,frame,checks


def scoring(pred,y):
    return float(log_loss(y,pred,labels=[0,1])),float(brier_score_loss(y,pred))


def ci(pnew,pbase,frame,unit='series'):
    y=frame.radiant_win.to_numpy(dtype=int)
    ll=lambda p:-(y*np.log(np.clip(p,1e-15,1-1e-15))+
                   (1-y)*np.log1p(-np.clip(p,1e-15,1-1e-15)))
    groups=(frame.match_id.astype(str) if unit=='match' else
            np.where(frame.series_id.astype(int)>0,
                     's'+frame.series_id.astype(str),
                     'm'+frame.match_id.astype(str)))
    tmp=pd.DataFrame({'group':groups,'n':1,'diff':ll(pnew)-ll(pbase)})
    a=tmp.groupby('group',sort=True).agg(n=('n','sum'),diff=('diff','sum')).to_numpy(float)
    observed=float(a[:,1].sum()/a[:,0].sum())
    rng=np.random.default_rng(SEED)
    reps=a[rng.integers(0,len(a),size=(BOOTS,len(a)))].sum(axis=1)
    boot=reps[:,1]/reps[:,0]
    lo,hi=np.quantile(boot,[.025,.975])
    return {'unit':unit,'clusters':len(a),'delta':observed,'lo':float(lo),'hi':float(hi)}


def safe_cuts(meta):
    ids=list(meta.match_id)
    keys=[('s',int(s)) if int(s)>0 else ('m',int(mid))
          for s,mid in zip(meta.series_id,ids)]
    span={}
    for i,key in enumerate(keys):
        if key not in span:span[key]=[i,i]
        else:span[key][1]=i
    return [cut for cut in range(1,len(meta))
            if all(not (a<cut<=b) for a,b in span.values())]


def walkforward(manifest,frame):
    m=manifest.loc[manifest.partition=='train'].sort_values(
        ['start_time','match_id']).reset_index(drop=True)
    valid=safe_cuts(m)
    result=[]
    # Choose deterministic chronological cutoffs by fractions of train GAME count.
    # Sparse group-safe cutpoints can create a shorter first validation block;
    # do not force a split through a professional series merely to hit a size.
    targets=[len(m)*f for f in (.52,.60,.75,.92)]
    points=[min(valid,key=lambda c:(abs(c-t),c)) for t in targets]
    assert points==sorted(set(points)) and len(points)==4,points
    for fold,(start,end) in enumerate(zip(points[:-1],points[1:]),1):
        train_ids=set(m.iloc[:start].match_id)
        val_ids=set(m.iloc[start:end].match_id)
        assert not train_ids&val_ids
        tr=frame.loc[frame.match_id.isin(train_ids)]
        va=frame.loc[frame.match_id.isin(val_ids)]
        p={}
        for name in ('M1_gold_time','M4_option_value'):
            model=N['fit_model'](tr,list(SPEC[name]))
            p[name]=model.predict_proba(va[list(SPEC[name])])[:,1]
        a,b=scoring(p['M4_option_value'],va.radiant_win),scoring(p['M1_gold_time'],va.radiant_win)
        result.append({'fold':fold,'train_games':len(train_ids),'eval_games':len(val_ids),
                       'm1_ll':b[0],'m4_ll':a[0],'m4_minus_m1':a[0]-b[0],
                       'm1_brier':b[1],'m4_brier':a[1]})
    return pd.DataFrame(result)


def main():
    dev,frame,checks=load_development()
    tr=frame.loc[frame.partition=='train'];va=frame.loc[frame.partition=='validation']
    y=va.radiant_win.to_numpy(dtype=int)
    probs={};results=[]
    for name,cols in SPEC.items():
        model=N['fit_model'](tr,list(cols))
        probs[name]=model.predict_proba(va[list(cols)])[:,1]
        ll,br=scoring(probs[name],y)
        results.append({'model':name,'predictors':len(cols),
                        'validation_logloss':ll,'validation_brier':br})
    result=pd.DataFrame(results)
    baseline_ll=result.loc[result.model=='M1_gold_time','validation_logloss'].iloc[0]
    result['delta_vs_m1']=result.validation_logloss-baseline_ll
    uncertainty=pd.DataFrame([ci(probs['M4_option_value'],probs['M1_gold_time'],va,unit)
                              for unit in ('match','series')])
    rolls=walkforward(dev,frame)
    phase=pd.cut(va.minute,[-1,9,19,29,1000],labels=['0-9','10-19','20-29','30+'])
    feat=[]
    for period,values in va.groupby(phase,observed=True):
        for col in FEATURES:
            feat.append({'phase':str(period),'feature':col,
                         'minute_rows':len(values),'available_pct':float(values[col].notna().mean()*100),
                         'nonzero_pct':float((values[col].fillna(0).abs()>1e-12).mean()*100)})
    features=pd.DataFrame(feat)
    # Registered screen gate. DO NOT reselect a different model if M4 fails.
    m4=result.loc[result.model=='M4_option_value'].iloc[0]
    ci_series=uncertainty.loc[uncertainty.unit=='series'].iloc[0]
    passed=bool(m4.delta_vs_m1<=-0.005 and ci_series.hi<0 and
                m4.validation_brier<=result.loc[result.model=='M1_gold_time','validation_brier'].iloc[0]
                and int((rolls.m4_minus_m1<0).sum())>=2)
    OUT.mkdir(parents=True,exist_ok=True)
    result.to_csv(OUT/'option_development_ablations.csv',index=False)
    uncertainty.to_csv(OUT/'option_development_paired_ci.csv',index=False)
    rolls.to_csv(OUT/'option_train_walkforward.csv',index=False)
    features.to_csv(OUT/'option_support_by_phase.csv',index=False)
    receipt={'training_games':291,'validation_games':103,'original_test_games_used':0,
             'previous_forward_games_used':0,'PIT_checks':checks,'http_calls':0,
             'screening_gate_passed':passed,'candidate':'M4_option_value',
             'note':'exploratory because historical validation outcomes were previously examined',
             'seed':SEED,'bootstrap':BOOTS,'features':list(FEATURES)}
    (OUT/'option_development_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('REGISTERED_M4_DEV_ONLY_ABLATION',result.round(6).to_string(index=False))
    print('PAIRED_WHOLE_GROUP_CI',uncertainty.round(6).to_string(index=False))
    print('TRAIN_ONLY_TIME_FOLDS',rolls.round(6).to_string(index=False))
    print('AVAILABILITY',features.round(3).to_string(index=False))
    print('DEV_HYPOTHESIS_SCREEN',json.dumps(receipt,sort_keys=True))

if __name__=='__main__':main()
