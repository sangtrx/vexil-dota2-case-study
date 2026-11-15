#!/usr/bin/env python3
"""Offline post-hoc 54-series sensitivity on fixed already-opened TEST predictions.

This never fits a model, modifies forecasts, or chooses a hypothesis.
Series membership is metadata fetched from the allowed OpenDota /matches endpoint,
frozen in docs/SERIES_GROUPS_TEST.json; it is NEVER a model input.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PRED=ROOT/"artifacts"/"heldout_predictions.csv"
META=ROOT/"docs"/"SERIES_GROUPS_TEST.json"
RECEIPT=ROOT/"docs"/"SERIES_CI_RECEIPT.json"

def compute():
    receipt=json.loads(RECEIPT.read_text())
    raw=PRED.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=receipt["source_csv_sha256"]:
        raise ValueError("Frozen forecast CSV has changed")
    rawmeta=META.read_bytes()
    if hashlib.sha256(rawmeta).hexdigest()!=receipt["series_group_metadata_sha256"]:
        raise ValueError("Frozen series grouping metadata has changed")
    meta=json.loads(rawmeta)
    frame=pd.read_csv(PRED)
    ids=set(frame.match_id.astype(int).unique())
    if ids != {int(k) for k in meta}:
        raise ValueError("Series metadata IDs differ from heldout forecasts")
    if frame.duplicated(["match_id","minute"]).any():
        raise ValueError("Repeated forecast keys")
    groups={}
    for mid in ids:
        gid=int(meta[str(mid)]["series_id"])
        groups[mid]=f"series:{gid}" if gid>0 else f"match:{mid}"
    frame["series"]=frame.match_id.map(groups)
    y=frame.radiant_win.to_numpy(float)
    model=np.clip(frame.p_model.to_numpy(float),1e-15,1-1e-15)
    baseline=np.clip(frame.p_baseline.to_numpy(float),1e-15,1-1e-15)
    frame["d_ll"]=-(y*np.log(model)+(1-y)*np.log1p(-model))+(y*np.log(baseline)+(1-y)*np.log1p(-baseline))
    frame["d_brier"]=(model-y)**2-(baseline-y)**2
    by=frame.groupby("series")[["d_ll","d_brier"]].agg(["sum","size"])
    n_groups=len(by)
    rng=np.random.default_rng(receipt["seed"])
    draws=rng.integers(0,n_groups,size=(receipt["n_bootstrap_resamples"],n_groups),endpoint=False)
    cnt=by[("d_ll","size")].to_numpy()[draws].sum(axis=1)
    ll=by[("d_ll","sum")].to_numpy()[draws].sum(axis=1)/cnt
    br=by[("d_brier","sum")].to_numpy()[draws].sum(axis=1)/cnt
    observed={
      "matches":len(ids),
      "minute_rows":len(frame),
      "series_clusters":n_groups,
      "series_id_missing_matches":sum(int(v["series_id"])<=0 for v in meta.values()),
      "primary_point_delta_ll":float(frame.d_ll.mean()),
      "primary_point_delta_brier":float(frame.d_brier.mean()),
      "series_bootstrap_delta_ll_ci":[float(v) for v in np.quantile(ll,[.025,.975])],
      "series_bootstrap_delta_brier_ci":[float(v) for v in np.quantile(br,[.025,.975])]
    }
    for key,val in observed.items():
        target=receipt[key]
        if isinstance(val,list):
            if not np.allclose(val,target,rtol=0,atol=1e-12):
                raise ValueError(f"Series bootstrap differs: {key}: {val} vs {target}")
        elif isinstance(val,float):
            if not np.isclose(val,target,rtol=0,atol=1e-12):
                raise ValueError(f"Series bootstrap differs: {key}: {val} vs {target}")
        elif val!=target:
            raise ValueError(f"Series bootstrap differs: {key}: {val} vs {target}")
    return observed

if __name__=="__main__":
    print(json.dumps(compute(),sort_keys=True,indent=2))
