#!/usr/bin/env python3
"""Frozen M0/M1 March TRAIN fit, parity-checked against original saved TEST predictions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
TRAIN_FILE = ROOT / "research/frozen_original_train_features.csv.gz"
DEVELOPMENT_FILE = ROOT / "research/frozen_original_development_features.csv.gz"
TEST_FILE = ROOT / "artifacts/heldout_predictions.csv"
VAL_FILE = ROOT / "artifacts/validation_m0_m1_predictions.csv"
SEED = 20261113
INPUTS = {
    "M0": ["gold_k"],
    "M1": ["gold_k", "minute10", "gold_x_time"],
}

def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fit_models():
    if sklearn.__version__ != "1.7.2":
        raise RuntimeError("Expected original scikit-learn 1.7.2, got " + sklearn.__version__)
    a = pd.read_csv(TRAIN_FILE)
    assert len(a)==10675 and a.match_id.nunique()==291
    assert a.partition.eq("train").all()
    assert not a.duplicated(["match_id","minute"]).any()
    ans={}
    for label, cols in INPUTS.items():
        model=Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("logistic", LogisticRegression(C=1., max_iter=1000, random_state=SEED)),
        ])
        model.fit(a[cols], a["radiant_win"])
        ans[label]=model
    return ans

def coefficient_receipt(models):
    m={}
    for name,model in models.items():
        scaler=model.named_steps["scale"]; logit=model.named_steps["logistic"]
        imputer=model.named_steps["imputer"]
        m[name]={
            "inputs":INPUTS[name],
            "imputer_median":imputer.statistics_.tolist(),
            "mean":scaler.mean_.tolist(),
            "scale":scaler.scale_.tolist(),
            "coefficient":logit.coef_.tolist(),
            "intercept":logit.intercept_.tolist(),
        }
    return m

def verify_saved_original_validation(models):
    """Same source model on already-inspected original VALIDATION; not a new outcome test."""
    original=pd.read_csv(DEVELOPMENT_FILE)
    frozen=pd.read_csv(VAL_FILE)
    v=original.loc[original.partition.eq("validation"),
                   ["match_id","minute",*INPUTS["M1"]]]
    joined=frozen.merge(v,on=["match_id","minute"],how="left",
                        validate="one_to_one",indicator=True)
    if len(joined)!=3781 or not joined["_merge"].eq("both").all():
        raise ValueError("Frozen VALIDATION prediction keys do not match TRAIN/VAL feature file")
    diffs={}
    for name,pname in (("M0","p_M0"),("M1","p_M1")):
        actual=models[name].predict_proba(joined[INPUTS[name]])[:,1]
        maxabs=float(np.max(np.abs(actual-joined[pname].to_numpy())))
        diffs[name]=maxabs
        if maxabs>1e-10:
            raise ValueError(f"Original VALIDATION parity mismatch {name}, maxabs={maxabs}")
    return diffs

def describe_models():
    m=fit_models()
    return {
        "train_sha256":filehash(TRAIN_FILE),
        "dev_feature_sha256":filehash(DEVELOPMENT_FILE),
        "original_test_sha256":filehash(TEST_FILE),
        "original_notebook_sha256":filehash(ROOT/"live_dota2_win_probability.ipynb"),
        "sklearn":sklearn.__version__,
        "original_validation_max_abs_prediction_delta":verify_saved_original_validation(m),
        "models":coefficient_receipt(m),
    }

if __name__=="__main__":
    print(json.dumps(describe_models(),indent=2,sort_keys=True))
