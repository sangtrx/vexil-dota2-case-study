"""Simple, practical frozen-M1 inference and monotonicity/latency audit.

Train-only source; never queries an OpenDota endpoint or scores test labels.
No HTTP or live-feed speed claims. Operational benchmark is CPU snapshot
extraction + preprocessing + prediction, with everything cached in memory.
"""
from __future__ import annotations
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
import pandas as pd

from research.robustness_study import build_data, CACHE, OUT

def predict_at_minute(model, game, t, ns, columns):
    if type(t) is not int or t<0:
        raise ValueError('minute must be a nonnegative int')
    # The model is NOT allowed to inspect radiant_win/end-match totals.
    # Feature extraction uses current and older match-clock data only.
    x=ns['snapshot_features'](game,t)
    features=pd.DataFrame([{k:x[k] for k in columns}],columns=columns)
    prob=float(model.predict_proba(features)[0,1])
    assert 0<=prob<=1 and math.isfinite(prob)
    return dict(match_id=int(game['match_id']),minute=t,
                model='M1_time_value',
                p_radiant_win=prob,
                timing_basis='parsed retrospective game clock; not a live receipt',
                live_feed_availability_verified=False)

def monotonic_audit(model,minutes):
    imputer=model.named_steps['imputer']
    scaler=model.named_steps['scale']
    logistic=model.named_steps['logistic']
    indices={'gold_k':0,'minute10':1,'gold_x_time':2}
    coef=np.asarray(logistic.coef_)[0]
    # Standardized logistic slope wrt gold_k at fixed minute
    slope_gold=float(coef[indices['gold_k']]/scaler.scale_[indices['gold_k']])
    slope_interact=float(coef[indices['gold_x_time']]/scaler.scale_[indices['gold_x_time']])
    rows=[]
    for t in range(minutes+1):
        derivative=slope_gold+slope_interact*math.log1p(t/10)
        rows.append(dict(minute=t,log_odds_slope_per_1000_gold=derivative,
                         monotone_gold_positive=derivative>0))
    table=pd.DataFrame(rows)
    return table,dict(coef_gold=slope_gold,coef_gold_x_logtime=slope_interact,
                      p_at_zero_gold_minute0=float(model.predict_proba(
                           pd.DataFrame([dict(gold_k=0,minute10=0,gold_x_time=0)]))[0,1]),
                      observed_maximum_minute=minutes,
                      minutes_with_nonpositive_gold_slope=int(
                           (table.log_odds_slope_per_1000_gold<=0).sum()))

def main():
    ns,m,data=build_data()
    columns=list(ns['SETS']['M1_time_value'])
    assert columns==['gold_k','minute10','gold_x_time']
    model=ns['fit_model'](data,columns)
    maxminute=int(data.minute.max())
    slopes,info=monotonic_audit(model,maxminute)
    # Reference parity: single-snapshot and batched source must produce
    # identical predictions. Only training games are used.
    api=ns['OpenDota'](cache_dir=CACHE/'api-cache')
    ids=sorted(set(data.match_id))[:60]
    games=[api.get('/matches/'+str(int(mid))) for mid in ids]
    assert api.calls==0
    cases=[]
    for game in games:
        for t in (0,1,10,20, min(30,int(game['duration'])//60)):
            if t>int(game['duration'])//60:continue
            cases.append((game,t))
    assert len(cases)>=200
    golden=[]
    for game,t in cases:
        one=predict_at_minute(model,game,t,ns,columns)
        row=data[(data.match_id==one['match_id']) & (data.minute==t)]
        assert len(row)==1
        from_table=float(model.predict_proba(row[columns])[0,1])
        assert abs(from_table-one['p_radiant_win'])<1e-13
        if t in (0,10,20):
            # Predicted outcome must be immune to winner and later
            # data; preserve IDs but poison end-match data and future.
            adversarial=ns['prefix_truncated'](game,t)
            same=predict_at_minute(model,adversarial,t,ns,columns)
            assert abs(same['p_radiant_win']-one['p_radiant_win'])<1e-13
        golden.append(one)
    rng=np.random.default_rng(13112026)
    idx=rng.integers(0,len(cases),size=1200)
    durations=[]
    for i in idx[:50]:
        game,t=cases[int(i)]
        predict_at_minute(model,game,t,ns,columns)
    for i in idx:
        game,t=cases[int(i)]
        start=time.perf_counter_ns()
        predict_at_minute(model,game,t,ns,columns)
        durations.append((time.perf_counter_ns()-start)/1e6)
    ms=np.asarray(durations)
    assert np.isfinite(ms).all() and np.min(ms)>0
    # This SHA is for deterministic primitive PIT snapshots on a
    # sampled TRAIN-only operational panel, not raw OpenDota parity.
    pred_rows=[(int(x['match_id']),int(x['minute']),
                format(x['p_radiant_win'],'.12g')) for x in golden]
    panel_sha=hashlib.sha256(json.dumps(pred_rows,separators=(',',':')).encode()).hexdigest()
    report=dict(allowed_endpoint_calls=0,existing_train_games=291,
         original_validation_games_scored=0,original_heldout_games_scored=0,
         parity_snapshots=len(cases),source_poisoning_checks=sum(
            1 for g,t in cases if t in (0,10,20)),
         model='M1_time_value',cpu='BigLinux epic',
         benchmark_iteration_count=len(ms),
         benchmark_excludes='API fetch, IPC, network/HTTP, system cold-start',
         benchmark_includes='Python snapshot + Pandas one-row + scikit-learn pipeline',
         p50_ms=float(np.quantile(ms,.5)),p95_ms=float(np.quantile(ms,.95)),
         p99_ms=float(np.quantile(ms,.99)),max_ms=float(ms.max()),
         deterministic_train_panel_sha256=panel_sha,
         **info)
    OUT.mkdir(parents=True,exist_ok=True)
    slopes.to_csv(OUT/'m1_gold_monotonicity_by_minute.csv',index=False)
    (OUT/'m1_operational_contract_receipt.json').write_text(
          json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('OPERATIONAL_LATENCY_AND_GOLD_MONOTONICITY',json.dumps(report,sort_keys=True),flush=True)
    print('GOLD_SLOPE_TAIL',slopes.iloc[[0,10,20,30,40,50,-1]].round(7).to_json(orient='records'),flush=True)

if __name__=='__main__':main()
