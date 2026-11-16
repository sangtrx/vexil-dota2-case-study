"""Contract tests for original-TRAIN-only empirical game-state illustration."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from research import train_leader_state_empirical as study

ROOT = Path(__file__).resolve().parents[1]


class TrainLeaderStateScienceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = study.load_train()
        cls.result = study.evaluate()
        cls.by_cell = {
            (int(c["abs_lead_lower_k"]), c["minute"]): c
            for c in cls.result["cells"]
        }

    def test_only_291_original_train_outcomes(self):
        self.assertEqual(self.source.shape[0], 10675)
        self.assertEqual(self.source.match_id.nunique(), 291)
        self.assertTrue(self.source.partition.eq("train").all())
        self.assertEqual(len(self.by_cell), 6)
        self.assertEqual(self.result["fixed_grid"]["minutes"], [10, 20, 30])
        self.assertEqual(
            self.result["fixed_grid"]["absolute_gold_lead_k_half_open_bins"],
            [[2.0, 4.0], [5.0, 7.0]]
        )
        self.assertEqual(
            self.result["source"]["train_features_sha256"],
            "066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915"
        )

    def test_original_model_predictors_and_training_fits(self):
        self.assertEqual(study.FEATURES, {
            "M0_gold_only": ("gold_k",),
            "M1_time_value": ("gold_k", "minute10", "gold_x_time")
        })
        fits = study.original_train_fits(self.source)
        for m in fits.values():
            self.assertEqual(m["logistic"].C, 1.0)
            self.assertEqual(m["logistic"].random_state, 20261113)
        # Compare the original frozen TRAIN fit at the notebook's +2k
        # minute-10/minute-30 scientific scenario, not a new TEST score.
        scenarios = pd.DataFrame({
            "gold_k": [2.0, 2.0],
            "minute10": [1.0, 3.0],
            "gold_x_time": [2 * np.log1p(1), 2 * np.log1p(3)]
        })
        np.testing.assert_allclose(
            fits["M1_time_value"].predict_proba(
                scenarios[list(study.FEATURES["M1_time_value"])]
            )[:, 1],
            [0.6649891894445682, 0.5940371481769873], rtol=0, atol=1e-6
        )
        self.assertTrue(self.result["not_a_model_selection_gate"])
        self.assertFalse(self.result["any_validation_rows_read"])
        self.assertFalse(self.result["any_TEST_rows_read"])

    def test_exact_empirical_outcomes_fixed_cells(self):
        expected = {
            (2, 10): (66, 82, 68), (2, 20): (46, 69, 60), (2, 30): (11, 25, 24),
            (5, 10): (8, 9, 9), (5, 20): (25, 35, 33), (5, 30): (24, 30, 28)
        }
        for key, (k, n, clusters) in expected.items():
            entry = self.by_cell[key]
            self.assertEqual(entry["eventual_leader_wins"], k)
            self.assertEqual(entry["games"], n)
            self.assertEqual(entry["series_groups"], clusters)
            self.assertAlmostEqual(entry["observed_leader_win_fraction"], k/n)

    def test_cluster_intervals_reproducible_and_not_fake_independent_rows(self):
        for key, entry in self.by_cell.items():
            lo, hi = entry["series_cluster_percentile_95_exploratory"]
            self.assertLessEqual(lo, entry["observed_leader_win_fraction"])
            self.assertGreaterEqual(hi, entry["observed_leader_win_fraction"])
            self.assertGreater(hi-lo, 0)
            self.assertLessEqual(entry["series_groups"], entry["games"])
            self.assertAlmostEqual(
                entry["wilson_95_by_game_descriptive"][0],
                study.wilson_interval(
                    entry["eventual_leader_wins"], entry["games"]
                )[0],
            )
        self.assertEqual(self.result["source"]["bootstrap_draws_per_cell"], 5000)

    def test_empirical_conditional_predictions_are_in_sample_only(self):
        for entry in self.by_cell.values():
            for model in ("M0", "M1"):
                p = entry[f"{model}_training_fitted_mean_p_leader"]
                self.assertTrue(0 < p < 1)
        m = self.by_cell[(2, 30)]
        np.testing.assert_allclose(
            [m["M0_training_fitted_mean_p_leader"],
             m["M1_training_fitted_mean_p_leader"]],
            [0.657, 0.650], atol=0.002, rtol=0
        )
        self.assertTrue(self.result["not_causal"])

    def test_receipt_numeric_replay_and_figure(self):
        # The original TRAIN cohort, per-cell counts and scientific boundaries
        # must match exactly; minute floating point predictions may vary at
        # insignificant ulps across supported BLAS/scikit-learn builds.
        stored = json.loads(study.RECEIPT.read_text())
        for key in ("analysis_type", "selection_or_refit_using_TEST",
                    "any_validation_rows_read", "any_TEST_rows_read",
                    "not_causal", "not_a_model_selection_gate", "cohort",
                    "fixed_grid", "source", "limitations"):
            self.assertEqual(stored[key], self.result[key])
        self.assertEqual(len(stored["cells"]), len(self.result["cells"]))
        float_fields = (
            "observed_leader_win_fraction", "M0_training_fitted_mean_p_leader",
            "M1_training_fitted_mean_p_leader"
        )
        interval_fields = (
            "wilson_95_by_game_descriptive",
            "series_cluster_percentile_95_exploratory"
        )
        for saved, actual in zip(stored["cells"], self.result["cells"]):
            for k in ("minute", "abs_lead_lower_k", "abs_lead_upper_exclusive_k",
                      "games", "eventual_leader_wins", "series_groups"):
                self.assertEqual(saved[k], actual[k])
            for k in float_fields:
                self.assertAlmostEqual(saved[k], actual[k], delta=1e-7)
            for k in interval_fields:
                np.testing.assert_allclose(saved[k], actual[k], rtol=0, atol=1e-7)
        self.assertTrue(study.FIGURE.is_file())
        self.assertGreater(study.FIGURE.stat().st_size, 40_000)
        # No access to frozen TEST or validation artefacts is part of the script.
        source = (ROOT/"research/train_leader_state_empirical.py").read_text()
        self.assertNotIn("heldout_predictions", source)
        self.assertNotIn("validation_m0_m1_predictions", source)

    def test_do_not_rewrite_frozen_science_or_applicant_disclosure(self):
        self.assertEqual(
            study.source_hash(ROOT/"live_dota2_win_probability.ipynb"),
            study.MODEL_SOURCE_SHA256
        )
        self.assertEqual(
            study.source_hash(ROOT/"artifacts/heldout_predictions.csv"),
            "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"
        )
        report = (ROOT/"REPORT.md").read_text()
        self.assertIn("Approximately **10 hours of active work**", report)
        self.assertIn("**Assistance disclosure:**", report)
        self.assertIn("TRAIN-only", report)


if __name__ == "__main__":
    unittest.main()
