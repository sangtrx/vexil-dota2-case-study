"""Read-only uncertainty and temporal-source adversarial contracts."""
from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from research.league_and_boundary_stress import (
    timing_boundaries, league_stress,
)


class LeagueBoundaryStressTests(unittest.TestCase):
    @staticmethod
    def example_leagues():
        rows = []
        for league in (11,22,33):
            for game in (1,2):
                for minute in range(4):
                    y = (league + game) % 2
                    base = .35 if y else .65
                    m = base + .03 if league==22 else base - .03
                    rows.append(dict(match_id=league*100+game,minute=minute,
                                     radiant_win=y,p_model=m,
                                     p_baseline=base,leagueid=league))
        return pd.DataFrame(rows)

    @staticmethod
    def example_chronology():
        return pd.DataFrame([
            dict(match_id=1,partition="train",series_id=10,
                 start_time=1000,estimated_end_time=1300),
            dict(match_id=2,partition="train",series_id=11,
                 start_time=1200,estimated_end_time=2000),
            dict(match_id=3,partition="validation",series_id=12,
                 start_time=1900,estimated_end_time=2300),
            dict(match_id=4,partition="validation",series_id=13,
                 start_time=2000,estimated_end_time=2400),
            dict(match_id=5,partition="test",series_id=14,
                 start_time=2500,estimated_end_time=2900),
        ])

    def test_temporal_boundary_overlap_and_available_label_slack(self):
        out=timing_boundaries(self.example_chronology())
        self.assertEqual(out["train_to_validation"]["prior_estimated_not_finished"],1)
        self.assertEqual(out["train_to_validation"]["max_estimated_overlap_seconds"],100)
        self.assertEqual(out["train_to_validation"]["estimated_availability_slack_seconds"],-100)
        self.assertEqual(out["validation_to_test"]["prior_estimated_not_finished"],0)
        self.assertEqual(out["validation_to_test"]["estimated_availability_slack_seconds"],100)

    def test_rejects_identity_duplicates_series_leaks_and_reordered_time(self):
        a=self.example_chronology()
        wrong=a.copy()
        wrong.loc[4,"series_id"]=11
        with self.assertRaisesRegex(ValueError,"Series overlaps partitions"):
            timing_boundaries(wrong)
        wrong=a.copy()
        wrong.loc[4,"match_id"]=3
        with self.assertRaisesRegex(ValueError,"Duplicate match IDs"):
            timing_boundaries(wrong)
        wrong=a.copy()
        wrong.loc[4,"start_time"]=1500
        with self.assertRaisesRegex(ValueError,"Non-chronological"):
            timing_boundaries(wrong)

    def test_league_cluster_is_not_minute_row_bootstrap(self):
        f=self.example_leagues()
        a=league_stress(f,seed=31,draws=500)
        b=league_stress(f.sample(frac=1,random_state=8),seed=31,draws=500)
        self.assertEqual(a["leagues"],3)
        self.assertEqual(a["matches"],6)
        self.assertEqual(a["minutes"],24)
        self.assertEqual(a["league_game_counts"],{"11":2,"22":2,"33":2})
        for metric in ("logloss","brier"):
            x,y=a["effects"][metric],b["effects"][metric]
            self.assertAlmostEqual(x["minute_weighted_delta"],
                                   y["minute_weighted_delta"],places=13)
            self.assertTrue(np.allclose(x["league_cluster_percentile95"],
                                        y["league_cluster_percentile95"],atol=1e-12))
            self.assertEqual(x["bootstrap_draws"],500)
        f.loc[1,"minute"]=0
        with self.assertRaisesRegex(ValueError,"Duplicate forecast key"):
            league_stress(f,draws=500)

    def test_missing_leagues_and_cross_league_match_fail_closed(self):
        f=self.example_leagues()
        wrong=f.copy()
        wrong.loc[wrong.match_id==1101,"leagueid"]=0
        with self.assertRaisesRegex(ValueError,"Unknown league"):
            league_stress(wrong,draws=500)
        wrong=f.copy()
        wrong.loc[0,"leagueid"]=55
        with self.assertRaisesRegex(ValueError,"Game assigned to multiple"):
            league_stress(wrong,draws=500)


if __name__ == "__main__":
    unittest.main()
