from __future__ import annotations
import unittest
import pandas as pd
from research.lineage_contract import canonical_hash,MAIN,ITEM
from research.robustness_study import make_folds
from research.operational_contract import guarded_predict_at_minute

class RobustnessContracts(unittest.TestCase):
    def test_canonical_hash_order_invariant_and_sensitive(self):
        frame=pd.DataFrame([
            {'match_id':2,'minute':1,'radiant_win':1,'gold_k':1.0,
             'minute10':.1,'gold_x_time':.09531018,'xp_k':3,
             'gold_velocity5_k':1,'xp_velocity5_k':2,'tower_delta':0,
             'barracks_delta':0,'roshan_delta':0,'kill_delta':0},
            {'match_id':1,'minute':0,'radiant_win':0,'gold_k':0.,
             'minute10':0.,'gold_x_time':0.,'xp_k':0.,
             'gold_velocity5_k':0,'xp_velocity5_k':0,'tower_delta':0,
             'barracks_delta':0,'roshan_delta':0,'kill_delta':0}])
        a=canonical_hash(frame,MAIN)
        b=canonical_hash(frame.iloc[::-1],MAIN)
        self.assertEqual(a,b)
        c=frame.copy();c.loc[c.match_id==2,'gold_k']=1.125
        self.assertNotEqual(a,canonical_hash(c,MAIN))
        with self.assertRaises(ValueError):
            canonical_hash(pd.concat([frame,frame.iloc[:1]],ignore_index=True),MAIN)

    def test_series_safe_embargo_synthetic_without_labels(self):
        m=pd.DataFrame([dict(match_id=1000+i,series_id=0,start_time=1000*i,
              duration=300,partition='train') for i in range(291)])
        m.loc[0,'duration']=500000  # result unavailable to each fold
        folds=make_folds(m)
        self.assertEqual(len(folds),5)
        for f in folds:
            self.assertNotIn(1000,f['train_ids'])
            self.assertFalse(f['train_ids']&f['eval_ids'])
            self.assertGreaterEqual(f['eval_games'],15)
            self.assertGreaterEqual(f['train_games'],55)

    def test_out_of_domain_abstains_without_touching_payload(self):
        d={'match_id':987654}
        result=guarded_predict_at_minute(None,d,99,None,[],supported_max=85)
        self.assertEqual(result['status'],'OUTSIDE_TRAIN_TIME_SUPPORT')
        self.assertIsNone(result['p_radiant_win'])
        with self.assertRaises(ValueError):
            guarded_predict_at_minute(None,d,-1,None,[],supported_max=85)

if __name__=='__main__':unittest.main()
