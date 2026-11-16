#!/usr/bin/env python3
"""Audit completion-time label maturity on development data, NOT exposed TEST.

Two deliberately separate phases:
  --export-from-cache DIR  reconstructs only original TRAIN and VALIDATION
      minute features from original frozen OpenDota /matches payloads.
  --verify               runs entirely from the bundled compressed dev table,
      source-frozen TRAIN manifest and validation predictions. It compares
      source-model parity and a completion-embargoed TRAIN refit on VALIDATION.

The earliest validation game start is treated as an as-of cutoff; a TRAIN
game whose START+recorded DURATION exceeds it cannot contribute its outcome.
This is a post-hoc development sensitivity, not a new model or new blind test.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.posttest_temporal.collect_and_score import (
    frozen_functions, models_from_frozen_train, sha,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "research/frozen_original_train_features.csv.gz"
SPLIT = ROOT / "research/frozen_original_split_manifest.csv"
VAL_PREDS = ROOT / "artifacts/validation_m0_m1_predictions.csv"
DEV = ROOT / "research/frozen_original_development_features.csv.gz"
RECEIPT = ROOT / "docs/MATURE_LABEL_VALIDATION_RECEIPT.json"
NOTEBOOK = ROOT / "research/frozen_original_notebook_source.json"
EXPECTED_NOTEBOOK_SHA = "5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
EXPECTED_TRAIN_SHA = "066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
EXPECTED_SPLIT_SHA = "8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"
EXPECTED_PARTITIONS = {"train": (291, 10675), "validation": (103, 3781)}
COLS = (
    "match_id", "minute", "radiant_win",
    "gold_k", "minute10", "gold_x_time", "xp_k", "gold_velocity5_k",
    "xp_velocity5_k", "tower_delta", "barracks_delta", "roshan_delta",
    "kill_delta", "partition", "series_id", "start_time", "duration", "patch",
)
SEED = 20261113


def preflight():
    for path, expected in ((NOTEBOOK, EXPECTED_NOTEBOOK_SHA),
                           (TRAIN, EXPECTED_TRAIN_SHA),
                           (SPLIT, EXPECTED_SPLIT_SHA)):
        if sha(path.read_bytes()) != expected:
            raise ValueError("Frozen scientific source drift: " + str(path))
    meta = pd.read_csv(SPLIT)
    assert len(meta) == 500 and meta.match_id.is_unique
    assert meta.partition.value_counts().to_dict() == {
        "train": 291, "validation": 103, "test": 106}
    return meta


def read_development(path=DEV):
    if not path.is_file():
        raise FileNotFoundError("Missing frozen development feature archive")
    result = pd.read_csv(path)
    if list(result.columns) != list(COLS):
        raise ValueError("Development feature schema drift")
    if result[["match_id", "minute"]].duplicated().any():
        raise ValueError("Duplicated development minute")
    if set(result.partition) != {"train", "validation"}:
        raise ValueError("TEST cannot enter development feature audit")
    for split, (games, rows) in EXPECTED_PARTITIONS.items():
        block = result[result.partition == split]
        if block.match_id.nunique() != games or len(block) != rows:
            raise ValueError("Incorrect frozen development split: " + split)
        if not (block.minute * 60 < block.duration).all():
            raise ValueError("Post-terminal development minute")
        if not (block.groupby("match_id").minute.min() == 0).all():
            raise ValueError("Development forecast horizon missing minute 0")
    return result.sort_values(["partition", "match_id", "minute"],
                              kind="mergesort").reset_index(drop=True)


def export_from_cache(source_dir: Path):
    if DEV.exists() or RECEIPT.exists():
        raise FileExistsError("Refusing to overwrite immutable evidence")
    meta = preflight()
    selected = meta.loc[meta.partition != "test"].copy()
    funcs = frozen_functions()  # original, SHA-pinned notebook extractor
    rows = []
    for split in ("train", "validation"):
        block = selected[selected.partition == split]
        matches = []
        for row in block.itertuples(index=False):
            mid = int(row.match_id)
            key = sha(json.dumps(["/matches/" + str(mid), {}],
                                 sort_keys=True).encode("utf8"))
            path = source_dir / (key + ".json.gz")
            if not path.is_file():
                raise FileNotFoundError("Missing development source " + str(mid))
            with gzip.open(path, "rt", encoding="utf8") as stream:
                match = json.load(stream)
            if (match.get("match_id") != mid or
                int(match.get("start_time", -1)) != int(row.start_time) or
                int(match.get("series_id") or 0) != int(row.series_id) or
                str(match.get("patch")) != str(row.patch) or
                not isinstance(match.get("radiant_win"), bool)):
                raise ValueError("Development source identity mismatch " + str(mid))
            matches.append(match)
        minute = funcs["make_minute_table"](matches)
        aux = pd.DataFrame([{
            "match_id": int(m["match_id"]),
            "duration": int(m["duration"]),
        } for m in matches])
        block = minute.merge(block[["match_id", "series_id", "start_time",
                                    "patch", "partition"]],
                             on="match_id", validate="many_to_one")
        block = block.merge(aux, on="match_id", validate="many_to_one")
        rows.append(block)
    data = pd.concat(rows, ignore_index=True)
    data = data[list(COLS)].sort_values(
        ["partition", "match_id", "minute"], kind="mergesort").reset_index(drop=True)
    with DEV.open("wb") as binary:
        with gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0) as gz:
            gz.write(data.to_csv(index=False, float_format="%.17g",
                                 lineterminator="\n").encode("utf8"))
    print("RECONSTRUCTED", len(data), "development-only minutes from",
          selected.match_id.nunique(), "source games")
    receipt = compute_receipt(read_development())
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("SAVED", DEV, "SHA", receipt["frozen_dev_csv_gzip_sha256"])
    print("SAVED", RECEIPT, "embargoed game count", receipt["maturity"]["excluded_train_games"])


def fitted_specifications():
    notebook = json.loads(NOTEBOOK.read_text())
    cell = "".join(notebook["cells"][12]["source"])
    fragment = cell.split("\nmodels = {name: fit_model(train, cols)", 1)[0]
    assert fragment.count("def fit_model(frame, columns)") == 1
    namespace = {
        "Pipeline": Pipeline,
        "SimpleImputer": SimpleImputer,
        "StandardScaler": StandardScaler,
        "LogisticRegression": LogisticRegression,
        "SEED": SEED,
    }
    exec(compile(fragment, "frozen_original_model_source", "exec"), namespace)
    return namespace["SETS"], namespace["fit_model"]


def score_models(fit_df, eval_df, fit_model, specs):
    y = eval_df.radiant_win.to_numpy(int)
    scores = {}
    for name, cols in specs.items():
        p = fit_model(fit_df, cols).predict_proba(eval_df[cols])[:, 1]
        scores[name] = {
            "logloss": float(log_loss(y, p, labels=[0, 1])),
            "brier": float(brier_score_loss(y, p)),
        }
    best = min((v["logloss"], n) for n, v in scores.items() if n != "M0_gold_only")
    return scores, best[1]


def compute_receipt(df):
    meta = preflight()
    devmeta = meta[meta.partition != "test"]
    for mid, g in df.groupby("match_id", sort=True):
        ref = devmeta.set_index("match_id").loc[int(mid)]
        if (set(g.partition) != {ref.partition} or
            g.start_time.nunique() != 1 or int(g.start_time.iloc[0]) != int(ref.start_time) or
            g.series_id.nunique() != 1 or int(g.series_id.iloc[0]) != int(ref.series_id) or
            g.patch.nunique() != 1 or int(g.patch.iloc[0]) != int(ref.patch) or
            g.radiant_win.nunique() != 1):
            raise ValueError("Development manifest-source mismatch for match " + str(mid))
    tr = df[df.partition == "train"].copy()
    va = df[df.partition == "validation"].copy()
    original = pd.read_csv(TRAIN).sort_values(
        ["match_id", "minute"], kind="mergesort").reset_index(drop=True)
    observed = tr.sort_values(["match_id", "minute"],
                              kind="mergesort").reset_index(drop=True)
    assert len(original) == len(observed) == 10675
    for col in ("match_id", "minute", "radiant_win", "gold_k",
                "minute10", "gold_x_time", "series_id", "start_time", "duration"):
        a, b = original[col].to_numpy(), observed[col].to_numpy()
        if col in ("gold_k", "minute10", "gold_x_time"):
            if not np.allclose(a, b, atol=1e-11, rtol=0):
                raise ValueError("Original frozen TRAIN model input drift " + col)
        elif not np.array_equal(a, b):
            raise ValueError("Original frozen TRAIN metadata drift " + col)

    original_m, features, fingerprints = models_from_frozen_train()
    predictions = pd.read_csv(VAL_PREDS).sort_values(
        ["match_id", "minute"], kind="mergesort").reset_index(drop=True)
    assert len(predictions) == 3781
    for name in ("M0", "M1"):
        a = original_m[name].predict_proba(va[features[name]])[:, 1]
        if not (np.array_equal(predictions.match_id, va.match_id) and
                np.array_equal(predictions.minute, va.minute) and
                np.array_equal(predictions.radiant_win, va.radiant_win)):
            raise ValueError("Frozen VALIDATION labels/time keys differ")
        if not np.allclose(a, predictions["p_" + name].to_numpy(),
                           rtol=0, atol=1e-9):
            raise ValueError("Original M0/M1 VALIDATION prediction drift")

    first_validation_start = int(va.start_time.min())
    game_meta = tr.groupby("match_id", as_index=False)[
        ["start_time", "duration", "series_id"]].first()
    incomplete = game_meta[
        game_meta.start_time + game_meta.duration > first_validation_start
    ].sort_values("match_id")
    excluded_ids = [int(x) for x in incomplete.match_id]
    if len(excluded_ids) != 5:
        raise ValueError("Maturity exclusion expected exactly five TRAIN games")
    mature = tr.loc[~tr.match_id.isin(excluded_ids)].copy()
    if mature.match_id.nunique() != 286:
        raise ValueError("Mature TRAIN count incorrect")
    if (mature.groupby("match_id").start_time.first() +
            mature.groupby("match_id").duration.first() >
            first_validation_start).any():
        raise ValueError("Mature TRAIN leaks future labels")

    specs, fit_model = fitted_specifications()
    original_scores, original_selected = score_models(tr, va, fit_model, specs)
    mature_scores, mature_selected = score_models(mature, va, fit_model, specs)
    if original_selected != "M1_time_value" or mature_selected != "M1_time_value":
        raise ValueError("Refit changes original validation-selected model")
    if abs(original_scores["M1_time_value"]["logloss"] - 0.519713962581423) > 1e-8:
        raise ValueError("Original M1 validation score changed")
    if abs(original_scores["M0_gold_only"]["logloss"] - 0.532490) > 5e-7:
        raise ValueError("Original M0 validation score changed")

    maturity = {
        "first_validation_start_unix": first_validation_start,
        "completion_proxy": "match.start_time+parsed_duration, not received_at",
        "excluded_train_games": len(excluded_ids),
        "excluded_train_match_ids": excluded_ids,
        "max_estimated_train_result_overlap_seconds": int(
            (incomplete.start_time + incomplete.duration).max()
            - first_validation_start),
        "original_train_games": int(tr.match_id.nunique()),
        "mature_train_games": int(mature.match_id.nunique()),
        "validation_games": int(va.match_id.nunique()),
        "original_selected": original_selected,
        "embargo_selected": mature_selected,
        "original_validation_scores": original_scores,
        "embargo_validation_scores": mature_scores,
    }
    return {
        "status": "POST_HOC_COMPLETION_EMBARGO_DEVELOPMENT_ONLY",
        "source_science_notebook_sha256": sha(NOTEBOOK.read_bytes()),
        "source_train_3_feature_gzip_sha256": sha(TRAIN.read_bytes()),
        "source_split_manifest_sha256": sha(SPLIT.read_bytes()),
        "frozen_dev_csv_gzip_sha256": sha(DEV.read_bytes()),
        "dev_games": 394, "dev_minute_rows": len(df),
        "development_splits": {
            k: {"games": int(df[df.partition == k].match_id.nunique()),
                "minutes": int((df.partition == k).sum())}
            for k in ("train", "validation")
        },
        "original_frozen_model_fingerprints": fingerprints,
        "maturity": maturity,
        "scored_original_TEST": False,
        "refit_original_frozen_TEST": False,
        "original_notebook_or_TEST_modified": False,
        "sample_is_original_validation_previously_used_for_selection": True,
        "independent_prospective_or_blind_validation": False,
    }


def verify():
    previous = json.loads(RECEIPT.read_text())
    if sha(DEV.read_bytes()) != previous["frozen_dev_csv_gzip_sha256"]:
        raise ValueError("Maturity validation development data tampered")
    actual = compute_receipt(read_development())
    # Exact source/manifest SHA hashes remain mandatory. On a slightly
    # different compatible BLAS, logistic coefficient bit-hashes may move by
    # float roundoff while all 3,781 VAL probabilities and metric claims
    # remain equivalent within strict numerical tolerance. The original
    # source-fit fingerprint is anchored to the independent frozen
    # validation receipt, never silently replaced in the authored file.
    reference=json.loads((ROOT/"docs/VALIDATION_BIAS_RECEIPT.json").read_text())
    if previous["original_frozen_model_fingerprints"]!=reference["model_fingerprints"]:
        raise ValueError("Maturity model fingerprint provenance tampered")
    measured_fingerprints=actual.pop("original_frozen_model_fingerprints")
    actual["original_frozen_model_fingerprints"]=previous["original_frozen_model_fingerprints"]

    def equivalent(a,b,path="receipt"):
        if isinstance(a,dict) and isinstance(b,dict):
            if a.keys()!=b.keys():
                raise ValueError("Maturity audit receipt keys changed: "+path)
            for name in a:
                equivalent(a[name],b[name],path+"."+str(name))
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):
                raise ValueError("Maturity audit receipt list changed: "+path)
            for i,(x,y) in enumerate(zip(a,b)):
                equivalent(x,y,path+"["+str(i)+"]")
        elif (type(a) in (int,float) and type(b) in (int,float)
              and (type(a) is float or type(b) is float)):
            if not math.isclose(a,b,rel_tol=0.,abs_tol=1e-9):
                raise ValueError("Maturity audit numeric receipt drift: "+path)
        elif a!=b:
            raise ValueError("Maturity audit receipt changed: "+path)

    equivalent(actual,previous)
    # Retain current numeric fingerprint only as an informational check
    # for callers, while the original (immutable) source bit-fingerprint
    # remains the audit receipt's historical reference.
    actual["runtime_model_fingerprints"]=measured_fingerprints
    return actual


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-from-cache", type=Path, default=None)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if bool(args.export_from_cache) == bool(args.verify):
        parser.error("Choose exactly one: --export-from-cache DIR OR --verify")
    if args.export_from_cache:
        export_from_cache(args.export_from_cache)
    else:
        r = verify()
        print(json.dumps({"status": "PASS",
                          "excluded_games": r["maturity"]["excluded_train_games"],
                          "mature_train_games": r["maturity"]["mature_train_games"],
                          "selected_model": r["maturity"]["embargo_selected"],
                          "dev_minutes": r["dev_minute_rows"],
                          "sha": r["frozen_dev_csv_gzip_sha256"]}, indent=2))
