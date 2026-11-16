#!/usr/bin/env python3
"""Offline original VALIDATION-label availability audit at first TEST start.

This is a retrospective label-timing audit, NOT a newly opened holdout.
It reads only the frozen 500-game partition metadata and the original
103-game derived VALIDATION feature archive, never TEST outcomes, minute
features or predictions. Original source SHA/TEST forecast are unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"research/frozen_original_split_manifest.csv"
DEVELOPMENT=ROOT/"research/frozen_original_development_features.csv.gz"
RECEIPT=ROOT/"docs/VAL_TEST_LABEL_MATURITY_RECEIPT.json"
ORIGINAL_MANIFEST_SHA="8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"
ORIGINAL_DEVELOPMENT_SHA="d4f91431d2c373eb772093bbf26ecb9c37c62714f95e89e0500e30b7700bd628"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def evaluate():
    if sha(MANIFEST.read_bytes())!=ORIGINAL_MANIFEST_SHA:
        raise ValueError("Frozen 500-game original split manifest altered")
    if sha(DEVELOPMENT.read_bytes())!=ORIGINAL_DEVELOPMENT_SHA:
        raise ValueError("Original development feature archive altered")
    meta=pd.read_csv(MANIFEST)
    dev=pd.read_csv(DEVELOPMENT)
    if (meta.match_id.nunique()!=500 or len(meta)!=500 or
        meta.partition.value_counts().to_dict()!={"train":291,"validation":103,"test":106}):
        raise ValueError("Frozen original partition counts changed")
    if len(dev)!=14456 or dev.match_id.nunique()!=394 or set(dev.partition)!={"train","validation"}:
        raise ValueError("Source is not original development-only archive")
    test=meta[meta.partition=="test"]
    val=dev.loc[dev.partition=="validation",[
        "match_id","start_time","duration","series_id","partition"
    ]].drop_duplicates()
    if len(val)!=103 or val.match_id.duplicated().any():
        raise ValueError("Original validation game duration unavailable")
    expected=meta.loc[meta.partition=="validation",[
        "match_id","start_time","series_id","partition"]]
    check=val.merge(expected,on="match_id",suffixes=("","_manifest"),validate="one_to_one")
    if (len(check)!=103 or
        not (check.start_time==check.start_time_manifest).all() or
        not (check.series_id==check.series_id_manifest).all() or
        not (check.partition==check.partition_manifest).all()):
        raise ValueError("Validation metadata does not match original manifest")
    first_test_start=int(test.start_time.min())
    lag=(val.start_time+val.duration)-first_test_start
    unfinished=val.loc[lag>0]
    last_estimated_end=int((val.start_time+val.duration).max())
    out={
        "status":"ORIGINAL_VALIDATION_TO_TEST_COMPLETION_PROXY_AUDIT",
        "frozen_original_split_manifest_sha256":ORIGINAL_MANIFEST_SHA,
        "frozen_original_development_archive_sha256":ORIGINAL_DEVELOPMENT_SHA,
        "first_test_start_unix":first_test_start,
        "validation_games":103,
        "test_games_metadata_only":106,
        "validation_outcomes_not_mature_at_first_test_start":len(unfinished),
        "validation_match_ids_unfinished_at_test":sorted(unfinished.match_id.astype(int).tolist()),
        "last_validation_estimated_end_unix":last_estimated_end,
        "last_validation_label_maturity_margin_seconds":first_test_start-last_estimated_end,
        "original_TEST_features_or_outcomes_scored":False,
        "models_fit_or_reselected":False,
        "proof_of_real_received_at":False,
        "original_holdout_was_previously_inspected":True,
        "duration_is_end_time_proxy_not_live_availability":True,
    }
    if out["last_validation_label_maturity_margin_seconds"]<0:
        raise ValueError("Some VALIDATION labels unavailable at original first TEST")
    return out


def verify():
    got=evaluate()
    recorded=json.loads(RECEIPT.read_text())
    if got!=recorded:
        raise ValueError("Frozen VALIDATION to TEST label-maturity receipt drift")
    return got


if __name__=="__main__":
    if RECEIPT.exists():
        value=verify()
    else:
        value=evaluate()
        RECEIPT.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:value[k] for k in (
        "status","first_test_start_unix",
        "validation_outcomes_not_mature_at_first_test_start",
        "last_validation_label_maturity_margin_seconds")},indent=2))
