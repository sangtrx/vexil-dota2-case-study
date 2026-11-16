"""Unmerged TRAIN-only negative research, independently verifiable from ZIP.

Optional research appendices NEVER change frozen original M0/M1 or TEST.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


class OfflineHeldResearchEvidenceTest(unittest.TestCase):
    def run_research(self,*args):
        env=dict(os.environ)
        env["OPENBLAS_NUM_THREADS"]="1"
        env["OMP_NUM_THREADS"]="1"
        env["MKL_NUM_THREADS"]="1"
        result=subprocess.run([sys.executable,*args],cwd=ROOT,
            capture_output=True,text=True,timeout=150,env=env)
        self.assertEqual(result.returncode,0,result.stdout+"\n"+result.stderr)
        self.assertIn("PASS",result.stdout)

    def test_train_oof_calibration_offset_worsens_reused_validation_ece(self):
        doc=json.loads((ROOT/"research/CALIBRATION_FORWARD_RECEIPT.json").read_text())
        val=doc["reused_validation"]
        self.assertEqual(doc["inputs"]["test_games_read"],0)
        self.assertLess(val["M1_offset"]["logloss"],val["M1_original"]["logloss"])
        self.assertGreater(val["M1_offset"]["ece10"],val["M1_original"]["ece10"])
        self.assertLess(val["paired_comparison"]["series_bootstrap_95ci_logloss"][0],0.)
        self.assertGreater(val["paired_comparison"]["series_bootstrap_95ci_logloss"][1],0.)
        self.run_research("research/verify_calibration_offline.py")

    def test_gold_by_time_fails_stronger_additive_null_promotion_gate(self):
        doc=json.loads((ROOT/"research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json").read_text())
        self.assertEqual(doc["null_model"],["gold_k","minute10"])
        self.assertEqual(doc["oof_games"],137)
        self.assertEqual(doc["oof_rows"],5081)
        self.assertFalse(doc["original_validation_or_test_outcomes_read"])
        self.assertFalse(doc["model_promotion_permitted"])
        for metric in ("logloss","brier"):
            vals=doc["interaction_null_bootstrap"]["M1_minus_gold_time_null_"+metric]
            self.assertLess(vals["percentile_ci_95"][0],0.)
            self.assertGreater(vals["percentile_ci_95"][1],0.)
        self.run_research("research/gold_interaction_null_influence.py","--check")


if __name__=="__main__":
    unittest.main()
