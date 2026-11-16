"""Portable evidence tests for author-controlled original 500-game prefix sweep."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from research.full_500_prefix_audit import (
    ROOT, RECEIPT, SCIENCE_SHA, SPLIT_SHA, compare_features,
    feature_only_prefix,
)


class FullCohortPrefixAuditContractTest(unittest.TestCase):
    def test_receipt_has_every_frozen_original_forecast_without_new_test_fit(self):
        z=json.loads(RECEIPT.read_text())
        self.assertEqual(z["notebook_sha256"],SCIENCE_SHA)
        self.assertEqual(z["split_sha256"],SPLIT_SHA)
        self.assertEqual(z["status"],"AUTHOR_CONTROLLED_ORIGINAL_500_FULL_MINUTE_PIT_AUDIT")
        self.assertEqual(z["match_count"],500)
        self.assertEqual(z["original_minute_forecasts_checked"],18292)
        self.assertEqual(z["checks_by_partition"],
                         {"train":10675,"validation":3781,"test":3836})
        self.assertEqual(z["eligible_minutes_with_shorter_than_five_minute_velocity_window"],2500)
        self.assertFalse(z["any_difference"])
        self.assertFalse(z["trained_or_selected_any_model"])
        self.assertFalse(z["scored_original_test_labels"])
        self.assertFalse(z["received_at_time_verified"])
        self.assertFalse(z["original_raw_json_in_reviewer_zip"])

    def test_future_objects_and_terminal_label_are_removed_before_comparison(self):
        players=[]
        for side in (list(range(5)),list(range(128,133))):
            for slot in side:
                players.append({"player_slot":slot,
                                "kills_log":[{"time":20},{"time":121}]})
        m={"radiant_gold_adv":[0,100,200],
           "radiant_xp_adv":[0,100,300],
           "objectives":[{"time":45,"type":"building_kill"},
                         {"time":121,"type":"building_kill"}],
           "players":players,
           "radiant_win":True,
           "duration":240}
        x=feature_only_prefix(m,1)
        self.assertEqual(x["radiant_gold_adv"],[0,100])
        self.assertEqual(x["radiant_xp_adv"],[0,100])
        self.assertEqual(len(x["objectives"]),1)
        self.assertEqual(len(x["players"][0]["kills_log"]),1)
        self.assertEqual(x["duration"],-999999)
        self.assertFalse(x["radiant_win"])
        self.assertEqual(len(m["radiant_gold_adv"]),3)
        compare_features({"x":0.0},{"x":0.0},123,1)
        with self.assertRaisesRegex(ValueError,"Future feature leak"):
            compare_features({"x":1.},{"x":2.},123,1)


if __name__=="__main__":
    unittest.main()
