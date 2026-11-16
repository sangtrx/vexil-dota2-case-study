#!/usr/bin/env python3
"""Append optional self-contained reviewer-audit cells, never changing model science.

The original output-saved notebook is archived byte-for-byte in research/.
New audit cells use notebook-memory original M0/M1 forecasts and TRAIN OOF,
not model selection on already opened VAL/TEST. Does not execute cells.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import nbformat

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"research/frozen_original_notebook_source.json"
MAIN=ROOT/"live_dota2_win_probability.ipynb"
PIT=ROOT/"research/reviewer_notebook_pit_appendix.py"
ANALYSIS=ROOT/"research/reviewer_notebook_report_appendix.py"
EXPECTED="5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
MARKDOWN="""## 7 · Reviewer-auditable diagnostic appendix (added 16 November 2026)

The **original 14 scientific code cells and their saved figures remain
source-frozen**. These two new appendix cells run after the original
forecasting pipeline and **do not refit, recalibrate, reselect, or change
any of the 3,836 original TEST predictions**. This section was added
*after TEST inspection*, so it cannot create a new blind evaluation.

First, all 18,292 admissible minute snapshots are re-evaluated against
source fields truncated to the forecast cutoff, with the final winner
and final duration deliberately poisoned. Next, all the report's
headline proper scores, a TRAIN-only no-skill prior, fixed-bin
descriptive calibration, and the stronger additive gold+time null
are reproduced using already-loaded notebook data.

The last forward-fold comparison uses only original TRAIN games and
refits on earlier *completed* matches. Its CI crossing zero means
the interaction's incremental forecast value remains **unconfirmed**.
Historical original source, TEST forecast CSV and the previous 14-cell
Colab receipt are archived separately for provenance.
"""
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def create(target:Path):
    if sha(FROZEN.read_bytes())!=EXPECTED:
        raise ValueError("Frozen original notebook source checksum changed")
    orig=nbformat.read(FROZEN,as_version=4)
    if len(orig.cells)!=26 or sum(c.cell_type=="code" for c in orig.cells)!=14:
        raise ValueError("Unexpected original 26-cell/14-code source")
    source1=PIT.read_text(encoding="utf8")
    source2=ANALYSIS.read_text(encoding="utf8")
    enhanced=nbformat.v4.new_notebook(metadata=orig.metadata)
    enhanced.cells=list(orig.cells)
    md=nbformat.v4.new_markdown_cell(MARKDOWN)
    md.id="vexil-reviewer-diagnostic-20261116"
    qa=nbformat.v4.new_code_cell(source1)
    qa.id="vexil-full-pit-20261116"
    qa.metadata["tags"]=["posthoc-audit","no-model-fit"]
    metrics=nbformat.v4.new_code_cell(source2)
    metrics.id="vexil-original-score-crosswalk-20261116"
    metrics.metadata["tags"]=["posthoc-audit","train-oof","no-test-refit"]
    enhanced.cells.extend([md,qa,metrics])
    if len(enhanced.cells)!=29 or sum(c.cell_type=="code" for c in enhanced.cells)!=16:
        raise ValueError("Appendix changed frozen structure")
    for i,c in enumerate(orig.cells):
        if enhanced.cells[i].source!=c.source:
            raise ValueError("Original scientific code changed in cell "+str(i))
    target.parent.mkdir(parents=True,exist_ok=True)
    nbformat.write(enhanced,target)
    print("APPENDED reviewer diagnostic cells 26/27/28, main notebook",target)
    print("SOURCE",sha(target.read_bytes()))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=MAIN)
    args=ap.parse_args()
    create(args.output)
