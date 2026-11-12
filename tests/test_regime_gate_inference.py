"""Deterministic checks for the two-comparator series-bootstrap evaluator."""
import unittest

import numpy as np
import pandas as pd

from research.evaluate_regime_gate import two_way_simultaneous_interval


class GateInferenceContracts(unittest.TestCase):
    @staticmethod
    def fixture():
        # Four games, three series groups. Candidate wins every single row
        # by exactly 0.05 vs M0 and 0.02 vs M1.
        return pd.DataFrame({
            "match_id":[1,1,2,2,3,3,4,4],
            "series_id":[100,100,100,100,200,200,300,300],
            "minute":[0,1,0,1,0,1,0,1],
            "ll_base":[.5]*8,
            "ll_m1":[.47]*8,
            "ll_gate":[.45]*8,
        })

    def test_preserves_two_ordered_comparisons_and_series_groups(self):
        result=two_way_simultaneous_interval(self.fixture(),group="series")
        self.assertEqual(result.comparison.tolist(),[
            "GATE_minus_M0_gold_only","GATE_minus_M1_time_value"])
        self.assertEqual(result.clusters.tolist(),[3,3])
        self.assertAlmostEqual(result.difference.iloc[0],-.05)
        self.assertAlmostEqual(result.difference.iloc[1],-.02)
        self.assertTrue((result.simultaneous_95_hi<0).all())

    def test_match_level_grouping_counts_each_game(self):
        result=two_way_simultaneous_interval(self.fixture(),group="match")
        self.assertEqual(result.clusters.tolist(),[4,4])
        self.assertTrue((result.simultaneous_95_lo<=result.difference).all())
        self.assertTrue((result.simultaneous_95_hi>=result.difference).all())

if __name__=="__main__":
    unittest.main()
