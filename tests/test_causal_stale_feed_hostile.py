import sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from causal_stale_feed_hostile import staleness_frame, LAGS,POLICIES
from stale_feed_reliability import lagged_views


def tiny():
    f=pd.DataFrame({
       "match_id":[11]*4+[22]*4,
       "minute":[0,1,2,3]*2,
       "minute10":[0.,.1,.2,.3]*2,
       "gold_k":[1.,2.,3.,4.,-1.,-2.,-3.,-4.]
    })
    f["gold_x_time"]=f.gold_k*np.log1p(f.minute10)
    from quant_bible_path_risk_train_only import prefix_path_features
    for col in ("adverse_excursion10_k","signed_realized_vol10_k","directional_efficiency10"):
        f[col]=0.
    for i,row in f.iterrows():
        g=f.loc[f.match_id==row.match_id].gold_k.to_numpy()[:int(row.minute)+1]
        for col,x in zip(("adverse_excursion10_k","signed_realized_vol10_k","directional_efficiency10"),prefix_path_features(g)):
            f.loc[i,col]=x
    return f


class CausalLateFeed(unittest.TestCase):
    def test_prior_reproduced_lookahead_at_unavailable_minutes(self):
        f=tiny().iloc[:4].reset_index(drop=True)
        fresh=np.array([.52,.54,.56,.58])
        wrong_gold,wrong_hold,n=lagged_views(f,fresh,3)
        self.assertEqual(n,3)
        np.testing.assert_allclose(wrong_gold.gold_k.iloc[:3].to_numpy(),[1.,1.,1.])
        np.testing.assert_allclose(wrong_hold[:3],[.52,.52,.52])
        # These are WRONG for true delay=3, so the new state must be missing.
        correct,pointer,available=staleness_frame(f,3)
        np.testing.assert_array_equal(available,[False,False,False,True])
        np.testing.assert_array_equal(pointer,[-1,-1,-1,0])
        self.assertEqual(correct.gold_k.iloc[3],1.)

    def test_match_reset_and_no_future(self):
        f=tiny()
        lagged,pointer,ready=staleness_frame(f,3)
        np.testing.assert_array_equal(pointer,[-1,-1,-1,0,-1,-1,-1,4])
        np.testing.assert_array_equal(ready,[False,False,False,True]*2)
        self.assertEqual(lagged.gold_k.iloc[7],-1.)

    def test_zero_lag_parity_all_model_inputs(self):
        f=tiny()
        x,p,ready=staleness_frame(f,0)
        self.assertTrue(ready.all())
        np.testing.assert_array_equal(p,np.arange(len(f)))
        for col in ("gold_k","minute10","gold_x_time",
                    "adverse_excursion10_k","signed_realized_vol10_k",
                    "directional_efficiency10"):
            np.testing.assert_allclose(x[col].to_numpy(float),f[col].to_numpy(float),
                                      rtol=0,atol=1e-12)

    def test_future_suffix_poison_changes_no_already_ready_earlier_view(self):
        f=tiny()
        old,_,ready=staleness_frame(f,1)
        mutated=f.copy()
        mutated.loc[mutated.minute>=3,"gold_k"]=np.array([100000.,-100000.])
        mutated["gold_x_time"]=mutated.gold_k*np.log1p(mutated.minute10)
        # Keep current path-derived source artificially stale at future
        # positions; the model only receives gold history to s=t-lag.
        new,_,ready_new=staleness_frame(mutated,1)
        self.assertTrue(np.array_equal(ready,ready_new))
        for idx in (1,2,5,6):
            self.assertAlmostEqual(old.loc[idx,"gold_k"],new.loc[idx,"gold_k"])
            self.assertAlmostEqual(old.loc[idx,"gold_x_time"],new.loc[idx,"gold_x_time"])

    def test_reject_unknown_lags_and_gaps(self):
        f=tiny()
        with self.assertRaises(ValueError):
            staleness_frame(f,2)
        broken=f.copy()
        broken.loc[1,"minute"]=3
        with self.assertRaises((AssertionError,ValueError)):
            staleness_frame(broken,1)

    def test_mirrored_gold_side_and_path_sign(self):
        f=tiny()
        mirror=f.copy()
        mirror["gold_k"]=-mirror.gold_k
        mirror["gold_x_time"]=-mirror.gold_x_time
        for col in ("adverse_excursion10_k",
                    "signed_realized_vol10_k","directional_efficiency10"):
            mirror[col]=-mirror[col]
        for lag in (0,1,3):
            x,p,ready=staleness_frame(f,lag)
            y,q,other=staleness_frame(mirror,lag)
            np.testing.assert_array_equal(ready,other)
            np.testing.assert_array_equal(p,q)
            for col in ("gold_k","gold_x_time",
                        "adverse_excursion10_k","signed_realized_vol10_k",
                        "directional_efficiency10"):
                np.testing.assert_allclose(x.loc[ready,col],-y.loc[ready,col],
                                          atol=1e-12,rtol=0)

    def test_registered_policies_only(self):
        self.assertEqual(LAGS,(1,3))
        self.assertEqual(POLICIES,("FRESH","CLOCK1","HOLD1","CLOCK3","HOLD3"))


if __name__=="__main__":
    unittest.main()
