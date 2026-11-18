"""Compact integrity gates for research-only September readouts."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research/external_september'

class ExternalSeptemberReceipts(unittest.TestCase):
    def test_bundled_external_receipt_and_csv_hash_consistent(self):
        r=json.loads((HERE/'external_september_scores.json').read_text())
        csv=HERE/'external_september_predictions.csv'
        self.assertEqual(hashlib.sha256(csv.read_bytes()).hexdigest(),r['scored_predictions_sha256'])
        self.assertEqual(r['selected_count'],200)
        self.assertEqual(r['usable_count'],199)
        self.assertEqual(r['minute_rows'],8740)
        self.assertEqual(r['series_or_singleton_groups'],104)
        self.assertEqual(r['frozen_external_support_gate'],'PASS')

    def test_posthoc_additive_is_explicitly_not_preregistered(self):
        r=json.loads((HERE/'posthoc_additive_null_receipt.json').read_text())
        self.assertIn('POST-HOC',r['scope'].upper())
        self.assertAlmostEqual(r['m1_minus_additive_ll'],-0.04134914121271521,places=10)
        self.assertGreater(r['m1_minus_additive_group_ci95'][1],-0.02)
        self.assertLess(r['m1_minus_additive_group_ci95'][1],0)

    def test_influence_and_original_benchmark_are_unchanged(self):
        r=json.loads((HERE/'posthoc_influence_receipt.json').read_text())
        self.assertIn('post-hoc',r['scope'].lower())
        self.assertEqual(r['teams']['distinct_teams'],33)
        self.assertEqual(r['teams']['team_match_graph_components'],3)
        self.assertTrue(r['teams']['all_leave_one_team_deltas_negative'])
        self.assertGreater(r['remove_most_favorable_matches']['5']['cluster_CI95'][1],0)
        employer=ROOT/'delivery/Vexil_Dota2_Creative_Research_20261118.zip'
        self.assertEqual(hashlib.sha256(employer.read_bytes()).hexdigest(),
                         '982528c82ba2dd5ee06f725ef360aa77561e5987e1c8992c9a51f77a91846568')

if __name__=='__main__':
    unittest.main()
