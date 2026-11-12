"""No-network tests of the single stage-shrinkage hypothesis."""
import unittest
import numpy as np

from research.regime_gate import gate, weight


class StageGateContracts(unittest.TestCase):
    def test_registered_boundary_values(self):
        x=np.array([0,1,9,10,11,15,19,20,21,50])
        expected=np.array([1,1,1,1,.9,.5,.1,0,0,0])
        np.testing.assert_allclose(weight(x),expected,atol=1e-12)
        self.assertTrue(np.all(np.diff(weight(np.arange(60)))<=0))

    def test_never_changes_training_or_uses_future(self):
        p1=np.array([.2,.7,.3,.8])
        p0=np.array([.3,.5,.4,.9])
        t=np.array([0,10,15,35])
        p=gate(p1,p0,t)
        np.testing.assert_allclose(p,[.2,.7,.35,.9])
        self.assertTrue(np.all((p>=0)&(p<=1)))

    def test_swapped_team_probability_complements(self):
        p1=np.array([.1,.3,.9])
        p0=np.array([.2,.7,.6])
        t=np.array([5,14,30])
        original=gate(p1,p0,t)
        flipped=gate(1-p1,1-p0,t)
        np.testing.assert_allclose(original+flipped,1.)

    def test_gate_logloss_obeys_probability_convexity(self):
        # Jensen's inequality holds rowwise for binary log loss.
        p0=np.array([.1,.7,.25,.91,.5])
        p1=np.array([.4,.6,.8,.3,.8])
        minutes=np.array([5,11,15,19,35])
        y=np.array([1,0,1,0,1])
        out=gate(p1,p0,minutes)
        w=weight(minutes)
        ll=lambda q: -(y*np.log(q)+(1-y)*np.log1p(-q))
        self.assertTrue(np.all(ll(out)<=w*ll(p1)+(1-w)*ll(p0)+1e-12))

    def test_bad_forecasts_fail_closed(self):
        with self.assertRaises(ValueError):
            gate(np.array([np.nan]),np.array([.5]),np.array([10]))
        with self.assertRaises(ValueError):
            gate(np.array([1.1]),np.array([.5]),np.array([10]))
        with self.assertRaises(ValueError):
            gate(np.array([.5]),np.array([.5]),np.array([-1]))
        with self.assertRaises(ValueError):
            gate(np.array([.5]),np.array([.5]),np.array([10.5]))

if __name__=="__main__":
    unittest.main()
