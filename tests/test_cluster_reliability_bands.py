"""Original TEST bin uncertainty; no recalibration fit and no frozen CSV edit."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research import cluster_reliability_bands as audit


class FixedBinClusterUncertaintyTest(unittest.TestCase):
    def test_posthoc_fixed_bins_and_cluster_unit_are_frozen(self):
        data=audit.check()
        self.assertEqual(data["status"],"FIXED_BIN_GROUPED_RELIABILITY_POSTHOC_NO_FIT")
        self.assertEqual((data["games"],data["minute_rows"],
                          data["series_or_singletons"],data["fixed_bins"]),
                         (106,3836,54,10))
        self.assertFalse(data["any_test_calibration_fit"])
        self.assertFalse(data["any_model_or_forecast_update"])
        self.assertTrue(data["test_is_already_opened"])
        self.assertAlmostEqual(
            data["models"]["M1"]["ece_10bin_descriptive"],0.07501877151942367,places=12)
        m=data["models"]["M1"]["bins"][8]
        self.assertEqual(m["forecast_interval"],[.8,.9])
        self.assertGreater(m["observed_minus_predicted"],0.11)
        self.assertGreater(m["observed_minus_predicted_ci_95_series"][0],0.)
        self.assertFalse(m["thin_support_below_10_original_groups"])

    def test_reject_changed_forecast_source_before_resampling(self):
        with tempfile.TemporaryDirectory() as d:
            altered=Path(d)/"heldout.csv"
            raw=audit.PRED.read_bytes()
            altered.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            with mock.patch.object(audit,"PRED",altered):
                with self.assertRaisesRegex(ValueError,"changed"):
                    audit.compute()


if __name__=="__main__":
    unittest.main()
