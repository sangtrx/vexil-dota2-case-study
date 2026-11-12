#!/usr/bin/env python3
"""Generate 3 PRIVATE CPU-only Kaggle notebook directories and a dataset stage.

Does not connect to Kaggle. Never embeds credentials, private Bible text
or unconsumed holdout data in a public artifact.
"""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_STAGE=Path("/home/ai-agent/.cache/vexil-bible-kaggle-stage-20261113")
DATA_ID="sangtruong/vexil-bible-development-qa-20261113"
DATA_SLUG="vexil-bible-development-qa-20261113"
EXPECTED_SHA="aebc0cccce1b4c7ed7591bafa3dd2cd52fc1f8de50aa7c79fcba5b2faf3532d4"

MODES={
    "scores":("Vexil Bible Proper Scores 20261113","vexil-bible-proper-scores-20261113"),
    "instability":("Vexil Bible Selection Instability 20261113","vexil-bible-selection-instability-20261113"),
    "maxt":("Vexil Bible Familywise Audit 20261113","vexil-bible-familywise-audit-20261113")
}

def sha(x):
    return hashlib.sha256(x.read_bytes()).hexdigest()

def cell(source,kind="code",cell_id="audit"):
    base={"cell_type":kind,"id":cell_id,"metadata":{},"source":source.splitlines(keepends=True)}
    if kind=="code":
        base.update(execution_count=None,outputs=[])
    return base

def notebook_for(mode):
    title,slug=MODES[mode]
    intro=f"""# {title}

Independent QA of previously examined Dota 2 development predictions.

This notebook **does not train any model** and is **not a new blind test**.
Source: private frozen dataset, original 291 train/103 validation split.
All 28 new models failed the precommitted selection screen. Original
M1 remains the take-home model.

Quant Research Bible v1.4.1, reference commit:
8e6374c8ac8c62da6611104555ce98f1cf40a528
"""
    code=f"""import hashlib, json, os, subprocess, sys
from pathlib import Path

mode = {mode!r}
data = Path(os.environ.get("VEXIL_BIBLE_DATASET", "/kaggle/input/{DATA_SLUG}"))
assert data.is_dir(), f"Attach PRIVATE Kaggle dataset {DATA_ID}, found {{data}}"
src = data / "dev_validation_predictions_28.csv"
sha256 = hashlib.sha256(src.read_bytes()).hexdigest()
assert sha256 == {EXPECTED_SHA!r}, "Wrong data version; refuse to score"
out = Path("/kaggle/working") if Path("/kaggle/working").is_dir() else Path(os.environ.get("VEXIL_BIBLE_OUTPUT", "/tmp/vexil-bible-qa"))
out.mkdir(parents=True,exist_ok=True)
script = data / "verify_bible.py"
subprocess.run([sys.executable,str(script),"--mode",mode,
                "--input-dir",str(data),"--output-dir",str(out)],check=True)
receipt = json.loads((out / f"kaggle_{{mode}}_receipt.json").read_text())
assert receipt["status"] == "PASS"
assert receipt["source_prediction_sha256"] == sha256
print(json.dumps(receipt, indent=2, sort_keys=True))
"""
    return {
        "cells":[cell(intro,"markdown",mode+"-intro"),cell(code,cell_id=mode+"-audit")],
        "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                    "language_info":{"name":"python","version":"3.12"}},
        "nbformat":4,"nbformat_minor":5
    }

def main():
    stage=DEFAULT_STAGE
    dataset=stage/"dataset"
    dataset.mkdir(parents=True,exist_ok=True)
    files={
        "dev_validation_predictions_28.csv":ROOT/"research/results/dev_validation_predictions_28.csv",
        "all_28_candidate_scores.csv":ROOT/"research/results/all_28_candidate_scores.csv",
        "calibration_and_phase_scores.csv":ROOT/"research/results/calibration_and_phase_scores.csv",
        "familywise_simultaneous_ci.csv":ROOT/"research/results/familywise_simultaneous_ci.csv",
        "all_estimator_weights.csv":ROOT/"research/bible/results/all_estimator_weights.csv",
        "cscv_20_selections.csv":ROOT/"research/bible/results/cscv_20_selections.csv",
        "series_oob_3000_selection.csv":ROOT/"research/bible/results/series_oob_3000_selection.csv",
        "validation_manifest_for_kaggle.csv":ROOT/"research/bible/results/validation_manifest_for_kaggle.csv",
        "known_trial_ledger.csv":ROOT/"research/bible/results/known_trial_ledger.csv",
        "verify_bible.py":ROOT/"kaggle/verify_bible.py"
    }
    manifest={}
    for name,src in files.items():
        assert src.is_file(),src
        dest=dataset/name
        shutil.copy2(src,dest)
        manifest[name]={"size":dest.stat().st_size,"sha256":sha(dest)}
    assert manifest["dev_validation_predictions_28.csv"]["sha256"]==EXPECTED_SHA
    metadata={
        "title":"Vexil Bible Development QA 20261113",
        "subtitle":"Reproducibility evidence for a Dota research project",
        "description":"PRIVATE, pre-examined development outputs only; 29 forecasts, 103 games. No unconsumed holdout labels, no unpublished Quant Bible text. Source OpenDota and derived research with copyright retained by source authors. Not a trading dataset.",
        "id":DATA_ID,
        "licenses":[{"name":"unknown"}]
    }
    (dataset/"dataset-metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    out=[]
    for mode,(title,slug) in MODES.items():
        d=ROOT/"kaggle"/("kernel_"+mode)
        d.mkdir(parents=True,exist_ok=True)
        filename=slug+".ipynb"
        (d/filename).write_text(json.dumps(notebook_for(mode),indent=1,ensure_ascii=False)+"\n")
        km={
            "id":"sangtruong/"+slug,"title":title,
            "code_file":filename,
            "language":"python","kernel_type":"notebook",
            "is_private":"true","enable_gpu":"false","enable_internet":"false",
            "dataset_sources":[DATA_ID],"competition_sources":[],
            "kernel_sources":[],"model_sources":[]
        }
        (d/"kernel-metadata.json").write_text(json.dumps(km,indent=2,sort_keys=True)+"\n")
        out.append({"mode":mode,"kernel_slug":km["id"],"source_file":filename})
    (stage/"dataset_files_sha256.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (ROOT/"kaggle/hosted_run_manifest.json").write_text(json.dumps({
        "state":"PREPARED_LOCALLY_NOT_UPLOADED_OR_EXECUTED",
        "dataset":DATA_ID,"private":True,
        "enable_internet":False,"enable_gpu":False,
        "expected_source_prediction_sha256":EXPECTED_SHA,
        "kernels":out,
        "local_stage":str(stage),
        "requires_new_user_authenticated_kaggle_cli":True,
        "do_not_claim_completed_kaggle_runs":True
    },indent=2,sort_keys=True)+"\n")
    print("PRIVATE_KAGGLE_RUNS_PREPARED",json.dumps({
       "dataset":DATA_ID,"private_kernels":[x["kernel_slug"] for x in out],
       "input_files":len(files),"data_bytes":sum(v["size"] for v in manifest.values()),
       "stage":str(stage)
    },sort_keys=True))

if __name__=="__main__":main()
