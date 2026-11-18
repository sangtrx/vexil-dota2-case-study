"""No data or labels are read in cohort selection; protocol invariants are testable offline."""
import unittest
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "sept_selection",ROOT/"research/external_september/discover_candidates.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class SeptemberProtocol(unittest.TestCase):
    def test_metadata_filters_and_deletes_outcomes(self):
        t=MOD.START
        good={"match_id":123,"start_time":t+100,"duration":2100,"series_id":7,"leagueid":8,
              "radiant_win":True,"radiant_score":25}
        result=MOD.clean_meta(good)
        self.assertEqual(set(result),set(MOD.FIELDS))
        self.assertNotIn("radiant_win",str(result))
        self.assertIsNone(MOD.clean_meta({**good,"duration":599}))
        self.assertIsNone(MOD.clean_meta({**good,"start_time":t-1}))
        self.assertIsNone(MOD.clean_meta({**good,"start_time":MOD.STOP}))
        self.assertIsNone(MOD.clean_meta({**good,"match_id":"123"}))

    def test_deterministic_latest_200_and_overlap_exclusion(self):
        t=MOD.START
        rows=[{"match_id":i+1000,"start_time":t+i*60,"duration":1100,
                "radiant_win":(i%2==0)} for i in range(240)]
        chosen=MOD.select_metadata(rows,{1238})
        self.assertEqual(len(chosen),200)
        self.assertNotIn(1238,[x["match_id"] for x in chosen])
        self.assertEqual(chosen[0]["match_id"],1239)
        self.assertEqual(chosen,MOD.select_metadata(list(reversed(rows)),{1238}))
        self.assertEqual(chosen,MOD.select_metadata(rows+rows,{1238}))
        self.assertTrue(all("radiant_win" not in x for x in chosen))

    def test_study_is_isolated_from_employer_deliverable(self):
        self.assertTrue((ROOT/"delivery/Vexil_Dota2_Creative_Research_20261118.zip").exists())
        self.assertTrue((ROOT/"REPORT.pdf").exists())
        import hashlib,zipfile
        bundle=ROOT/"delivery/Vexil_Dota2_Creative_Research_20261118.zip"
        self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(),
                         "982528c82ba2dd5ee06f725ef360aa77561e5987e1c8992c9a51f77a91846568")
        with zipfile.ZipFile(bundle) as reader:
            self.assertFalse(any("external_september" in name for name in reader.namelist()))

if __name__=="__main__":unittest.main()
