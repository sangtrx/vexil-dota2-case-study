#!/usr/bin/env python3
"""Exploratory TRAIN-only forward-OOF intercept calibration, no TEST ingestion.

The data sources are the cached raw /matches JSON and the frozen manifest
exported by the submission notebook. Original TEST match payloads are never
loaded. Running this script does not fit or alter any delivered model artifact.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit, logit
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261113
BOOTSTRAP_SEED = 20261115
DRAW_COUNT = 5000
MANIFEST_SHA = "e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea"
SPLIT_MANIFEST_FILE_SHA = "8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"
DEV_FEATURE_FILE_SHA = "2e591298ff543563298bcd6fe2ede3424b2b1e3befd3c6a97d5d759f5cda4efc"
ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "research/CALIBRATION_FORWARD_RECEIPT.json"
CUT_FRACTIONS = (0.45, 0.65, 0.75, 0.88)
COLS = ["gold_k", "minute10", "gold_x_time"]


def exact_data_cache_path(cache: Path, match_id: int) -> Path:
    key = hashlib.sha256(json.dumps([f"/matches/{match_id}", {}], sort_keys=True).encode()).hexdigest()
    return cache / (key + ".json.gz")


def verify_split_manifest_bytes(path: Path):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=SPLIT_MANIFEST_FILE_SHA:
        raise ValueError("Full five-column frozen manifest SHA mismatch")
    return digest


def validate_manifest(manifest: pd.DataFrame):
    names = ["match_id", "start_time", "patch"]
    if not set(names + ["partition", "series_id"]).issubset(manifest):
        raise ValueError("Invalid manifest columns")
    stable = manifest[names].sort_values(["start_time", "match_id"], kind="stable")
    identity = hashlib.sha256(stable.to_csv(index=False).encode()).hexdigest()
    if identity != MANIFEST_SHA:
        raise ValueError("Frozen cohort identity mismatch " + identity)
    counts = manifest.partition.value_counts().to_dict()
    if counts != {"train": 291, "validation": 103, "test": 106}:
        raise ValueError("The original 291/103/106 split is required")
    if manifest.match_id.duplicated().any():
        raise ValueError("Repeated match identifier")
    return identity


def parse_game_features(game, meta):
    mid = int(meta["match_id"])
    if type(game.get("match_id")) is not int or game["match_id"] != mid:
        raise ValueError("Incorrect game payload identifier")
    if int(game.get("start_time", -1)) != int(meta["start_time"]):
        raise ValueError("Start time mismatch")
    if str(game.get("patch")) != str(meta["patch"]):
        raise ValueError("Patch mismatch")
    if int(game.get("series_id") or 0) != int(meta["series_id"]):
        raise ValueError("Series mismatch")
    y = game.get("radiant_win")
    if type(y) is not bool:
        raise ValueError("Missing terminal outcome or invalid type")
    duration = game.get("duration")
    if type(duration) is not int or duration < 600:
        raise ValueError("Invalid duration")

    gold = game.get("radiant_gold_adv")
    xp = game.get("radiant_xp_adv")
    players = game.get("players")
    n = (duration - 1) // 60 + 1
    if (not isinstance(gold, list) or len(gold) < n
            or not isinstance(xp, list) or len(xp) != len(gold)
            or not isinstance(players, list) or len(players) != 10):
        raise ValueError("Missing aligned data")

    slots = [p.get("player_slot") if isinstance(p, dict) else None for p in players]
    if any(type(x) is not int for x in slots) or set(slots) != set(range(5)) | set(range(128, 133)):
        raise ValueError("Invalid player slot set")
    for player in players:
        times = player.get("times")
        g = player.get("gold_t")
        x = player.get("xp_t")
        if (not isinstance(times, list) or len(times) != len(gold)
                or not isinstance(g, list) or len(g) != len(gold)
                or not isinstance(x, list) or len(x) != len(gold)):
            raise ValueError("Misaligned per-player economy arrays")
        if any(type(t) is not int or t != 60*i for i, t in enumerate(times)):
            raise ValueError("Invalid minute times")
    for t in range(n):
        gsum = sum((1 if p["player_slot"] < 128 else -1)*p["gold_t"][t] for p in players)
        xsum = sum((1 if p["player_slot"] < 128 else -1)*p["xp_t"][t] for p in players)
        if (type(gold[t]) not in (int, float) or not math.isfinite(gold[t])
                or type(xp[t]) not in (int, float) or not math.isfinite(xp[t])
                or not math.isclose(gsum, gold[t], rel_tol=0, abs_tol=1e-6)
                or not math.isclose(xsum, xp[t], rel_tol=0, abs_tol=1e-6)):
            raise ValueError("Mismatched same-minute economy")
    rows = []
    for t in range(n):
        assert 60*t < duration
        g = gold[t]/1000
        rows.append({
            "match_id": mid, "minute": t, "radiant_win": int(y),
            "gold_k": g, "minute10": t/10,
            "gold_x_time": g*np.log1p(t/10),
            "partition": str(meta["partition"]),
            "series_id": int(meta["series_id"]),
            "start_time": int(meta["start_time"]),
            "duration": duration,
        })
    return rows


def load_development(cache: Path, manifest_path: Path):
    verify_split_manifest_bytes(manifest_path)
    manifest = pd.read_csv(manifest_path)
    identity = validate_manifest(manifest)
    all_rows = []
    digest = hashlib.sha256()
    loaded_ids = set()
    for item in manifest.sort_values(["start_time", "match_id"]).to_dict("records"):
        if item["partition"] == "test":
            # This branch must not even open source TEST files.
            continue
        mid = int(item["match_id"])
        file = exact_data_cache_path(cache, mid)
        with gzip.open(file, "rt", encoding="utf-8") as f:
            game = json.load(f)
        rows = parse_game_features(game, item)
        # Bind the receipt to the actual compressed raw source payload bytes,
        # not merely match identities and row counts.
        digest.update(hashlib.sha256(file.read_bytes()).digest())
        digest.update(json.dumps([mid, len(rows), item["partition"]]).encode())
        loaded_ids.add(mid)
        all_rows.extend(rows)
    test_ids=set(manifest.loc[manifest.partition=="test","match_id"].astype(int))
    actually_read_test_ids=loaded_ids.intersection(test_ids)
    if actually_read_test_ids:
        raise AssertionError("TEST payload was read during calibration")
    if len(loaded_ids) != 394:
        raise AssertionError("Unexpected development game count")
    df = pd.DataFrame(all_rows)
    counts = df.groupby("partition").size().to_dict()
    if counts != {"train": 10675, "validation": 3781}:
        raise AssertionError("Strict minute-snapshot row count mismatch: "+repr(counts))
    if df[["match_id", "minute"]].duplicated().any():
        raise AssertionError("Repeated match minute")
    return df, identity, digest.hexdigest(),len(actually_read_test_ids)


def make_model():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("logistic", LogisticRegression(C=1, max_iter=1000, random_state=SEED)),
    ])


def series_safe_cutpoints(manifest, fractions=CUT_FRACTIONS):
    info = manifest[manifest.partition == "train"].sort_values(["start_time", "match_id"]).reset_index(drop=True)
    keys = [("s", int(r.series_id)) if int(r.series_id)>0 else ("m", int(r.match_id))
            for r in info.itertuples()]
    lo, hi = {}, {}
    for i, k in enumerate(keys):
        lo[k] = min(lo.get(k, i),i)
        hi[k] = max(hi.get(k,i),i)
    valid = [i for i in range(1,len(info)) if not any(lo[k]<i<=hi[k] for k in lo)]
    cuts = [min(valid,key=lambda i:(abs(i-frac*len(info)),i)) for frac in fractions]
    if cuts != sorted(set(cuts)):
        raise ValueError("Not enough series-safe chronology")
    return info, cuts+[len(info)]


def forward_oof(train: pd.DataFrame, meta: pd.DataFrame, *, fractions=CUT_FRACTIONS,
                maturity_buffer_seconds=0):
    if maturity_buffer_seconds<0:
        raise ValueError("Negative maturity buffer")
    info, cuts = series_safe_cutpoints(meta, fractions=fractions)
    blocks = []
    predictions = []
    for left, right in zip(cuts[:-1], cuts[1:]):
        begin = int(info.iloc[left]["start_time"])
        older = info.iloc[:left].copy()
        # Label maturity: training example ends before first later game begins.
        # Read duration only from TRAIN features; never read future evaluation labels.
        maturities = train.groupby("match_id")["duration"].first()
        completed = set(int(r.match_id) for r in older.itertuples()
                        if int(r.start_time) + int(maturities.loc[int(r.match_id)]) + maturity_buffer_seconds <= begin)
        eval_ids = set(info.iloc[left:right].match_id.astype(int))
        older_rows = train[train.match_id.isin(completed)]
        later_rows = train[train.match_id.isin(eval_ids)]
        if (older_rows.match_id.nunique()<100 or later_rows.match_id.nunique()<15
                or not completed.isdisjoint(eval_ids)
                or older_rows.radiant_win.nunique() != 2):
            raise AssertionError("Invalid chronological OOF fold")
        if max(int(r.start_time)+int(maturities.loc[int(r.match_id)]) + maturity_buffer_seconds
               for r in older.itertuples() if int(r.match_id) in completed) > begin:
            raise AssertionError("Future training labels leaked")
        model=make_model().fit(older_rows[COLS],older_rows.radiant_win)
        p=model.predict_proba(later_rows[COLS])[:,1]
        predictions.append(pd.DataFrame({
            "match_id":later_rows.match_id.to_numpy(),
            "series_id":later_rows.series_id.to_numpy(),
            "minute":later_rows.minute.to_numpy(),
            "y":later_rows.radiant_win.to_numpy(dtype=int),
            "p":p,
        }))
        blocks.append({
            "older_complete_games": int(older_rows.match_id.nunique()),
            "embargoed_old_games": int(len(older)-older_rows.match_id.nunique()),
            "new_games": int(len(eval_ids)),
            "new_rows": int(len(later_rows)),
            "earliest_new_start": begin,
        })
    out = pd.concat(predictions, ignore_index=True)
    if out[["match_id","minute"]].duplicated().any():
        raise AssertionError("OOF pair collision")
    return out, blocks


def find_intercept_offset(p, y):
    """Single-parameter global logit shift. No threshold search or tuning."""
    p=np.asarray(p,dtype=float)
    y=np.asarray(y,dtype=int)
    if not (np.all(np.isfinite(p)) and np.all((p>0)&(p<1)) and set(np.unique(y))=={0,1}):
        raise ValueError("Invalid input for intercept-only calibration")
    z=logit(p)
    f=lambda b: float(np.mean(expit(z+b)-y))
    if f(-20)>0 or f(20)<0:
        raise ValueError("Calibration offset root not bracketed")
    b=float(brentq(f,-20,20,xtol=1e-12))
    if abs(f(b))>1e-10:
        raise AssertionError("Calibration root residual")
    return b


def ece10(y,p):
    y=np.asarray(y,dtype=int)
    p=np.asarray(p,dtype=float)
    idx=np.minimum((p*10).astype(int),9)
    return float(sum(abs(y[idx==b].mean()-p[idx==b].mean())*
                     np.mean(idx==b)
                     for b in range(10) if (idx==b).any()))


def metric_summary(frame, probname):
    y=frame.y.to_numpy(dtype=int);p=frame[probname].to_numpy(dtype=float)
    return {
        "logloss":float(log_loss(y,p,labels=[0,1])),
        "brier":float(brier_score_loss(y,p)),
        "ece10":ece10(y,p),
        "signed_mean_prediction_minus_outcome":float(np.mean(p-y)),
        "rows":int(len(frame)),
        "games":int(frame.match_id.nunique()),
    }


def paired_bootstrap(frame, draws=DRAW_COUNT):
    a=frame.copy()
    y=a.y.to_numpy(dtype=int)
    p0=a.p_uncal.to_numpy(dtype=float)
    p1=a.p_offset.to_numpy(dtype=float)
    eps=1e-15
    ll0=-(y*np.log(p0)+(1-y)*np.log1p(-p0))
    ll1=-(y*np.log(p1)+(1-y)*np.log1p(-p1))
    a["dlogloss"]=ll1-ll0
    a["dbrier"]=(p1-y)**2-(p0-y)**2
    a["group"]=np.where(a.series_id.to_numpy(dtype=int)>0,
                        "s"+a.series_id.astype(str),"m"+a.match_id.astype(str))
    groups=a.groupby("group",sort=True).agg(
        n=("match_id","size"),logloss=("dlogloss","sum"),brier=("dbrier","sum"))
    ns=groups.n.to_numpy()
    ds=groups[["logloss","brier"]].to_numpy()
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    draws_idx=rng.integers(0,len(groups),size=(draws,len(groups)))
    norm=ns[draws_idx].sum(axis=1)
    samples=ds[draws_idx].sum(axis=1)/norm[:,None]
    by_game=a.groupby("match_id")[["dlogloss","dbrier"]].mean()
    return {
        "groups":int(len(groups)), "draws":int(draws),
        "difference_cal_minus_original_logloss":float(a.dlogloss.mean()),
        "difference_cal_minus_original_brier":float(a.dbrier.mean()),
        "series_bootstrap_95ci_logloss":np.quantile(samples[:,0],[.025,.975]).tolist(),
        "series_bootstrap_95ci_brier":np.quantile(samples[:,1],[.025,.975]).tolist(),
        "equal_game_mean_difference_logloss":float(by_game.dlogloss.mean()),
        "equal_game_mean_difference_brier":float(by_game.dbrier.mean()),
    }


def study(cache, manifest):
    df, manifest_sha, source_digest,actual_test_reads=load_development(cache,manifest)
    train=df[df.partition=="train"].copy()
    val=df[df.partition=="validation"].copy()
    meta=pd.read_csv(manifest)
    oof, blocks=forward_oof(train,meta)
    offset=find_intercept_offset(oof.p.to_numpy(),oof.y.to_numpy())
    model=make_model().fit(train[COLS],train.radiant_win)
    pm=model.predict_proba(val[COLS])[:,1]
    # This replicates the SELECTED original M1 validation: predeclared tolerance,
    # no calibration, binning or output selection on VAL.
    baseline=make_model().fit(train[["gold_k"]],train.radiant_win)
    pbase=baseline.predict_proba(val[["gold_k"]])[:,1]
    original_ll=float(log_loss(val.radiant_win,pm))
    baseline_ll=float(log_loss(val.radiant_win,pbase))
    if not(abs(original_ll-.5197)<.0001 and abs(baseline_ll-.5325)<.0001):
        raise AssertionError(f"Original validation replication failed: {original_ll}, {baseline_ll}")
    vv=pd.DataFrame({
        "match_id":val.match_id.to_numpy(),"series_id":val.series_id.to_numpy(),
        "minute":val.minute.to_numpy(),"y":val.radiant_win.to_numpy(dtype=int),
        "p_uncal":pm,"p_offset":expit(logit(pm)+offset),
    })
    return {
        "evidence_class":"TRAIN_ONLY_OFFSET_REUSED_VAL_EXPLORATORY_NO_TEST_ACCESS",
        "protocol":"research/CALIBRATION_PROTOCOL.md",
        "inputs":{"manifest_identity_sha256":manifest_sha,
                  "train_and_validation_cached_payloads_digest":source_digest,
                  "training_games":291,"validation_games":103,
                  "train_rows":10675,"validation_rows":3781,
                  "test_games_read":0},
        "selection":{"fixed_candidate":"one-parameter log-odds intercept only",
                     "offset":offset, "oof_train_games":int(oof.match_id.nunique()),
                     "oof_rows":int(len(oof)), "folds":blocks,
                     "oof_uncalibrated":metric_summary(oof.rename(columns={"p":"p_uncal"}),"p_uncal"),
                     "oof_fitted":metric_summary(
                         oof.assign(p_offset=expit(logit(oof.p)+offset)),"p_offset")},
        "reused_validation":{"baseline_M0_logloss":baseline_ll,
                             "M1_original":metric_summary(vv,"p_uncal"),
                             "M1_offset":metric_summary(vv,"p_offset"),
                             "paired_comparison":paired_bootstrap(vv)},
        "test_untouched":True,
        "selected_model_unchanged":True,
        "cloud_parity_not_claimed":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache",required=True,type=Path)
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--write",action="store_true")
    ap.add_argument("--check",action="store_true")
    arg=ap.parse_args()
    if arg.write and arg.check:
        ap.error("Choose only one of --write or --check")
    result=study(arg.cache,arg.manifest)
    payload=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if arg.write:
        RECEIPT_PATH.write_text(payload)
        print("WROTE",RECEIPT_PATH)
    if arg.check:
        if RECEIPT_PATH.read_text()!=payload:
            raise SystemExit("FAIL: receipt mismatch")
        print("PASS: development-only receipt reproduced")
    p=result["reused_validation"]["paired_comparison"]
    print("OOF intercept offset",result["selection"]["offset"],"OOF",result["selection"]["oof_rows"])
    print("VAL M1 logloss original/offset",
          result["reused_validation"]["M1_original"]["logloss"],
          result["reused_validation"]["M1_offset"]["logloss"])
    print("VAL M1 Brier original/offset",
          result["reused_validation"]["M1_original"]["brier"],
          result["reused_validation"]["M1_offset"]["brier"])
    print("Series bootstrap paired DELTA logloss",p["difference_cal_minus_original_logloss"],
          p["series_bootstrap_95ci_logloss"])
    print("Series bootstrap paired DELTA brier",p["difference_cal_minus_original_brier"],
          p["series_bootstrap_95ci_brier"])


if __name__=="__main__":
    main()
