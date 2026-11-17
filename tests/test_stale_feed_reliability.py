"""Stale feed invariants: single-match, lagged prefix, no peeking and mirror."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from stale_feed_reliability import lagged_views


class StaleFeed(unittest.TestCase):
    def setUp(self):
        self.df=pd.DataFrame({
            "match_id":[10]*4+[20]*3,
            "minute":[0,1,2,3,0,1,2],
            "minute10":[0,.1,.2,.3,0,.1,.2],
            "gold_k":[.1,.4,.9,1.4,-.2,-.7,-.9]})
        self.df["gold_x_time"]=self.df.gold_k*np.log1p(self.df.minute10)
        self.p=np.array([.50,.55,.6,.65,.48,.4,.35])

    def test_zero_delay_identity(self):
        x,held,short=lagged_views(self.df,self.p,0)
        np.testing.assert_array_equal(x.gold_k,self.df.gold_k)
        np.testing.assert_allclose(x.gold_x_time,self.df.gold_x_time,rtol=0,atol=1e-14)
        np.testing.assert_array_equal(held,self.p)
        self.assertEqual(short,0)

    def test_three_minute_old_never_lookahead_and_restart(self):
        x,held,short=lagged_views(self.df,self.p,3)
        np.testing.assert_array_equal(x.gold_k,[.1,.1,.1,.1,-.2,-.2,-.2])
        np.testing.assert_array_equal(held,[.5,.5,.5,.5,.48,.48,.48])
        self.assertEqual(short,6)

    def test_one_minute_old(self):
        x,held,short=lagged_views(self.df,self.p,1)
        np.testing.assert_allclose(x.gold_k,[.1,.1,.4,.9,-.2,-.2,-.7])
        np.testing.assert_allclose(held,[.5,.5,.55,.6,.48,.48,.4])
        self.assertEqual(short,2)

    def test_clock_feature_uses_current_time_and_old_gold(self):
        x,_,_=lagged_views(self.df,self.p,1)
        np.testing.assert_allclose(x.gold_x_time.to_numpy(),
                                   x.gold_k.to_numpy()*np.log1p(self.df.minute10.to_numpy()))

    def test_future_suffix_poison(self):
        first,held,_=lagged_views(self.df,self.p,1)
        changed=self.df.copy()
        changed.loc[3,"gold_k"]=9999
        changed.loc[3,"gold_x_time"]=9999*np.log1p(changed.loc[3,"minute10"])
        p=self.p.copy();p[3]=.999
        alt,hold2,_=lagged_views(changed,p,1)
        np.testing.assert_array_equal(first.gold_k.iloc[:3],alt.gold_k.iloc[:3])
        np.testing.assert_array_equal(held[:3],hold2[:3])

    def test_swap_sides_is_odd_for_features_and_complement_for_hold(self):
        original,held,_=lagged_views(self.df,self.p,1)
        mirrored=self.df.copy()
        mirrored["gold_k"]=-mirrored["gold_k"]
        mirrored["gold_x_time"]=-mirrored["gold_x_time"]
        negative,complement,_=lagged_views(mirrored,1-self.p,1)
        np.testing.assert_allclose(negative.gold_k,-original.gold_k)
        np.testing.assert_allclose(negative.gold_x_time,-original.gold_x_time)
        np.testing.assert_allclose(complement,1-held)

    def test_wrong_reference_interaction_rejected(self):
        broken=self.df.copy()
        broken["gold_x_time"]=broken.gold_k*broken.minute10
        with self.assertRaisesRegex(AssertionError,"feature contract"):
            lagged_views(broken,self.p,1)

    def test_invalid_inputs(self):
        bad=self.df.copy()
        bad.loc[1,"minute"]=3
        with self.assertRaises(ValueError):
            lagged_views(bad,self.p,1)
        with self.assertRaises(ValueError):
            lagged_views(self.df,self.p,-1)
        with self.assertRaises(ValueError):
            lagged_views(self.df,np.array([.2]),1)

if __name__=="__main__":
    unittest.main()
