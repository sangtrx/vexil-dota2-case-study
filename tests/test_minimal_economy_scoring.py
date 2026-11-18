import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from minimal_economy_scoring import (
    relative_earned_share, sat_asinh, match_equal_weights,
    BASE,NEW,INPUTS,MODELS, grouped_delta,
)


class MinimalEconomyContracts(unittest.TestCase):
    def test_no_unregistered_model_search(self):
        self.assertEqual(NEW,("E_SHARE1","SAT_ASINH3","MATCH_EQUAL"))
        self.assertEqual(len(MODELS),6)
        self.assertEqual([len(INPUTS[x]) for x in NEW],[4,3,3])

    def test_gold_share_bounded_mirror_and_player_permutation(self):
        a=np.array([[2.,4.,7.]]*5)
        b=np.array([[1.,3.,5.]]*5)
        actual=relative_earned_share(a,b,2)
        self.assertAlmostEqual(actual,10./(35+25+1000),places=13)
        self.assertAlmostEqual(actual,-relative_earned_share(b,a,2),places=15)
        np.testing.assert_allclose(actual,relative_earned_share(a[::-1],b[::-1],2),rtol=0,atol=1e-14)
        self.assertGreaterEqual(actual,-1)
        self.assertLessEqual(actual,1)

    def test_no_future_suffix_in_share(self):
        a=np.ones((5,4),dtype=float)
        b=np.ones((5,4),dtype=float)*2
        val=relative_earned_share(a,b,1)
        a[:,2:]=1e9
        b[:,2:]=1e8
        self.assertEqual(val,relative_earned_share(a,b,1))

    def test_asinh_odd_and_zero_time(self):
        frame=pd.DataFrame({"gold_k":[-3.,0.,3.],"minute10":[0.,0.,0.]})
        out=sat_asinh(frame)
        self.assertAlmostEqual(out.gold_asinh_3k.iloc[0],-out.gold_asinh_3k.iloc[2])
        np.testing.assert_allclose(out.gold_asinh_x_time,np.zeros(3),atol=0)

    def test_match_weights_do_not_count_forecast_rows_equally(self):
        # Scope is strictly 291 games/10675 rows, reject toy nonfrozen fit.
        with self.assertRaisesRegex(AssertionError,"Not frozen"):
            match_equal_weights(pd.DataFrame({"match_id":[1,1,2],"minute":[0,1,0]}))

    def test_real_291_match_weights_same_total_and_no_test_rows(self):
        from train_time_effect_ci import require_data
        data=require_data()
        self.assertEqual(set(data.partition),{"train"})
        self.assertEqual(len(data),10675)
        weights=match_equal_weights(data)
        check=(pd.DataFrame({"match_id":data.match_id,"weight":weights})
               .groupby("match_id").weight.sum().to_numpy())
        self.assertEqual(len(check),291)
        np.testing.assert_allclose(check,np.full(291,10675./291.),atol=1e-12,rtol=0)
        self.assertAlmostEqual(float(weights.sum()),10675.,places=8)
        self.assertGreater(float(np.ptp(weights)),0.)

    def test_game_average_cluster_ci_has_distinct_estimand(self):
        df=pd.DataFrame({
            "match_id":[10,10,20],
            "series_id":[11,11,22],
            "minute":[0,31,31],
            "ll_A":[.1,.1,.3],
            "ll_B":[.2,.2,.2],
            "br_A":[.01,.01,.09],
            "br_B":[.04,.04,.04],
        })
        draws=np.random.default_rng(20261118).integers(0,2,size=(5000,2))
        result=grouped_delta(df,"A","B",draws)
        self.assertAlmostEqual(result["delta_logloss"],-1/30,places=12)
        self.assertAlmostEqual(result["equal_match_delta_logloss"],0.,places=12)
        self.assertEqual(len(result["equal_match_95_series_interval_ll"]),2)
        self.assertLess(result["equal_match_95_series_interval_ll"][0],0.)
        self.assertGreater(result["equal_match_95_series_interval_ll"][1],0.)

    def test_invalid_negative_gold_not_permitted(self):
        with self.assertRaises(ValueError):
            relative_earned_share(np.full((5,2),-1.),np.ones((5,2)),1)

    def test_refuse_unnamed_or_malformed_bootstrap(self):
        with self.assertRaises(Exception):
            grouped_delta(pd.DataFrame({"x":[0]}),"A","B",np.zeros((5000,1),dtype=int))

if __name__=="__main__":
    unittest.main()
