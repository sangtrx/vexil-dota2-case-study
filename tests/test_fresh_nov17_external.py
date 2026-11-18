import sys
from pathlib import Path
import unittest
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from fresh_nov17_external import MODELS,START,END,MAX_PAGE,MAX_GAMES,check_payload,metrics_and_ci

class FrozenExternalSourceTest(unittest.TestCase):
    def test_precommitted_4_models(self):
        self.assertEqual(MODELS,("M0_gold","M1_interaction","Q1_path","MATCH_EQUAL"))
        self.assertEqual((MAX_PAGE,MAX_GAMES),(4,45))
        self.assertEqual(END-START,86400)

    def test_outcome_missing_source_rejected(self):
        raw={"match_id":2,"start_time":START,"duration":999}
        row={"match_id":2,"start_time":START,"duration":999}
        self.assertEqual(check_payload(raw,row)[0],"missing_final_label")

    def test_no_false_game_validity(self):
        raw={"match_id":1,"start_time":START,"duration":1800,"radiant_win":True,"patch":60}
        row={"match_id":2,"start_time":START,"duration":1800}
        self.assertEqual(check_payload(raw,row)[0],"listed_identity_time_or_duration_mismatch")

    def test_bootstrap_equal_games_weight_not_equal_minutes(self):
        # Different number of minutes per game and different series.
        f=pd.DataFrame({"match_id":[1,1,1,2],"minute":[0,1,31,31],"series_id":[9,9,9,10],
           "ll_X":[.1,.1,.1,.5],"ll_Y":[.2,.2,.2,.3],
           "br_X":[.1,.1,.1,.1],"br_Y":[.2,.2,.2,.2]})
        out=metrics_and_ci(f,"X","Y")
        self.assertAlmostEqual(out["equal_match_delta_logloss"],.05,places=12)
        self.assertAlmostEqual(out["minute_delta_logloss"],-.025,places=12)
        self.assertLess(out["equal_match_95_ci"][0],0)
        self.assertGreater(out["equal_match_95_ci"][1],0)

if __name__=="__main__":
    unittest.main()
