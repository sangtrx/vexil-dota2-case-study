import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
import conditional_gold_forward as F
from train_time_effect_ci import require_data

class ForwardFoldContract(unittest.TestCase):
    def test_exact_original_train_scope_and_fold_isolation(self):
        d=require_data()
        oof,folds=F.build_oof(d)
        self.assertEqual(oof.match_id.nunique(),137)
        self.assertEqual(len(oof),5081)
        self.assertEqual([f["eval_games"] for f in folds],[22,44,32,39])
        self.assertEqual([f["embargoed_old_games"] for f in folds],[0,0,2,0])
        self.assertTrue(oof.match_id.isin(d.match_id).all())
        self.assertEqual(oof[["match_id","minute"]].duplicated().sum(),0)
        self.assertEqual(len(folds),4)

    def test_fixed_logloss_and_brier_bootstrap_uses_70_series_groups(self):
        d=require_data()
        oof,_=F.build_oof(d)
        a=F.series_bootstrap(oof,draws=14)
        b=F.series_bootstrap(oof,draws=14)
        self.assertEqual(a,b)
        self.assertEqual(a["groups"],70)
        for key in ("M1_minus_M0_logloss","M1_minus_M0_brier"):
            self.assertEqual(len(a[key]["percentile_ci_95"]),2)
            self.assertLess(a[key]["percentile_ci_95"][0],a[key]["percentile_ci_95"][1])

    def test_frozen_forward_receipt_and_negative_model_promotion_decision(self):
        import json
        d=json.loads((ROOT/"research/CONDITIONAL_GOLD_FORWARD_RECEIPT.json").read_text())
        self.assertEqual(d["scope"],
                         "POST_RESULT_TRAIN_ONLY_FORWARD_OOF_NOT_INDEPENDENT_TEST")
        self.assertFalse(d["original_test_or_val_labels_read"])
        self.assertTrue(d["no_model_promotion"])
        self.assertEqual((d["forward_eval_games"],d["forward_eval_rows"]),(137,5081))
        self.assertEqual(d["cluster_bootstrap"]["groups"],70)
        self.assertEqual([f["embargoed_old_games"] for f in d["folds"]],[0,0,2,0])
        for fold in d["folds"]:
            self.assertGreater(fold["M1_conditional_gold_logodds_delta_t10_minus_t30"],0)
        ll=d["cluster_bootstrap"]["M1_minus_M0_logloss"]
        br=d["cluster_bootstrap"]["M1_minus_M0_brier"]
        self.assertLess(ll["percentile_ci_95"][0],0)
        self.assertGreater(ll["percentile_ci_95"][1],0)
        self.assertGreater(br["point"],0)
        self.assertLess(br["percentile_ci_95"][0],0)
        self.assertGreater(br["percentile_ci_95"][1],0)

    def test_negative_skill_readout_is_explicit(self):
        text=" ".join((ROOT/"research/CONDITIONAL_GOLD_FORWARD_READOUT.md").read_text().lower().split())
        for phrase in ("three of four", "does **not** establish improved prediction",
                       "contains 0", "do not justify production promotion"):
            self.assertIn(phrase,text)

if __name__=="__main__":
    unittest.main()
