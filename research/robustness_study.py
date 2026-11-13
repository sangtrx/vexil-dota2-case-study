"""Time-embargoed, series-safe rolling-origin research on TRAIN games only."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('/home/ai-agent/.cache/vexil-real-data-20261113')
OUT=ROOT/'research/results'
FRACTIONS=(.53,.62,.75,.84,.92,1.)

def defs():
    sys.path.insert(0,str(ROOT))
    from tests.test_notebook_contracts import load_definitions
    return load_definitions()

def series_key(row):
    sid=int(row.series_id)
    return ('s',sid) if sid>0 else ('m',int(row.match_id))

def make_folds(manifest):
    manifest=manifest.sort_values(['start_time','match_id']).reset_index(drop=True)
    assert len(manifest)==291 and manifest.partition.eq('train').all()
    spans={}
    for i,row in enumerate(manifest.itertuples()):
        key=series_key(row)
        if key not in spans:spans[key]=[i,i]
        else:spans[key][1]=i
    valid=[i for i in range(1,len(manifest))
           if not any(lo<i<=hi for lo,hi in spans.values())]
    cuts=[min(valid,key=lambda i:(abs(i-frac*len(manifest)),i))
          if frac<1 else len(manifest) for frac in FRACTIONS]
    assert cuts==sorted(set(cuts)),cuts
    folds=[]
    for idx,(left,right) in enumerate(zip(cuts[:-1],cuts[1:]),1):
        later=manifest.iloc[left:right].copy()
        earlier=manifest.iloc[:left].copy()
        first=int(later.start_time.min())
        incomplete_keys={series_key(row) for row in earlier.itertuples()
                         if row.start_time+row.duration>first}
        okay=earlier[(earlier.start_time+earlier.duration)<=first].copy()
        okay=okay.loc[~okay.apply(series_key,axis=1).isin(incomplete_keys)]
        trkeys={series_key(row) for row in okay.itertuples()}
        vakeys={series_key(row) for row in later.itertuples()}
        assert not trkeys&vakeys
        assert okay.start_time.max()<first
        assert (okay.start_time+okay.duration<=first).all()
        assert okay.match_id.nunique()>=55 and later.match_id.nunique()>=15
        folds.append(dict(fold=idx,
            train_ids=frozenset(okay.match_id.astype(int)),
            eval_ids=frozenset(later.match_id.astype(int)),
            eval_first_start=first,
            train_games=len(okay), eval_games=len(later),
            embargo_games=len(earlier)-len(okay),
            train_series=len(trkeys),eval_series=len(vakeys)))
    return folds

def build_data():
    ns=defs()
    manifest=pd.read_csv(CACHE/'vexil_takehome_outputs/match_manifest.csv')
    manifest=manifest.loc[manifest.partition=='train'].copy()
    assert manifest.match_id.nunique()==291
    api=ns['OpenDota'](cache_dir=CACHE/'api-cache')
    games=[api.get('/matches/'+str(int(mid))) for mid in manifest.match_id]
    assert api.calls==0
    durations={int(g['match_id']):int(g['duration']) for g in games}
    manifest['duration']=manifest.match_id.map(durations)
    rows=[]
    for game in games:
        mid=int(game['match_id'])
        for t in range(int(game['duration'])//60+1):
            f=ns['snapshot_features'](game,t)
            item=ns['item_purchase_snapshot'](game,t)
            rows.append(dict(match_id=mid,minute=t,
                             radiant_win=int(game['radiant_win']),**f,
                             major_item_diff=item[0],
                             blink_bkb_diff=item[1]))
    data=pd.DataFrame(rows)
    assert data.match_id.nunique()==291 and len(data)==10683
    assert data[['major_item_diff','blink_bkb_diff']].notna().all().all()
    return ns,manifest,data

def scores(y,p,ids):
    p=np.clip(np.asarray(p,dtype=float),1e-15,1-1e-15)
    y=np.asarray(y,dtype=int)
    z=pd.DataFrame(dict(match_id=ids,
                        logloss=-(y*np.log(p)+(1-y)*np.log1p(-p)),
                        brier=(p-y)**2))
    by=z.groupby('match_id')[['logloss','brier']].mean()
    return dict(minute_logloss=float(z.logloss.mean()),
                minute_brier=float(z.brier.mean()),
                equal_match_logloss=float(by.logloss.mean()),
                equal_match_brier=float(by.brier.mean()))

def main():
    ns,manifest,data=build_data()
    folds=make_folds(manifest)
    models={k:list(v) for k,v in ns['SETS'].items()}
    models['P20_item_purchases']=models['M1_time_value']+[
        'major_item_diff','blink_bkb_diff']
    assert set(models)=={
        'M0_gold_only','M1_time_value','M2_lead_fragility',
        'M3_objective_conversion','P20_item_purchases'}
    results=[]
    for fold in folds:
        earlier=data[data.match_id.isin(fold['train_ids'])]
        later=data[data.match_id.isin(fold['eval_ids'])]
        assert earlier.match_id.nunique()==fold['train_games']
        assert later.match_id.nunique()==fold['eval_games']
        for name,columns in models.items():
            pipe=ns['fit_model'](earlier,columns)
            p=pipe.predict_proba(later[columns])[:,1]
            results.append(dict(fold=fold['fold'],model=name,
                train_games=fold['train_games'],eval_games=fold['eval_games'],
                embargo_games=fold['embargo_games'],
                eval_minute_rows=len(later),
                **scores(later.radiant_win,p,later.match_id)))
    table=pd.DataFrame(results)
    assert len(table)==25
    comparisons=[]
    for f in folds:
        sub=table[table.fold==f['fold']].set_index('model')
        comparisons.append(dict(fold=f['fold'],
          train_games=f['train_games'],eval_games=f['eval_games'],
          embargo_games=f['embargo_games'],
          m1_minus_m0_minute_ll=float(sub.loc['M1_time_value','minute_logloss']-
                 sub.loc['M0_gold_only','minute_logloss']),
          m1_minus_m0_match_ll=float(sub.loc['M1_time_value','equal_match_logloss']-
                 sub.loc['M0_gold_only','equal_match_logloss']),
          p20_minus_m1_minute_ll=float(sub.loc['P20_item_purchases','minute_logloss']-
                 sub.loc['M1_time_value','minute_logloss']),
          p20_minus_m1_match_ll=float(sub.loc['P20_item_purchases','equal_match_logloss']-
                 sub.loc['M1_time_value','equal_match_logloss']),
          best_minute_model=str(sub.minute_logloss.idxmin()),
          best_match_model=str(sub.equal_match_logloss.idxmin())))
    summary=pd.DataFrame(comparisons)
    safe=[{k:v for k,v in f.items() if k not in ('train_ids','eval_ids')} for f in folds]
    OUT.mkdir(parents=True,exist_ok=True)
    table.to_csv(OUT/'embargoed_train_only_25_scores.csv',index=False)
    summary.to_csv(OUT/'embargoed_train_only_5_comparisons.csv',index=False)
    (OUT/'embargoed_train_only_fold_receipt.json').write_text(json.dumps({
      'source':'frozen original 291 train matches only',
      'protocol_fractions':list(FRACTIONS),'folds':safe,
      'network_requests':0,'original_validation_matches_scored':0,
      'original_heldout_matches_scored':0,
      'models':list(models),'rows':len(table),
      'm1_minute_favorable_folds':int((summary.m1_minus_m0_minute_ll<0).sum()),
      'm1_match_favorable_folds':int((summary.m1_minus_m0_match_ll<0).sum()),
      'p20_minute_favorable_folds':int((summary.p20_minus_m1_minute_ll<0).sum()),
      'p20_match_favorable_folds':int((summary.p20_minus_m1_match_ll<0).sum()),
      'caveat':'retrospective; model ideas pre-exposed; folds share training data; estimated end ignores pauses',
    },sort_keys=True,indent=2)+'\n')
    print('FOLDS',json.dumps(safe,sort_keys=True),flush=True)
    print('COMPARISONS',summary.round(6).to_json(orient='records'),flush=True)
    print('ALL_25',table.round(6).to_json(orient='records'),flush=True)

if __name__=='__main__':main()
