"""Small deterministic checks on paired scoring and series dependence."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from research.forward_baseline_replication import paired_interval


class ExternalScoringContractTest(unittest.TestCase):
    def test_paired_benefit_is_not_per_minute_independence(self):
        data=pd.DataFrame({
            "match_id":[1,1,2,2,3,3],
            "series_id":[111,111,111,111,222,222],
            "minute":[0,1,0,1,0,1],
            "logloss_model":[0.1]*6,
            "logloss_baseline":[0.2]*6
        })
        x=paired_interval(data,"logloss",unit="match_id")
        y=paired_interval(data,"logloss",unit="series_id")
        self.assertEqual(x["clusters"],3)
        self.assertEqual(y["clusters"],2)
        for out in (x,y):
            self.assertAlmostEqual(out["delta"],-.1)
            self.assertAlmostEqual(out["lo"],-.1)
            self.assertAlmostEqual(out["hi"],-.1)

    def test_phase_interval_keeps_exact_loss_weights(self):
        data=pd.DataFrame({
            "match_id":[1,1,1,2],
            "series_id":[1,1,1,2],
            "minute":[0,1,2,0],
            "brier_model":[.2,.2,.2,.4],
            "brier_baseline":[.3,.3,.3,.3],
        })
        x=paired_interval(data,"brier")
        # Match1 contributes three predictions, match2 one: -0.05 average.
        self.assertEqual(x["matches"] if "matches" in x else x["clusters"],2)
        self.assertAlmostEqual(x["delta"],-.05)
        self.assertLess(x["lo"],x["hi"])

if __name__=="__main__":
    unittest.main()
