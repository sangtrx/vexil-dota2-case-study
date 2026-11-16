import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
import gold_interaction_null_influence as M
from train_time_effect_ci import require_data


class GoldInteractionNullContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame=require_data()

    def test_null_is_gold_and_minute_not_just_gold(self):
        self.assertEqual(M.NULL_FEATURES,["gold_k","minute10"])
        self.assertEqual(len(M.FEATURES),3)
        self.assertEqual(M.FEATURES[-1],"gold_x_time")

    def test_original_four_fold_scope(self):
        oof,folds=M.forward_interaction_only(self.frame)
        self.assertEqual(len(oof),5081)
        self.assertEqual(oof.match_id.nunique(),137)
        self.assertEqual([b["eval_games"] for b in folds],[22,44,32,39])
        self.assertEqual([b["embargo"] for b in folds],[0,0,2,0])
        self.assertFalse(oof[["match_id","minute"]].duplicated().any())

    def test_series_crossing_forward_boundary_fails_closed(self):
        # Inject a known series on both sides of the first TRAIN cut.
        frame=self.frame.copy()
        meta=frame[["match_id","start_time","series_id"]].drop_duplicates()
        meta=meta.sort_values(["start_time","match_id"],kind="stable").reset_index(drop=True)
        older=int(meta.iloc[153].match_id)
        new=int(meta.iloc[154].match_id)
        known=int(meta.iloc[153].series_id)
        if known<=0:
            known=int(meta.iloc[:154].loc[meta.iloc[:154].series_id>0,"series_id"].iloc[-1])
        frame.loc[frame.match_id==new,"series_id"]=known
        with self.assertRaisesRegex(ValueError,"Series crosses"):
            M.forward_interaction_only(frame)

    def test_leave_one_cluster_keeps_train_only_and_171_groups(self):
        r=M.patch_and_influence(self.frame)
        self.assertEqual(r["leave_one_cluster"]["clusters"],171)
        self.assertEqual(r["patch_subfit"]["59"]["games"],250)
        self.assertEqual(r["patch_subfit"]["60"]["games"],41)
        self.assertLess(r["leave_one_cluster"]["minimum_D"],
                        r["leave_one_cluster"]["maximum_D"])

    def test_receipt_fails_predictive_promotion_gate(self):
        import json
        d=json.loads((ROOT/"research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json").read_text())
        self.assertEqual(d["scope"],
            "TRAIN_ONLY_POST_RESULT_HOSTILE_CORRECT_INTERACTION_NULL")
        self.assertFalse(d["original_validation_or_test_outcomes_read"])
        self.assertFalse(d["model_promotion_permitted"])
        self.assertEqual((d["oof_games"],d["oof_rows"]),(137,5081))
        self.assertEqual(d["null_model"],["gold_k","minute10"])
        r=d["interaction_null_bootstrap"]
        self.assertEqual(r["groups"],70)
        self.assertEqual(r["draws"],5000)
        for key in ("M1_minus_gold_time_null_logloss",
                    "M1_minus_gold_time_null_brier"):
            lo,hi=r[key]["percentile_ci_95"]
            self.assertLess(lo,0)
            self.assertGreater(hi,0)
        patches=d["patch_and_cluster_influence"]["patch_subfit"]
        self.assertEqual(patches["59"]["games"],250)
        self.assertEqual(patches["60"]["games"],41)
        self.assertLess(patches["60"]["fit_D"],patches["59"]["fit_D"])
        inf=d["patch_and_cluster_influence"]["leave_one_cluster"]
        self.assertEqual(inf["clusters"],171)
        self.assertEqual(inf["negative_D_count"],0)
        self.assertEqual(len(inf["top_five_by_absolute_impact"]),5)

if __name__=="__main__":
    unittest.main()
