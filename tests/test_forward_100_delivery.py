"""Smoke tests and adversarial tampering for the ZIP-only 100-game supplement."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
PROG=ROOT/"scripts/verify_forward_100.py"
spec=importlib.util.spec_from_file_location("vexil_forward_100_verifier",PROG)
VERIFY=importlib.util.module_from_spec(spec)
spec.loader.exec_module(VERIFY)

class ForwardEvidenceTests(TestCase):
    def test_independent_zip_csv_bootstrap_and_league_reproduction(self):
        result=VERIFY.verify()
        self.assertEqual(result["status"],"PASS_ZIP_ONLY_100_FROZEN_FORECAST_AUDIT")
        self.assertEqual(result["100_matches"],100)
        self.assertEqual(result["minute_rows"],4355)
        self.assertEqual(result["series_or_singletons"],56)
        self.assertEqual(result["leagues"],4)
        self.assertFalse(result["recomputed_original_500_model"])
        self.assertFalse(result["requires_original_raw_json"])
        self.assertLess(result["CI_M1_minus_M0_logloss"][0],0)
        self.assertGreater(result["CI_M1_minus_M0_logloss"][1],0)

    def test_original_500_scientific_forecasts_remain_frozen(self):
        file=ROOT/"artifacts/heldout_predictions.csv"
        self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),
                         VERIFY.EXPECTED_ORIGINAL_TEST_SHA)
        report=(ROOT/"REPORT.md").read_text()
        self.assertIn("106 TEST games",report)
        self.assertIn("3,836",report)
        self.assertIn("Patch 60 is not unseen",report)
        self.assertIn("100 already completed",report)
        self.assertIn("both contain zero",report.lower())

    def test_no_calendar_prospective_or_calibration_proven_claim(self):
        narrative=(ROOT/"docs/FORWARD_100_STRESS.md").read_text().lower()
        self.assertIn("played before",narrative)
        self.assertIn("four leagues",narrative)
        self.assertIn("ece deteriorated",narrative)
        self.assertIn("does not",narrative)
        self.assertNotIn("achieves statistically significant",narrative)

    def test_reject_mutated_probability_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"mutated.csv"
            orig=VERIFY.PRED.read_text()
            fields=orig.splitlines()
            parts=fields[1].split(",")
            parts[-1]="0.321654"
            fields[1]=",".join(parts)
            path.write_text("\n".join(fields)+"\n")
            with patch.object(VERIFY,"PRED",path),self.assertRaisesRegex(
                ValueError,"source predictions not matching|prediction|Forward evidence|Frozen"):
                VERIFY.verify()

    def test_reject_mutated_metadata_and_league(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"metadata.csv"
            orig=VERIFY.META.read_text()
            rows=orig.splitlines()
            head=rows[0].split(",")
            ix=head.index("league_id")
            cols=rows[1].split(",")
            cols[ix]="999999"
            rows[1]=",".join(cols)
            path.write_text("\n".join(rows)+"\n")
            with patch.object(VERIFY,"META",path),self.assertRaises(ValueError):
                VERIFY.verify()

    def test_reject_mutated_cohort_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"ids.json"
            data=json.loads(VERIFY.CANDIDATES.read_text())
            data["candidate_ids_and_start_times"][0]["match_id"]+=101
            path.write_text(json.dumps(data))
            with patch.object(VERIFY,"CANDIDATES",path),self.assertRaisesRegex(
                ValueError,"candidate listing provenance"):
                VERIFY.verify()

    def test_reject_forged_score_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"evidence.json"
            data=json.loads(VERIFY.EVIDENCE.read_text())
            data["forward_scores"]["M1"]["logloss"]-=.10
            path.write_text(json.dumps(data))
            with patch.object(VERIFY,"EVIDENCE",path),self.assertRaisesRegex(
                ValueError,"Forward evidence mismatch"):
                VERIFY.verify()

    def test_rejected_game_not_reintroduced_and_input_horizon_correct(self):
        e=json.loads(VERIFY.EVIDENCE.read_text())
        rejects=[row for row in e["cohort_collection_receipt"]["candidate_audit"]
                 if not row["accepted"]]
        self.assertEqual(len(rejects),1)
        self.assertEqual(rejects[0]["reason"],"unparsed_gold")
        self.assertNotIn(rejects[0]["match_id"],[
            row["match_id"] for row in e["cohort_collection_receipt"]["eligible"]])
        self.assertEqual(e["league_concentration_receipt"]["top_two_leagues_games"],85)
        self.assertTrue(e["newer_matches_predate_protocol"])
        self.assertTrue(e["source_provenance_and_method_self_attested"])

if __name__=="__main__":
    import unittest
    unittest.main()
