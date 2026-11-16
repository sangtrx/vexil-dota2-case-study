"""Frozen original 500-game TEST calibration-bias audit, no refit or API."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "vexil_calibration_bias",ROOT/"research/calibration_bias_sensitivity.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class CalibrationBiasOnFrozenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual=MOD.evaluate()

    def test_reconstructs_frozen_provenance_and_uncertainty(self):
        r=self.actual
        self.assertEqual(r["games"],106)
        self.assertEqual(r["minute_forecasts"],3836)
        self.assertEqual(r["series_or_singletons"],54)
        self.assertEqual(r["bootstrap_draws"],10000)
        self.assertTrue(r["no_calibration_fit_or_model_selection"])
        self.assertTrue(r["calibration_on_inspected_test_only"])
        self.assertAlmostEqual(r["observed_win_rate_game_weighted"],63/106,places=13)
        self.assertAlmostEqual(r["observed_win_rate_minute_weighted"],.6045359749739312,places=13)
        self.assertAlmostEqual(r["M0_mean_prediction_minus_outcome_minute"],-.062149527354278644,places=13)
        self.assertAlmostEqual(r["M1_mean_prediction_minus_outcome_minute"],-.06168021181175666,places=13)
        self.assertAlmostEqual(r["M1_mean_prediction_minus_outcome_equal_game"],-.05233050240395265,places=13)
        for metric in ("M0","M1"):
            for weight in ("minute","equal_game"):
                ci=r[f"{metric}_mean_prediction_minus_outcome_{weight}_95ci_series"]
                self.assertLess(ci[0],0)
                self.assertGreater(ci[1],0)

    def test_saved_result_reproduces_in_full_and_rejects_forgery(self):
        receipt=json.loads((ROOT/"docs/CALIBRATION_BIAS_RECEIPT.json").read_text())
        MOD.check(receipt,self.actual)
        tampered=json.loads(json.dumps(receipt))
        tampered["M1_mean_prediction_minus_outcome_minute_95ci_series"][0]-=.01
        with self.assertRaisesRegex(ValueError,"Calibration numerical receipt changed"):
            MOD.check(tampered,self.actual)
        forged=json.loads(json.dumps(receipt))
        forged["no_calibration_fit_or_model_selection"]=False
        with self.assertRaisesRegex(ValueError,"Calibration metadata receipt changed"):
            MOD.check(forged,self.actual)

    def test_point_bias_matches_independent_groupby_oracle(self):
        frame=pd.read_csv(ROOT/"artifacts/heldout_predictions.csv")
        y=frame.radiant_win.to_numpy(dtype=float)
        self.assertEqual(len(y),3836)
        self.assertEqual(frame.match_id.nunique(),106)
        for name,col in (("M0","p_baseline"),("M1","p_model")):
            raw=(frame[col].to_numpy(dtype=float)-y)
            self.assertAlmostEqual(float(np.mean(raw)),
                self.actual[f"{name}_mean_prediction_minus_outcome_minute"],places=13)
            per_game=frame.assign(residual=raw).groupby("match_id").residual.mean()
            self.assertAlmostEqual(float(per_game.mean()),
                self.actual[f"{name}_mean_prediction_minus_outcome_equal_game"],places=13)

    def test_series_bootstrap_matches_independent_groupby_oracle(self):
        # Build a separate pandas+NumPy oracle rather than reusing the
        # production audit's cluster sums or quantile helper.
        src=pd.read_csv(ROOT/"artifacts/heldout_predictions.csv")
        info=json.loads((ROOT/"docs/SERIES_GROUPS_TEST.json").read_text())
        def group(mid):
            sid=int(info[str(mid)]["series_id"])
            return "s"+str(sid) if sid>0 else "m"+str(mid)
        src["group"]=[group(x) for x in src.match_id]
        src["resid"]=src.p_model-src.radiant_win
        groups=src.groupby("group",sort=True)
        counts=groups.size().to_numpy()
        totals=groups.resid.sum().to_numpy()
        self.assertEqual(len(counts),54)
        draw=np.random.default_rng(20261116).integers(
            0,len(counts),size=(10000,len(counts)))
        series_samples=totals[draw].sum(axis=1)/counts[draw].sum(axis=1)
        expected=np.quantile(series_samples,[.025,.975])
        np.testing.assert_allclose(
            expected,
            self.actual["M1_mean_prediction_minus_outcome_minute_95ci_series"],
            rtol=0,atol=1e-13)

        by_game=src.groupby(["group","match_id"],sort=True).resid.mean().reset_index()
        per_series=by_game.groupby("group",sort=True)
        n_games=per_series.size().to_numpy()
        total_game_res=per_series.resid.sum().to_numpy()
        game_samples=total_game_res[draw].sum(axis=1)/n_games[draw].sum(axis=1)
        game_ci=np.quantile(game_samples,[.025,.975])
        np.testing.assert_allclose(
            game_ci,
            self.actual["M1_mean_prediction_minus_outcome_equal_game_95ci_series"],
            rtol=0,atol=1e-13)

    def test_rejects_changed_forecast_or_series_file(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"changed.csv"
            p.write_bytes(MOD.PRED.read_bytes()+b"\n")
            with patch.object(MOD,"PRED",p),self.assertRaisesRegex(
                ValueError,"Original frozen predictions or series"):
                MOD.evaluate()
            q=Path(temp)/"groups.json"
            q.write_text("{}\n")
            with patch.object(MOD,"GROUPS",q),self.assertRaisesRegex(
                ValueError,"Original frozen predictions or series"):
                MOD.evaluate()

    def test_no_claim_of_deployment_population_underprediction(self):
        text=(ROOT/"docs/CALIBRATION_BIAS_READOUT.md").read_text()
        report=(ROOT/"REPORT.md").read_text()
        self.assertIn("not a population calibration finding",text)
        self.assertIn("54 professional-series",text)
        self.assertIn("−0.1410,+0.0250",report)
        self.assertIn("63/106",report)
        self.assertIn("No TEST recalibration",text)


if __name__=="__main__":
    unittest.main()
