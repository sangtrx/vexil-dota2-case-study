"""Validate a hosted Vexil execution against local frozen scientific outputs.

This script reads user-supplied hosted artifacts offline. It does not launch
Colab/Kaggle, request credentials or authenticate a hosted job. The notebook
URL/runtime provenance must be independently inspected by the applicant.
"""
from __future__ import annotations

import argparse
import base64
import struct
import json
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from PIL import Image

TABLES = (
    "match_manifest.csv", "validation_ablations.csv", "heldout_metrics.csv",
    "terminal_sensitivity.csv", "heldout_predictions.csv",
    "minute20_comeback.csv", "exploratory_item_ablation.csv",
    "exploratory_item_folds.csv",
)
SOURCE_FIELDS = (
    "manifest_sha256", "model_input_sha256", "outcome_label_sha256",
    "dev_item_input_sha256", "cohort_metadata_sha256",
    "train_model_input_sha256", "train_outcome_label_sha256",
    "train_item_input_sha256",
)
RECEIPT_FIELDS = (
    "matches", "minute_rows", "patch_counts", "split_match_counts",
    "model_selected_on_validation", "seed", "canonical_float_places",
)

PLOTS = (
    "calibration.png", "time_value_scenarios.png",
    "heldout_game_trajectory.png", "minute20_comeback.png",
)


def verify_derived_images(directory: Path) -> dict:
    """Validate all four actual chart artifacts independent of provider UI."""
    records = {}
    for name in PLOTS:
        path = directory/name
        raw = path.read_bytes()
        if len(raw) < 10000 or not raw.startswith(bytes([137,80,78,71,13,10,26,10])):
            raise ValueError(f"Missing/corrupt PNG artifact: {name}")
        width, height = struct.unpack(">II", raw[16:24])
        if width < 400 or height < 200:
            raise ValueError(f"Unexpected PNG resolution: {name}")
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, ValueError) as exc:
            raise ValueError(f"Broken PNG image: {name}") from exc
        records[name] = {"bytes":len(raw),"size":[width,height]}
    return records



def compare_notebook(local_path: Path, hosted_path: Path,
                     require_embedded_images: bool = True) -> dict:
    local = nbformat.read(str(local_path), as_version=4)
    hosted = nbformat.read(str(hosted_path), as_version=4)
    nbformat.validate(local)
    nbformat.validate(hosted)
    if len(local.cells) != len(hosted.cells):
        raise ValueError("Hosted notebook has a different cell count")
    for i, (a, b) in enumerate(zip(local.cells, hosted.cells)):
        if a.cell_type != b.cell_type or a.source != b.source:
            raise ValueError(f"Hosted source differs in notebook cell {i}")
    code = [c for c in hosted.cells if c.cell_type == "code"]
    if len(code) != 14 or any(c.execution_count is None for c in code):
        raise ValueError("Hosted notebook did not save a full 14-code-cell execution")
    if any(o.output_type == "error" for c in code for o in c.outputs):
        raise ValueError("Hosted notebook has an error output")
    images = 0
    for cell_number, expected in ((15, 1), (20, 2), (22, 1)):
        if len(hosted.cells) <= cell_number:
            raise ValueError("Hosted notebook is missing expected visual cells")
        embedded = [output.data["image/png"]
                    for output in hosted.cells[cell_number].outputs
                    if output.output_type == "display_data"
                    and "image/png" in output.data]
        if require_embedded_images and len(embedded) != expected:
            raise ValueError(f"Missing saved PNG plots in notebook cell {cell_number}")
        if not require_embedded_images and len(embedded) not in (0, expected):
            raise ValueError(f"Partially stripped PNG outputs in notebook cell {cell_number}")
        for b64 in embedded:
            binary = base64.b64decode(b64 if isinstance(b64, str)
                                      else "".join(b64), validate=True)
            if not binary.startswith(bytes([137,80,78,71,13,10,26,10])) or len(binary) < 10000:
                raise ValueError(f"Corrupt saved PNG plot in notebook cell {cell_number}")
            images += 1
    return dict(cells=len(hosted.cells), executed_code_cells=len(code),
                source_exact_match=True, error_outputs=0,
                embedded_pngs=images)


