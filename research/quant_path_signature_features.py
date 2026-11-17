#!/usr/bin/env python3
"""Exactly four bounded, causal economic-path signatures from TRAIN only.

The two cross-stream coordinates are constructed from as-of gold and XP
advantage histories; all outputs are odd under Radiant/Dire team swap.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/QUANT_PATH_SIGNATURES_PROTOCOL.md"
BASE_SHA = "e89526a951554e196983d8013afb378a151506f97953a8a1e6e2579c50f1da1b"
FIELDS = (
    "sig_goldxp_loop10",
    "sig_goldxp_leadlag10",
    "lead_occupancy10",
    "leader_underwater_area10",
)
WINDOW = 10


def prefix_features(gold: np.ndarray, xp: np.ndarray) -> np.ndarray:
    """Features of current and preceding <=10 minute observations, no fitting."""
    g = np.asarray(gold, dtype=np.float64)
    x = np.asarray(xp, dtype=np.float64)
    if g.ndim != 1 or x.shape != g.shape or not len(g):
        raise ValueError("Gold/XP must be equal, nonempty, 1-D prefixes")
    if not np.isfinite(g).all() or not np.isfinite(x).all():
        raise ValueError("Non-finite prefix inputs")
    g, x = g[-(WINDOW+1):], x[-(WINDOW+1):]
    s = float(np.sign(g[-1]))
    w = math.tanh(float(g[-1]) / 5.0)
    dg, dx = np.diff(g), np.diff(x)
    den = 1.0 + float(np.abs(dg).sum() * np.abs(dx).sum())

    if len(dg):
        gc, xc = g - g[0], x - x[0]
        area = float(0.5 * np.sum(gc[:-1] * xc[1:] - gc[1:] * xc[:-1]))
    else:
        area = 0.0
    if len(dg) >= 2:
        flow = float(np.sum(dx[:-1] * dg[1:] - dg[:-1] * dx[1:]))
    else:
        flow = 0.0
    occupancy = float(np.sign(g).mean())
    if s:
        leader = s * g
        underwater = float(-s * np.mean(np.maximum.accumulate(leader) - leader)
                           / (1.0 + abs(float(g[-1]))))
    else:
        underwater = 0.0
    out = np.asarray([w * area / den, w * flow / den,
                      occupancy, underwater],dtype=np.float64)
    if not np.isfinite(out).all():
        raise AssertionError("Non-finite path signature")
    return out


def attach_features(frame: pd.DataFrame, *, check_all: bool = True) -> tuple[pd.DataFrame,dict]:
    """Build features on the 291 original TRAIN games only, including PIT gates."""
    if not {"match_id","minute","gold_k","xp_level","partition"}.issubset(frame):
        raise ValueError("Missing trusted frozen TRAIN columns")
    if set(frame.partition) != {"train"}:
        raise ValueError("Non-TRAIN data refused")
    if len(frame) != 10675 or frame.match_id.nunique() != 291:
        raise ValueError("Frozen original TRAIN scope changed")
    if frame[["match_id","minute"]].duplicated().any():
        raise ValueError("Duplicate minute prediction")
    df = frame.sort_values(["match_id","minute"],kind="stable").reset_index(drop=True).copy()
    values = np.zeros((len(df), len(FIELDS)),dtype=np.float64)
    mirrored, poisoned, total = 0, 0, 0
    for _,grp in df.groupby("match_id",sort=False):
        idx = grp.index.to_numpy(dtype=int)
        minute = grp.minute.to_numpy(dtype=int)
        if not np.array_equal(minute,np.arange(len(grp))):
            raise ValueError("Forecast must have entire contiguous causal match prefix")
        gold = grp.gold_k.to_numpy(float)
        xp = grp.xp_level.to_numpy(float)
        if not np.isfinite(gold).all() or not np.isfinite(xp).all():
            raise ValueError("Invalid original economy time series")
        for t, row in enumerate(idx):
            p = prefix_features(gold[:t+1],xp[:t+1])
            values[row] = p
            total += 1
            if check_all:
                neg = prefix_features(-gold[:t+1],-xp[:t+1])
                if not np.allclose(neg,-p,rtol=0,atol=1e-10):
                    raise AssertionError("Side-swap parity violated")
                mirrored += 1
                if t+1 < len(gold):
                    poison_g = gold.copy()
                    poison_x = xp.copy()
                    poison_g[t+1:] = 1e6 * np.arange(1,len(gold)-t)
                    poison_x[t+1:] = -1e6 * np.arange(1,len(xp)-t)
                    poisoned_p = prefix_features(poison_g[:t+1],poison_x[:t+1])
                    if not np.array_equal(poisoned_p,p):
                        raise AssertionError("Future suffix influenced a forecast")
                poisoned += 1
    for j,name in enumerate(FIELDS):
        df[name]=values[:,j]
    if len(df)!=10675 or total!=10675 or not np.isfinite(values).all():
        raise AssertionError("Feature extraction count drift")
    return df, {
        "source":"frozen original TRAIN-derived as-of gold_k and xp_level",
        "original_raw_semantic_time_axis_verified":False,
        "all_rows":total,"matches":df.match_id.nunique(),
        "side_mirror_checks":mirrored,"causal_suffix_checks":poisoned,
        "features":list(FIELDS),"window_prior_minutes":WINDOW,
    }
