#!/usr/bin/env python3
"""Regenerate only TRAIN+VAL features with deterministic gzip (no TEST payloads)."""
import argparse
import gzip
import hashlib
from pathlib import Path

import pandas as pd

from forward_oof_calibration import (
    ROOT, load_development, DEV_FEATURE_FILE_SHA,
    verify_split_manifest_bytes,
)

OUT=ROOT/"research/calibration_development_features.csv.gz"
MAN=ROOT/"research/calibration_frozen_manifest.csv"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    args=ap.parse_args()
    verify_split_manifest_bytes(args.manifest)
    df,_,_,test_read=load_development(args.cache,args.manifest)
    if test_read!=0:
        raise AssertionError("TEST payload unexpectedly read")
    cols=["match_id","minute","radiant_win","gold_k","minute10","gold_x_time",
          "partition","series_id","start_time","duration"]
    content=df[cols].to_csv(index=False).encode()
    import io
    buf=io.BytesIO()
    with gzip.GzipFile(filename="",mode="wb",fileobj=buf,mtime=0,compresslevel=9) as g:
        g.write(content)
    bytes_out=buf.getvalue()
    digest=hashlib.sha256(bytes_out).hexdigest()
    if digest!=DEV_FEATURE_FILE_SHA:
        raise AssertionError("Export differs from original frozen development features")
    if bytes_out!=OUT.read_bytes():
        raise AssertionError("Committed development dataset changed")
    print("PASS frozen 291 TRAIN + 103 VAL only; 0 TEST reads; SHA",digest)


if __name__=="__main__":
    main()
