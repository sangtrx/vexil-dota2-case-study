"""Regression: executing an unchanged notebook must not rewrite released evidence.

The real 500-match fresh-kernel replay first exposed a false FAIL on 16 Nov
2026: Jupyter execution timestamps/stream boundaries varied, so the runner
overwrote the submitted notebook and compared its unstable whole-file SHA to
the original reviewer receipt. These are not changes in scientific output.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import nbformat
from research import reviewer_notebook_appendix_replay as qa
from research import full_notebook_replay as base_replay


class ReviewerNotebookReceiptIdempotencyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.notebook = self.root / "live_dota2_win_probability.ipynb"
        self.receipt = self.root / "REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json"
        shutil.copyfile(qa.MAIN, self.notebook)
        shutil.copyfile(qa.RECEIPT, self.receipt)
        self.initial_notebook_sha = self.sha(self.notebook)
        self.initial_receipt_sha = self.sha(self.receipt)
        self.out_dir = self.root / "replayed"

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def fake_full_replay(self, unused_cache, out_dir):
        """A scientific-equivalent notebook with a different execution clock."""
        out_dir.mkdir(parents=True, exist_ok=False)
        nb = nbformat.read(str(self.notebook), as_version=4)
        nb.cells[2].metadata["execution"] = {
            "iopub.status.busy": "2030-01-01T00:00:01Z",
            "iopub.status.idle": "2030-01-01T00:00:03Z",
        }
        nbformat.write(nb, str(out_dir / "executed_fresh_kernel.ipynb"))
        self.assertNotEqual(self.sha(self.notebook),
                            self.sha(out_dir / "executed_fresh_kernel.ipynb"))
        return {
            "source_code_sha256": base_replay.EXPECTED_NOTEBOOK_CODE_SHA,
            "executed_code_cells": 16,
            "cell_execution_errors": 0,
            "zero_http_calls": True,
            "cache_hits": 500,
            "report_figures_byte_equal_to_notebook_outputs": True,
            "local_fresh_kernel_test_csv_byte_parity_verified": True,
        }

    def run_replay_with_mocked_kernel(self):
        with (
            patch.object(qa, "MAIN", self.notebook),
            patch.object(qa, "RECEIPT", self.receipt),
            patch.object(base_replay, "execute_replay",
                         side_effect=self.fake_full_replay)
        ):
            qa.execute(self.root / "unused_raw_cache", self.out_dir)

    def test_replay_receipt_uses_released_notebook_and_leaves_it_untouched(self):
        # RED on original code: raises "Existing reviewed appendix receipt
        # would be overwritten"; original code also modifies notebook bytes.
        self.run_replay_with_mocked_kernel()
        self.assertEqual(self.sha(self.notebook), self.initial_notebook_sha)
        self.assertEqual(self.sha(self.receipt), self.initial_receipt_sha)
        self.assertTrue((self.out_dir / "executed_fresh_kernel.ipynb").is_file())

    def test_frozen_heldout_hash_is_a_real_fail_closed_check(self):
        # Guard the opposite failure: actual scientific evidence must still
        # fail replay even if the notebook/metadata itself is unchanged.
        with patch.object(qa, "EXPECTED_TEST_SHA", "0" * 64):
            with self.assertRaisesRegex(ValueError, "Original heldout results changed"):
                self.run_replay_with_mocked_kernel()
        self.assertEqual(self.sha(self.notebook), self.initial_notebook_sha)
        self.assertEqual(self.sha(self.receipt), self.initial_receipt_sha)


if __name__ == "__main__":
    unittest.main()
