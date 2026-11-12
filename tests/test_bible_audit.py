"""Quality gates for the retrospective Bible-based research audit."""
from __future__ import annotations
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research/bible/results"

class BibleExperimentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((OUT/"stability_receipt.json").read_text())
        cls.cscv=pd.read_csv(OUT/"cscv_20_selections.csv")
        cls.oob=pd.read_csv(OUT/"series_oob_3000_selection.csv")

    def test_immutable_source_lineage(self):
        r=self.report
        src=ROOT/"research/results/dev_validation_predictions_28.csv"
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),r["input_predictions_sha256"])
        self.assertEqual(r["source_bible_main_sha"],"8e6374c8ac8c62da6611104555ce98f1cf40a528")
        self.assertTrue(r["no_model_fit"])
        self.assertTrue(r["no_api_calls"])
        self.assertEqual(r["new_independent_holdout_games"],0)

    def test_all_source_reproduction(self):
        self.assertEqual(self.report["models"],29)
        self.assertEqual(self.report["validation_games"],103)
        self.assertEqual(self.report["validation_series"],53)
        self.assertEqual(self.report["validation_minute_rows"],3784)
        rank=pd.read_csv(OUT/"all_estimator_weights.csv")
        self.assertEqual(len(rank),29)
        self.assertAlmostEqual(rank.loc[rank.model=="P20","minute_dll_vs_M1"].item(),-0.0052478275179806836,places=12)

    def test_block_selection_reversal(self):
        self.assertEqual(len(self.cscv),20)
        self.assertEqual(self.cscv.worse_than_panel_median.sum(),6)
        self.assertEqual((self.cscv.OOS_winner_minus_M1>0).sum(),10)
        self.assertEqual(set(self.cscv.OOS_rank.between(1,29)),{True})

    def test_series_oob_bootstrap(self):
        self.assertEqual(len(self.oob),3000)
        self.assertEqual((self.oob.winner_IS=="P20").sum(),1363)
        self.assertEqual((self.oob.OOB_winner_minus_M1>0).sum(),1544)
        self.assertTrue((self.oob.OOB_groups>0).all())

    def test_historical_trials_not_claimed_independent(self):
        rec=json.loads((OUT/"trial_ledger_receipt.json").read_text())
        ledger=pd.read_csv(OUT/"known_trial_ledger.csv")
        self.assertEqual(len(ledger),38)
        self.assertEqual(ledger.trial_id.nunique(),38)
        self.assertIsNone(rec["independent_trials_estimated"])
        self.assertTrue(rec["unknown_unrecorded_trials"])

    def test_hosted_kaggle_not_falsely_complete(self):
        m=json.loads((ROOT/"kaggle/hosted_run_manifest.json").read_text())
        self.assertEqual(len(m["kernels"]),3)
        self.assertTrue(m["private"])
        self.assertFalse(m["enable_internet"])
        self.assertFalse(m["enable_gpu"])
        self.assertTrue(m["do_not_claim_completed_kaggle_runs"])
        self.assertEqual(m["state"],"PREPARED_LOCALLY_NOT_UPLOADED_OR_EXECUTED")

if __name__=="__main__":
    unittest.main()
