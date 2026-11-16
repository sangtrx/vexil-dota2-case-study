"""Reviewer single-notebook extension: original 14 science code cells never edited."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import nbformat

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"research/frozen_original_500_notebook.ipynb"
MAIN=ROOT/"live_dota2_win_probability.ipynb"
PIT=ROOT/"research/reviewer_notebook_pit_appendix.py"
ANALYSIS=ROOT/"research/reviewer_notebook_report_appendix.py"
RECEIPT=ROOT/"docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json"
ORIGINAL_SHA="5e016e61badc3f28bce50f5a692da4a143f8255dc586ad7f429d07e42726ecca"


def sha(b):
    return hashlib.sha256(b).hexdigest()


class ReviewerNotebookAppendixContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads(RECEIPT.read_text())
        cls.original=nbformat.read(FROZEN,as_version=4)
        cls.current=nbformat.read(MAIN,as_version=4)

    def test_original_science_code_and_saved_output_archive_unchanged(self):
        self.assertEqual(sha(FROZEN.read_bytes()),ORIGINAL_SHA)
        self.assertEqual(len(self.original.cells),26)
        self.assertEqual(sum(c.cell_type=="code" for c in self.original.cells),14)
        self.assertEqual(len(self.current.cells),29)
        self.assertEqual(sum(c.cell_type=="code" for c in self.current.cells),16)
        self.assertEqual(
            [(c.cell_type,c.source) for c in self.current.cells[:26]],
            [(c.cell_type,c.source) for c in self.original.cells])

    def test_two_selfcontained_appendix_cells_have_saved_real_outputs(self):
        nb=self.current
        self.assertEqual(nb.cells[27].source,PIT.read_text())
        self.assertEqual(nb.cells[28].source,ANALYSIS.read_text())
        self.assertEqual([c.cell_type for c in nb.cells[-3:]],["markdown","code","code"])
        self.assertIn("after TEST inspection",nb.cells[26].source)
        code=[c for c in nb.cells if c.cell_type=="code"]
        self.assertEqual([c.execution_count for c in code],list(range(1,17)))
        self.assertEqual(len([c for c in code if not c.outputs]),1)
        output="\n".join(
            str(o.get("text","")) for c in nb.cells[27:29]
            for o in c.outputs if o.get("output_type")=="stream"
        )
        for value in ("18,292/18,292","2,500 first-five-minute",
                      "TRAIN-only gold×time vs stronger gold+time NULL",
                      "CI includes zero","Model decision preserved"):
            self.assertIn(value,output)
        self.assertTrue(all(c.execution_count is not None and c.outputs
                            for c in nb.cells[27:29]))
        self.assertEqual(sum("image/png" in o.get("data",{})
              for c in code for o in c.outputs),4)
        self.assertTrue(all(o.get("output_type")!="error"
                            for c in code for o in c.outputs))

    def test_offline_receipt_pins_reviewer_notebook_and_core_provenance(self):
        r=self.receipt
        self.assertEqual(r["status"],"APPEND_ONLY_REVIEWER_NOTEBOOK_SOURCE_FROZEN_QA")
        self.assertEqual(r["source_science_notebook_sha256"],ORIGINAL_SHA)
        self.assertEqual(r["new_reviewer_notebook_sha256"],sha(MAIN.read_bytes()))
        self.assertEqual(r["appended_code_cells"],2)
        self.assertEqual(r["executed_total_code_cells"],16)
        self.assertEqual(r["unchanged_scientific_code_sha256"],
                         "e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b")
        self.assertEqual(r["heldout_3836_csv_sha256"],
                         "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441")
        self.assertTrue(r["all_18292_minute_PIT_checks_passed"])
        self.assertFalse(r["cloud_extended_appendix_replay_verified"])
        self.assertTrue(r["original_test_previously_inspected"])
        self.assertEqual(r["appendix_source_sha256"]["PIT"],sha(PIT.read_bytes()))
        self.assertEqual(r["appendix_source_sha256"]["report_crosswalk"],sha(ANALYSIS.read_bytes()))

    def test_model_no_heldout_refit_in_appendix(self):
        pit=PIT.read_text()
        m=ANALYSIS.read_text()
        self.assertIn("reviewer_feature_prefix",pit)
        self.assertIn("reviewer_pre_full_window == 2500",pit)
        self.assertIn("TRAIN-only",m)
        self.assertIn("train[train.match_id.isin(mature_ids)]",m)
        self.assertIn("reviewer_forward_ci",m)
        self.assertNotIn("/matches/",pit+m)
        self.assertNotIn("/proMatches",pit+m)
        self.assertNotIn("fit_model(test",m)
        self.assertNotIn("fit_model(validation",m)


if __name__=="__main__":
    unittest.main()
