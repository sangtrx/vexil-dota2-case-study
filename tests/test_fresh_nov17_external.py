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

    def test_frozen_source_has_no_winner_or_scores_and_unique_ids(self):
        import json
        from fresh_nov17_external import LISTING, START, END, MAX_GAMES
        data=json.loads(LISTING.read_text())
        chosen=data["selected"]
        self.assertEqual(len(chosen),17)
        self.assertTrue(data["reached_start_boundary"])
        self.assertLessEqual(len(chosen),MAX_GAMES)
        self.assertEqual(len({r["match_id"] for r in chosen}),len(chosen))
        self.assertEqual(chosen,sorted(chosen,key=lambda r:(r["start_time"],r["match_id"])))
        self.assertTrue(all(START<=r["start_time"]<END for r in chosen))
        for row in chosen:
            self.assertEqual(set(row),{"match_id","start_time","duration","series_id","leagueid"})
            self.assertNotIn("radiant_win",row)
            self.assertNotIn("radiant_score",row)
            self.assertNotIn("dire_score",row)

    def test_collected_sources_are_selected_without_outcome_filter(self):
        import json
        from fresh_nov17_external import LISTING,ROOT,sha_file
        listing=json.loads(LISTING.read_text())
        receipt=json.loads((ROOT/"research/FRESH_NOV17_SOURCE_RECEIPT.json").read_text())
        self.assertEqual(receipt["selection_sha256"],sha_file(LISTING))
        self.assertEqual(receipt["accepted_count"],17)
        self.assertEqual(receipt["selected_count"],17)
        self.assertEqual(set(x["match_id"] for x in receipt["accepted"]),
                         set(x["match_id"] for x in listing["selected"]))
        self.assertTrue(receipt["source_games_collected_without_model_scoring"])
        self.assertTrue(receipt["all_exclusions_source_only"])
        self.assertFalse(receipt["outcome_preselection"])

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
