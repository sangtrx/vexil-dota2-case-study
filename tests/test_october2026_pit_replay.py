"""Replay the entire October PIT receipt and catch the actual leakage class."""
import gzip
import json
import unittest

from research import october2026_pit_replay as pit
from research.posttest_temporal.collect_and_score import frozen_functions


class OctoberPointInTimeReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entry = json.loads(pit.COLLECTION.read_text())["accepted"][0]
        cls.match = json.loads(
            gzip.decompress((pit.RAW / f'{entry["match_id"]}.json.gz').read_bytes())
        )
        cls.snapshot = staticmethod(frozen_functions()["snapshot_features"])

    def test_all_7346_forecasts_reproduce_saved_source_receipt(self):
        actual = pit.audit()
        archived = json.loads(pit.RECEIPT.read_text())
        self.assertEqual(actual, archived)
        self.assertEqual(actual["prefix_checked_forecasts"], 7346)
        self.assertEqual(actual["feature_comparisons"], 73460)

    def test_future_economy_and_label_do_not_change_forecast(self):
        game = self.match
        minute = 9
        full = self.snapshot(game, minute)
        masked = pit.prefix_only(game, minute)
        self.assertNotEqual(masked["radiant_win"], game["radiant_win"])
        self.assertEqual(masked["duration"], -999999)
        self.assertTrue(pit.identical_features(full, self.snapshot(masked, minute)))

    def test_leakage_checker_rejects_changed_present_value(self):
        game = self.match
        minute = 9
        truncated = pit.prefix_only(game, minute)
        before = self.snapshot(truncated, minute)
        truncated["radiant_gold_adv"][minute] += 5000
        after = self.snapshot(truncated, minute)
        self.assertFalse(pit.identical_features(before, after))

    def test_field_checker_rejects_missing_and_changed_fields(self):
        self.assertFalse(pit.identical_features({"gold_k": 1}, {"gold_k": 2}))
        self.assertFalse(pit.identical_features({"gold_k": 1}, {"xp_k": 1}))
        self.assertTrue(pit.identical_features({"gold_k": float("nan")},
                                                {"gold_k": float("nan")}))


if __name__ == "__main__":
    unittest.main()
