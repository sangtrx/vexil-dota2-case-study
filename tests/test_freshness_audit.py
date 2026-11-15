"""Small offline contract checks for the exploratory freshness audit."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "research/freshness_innovation_audit.py"
SPEC = importlib.util.spec_from_file_location("freshness_audit", SRC)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class FreshnessAuditContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.csv_path = root / "p.csv"
        self.series_path = root / "series.json"
        self.series_path.write_text(json.dumps({
            "1": {"series_id": 10}, "2": {"series_id": 20}
        }), encoding="utf-8")
        self.rows = []
        for mid, y, probs in [
            (1, 1, [0.3, 0.5, 0.8, 0.9, 0.95, 0.96]),
            (2, 0, [0.7, 0.6, 0.4, 0.2, 0.1, 0.04]),
        ]:
            for t, prob in enumerate(probs):
                self.rows.append({
                    "match_id": mid, "minute": t, "p_model": prob,
                    "p_baseline": 0.5, "radiant_win": y
                })
        self.save()

    def save(self):
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "match_id", "minute", "p_model", "p_baseline", "radiant_win"
            ])
            writer.writeheader()
            writer.writerows(self.rows)

    def test_exact_pair_count_and_forecast_source(self):
        games, series, dims = MOD.load_data(
            self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False
        )
        self.assertEqual(dims["games"], 2)
        self.assertEqual(len(MOD.paired_observations(games, series, 1)["M1"]), 10)
        self.assertEqual(len(MOD.paired_observations(games, series, 5)["M1"]), 2)

    def test_identity_and_negative_control(self):
        result = MOD.analyze(
            self.csv_path, self.series_path, expected_sha=None,
            fixed_cohort=False, draws=101
        )
        fresh = result["lags"]["1"]["M1"]
        baseline = result["lags"]["1"]["M0"]
        self.assertGreater(fresh["brier_value"], 0)
        self.assertAlmostEqual(baseline["brier_value"], 0.0)
        self.assertAlmostEqual(
            fresh["brier_value"],
            fresh["innovation_energy"] + fresh["calibration_term"],
            places=12
        )
        self.assertEqual(result["lags"]["5"]["M1"]["n"], 2)
        self.assertEqual(result["lags"]["1"]["M1"]["series_bootstrap_95ci"],
                         MOD.analyze(self.csv_path, self.series_path, expected_sha=None,
                                     fixed_cohort=False, draws=101)["lags"]["1"]["M1"]["series_bootstrap_95ci"])

    def test_same_row_bridge_identity(self):
        result = MOD.analyze(self.csv_path, self.series_path,
                             expected_sha=None, fixed_cohort=False, draws=101)
        for lag in ("1", "2", "5"):
            model = result["lags"][lag]["M1"]
            comparison = result["lags"][lag]["same_row_model_comparison"]
            self.assertEqual(model["n"], comparison["n"])
            self.assertAlmostEqual(
                model["brier_value"],
                comparison["m1_fresh_gain_over_m0_brier"]
                + comparison["m1_stale_disadvantage_to_m0_fresh_brier"],
                places=12
            )
            self.assertAlmostEqual(
                model["logloss_value"],
                comparison["m1_fresh_gain_over_m0_logloss"]
                + comparison["m1_stale_disadvantage_to_m0_fresh_logloss"],
                places=12
            )

    def test_row_permutation_changes_no_score(self):
        left = MOD.analyze(self.csv_path, self.series_path, expected_sha=None,
                           fixed_cohort=False, draws=101)
        self.rows.reverse()
        self.save()
        right = MOD.analyze(self.csv_path, self.series_path, expected_sha=None,
                            fixed_cohort=False, draws=101)
        self.assertEqual(left["lags"], right["lags"])
        self.assertEqual(left["lags"]["1"]["M1"]["influence"]["games_positive"], 2)

    def test_series_id_zero_fail(self):
        self.series_path.write_text(json.dumps({
            "1": {"series_id": 0}, "2": {"series_id": 20}
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False)

    def test_inconsistent_outcomes_fail(self):
        self.rows[1]["radiant_win"] = 0
        self.save()
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False)

    def test_duplicate_or_invalid_probability_fail(self):
        self.rows.append(dict(self.rows[0]))
        self.save()
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False)
        self.rows.pop()
        self.rows[0]["p_model"] = 1.0
        self.save()
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False)

    def test_missing_series_fail(self):
        self.series_path.write_text(json.dumps({"1": {"series_id": 10}}), encoding="utf-8")
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha=None, fixed_cohort=False)

    def test_forecast_integrity_fail_closed(self):
        with self.assertRaises(ValueError):
            MOD.load_data(self.csv_path, self.series_path, expected_sha="deadbeef", fixed_cohort=False)


if __name__ == "__main__":
    unittest.main()