def compare_tables(local_dir: Path, hosted_dir: Path, atol: float=2e-7) -> dict:
    records = {}
    for name in TABLES:
        a = pd.read_csv(local_dir/name)
        b = pd.read_csv(hosted_dir/name)
        if a.shape != b.shape or list(a.columns) != list(b.columns):
            raise ValueError(f"Hosted schema/row count mismatch: {name}")
        biggest = 0.
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
                left = a[col].to_numpy(dtype=float)
                right = b[col].to_numpy(dtype=float)
                if not np.allclose(left,right,atol=atol,rtol=0,equal_nan=True):
                    raise ValueError(f"Hosted numeric drift: {name}, column {col}")
                valid = np.isfinite(left-right)
                if valid.any():
                    biggest=max(biggest, float(np.abs(left-right)[valid].max()))
            elif not a[col].equals(b[col]):
                raise ValueError(f"Hosted nonnumeric drift: {name}, column {col}")
        records[name] = dict(rows=len(a), max_absolute_numeric_difference=biggest)
    return records


def verify(local_dir: Path, hosted_dir: Path, local_notebook: Path,
           hosted_notebook: Path, expected_runtime: str) -> dict:
    if expected_runtime not in ("colab", "kaggle"):
        raise ValueError("Expected runtime must be colab or kaggle")
    before=json.loads((local_dir/"derived_run_receipt.json").read_text())
    after=json.loads((hosted_dir/"derived_run_receipt.json").read_text())
    for key in SOURCE_FIELDS+RECEIPT_FIELDS:
        if before.get(key) != after.get(key):
            raise ValueError(f"Semantic source or frozen run receipt drift: {key}")
    if before["matches"]!=500 or before["minute_rows"]!=18304:
        raise ValueError("Local reference is not the validated frozen 500-match cohort")
    if before["model_selected_on_validation"]!="M1_time_value":
        raise ValueError("Unexpected model promotion")
    flags=after.get("runtime") or {}
    should_colab=expected_runtime=="colab"
    if flags.get("colab_detected") is not should_colab or flags.get("kaggle_detected") is should_colab:
        raise ValueError("Hosted receipt self-reported runtime does not match target")
    retrieval=after.get("retrieval") or {}
    if retrieval.get("api_calls",0) < 500 or retrieval.get("cache_hits") != 0:
        raise ValueError("Not a fresh OpenDota 500-match API retrieval receipt")
    if retrieval.get("candidate_exclusions") != 0:
        raise ValueError("The frozen 500-match cohort was modified")
    files=compare_tables(local_dir, hosted_dir)
    images=verify_derived_images(hosted_dir)
    # Kaggle's authenticated notebook pull can strip media outputs while
    # preserving executed code counts. Require four separately downloaded
    # real chart artifacts instead of rejecting a valid hosted execution.
    # Colab .ipynb downloads must retain all four embedded PNGs.
    cells=compare_notebook(local_notebook, hosted_notebook,
                           require_embedded_images=(expected_runtime=="colab"))
    return dict(
        outcome="NUMERICAL_AND_SAVED_SOURCE_PARITY_PASS",
        expected_runtime=expected_runtime,
        runtime_self_report=flags,
        hosted_http_calls=retrieval.get("api_calls"),
        hosted_cache_hits=retrieval.get("cache_hits"),
        raw_json_hash_unchanged=(
            before.get("source_content_sha256") ==
            after.get("source_content_sha256")),
        semantic_hashes_exact=True,
        scientific_files=files,
        exported_pngs=images,
        source_notebook=cells,
        limitations=[
            "Runtime flags and API-call counts are self-reported by the executed notebook.",
            "Kaggle notebook pulls may omit output media; verified exported PNG files are required.",
            "Use the authenticated Colab/Kaggle run URL and execution history to establish hosting provenance.",
            "This is the same already-inspected 500-match population, not new independent predictive evidence."
        ],
    )


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--local-output-dir",type=Path,required=True)
    p.add_argument("--hosted-output-dir",type=Path,required=True)
    p.add_argument("--local-notebook",type=Path,required=True)
    p.add_argument("--hosted-notebook",type=Path,required=True)
    p.add_argument("--expected-runtime",choices=("colab","kaggle"),required=True)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    result=verify(args.local_output_dir,args.hosted_output_dir,
                  args.local_notebook,args.hosted_notebook,
                  args.expected_runtime)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("HOSTED_RUN_VERIFICATION",json.dumps({
        "outcome":result["outcome"],
        "expected_runtime":result["expected_runtime"],
        "hosted_api_calls":result["hosted_http_calls"],
        "files":len(result["scientific_files"]),
        "source_cells":result["source_notebook"]["cells"],
        "raw_json_hash_unchanged":result["raw_json_hash_unchanged"]
    },sort_keys=True))


if __name__=="__main__":
    main()
