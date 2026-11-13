"""Canonical, cross-environment feature lineage fingerprint.

The raw OpenDota JSON can be re-parsed between runs. Hash only the
exact minute-level features and labels the models consume. Read-only
audit; no external API or new holdout model selection.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.robustness_study import build_data,OUT

MAIN=['match_id','minute','radiant_win','gold_k','minute10',
      'gold_x_time','xp_k','gold_velocity5_k','xp_velocity5_k',
      'tower_delta','barracks_delta','roshan_delta','kill_delta']
ITEM=['match_id','minute','major_item_diff','blink_bkb_diff']

def canonical_hash(frame,cols,decimals=8):
    if not set(cols).issubset(frame.columns):
        raise ValueError('required feature columns missing')
    v=frame.loc[:,cols].sort_values(['match_id','minute'],kind='stable').reset_index(drop=True)
    if v[['match_id','minute']].duplicated().any():
        raise ValueError('duplicate match-minute snapshot')
    for col in cols:
        if pd.api.types.is_numeric_dtype(v[col]) and not pd.api.types.is_integer_dtype(v[col]):
            if np.isinf(v[col].to_numpy(float)).any():
                raise ValueError('infinite numeric source field')
    # Canonical decimal representation tolerates platform ULP differences
    # in the log-time interaction but not substantive data drift.
    csv=v.to_csv(index=False,float_format=f'%.{decimals}f',
                 na_rep='NA',lineterminator='\n')
    return hashlib.sha256(csv.encode('utf-8')).hexdigest()

def main():
    ns,m,train=build_data()
    assert len(train)==10683 and train.match_id.nunique()==291
    assert len(set(MAIN))==len(MAIN)
    primary=canonical_hash(train,MAIN)
    purchases=canonical_hash(train,ITEM)
    again=canonical_hash(train.sample(frac=1,random_state=15),MAIN)
    assert primary==again, 'hash must ignore row ordering'
    empty={col:int(train[col].isna().sum()) for col in MAIN}
    assert empty['gold_k']==0 and empty['minute10']==0
    log=dict(
        scope='original 291 train games (not validation/test)',
        train_games=291,minute_rows=len(train),
        primary_features_sha256=primary,
        item_purchase_features_sha256=purchases,
        canonical_float_decimal_places=8,
        required_main_columns=MAIN,required_item_columns=ITEM,
        missing_count_per_column=empty,
        no_network_calls=True,
        no_heldout_model_scoring=True
    )
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'train_feature_lineage_receipt.json').write_text(
        json.dumps(log,sort_keys=True,indent=2)+'\n')
    print('FEATURE_LINEAGE_CANONICAL_TRAIN_PASS',
          json.dumps(log,sort_keys=True),flush=True)

if __name__=='__main__':main()
