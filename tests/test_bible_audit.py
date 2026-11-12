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
        self.assertEqual(self.cscv.complement_pair.nunique(),10)
        self.assertTrue(self.cscv.groupby("complement_pair").size().eq(2).all())
        self.assertEqual(self.cscv.worse_than_panel_median.sum(),6)
        self.assertEqual((self.cscv.OOS_winner_minus_M1>0).sum(),10)
        self.assertEqual(set(self.cscv.OOS_rank.between(1,29)),{True})

    def test_series_oob_bootstrap(self):
        self.assertEqual(len(self.oob),3000)
        self.assertEqual((self.oob.winner_IS=="P20").sum(),1363)
        self.assertEqual((self.oob.winner_IS=="M1_time_value").sum(),0)
        self.assertAlmostEqual(self.report["oob_selected_worse_given_non_m1"],1544/3000)
        self.assertEqual((self.oob.OOB_winner_minus_M1>0).sum(),1544)
        self.assertTrue((self.oob.OOB_groups>0).all())

    def test_historical_trials_not_claimed_independent(self):
        rec=json.loads((OUT/"trial_ledger_receipt.json").read_text())
        ledger=pd.read_csv(OUT/"known_trial_ledger.csv")
        self.assertEqual(len(ledger),38)
        self.assertEqual(ledger.trial_id.nunique(),38)
        self.assertIsNone(rec["independent_trials_estimated"])
        self.assertTrue(rec["unknown_unrecorded_trials"])

    def test_event_time_aware_chronology_limit(self):
        receipt=json.loads((OUT/"chronology_receipt.json").read_text())
        comp=pd.read_csv(OUT/"chronology_components.csv")
        x=pd.read_csv(OUT/"old_six_bucket_overlap_audit.csv")
        self.assertEqual(receipt["approx_disjoint_component_count"],4)
        self.assertEqual(comp.games.tolist(),[62,2,3,36])
        self.assertEqual(comp.series_groups.tolist(),[34,1,1,17])
        self.assertEqual(int(x.intervals_overlap.sum()),4)
        self.assertTrue(receipt["no_new_test_labels"])
        self.assertTrue(receipt["no_model_fit"])
        self.assertTrue(receipt["no_network_calls"])
        self.assertEqual(len(pd.read_csv(OUT/"chronology_4component_scores.csv")),116)

    def test_distinct_arithmetic_reference(self):
        rec=json.loads((OUT/"independent_stdlib_reference_receipt.json").read_text())
        self.assertEqual(rec["series_bootstrap_draws"],4000)
        self.assertEqual(rec["groups"],53)
        self.assertAlmostEqual(rec["p20_minus_m1_ll_minute_weighted"],-0.0052478275179806836)
        self.assertAlmostEqual(rec["p20_minus_m1_ll_equal_match"],-0.004491209735395407)
        self.assertAlmostEqual(rec["p20_minus_m1_ll_equal_series"],-0.002869279834146532)
        self.assertLess(rec["alternative_series_percentile95_lower"],0)
        self.assertGreater(rec["alternative_series_percentile95_upper"],0)
        self.assertTrue(rec["no_training"])

    def test_all_kaggle_sources_pinned(self):
        m=json.loads((ROOT/"kaggle/hosted_run_manifest.json").read_text())
        self.assertEqual(len(m["kernels"]),4)
        self.assertEqual(len(m["dataset_manifest_sha256"]),64)
        self.assertEqual(len(m["verification_script_sha256"]),64)
        self.assertTrue(all(len(k["notebook_sha256"])==64 for k in m["kernels"]))

    def test_hosted_kaggle_four_complete(self):
        m=json.loads((ROOT/"kaggle/hosted_run_manifest.json").read_text())
        receipt=json.loads((ROOT/"kaggle/hosted_run_verification_20261113.json").read_text())
        self.assertEqual(len(m["kernels"]),4)
        self.assertTrue(m["private"])
        self.assertFalse(m["enable_internet"])
        self.assertFalse(m["enable_gpu"])
        self.assertFalse(m["do_not_claim_completed_kaggle_runs"])
        self.assertEqual(m["state"],"HOSTED_COMPLETE_NUMERICALLY_VERIFIED")
        self.assertEqual(receipt["hosted_run_complete_count"],4)
        self.assertTrue(receipt["all_4_numeric_and_source_parity_pass"])
        self.assertTrue(receipt["no_new_holdout_scored"])
        self.assertTrue(receipt["no_model_retrained"])
        self.assertEqual(receipt["dataset_manifest_sha256"],m["dataset_manifest_sha256"])
        self.assertEqual(receipt["source_code_sha256"],m["verification_script_sha256"])

    def test_all_hosted_output_receipts_are_versioned(self):
        p=json.loads((ROOT/"kaggle/hosted_run_verification_20261113.json").read_text())
        expected={"scores","instability","maxt","chronology"}
        self.assertEqual(set(p["modes"]),expected)
        count=0
        for mode,r in p["modes"].items():
            self.assertEqual(r["remote_status"],"KernelWorkerStatus.COMPLETE")
            self.assertTrue(r["private_metadata_verified"])
            self.assertTrue(r["code_cell_matches_checked_in_source"])
            for filename,checksum in r["receipt_and_output_sha256"].items():
                file=ROOT/"research/bible/results/hosted_kaggle_20261113"/mode/filename
                self.assertTrue(file.is_file(),str(file))
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),checksum)
                count+=1
        self.assertEqual(count,9)  # four JSON receipts plus five numeric CSVs

if __name__=="__main__":
    unittest.main()
