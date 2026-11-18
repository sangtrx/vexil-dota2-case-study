import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from boosted_trees_direct import (
    INPUTS,CANDIDATES,REFS,PARAMS,SCREEN_SIZE,SEED,
    candidate_model,check_environment,match_equal_fit_weights,
    binned_calibration,folded_source,paired_series_ci,
)
from rich_feature_engineering import BASE,RICH
from rich_feature_models import load_train


class DirectBoostedFrozen(unittest.TestCase):
    def test_dependencies_and_protocol(self):
        v=check_environment()
        self.assertEqual((v["xgboost"],v["lightgbm"],v["narwhals"]),
                         ("3.4.1","4.7.0","2.21.2"))
        self.assertEqual((SCREEN_SIZE,SEED),(8,20261118))

    def test_exact_features_and_families(self):
        self.assertEqual(CANDIDATES,("XGB3","XGB84","LGB3","LGB84"))
        self.assertEqual(len(BASE),3)
        self.assertEqual(len(RICH),81)
        self.assertEqual(len(INPUTS["XGB84"]),84)
        for n in CANDIDATES:
            self.assertEqual(len(INPUTS[n]),3 if n.endswith("3") else 84)
            self.assertNotIn("duration",INPUTS[n])
            self.assertNotIn("radiant_win",INPUTS[n])
            self.assertNotIn("series_id",INPUTS[n])
            self.assertNotIn("match_id",INPUTS[n])
            self.assertNotIn("patch",INPUTS[n])
        self.assertEqual(INPUTS["XGB3"],INPUTS["LGB3"])
        self.assertEqual(INPUTS["XGB84"],INPUTS["LGB84"])

    def test_same_highly_regularized_predeclared_params(self):
        for name in CANDIDATES:
            m=candidate_model(name)
            self.assertEqual(list(m.named_steps),["imputer","model"])
            p=m.named_steps["model"].get_params()
            self.assertEqual(p["n_estimators"],90)
            self.assertEqual(p["max_depth"],2 if name.startswith("XGB") else 3)
            self.assertEqual(p["colsample_bytree"],1 if name.endswith("3") else .8)
            self.assertEqual(p["random_state"],SEED)
            self.assertEqual(p["n_jobs"],2)
            self.assertNotIn("eval_set",p)
            if name.startswith("XGB"):
                self.assertEqual(p["min_child_weight"],35)
            else:
                self.assertEqual(p["min_child_samples"],175)
                self.assertTrue(p["deterministic"])
        with self.assertRaises(ValueError):
            candidate_model("XGB_tuned_on_TEST")

    def test_equal_game_weights_dont_depend_on_rows_per_game(self):
        sample=pd.DataFrame({
            "match_id":[7,7,7,8,8,9],
            "minute":[0,1,2,0,1,0],
        })
        w=match_equal_fit_weights(sample)
        sums=pd.DataFrame({"m":sample.match_id,"w":w}).groupby("m").w.sum()
        np.testing.assert_allclose(sums.to_numpy(),[2.,2.,2.],rtol=0,atol=1e-12)
        self.assertAlmostEqual(w.sum(),len(sample))
        broken=sample.copy()
        broken.loc[5,"minute"]=0
        broken.loc[5,"match_id"]=8
        with self.assertRaises(ValueError):
            match_equal_fit_weights(broken)

    def test_calibration_bounds_and_exact_bin_count(self):
        y=np.array([1,0,1,0])
        p=np.array([.99,.11,.4,.5])
        r=binned_calibration(y,p)
        self.assertEqual(sum(x["n_rows"] for x in r["bins"]),len(y))
        self.assertEqual(len(r["bins"]),10)
        self.assertTrue(0<=r["ece_10_minute_rows_descriptive"]<=1)
        for candidate in (np.array([0.,.1]),np.array([1.,.9]),np.array([.1,np.nan])):
            with self.assertRaises(ValueError):
                binned_calibration(np.array([1,0]),candidate)

    def test_frozen_train_only_fold_source_shape_and_maturity(self):
        df,_=load_train()
        folds=list(folded_source(df))
        self.assertEqual(len(folds),4)
        self.assertEqual(sum(len(ev) for _,_,ev,_ in folds),5081)
        self.assertEqual(sum(ev.match_id.nunique() for _,_,ev,_ in folds),137)
        for k,fit,ev,immature in folds:
            self.assertGreater(fit.match_id.nunique(),0)
            self.assertGreaterEqual(immature,0)
            self.assertFalse(set(fit.match_id)&set(ev.match_id))
            self.assertTrue((ev.minute*60 < ev.duration).all())
            self.assertEqual(set(fit.partition),{"train"})
            self.assertEqual(set(ev.partition),{"train"})

    def test_70_series_bootstrap_grouped_not_iid(self):
        n=70
        f=pd.DataFrame({
            "match_id":np.arange(1,n+1),"series_id":np.zeros(n,dtype=int),
            "minute":np.zeros(n,dtype=int),
            "ll_a":np.full(n,.30),"ll_b":np.full(n,.35),
            "br_a":np.full(n,.15),"br_b":np.full(n,.16),
        })
        # add a late row per game to make the late Brier guardrail defined.
        g=f.copy()
        g["minute"]=31
        oof=pd.concat([f,g],ignore_index=True)
        out=paired_series_ci(oof,"a","b",draws=100)
        self.assertEqual(out["series_groups"],70)
        self.assertAlmostEqual(out["delta_logloss_minute"],-.05,places=11)
        self.assertAlmostEqual(out["delta_brier"],-.01,places=11)
        np.testing.assert_allclose(out["ci95_minute"],[-.05,-.05],rtol=0,atol=1e-11)

    def test_synthetic_api_smoke_and_feature_order_rejection(self):
        rng=np.random.default_rng(20261118)
        n=1200
        x=pd.DataFrame(rng.normal(size=(n,len(BASE+RICH))),columns=BASE+RICH)
        y=(x.gold_k+0.25*x.minute10>0).astype(int)
        for name in CANDIDATES:
            c=list(INPUTS[name])
            model=candidate_model(name)
            model.fit(x[c],y)
            p=model.predict_proba(x[c].iloc[:8])[:,1]
            self.assertEqual(p.shape,(8,))
            self.assertTrue((p>0).all() and (p<1).all())
            self.assertTrue(np.isfinite(p).all())
            with self.assertRaises(ValueError):
                model.predict_proba(x[c[::-1]].iloc[:8])

if __name__=="__main__":
    unittest.main()
