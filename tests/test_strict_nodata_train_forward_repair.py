import unittest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from strict_nodata_train_forward_repair import fixed_lag_predictions


class FakeLogistic:
    def predict_proba(self,features):
        a=features.gold_k.to_numpy(float)
        p=1/(1+np.exp(-a))
        return np.stack([1-p,p],axis=1)


class StrictTrainFeed(unittest.TestCase):
    def test_new_policy_no_model_called_during_absent_first_3_min(self):
        ev=pd.DataFrame({
          "match_id":[7]*5,"minute":list(range(5)),
          "minute10":[0,.1,.2,.3,.4],
          "gold_k":[1.,2.,3.,4.,5.],
        })
        ev["gold_x_time"]=ev.gold_k*np.log1p(ev.minute10)
        fresh=np.array([.52,.54,.56,.58,.61])
        clock,hold,missing=fixed_lag_predictions(FakeLogistic(),ev,fresh,3)
        self.assertEqual(missing,3)
        np.testing.assert_array_equal(clock[:3],np.full(3,.5))
        np.testing.assert_array_equal(hold[:3],np.full(3,.5))
        np.testing.assert_array_equal(hold[3:],[.52,.54])
        self.assertAlmostEqual(clock[3],1/(1+np.exp(-1)))
        self.assertAlmostEqual(clock[4],1/(1+np.exp(-2)))

    def test_source_missing_in_one_game_does_not_reuse_previous_game_p(self):
        ev=pd.DataFrame({
          "match_id":[7]*4+[8]*4,"minute":list(range(4))*2,
          "minute10":[0,.1,.2,.3]*2,
          "gold_k":[1.,2.,3.,4.,-1.,-2.,-3.,-4.],
        })
        ev["gold_x_time"]=ev.gold_k*np.log1p(ev.minute10)
        fresh=np.linspace(.51,.64,len(ev))
        clock,hold,missing=fixed_lag_predictions(FakeLogistic(),ev,fresh,1)
        self.assertEqual(missing,2)
        self.assertEqual(clock[0],.5)
        self.assertEqual(clock[4],.5)
        self.assertEqual(hold[4],.5)
        self.assertAlmostEqual(hold[5],fresh[4])

if __name__=="__main__":
    unittest.main()
