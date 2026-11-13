"""Offline adversarial contracts for development-only forward stability."""
from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from research.train_forward_stability import (
    FEATURES, PREEXISTING_FRACTIONS, FRACTIONS,
    safe_boundaries, compare_folds,
)


class ForwardStabilityContracts(unittest.TestCase):
    def test_audit_uses_exact_frozen_m0_m1_and_preexisting_cut_schedule(self):
        from test_notebook_contracts import N, source_at
        self.assertEqual(tuple(N["SETS"]["M0_gold_only"]),
                         FEATURES["M0_gold_only"])
        self.assertEqual(tuple(N["SETS"]["M1_time_value"]),
                         FEATURES["M1_time_value"])
        # This sequence already exists in the original development-item
        # fold calculation. No optimization against held-out results.
        self.assertIn("for f in (.52,.60,.75,.92)",source_at(12))
        self.assertEqual(PREEXISTING_FRACTIONS,(.52,.60,.75,.92))

    def test_series_boundaries_exclude_splitting_and_random_order(self):
        rows=[]
        for i in range(120):
            rows.append({"match_id":1000+i,"start_time":20000+500*i,
                         "series_id":100+i//3,"patch":59,"partition":"train"})
        a=pd.DataFrame(rows)
        x=safe_boundaries(a,PREEXISTING_FRACTIONS)
        y=safe_boundaries(a.sample(frac=1,random_state=7),
                          PREEXISTING_FRACTIONS)
        self.assertEqual(x,y)
        self.assertEqual(len(x),4)
        for cut in x:
            self.assertEqual(cut % 3,0)
        with self.assertRaises(ValueError):
            safe_boundaries(a,(.9,.5))
        with self.assertRaises(ValueError):
            safe_boundaries(a,(.4,.4))

    def test_forward_folds_exclude_heldout_and_keep_completed_labels(self):
        rows=[]
        for i in range(120):
            rows.append({"match_id":1000+i,"start_time":20000+500*i,
                         "series_id":100+i//3,"patch":59,
                         "partition":"train"})
        meta=pd.DataFrame(rows)
        frames=[]
        for r in rows:
            for minute in range(11):
                # Constant early labels would make logistic fit impossible,
                # so make balanced outcomes in each chronological window.
                winner=(r["match_id"]%7)<3
                frames.append({"match_id":r["match_id"],"minute":minute,
                               "source_duration":600,
                               "radiant_win":int(winner),
                               "gold_k":(0.4 if winner else -0.3)*minute,
                               "minute10":minute/10,
                               "gold_x_time":(0.4 if winner else -0.3)*minute*np.log1p(minute/10)})
        f=pd.DataFrame(frames)
        result=compare_folds(meta,f,PREEXISTING_FRACTIONS)
        self.assertEqual(len(result["folds"]),3)
        self.assertEqual(sum(x["evaluation_minutes"] for x in result["folds"]),
                         result["total_evaluation_minutes"])
        self.assertTrue(all(x["embargoed_prior_games"]>=0 for x in result["folds"]))
        for name in ("pooled_minute_weighted_delta_logloss",
                     "pooled_minute_weighted_delta_brier"):
            self.assertTrue(np.isfinite(result[name]))
        rogue=meta.copy()
        rogue.loc[1,"partition"]="test"
        with self.assertRaisesRegex(ValueError,"Non-train"):
            compare_folds(rogue,f)
        broken=f.copy()
        broken.loc[0,"source_duration"]=1
        with self.assertRaisesRegex(ValueError,"duration changed"):
            compare_folds(meta,broken)


if __name__=="__main__":
    unittest.main()
