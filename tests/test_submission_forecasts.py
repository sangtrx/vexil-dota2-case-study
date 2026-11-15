"""Submission-output contract: full saved forecasts match frozen notebook."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NOTEBOOK_SHA256 = "d6eea01465b2b2896ac3ed034427a09f4ed09e34a1e597712077813e2bbaa8e1"
EXPECTED_FORECAST_SHA256 = "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441"


class SubmissionForecastsTest(unittest.TestCase):
    def test_full_3836_predictions_attached_and_frozen(self):
        file = ROOT / "artifacts/heldout_predictions.csv"
        raw = file.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_FORECAST_SHA256)
        self.assertEqual(
            hashlib.sha256((ROOT / "live_dota2_win_probability.ipynb").read_bytes()).hexdigest(),
            EXPECTED_NOTEBOOK_SHA256)
        frame = pd.read_csv(file)
        self.assertEqual(
            list(frame.columns),
            ["match_id", "minute", "p_model", "p_baseline", "radiant_win"])
        self.assertEqual(len(frame), 3836)
        self.assertEqual(frame.match_id.nunique(), 106)
        self.assertEqual(frame[["match_id", "minute"]].duplicated().sum(), 0)
        self.assertTrue(frame.radiant_win.isin((0, 1)).all())
        for _, block in frame.groupby("match_id", sort=False):
            self.assertEqual(block.radiant_win.nunique(), 1)
            self.assertEqual(list(block.minute), list(range(len(block))))
        for key in ("p_model", "p_baseline"):
            p = frame[key].to_numpy(float)
            self.assertTrue(np.isfinite(p).all())
            self.assertTrue(((p >= 0) & (p <= 1)).all())

    def test_descriptive_calibration_from_frozen_forecasts(self):
        # Fixed ten equal-width bins. No refit, threshold search, or
        # test-set recalibration; descriptive only on correlated minute rows.
        frame = pd.read_csv(ROOT / "artifacts/heldout_predictions.csv")
        y = frame.radiant_win.to_numpy(float)
        self.assertEqual(len(y), 3836)
        self.assertAlmostEqual(float(y.mean()), 0.6045359749739312, places=12)
        for name, expected in (
            ("model", 0.07501877151942367),
            ("baseline", 0.08948284614037452),
        ):
            p = frame["p_" + name].to_numpy(float)
            bins = np.minimum(np.floor(10 * p).astype(int), 9)
            ece = sum(abs(float((y[mask] - p[mask]).sum()))
                      for b in range(10)
                      if (mask := (bins == b)).any()) / len(y)
            self.assertAlmostEqual(ece, expected, places=12)
        self.assertAlmostEqual(
            float(frame.p_model.mean()), 0.5428557631621745, places=12)

    def test_independent_scores_and_provenance(self):
        file = ROOT / "artifacts/heldout_predictions.csv"
        frame = pd.read_csv(file)
        y = frame.radiant_win.to_numpy(float)
        figures = {}
        for name in ("model", "baseline"):
            p = frame["p_" + name].to_numpy(float)
            v = np.clip(p, 1e-15, 1-1e-15)
            figures[name] = {
                "ll": float(np.mean(-(y * np.log(v) + (1-y) * np.log1p(-v)))),
                "br": float(np.mean((p-y)**2)),
            }
        self.assertAlmostEqual(figures["model"]["ll"], 0.504014697253528, places=13)
        self.assertAlmostEqual(figures["baseline"]["ll"], 0.5164444241748873, places=13)
        self.assertAlmostEqual(figures["model"]["br"], 0.1683528340689237, places=13)
        self.assertAlmostEqual(figures["baseline"]["br"], 0.1719121780368728, places=13)
        self.assertLess(figures["model"]["ll"], figures["baseline"]["ll"])
        self.assertLess(figures["model"]["br"], figures["baseline"]["br"])
        nb = json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        code = "\n".join("".join(x["source"]) for x in nb["cells"] if x["cell_type"]=="code")
        self.assertNotIn("artifacts/heldout_predictions.csv", code)
        self.assertIn("final_predictions.to_csv(ARTIFACT_DIR", code)


if __name__ == "__main__":
    unittest.main()
