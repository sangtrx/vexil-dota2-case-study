import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from all_family_features import one_snapshot,mirror,COLS,FAMILY


class FamilyContracts(unittest.TestCase):
    def test_frozen_registration_and_disjointness(self):
        self.assertEqual(len(COLS),9)
        self.assertEqual({k:len(v) for k,v in FAMILY.items()},{"R":2,"O":2,"C":2,"I":3})
        self.assertEqual(len(set(COLS)),9)

    def test_regime_reversal_and_ordinal_entropic_flip(self):
        g=[0,1,2,2.5,1.7,0.9,0.2,-.4,0.5,1,2]
        a=one_snapshot(g,10,[],[])
        b=one_snapshot([-v for v in g],10,[],[])
        for k in COLS:self.assertAlmostEqual(a[k],-b[k],places=12)
        self.assertGreater(abs(a["reg_cusum10"]),0)
        self.assertTrue(np.isfinite(a["ordinal_entropy10"]))

    def test_constant_history_all_zero_except_undefined_occupancy(self):
        a=one_snapshot([0]*15,14,[],[])
        self.assertEqual(set(a.values()),{0.})

    def test_event_exclusion_and_objective_side(self):
        g=[0,1,2,4,5]
        a=one_snapshot(g,3,[(120,1),(241,-1)],[])
        self.assertGreater(a["objective_conversion5"],0)
        b=one_snapshot(g,3,[(241,-1)],[])
        self.assertEqual(b["objective_conversion5"],0)
        c=one_snapshot([-v for v in g],3,[(120,-1),(241,1)],[])
        for k in FAMILY["C"]:
            self.assertAlmostEqual(a[k],-c[k],places=12)

    def test_item_first_purchase_and_future_no_signal(self):
        p=[(30,1,"blink",0),(75,1,"blink",0),(180,-1,"black_king_bar",128),
           (500,1,"black_king_bar",1)]
        a=one_snapshot([0,1,2,3],3,[],p)
        self.assertEqual(a["item_blink_diff"],1)
        self.assertEqual(a["item_bkb_diff"],-1)
        self.assertEqual(a["item_recent5_diff"],0)
        b=one_snapshot([0,1,2,3],3,[],p+[(100000,-1,"blink",129)])
        self.assertEqual(a,b)

    def test_mirror_both_inputs(self):
        g=[-.2,-.1,.5,1,1.8,1.2]
        obj=[(110,1),(200,-1)]
        pur=[(120,1,"blink",0),(210,-1,"black_king_bar",128)]
        mo,mp=mirror(obj,pur)
        a=one_snapshot(g,5,obj,pur)
        b=one_snapshot([-v for v in g],5,mo,mp)
        for k in COLS:self.assertAlmostEqual(a[k],-b[k],places=12)

    def test_both_future_suffix_and_logs_poisoned(self):
        a=one_snapshot([0,1,2,3],2,[(120,1)],[(119,1,"blink",0)])
        b=one_snapshot([0,1,2,999],2,[(120,1),(500,-1)],[(119,1,"blink",0),(555,-1,"black_king_bar",128)])
        self.assertEqual(a,b)

    def test_invalid_gold_rejected(self):
        with self.assertRaises(ValueError):
            one_snapshot([0,float("nan")],1,[],[])
        with self.assertRaises(ValueError):
            one_snapshot([0],1,[],[])


if __name__=="__main__":
    unittest.main()
