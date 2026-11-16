import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
import gold_local_window_survivor as M
from train_time_effect_ci import require_data

class GoldLocalWindowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=require_data()

    def test_complete_survivor_panel_retrospective_only(self):
        _,e,l=M.panel(self.data,balanced=True)
        self.assertEqual(set(e.match_id),set(l.match_id))
        self.assertTrue((e.groupby("match_id").minute.nunique()==5).all())
        self.assertTrue((l.groupby("match_id").minute.nunique()==5).all())
        self.assertTrue(e.minute.between(8,12).all())
        self.assertTrue(l.minute.between(28,32).all())

    def test_balanced_panel_equals_duration_survival_under_frozen_clock(self):
        _,early,late=M.panel(self.data,balanced=True)
        expected=set(self.data.loc[self.data.duration>1920,"match_id"])
        self.assertEqual(set(early.match_id),expected)
        self.assertEqual(set(late.match_id),expected)

    def test_all_available_panel_contains_survivors_and_more(self):
        _,e,l=M.panel(self.data,balanced=False)
        _,u,v=M.panel(self.data,balanced=True)
        self.assertGreaterEqual(e.match_id.nunique(),u.match_id.nunique())
        self.assertGreaterEqual(l.match_id.nunique(),v.match_id.nunique())
        self.assertEqual(len(set(M.cluster_ids(self.data))),171)

    def test_descriptive_local_coefficients_and_auc_are_finite(self):
        import math
        _,e,l=M.panel(self.data,balanced=True)
        a=M.window_measures(e);b=M.window_measures(l)
        for r in (a,b):
            self.assertTrue(math.isfinite(r["logodds_per_plus_2k_gold"]))
            self.assertTrue(0<=r["auc_gold_vs_winner"]<=1)
            self.assertGreater(r["observed_gold_SD_thousands"],0)

    def test_receipt_rejects_less_information_interpretation(self):
        import json
        d=json.loads((ROOT/"research/GOLD_LOCAL_WINDOW_SURVIVOR_RECEIPT.json").read_text())
        self.assertEqual(d["scope"],
            "TRAIN_ONLY_POST_SELECTION_LOCAL_WINDOW_AND_SURVIVOR_FALSIFICATION")
        self.assertFalse(d["test_or_validation_outcomes_read"])
        self.assertFalse(d["model_promotion"])
        self.assertEqual(d["draws"],1000)
        self.assertEqual(d["source_train_sha256"],M.TRAIN_SHA)
        self.assertEqual(d["source_manifest_sha256"],M.MANIFEST_SHA)
        panels=d["panels"]
        self.assertEqual(panels["all_available_games"]["cluster_count"],171)
        self.assertEqual(panels["balanced_survivors_to_minute_32"]["cluster_count"],133)
        p=panels["balanced_survivors_to_minute_32"]
        self.assertTrue(p["balanced_on_future_survival_NOT_an_online_feature"])
        self.assertEqual(p["early"]["games"],p["late"]["games"])
        auc=p["differences_early_minus_late"]["auc_gold_vs_winner"]
        self.assertLess(auc["point"],0)
        self.assertLess(auc["percentile_ci_95"][1],0)
        unit=p["differences_early_minus_late"]["logodds_per_plus_2k_gold"]
        self.assertLess(unit["percentile_ci_95"][0],0)
        self.assertGreater(unit["percentile_ci_95"][1],0)
        sd=p["differences_early_minus_late"]["logodds_per_one_gold_SD"]
        self.assertLess(sd["percentile_ci_95"][1],0)

    def test_readout_conclusion_is_not_positive_recruiter_claim(self):
        text=" ".join((ROOT/"research/GOLD_LOCAL_WINDOW_SURVIVOR_READOUT.md").read_text().lower().split())
        for fragment in ("reject the unqualified inference", "auc",
                         "collider-selected on future duration",
                         "crosses zero", "the recruiter report"):
            self.assertIn(fragment,text)

if __name__=="__main__":
    unittest.main()
