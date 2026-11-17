"""Exact fixed delay visibility and no forward leakage."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from event_delay_hostile import visible_events
from all_family_features import one_snapshot


class EventDelayTests(unittest.TestCase):
    def setUp(self):
        self.o=[(0.,1),(59.,-1),(60.,1),(119.,-1),(120.,-1)]
        self.p=[(0.,1,"blink",0),
                (60.,-1,"black_king_bar",128),
                (119.,1,"blink",1),(120.,-1,"blink",129)]
        self.g=[0.,2.,1.]

    def test_t0_delayed_must_not_see_purchases_at_zero(self):
        o,p=visible_events(self.o,self.p,0,60)
        self.assertEqual(o,[])
        self.assertEqual(p,[])
        x=one_snapshot(self.g,0,o,p)
        self.assertEqual(x["item_blink_diff"],0)

    def test_event_exact_current_minute_known_only_without_lag(self):
        o,p=visible_events(self.o,self.p,1,0)
        self.assertIn((60.,1),o)
        self.assertIn((60.,-1,"black_king_bar",128),p)
        o,p=visible_events(self.o,self.p,1,60)
        self.assertNotIn((60.,1),o)
        self.assertNotIn((60.,-1,"black_king_bar",128),p)
        self.assertIn((0.,1),o)
        self.assertIn((0.,1,"blink",0),p)

    def test_future_poison_ignored(self):
        before=visible_events(self.o,self.p,1,60)
        after=visible_events(self.o+[(1e9,1)],self.p+[(1e9,1,"blink",2)],1,60)
        self.assertEqual(before,after)

    def test_no_cross_match_history(self):
        o,p=visible_events([],[],2,60)
        self.assertEqual((o,p),([],[]))

    def test_invalid_tuning_rejected(self):
        with self.assertRaises(ValueError):
            visible_events(self.o,self.p,1,30)
        with self.assertRaises(ValueError):
            visible_events(self.o,self.p,-1,60)

if __name__=="__main__":
    unittest.main()
