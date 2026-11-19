#!/usr/bin/env python3
"""Independent offline verification of the frozen March TEST predictions.

Requires numpy and pandas from requirements.txt. Does not refit or
rescore an already inspected TEST or access any API.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def verify():
    source = ROOT / "artifacts/heldout_predictions.csv"
    groups_path = ROOT / "docs/SERIES_GROUPS_TEST.json"
    receipt = json.loads((ROOT / "docs/SERIES_CI_RECEIPT.json").read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != receipt["source_csv_sha256"]:
        raise AssertionError("Frozen forecast hash drifted")
    if hashlib.sha256(groups_path.read_bytes()).hexdigest() != receipt["series_group_metadata_sha256"]:
        raise AssertionError("Frozen series metadata hash drifted")

    x = pd.read_csv(source)
    metadata = json.loads(groups_path.read_text())
    assert len(x) == 3836 and x.match_id.nunique() == 106
    assert set(map(str, x.match_id.unique())) == set(metadata)
    assert not x[["match_id", "minute"]].duplicated().any()
    y = x.radiant_win.to_numpy(dtype=float)
    a = x.p_baseline.to_numpy(dtype=float)
    b = x.p_model.to_numpy(dtype=float)
    assert set(np.unique(y)).issubset({0.0, 1.0})
    assert np.all((a > 0) & (a < 1)) and np.all((b > 0) & (b < 1))
    logloss = lambda q: -y*np.log(q)-(1-y)*np.log1p(-q)
    x["dll"] = logloss(b)-logloss(a)
    x["dbrier"] = (b-y)**2-(a-y)**2
    if abs(x.dll.mean()-receipt["primary_point_delta_ll"])>1e-12:
        raise AssertionError("Primary log-loss delta drifted")
    if abs(x.dbrier.mean()-receipt["primary_point_delta_brier"])>1e-12:
        raise AssertionError("Primary Brier delta drifted")
    x["series_group"] = [
        int(metadata[str(mid)]["series_id"]) or -int(mid)
        for mid in x.match_id
    ]
    g=x.groupby("series_group",sort=True)[["dll","dbrier"]].agg(["sum","size"])
    arr=np.stack([
        g["dll"]["sum"].to_numpy(float),
        g["dbrier"]["sum"].to_numpy(float),
        g["dll"]["size"].to_numpy(float),
    ],axis=1)
    assert len(arr)==receipt["series_clusters"]==54
    rng=np.random.default_rng(receipt["seed"])
    result=np.empty((receipt["n_bootstrap_resamples"],2),dtype=float)
    for i in range(len(result)):
        sampled=arr[rng.integers(0,len(arr),size=len(arr))]
        denom=sampled[:,2].sum()
        result[i]=sampled[:,0:2].sum(axis=0)/denom
    ci=np.quantile(result,[.025,.975],axis=0)
    for j,name in enumerate(("series_bootstrap_delta_ll_ci","series_bootstrap_delta_brier_ci")):
        if not np.allclose(ci[:,j],receipt[name],rtol=0,atol=1e-10):
            raise AssertionError(f"Series CI mismatch: {name}: {ci[:,j]} vs {receipt[name]}")
    return {"games":106,"minutes":len(x),"groups":len(arr),
            "M1_minus_M0_logloss":float(x.dll.mean()),
            "M1_minus_M0_brier":float(x.dbrier.mean()),
            "series_CI_logloss":ci[:,0].tolist(),
            "series_CI_brier":ci[:,1].tolist(),
            "new_blind_test":False}


if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
