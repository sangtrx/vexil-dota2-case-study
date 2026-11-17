"""Pre-data collection invariants for the Nov-17 research follow-up."""
import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research import october2026_external_holdout as h


class FixedExternalCohortTest(unittest.TestCase):
    def test_frozen_date_and_original_model_contract(self):
        self.assertEqual(h.LOWER, 1790812800)
        self.assertEqual(h.UPPER, 1793491200)
        self.assertEqual(h.MAX_PAGES, 20)
        self.assertEqual(h.MAX_DETAILS, 180)
        self.assertEqual(h.SEED, 20261117)
        self.assertEqual(h.BOOTSTRAPS, 10000)
        self.assertEqual(len(h.unique_old_ids_and_series()[0]), 652)
        _, _, fp = h.frozen.models_from_frozen_train()
        self.assertEqual(fp, h.FINGERPRINTS)

    def test_outcomes_cannot_change_listing_selection(self):
        seen, old_series = h.unique_old_ids_and_series()
        near_old = next(iter(seen))
        oldsid = next(iter(old_series))
        rows = [
            {"match_id": 9999999985, "start_time": h.LOWER+2, "series_id": 111,
             "radiant_win": True},
            {"match_id": 9999999984, "start_time": h.LOWER+2, "series_id": 111,
             "radiant_win": False},
            {"match_id": 9999999983, "start_time": h.LOWER-1, "series_id": 0},
            {"match_id": 9999999982, "start_time": h.UPPER, "series_id": 0},
            {"match_id": 9999999981, "start_time": h.LOWER, "series_id": oldsid},
            {"match_id": near_old, "start_time": h.LOWER, "series_id": 0},
        ]
        # Re-order the historic ID by descending sorting; no outcome inspection.
        rows.sort(key=lambda r:r["match_id"],reverse=True)
        first,counts=h.selection_from_pages([rows])
        changed=copy.deepcopy(rows)
        for r in changed:
            r["radiant_win"]=not r.get("radiant_win",False)
            r["dire_score"]=99999
        second,counts2=h.selection_from_pages([changed])
        self.assertEqual(first,second)
        self.assertEqual(counts,counts2)
        self.assertEqual(
            {z["match_id"] for z in first}, {9999999984,9999999985}
        )
        self.assertEqual(counts["historical_overlap"],2)

    def test_duplicate_and_reordered_discovery_rejected(self):
        base={"match_id":9999999981,"start_time":h.LOWER,"series_id":0}
        for pages in ([[base,base]], [[base,{**base,"match_id":9999999982}]]):
            with self.assertRaisesRegex(ValueError,"Non-descending or duplicate"):
                h.selection_from_pages(pages)

    def test_strict_eligibility_helper_reuses_original_clock_and_restores_window(self):
        candidate={"match_id":9999999987,"start_time":h.LOWER+4,"series_id":17}
        payload={"match_id":9999999987,"start_time":h.LOWER+4,"series_id":17}
        low,high=h.frozen.MIN_START,h.frozen.MAX_START
        with mock.patch.object(h.frozen,"eligible",return_value="unparsed_gold") as fn:
            self.assertEqual(h.eligible_detail(payload,candidate,{}),"unparsed_gold")
            self.assertEqual(h.frozen.MIN_START,low)
            self.assertEqual(h.frozen.MAX_START,high)
            self.assertEqual(fn.call_args[0][1:],(candidate["match_id"],candidate["start_time"],{}))
        self.assertEqual(h.eligible_detail({**payload,"series_id":18},candidate,{}),
                         "series_mismatch")

    def test_bootstrap_negative_and_positive_cannot_depend_on_outcomes_for_selection(self):
        import pandas as pd
        df=pd.DataFrame({"match_id":[1,1,2,3,3],
                        "series_id":[4,4,4,0,0],
                        "d_ll":[-0.2,-0.1,0.3,-0.5,-0.7],
                        "d_brier":[0.02,-0.01,0.03,-0.04,0.08]})
        first=h.clustered_interval(df,"series","ll")
        second=h.clustered_interval(df,"series","ll")
        match=h.clustered_interval(df,"match","ll")
        self.assertEqual(first,second)
        self.assertEqual(len(match),2)
        self.assertLessEqual(first[0],first[1])


if __name__ == "__main__":
    unittest.main()
