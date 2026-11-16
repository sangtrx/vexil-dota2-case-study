#!/usr/bin/env python3
"""Build and verify a deterministic reviewer-facing Vexil submission archive."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
import tempfile
import numpy as np
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "delivery" / "Vexil_Dota2_Takehome_20261116.zip"
MODEL_CODE_SHA256 = "e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b"
EXPECTED_NOTEBOOK_SHA256 = "5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
EXPECTED_FORECAST_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
FILES = (
    "README.md",
    "SUBMISSION_PACKAGE_README.md",
    "HISTORY.md",
    "live_dota2_win_probability.ipynb",
    "requirements.txt",
    "REPORT.md",
    "REPORT.pdf",
    "artifacts/heldout_predictions.csv",
    "artifacts/forward_100_predictions.csv",
    "artifacts/forward_100_metadata.csv",
    "docs/FORWARD_100_STRESS.md",
    "docs/FORWARD_100_EVIDENCE.json",
    "docs/FORWARD_100_CANDIDATES.json",
    "docs/FORWARD_100_ORIGINAL_PROTOCOL.md",
    "docs/FORWARD_100_CLARIFICATIONS.md",
    "docs/NOVEMBER_120_RESEARCH_MANIFEST.csv",
    "docs/NOVEMBER_COHORT_OVERLAP_RECEIPT.json",
    "scripts/verify_november_cohort_overlap.py",
    "tests/test_november_cohort_overlap.py",
    "docs/figures/forward_100_phase.png",
    "scripts/verify_forward_100.py",
    "tests/test_forward_100_delivery.py",
    "docs/figures/heldout_reliability.png",
    "docs/figures/time_value_scenarios.png",
    "docs/figures/heldout_game_trajectory.png",
    "docs/EXPERIMENT_REGISTER.md",
    "docs/RESEARCH_DECISION_TRAIL.md",
    "docs/CURATION_PROVENANCE.md",
    "docs/STRICT_SERIES_ECE_RECEIPT.json",
    "docs/ERROR_ANALYSIS.md",
    "docs/ERROR_AUDIT_RECEIPT.json",
    "docs/CALIBRATION_BIAS_READOUT.md",
    "docs/CALIBRATION_BIAS_RECEIPT.json",
    "research/calibration_bias_sensitivity.py",
    "tests/test_calibration_bias_sensitivity.py",
    "artifacts/validation_m0_m1_predictions.csv",
    "docs/VALIDATION_BIAS_RECEIPT.json",
    "research/posttest_temporal/TRAIN_PARITY_RECEIPT.json",
    "research/posttest_temporal/collect_and_score.py",
    "research/validation_bias_reconstruct.py",
    "scripts/verify_validation_bias.py",
    "tests/test_validation_bias.py",
    "docs/COLAB_COLD_RUN_RECEIPT.json",
    "docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json",
    "research/FULL_NOTEBOOK_REPLAY_PROTOCOL.md",
    "research/full_notebook_replay.py",
    "tests/test_full_notebook_replay.py",
    "docs/SERIES_GROUPS_TEST.json",
    "docs/SERIES_CI_RECEIPT.json",
    "research/series_cluster_sensitivity.py",
    "docs/figures/phase_error_audit.png",
    "research/error_diagnostics.py",
    "research/render_error_figure.py",
    "research/TRAIN_CONTRAST_PROTOCOL.md",
    "research/train_time_effect_ci.py",
    "research/frozen_original_train_features.csv.gz",
    "research/frozen_original_split_manifest.csv",
    "research/TRAIN_TIME_CONTRAST_RECEIPT.json",
    "tests/test_train_time_effect_ci.py",
    "tests/test_private_access_disclosure.py",
    "scripts/render_report.py",
    "scripts/render_report_weasyprint.py",
    "scripts/report.css",
    "tests/test_notebook_contracts.py",
    "tests/test_report_contract.py",
    "tests/test_submission_forecasts.py",
    "tests/test_error_diagnostics.py",
)
STAMP = (2026, 11, 16, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify() -> dict:
    raw = (ROOT / "live_dota2_win_probability.ipynb").read_bytes()
    if sha(raw) != EXPECTED_NOTEBOOK_SHA256:
        raise ValueError("Frozen, output-saved reviewer notebook has changed.")
    notebook = json.loads(raw)
    cells = notebook["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    if len(cells) != 26 or len(code) != 14:
        raise ValueError("Expected exactly 26 notebook cells, 14 executable.")
    if any(c.get("execution_count") is None for c in code):
        raise ValueError("All 14 notebook code cells must have successful execution counts.")
    # Cell 4 declares the frozen match ID cohort and produces no output.
    # The other 13 executed code cells retain actual reviewer-visible output.
    empty_outputs=[i for i,c in enumerate(cells)
                   if c["cell_type"]=="code" and not c.get("outputs")]
    if empty_outputs != [4]:
        raise ValueError("Expected only the source-definition cell 4 to lack saved outputs.")
    if any(x.get("output_type") == "error" for c in code for x in c.get("outputs", [])):
        raise ValueError("Notebook contains an execution error.")
    if sum("image/png" in x.get("data", {}) for c in code for x in c.get("outputs", [])) != 4:
        raise ValueError("Expected four real, embedded notebook figures.")
    model_code = "".join("".join(c["source"]) for i, c in enumerate(cells)
                         if c["cell_type"] == "code" and i != 2)
    if sha(model_code.encode()) != MODEL_CODE_SHA256:
        raise ValueError("Scientific code does not match the pinned and locally tested corrected source.")
    setup = "".join(cells[2]["source"])
    setup_out = "".join(
        "".join(x.get("text", "")) if isinstance(x.get("text"), list)
        else str(x.get("text", ""))
        for x in cells[2].get("outputs", [])
        if x.get("output_type") == "stream"
    )
    if "10 hours active" not in setup or "Approximately 10 hours active" not in setup_out:
        raise ValueError("Missing candidate-estimated hours in Setup and saved output.")

    pins = (ROOT / "requirements.txt").read_text().splitlines()
    pins = [line.strip() for line in pins if line.strip() and not line.startswith("#")]
    if not pins or any("==" not in line for line in pins):
        raise ValueError("Unpinned dependency in requirements.txt.")
    page_info = subprocess.check_output(["pdfinfo", str(ROOT / "REPORT.pdf")], text=True)
    pages = int(next(x.split(":", 1)[1] for x in page_info.splitlines()
                     if x.startswith("Pages:")))
    if pages > 4:
        raise ValueError("Report exceeds the four-page assignment limit.")
    # A PDF with no embedded figures or local-only file:// links is not shippable.
    info_urls = subprocess.check_output(["pdfinfo", "-url", str(ROOT / "REPORT.pdf")], text=True)
    if "file:///" in info_urls:
        raise ValueError("PDF contains machine-local file hyperlinks.")
    if "github.com/sangtrx/" in info_urls:
        raise ValueError("PDF includes private GitHub hyperlinks that a recruiter cannot open.")
    # REPORT.md can change without refreshing REPORT.pdf. Check that key
    # employer-facing scientific statements and disclosure survived rendering.
    pdf_content=" ".join(subprocess.check_output(
        ["pdftotext","-layout",str(ROOT/"REPORT.pdf"),"-"],text=True).split())
    # PDF line-wrap may insert whitespace into a hyphenated compound.
    pdf_content=pdf_content.replace("cloud- export","cloud-export")
    for statement in (
            "16 November 2026",
            "no reviewer access granted",
            "63/106 game winners",
            "0.5174",
            "53-series",
            "−0.0436,+0.1001",
            "0.5429",
            "−0.1410,+0.0250",
            "cloud-export CSV byte parity was not verified",
            "No third-party Dota predictor was copied"):
        if statement not in pdf_content:
            raise ValueError("Stale or inconsistent REPORT.pdf rendering: "+statement)
    images = subprocess.check_output(["pdfimages", "-list", str(ROOT / "REPORT.pdf")], text=True)
    image_lines = [line for line in images.splitlines() if line.lstrip()[:1].isdigit()]
    if len(image_lines) < 4:
        raise ValueError("Report PDF has missing rendered figures.")
    report = (ROOT / "REPORT.md").read_text()
    if not all(x in report for x in ("**Time spent:**", "**Assistance disclosure:**", "**Result:**")):
        raise ValueError("Missing hours, assistance or results in report.")
    if "reviewer access provided separately" in report or "reviewer access granted separately" in (ROOT/"README.md").read_text():
        raise ValueError("Report falsely asserts private repo access granted")
    if "no reviewer access granted" not in report:
        raise ValueError("Source-repository access boundary missing")

    # This is a separate TRAIN-only post-selection interpretation audit, not
    # a new model comparison on original TEST. Do not load later labels.
    train_bytes = (ROOT/"research/frozen_original_train_features.csv.gz").read_bytes()
    split_bytes = (ROOT/"research/frozen_original_split_manifest.csv").read_bytes()
    contrast = json.loads((ROOT/"research/TRAIN_TIME_CONTRAST_RECEIPT.json").read_text())
    if (sha(train_bytes)!="066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
            or sha(split_bytes)!="8b91d5f740beea214c66d4e4c396edc3dfa39b931ebf5f5fef8566b19cdd3216"
            or contrast["source_train_sha256"]!=sha(train_bytes)
            or contrast["source_manifest_sha256"]!=sha(split_bytes)
            or contrast["train_games"]!=291 or contrast["train_rows"]!=10675
            or contrast["train_series_or_singleton_clusters"]!=171
            or contrast["bootstrap_draws"]!=2000
            or contrast["original_val_or_test_outcomes_opened_by_script"]!=0
            or contrast["selection_or_promotion_using_results"]):
        raise ValueError("TRAIN-only contrast provenance, sample or no-TEST contract drifted")
    diff=contrast["time_contrast"]
    lo,hi=diff["95ci"]
    if (not lo<0<hi or not math.isclose(diff["point"],0.07095204126763399,abs_tol=1e-12)
            or not math.isclose(lo,-0.010760791875407993,abs_tol=1e-12)
            or not math.isclose(hi,0.13792387963490257,abs_tol=1e-12)):
        raise ValueError("TRAIN-only series-bootstrap interval changed")
    if ("[−1.1,+13.8] pp" not in report
            or "crossing zero" not in report
            or "post-selection TRAIN-only" not in report
            or "not a causal effect" not in report):
        raise ValueError("Report must disclose that the TRAIN-only contrast interval crosses zero and is not causal")

    # Check post-hoc calibration-in-the-large without fitting on TEST.
    import importlib.util
    calprogram=ROOT/"research/calibration_bias_sensitivity.py"
    calspec=importlib.util.spec_from_file_location("vexil_calibration_bias_package",calprogram)
    calmod=importlib.util.module_from_spec(calspec)
    calspec.loader.exec_module(calmod)
    bias=calmod.evaluate()
    calmod.check(json.loads((ROOT/"docs/CALIBRATION_BIAS_RECEIPT.json").read_text()),bias)
    if (bias["games"]!=106 or bias["minute_forecasts"]!=3836
            or bias["series_or_singletons"]!=54
            or bias["no_calibration_fit_or_model_selection"] is not True
            or not bias["M1_mean_prediction_minus_outcome_minute_95ci_series"][0]<0<
                bias["M1_mean_prediction_minus_outcome_minute_95ci_series"][1]
            or "docs/CALIBRATION_BIAS_READOUT.md" not in report):
        raise ValueError("Calibration must be source-frozen, grouped, and nonconfirmatory")

    # Preserve the authentic original source ancestry while documenting
    # that the 16 November review sequence is a new curation, not
    # retroactively dated experimental work.
    provenance=(ROOT/"docs/CURATION_PROVENANCE.md").read_text()
    trail=(ROOT/"docs/RESEARCH_DECISION_TRAIL.md").read_text()
    if ("No commits are backdated" not in provenance
            or "retains the **authentic Git ancestry**" not in provenance
            or "not** an invented" not in trail
            or "**Retain M0; shadow-test M1" not in trail):
        raise ValueError("Curation provenance or decision-gate language missing")

    # The original validation cohort was already used to select M1.
    # Reproducing its bias is diagnostic only, never a new held-out trial.
    valprogram=ROOT/"scripts/verify_validation_bias.py"
    valspec=importlib.util.spec_from_file_location("vexil_validation_bias_package",valprogram)
    valmod=importlib.util.module_from_spec(valspec)
    valspec.loader.exec_module(valmod)
    val_audit=valmod.check()
    if (val_audit["status"]!="PASS_FROZEN_VALIDATION_BIAS_OFFLINE"
            or val_audit["validation_games"]!=103
            or val_audit["validation_minutes"]!=3781
            or val_audit["series_or_singletons"]!=53
            or not val_audit["never_a_new_blind_test"]
            or "53-series" not in report
            or "docs/CALIBRATION_BIAS_READOUT.md" not in report):
        raise ValueError("VALIDATION bias source and interpretation contract failed")

    # Supplemental post-TEST evaluation has its own frozen, reader-executable
    # validation path. It must never refit, adjust, or replace the main
    # 500-game experiment or claimed original TEST results.
    import importlib.util
    program=ROOT/"scripts/verify_forward_100.py"
    spec=importlib.util.spec_from_file_location("vexil_forward_100_package_verifier",program)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    supplement=module.verify()
    overlap_program=ROOT/"scripts/verify_november_cohort_overlap.py"
    overlap_spec=importlib.util.spec_from_file_location("vexil_overlap_package_verifier",overlap_program)
    overlap_module=importlib.util.module_from_spec(overlap_spec)
    overlap_spec.loader.exec_module(overlap_module)
    overlap=overlap_module.verify()
    if (overlap["status"]!="PASS_COHORTS_NOT_INDEPENDENT"
            or overlap["shared_games"]!=68 or overlap["new_100_games"]!=100
            or overlap["archived_120_games"]!=120
            or not overlap["do_not_pool_100_and_120_scores"]):
        raise ValueError("November cohort overlap/non-independence disclosure failed")
    if "Sixty-eight of these games" not in (ROOT/"REPORT.md").read_text():
        raise ValueError("Main report omitted material 68-game overlap disclosure")
    if (supplement["status"]!="PASS_ZIP_ONLY_100_FROZEN_FORECAST_AUDIT"
            or supplement["100_matches"]!=100
            or supplement["minute_rows"]!=4355
            or supplement["series_or_singletons"]!=56
            or supplement["leagues"]!=4
            or supplement["requires_original_raw_json"]
            or supplement["recomputed_original_500_model"]
            or supplement["no_model_selection"] is not True):
        raise ValueError("Supplemental 100-game source and scoring contract failed")

    cloud_receipt=json.loads((ROOT / "docs/COLAB_COLD_RUN_RECEIPT.json").read_text())
    if (cloud_receipt["scientific_code_sha256"]!=MODEL_CODE_SHA256
            or cloud_receipt["repo_main_notebook_sha256"]!=EXPECTED_NOTEBOOK_SHA256
            or cloud_receipt["code_cells_executed"]!=14
            or cloud_receipt["test_minute_rows"]!=3836
            or cloud_receipt["cloud_csv_byte_equality_verified"]):
        raise ValueError("Colab execution receipt conflicts with pinned scientific delivery.")

    forecasts = (ROOT / "artifacts/heldout_predictions.csv").read_bytes()
    full_replay=json.loads((ROOT / "docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json").read_text())
    fig_map={
        "calibration.png":"docs/figures/heldout_reliability.png",
        "time_value_scenarios.png":"docs/figures/time_value_scenarios.png",
        "heldout_game_trajectory.png":"docs/figures/heldout_game_trajectory.png",
    }
    if (full_replay["evidence_class"]!="AUTHOR_CONTROLLED_NO_NETWORK_500_MATCH_FRESH_KERNEL_REPLAY"
            or full_replay["source_code_sha256"]!=MODEL_CODE_SHA256
            or full_replay["source_notebook_sha256"]!=EXPECTED_NOTEBOOK_SHA256
            or full_replay["original_test_predictions_sha256"]!=EXPECTED_FORECAST_SHA256
            or not full_replay["local_fresh_kernel_test_csv_byte_parity_verified"]
            or not full_replay["report_figures_byte_equal_to_notebook_outputs"]
            or full_replay["executed_code_cells"]!=14
            or full_replay["cell_execution_errors"]!=0
            or full_replay["cache_hits"]!=500 or not full_replay["zero_http_calls"]
            or full_replay["source_gzip_files_copied"]!=500
            or full_replay["matches"]!=500 or full_replay["minute_rows"]!=18292
            or not full_replay["jupyter_kernel_is_controller_python"]
            or full_replay["split_minute_rows"]!={"train":10675,"validation":3781,"test":3836}
            or full_replay["split_match_counts"]!={"train":291,"validation":103,"test":106}
            or full_replay["selected_model"]!="M1_time_value"
            or full_replay["cloud_csv_byte_parity_claimed"]
            or full_replay["employer_release_or_submission_modified"]):
        raise ValueError("500-game fresh-kernel full-replay evidence differs from frozen outputs")
    validated={
        "M0_gold_only":(0.5324900423908928,0.1810746830906831),
        "M1_time_value":(0.519713962581423,0.1759016844633338),
        "M2_lead_fragility":(0.5223863883284187,0.17779381881266196),
        "M3_objective_conversion":(0.5282050730295414,0.18063144342728849),
    }
    if set(full_replay["validation_model_scores"])!=set(validated):
        raise ValueError("Fresh-kernel validation candidate list differs")
    for name,(ll,brier) in validated.items():
        values=full_replay["validation_model_scores"][name]
        if (abs(values["logloss"]-ll)>1e-9 or abs(values["brier"]-brier)>1e-9):
            raise ValueError("Fresh-kernel validation scores differ")
    for metric,(m0,m1) in {
        "logloss":(0.5164444241748873,0.504014697253528),
        "brier":(0.1719121780368728,0.1683528340689237),
    }.items():
        row=full_replay["heldout_scores"][metric]
        if abs(row["M0"]-m0)>1e-9 or abs(row["M1"]-m1)>1e-9:
            raise ValueError("Fresh-kernel TEST scores differ")

    for label in ("model_inputs","outcome_labels","dev_item_inputs","cohort_metadata"):
        if full_replay["source_lineage_sha256"][label] != cloud_receipt["source_lineage_sha256"][label]:
            raise ValueError("Fresh-kernel source/label lineage conflicts with fresh Colab")
    for generated,repo_path in fig_map.items():
        if full_replay["outputs_sha256"][generated]!=sha((ROOT/repo_path).read_bytes()):
            raise ValueError("Fresh notebook replay figure and report figure diverged")
    if full_replay["outputs_sha256"]["heldout_predictions.csv"]!=sha(forecasts):
        raise ValueError("Full notebook replay TEST CSV and repository CSV diverged")

    series_receipt=json.loads((ROOT / "docs/SERIES_CI_RECEIPT.json").read_text())
    series_meta=(ROOT / "docs/SERIES_GROUPS_TEST.json").read_bytes()
    if (series_receipt["source_csv_sha256"]!=EXPECTED_FORECAST_SHA256
            or series_receipt["series_group_metadata_sha256"]!=sha(series_meta)
            or series_receipt["series_clusters"]!=54
            or series_receipt["matches"]!=106
            or series_receipt["minute_rows"]!=3836):
        raise ValueError("Series-cluster sensitivity receipt is stale or ungrounded.")

    if sha(forecasts) != EXPECTED_FORECAST_SHA256:
        raise ValueError("Frozen held-out predictions have changed.")
    # Never package a stale post-hoc audit under a new frozen forecast receipt.
    audit = json.loads((ROOT / "docs/ERROR_AUDIT_RECEIPT.json").read_text())
    if audit.get("source_forecasts_sha256") != EXPECTED_FORECAST_SHA256:
        raise ValueError("Error-audit receipt does not match frozen source CSV.")
    if audit.get("overall", {}).get("minute_rows") != 3836 or audit.get("overall", {}).get("matches") != 106:
        raise ValueError("Error-audit receipt dimensions have changed.")
    rows = list(csv.DictReader(io.StringIO(forecasts.decode("utf8"))))
    if len(rows) != 3836 or len({r["match_id"] for r in rows}) != 106:
        raise ValueError("Expected exactly 106 games and 3,836 forecasts.")
    if not rows or list(rows[0]) != ["match_id", "minute", "p_model", "p_baseline", "radiant_win"]:
        raise ValueError("Missing required held-out probability columns.")
    for row in rows:
        if row["radiant_win"] not in ("0", "1"):
            raise ValueError("Invalid held-out target.")
        for key in ("p_model", "p_baseline"):
            p = float(row[key])
            if not math.isfinite(p) or p <= 0 or p >= 1:
                raise ValueError("Invalid probability in held-out CSV.")

    # Reproduce the original paired whole-match bootstrap on the immutable
    # corrected forecasts, not a new test or a new model-selection procedure.
    # Match clusters are the resampling unit and minute opportunities are the
    # scoring denominator; same-series correlation remains a limitation.
    ids=sorted({int(r["match_id"]) for r in rows})
    grouped={mid:[] for mid in ids}
    for row in rows:
        grouped[int(row["match_id"])].append(row)
    def match_ci(metric: str) -> tuple[float,float]:
        values=[]
        for mid in ids:
            subset=grouped[mid]
            def loss(row,model):
                y=int(row["radiant_win"])
                p=float(row[model])
                return (p-y)**2 if metric=="brier" else -(y*math.log(p)+(1-y)*math.log1p(-p))
            values.append([len(subset),
                           sum(loss(x,"p_model") for x in subset),
                           sum(loss(x,"p_baseline") for x in subset)])
        a=np.asarray(values,dtype=float)
        rng=np.random.default_rng(20261113)
        idx=rng.integers(0,len(a),size=(2000,len(a)))
        vals=a[idx].sum(axis=1)
        delta=(vals[:,1]-vals[:,2])/vals[:,0]
        return tuple(map(float,np.quantile(delta,[.025,.975])))
    ci_ll=match_ci("logloss")
    ci_brier=match_ci("brier")
    for got,expected in [
        (ci_ll,(-.03037142153342258,.0014126953857700388)),
        (ci_brier,(-.006938042296466374,.00019175815572719667)),
    ]:
        if any(abs(a-b)>1e-10 for a,b in zip(got,expected)):
            raise ValueError("Paired whole-match bootstrap CI contract drifted.")
    readme=(ROOT/"README.md").read_text()
    report=(ROOT/"REPORT.md").read_text()
    if "[-0.0304, +0.0014]" not in readme or "[−0.0304,+0.0014]" not in report:
        raise ValueError("README and report CI display does not match corrected forecasts.")
    if "28-way adjusted" not in report or "[−0.0169,+0.0064]" not in report:
        raise ValueError("Historical exploratory P20 interval/provenance absent.")
    if "AI reviews are not independent human peer review" not in report:
        raise ValueError("Mandatory accurate AI-review disclosure missing.")
    if "https://github.com/sangtrx/vexil-dota2-assessment" in report:
        raise ValueError("Reviewer PDF links to retired snapshot repository.")
    for local_source in ("docs/EXPERIMENT_REGISTER.md",
                         "docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json",
                         "docs/COLAB_COLD_RUN_RECEIPT.json",
                         "docs/ERROR_ANALYSIS.md"):
        if local_source not in report:
            raise ValueError("Reviewer PDF must identify bundled evidence: "+local_source)
    if "https://github.com/" in report:
        raise ValueError("Standalone PDF relies on inaccessible private GitHub links.")
    for text in ("100 eligible parsed professional games",
                 "11–15 November 2026", "4,355", "56 series/singleton",
                 "both include zero", "not an unseen patch",
                 "docs/FORWARD_100_STRESS.md"):
        if text.lower() not in report.lower():
            raise ValueError("Standalone report lacks honest later-cohort interpretation: "+text)
    if "artifacts/forward_100_predictions.csv" not in (ROOT/"docs/FORWARD_100_STRESS.md").read_text():
        raise ValueError("Supplement omits the actual frozen 4,355-row forecast source")
    if "no reviewer access granted" not in report or "both include zero" not in report:
        raise ValueError("Source-private/uncertainty limitations have been dropped")

    def measures(key: str) -> tuple[float, float]:
        ll = brier = 0.0
        for row in rows:
            y = int(row["radiant_win"])
            p = float(row[key])
            ll -= y * math.log(p) + (1 - y) * math.log1p(-p)
            brier += (p-y)**2
        return ll / len(rows), brier / len(rows)

    m0 = measures("p_baseline")
    m1 = measures("p_model")
    reference = ((0.5164444241748873, 0.1719121780368728),
                 (0.504014697253528, 0.1683528340689237))
    if any(abs(a - b) > 1e-12
           for computed, expected in zip((m0, m1), reference)
           for a, b in zip(computed, expected)):
        raise ValueError("Recomputed held-out metrics differ from report.")
    return {"pages": pages, "forecast_rows": len(rows), "heldout_games": 106,
            "calibration_bias_clusters": bias["series_or_singletons"],
            "calibration_bias_interval": bias["M1_mean_prediction_minus_outcome_minute_95ci_series"],
            "validation_bias_clusters":val_audit["series_or_singletons"],
            "validation_minute_rows":val_audit["validation_minutes"],
            "supplement_games": supplement["100_matches"],
            "supplement_minute_rows": supplement["minute_rows"],
            "supplement_series_clusters": supplement["series_or_singletons"],
            "supplement_leagues": supplement["leagues"],
            "paired_match_ci_logloss": ci_ll, "paired_match_ci_brier": ci_brier,
            "M0": m0, "M1": m1}


def run() -> dict:
    acceptance = verify()
    entries = {name: (ROOT / name).read_bytes() for name in FILES}
    manifest = {
        "project": "Vexil Capital Senior Data Scientist Dota 2 take-home",
        "created_on": "2026-11-16",
        "report_pages": acceptance["pages"],
        "notebook_sha256": EXPECTED_NOTEBOOK_SHA256,
        "scientific_code_sha256": MODEL_CODE_SHA256,
        "files": {n: {"bytes": len(v), "sha256": sha(v)}
                  for n, v in sorted(entries.items())},
    }
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    entries["PACKAGE_MANIFEST.json"] = payload
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w") as target:
        for name, data in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=STAMP)
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            target.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)
    with zipfile.ZipFile(DEST) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed.")
        for name, original in entries.items():
            if sha(archive.read(name)) != sha(original):
                raise ValueError("ZIP file changed: " + name)
    # Assert the shipped ZIP, not just the author worktree, can pass
    # all offline tests with NO .git, external cache, or private repo.
    with tempfile.TemporaryDirectory(prefix="vexil-clean-reviewer-") as scratch:
        with zipfile.ZipFile(DEST) as archive:
            archive.extractall(scratch)
        result=subprocess.run(
            [sys.executable,"-m","unittest","discover","-s","tests",
             "-p","test_*.py","-q"],
            cwd=scratch,capture_output=True,text=True,timeout=180)
        if result.returncode!=0:
            raise ValueError("Shipped ZIP fails reviewer-only offline tests: "+
                             (result.stdout+chr(10)+result.stderr)[-4500:])
        count=re.search(r"Ran\s+(\d+)\s+tests?\s+in\s+",result.stderr)
        if not count or int(count.group(1)) < 111 or "OK" not in result.stderr:
            raise ValueError("Extracted ZIP test suite incomplete or not PASS: "+
                             result.stderr[-1500:])
    return {"path": str(DEST), "zip_sha256": sha(DEST.read_bytes()),
            "size_bytes": DEST.stat().st_size, "files": len(entries),
            "science_code_sha256_pinned": True, **acceptance}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
