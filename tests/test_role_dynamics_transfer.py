import sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from role_dynamics_transfer import (
    INPUTS_NEW, NEW, FITTED, ALL_MODELS,
    proper_for_prob, paired_series
)


class RoleEvaluationContract(unittest.TestCase):
    def test_exact_three_fitted_and_one_fixed_pool(self):
        self.assertEqual(NEW,("RANK3","COUPLING3","RANK_COUPLING6","CONSENSUS"))
        self.assertEqual(len(FITTED),7)
        self.assertEqual(len(ALL_MODELS),8)
        self.assertEqual([len(INPUTS_NEW[k]) for k in ("RANK3","COUPLING3","RANK_COUPLING6")],[6,6,9])

    def test_consensus_bounded_example(self):
        a=np.array([.2,.8])
        b=np.array([.6,.4])
        c=.5*a+.5*b
        np.testing.assert_allclose(c,[.4,.6],rtol=0,atol=1e-15)
        ll,br=proper_for_prob(np.array([0,1]),c)
        self.assertEqual(len(ll),2)
        self.assertGreater(float(br.mean()),0)

    def test_proper_rejects_invalid(self):
        with self.assertRaises(AssertionError):
            proper_for_prob(np.array([0,1]),[0,1])
        with self.assertRaises(AssertionError):
            proper_for_prob(np.array([0]),[float("nan")])

    def test_cluster_bootstrap_not_single_minute_rows(self):
        frame=pd.DataFrame({
            "match_id":[1,1,2,2],
            "series_id":[7,7,8,8],
            "minute":[0,31,0,31],
            "ll_X":[.3,.2,.5,.4],
            "ll_Y":[.4,.3,.4,.3],
            "br_X":[.1,.2,.3,.1],
            "br_Y":[.2,.3,.2,.3]})
        draw=np.zeros((5000,2),dtype=int)
        d=paired_series(frame,"X","Y",draw)
        self.assertEqual(d["series_bootstrap_95_ll"][0],-.1)
        self.assertEqual(d["series_bootstrap_95_ll"][1],-.1)

if __name__=="__main__":
    unittest.main()
