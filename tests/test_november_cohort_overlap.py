"""Mandatory non-independence disclosure for November 100 and 120 samples."""
from __future__ import annotations
import csv, hashlib, importlib.util, json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("vexil_cohort_overlap",
                                          ROOT/"scripts/verify_november_cohort_overlap.py")
audit=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CohortOverlapTest(unittest.TestCase):
    def test_archived_cohort_overlap_is_exact_and_not_counted_as_replication(self):
        recorded=json.loads((ROOT/"docs/NOVEMBER_COHORT_OVERLAP_RECEIPT.json").read_text())
        actual=audit.verify()
        self.assertEqual(actual,recorded)
        self.assertEqual(actual["shared_games"],68)
        self.assertEqual(actual["new_100_only_games"],32)
        self.assertEqual(actual["archived_120_only_games"],52)
        self.assertTrue(actual["no_independent_replication_claim"])
        self.assertTrue(actual["do_not_pool_100_and_120_scores"])
        report=(ROOT/"REPORT.md").read_text().lower()
        supplement=(ROOT/"docs/FORWARD_100_STRESS.md").read_text().lower()
        self.assertIn("sixty-eight of these games",report)
        self.assertIn("not independent replications",report)
        self.assertIn("68 common game ids",supplement)
        self.assertIn("not two independent temporal replications",supplement)
        self.assertIn("not before all previous looks",supplement)
        self.assertIn("68/100 outcomes were available",supplement)

    def test_rejects_archived_research_manifest_replacement(self):
        with TemporaryDirectory() as tmp:
            fake=Path(tmp)/"older.csv"
            fake.write_text("match_id,start_time\n101,1000\n")
            with patch.object(audit,"OLD_120",fake):
                with self.assertRaisesRegex(ValueError,"SHA differs"):
                    audit.verify()

    def test_rejects_current_100_game_selection_replacement(self):
        with TemporaryDirectory() as tmp:
            fake=Path(tmp)/"current.csv"
            fake.write_text("match_id\n1\n")
            with patch.object(audit,"MAIN_100",fake):
                with self.assertRaisesRegex(ValueError,"SHA differs"):
                    audit.verify()


if __name__=="__main__":
    unittest.main()
