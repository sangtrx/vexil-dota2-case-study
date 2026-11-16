"""Mechanistic identity checks, not a new blind model-evaluation test."""
import importlib.util
import json
import math
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
import conditional_gold_value as M


class ConditionalGoldValueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train = M.require_data()

    def test_input_feature_contract(self):
        x=M.contrast_rows()
        self.assertEqual(x.shape,(4,3))
        self.assertEqual(x.gold_k.tolist(),[0,2,0,2])
        self.assertEqual(x.minute10.tolist(),[1,1,3,3])
        self.assertAlmostEqual(x.gold_x_time.iloc[1],2*math.log(2))
        self.assertAlmostEqual(x.gold_x_time.iloc[3],2*math.log(4))

    def test_gold_logodds_value_is_independent_of_time_intercept(self):
        pipe=M.model().fit(self.train[M.FEATURES],
                           self.train.radiant_win.astype(int))
        x=M.contrast_rows()
        # If adding a time-only logit term to every state within a minute,
        # both gold log-odds contrasts remain unchanged.
        d=pipe.decision_function(x)
        d2=d+np.array([0.6,0.6,-1.4,-1.4])
        self.assertAlmostEqual((d[1]-d[0])-(d[3]-d[2]),
                               (d2[1]-d2[0])-(d2[3]-d2[2]),places=12)

    def test_exact_interaction_coefficient_identity(self):
        p=M.model().fit(self.train[M.FEATURES],
                          self.train.radiant_win.astype(int))
        f=M.evaluate_fit(self.train)
        implied=2*(math.log(2)-math.log(4)) * f["fitted_gold_interaction"]
        self.assertAlmostEqual(implied,
                f["logodds_difference_t10_minus_t30"],places=11)
        self.assertAlmostEqual(f["p2k_t10"],0.6649891894445361,places=11)
        self.assertAlmostEqual(f["p2k_t30"],0.5940371481769021,places=11)

    def test_split_and_scope(self):
        self.assertEqual(self.train.partition.unique().tolist(),["train"])
        self.assertEqual(self.train.match_id.nunique(),291)
        self.assertEqual(len(self.train),10675)

    def test_full_receipt_records_a_positive_train_only_mechanistic_effect(self):
        d=json.loads((ROOT/"research/CONDITIONAL_GOLD_VALUE_RECEIPT.json").read_text())
        self.assertEqual(d["evidence_class"],
                         "TRAIN_ONLY_POST_SELECTION_GOLD_EFFECT_NOT_HOLDOUT")
        self.assertFalse(d["model_selection_or_test_promotion"])
        self.assertEqual((d["train_games"],d["train_rows"]), (291,10675))
        self.assertEqual((d["groups"],d["identified_series"],d["standalone_games"]),
                         (171,149,22))
        self.assertEqual(d["draws"],2000)
        self.assertEqual(d["source_train_sha256"],M.TRAIN_SHA)
        self.assertEqual(d["source_manifest_sha256"],M.MANIFEST_SHA)
        self.assertAlmostEqual(d["primary"]["point"],0.27866112149160505,places=11)
        low,high=d["primary"]["percentile_ci_95"]
        self.assertGreater(low,0)
        self.assertGreater(high,low)
        self.assertEqual(d["primary"]["positive_draw_share"],1.0)
        self.assertAlmostEqual(d["secondary"]["point"],0.06438552434570177,places=11)
        self.assertEqual(d["M0_time_invariant_gold_logodds_difference"],0)
        self.assertAlmostEqual(d["point"]["p2k_t10"],0.6649891894445361,places=11)
        self.assertAlmostEqual(d["point"]["p2k_t30"],0.5940371481769021,places=11)

    def test_readout_rejects_causal_or_new_holdout_interpretation(self):
        text=(ROOT/"research/CONDITIONAL_GOLD_VALUE_READOUT.md").read_text()
        for term in ("TRAIN-only", "NOT a p-value", "not a causal",
                     "not causal", "proper score", "independent hostile review"):
            self.assertIn(term.lower(),text.lower())

    def test_numeric_parity_guard_rejects_large_drift_and_flags(self):
        example={"k":2,"x":{"p":.71,"effect":-.1,"arr":[.4,.8]},
                 "confirmed":False}
        eps=deepcopy(example);eps["x"]["p"]+=1e-7
        M.compare(eps,example)
        wrong=deepcopy(example);wrong["confirmed"]=True
        with self.assertRaises(ValueError):M.compare(wrong,example)
        wrong=deepcopy(example);wrong["x"]["arr"][1]+=.02
        with self.assertRaises(ValueError):M.compare(wrong,example)
        wrong=deepcopy(example);wrong["x"]["p"]=float("nan")
        with self.assertRaises(ValueError):M.compare(wrong,example)


if __name__=="__main__":
    unittest.main()
