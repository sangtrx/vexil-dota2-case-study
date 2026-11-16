#!/usr/bin/env python3
"""Fixed M1 time contrast and TRAIN-series bootstrap, no original TEST access.

This does not select a new model. Intended as descriptive uncertainty around
an already reported conditional forecast at +2,000 gold minutes 10 and 30.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
TRAIN=ROOT/"research/frozen_original_train_features.csv.gz"
MANIFEST=ROOT/"research/frozen_original_split_manifest.csv"
RECEIPT=ROOT/"research/TRAIN_TIME_CONTRAST_RECEIPT.json"
TRAIN_SHA="066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
MANIFEST_SHA="8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"
SEED=20261115
DRAWS=2000
FEATURES=["gold_k","minute10","gold_x_time"]


def model():
    return Pipeline([
        ("imputer",SimpleImputer(strategy="median",keep_empty_features=True)),
        ("scale",StandardScaler()),
        ("logistic",LogisticRegression(C=1,max_iter=1000,random_state=20261113)),
    ])


def require_data():
    if hashlib.sha256(TRAIN.read_bytes()).hexdigest()!=TRAIN_SHA:
        raise ValueError("TRAIN-only feature blob differs from locked protocol")
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest()!=MANIFEST_SHA:
        raise ValueError("Original full five-column manifest differs")
    frame=pd.read_csv(TRAIN,float_precision="round_trip")
    manifest=pd.read_csv(MANIFEST)
    if not set(["match_id","minute","radiant_win","gold_k","minute10",
                "gold_x_time","partition","series_id","start_time","duration"]).issubset(frame):
        raise ValueError("Features missing")
    if set(frame.partition)!={"train"} or frame.match_id.nunique()!=291 or len(frame)!=10675:
        raise ValueError("TRAIN-only 291-game frozen dataset required")
    if set(frame.match_id).intersection(set(manifest.loc[manifest.partition!="train","match_id"])):
        raise ValueError("Validation/TEST match found in TRAIN")
    frame_meta=frame[["match_id","series_id","start_time"]].drop_duplicates().set_index("match_id").sort_index()
    saved_meta=manifest.loc[manifest.partition=="train",
            ["match_id","series_id","start_time"]].set_index("match_id").sort_index()
    if not frame_meta.equals(saved_meta):
        raise ValueError("Frozen series/start metadata modified")
    if frame[["match_id","minute"]].duplicated().any():
        raise ValueError("Multiple forecasts for same match-minute")
    if not ((frame.minute*60).to_numpy() < frame.duration.to_numpy()).all():
        raise ValueError("Postterminal feature row")
    if frame[FEATURES].isna().any().any() or not np.isfinite(frame[FEATURES].to_numpy()).all():
        raise ValueError("Missing or nonfinite M1 feature")
    if not np.allclose(frame.gold_x_time,frame.gold_k*np.log1p(frame.minute10),atol=1e-12,rtol=0):
        raise ValueError("Interaction definition drift")
    return frame


def scenario():
    return pd.DataFrame({
        "gold_k":[2.0,2.0],
        "minute10":[1.0,3.0],
        "gold_x_time":[2*np.log1p(1.0),2*np.log1p(3.0)],
    })


def fit_scenario(df):
    m=model().fit(df[FEATURES],df.radiant_win.astype(int))
    p=m.predict_proba(scenario()[FEATURES])[:,1]
    return float(p[0]),float(p[1]),float(p[0]-p[1])


def cluster_ids(df):
    # A series stays intact; standalone games are singleton groups.
    return np.where(df.series_id.astype(int)>0,
                    "s"+df.series_id.astype(str),
                    "m"+df.match_id.astype(str))


def calculate(df, draws=DRAWS):
    meta=df.copy()
    meta["resample_group"]=cluster_ids(meta)
    grouped={k:g.drop(columns=["resample_group"]) for k,g in meta.groupby("resample_group",sort=True)}
    clusters=list(grouped)
    if len(clusters)<80:
        raise ValueError("Too few professional TRAIN series for bootstrap")
    for g in grouped.values():
        if g.match_id.nunique()>1 and g.series_id.astype(int).eq(0).any():
            raise ValueError("Unknown-series games collapsed together")
    point=fit_scenario(df)
    rng=np.random.default_rng(SEED)
    output=[]
    for b in range(draws):
        idx=rng.integers(0,len(clusters),size=len(clusters))
        # Replicate entire series: both preprocessing and LR refit on same
        # repeated minute rows (no independent-minute bootstrap).
        sample=pd.concat([grouped[clusters[int(i)]] for i in idx],ignore_index=True)
        if sample.radiant_win.nunique()!=2:
            raise ValueError("Bootstrap resample lost one outcome class")
        output.append(fit_scenario(sample))
        if (b+1)%500==0:
            print("BOOTSTRAP",b+1,"/",draws,flush=True)
    values=np.asarray(output)
    if values.shape!=(draws,3) or not np.isfinite(values).all():
        raise AssertionError("Bootstrap matrix invalid")
    cuts=np.quantile(values,[0.025,0.975],axis=0)
    return {
        "evidence_class":"TRAIN_ONLY_POST_SELECTION_DESCRIPTIVE_SERIES_BOOTSTRAP",
        # Measured from the only input table with outcomes. The separately
        # hashed 500-game split manifest contains IDs only, never outcomes.
        "original_val_or_test_outcomes_opened_by_script":int((df.partition!="train").sum()),
        "target":"P(Radiant win|gold_k=2,minute=10) minus P(Radiant win|gold_k=2,minute=30)",
        "train_games":int(df.match_id.nunique()),"train_rows":len(df),
        "train_series_or_singleton_clusters":len(clusters),
        "bootstrap_draws":draws,"bootstrap_seed":SEED,
        "source_train_sha256":TRAIN_SHA,
        "source_manifest_sha256":MANIFEST_SHA,
        "moment_10_probability":{"point":point[0],"95ci":cuts[:,0].tolist()},
        "moment_30_probability":{"point":point[1],"95ci":cuts[:,1].tolist()},
        "time_contrast":{"point":point[2],"95ci":cuts[:,2].tolist(),
                         "bootstrap_share_positive":float((values[:,2]>0).mean())},
        "selection_or_promotion_using_results":False,
    }


def verify_replay(actual: dict, frozen: dict) -> None:
    """Cross-runtime numeric parity without permitting source/protocol drift.

    Source hashes, cohort counts, seeds, flags and field names are exact.
    Only floating scientific estimates have small platform-aware tolerance.
    This is not a statistical test, and it does not hide model differences.
    """
    exact=("evidence_class","original_val_or_test_outcomes_opened_by_script",
           "target","train_games","train_rows",
           "train_series_or_singleton_clusters","bootstrap_draws",
           "bootstrap_seed","source_train_sha256","source_manifest_sha256",
           "selection_or_promotion_using_results")
    if set(actual)!=set(frozen):
        raise ValueError("Receipt schema differs")
    for key in exact:
        if type(actual[key]) is not type(frozen[key]) or actual[key]!=frozen[key]:
            raise ValueError("Changed frozen study field: "+key)
    for key in ("moment_10_probability","moment_30_probability","time_contrast"):
        if set(actual[key])!=set(frozen[key]):
            raise ValueError("Changed metric schema: "+key)
        for name,original in frozen[key].items():
            recalculated=actual[key][name]
            if name=="95ci":
                if len(recalculated)!=2 or len(original)!=2:
                    raise ValueError("Changed percentile interval shape")
                candidates=zip(recalculated,original)
            else:
                candidates=[(recalculated,original)]
            for a,b in candidates:
                if not isinstance(a,(float,int)) or not math.isfinite(a):
                    raise ValueError("Invalid nonfinite metric "+key+"/"+name)
                tol=0.001 if name=="bootstrap_share_positive" else 2e-6
                if not math.isclose(a,b,abs_tol=tol,rel_tol=0):
                    raise ValueError("Numerical drift "+key+"/"+name+
                                     f": observed {a}, expected {b}")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write",action="store_true")
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--draws",type=int,default=DRAWS)
    args=ap.parse_args()
    if (args.write==args.check) or args.draws!=DRAWS:
        ap.error("Use one of --write/--check, exactly 2000 frozen draws")
    result=calculate(require_data(),DRAWS)
    payload=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.write:
        RECEIPT.write_text(payload)
        print("WROTE",RECEIPT)
    else:
        verify_replay(result,json.loads(RECEIPT.read_text()))
        print("PASS: frozen TRAIN-only result matches with strict source and numeric parity")
    print("TRAIN-SERIES CONTRAST",result["time_contrast"])


if __name__=="__main__":
    main()
