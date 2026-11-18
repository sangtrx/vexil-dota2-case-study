import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
STUDY=ROOT/'research/external_september'
OUT=json.loads((STUDY/'external_september_scores.json').read_text())
META=json.loads((STUDY/'selected_metadata.json').read_text())
P=pd.read_csv(STUDY/'external_september_predictions.csv')
def check(ok,msg):
    if not ok:raise AssertionError(msg)
    print('PASS',msg)

sel=set(int(x['match_id']) for x in META['matches'])
excluded=set(int(x['match_id']) for x in OUT['rejections'])
included=set(int(x) for x in P.match_id.unique())
check(sel == excluded|included and not (excluded&included),'COMPLETE_PRECOMMITTED_200_DENOMINATOR')
check(len(included)==OUT['usable_count'],'USABLE_COUNT_EXACT')
check(len(excluded)==OUT['missing_or_invalid_count'],'FAILURES_EXACT')
check(int(P.shape[0])==OUT['minute_rows'],'MINUTE_ROW_COUNT')
check(P.groupby('match_id').radiant_win.nunique().max()==1,'CONSTANT_MATCH_LABEL')
lookup={int(x['match_id']):int(x['duration']) for x in META['matches']}
check(all(60*int(row.minute)<lookup[int(row.match_id)] for row in P.itertuples()),
      'STRICT_PRE_TERMINAL_MINUTES')
check(P[['p_m0','p_m1']].ge(0).all().all() and
      P[['p_m0','p_m1']].le(1).all().all(),'BOUNDED_PREDICTIONS')
y=P.radiant_win.to_numpy()
for label in ('m0','m1'):
    p=P['p_'+label].to_numpy()
    ll=-y*np.log(np.clip(p,1e-12,1-1e-12))-(1-y)*np.log1p(-np.clip(p,1e-12,1-1e-12))
    brier=(p-y)**2
    check(abs(ll.mean()-OUT['primary_logloss'][label])<1e-10,'RECOMPUTED_LOG_LOSS_'+label)
    check(abs(brier.mean()-OUT['brier'][label])<1e-10,'RECOMPUTED_BRIER_'+label)
    P['ll_'+label]=ll
    P['brier_'+label]=brier
delta=P.ll_m1.mean()-P.ll_m0.mean()
check(abs(delta-OUT['primary_logloss']['m1_minus_m0'])<1e-10,'RECOMPUTED_LL_DELTA')
groups=np.array([(len(g),(g.ll_m1-g.ll_m0).sum())
    for _,g in P.groupby('series_group',sort=True)],dtype=float)
rng=np.random.default_rng(20261118)
arr=np.empty(5000)
for i in range(5000):
    a=groups[rng.integers(0,len(groups),size=len(groups))]
    arr[i]=a[:,1].sum()/a[:,0].sum()
ci=np.quantile(arr,[.025,.975])
check(np.max(np.abs(ci-OUT['primary_logloss']['paired_group_bootstrap_95_ci']))<1e-10,
      'INDEPENDENT_SERIES_BOOTSTRAP_RECALC')
assert len(groups)==OUT['series_or_singleton_groups']
late=P[P.minute>=30]
late_delta=(late.brier_m1-late.brier_m0).mean() if len(late) else None
target=(len(included)>=150 and len(groups)>=40 and -delta>=0.005 and
        ci[1]<0 and late_delta is not None and late_delta<=0.002)
check(('PASS' if target else 'FAIL')==OUT['frozen_external_support_gate'],
      'LOCKED_PROMOTION_GATE_RECALCULATED')
check(META['selected_metadata_sha256']==OUT['selection_sha256'],
      'FROZEN_COHORT_SHA')
check(hashlib.sha256((STUDY/'external_september_predictions.csv').read_bytes()).hexdigest()
    ==OUT['scored_predictions_sha256'],'SAVED_FORECASTS_SHA')
print('VERDICT',json.dumps({'delta_ll':delta,'ci':ci.tolist(),
    'usable':len(included),'groups':len(groups),
    'gate':OUT['frozen_external_support_gate']},sort_keys=True))
