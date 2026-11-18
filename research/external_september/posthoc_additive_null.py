#!/usr/bin/env python3
"""POST-RESULT sensitivity: fixed March TRAIN additive gold+minute comparator.

The September M0-M1 result was already seen; this does not create a blind test,
cannot modify the preregistered gate, and cannot select a winning model.
"""
from __future__ import annotations
import contextlib
import gzip
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from frozen_models import INPUTS,fit_models
from score_locked import exact_feature_functions

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CACHE=Path('/srv/ai/tmp/vexil-september-raw-20261118')

def logloss(y,p):
    p=np.clip(np.asarray(p,float),1e-12,1-1e-12)
    y=np.asarray(y,int)
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def bootstrap(delta, groups, nboot=5000):
    table=pd.DataFrame({'d':delta,'grp':groups})
    agg=np.array([(len(x),x.d.sum()) for _,x in table.groupby('grp',sort=True)])
    rng=np.random.default_rng(20261118)
    out=np.empty(nboot)
    for i in range(nboot):
        sample=agg[rng.integers(len(agg),size=len(agg))]
        out[i]=sample[:,1].sum()/sample[:,0].sum()
    return np.quantile(out,[.025,.975]).tolist()

def main():
    original=pd.read_csv(ROOT/'research/frozen_original_train_features.csv.gz')
    cols=['gold_k','minute10']
    model=Pipeline([
        ('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
        ('scale',StandardScaler()),
        ('logistic',LogisticRegression(C=1.,max_iter=1000,random_state=20261113)),
    ])
    model.fit(original[cols],original.radiant_win)
    check=fit_models()
    original_predictions=pd.read_csv(HERE/'external_september_predictions.csv')
    selected=json.loads((HERE/'selected_metadata.json').read_text())
    selected_ids=set(original_predictions.match_id.unique())
    make=exact_feature_functions()
    parts=[]
    with contextlib.redirect_stdout(io.StringIO()):
        for item in selected['matches']:
            mid=item['match_id']
            if mid not in selected_ids:continue
            with gzip.open(CACHE/f'{mid}.json.gz','rt') as f:raw=json.load(f)
            d=make([raw])
            parts.append(d[['match_id','minute','gold_k','minute10','gold_x_time']])
    fresh=pd.concat(parts,ignore_index=True)
    joined=original_predictions.merge(fresh,on=['match_id','minute'],how='left',validate='one_to_one',indicator=True)
    assert len(joined)==8740 and joined._merge.eq('both').all()
    for name in ('M0','M1'):
        m=check[name]
        p=m.predict_proba(joined[INPUTS[name]])[:,1]
        original_p=joined['p_'+name.lower()].to_numpy()
        assert np.max(np.abs(p-original_p))<1e-10
    add=model.predict_proba(joined[cols])[:,1]
    y=joined.radiant_win.to_numpy()
    ll_add=logloss(y,add)
    ll_m1=logloss(y,joined.p_m1)
    ll_m0=logloss(y,joined.p_m0)
    d=ll_m1-ll_add
    result={
      'scope':'POST-HOC strong-null sensitivity, after original March TEST and September M0-M1 result were viewed; no model promotion',
      'fit_source':'original March 291 TRAIN games only; logistic C=1, gold_k + minute10; fixed 20261113 seed',
      'sept_match_count':int(joined.match_id.nunique()),
      'minute_rows':len(joined),
      'additive_gold_time_logloss':float(ll_add.mean()),
      'm0_gold_only_logloss':float(ll_m0.mean()),
      'm1_gold_time_interaction_logloss':float(ll_m1.mean()),
      'm1_minus_additive_ll':float(d.mean()),
      'm1_minus_additive_group_ci95':bootstrap(d,joined.series_group),
      'additive_minus_m0_ll':float((ll_add-ll_m0).mean()),
      'additive_m1_brier':{
        'additive':float(np.mean((add-y)**2)),
        'm1':float(np.mean((joined.p_m1-y)**2)),
      },
      'm1_minus_additive_by_league':{
        str(int(lid)):float(np.mean(d[joined.league_id.to_numpy()==lid]))
        for lid in sorted(joined.league_id.unique())
      },
      'parity_of_m0_m1_against_saved_predictions':'max_abs < 1e-10',
    }
    path=HERE/'posthoc_additive_null_receipt.json'
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('POSTHOC_ADDITIVE',json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
