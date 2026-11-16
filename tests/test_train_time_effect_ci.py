import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
F=ROOT/"research/train_time_effect_ci.py"
S=importlib.util.spec_from_file_location("train_ci",F)
M=importlib.util.module_from_spec(S)
S.loader.exec_module(M)


class TrainOnlyTimeContrast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df=M.require_data()

    def test_original_train_split_exactly_and_no_later_ids(self):
        manifest=pd.read_csv(M.MANIFEST)
        self.assertEqual(self.df.match_id.nunique(),291)
        self.assertEqual(len(self.df),10675)
        self.assertEqual(len(set(M.cluster_ids(self.df))),171)
        self.assertTrue(set(self.df.match_id).isdisjoint(
            set(manifest.loc[manifest.partition.isin(["validation","test"]),"match_id"])))

    def test_original_model_is_unmodified(self):
        p10,p30,delta=M.fit_scenario(self.df)
        self.assertAlmostEqual(p10,0.6649891894445361,places=11)
        self.assertAlmostEqual(p30,0.5940371481769021,places=11)
        self.assertAlmostEqual(delta,p10-p30,places=12)

    def test_real_train_matched_state_pair_has_nearly_identical_m1_probabilities(self):
        # Author-observed objective events are described in the register;
        # this test independently checks TRAIN membership, timing,
        # economy features, labels, and frozen M1 predictions from
        # the bundled TRAIN data, without touching VAL or TEST labels.
        ids=(8739246794,8739992397)
        pair=self.df.loc[
            self.df.match_id.isin(ids) & (self.df.minute==25)
        ].sort_values("match_id")
        self.assertEqual(pair.match_id.astype(int).tolist(),list(ids))
        self.assertEqual(pair.radiant_win.astype(int).tolist(),[1,1])
        np.testing.assert_allclose(pair.gold_k.to_numpy(),[1.901,1.929],
                                   atol=1e-12,rtol=0)
        self.assertTrue((pair.minute*60<pair.duration).all())
        fit=M.model().fit(self.df[M.FEATURES],self.df.radiant_win.astype(int))
        prob=fit.predict_proba(pair[M.FEATURES])[:,1]
        np.testing.assert_allclose(prob,[0.6031228483004619,0.6046407157637871],
                                   atol=1e-12,rtol=0)
        self.assertLess(float(abs(prob[1]-prob[0])),0.002)
        self.assertGreater(float(abs(prob[1]-prob[0])),0.001)

    def test_fixed_gold_and_time_interaction_is_exact(self):
        s=M.scenario()
        self.assertEqual(s["gold_k"].tolist(),[2.0,2.0])
        self.assertEqual(s["minute10"].tolist(),[1.0,3.0])
        self.assertAlmostEqual(s.gold_x_time.iloc[0],2*np.log1p(1))
        self.assertAlmostEqual(s.gold_x_time.iloc[1],2*np.log1p(3))

    def test_groups_are_series_not_independent_minutes(self):
        f=pd.DataFrame({"match_id":[1,1,2,2,3,3],
                        "series_id":[7,7,7,7,0,0]})
        self.assertEqual(M.cluster_ids(f).tolist(),
                         ["s7","s7","s7","s7","m3","m3"])

    def test_minute_endpoints_are_strictly_preterminal(self):
        self.assertTrue(((self.df.minute*60)<self.df.duration).all())
        for mid,g in self.df.groupby("match_id"):
            self.assertEqual(g.minute.min(),0)
            self.assertEqual(len(g),g.minute.max()+1)

    def test_one_small_grouped_bootstrap_is_deterministic(self):
        # Refit the original pipeline; never depend on an outcome from VAL or TEST.
        result1=M.calculate(self.df,draws=6)
        result2=M.calculate(self.df,draws=6)
        self.assertEqual(result1,result2)
        self.assertEqual(result1["train_games"],291)
        self.assertEqual(result1["train_series_or_singleton_clusters"],171)
        self.assertEqual(result1["original_val_or_test_outcomes_opened_by_script"],0)

    def test_exact_source_includes_149_series_and_22_singletons(self):
        one=self.df[["match_id","series_id"]].drop_duplicates()
        self.assertEqual(one.loc[one.series_id==0,"match_id"].nunique(),22)
        self.assertEqual(one.loc[one.series_id>0,"series_id"].nunique(),149)

    def test_cross_platform_replay_guard_allows_tiny_roundoff_not_result_tampering(self):
        from copy import deepcopy
        receipt=json.loads(M.RECEIPT.read_text())
        small=deepcopy(receipt)
        small["moment_10_probability"]["point"]+=1e-7
        M.verify_replay(small,receipt)
        large=deepcopy(receipt)
        large["time_contrast"]["95ci"][0]+=0.01
        with self.assertRaises(ValueError):
            M.verify_replay(large,receipt)
        wrong=deepcopy(receipt)
        wrong["source_manifest_sha256"]="0"*64
        with self.assertRaises(ValueError):
            M.verify_replay(wrong,receipt)

    def test_receipt_if_present_does_not_promote_model(self):
        if not M.RECEIPT.exists():
            self.skipTest("First group-bootstrap not executed yet")
        d=json.loads(M.RECEIPT.read_text())
        self.assertFalse(d["selection_or_promotion_using_results"])
        self.assertEqual(d["source_train_sha256"],M.TRAIN_SHA)
        self.assertEqual(d["bootstrap_draws"],2000)
        self.assertEqual(d["train_series_or_singleton_clusters"],171)


if __name__=="__main__":
    unittest.main()
