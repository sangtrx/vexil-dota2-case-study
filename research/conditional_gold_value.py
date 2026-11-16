#!/usr/bin/env python3
"""Fixed-M1 TRAIN-only conditional gold effect, not a model selection test."""
from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from train_time_effect_ci import (
    DRAWS, FEATURES, MANIFEST_SHA, SEED, TRAIN_SHA,
    cluster_ids, model, require_data,
)
from sklearn.exceptions import ConvergenceWarning

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/CONDITIONAL_GOLD_VALUE_RECEIPT.json"


def contrast_rows() -> pd.DataFrame:
    """Ordering: zero/plus2 at t10, then zero/plus2 at t30."""
    return pd.DataFrame({
        "gold_k": [0., 2., 0., 2.],
        "minute10": [1., 1., 3., 3.],
        "gold_x_time": [0., 2.*math.log1p(1.), 0., 2.*math.log1p(3.)],
    })[FEATURES]


def evaluate_fit(frame: pd.DataFrame) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("error",ConvergenceWarning)
        pipe = model().fit(frame[FEATURES], frame.radiant_win.astype(int))
    x = contrast_rows()
    odds_logits = pipe.decision_function(x)
    p = pipe.predict_proba(x)[:, 1]
    g10 = float(odds_logits[1] - odds_logits[0])
    g30 = float(odds_logits[3] - odds_logits[2])
    d = float(g10 - g30)

    # Algebraic check: the minute main effect and global intercept cancel.
    step = pipe.named_steps["scale"].scale_
    coefficients = pipe.named_steps["logistic"].coef_[0]
    d_from_interaction = float(
        2. * (math.log1p(1.) - math.log1p(3.))
        * coefficients[2] / step[2]
    )
    if not math.isclose(d, d_from_interaction, abs_tol=1e-11, rel_tol=0):
        raise AssertionError("Conditional-gold contrast contains a time baseline effect")
    u10 = float(p[1] - p[0])
    u30 = float(p[3] - p[2])
    return {
        "gold_logodds_t10": g10,
        "gold_logodds_t30": g30,
        "logodds_difference_t10_minus_t30": d,
        "gold_probability_uplift_t10": u10,
        "gold_probability_uplift_t30": u30,
        "probability_uplift_difference_t10_minus_t30": u10-u30,
        "p0_t10":float(p[0]), "p2k_t10":float(p[1]),
        "p0_t30":float(p[2]), "p2k_t30":float(p[3]),
        "fitted_gold_interaction": float(coefficients[2] / step[2]),
    }


PRIMARY = "logodds_difference_t10_minus_t30"
SECONDARY = "probability_uplift_difference_t10_minus_t30"


def calculate(frame: pd.DataFrame, draws: int = DRAWS) -> dict:
    frame = frame.copy()
    frame["cluster"] = cluster_ids(frame)
    groups = {key: group.drop(columns="cluster")
              for key, group in frame.groupby("cluster",sort=True)}
    names = sorted(groups)
    if len(names) != 171:
        raise ValueError("Exactly 171 TRAIN resampling groups required")
    point = evaluate_fit(frame)
    rng = np.random.default_rng(SEED)
    sampled = np.empty((draws,2), dtype=float)
    for b in range(draws):
        picks = rng.integers(0,len(names),size=len(names))
        block = pd.concat([groups[names[int(i)]] for i in picks],ignore_index=True)
        if block.radiant_win.nunique() != 2:
            raise ValueError("Bootstrap resample lost outcome class")
        m = evaluate_fit(block)
        sampled[b,0] = m[PRIMARY]
        sampled[b,1] = m[SECONDARY]
        if (b+1)%500 == 0:
            print(f"BOOTSTRAP {b+1}/{draws}",flush=True)
    intervals = np.quantile(sampled,[.025,.975],axis=0)
    if not np.isfinite(sampled).all():
        raise ValueError("Nonfinite bootstrap effects")
    group_ids=cluster_ids(frame)
    distinct_series=int(frame.loc[frame.series_id>0,"series_id"].nunique())
    singleton_games=int(frame.loc[frame.series_id==0,"match_id"].nunique())
    if distinct_series+singleton_games!=len(names):
        raise ValueError("Series/singleton identities inconsistent")
    scope=frame.partition.value_counts().to_dict()
    if set(scope)!={"train"}:
        raise ValueError("Non-TRAIN outcomes accessed")
    core = {
        "evidence_class":"TRAIN_ONLY_POST_SELECTION_GOLD_EFFECT_NOT_HOLDOUT",
        "protocol":"research/CONDITIONAL_GOLD_VALUE_PROTOCOL.md",
        "source_train_sha256":TRAIN_SHA,
        "source_manifest_sha256":MANIFEST_SHA,
        "train_games":int(frame.match_id.nunique()),"train_rows":len(frame),
        "groups":len(names),"identified_series":distinct_series,"standalone_games":singleton_games,
        "draws":draws, "seed":SEED,
        "labels_loaded":"TRAIN outcomes only; frozen split manifest has no outcomes",
        "model_selection_or_test_promotion":False,
        "interpretation":"Associational conditional-logit contrasts, not causal gold value",
        "point":point,
        "primary":{
            "name":PRIMARY,
            "point":point[PRIMARY],
            "percentile_ci_95":intervals[:,0].tolist(),
            "positive_draw_share":float(np.mean(sampled[:,0]>0)),
        },
        "secondary":{
            "name":SECONDARY,
            "point":point[SECONDARY],
            "percentile_ci_95":intervals[:,1].tolist(),
            "positive_draw_share":float(np.mean(sampled[:,1]>0)),
        },
        "M0_time_invariant_gold_logodds_difference":0.0,
    }
    return core


def compare(actual:dict, frozen:dict)->None:
    def visit(a,b,path=""):
        if isinstance(b,dict):
            if not isinstance(a,dict) or set(a)!=set(b):
                raise ValueError("Schema changed: "+path)
            for k in b:
                visit(a[k],b[k],path+"."+k)
        elif isinstance(b,list):
            if not isinstance(a,list) or len(a)!=len(b):
                raise ValueError("Vector changed: "+path)
            for i,(u,v) in enumerate(zip(a,b)):
                visit(u,v,path+f"[{i}]")
        elif isinstance(b,float):
            if not isinstance(a,(float,int)) or not math.isfinite(a):
                raise ValueError("Nonfinite value at "+path)
            # Cross-runtime tolerances are for floating estimates only.
            tol=0.002 if path.endswith("positive_draw_share") else 3e-6
            if not math.isclose(a,b,rel_tol=0,abs_tol=tol):
                raise ValueError("Numeric difference "+path+f": {a} != {b}")
        elif a!=b or type(a) is not type(b):
            raise ValueError("Source, status or protocol change: "+path)
    visit(actual,frozen)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    args=parser.parse_args()
    value=calculate(require_data())
    if args.write:
        RECEIPT.write_text(json.dumps(value,indent=2,sort_keys=True,
                                      allow_nan=False)+"\n")
        print("WROTE",RECEIPT)
    else:
        compare(value,json.loads(RECEIPT.read_text()))
        print("PASS pinned TRAIN-only conditional gold value receipt")
    print("PRIMARY",value["primary"])
    print("SECONDARY",value["secondary"])


if __name__ == "__main__":
    main()
