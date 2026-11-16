#!/usr/bin/env python3
"""Verify extended notebook in one fresh offline kernel, preserving frozen science.

Uses the original author-controlled 500-match OpenDota raw JSON cache.
The exported reviewer notebook is standalone in Colab (live OpenDota), but
this local QA avoids network and refuses any change to the original 26 cells'
source, model prediction CSV, cohort, scientific code or original figures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import nbformat

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"live_dota2_win_probability.ipynb"
FROZEN=ROOT/"research/frozen_original_notebook_source.json"
PIT=ROOT/"research/reviewer_notebook_pit_appendix.py"
METRIC=ROOT/"research/reviewer_notebook_report_appendix.py"
RECEIPT=ROOT/"docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json"
FROZEN_SHA="5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
EXPECTED_TEST_SHA="03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"


def sha(raw:bytes):
    return hashlib.sha256(raw).hexdigest()


def checked_sources(nb):
    if sha(FROZEN.read_bytes())!=FROZEN_SHA:
        raise ValueError("Frozen historic original notebook altered")
    original=nbformat.read(FROZEN,as_version=4)
    if len(original.cells)!=26 or len(nb.cells)!=29:
        raise ValueError("Append-only cell contract broken")
    for i,c in enumerate(original.cells):
        d=nb.cells[i]
        if d.cell_type!=c.cell_type or d.source!=c.source:
            raise ValueError("Original notebook cell source changed: "+str(i))
    if [c.cell_type for c in nb.cells[-3:]]!=["markdown","code","code"]:
        raise ValueError("Unexpected extension cell kinds")
    if nb.cells[27].source != PIT.read_text() or nb.cells[28].source != METRIC.read_text():
        raise ValueError("Current appendix code != reviewable standalone source")
    code=[c for c in nb.cells if c.cell_type=="code"]
    if len(code)!=16:
        raise ValueError("Expected original 14 plus 2 append-only code cells")
    return original


def execute(cache_dir:Path,out_dir:Path):
    sys.path.insert(0,str(ROOT))
    import research.full_notebook_replay as replay
    future=nbformat.read(MAIN,as_version=4)
    original=checked_sources(future)
    orig_fp=replay.scientific_fingerprint
    main_nb=replay.NB
    original_n_code=replay.EXPECTED_CODE_CELLS
    def fingerprint_first_original(nb):
        checked_sources(nb)
        subset=SimpleNamespace(cells=nb.cells[:26])
        return orig_fp(subset)
    try:
        replay.NB=MAIN
        replay.EXPECTED_CODE_CELLS=16
        replay.scientific_fingerprint=fingerprint_first_original
        receipt=replay.execute_replay(cache_dir,out_dir)
    finally:
        replay.NB=main_nb
        replay.EXPECTED_CODE_CELLS=original_n_code
        replay.scientific_fingerprint=orig_fp
    executed=nbformat.read(out_dir/"executed_fresh_kernel.ipynb",as_version=4)
    checked_sources(executed)
    if receipt["source_code_sha256"]!=replay.EXPECTED_NOTEBOOK_CODE_SHA:
        raise ValueError("Science model fingerprint drift")
    if receipt["executed_code_cells"]!=16 or receipt["cell_execution_errors"]!=0:
        raise ValueError("Appendix kernel run failed")
    appendix_output="\n".join(
        str(o.get("text","")) for cell in executed.cells[27:29]
        for o in cell.get("outputs",[]) if o.get("output_type")=="stream"
    )
    for token in ("18,292/18,292", "2,500 first-five-minute",
                  "TRAIN-only gold×time vs stronger gold+time NULL",
                  "CI includes zero", "Model decision preserved"):
        if token not in appendix_output:
            raise ValueError("Reviewer QA audit output missing: "+token)
    for i in (27,28):
        if (not executed.cells[i].outputs or
            executed.cells[i].execution_count is None):
            raise ValueError("Appendix has missing executed outputs")
    if sha((ROOT/"artifacts/heldout_predictions.csv").read_bytes())!=EXPECTED_TEST_SHA:
        raise ValueError("Original heldout results changed")
    nbformat.write(executed,MAIN)
    saved=nbformat.read(MAIN,as_version=4)
    checked_sources(saved)
    if sha(saved.cells[27].source.encode())!=sha(PIT.read_bytes()):
        raise ValueError("Post-save appendix source drift")
    result={
        "status":"APPEND_ONLY_REVIEWER_NOTEBOOK_SOURCE_FROZEN_QA",
        "source_science_notebook_sha256":FROZEN_SHA,
        "new_reviewer_notebook_sha256":sha(MAIN.read_bytes()),
        "unchanged_scientific_code_sha256":receipt["source_code_sha256"],
        "heldout_3836_csv_sha256":EXPECTED_TEST_SHA,
        "source_cells_26_bytewise_code_parity":True,
        "appended_markdown_cells":1,
        "appended_code_cells":2,
        "executed_total_code_cells":16,
        "no_network_calls":receipt["zero_http_calls"],
        "cached_original_matches":receipt["cache_hits"],
        "original_figures_exact_byte_parity":receipt["report_figures_byte_equal_to_notebook_outputs"],
        "original_TEST_predictions_byte_parity":receipt["local_fresh_kernel_test_csv_byte_parity_verified"],
        "all_18292_minute_PIT_checks_passed":True,
        "readable_original_and_new_outputs_preserved":True,
        "original_test_previously_inspected":True,
        "no_new_original_TEST_fit_or_model_promotion":True,
        "appendix_source_sha256":{
            "PIT":sha(PIT.read_bytes()),
            "report_crosswalk":sha(METRIC.read_bytes()),
        },
        "QA_source":"original 500 OpenDota match JSONs, author-controlled raw cache",
        "cloud_extended_appendix_replay_verified":False,
    }
    if RECEIPT.exists():
        old=json.loads(RECEIPT.read_text())
        if old!=result:
            raise ValueError("Existing reviewed appendix receipt would be overwritten")
    else:
        RECEIPT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache-dir",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args()
    execute(args.cache_dir,args.out_dir)
