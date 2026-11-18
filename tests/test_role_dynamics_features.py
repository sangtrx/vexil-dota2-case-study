import sys
import unittest
from pathlib import Path

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from role_dynamics_features import (one_snapshot,rank_flip,rank_alignment,
                                    RANK3,COUPLING3,ALL6)


def demo():
    base=np.array([
        [1.,3,5,5,5,5,9],
        [1.,2,3,4,5,6,7],
        [1.,2,4,6,8,10,11],
        [1.,4,6,8,9,12,15],
        [1.,1,2,3,4,5,6]])
    opposing=base[::-1].copy()*0.85
    xp=(base*1.5+np.arange(5)[:,None])
    opx=xp[::-1]*0.9
    return base,opposing,xp,opx


class RoleFeatureContract(unittest.TestCase):
    def test_new_feature_count_and_no_previous_static_gini_dup(self):
        self.assertEqual(len(ALL6),6)
        self.assertEqual(len(set(ALL6)),6)
        self.assertEqual(len(RANK3),3)
        self.assertEqual(len(COUPLING3),3)
        self.assertTrue(all("gini" not in s for s in ALL6))

    def test_swap_side_odd(self):
        a=demo()
        for minute in range(7):
            x=one_snapshot(*a,minute)
            y=one_snapshot(a[1],a[0],a[3],a[2],minute)
            for name in ALL6:
                self.assertAlmostEqual(x[name],-y[name],places=12)

    def test_invariant_to_player_order(self):
        a=demo()
        p=np.array([3,0,4,2,1])
        q=np.array([1,4,0,3,2])
        for minute in range(7):
            x=one_snapshot(*a,minute)
            y=one_snapshot(a[0][p],a[1][q],a[2][p],a[3][q],minute)
            for name in ALL6:
                self.assertAlmostEqual(x[name],y[name],places=12)

    def test_future_poison(self):
        a=list(demo())
        before=one_snapshot(*a,3)
        for arr in a:
            arr[:,4:]=1e8
        self.assertEqual(before,one_snapshot(*a,3))

    def test_rank_reversals(self):
        self.assertEqual(rank_flip(np.array([1,2,3,4,5]),np.array([5,4,3,2,1])),1)
        self.assertEqual(rank_flip(np.array([1,2,3,4,5]),np.array([1,2,3,4,5])),0)

    def test_rank_alignment_bounds(self):
        x=np.arange(1,6)
        self.assertEqual(rank_alignment(x,x),1.)
        self.assertEqual(rank_alignment(x,x[::-1]),-1.)

    def test_zero_flow_at_start(self):
        x=one_snapshot(*demo(),0)
        self.assertEqual(x["flow_hhi5_gap"],0)
        self.assertEqual(x["flow_funnel_shift5_gap"],0)
        self.assertEqual(x["leader_flow_funnel"],0)

    def test_invalid_prefix_rejected(self):
        a=list(demo())
        with self.assertRaises(ValueError):
            one_snapshot(*a,99)
        a[0][0,0]=np.nan
        with self.assertRaises(ValueError):
            one_snapshot(*a,0)


if __name__=="__main__":
    unittest.main()
