#!/usr/bin/env python3
"""Refuse to declare Kaggle success without actual hosted JSON receipts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--local",type=Path,required=True)
    a=p.parse_args()
    for mode in ("scores","instability","maxt","chronology"):
        local=json.loads((a.local/("kaggle_"+mode+"_receipt.json")).read_text())
        remote=json.loads((a.source/mode/("kaggle_"+mode+"_receipt.json")).read_text())
        assert remote["status"]=="PASS"
        assert remote["run_location"]=="kaggle","Not hosted, refuse success"
        assert remote["kaggle_execution_env_detected"],"No Kaggle runtime environment evidence"
        for field in ("dataset_manifest_sha256","verification_script_sha256",
                      "stability_source_sha256","packaged_from_source_head"):
            assert remote[field]==local[field],(mode,field)
        assert local["source_prediction_sha256"]==remote["source_prediction_sha256"]
        assert local["source_known_trial_ledger_sha256"]==remote["source_known_trial_ledger_sha256"]
        for name,local_val in local["results"].items():
            remote_val=remote["results"][name]
            if type(local_val) is float:
                assert abs(local_val-remote_val)<1e-11,(mode,name,local_val,remote_val)
            else:assert local_val==remote_val,(mode,name)
        print("HOSTED_KAGGLE_NUMERICAL_PARITY_PASS",mode,remote["numpy_version"],remote["pandas_version"])
    print("FOUR_HOSTED_QA_KERNELS_VERIFIED_AFTER_OUTPUT_DOWNLOAD")

if __name__=="__main__":main()
