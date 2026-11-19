"""Static report-to-figure packaging checks, no model rerun or network."""
from __future__ import annotations

import shutil
import struct
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReportDeliveryContractTest(unittest.TestCase):
    def test_full_experiment_register(self):
        import re
        text = (ROOT / "docs/EXPERIMENT_REGISTER.md").read_text(encoding="utf8")
        candidates = re.findall(r"^\| (P\d{2}) \|", text, flags=re.M)
        self.assertEqual(len(candidates), 28)
        self.assertEqual(set(candidates), {f"P{i:02d}" for i in range(1,29)})
        for pr in range(3,12):
            self.assertIn(f"| [#{pr}](https://github.com/sangtrx/vexil-dota2-win-probability/pull/{pr}) |", text)
        self.assertIn("https://github.com/sangtrx/vexil-dota2-win-probability/pull/", text)
        for phrase in ("0/28", "previously inspected", "M4", "S2",
                       "stage gate", "24,126", "not a second", "[-0.016929,+0.006434]"):
            self.assertIn(phrase.lower(),text.lower())

    def test_fable_handoff_truth_and_historical_provenance(self):
        report=(ROOT/"REPORT.md").read_text()
        readme=(ROOT/"README.md").read_text()
        register=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
        self.assertIn("[−0.0304,+0.0014]",report)
        self.assertIn("[−0.0304,+0.0014]",readme)
        self.assertIn("adjusted 28-way 95% CI [-0.016929,+0.006434]",register)
        self.assertIn("P20",register)
        self.assertIn("docs/EXPERIMENT_REGISTER.md",report)
        self.assertIn("**Time spent:** Approximately **10 hours of active work**",report)
        self.assertIn("**Assistance disclosure:**",report)
        self.assertIn("Claude Sonnet and Fable AI conducted read-only critiques",report)
        self.assertIn("AI reviews are not independent human peer review",report)
        self.assertIn("No third-party Dota predictor was copied",report)
        self.assertIn("docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json",report)
        self.assertNotIn("https://github.com/",report)
        self.assertIn("docs/RESEARCH_DECISION_TRAIL.md",readme)
        self.assertIn("docs/CURATION_PROVENANCE.md",readme)

    def test_handoff_test_scope_does_not_have_a_stale_exact_count(self):
        self.assertIn("181 offline checks",(ROOT/"README.md").read_text())
        self.assertIn("181 offline unit/contract checks",
                      (ROOT/"SUBMISSION_PACKAGE_README.md").read_text())

    def test_local_setup_does_not_promise_unsupported_future_python_versions(self):
        readme=(ROOT/"README.md").read_text()
        package=(ROOT/"SUBMISSION_PACKAGE_README.md").read_text()
        self.assertIn("Local Python 3.12 (verified with exact pins)",readme)
        self.assertIn("python3.12 -m venv .venv",readme)
        self.assertIn("Python 3.12 (verified)",package)
        self.assertNotIn("Local Python 3.11+",readme)

    def test_fresh_kernel_full_replay_has_exact_forecasts_and_report_figures(self):
        import hashlib
        import json
        receipt=json.loads((ROOT/"docs/FULL_NOTEBOOK_REPLAY_RECEIPT.json").read_text())
        self.assertEqual(receipt["executed_code_cells"],14)
        self.assertEqual(receipt["cell_execution_errors"],0)
        self.assertTrue(receipt["zero_http_calls"])
        self.assertEqual(receipt["cache_hits"],500)
        self.assertTrue(receipt["jupyter_kernel_is_controller_python"])
        self.assertEqual(receipt["split_minute_rows"],
                         {"train":10675,"validation":3781,"test":3836})
        self.assertEqual(len(receipt["validation_model_scores"]),4)
        self.assertAlmostEqual(receipt["validation_model_scores"]["M1_time_value"]["logloss"],
                               0.519713962581423,places=11)
        self.assertAlmostEqual(receipt["heldout_scores"]["logloss"]["M1"],
                               0.504014697253528,places=11)
        self.assertTrue(receipt["local_fresh_kernel_test_csv_byte_parity_verified"])
        self.assertTrue(receipt["report_figures_byte_equal_to_notebook_outputs"])
        self.assertFalse(receipt["cloud_csv_byte_parity_claimed"])
        self.assertEqual(
            receipt["original_test_predictions_sha256"],
            hashlib.sha256((ROOT/"artifacts/heldout_predictions.csv").read_bytes()).hexdigest())
        for generated,asset in (
            ("calibration.png","docs/figures/heldout_reliability.png"),
            ("time_value_scenarios.png","docs/figures/time_value_scenarios.png"),
            ("heldout_game_trajectory.png","docs/figures/heldout_game_trajectory.png")
        ):
            self.assertEqual(receipt["outputs_sha256"][generated],
                hashlib.sha256((ROOT/asset).read_bytes()).hexdigest())

    def test_research_question_does_not_conflate_gold_slope_and_information(self):
        report=(ROOT/"REPORT.md").read_text()
        readme=(ROOT/"README.md").read_text()
        self.assertIn("Does adding game time improve the probability",report)
        self.assertIn("not an effect caused by time",report)
        self.assertIn("no confirmed incremental benefit",report)
        self.assertNotIn("same gold lead equally informative",report)
        self.assertIn("not newly blind",readme)

    def test_historical_200_game_study_is_preserved_without_crowding_report(self):
        report=(ROOT/"REPORT.md").read_text()
        register=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
        supplement=(ROOT/"docs/FORWARD_100_STRESS.md").read_text()
        for fragment in ("200-match cohort","0.545075","0.533704","0.539850",
                         "0.18647","secondary and descriptive"):
            self.assertIn(fragment.lower(), register.lower())
        self.assertIn("0.00455 worse",report)
        self.assertIn("[−0.0037,+0.0109]",report)
        self.assertIn("68 games overlap",report)
        self.assertIn("docs/FORWARD_100_STRESS.md",report)
        self.assertIn("artifacts/forward_100_predictions.csv",supplement)
        self.assertIn("pre-correction",register.lower())

    def test_historical_200_cohort_and_private_source_are_explicit(self):
        report=(ROOT/"REPORT.md").read_text()
        readme=(ROOT/"README.md").read_text()
        register=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
        self.assertIn("strict pre-terminal",report)
        self.assertIn("before the later strict pre-terminal notebook correction",register)
        self.assertIn("no preregistered direct paired confidence interval",register)
        self.assertIn("Original research commits and branches are retained",report)
        self.assertNotIn("no reviewer access granted",report)
        self.assertIn("original github pr discussions remain in a separately private",readme.lower())
        self.assertIn("No original commit was rewritten or backdated",(ROOT/"HISTORY.md").read_text())
        self.assertNotIn("late-game failures",report)

    def test_colab_run_receipt_is_scoped_honestly(self):
        import hashlib
        import json
        receipt=json.loads((ROOT / "docs/COLAB_COLD_RUN_RECEIPT.json").read_text())
        notebook=json.loads((ROOT / "research/frozen_original_notebook_source.json").read_text())
        code="".join("".join(c["source"]) for i,c in enumerate(notebook["cells"])
                     if c["cell_type"]=="code" and i!=2)
        self.assertEqual(hashlib.sha256(code.encode()).hexdigest(),
                         receipt["scientific_code_sha256"])
        self.assertEqual(receipt["code_cells_executed"],14)
        self.assertEqual(receipt["execution_errors"],0)
        self.assertEqual(receipt["cache_hits"],0)
        self.assertEqual(receipt["matches_loaded"],500)
        self.assertEqual(receipt["test_minute_rows"],3836)
        self.assertFalse(receipt["cloud_csv_byte_equality_verified"])
        self.assertFalse(receipt["raw_notebook_sha_parity"])
        # The candidate-owned *current* notebook also completed an actual
        # 16/16 Google Colab run; its code and source fingerprints agree.
        newer=json.loads((ROOT/"docs/COLAB_16CELL_RUN_RECEIPT.json").read_text())
        self.assertEqual(newer["code_cells_executed"],16)
        self.assertEqual(newer["execution_counts"],list(range(1,17)))
        self.assertEqual(newer["execution_errors"],0)
        self.assertEqual(newer["matches_loaded"],500)
        self.assertEqual(newer["PIT_snapshots_checked"],18292)
        self.assertEqual(newer["api_calls"],510)
        self.assertEqual(newer["scientific_code_sha256"],receipt["scientific_code_sha256"])
        self.assertFalse(newer["cloud_csv_byte_equality_verified"])
        self.assertFalse(newer["new_blind_TEST_claimed"])
        self.assertIn("16-cell Colab Run All",(ROOT/"REPORT.md").read_text())

    def test_notebook_claim_matches_completed_cloud_receipt(self):
        import json
        nb = json.loads((ROOT / "live_dota2_win_probability.ipynb").read_text())
        opening = "".join(nb["cells"][0]["source"])
        closing = "".join(nb["cells"][25]["source"])
        receipt = json.loads((ROOT / "docs/COLAB_COLD_RUN_RECEIPT.json").read_text())
        self.assertIn("fresh Google Colab CPU Run all", opening)
        self.assertIn("Cloud-export CSV byte equality was not verified", opening)
        self.assertNotIn("not independently cold-run on cloud", opening)
        self.assertIn("paired interval includes zero", closing)
        self.assertEqual(receipt["code_cells_executed"], 14)
        self.assertEqual(receipt["execution_errors"], 0)
        self.assertFalse(receipt["cloud_csv_byte_equality_verified"])

    def test_pdf_cannot_mislead_on_private_links_or_posthoc_signs(self):
        report=(ROOT/"REPORT.md").read_text()
        self.assertNotIn("https://github.com/",report)
        self.assertNotIn("Pre-registered original TEST",report)
        self.assertNotIn("no reviewer access granted",report)
        self.assertIn("Both primary paired 95% confidence intervals include zero",report)
        self.assertIn("The corrected TEST is not a fresh blind holdout",report)
        self.assertIn("about 0.00455 worse",report)
        for file_path in ("docs/EXPERIMENT_REGISTER.md",
                          "docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json",
                          "docs/COLAB_16CELL_RUN_RECEIPT.json"):
            self.assertIn(file_path,report)
            self.assertTrue((ROOT/file_path).is_file())
        readme=(ROOT/"README.md").read_text()
        for file_path in ("docs/COLAB_COLD_RUN_RECEIPT.json","docs/ERROR_ANALYSIS.md"):
            self.assertIn(file_path,readme)
            self.assertTrue((ROOT/file_path).is_file())

    @unittest.skipUnless(shutil.which("pdftotext"),"poppler pdftotext not installed")
    def test_pdf_contains_current_md_scientific_and_disclosure_text(self):
        source=(ROOT/"REPORT.md").read_text()
        pdf=" ".join(subprocess.check_output(
            ["pdftotext","-layout",str(ROOT/"REPORT.pdf"),"-"],text=True
        ).split())
        for snippet in ("19 November 2026","286 mature TRAIN games","143 seconds",
                        "18,292","1/4 folds","[−0.0304,+0.0014]",
                        "0.1028","0.1074 (worse)","63/106 Radiant-winning games",
                        "16-code-cell notebook","No third-party Dota predictor was copied"):
            self.assertIn(snippet,source)
            self.assertIn(snippet,pdf)

    def test_later_report_discloses_phase_and_calibration_negative_results(self):
        report=(ROOT/"REPORT.md").read_text()
        supplement=(ROOT/"docs/FORWARD_100_STRESS.md").read_text()
        self.assertIn("early 0–9-minute",supplement)
        self.assertIn("The original TEST 30+ Brier point estimate",supplement)
        self.assertIn("Neither is a confirmed",supplement)
        self.assertIn("removing one league reverses the gain",report)
        self.assertIn("68 games overlap",report)
        self.assertIn("both intervals contain zero",report)
        self.assertIn("not a test on an unseen patch",report)
        self.assertIn("Brier score is about 0.00455 worse",report)
        self.assertIn("0.0559 to 0.0680",report)

    def test_reviewer_text_matches_scientific_boundaries(self):
        import json
        nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        text="\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"]=="markdown")
        report=(ROOT/"REPORT.md").read_text()
        readme=(ROOT/"README.md").read_text()
        guide=(ROOT/"SUBMISSION_PACKAGE_README.md").read_text()
        self.assertIn("strictly before match end",text)
        self.assertIn("corrected terminal boundary",text)
        self.assertIn("60*t < duration",text)
        self.assertIn("strict pre-terminal",report)
        self.assertIn("10 hours",text)
        self.assertIn("10 hours",report)
        self.assertIn("candidate's time estimate",guide)
        self.assertIn("106",report)
        self.assertIn("3,836",readme)
        self.assertIn("3,836",guide)

    def test_notebook_all_executed_and_only_definitions_cell_has_no_output(self):
        import json
        nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        cells=nb["cells"]
        code=[(i,c) for i,c in enumerate(cells) if c["cell_type"]=="code"]
        self.assertEqual(len(code),16)
        self.assertTrue(all(c.get("execution_count") is not None for i,c in code))
        self.assertEqual([i for i,c in code if not c.get("outputs")],[4])
        self.assertEqual(sum(bool(c.get("outputs")) for i,c in code),15)
        self.assertIn("16 executed code cells",(ROOT/"SUBMISSION_PACKAGE_README.md").read_text())
        self.assertIn("All have saved outputs except the original",(
            ROOT/"SUBMISSION_PACKAGE_README.md").read_text())

    def test_trajectory_figure_matches_saved_notebook_output_byte_for_byte(self):
        import base64
        import json
        import hashlib
        nb = json.loads((ROOT / "live_dota2_win_probability.ipynb").read_text())
        cell = nb["cells"][20]
        self.assertIn('show_embedded_figure(fig, "heldout_game_trajectory.png")',
                      "".join(cell["source"]))
        figures = [output["data"]["image/png"] for output in cell["outputs"]
                   if "image/png" in output.get("data", {})]
        self.assertGreaterEqual(len(figures), 2)
        encoded = figures[-1]
        original = base64.b64decode("".join(encoded) if isinstance(encoded, list)
                                    else encoded)
        exported = (ROOT / "docs/figures/heldout_game_trajectory.png").read_bytes()
        self.assertEqual(hashlib.sha256(original).digest(),
                         hashlib.sha256(exported).digest())
        self.assertEqual(original, exported)

    def test_report_figures_and_rendered_pdf_are_present(self):
        markdown=(ROOT/"REPORT.md").read_text()
        for relative in ("docs/figures/heldout_reliability.png",
                         "docs/figures/time_value_scenarios.png",
                         "docs/figures/train_interaction_vs_additive_null.png",
                         "docs/figures/phase_error_audit.png"):
            self.assertIn("]("+relative+")",markdown)
            source=(ROOT/relative).read_bytes()
            self.assertEqual(source[:8],bytes([137,80,78,71,13,10,26,10]))
            width,height=struct.unpack(">II",source[16:24])
            self.assertGreater(width,600)
            self.assertGreater(height,400)
            self.assertGreater(len(source),25000)
        self.assertIn("**Decision.**",markdown)
        self.assertIn("**Assistance disclosure:**",markdown)
        self.assertIn("**Time spent:**",markdown)
        self.assertIn("no confirmed incremental benefit",markdown)
        self.assertIn("0/28",(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text())
        self.assertTrue((ROOT/"REPORT.pdf").read_bytes().startswith(b"%PDF-"))
        if shutil.which("pdfinfo"):
            info=subprocess.check_output(["pdfinfo",str(ROOT/"REPORT.pdf")],text=True)
            pages=[int(x.split(":",1)[1]) for x in info.splitlines() if x.startswith("Pages:")]
            self.assertEqual(len(pages),1)
            self.assertLessEqual(pages[0],4)
        if shutil.which("pdfinfo"):
            annotations=subprocess.check_output(["pdfinfo","-url",str(ROOT/"REPORT.pdf")],text=True)
            self.assertNotIn("file:///",annotations)
            self.assertNotIn("github.com/sangtrx/",annotations)
        if shutil.which("pdfimages"):
            listings=subprocess.check_output(["pdfimages","-list",str(ROOT/"REPORT.pdf")],text=True)
            image_lines=[x for x in listings.splitlines() if x.lstrip()[:1].isdigit()]
            self.assertGreaterEqual(len(image_lines),4)

if __name__ == "__main__":
    unittest.main()
