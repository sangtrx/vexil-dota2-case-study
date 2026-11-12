#!/usr/bin/env python3
"""Independent recomputation from saved predictions, no models fitted."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/results'
EPS=1e-15

def main():
    scores=pd.read_csv(OUT/'all_28_candidate_scores.csv')
    val=pd.read_csv(OUT/'dev_validation_predictions_28.csv')
    folds=pd.read_csv(OUT/'train_only_3fold_scores.csv')
    phases=pd.read_csv(OUT/'calibration_and_phase_scores.csv')
    receipt=json.loads((OUT/'screen_receipt.json').read_text())
    lock=json.loads((OUT/'screen_consumed.lock.json').read_text())
    assert receipt['source_git_head']==lock['source_git_head']
    assert val.match_id.nunique()==103 and len(val)==3784
    assert scores.model.nunique()==29 and len(scores)==29
    assert len(folds)==87 and len(phases)==145
    assert val[['match_id','minute']].duplicated().sum()==0
    assert val.partition.eq('validation').all()
    assert val.groupby('match_id')['radiant_win'].nunique().eq(1).all()
    assert scores.model.str.startswith('P').sum()==28
    y=val.radiant_win.to_numpy(int)
    losses={}
    for row in scores.to_dict('records'):
        p=val['p_'+row['model']].to_numpy(dtype=float)
        assert np.isfinite(p).all() and np.all((p>=0)&(p<=1))
        q=np.clip(p,EPS,1-EPS)
        loss=-(y*np.log(q)+(1-y)*np.log1p(-q))
        brier=(p-y)**2
        losses[row['model']]=loss
        assert abs(loss.mean()-row['logloss'])<1e-12,(row['model'],'logloss')
        assert abs(brier.mean()-row['brier'])<1e-12,(row['model'],'brier')
    m1=losses['M1_time_value']
    for row in scores.to_dict('records'):
        delta=float(np.mean(losses[row['model']]-m1))
        assert abs(delta-row['delta_ll_vs_M1'])<1e-12,row['model']
    phase=np.select([val.minute<=9,val.minute<=19,val.minute<=29],
                    ['0-9','10-19','20-29'],default='30+')
    for row in phases.to_dict('records'):
        mask=np.ones(len(val),dtype=bool) if row['phase']=='overall' else phase==row['phase']
        assert mask.sum()==row['rows'] and val.loc[mask,'match_id'].nunique()==row['matches']
        assert abs(losses[row['model']][mask].mean()-row['logloss'])<1e-12,row['model']
    assert not scores.passes_exploratory_screen.any()
    assert receipt['num_passed']==0
    assert receipt['candidate_count']==28
    assert receipt['original_test_games_accessed']==0
    assert receipt['first_forward_test_games_accessed']==0
    assert receipt['second_forward_test_games_accessed']==0
    print('INDEPENDENT_FACTORY_AUDIT_PASS',
          json.dumps({'models':len(scores),'validation_rows':len(val),
            'phase_rows':len(phases),'fold_rows':len(folds),
            'candidate_passes':0,'top_point_model':scores.loc[scores.model!='M1_time_value'].sort_values('logloss').iloc[0].model,
            'source_head':receipt['source_git_head']},sort_keys=True))
    return

if __name__=='__main__':main()
