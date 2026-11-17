"""Forecast filtering: causal-prefix, symmetry, restart and event regressions."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from causal_forecast_filter import filter_match


class FilterInvariants(unittest.TestCase):
    def setUp(self):
        self.p = np.array([.51,.72,.44,.65,.54], dtype=float)
        self.ev = np.array([[0,0,0],[0,0,0],[1,0,0],[1,0,-1],[1,0,-1]], float)

    def test_initial_and_event_reset(self):
        s1, s2, flags = filter_match(self.p, self.ev)
        np.testing.assert_array_equal(flags, [False,False,True,True,False])
        self.assertEqual(s1[0], self.p[0])
        self.assertEqual(s2[0], self.p[0])
        np.testing.assert_allclose(s2[flags], self.p[flags], rtol=0, atol=1e-14)
        self.assertNotEqual(s1[1], self.p[1])

    def test_no_events_same_stream(self):
        zeros = np.zeros_like(self.ev)
        s1, s2, flags = filter_match(self.p, zeros)
        np.testing.assert_allclose(s1, s2, rtol=0, atol=0)
        self.assertFalse(flags.any())

    def test_radiant_dire_mirror(self):
        a, b, flags = filter_match(self.p, self.ev)
        c, d, mirrored_flags = filter_match(1-self.p, -self.ev)
        np.testing.assert_array_equal(flags,mirrored_flags)
        np.testing.assert_allclose(c,1-a,rtol=0,atol=1e-14)
        np.testing.assert_allclose(d,1-b,rtol=0,atol=1e-14)

    def test_suffix_poison_cannot_change_earlier_output(self):
        s1, s2, _ = filter_match(self.p,self.ev)
        p2=self.p.copy();p2[3:]=[.999,.001]
        e2=self.ev.copy();e2[3:]=[[-200,99,100],[90,-100,400]]
        a,b,_=filter_match(p2,e2)
        np.testing.assert_array_equal(s1[:3],a[:3])
        np.testing.assert_array_equal(s2[:3],b[:3])

    def test_restart_and_short_prefix(self):
        a,b,flag=filter_match(np.array([.4]),np.zeros((1,3)))
        np.testing.assert_array_equal(a,[.4])
        np.testing.assert_array_equal(b,[.4])
        self.assertFalse(flag.any())
        a,b,_=filter_match(self.p,self.ev)
        x,y,_=filter_match(self.p,self.ev)
        np.testing.assert_array_equal(a,x)
        np.testing.assert_array_equal(b,y)

    def test_bad_inputs_fail_closed(self):
        for p,ev in [
            (np.array([0.,.2]),np.zeros((2,3))),
            (np.array([.3,np.nan]),np.zeros((2,3))),
            (np.array([.3,.5]),np.zeros((1,3))),
            (np.array([.3,.5]),np.full((2,3),np.inf)),
        ]:
            with self.assertRaises(ValueError):
                filter_match(p,ev)

if __name__ == "__main__":
    unittest.main()
