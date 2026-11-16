"""Offline tests of original-development, as-of-mature label sensitivity."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from research import mature_label_validation_audit as audit


class MatureLabelValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(audit.RECEIPT.read_text())

    def test_only_dev_matches_and_all_original_snapshots(self):
        z = audit.read_development()
        self.assertEqual(len(z), 14456)
        self.assertEqual(z.match_id.nunique(), 394)
        source = pd.read_csv(audit.SPLIT)
        test_ids = set(source.loc[source.partition == "test", "match_id"])
        self.assertFalse(test_ids & set(z.match_id))
        self.assertEqual(z.partition.value_counts().to_dict(), {
            "train": 10675, "validation": 3781
        })

    def test_same_original_frozen_models_and_embargo_model_selection(self):
        audited = audit.verify()
        maturity = audited["maturity"]
        self.assertEqual(maturity["excluded_train_games"], 5)
        self.assertEqual(maturity["mature_train_games"], 286)
        self.assertEqual(maturity["max_estimated_train_result_overlap_seconds"], 1606)
        self.assertEqual(maturity["original_selected"], "M1_time_value")
        self.assertEqual(maturity["embargo_selected"], "M1_time_value")
        self.assertAlmostEqual(
            maturity["embargo_validation_scores"]["M1_time_value"]["logloss"],
            0.5202093300554129, places=11)
        self.assertAlmostEqual(
            maturity["embargo_validation_scores"]["M0_gold_only"]["logloss"],
            0.5329400778888694, places=11)

    def test_failed_change_to_gz_source_is_rejected_before_model_fit(self):
        with tempfile.TemporaryDirectory() as d:
            corrupted = Path(d) / "source.csv.gz"
            raw = audit.DEV.read_bytes()
            corrupted.write_bytes(raw[:-2] + bytes([raw[-2] ^ 1]) + raw[-1:])
            with mock.patch.object(audit, "DEV", corrupted):
                with self.assertRaisesRegex(ValueError, "tampered"):
                    audit.verify()
        self.assertEqual(audit.DEV.read_bytes(), raw)

    def test_senior_report_discloses_causal_and_calibration_nulls(self):
        report = (audit.ROOT / "REPORT.md").read_text()
        readme = (audit.ROOT / "README.md").read_text()
        for token in ("286 mature TRAIN games", "0.5202", "0.5329",
                      "[−0.0148,+0.0090]", "0.5197→0.5186",
                      "0.0492→0.0561", "No TEST recalibration"):
            self.assertIn(token, report)
        self.assertIn("does not call /proMatches", readme)
        self.assertIn("not a second blind evaluation", report)
        self.assertIn("docs/DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md", readme)

    def test_notebook_still_has_frozen_default_and_optional_discovery(self):
        notebook = json.loads(audit.NOTEBOOK.read_text())
        source4 = "".join(notebook["cells"][4]["source"])
        source5 = "".join(notebook["cells"][5]["source"])
        self.assertIn("def collect_matches(api, frozen=())", source4)
        self.assertIn('api.get("/proMatches"', source4)
        self.assertIn("matches, rejected = collect_matches(api, FROZEN_MATCH_IDS)", source5)
        self.assertIn("if frozen:", source4)

    def test_receipt_does_not_turn_validation_into_a_new_test(self):
        r = self.receipt
        self.assertEqual(r["status"], "POST_HOC_COMPLETION_EMBARGO_DEVELOPMENT_ONLY")
        self.assertTrue(r["sample_is_original_validation_previously_used_for_selection"])
        self.assertFalse(r["scored_original_TEST"])
        self.assertFalse(r["refit_original_frozen_TEST"])
        self.assertFalse(r["independent_prospective_or_blind_validation"])


if __name__ == "__main__":
    unittest.main()
