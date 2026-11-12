#!/usr/bin/env python3
"""Run the 28 preregistered hypotheses once on previously inspected dev games.

Absolutely NO original 106-test or forward 200+200 match is loaded or scored.
This is exploratory, not fresh blinded evidence.

Every hyperparameter, feature, fold boundary, multiple-test family and
advancement criterion is fixed before the first reported model score.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from tests.test_notebook_contracts import load_definitions
from research.proposal_factory_features import (
    HERO_COLUMNS, build_match_events, make_snapshot, prefix_poison
)
from research.proposal_factory_registry import (
    BASE, SPECS, SEED, PRACTICAL_IMPROVEMENT, BOOTSTRAP_REPS
)

N=load_definitions()
BASE_CACHE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
OUT=Path('/home/ai-agent/.cache/vexil-proposal-factory-20261113')
EXPECTED_MODELS=28
EPS=1e-15

def source_check():
    manifest=json.loads((ROOT/'research/proposal_registry_manifest.json').read_text())
    sources={
        'registry_sha256':ROOT/'research/proposal_factory_registry.py',
        'feature_source_sha256':ROOT/'research/proposal_factory_features.py',
    }
    assert manifest['proposal_count']==len(SPECS)==EXPECTED_MODELS
    for key,src in sources.items():
        assert manifest[key]==hashlib.sha256(src.read_bytes()).hexdigest(),(key,src)
    assert BOOTSTRAP_REPS==5000 and PRACTICAL_IMPROVEMENT==.005
    return manifest

def pct_logloss(y,p):
    v=np.clip(p,EPS,1-EPS)
    return -(y*np.log(v)+(1-y)*np.log1p(-v))

def fit_fixed(frame, cols, family):
    if family=='hero_ridge':
        c=.03
    elif family=='strong_ridge':
        c=.2
    elif family=='spline':
        c=.4
    else:
        c=1.
    if family in ('tree_base','tree_macro'):
        model=Pipeline([
            ('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
            ('gbdt',HistGradientBoostingClassifier(
                learning_rate=.05,max_iter=80,max_depth=2,
                min_samples_leaf=90,l2_regularization=20.,
                early_stopping=False,random_state=SEED,
            ))
        ])
    elif family=='spline':
        # ColumnTransformer receives numpy AFTER imputation, so use numeric indices.
        model=Pipeline([
            ('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
            ('shape',ColumnTransformer([
                ('spline',SplineTransformer(n_knots=5,degree=2,include_bias=False),
                 [0,1]),
                ('linear','passthrough',[2])
            ],remainder='drop')),
            ('scale',StandardScaler()),
            ('logit',LogisticRegression(C=c,max_iter=1400,random_state=SEED))
        ])
    else:
        model=Pipeline([
            ('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
            ('scale',StandardScaler()),
            ('logit',LogisticRegression(C=c,max_iter=1400,random_state=SEED))
        ])
    model.fit(frame[list(cols)],frame['radiant_win'].to_numpy(dtype=int))
    return model

def cols_for(spec):
    ident,_,_,extra,_,_,algorithm=spec
    if algorithm=='hero_ridge':
        return tuple(BASE)+HERO_COLUMNS
    return tuple(BASE)+tuple(extra)

def all_specs():
    return [('M1_time_value','baseline','Gold×Time',tuple(),
             'baseline','all gains must beat this','logistic')]+SPECS

def cache_path_for(mid):
    # Exact existing OpenDota cache key, matching the two-API notebook client.
    key=hashlib.sha256(json.dumps(
        ['/matches/'+str(int(mid)),{}],sort_keys=True
    ).encode()).hexdigest()
    return BASE_CACHE/'api-cache'/(key+'.json.gz')

def load_dev_features():
    meta_all=pd.read_csv(BASE_CACHE/'vexil_takehome_outputs/match_manifest.csv')
    assert len(meta_all)==500 and meta_all.match_id.nunique()==500
    kept=meta_all.loc[meta_all.partition.isin(('train','validation'))].copy()
    assert kept.partition.value_counts().to_dict()=={'train':291,'validation':103}
    assert kept.match_id.nunique()==394
    assert not kept[['match_id','partition']].duplicated().any().any()
    # Assert full source exists before instantiating a network-capable client.
    for mid in kept.match_id:
        assert cache_path_for(mid).is_file(),f'No frozen cache for {mid}'
    api=N['OpenDota'](cache_dir=BASE_CACHE/'api-cache')
    games=[api.get('/matches/'+str(int(mid))) for mid in kept.match_id]
    assert api.calls==0
    records=[]
    checks=0
    from math import isfinite
    checkpoints=[0,1,9,10,11,15,19,20,25,30]
    for i,game in enumerate(games,1):
        mid=int(game['match_id'])
        observed=build_match_events(game)
        assert all(observed[key] for key in
                   ('obj_ok','kills_ok','buyback_ok','purchases_ok','players_ok')),(mid,'incomplete parser')
        duration=int(game['duration'])
        for t in range(duration//60+1):
            feat=make_snapshot(game,t,N['snapshot_features'],observed)
            records.append({'match_id':mid,'minute':t,
                            'radiant_win':int(game['radiant_win']),**feat})
        for t in sorted(set([x for x in checkpoints if x<=duration//60]+[duration//60])):
            feat=make_snapshot(game,t,N['snapshot_features'],observed)
            poisoned=prefix_poison(game,t)
            check=make_snapshot(poisoned,t,N['snapshot_features'])
            assert feat.keys()==check.keys(),(mid,t,'feature-set-drift')
            for key in feat:
                aa,bb=feat[key],check[key]
                if pd.isna(aa):
                    assert pd.isna(bb),(mid,t,key,'NAN poisoning')
                else:
                    assert math.isclose(aa,bb,rel_tol=0.,abs_tol=1e-10),(
                        mid,t,key,aa,bb)
            checks+=1
        if i%100==0:print('FEATURE_BUILDER_GAMES',i,
                         'ROWS',len(records),'PIT_ASSERTIONS',checks,flush=True)
    table=pd.DataFrame(records).merge(
        kept[['match_id','partition','start_time','series_id','patch']],
        on='match_id',validate='many_to_one')
    assert len(table.match_id.unique())==394
    assert all(not np.isinf(table[k]).any() for k in table.select_dtypes(include='number').columns)
    assert api.calls==0
    return kept,table,checks

def safe_cutpoints(train_info):
    m=train_info.sort_values(['start_time','match_id']).reset_index(drop=True)
    spans={}
    for i,(sid,mid) in enumerate(zip(m.series_id,m.match_id)):
        key=('s',int(sid)) if int(sid)>0 else ('m',int(mid))
        if key not in spans:spans[key]=[i,i]
        else:spans[key][1]=i
    good=[cut for cut in range(1,len(m))
          if all(not(a<cut<=b) for a,b in spans.values())]
    # Four deterministic nearest series-safe cutpoints, -> three folds.
    points=[min(good,key=lambda c:(abs(c-len(m)*frac),c))
            for frac in (.52,.60,.75,.92)]
    assert len(set(points))==4 and points==sorted(points),points
    return m,points

def fit_and_score(frame,train_ids,eval_ids,specs):
    train=frame.loc[frame.match_id.isin(train_ids)]
    val=frame.loc[frame.match_id.isin(eval_ids)]
    assert train.match_id.nunique()==len(train_ids)
    assert val.match_id.nunique()==len(eval_ids)
    assert not set(train.match_id)&set(val.match_id)
    y=val.radiant_win.to_numpy(dtype=int)
    probs={}
    for j,spec in enumerate(specs):
        name=spec[0]
        cols=cols_for(spec)
        model=fit_fixed(train,cols,spec[-1])
        pred=model.predict_proba(val[list(cols)])[:,1]
        assert len(pred)==len(val) and np.isfinite(pred).all()
        assert np.all((pred>=0)&(pred<=1))
        probs[name]=pred
    return val,probs

def score_summary(frame,probs):
    y=frame.radiant_win.to_numpy(dtype=int)
    base_loss=pct_logloss(y,probs['M1_time_value'])
    base_br=(probs['M1_time_value']-y)**2
    out=[]
    for s in all_specs():
        name=s[0]
        pred=probs[name]
        loss=pct_logloss(y,pred)
        br=(pred-y)**2
        per_match=(pd.DataFrame({
            'match_id':frame.match_id.to_numpy(),
            'difference':loss-base_loss
        }).groupby('match_id',sort=True)['difference'].mean().mean())
        out.append({
            'model':name,'family':s[1],'title':s[2],
            'algorithm':s[-1],'new_features':len(s[3]),
            'column_count':len(cols_for(s)),
            'minute_rows':len(frame),'matches':frame.match_id.nunique(),
            'logloss':float(loss.mean()),'brier':float(br.mean()),
            'delta_ll_vs_M1':float((loss-base_loss).mean()),
            'delta_brier_vs_M1':float((br-base_br).mean()),
            'equal_match_mean_delta_ll':float(per_match),
        })
    return pd.DataFrame(out)

def time_folds(manifest):
    m,points=safe_cutpoints(manifest[manifest.partition=='train'])
    for f,(a,b) in enumerate(zip(points[:-1],points[1:]),1):
        older=set(m.iloc[:a].match_id.astype(int))
        later=set(m.iloc[a:b].match_id.astype(int))
        assert older and later and not older&later
        print('TRAIN_ONLY_FOLD',f,'train',len(older),'eval',len(later),'cut',a,b,flush=True)
        yield f,older,later

def familywise_bootstrap(eval_frame,probs):
    names=[s[0] for s in SPECS]
    y=eval_frame.radiant_win.to_numpy(dtype=int)
    groups=[
        ('s',int(s)) if int(s)>0 else ('m',int(mid))
        for s,mid in zip(eval_frame.series_id,eval_frame.match_id)
    ]
    group_index,keys=pd.factorize(pd.Series(groups,dtype='object'),sort=True)
    ngrp=len(keys)
    assert ngrp>30 and ngrp<=eval_frame.match_id.nunique()
    nvec=np.bincount(group_index,minlength=ngrp).astype(float)
    main_loss=pct_logloss(y,probs['M1_time_value'])
    diffs=np.column_stack([
        pct_logloss(y,probs[name])-main_loss
        for name in names
    ])
    sum_by_group=np.vstack([
        np.bincount(group_index,weights=diffs[:,j],minlength=ngrp)
        for j in range(len(names))
    ]).T
    assert sum_by_group.shape==(ngrp,len(names))
    observed=sum_by_group.sum(axis=0)/nvec.sum()
    rng=np.random.default_rng(SEED)
    indices=rng.integers(0,ngrp,size=(BOOTSTRAP_REPS,ngrp))
    rep_sums=sum_by_group[indices].sum(axis=1)
    rep_ns=nvec[indices].sum(axis=1)
    boot=rep_sums/rep_ns[:,None]
    std=boot.std(axis=0,ddof=1)
    assert all(std>1e-12)
    max_t=np.max(np.abs((boot-observed[None,:])/std[None,:]),axis=1)
    multiplier=float(np.quantile(max_t,.95))
    rows=[]
    for j,name in enumerate(names):
        lo,hi=np.quantile(boot[:,j],[.025,.975])
        rows.append({
            'model':name,'series_or_singleton_clusters':ngrp,
            'series_grouped_delta_ll':float(observed[j]),
            'paired_percentile95_low':float(lo),
            'paired_percentile95_high':float(hi),
            'maxT_familywise95_low':float(observed[j]-multiplier*std[j]),
            'maxT_familywise95_high':float(observed[j]+multiplier*std[j]),
            'simultaneous_multiplier':multiplier,
            'bootstrap_reps':BOOTSTRAP_REPS,'seed':SEED,
        })
    return pd.DataFrame(rows)

def reliability(frame,probs):
    y=frame.radiant_win.to_numpy(dtype=int)
    phase=np.select([frame.minute<=9,frame.minute<=19,frame.minute<=29],
                    ['0-9','10-19','20-29'],default='30+')
    rows=[]
    for name,pred in probs.items():
        for label in ('overall','0-9','10-19','20-29','30+'):
            mask=np.ones(len(frame),dtype=bool) if label=='overall' else phase==label
            if not mask.any():continue
            p=pred[mask]
            target=y[mask]
            bins=np.clip(np.floor(p*10).astype(int),0,9)
            ece=0.
            for bi in range(10):
                hit=bins==bi
                if not hit.any():continue
                ece+=hit.sum()/len(p)*abs(np.mean(p[hit])-np.mean(target[hit]))
            rows.append({'model':name,'phase':label,'matches':int(frame.loc[mask,'match_id'].nunique()),
                         'rows':int(mask.sum()),
                         'logloss':float(pct_logloss(target,p).mean()),
                         'brier':float(np.mean((p-target)**2)),
                         'ece10_descriptive':ece})
    return pd.DataFrame(rows)

def main():
    registration=source_check()
    import subprocess
    githead=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    gitdirty=subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True)
    assert not gitdirty,"Commit and freeze evaluator before running"
    OUT.mkdir(parents=True,exist_ok=True)
    lock=OUT/'screen_consumed.lock.json'
    receipt=OUT/'screen_receipt.json'
    if lock.exists() or receipt.exists():
        raise RuntimeError("Previous screen consumed. No adaptive rerun permitted.")
    manifest,features,pit_checks=load_dev_features()
    # Lock one-shot screening after fully verified and built feature data, before fitting.
    lock.write_text(json.dumps({
        'source_git_head':githead,
        'registry_sha256':registration['registry_sha256'],
        'feature_sha256':registration['feature_source_sha256'],
        'stage':'original previously-inspected dev only',
        'num_fixed_proposals':len(SPECS),
    },sort_keys=True,indent=2)+'\n')
    print('ONE_SHOT_RESEARCH_SCREEN_LOCKED',githead,'PIT_checks',pit_checks,flush=True)
    specs=all_specs()
    folds=[]
    for fold,older,later in time_folds(manifest):
        frame,preds=fit_and_score(features,older,later,specs)
        summaries=score_summary(frame,preds)
        summaries['fold']=fold
        summaries['train_games']=len(older)
        summaries['val_games']=len(later)
        folds.extend(summaries.to_dict('records'))
        print('COMPLETED_TRAIN_ONLY_FOLD',fold,flush=True)
    fold_table=pd.DataFrame(folds)
    trainids=set(manifest.loc[manifest.partition=='train','match_id'].astype(int))
    validids=set(manifest.loc[manifest.partition=='validation','match_id'].astype(int))
    val,preds=fit_and_score(features,trainids,validids,specs)
    score_table=score_summary(val,preds)
    corrected=familywise_bootstrap(val,preds)
    calibration=reliability(val,preds)
    score_table=score_table.merge(corrected,on='model',how='left',validate='one_to_one')
    directions=fold_table.groupby('model')['delta_ll_vs_M1'].agg(
        favorable_train_folds=lambda x:int((x<0).sum()),
        folds=lambda x:len(x)
    ).reset_index()
    score_table=score_table.merge(directions,on='model',validate='one_to_one')
    score_table['passes_exploratory_screen']=(
        (score_table.model!='M1_time_value') &
        (score_table.delta_ll_vs_M1<=-PRACTICAL_IMPROVEMENT) &
        (score_table.delta_brier_vs_M1<=0) &
        (score_table.favorable_train_folds>=2) &
        (score_table.maxT_familywise95_high<0)
    )
    eligible=score_table.loc[score_table.passes_exploratory_screen]
    if len(eligible):
        ranked=eligible.sort_values(['delta_ll_vs_M1','column_count','model'],kind='mergesort')
        selected=str(ranked.iloc[0]['model'])
    else:
        selected=None
    columns=['match_id','minute','series_id','partition','radiant_win']
    p_frame=val[columns].copy().reset_index(drop=True)
    for name,pred in preds.items():
        p_frame['p_'+name]=pred
    result_dir=OUT
    p_frame.to_csv(result_dir/'dev_validation_predictions_28.csv',index=False)
    score_table.sort_values('logloss').to_csv(result_dir/'all_28_candidate_scores.csv',index=False)
    fold_table.to_csv(result_dir/'train_only_3fold_scores.csv',index=False)
    corrected.to_csv(result_dir/'familywise_simultaneous_ci.csv',index=False)
    calibration.to_csv(result_dir/'calibration_and_phase_scores.csv',index=False)
    receipt_payload={
        'validation_labels_already_seen_in_prior_work':True,
        'independent_holdout_reused':False,
        'original_test_games_accessed':0,
        'first_forward_test_games_accessed':0,
        'second_forward_test_games_accessed':0,
        'source_git_head':githead,
        'registry_sha256':registration['registry_sha256'],
        'feature_sha256':registration['feature_source_sha256'],
        'train_games':291,'validation_games':103,
        'candidate_count':len(SPECS),'fold_count':3,
        'pit_checks':pit_checks,
        'series_clusters':int(corrected.series_or_singleton_clusters.iloc[0]),
        'familywise_bootstrap':BOOTSTRAP_REPS,
        'practical_absolute_improvement_required':PRACTICAL_IMPROVEMENT,
        'selected_for_fresh_confirmation':selected,
        'num_passed':len(eligible),
        'comment':'Registration and original source frozen. Dev screen exploratory only. No blind-test scores examined for 28 new candidates.',
    }
    receipt.write_text(json.dumps(receipt_payload,indent=2,sort_keys=True)+'\n')
    print('ALL_28_SCORED',score_table[['model','logloss','brier','delta_ll_vs_M1',
         'favorable_train_folds','maxT_familywise95_high',
         'passes_exploratory_screen']].sort_values('logloss').to_string(
             index=False,float_format=lambda x:f'{x:.6f}'))
    print('PROPOSAL_FACTORY_COMPLETE',json.dumps(receipt_payload,sort_keys=True),flush=True)

if __name__=='__main__':main()
