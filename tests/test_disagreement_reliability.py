"""Causal fixed-score invariants; all model-fit/output checks run on TRAIN only."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from disagreement_reliability import risk_scores, wrong_decision, alert_budget


class DisagreementContract(unittest.TestCase):
    def setUp(self):
        self.m0=np.array([.2,.8,.7])
        self.m1=np.array([.3,.6,.7])
        self.q1=np.array([.5,.7,.6])

    def test_formula_strict(self):
        r=risk_scores(self.m0,self.m1,self.q1)
        np.testing.assert_allclose(r["disagreement"],[.2,.2,.1],atol=1e-12)
        np.testing.assert_allclose(r["uncertainty"],[.3,.4,.3],atol=1e-12)

    def test_mirror_invariance(self):
        a=risk_scores(self.m0,self.m1,self.q1)
        b=risk_scores(1-self.m0,1-self.m1,1-self.q1)
        for k in a:
            np.testing.assert_allclose(a[k],b[k],atol=1e-12)

    def test_independent_current_minute_suffix(self):
        orig=risk_scores(self.m0,self.m1,self.q1)
        pert=[x.copy() for x in (self.m0,self.m1,self.q1)]
        for a in pert: a[-1]=.999
        other=risk_scores(*pert)
        for k in orig:
            np.testing.assert_array_equal(orig[k][:-1],other[k][:-1])

    def test_reject_bad_probs_and_shape(self):
        with self.assertRaises(ValueError):
            risk_scores(np.array([0.0]),np.array([.3]),np.array([.5]))
        with self.assertRaises(ValueError):
            risk_scores(np.array([.4]),np.array([.3,.5]),np.array([.5]))
        with self.assertRaises(ValueError):
            risk_scores(np.array([np.nan]),np.array([.3]),np.array([.5]))

    def test_labels_not_in_current_minute_risk(self):
        self.assertEqual(set(risk_scores(self.m0,self.m1,self.q1)),
                         {"disagreement","uncertainty","component_m0","component_q1"})
        np.testing.assert_array_equal(wrong_decision(
            np.array([0,1,0]),self.m1),[0,0,1])
        with self.assertRaises(ValueError):
            wrong_decision(np.array([0,3,1]),self.m1)

    def test_alert_budget_tie_break_does_not_use_outcomes(self):
        risk=np.array([.9,.4,.7,.4,.2])
        y=np.array([0,1,1,0,0])
        x=alert_budget(y,risk,frac=.4)
        self.assertEqual(x["alerts"],2)
        self.assertEqual(x["wrong_alerts"],1)
        self.assertEqual(x["precision"],.5)

if __name__=="__main__":
    unittest.main()
