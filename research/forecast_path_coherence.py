#!/usr/bin/env python3
"""Exploratory fixed-event martingale diagnostic for saved M1 forecasts.

Reads only two already-consumed forward cohorts. Never fits or selects models.
For games ending before t+5, the terminal target is absorbed at Y.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path('/home/ai-agent/.cache')
PATHS=[
 ('forward1',BASE/'vexil-edge-v2-20261113/forward_baseline_predictions.csv','p_model'),
 ('forward2',BASE/'vexil-edge-v3-20261113/gate_confirmation_predictions.csv','p_m1')
]
OUT=BASE/'vexil-option-novelty-20261113'
TIMES=(10,20,30)
H=5
BOOT=5000
SEED=20261113


def trajectories():
    records=[]
    for cohort,path,pcol in PATHS:
        f=pd.read_csv(path)
        assert f.match_id.nunique()==200
        for mid,g in f.groupby('match_id',sort=True):
            g=g.sort_values('minute'); times=g.minute.to_numpy(int)
            assert np.array_equal(times,np.arange(times[-1]+1))
            y=int(g.radiant_win.iloc[0]);series=int(g.series_id.iloc[0])
            assert g.radiant_win.nunique()==1
            probs=g[pcol].to_numpy(float)
            for t in TIMES:
                if t>times[-1]:continue
                future=t+H
                absorbed=future>times[-1]
                p_next=float(y if absorbed else probs[future])
                p_now=float(probs[t])
                risk=('low' if p_now<.35 else 'mid' if p_now<=.65 else 'high')
                records.append({'cohort':cohort,'match_id':int(mid),
                                'series_group':(cohort+'-s'+str(series) if series>0
                                                else cohort+'-m'+str(mid)),
                                'minute':t,'horizon':H,'p_now':p_now,
                                'p_future_absorbed':p_next,
                                'revision':p_next-p_now,'risk_bin':risk,
                                'finished_within_h':int(absorbed)})
    return pd.DataFrame(records)


def ci(group):
    a=group.groupby('series_group',sort=True).agg(n=('revision','size'),s=('revision','sum'))
    vec=a[['n','s']].to_numpy(float)
    actual=vec[:,1].sum()/vec[:,0].sum()
    rng=np.random.default_rng(SEED)
    indices=rng.integers(0,len(vec),size=(BOOT,len(vec)))
    x=vec[indices].sum(axis=1)
    stats=x[:,1]/x[:,0]
    lo,hi=np.quantile(stats,[.025,.975])
    return {'games':group.match_id.nunique(),'observations':len(group),
            'clusters':len(vec),'absorbed_pct':float(group.finished_within_h.mean()*100),
            'mean_revision':float(actual),'ci_low':float(lo),'ci_high':float(hi)}


def main():
    df=trajectories()
    rows=[]
    for key,g in df.groupby(['cohort','minute']):
        rows.append({'cohort':key[0],'minute':key[1],'risk_bin':'all',**ci(g)})
        for risk,h in g.groupby('risk_bin'):
            if h.match_id.nunique()<20:continue
            rows.append({'cohort':key[0],'minute':key[1],'risk_bin':risk,**ci(h)})
    out=pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT/'martingale_five_minute_revisions.csv',index=False)
    out.to_csv(OUT/'martingale_exploratory_ci.csv',index=False)
    print('EXPLORATORY_FIXED_EVENT_FORECAST_REVISIONS')
    print(out.round(5).to_string(index=False))
    print('LIMITATIONS: NOT a proof of auto-calibration; tested after observing forward cohorts; small and series-dependent samples; terminal absorption uses final results only at game end')
    return out

if __name__=='__main__':main()
