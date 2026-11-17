"""Bounded frozen source-contract checks. No outcome scoring in unit tests."""
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from oct_nov_feature_transfer import MODEL_NAMES, SCOPE, MODEL_NAMES_INPUTS_ALL, paired_series_metric


class TransferContract(unittest.TestCase):
    def test_only_four_frozen_model_names(self):
        self.assertEqual(MODEL_NAMES,("M0_gold","M1_interaction","Q1_path","ALL"))
        self.assertEqual(len(MODEL_NAMES_INPUTS_ALL),12)

    def test_cohort_list_and_time_windows_immutable(self):
        self.assertEqual(list(SCOPE),["October","November"])
        self.assertEqual([SCOPE[x]["n_games"] for x in SCOPE],[180,22])
        self.assertEqual([SCOPE[x]["n_rows"] for x in SCOPE],[7346,952])

    def test_groups_bootstrap_cluster_not_minutes(self):
        # Two series containing overlapping minutes; dependent draws use clusters.
        f=pd.DataFrame({
            "match_id":[10,10,11,11],
            "series_id":[5,5,6,6],
            "minute":[0,1,0,1],
            "ll_A":[0.1,0.3,0.2,0.2],
            "ll_B":[0.2,0.2,0.1,0.2],
            "br_A":[0.1,0.1,0.1,0.1],
            "br_B":[0.2,0.2,0.2,0.2],
        })
        with self.assertRaisesRegex(AssertionError,"Missing minute 30"):
            paired_series_metric(f,"A","B",20261118)

    def test_source_rejects_unknown_missing_filename(self):
        from oct_nov_feature_transfer import check_scope_file
        with self.assertRaises(FileNotFoundError):
            check_scope_file(Path("/nonexistent"),"none.csv","fake")

if __name__=="__main__":
    unittest.main()
