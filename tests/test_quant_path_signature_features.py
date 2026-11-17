"""Qualitative mechanism oracles and strict radiantd/dire causality invariants."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from quant_path_signature_features import prefix_features


class EconomicPathTests(unittest.TestCase):
    def test_clockwise_vs_anticlockwise_xp_gold_area(self):
        xpleads=prefix_features([0,0,1],[0,1,1])
        goldleads=prefix_features([0,1,1],[0,0,1])
        self.assertLess(xpleads[0],0)
        self.assertGreater(goldleads[0],0)
        self.assertGreater(xpleads[1],0)
        self.assertLess(goldleads[1],0)
        np.testing.assert_allclose(xpleads[:2],-goldleads[:2],rtol=0,atol=1e-14)

    def test_empty_history_warmup(self):
        a=prefix_features([2.],[3.])
        np.testing.assert_array_equal(a,[0.,0.,1.,0.])
        z=prefix_features([0.],[0.])
        np.testing.assert_array_equal(z,[0.,0.,0.,0.])

    def test_occupancy_vs_current_snapshot(self):
        longleading=prefix_features([1,1,2,3],[1,1,2,3])
        recentflip=prefix_features([-1,-1,-2,3],[1,1,2,3])
        self.assertGreater(longleading[2],recentflip[2])

    def test_underwater_burden_vs_smooth_growth(self):
        rising=prefix_features([0,1,2,3],[0,1,2,3])
        retreat=prefix_features([0,3,4,3],[0,1,2,3])
        self.assertEqual(rising[3],0.)
        self.assertLess(retreat[3],0.)

    def test_swap_odd_for_every_output(self):
        for g,x in [
            ([0,0,1],[0,1,1]),
            ([1,-2,-.3,2.5],[.1,2.,-1.,3.]),
            ([-4,-3,-2,-1],[2,-.5,-1.,2.]),
            ([0.,0.,0.],[0.,0.,0.]),
        ]:
            np.testing.assert_allclose(
                prefix_features(-np.array(g),-np.array(x)),
                -prefix_features(g,x),rtol=0,atol=1e-12)

    def test_suffix_cannot_affect_past(self):
        g=np.array([1.,2.,3.,4.,5.,6.])
        x=np.array([-1.,0.,1.,1.5,2.,4.])
        p=prefix_features(g[:4],x[:4])
        g[4:]=[99,1e6]
        x[4:]=[-99,-1e6]
        np.testing.assert_array_equal(prefix_features(g[:4],x[:4]),p)

    def test_invalid_length_and_nonfinite_inputs(self):
        with self.assertRaises(ValueError):
            prefix_features([],[])
        with self.assertRaises(ValueError):
            prefix_features([1,2],[1])
        with self.assertRaises(ValueError):
            prefix_features([1,float("nan")],[1,2])
        with self.assertRaises(ValueError):
            prefix_features([[1],[2]],[1,2])

    def test_fixed_window_older_history_irrelevant(self):
        g=np.asarray([float(i) for i in range(25)])
        x=np.sin(np.arange(25)*.2)
        p=prefix_features(g,x)
        poison_g=g.copy(); poison_x=x.copy()
        poison_g[:-11]=1e5
        poison_x[:-11]=-1e5
        np.testing.assert_array_equal(prefix_features(poison_g,poison_x),p)

if __name__=="__main__":
    unittest.main()
