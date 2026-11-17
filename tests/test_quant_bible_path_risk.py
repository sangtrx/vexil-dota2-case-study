"""Regression checks for one TRAIN-only Quant Bible path hypothesis."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
import quant_bible_path_risk_train_only as q


class QuantBiblePathTests(unittest.TestCase):
    def test_synthetic_adverse_excursion_and_volatility(self):
        v = q.prefix_path_features(np.array([0., 1., 0.5]))
        self.assertAlmostEqual(v[0], 0.5)
        self.assertAlmostEqual(v[1], np.sqrt((1.**2 + 0.5**2)/2))
        self.assertAlmostEqual(v[2], 0.5/(1.5 + 1e-6))
        z = q.prefix_path_features(np.array([0.]))
        np.testing.assert_array_equal(z, [0., 0., 0.])

    def test_all_partial_prefixes_and_mirrored_sides(self):
        rng = np.random.default_rng(20261113)
        for _ in range(25):
            gold = rng.normal(size=55).cumsum()
            for t in range(len(gold)):
                v = q.prefix_path_features(gold[:t+1])
                np.testing.assert_allclose(
                    v, q.prefix_path_features(
                        np.concatenate([gold[:t+1], np.full(23, 1e9)])[:t+1]),
                    atol=0, rtol=0,
                )
                np.testing.assert_allclose(
                    q.prefix_path_features(-gold[:t+1]), -v,
                    atol=1e-12, rtol=0,
                )

    def test_bad_or_future_invalid_input_rejected(self):
        for arr in ([], [float("nan")], [1., float("inf")], [[1., 2.]]):
            with self.assertRaises(ValueError):
                q.prefix_path_features(np.asarray(arr))

    def test_source_is_original_train_only_and_readout_matches_recompute(self):
        self.assertEqual(
            hashlib.sha256(
                (ROOT/"research/frozen_original_train_features.csv.gz").read_bytes()
            ).hexdigest(), "066a03d21b673dcd2d9cd82d027c38ba789489a32b8bb3f2de8271b3f6280915")
        x = json.loads((ROOT/"research/QUANT_BIBLE_PATH_RECEIPT.json").read_text())
        self.assertFalse(x["original_VAL_or_TEST_loaded"])
        self.assertTrue(x["no_new_model_selected_on_TEST"])
        self.assertFalse(x["predeclared_gate_met"])
        self.assertFalse(x["promote_into_original_submission"])
        self.assertEqual([x["oof_games"],x["oof_rows"],x["oof_series_or_singletons"]],
                         [137,5081,70])
        self.assertEqual(x["feature_prefix_audit"]["audited_prefixes"], 10675)
        self.assertEqual(x["feature_prefix_audit"]["mirror_symmetry_pass"], 10675)
        self.assertEqual(x, q.result_object())
        self.assertEqual((ROOT/"research/QUANT_BIBLE_PATH_READOUT.md").read_text(),
                         q.markdown_receipt(x))


if __name__ == "__main__":
    unittest.main()
