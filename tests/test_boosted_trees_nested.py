import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))

from boosted_trees_nested import (
    PROFILES,PROFILE_NAMES,PROTO,CANDIDATES,
    tuned_model,inner_fold_slices,best_profile,fit_and_predict,
)
from boosted_trees_direct import folded_source,INPUTS,check_environment
from rich_feature_models import load_train
from train_time_effect_ci import cluster_ids


class NestedFairnessContract(unittest.TestCase):
    def test_protocol_version_is_frozen(self):
        self.assertTrue(PROTO.exists())
        self.assertEqual(PROFILE_NAMES,("conservative","moderate","flexible"))
        self.assertEqual(len(CANDIDATES)*len(PROFILE_NAMES),12)
        self.assertEqual(check_environment()["lightgbm"],"4.7.0")

    def test_explicit_predeclared_param_grid_no_outer_tuning(self):
        for family in ("XGB","LGB"):
            self.assertEqual(set(PROFILES[family]),set(PROFILE_NAMES))
            self.assertEqual([PROFILES[family][p]["n_estimators"] for p in PROFILE_NAMES],
                             [90,150,180])
        for name in CANDIDATES:
            for profile in PROFILE_NAMES:
                m=tuned_model(name,profile)
                self.assertEqual(list(m.named_steps),["imputer","model"])
                opts=m.named_steps["model"].get_params()
                self.assertEqual(opts["random_state"],20261118)
                self.assertEqual(opts["n_jobs"],2)
                self.assertEqual(opts["n_estimators"],PROFILES[
                    "XGB" if name.startswith("XGB") else "LGB"][profile]["n_estimators"])
                self.assertNotIn("early_stopping_rounds",opts) if name.startswith("LGB") else None
        with self.assertRaises(ValueError):
            tuned_model("XGB84","post_test_perfect")

    def test_inner_group_splits_use_only_outer_fit(self):
        d,_=load_train()
        for k,outer_fit,outer_eval,_ in folded_source(d):
            before=set(outer_fit.match_id)
            future=set(outer_eval.match_id)
            folds=list(inner_fold_slices(outer_fit))
            self.assertEqual(len(folds),2)
            for j,train,ev,info in folds:
                self.assertGreaterEqual(info["fit_professional_groups"],8)
                self.assertGreaterEqual(info["val_professional_groups"],5)
                self.assertTrue(set(train.match_id).issubset(before))
                self.assertTrue(set(ev.match_id).issubset(before))
                self.assertFalse(set(train.match_id)&future)
                self.assertFalse(set(ev.match_id)&future)
                self.assertFalse(set(train.match_id)&set(ev.match_id))
                self.assertFalse(set(cluster_ids(train)) & set(cluster_ids(ev)))
                cutoff=int(ev.start_time.min())
                self.assertTrue((train.start_time+train.duration<=cutoff).all())
                self.assertEqual(int(info["val_minutes"]),len(ev))

    def test_label_permutation_cannot_move_inner_groups(self):
        d,_=load_train()
        _,fit,_,_=next(iter(folded_source(d)))
        a=list(inner_fold_slices(fit))
        altered=fit.copy()
        altered["radiant_win"]=1-altered.radiant_win.astype(int)
        b=list(inner_fold_slices(altered))
        for one,two in zip(a,b):
            self.assertEqual(set(one[1].match_id),set(two[1].match_id))
            self.assertEqual(set(one[2].match_id),set(two[2].match_id))
            self.assertEqual(one[3],two[3])

    def test_ties_break_to_original_conservative_profile(self):
        self.assertEqual(best_profile({"conservative":.42,"moderate":.42,"flexible":.42}),
                         "conservative")
        self.assertEqual(best_profile({"conservative":.45,"moderate":.43,"flexible":.44}),
                         "moderate")
        with self.assertRaises(ValueError):
            best_profile({"conservative":.5,"moderate":.5})

    def test_no_model_fit_using_eval_label_or_time_meta_as_input(self):
        for name in CANDIDATES:
            cols=INPUTS[name]
            for f in ("radiant_win","duration","start_time","match_id","series_id","partition"):
                self.assertNotIn(f,cols)

    def test_synthetic_nested_apis_are_compatible(self):
        rng=np.random.default_rng(20261118)
        d=pd.DataFrame(rng.normal(size=(800,84)),columns=list(INPUTS["XGB84"]))
        d["radiant_win"]=(d.gold_k>0).astype(int)
        for m in ("XGB3","LGB3"):
            cols=list(INPUTS[m])
            p=fit_and_predict(tuned_model(m,"moderate"),d.iloc[:700],d.iloc[700:],cols)
            self.assertEqual(len(p),100)
            self.assertTrue(np.isfinite(p).all())
            self.assertTrue(((0<p)&(p<1)).all())


if __name__=="__main__":
    unittest.main()
