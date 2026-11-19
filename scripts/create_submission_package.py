#!/usr/bin/env python3
"""Build the full internal research archive; not the minimal recruiter ZIP."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
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
DEST = ROOT / ".internal-review" / "Vexil_Dota2_FullResearch_20261119.zip"
MODEL_CODE_SHA256 = "e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b"
EXPECTED_NOTEBOOK_SHA256 = "5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"
EXPECTED_REVIEWER_NOTEBOOK_SHA256 = "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f"
# The genuine prior Colab run belongs to its recorded pre-editorial notebook,
# not the current spelling-only appendix edit. Do not rewrite cloud evidence.
PRE_EDITORIAL_CLOUD_NOTEBOOK_SHA256 = "466dce5d64adf081fb20642df210f903794745714675e225415c0aa8770f8304"
EXPECTED_FORECAST_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
FILES = (
    "README.md",
    "delivery/REVIEWER_README.md",
    "delivery/SUPPLEMENTARY_EXPERIMENTS.md",
    "delivery/Vexil_Dota2_Takehome_20261119.zip",
    "docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json",
    "scripts/build_reviewer_package.py",
    "SUBMISSION_PACKAGE_README.md",
    "HISTORY.md",
    "live_dota2_win_probability.ipynb",
    "research/frozen_original_notebook_source.json",
    "research/reviewer_notebook_pit_appendix.py",
    "research/reviewer_notebook_report_appendix.py",
    "research/reviewer_notebook_appendix_replay.py",
    "scripts/build_reviewer_notebook_appendix.py",
    "docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json",
    "tests/test_reviewer_notebook_appendix.py",
    "tests/test_reviewer_replay_idempotency.py",
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
    "docs/figures/train_matched_state_aliasing.png",
    "research/render_train_state_aliasing_figure.py",
    "tests/test_train_state_aliasing_figure.py",
    "research/train_leader_state_empirical.py",
    "research/render_interaction_null_figure.py",
    "docs/figures/train_interaction_vs_additive_null.png",
    "docs/TRAIN_LEADER_STATE_EMPIRICAL.md",
    "docs/TRAIN_LEADER_STATE_EMPIRICAL_RECEIPT.json",
    "docs/figures/train_leader_state_empirical.png",
    "tests/test_train_leader_state_empirical.py",
    "tests/test_fable_science_closure.py",
    "docs/EXPERIMENT_REGISTER.md",
    "docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md",
    "docs/RECORDED_RESEARCH_BRANCHES.md",
    "tests/test_creative_atlas_contract.py",
    "tests/test_concise_reviewer_bundle.py",
    "research/rich_feature_engineering.py",
    "tests/test_roshan_team_attribution.py",
    "tests/test_roshan_corrected_receipts.py",
    "research/ROSHAN_CORRECTION_20261119.md",
    "research/RICH_FEATURE_TRAIN_ONLY_ROSHAN_CORRECTED.csv.gz",
    "research/RICH_FEATURE_RAW_PROVENANCE_ROSHAN_CORRECTED.json",
    "research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_RECEIPT.json",
    "research/RICH_FEATURE_MODEL_ROSHAN_CORRECTED_READOUT.md",
    "research/roshan_corrected_rich_models.py",
    "research/quant_bible_path_risk_train_only.py",
    "research/QUANT_BIBLE_PATH_RECEIPT.json",
    "research/ROSHAN_CORRECTED_BOOSTED_RECEIPT.json",
    "research/ROSHAN_CORRECTED_BOOSTED_READOUT.md",
    "research/roshan_corrected_boosted_models.py",
    "research/BOOSTED_TREES_LOCKED_PROTOCOL_20261118.md",
    "research/BOOSTED_TREES_PRE_SCORE_DEPENDENCY_AMENDMENT_20261118.md",
    "research/QUANT_BIBLE_PATH_READOUT.md",
    "research/QUANT_PATH_SIGNATURES_READOUT.md",
    "research/OCT_NOV_FEATURE_TRANSFER_READOUT.md",
    "research/ROLE_DYNAMICS_TRANSFER_READOUT.md",
    "research/RICH_FEATURE_DIVERSITY_AUDIT.md",
    "research/MINIMAL_ECONOMY_SCORE_READOUT.md",
    "research/DISAGREEMENT_RELIABILITY_READOUT.md",
    "research/EVENT_DELAY_HOSTILE_READOUT.md",
    "research/CROSS_ARRAY_TIME_ALIGNMENT_READOUT.md",
    "research/FRESH_NOV17_EXTERNAL_READOUT.md",
    "research/CAUSAL_STALE_FEED_HOSTILE_READOUT.md",
    "research/STRICT_NODATA_TRAIN_FORWARD_REPAIR_READOUT.md",
    "research/CAUSAL_FORECAST_FILTER_READOUT.md",
    "research/RICH_FEATURE_MODEL_READOUT.md",
    "research/BOOSTED_TREES_DIRECT_READOUT.md",
    "research/BOOSTED_NESTED_FAIRNESS_READOUT.md",
    "research/BOOSTED_TREES_HOSTILE_DECISION_20261118.md",
    "research/POST_RESULT_EQUAL_MATCH_SENSITIVITY_NOTE_20261118.md",
    "docs/RESEARCH_DECISION_TRAIL.md",
    "docs/TEAM_LEAGUE_DEPENDENCE.md",
    "docs/TEAM_LEAGUE_DEPENDENCE_RECEIPT.json",
    "research/frozen_cohort_group_metadata.csv",
    "research/team_league_dependency_audit.py",
    "tests/test_team_league_dependence.py",
    "docs/DISCOVERY_PROVENANCE.md",
    "tests/test_discovery_provenance.py",
    "docs/CURATION_PROVENANCE.md",
    "docs/REVIEWER_HISTORY_MAP.md",
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
    "docs/COLAB_16CELL_RUN_RECEIPT.json",
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
    "research/frozen_original_development_features.csv.gz",
    "research/mature_label_validation_audit.py",
    "research/label_maturity_policy.py",
    "research/validation_test_label_maturity.py",
    "docs/VAL_TEST_LABEL_MATURITY_RECEIPT.json",
    "docs/MATURE_LABEL_VALIDATION_RECEIPT.json",
    "docs/DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md",
    "docs/DEVELOPMENT_ASOF_ROBUSTNESS_RECEIPT.json",
    "docs/REVIEWER_SCIENTIFIC_LIMITS.md",
    "research/development_asof_robustness.py",
    "research/preterminal_TEST_predictions_3837.csv",
    "research/verify_terminal_correction_history.py",
    "docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json",
    "tests/test_reviewer_scientific_integrity.py",
    "tests/test_mature_label_validation.py",
    "tests/test_label_maturity_policy.py",
    # Original unmerged-HOLD research, now self-contained and runnable:
    "research/CALIBRATION_PROTOCOL.md",
    "research/CALIBRATION_FORWARD_RECEIPT.json",
    "research/CALIBRATION_FINDINGS.md",
    "research/CALIBRATION_ERRATA.md",
    "research/calibration_development_features.csv.gz",
    "research/calibration_development_features.sha256",
    "research/calibration_frozen_manifest.csv",
    "research/forward_oof_calibration.py",
    "research/verify_calibration_offline.py",
    "research/GOLD_INTERACTION_HOSTILE_PROTOCOL.md",
    "research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json",
    "research/GOLD_INTERACTION_NULL_READOUT.md",
    "research/gold_interaction_null_influence.py",
    "research/conditional_gold_forward.py",
    "research/conditional_gold_value.py",
    "tests/test_original_hold_evidence.py",
    "research/full_500_prefix_audit.py",
    "docs/FULL_500_PREFIX_AUDIT_RECEIPT.json",
    "tests/test_full_500_prefix_audit.py",
    "research/cluster_reliability_bands.py",
    "docs/CALIBRATION_FIXED_BIN_GROUPED_CI_RECEIPT.json",
    "docs/CALIBRATION_FIXED_BIN_GROUPED_CI.md",
    "tests/test_cluster_reliability_bands.py",
    "research/TRAIN_TIME_CONTRAST_RECEIPT.json",
    "tests/test_train_time_effect_ci.py",
    "tests/test_private_access_disclosure.py",
    "scripts/create_submission_package.py",
    "scripts/render_report.py",
    "scripts/render_report_weasyprint.py",
    "scripts/report.css",
    "tests/test_notebook_contracts.py",
    "tests/test_report_contract.py",
    "tests/test_submission_forecasts.py",
    "tests/test_error_diagnostics.py",
)
STAMP = (2026, 11, 19, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify() -> dict:
    # Original Vexil brief asks for ONE runnable .ipynb with all work.
    # Frozen scientific source is retained in a plain JSON provenance file.
    if [name for name in FILES if name.endswith(".ipynb")]!=[
            "live_dota2_win_probability.ipynb"]:
        raise ValueError("Vexil requires exactly one runnable main notebook")
    # Preserve scientific provenance: original full notebook is byte-for-byte
    # archived. The reviewer notebook is a separate, post-TEST APPEND-ONLY
    # 16-code-cell version with all original 26 cells' code intact.
    original_raw=(ROOT/"research/frozen_original_notebook_source.json").read_bytes()
    if sha(original_raw)!=EXPECTED_NOTEBOOK_SHA256:
        raise ValueError("Original 14-cell scientific notebook archive drift")
    original=json.loads(original_raw)
    raw = (ROOT / "live_dota2_win_probability.ipynb").read_bytes()
    if sha(raw) != EXPECTED_REVIEWER_NOTEBOOK_SHA256:
        raise ValueError("Extended 16-cell reviewer notebook hash changed")
    notebook = json.loads(raw)
    cells = notebook["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    if (len(original["cells"])!=26 or len(cells)!=29 or len(code)!=16
            or sum(c["cell_type"]=="code" for c in original["cells"])!=14):
        raise ValueError("Expected original 26/14 and extended 29/16 notebook")
    if any((a["cell_type"]!=b["cell_type"] or
            "".join(a["source"])!="".join(b["source"]))
            for a,b in zip(cells[:26],original["cells"])):
        raise ValueError("Original 26 notebook cells' scientific sources changed")
    if (cells[27]["cell_type"]!="code" or cells[28]["cell_type"]!="code"
            or "".join(cells[27]["source"])!=(ROOT/"research/reviewer_notebook_pit_appendix.py").read_text()
            or "".join(cells[28]["source"])!=(ROOT/"research/reviewer_notebook_report_appendix.py").read_text()):
        raise ValueError("Auditable embedded appendix != source files")
    appendix=json.loads((ROOT/"docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json").read_text())
    if (appendix["new_reviewer_notebook_sha256"]!=sha(raw)
            or appendix["source_science_notebook_sha256"]!=EXPECTED_NOTEBOOK_SHA256
            or appendix["unchanged_scientific_code_sha256"]!=MODEL_CODE_SHA256
            or appendix["heldout_3836_csv_sha256"]!=EXPECTED_FORECAST_SHA256
            or appendix["executed_total_code_cells"]!=16
            or not appendix["all_18292_minute_PIT_checks_passed"]
            or not appendix["original_TEST_predictions_byte_parity"]
            or not appendix["original_figures_exact_byte_parity"]
            or not appendix["no_network_calls"]
            or appendix["cloud_extended_appendix_replay_verified"]):
        raise ValueError("Extended notebook independent kernel QA receipt invalid")
    for key,filename in (("PIT","research/reviewer_notebook_pit_appendix.py"),
                         ("report_crosswalk","research/reviewer_notebook_report_appendix.py")):
        if appendix["appendix_source_sha256"][key]!=sha((ROOT/filename).read_bytes()):
            raise ValueError("Extended appendix source receipt checksum changed")
    if any(c.get("execution_count") is None for c in code):
        raise ValueError("All 16 notebook code cells must have executed.")
    # Cell 4 defines frozen cohort IDs; it intentionally emits no outputs.
    empty_outputs=[i for i,c in enumerate(cells)
                   if c["cell_type"]=="code" and not c.get("outputs")]
    if empty_outputs != [4]:
        raise ValueError("Expected only source-definition cell 4 to lack output")
    if any(x.get("output_type") == "error" for c in code for x in c.get("outputs", [])):
        raise ValueError("Notebook contains an execution error.")
    if sum("image/png" in x.get("data", {}) for c in code for x in c.get("outputs", [])) != 4:
        raise ValueError("Expected four original real, embedded notebook figures.")
    output=" ".join(
        "".join(x.get("text", [])) if isinstance(x.get("text"), list)
        else str(x.get("text",""))
        for c in cells[27:29] for x in c.get("outputs",[])
        if x.get("output_type")=="stream")
    for token in ("18,292/18,292", "2,500 first-five-minute",
                  "TRAIN-only gold×time vs stronger gold+time NULL",
                  "CI includes zero","Model decision preserved"):
        if token not in output:
            raise ValueError("Rendered notebook lacks a verified reviewer crosswalk: "+token)
    # Only the original 14 scientific source cells define the original
    # model hash. New post-hoc QA is checked separately and cannot alter it.
    model_code = "".join("".join(c["source"]) for i,c in enumerate(cells[:26])
                         if c["cell_type"]=="code" and i != 2)
    if sha(model_code.encode()) != MODEL_CODE_SHA256:
        raise ValueError("Frozen original scientific model code changed.")
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
            "19 November 2026",
            "106 held-out games",
            "286 mature TRAIN games",
            "143 seconds",
            "18,292",
            "−0.0148,+0.0090",
            "[−0.0304,+0.0014]",
            "0.1028",
            "0.1074 (worse)",
            "0.5429",
            "63/106 = 0.5943",
            "+0.03139", "+0.00748", "[−0.00670,−0.00038]",
            "291-game TRAIN fit", "XGBoost 3.4.1",
            "one executed 16-code-cell notebook",
            "AI reviews are not independent human peer review"):
        if statement not in pdf_content:
            raise ValueError("Stale or inconsistent REPORT.pdf rendering: "+statement)
    images = subprocess.check_output(["pdfimages", "-list", str(ROOT / "REPORT.pdf")], text=True)
    image_lines = [line for line in images.splitlines() if line.lstrip()[:1].isdigit()]
    if len(image_lines) < 4:
        raise ValueError("Report PDF has missing rendered figures.")
    report = (ROOT / "REPORT.md").read_text()
    if not all(x in report for x in ("**Time spent:**", "**Assistance disclosure:**", "**Decision.**")):
        raise ValueError("Missing hours, assistance or results in report.")
    if "reviewer access provided separately" in report or "reviewer access granted separately" in (ROOT/"README.md").read_text():
        raise ValueError("Report falsely asserts private repo access granted")
    if "no reviewer access granted" in report:
        raise ValueError("Private access workflow leaked into scientific report")

    # The original VAL->TEST chronology is independently checked using
    # original development-only outcomes and TEST start metadata (no TEST
    # prediction, winner or score ever consulted).
    vtpath=ROOT/"research/validation_test_label_maturity.py"
    vtspec=importlib.util.spec_from_file_location("vexil_val_test_maturity",vtpath)
    vtmodule=importlib.util.module_from_spec(vtspec)
    vtspec.loader.exec_module(vtmodule)
    vt=vtmodule.verify()
    if (vt["validation_outcomes_not_mature_at_first_test_start"]!=0
            or vt["last_validation_label_maturity_margin_seconds"]!=143
            or vt["models_fit_or_reselected"]
            or vt["original_TEST_features_or_outcomes_scored"]
            or vt["proof_of_real_received_at"]
            or "143 seconds" not in report):
        raise ValueError("VAL to TEST source-label maturity audit inconsistent")

    # Completion-time, development-only maturity audit: the reviewer ZIP
    # must independently refit M0-M3 from exactly 394 frozen original
    # TRAIN/VAL matches and reproduce both 291- and 286-game selections.
    maturity_file=ROOT/"research/mature_label_validation_audit.py"
    maturity_spec=importlib.util.spec_from_file_location(
        "vexil_mature_label_package_verifier",maturity_file)
    maturity_module=importlib.util.module_from_spec(maturity_spec)
    maturity_spec.loader.exec_module(maturity_module)
    mature=maturity_module.verify()
    if (mature["dev_games"]!=394 or mature["dev_minute_rows"]!=14456
            or mature["maturity"]["mature_train_games"]!=286
            or mature["maturity"]["original_selected"]!="M1_time_value"
            or mature["maturity"]["embargo_selected"]!="M1_time_value"
            or mature["scored_original_TEST"]
            or mature["independent_prospective_or_blind_validation"]
            or "286 mature TRAIN games" not in report
            or "[−0.0148,+0.0090]" not in report):
        raise ValueError("Mature-label or strong-null reviewer evidence drift")

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
    # The exact scenario CI is fully preserved in the audited receipt;
    # the four-page reader report should explain model interpretation
    # without reproducing every post-hoc contrast.
    if ("not an effect caused by time" not in report
            or "not evidence of a within-game time effect" not in report):
        raise ValueError("Figure 1 or empirical time comparison is misrepresented")

    # Check post-hoc calibration-in-the-large without fitting on TEST.
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
            or "docs/CALIBRATION_BIAS_READOUT.md" not in (ROOT/"README.md").read_text()):
        raise ValueError("Calibration must be source-frozen, grouped, and nonconfirmatory")

    # Preserve the authentic original source ancestry while documenting
    # that the 16 November review sequence is a new curation, not
    # retroactively dated experimental work.
    provenance=(ROOT/"docs/CURATION_PROVENANCE.md").read_text()
    trail=(ROOT/"docs/RESEARCH_DECISION_TRAIL.md").read_text()
    branch_index=(ROOT/"docs/REVIEWER_HISTORY_MAP.md").read_text()
    if ("7b3584f" not in branch_index or "5f405b5" not in branch_index
            or "DRAFT / HOLD" not in branch_index or "not copied" not in branch_index
            or any(f"Actual PR #{n}" not in branch_index for n in range(3,17))):
        raise ValueError("Reviewer timeline must show original and rejected-branch proofs")
    if ("No commits are backdated" not in provenance
            or "retains the **authentic Git ancestry**" not in provenance
            or "This index was written on 16 November 2026, after the experiments" not in trail
            or "**Retain M0; shadow-test M1" not in trail):
        raise ValueError("Curation provenance or decision-gate language missing")

    # Source-audited all original 18,292 PIT snapshots from the external
    # raw cache, without scoring TEST or fitting any new model. ZIP-only
    # reviewers can verify the self-consistent frozen receipt and rerun
    # the complete sweep if they independently redownload the source.
    prefix=json.loads((ROOT/"docs/FULL_500_PREFIX_AUDIT_RECEIPT.json").read_text())
    if (prefix["notebook_sha256"]!=EXPECTED_NOTEBOOK_SHA256
            or prefix["original_minute_forecasts_checked"]!=18292
            or prefix["checks_by_partition"]!={"train":10675,"validation":3781,"test":3836}
            or prefix["match_count"]!=500
            or prefix["eligible_minutes_with_shorter_than_five_minute_velocity_window"]!=2500
            or prefix["any_difference"] or prefix["scored_original_test_labels"]
            or prefix["trained_or_selected_any_model"]
            or prefix["received_at_time_verified"]
            or "18,292" not in report):
        raise ValueError("Frozen source-feature full prefix sweep evidence missing")

    # Reliability bands are fixed-bin diagnostic CIs on already opened
    # TEST forecasts; they are NOT a calibration layer or model update.
    bpath=ROOT/"research/cluster_reliability_bands.py"
    bspec=importlib.util.spec_from_file_location("vexil_fixed_bin_calibration",bpath)
    bmod=importlib.util.module_from_spec(bspec)
    bspec.loader.exec_module(bmod)
    bins=bmod.check()
    if (bins["minute_rows"]!=3836 or bins["series_or_singletons"]!=54
            or bins["draws"]!=5000 or bins["fixed_bins"]!=10
            or not bins["test_is_already_opened"] or bins["any_test_calibration_fit"]
            or bins["any_model_or_forecast_update"]
            or not (ROOT/"docs/CALIBRATION_FIXED_BIN_GROUPED_CI.md").is_file()):
        raise ValueError("Fixed-bin grouped calibration uncertainty audit failed")

    # The two source code experiments remain unmerged DRAFT/HOLD as
    # candidates. Package their actual original TRAIN-only receipts and
    # portable development-only model checkers for skeptical reviewers.
    cal_evidence=json.loads((ROOT/"research/CALIBRATION_FORWARD_RECEIPT.json").read_text())
    null_evidence=json.loads((ROOT/"research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json").read_text())
    cal_scores=cal_evidence["reused_validation"]
    null_scores=null_evidence["interaction_null_bootstrap"]["M1_minus_gold_time_null_logloss"]
    if (cal_evidence["inputs"]["test_games_read"]!=0
            or not cal_scores["M1_offset"]["ece10"]>cal_scores["M1_original"]["ece10"]
            or cal_scores["paired_comparison"]["series_bootstrap_95ci_logloss"][0]>=0
            or cal_scores["paired_comparison"]["series_bootstrap_95ci_logloss"][1]<=0
            or null_evidence["original_validation_or_test_outcomes_read"]
            or null_evidence["model_promotion_permitted"]
            or null_evidence["null_model"]!=["gold_k","minute10"]
            or not null_scores["percentile_ci_95"][0]<0<null_scores["percentile_ci_95"][1]):
        raise ValueError("Optional HOLD calibration/strong-null receipts falsely promoted")

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
            or "0.5429" not in report
            or "docs/CALIBRATION_BIAS_READOUT.md" not in (ROOT/"README.md").read_text()):
        raise ValueError("VALIDATION bias source and interpretation contract failed")

    # Supplemental post-TEST evaluation has its own frozen, reader-executable
    # validation path. It must never refit, adjust, or replace the main
    # 500-game experiment or claimed original TEST results.
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
    if "68 games overlap" not in (ROOT/"REPORT.md").read_text():
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
        raise ValueError("Historical 14-cell Colab execution receipt conflicts with science.")

    # A separate, private candidate-owned fresh Colab Run All on the
    # PRE-EDITORIAL 16-cell notebook, inspected from the authenticated Drive file.
    # Historical 14-cell receipt remains immutable; do not interpret score
    # parity as proof of cloud CSV byte equality or a fresh blind TEST.
    cloud16=json.loads((ROOT / "docs/COLAB_16CELL_RUN_RECEIPT.json").read_text())
    if (cloud16["status"]!="FRESH_GOOGLE_COLAB_16_OF_16_RUN_ALL_PASS_NUMERIC_SOURCE_PARITY"
            or cloud16["code_cells_total"]!=16
            or cloud16["code_cells_executed"]!=16
            or cloud16["execution_counts"]!=list(range(1,17))
            or cloud16["execution_errors"]!=0
            or cloud16["repo_frozen_16cell_notebook_sha256"]!=PRE_EDITORIAL_CLOUD_NOTEBOOK_SHA256
            or cloud16["scientific_code_sha256"]!=MODEL_CODE_SHA256
            or cloud16["appendix_source_sha256"]["PIT"]!=appendix["appendix_source_sha256"]["PIT"]
            or cloud16["appendix_source_sha256"]["report_crosswalk"]!="c1bd43c6da3a50bce21e6477a8400e77fa25b8643a5ff33c4dabebaf65ff5e36"
            or cloud16["api_calls"]!=510 or cloud16["cache_hits"]!=0
            or cloud16["matches_loaded"]!=500
            or cloud16["patch_match_counts"]!={"59":250,"60":250}
            or cloud16["split_minute_rows"]!={"train":10675,"validation":3781,"test":3836}
            or cloud16["all_minute_rows"]!=18292
            or cloud16["PIT_snapshots_checked"]!=18292
            or cloud16["scores_round6"]["M1_logloss"]!=0.504015
            or cloud16["scores_round6"]["M0_logloss"]!=0.516444
            or cloud16["cloud_csv_byte_equality_verified"]
            or cloud16["new_blind_TEST_claimed"]
            or cloud16["live_received_at_verified"]
            or "docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json" not in (ROOT/"REPORT.md").read_text()):
        raise ValueError("16-cell Colab receipt or honest evidence boundary is invalid")

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
    if "[−0.0304,+0.0014]" not in readme or "[−0.0304,+0.0014]" not in report:
        raise ValueError("README and report CI display does not match corrected forecasts.")
    # The historical P20 28-way interval belongs in the full experiment
    # register, not as defensive reviewer-facing narrative.
    register=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
    if ("adjusted 28-way 95% CI [-0.016929,+0.006434]" not in register
            or "P20" not in register):
        raise ValueError("Historical exploratory P20 provenance absent.")
    if "AI reviews are not independent human peer review" not in report:
        raise ValueError("Mandatory accurate AI-review disclosure missing.")
    if "https://github.com/sangtrx/vexil-dota2-assessment" in report:
        raise ValueError("Reviewer PDF links to retired snapshot repository.")
    for local_source in ("docs/EXPERIMENT_REGISTER.md",
                         "docs/DISCOVERY_PROVENANCE.md",
                         "docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json",
                         "docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json"):
        if local_source not in report:
            raise ValueError("Reviewer PDF must identify primary evidence: "+local_source)
    for local_source in ("docs/COLAB_COLD_RUN_RECEIPT.json",
                         "docs/ERROR_ANALYSIS.md"):
        if local_source not in readme:
            raise ValueError("README must reference archived evidence: "+local_source)
    if "https://github.com/" in report:
        raise ValueError("Standalone PDF relies on inaccessible private GitHub links.")
    # Detailed secondary November stress metrics belong in the supplement.
    # The main report still needs the overlap/uncertainty boundary.
    if ("68 games overlap" not in report
            or "both intervals contain zero" not in report
            or "not a test on an unseen patch" not in report
            or "further study details are in the private source repository, not the ZIP" not in report
            or "docs/FORWARD_100_STRESS.md" not in readme):
        raise ValueError("Report omitted material uncertainty or cohort scope")
    if "artifacts/forward_100_predictions.csv" not in (ROOT/"docs/FORWARD_100_STRESS.md").read_text():
        raise ValueError("Supplement omits the actual frozen 4,355-row forecast source")
    if ("Both primary paired 95% confidence intervals include zero" not in report
            or "The corrected TEST is not a fresh blind holdout" not in report):
        raise ValueError("Main paired uncertainty / already-opened TEST boundary omitted")

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
        "created_on": "2026-11-19",
        "report_pages": acceptance["pages"],
        "notebook_sha256": EXPECTED_REVIEWER_NOTEBOOK_SHA256,
        "frozen_original_notebook_sha256": EXPECTED_NOTEBOOK_SHA256,
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
        if not count or int(count.group(1)) < 188 or "OK" not in result.stderr:
            raise ValueError("Extracted ZIP test suite incomplete or not PASS: "+
                             result.stderr[-1500:])
    return {"path": str(DEST), "zip_sha256": sha(DEST.read_bytes()),
            "size_bytes": DEST.stat().st_size, "files": len(entries),
            "science_code_sha256_pinned": True, **acceptance}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
