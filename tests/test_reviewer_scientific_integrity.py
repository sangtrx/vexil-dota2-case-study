"""Independent, offline checks of scientific receipts and reviewer hyperlink integrity.

No fitting on TEST and no raw HTTP retrieval.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import posixpath
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


class ReviewerScientificIntegrityTest(unittest.TestCase):
    def test_development_only_asof_and_forward_fold_receipt(self):
        source = (ROOT / "research/development_asof_robustness.py").read_text()
        self.assertNotIn("heldout_predictions", source)
        self.assertNotIn("test.radiant_win", source)
        spec = importlib.util.spec_from_file_location(
            "vexil_development_robustness",
            ROOT / "research/development_asof_robustness.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = module.compute()
        module.verify(actual)
        self.assertEqual(len(actual["audit_script_sha256"]), 64)
        self.assertEqual(actual["source_access_manifest"], list(module.INPUTS))
        self.assertTrue(actual["verified_environment"]["python"].startswith("3.12."))
        # A falsified numerical receipt must fail even with float tolerance.
        forged = json.loads(json.dumps(actual))
        forged["asof"][4]["label_mature_val_subset_scores"]["M2_lead_fragility"]["logloss"] += .01
        with self.assertRaisesRegex(ValueError, "Float drift"):
            module.verify(forged)
        self.assertFalse(actual["forecast_test_records_read"])
        self.assertFalse(actual["live_received_at_verified"])
        self.assertEqual(actual["forward_pooled"]["minute_rows"], 5081)
        self.assertEqual(actual["asof"][4]["mature_train_games"], 277)
        self.assertEqual(actual["asof"][4]["mature_val_games_at_first_test"], 96)
        self.assertEqual(actual["asof"][4]["lowest_loss_on_mature_val_subset"],
                         "M2_lead_fragility")
        m2 = actual["asof"][4]["label_mature_val_subset_scores"]["M2_lead_fragility"]["logloss"]
        m1 = actual["asof"][4]["label_mature_val_subset_scores"]["M1_time_value"]["logloss"]
        self.assertAlmostEqual(m2, .517823, places=6)
        self.assertAlmostEqual(m1, .518090, places=6)
        self.assertLess(m2, m1)
        report = (ROOT / "REPORT.md").read_text()
        self.assertIn("0.517823 vs 0.518090", report)
        self.assertIn("not a verified label-arrival margin", report)
        limits = (ROOT / "docs/REVIEWER_SCIENTIFIC_LIMITS.md").read_text()
        self.assertIn("historical pre-correction commit 009f54d", limits)
        self.assertIn("Both forecast CSVs are now included", limits)

    def test_original_test_before_after_correction_is_independently_recomputed(self):
        spec = importlib.util.spec_from_file_location(
            "vexil_terminal_history",
            ROOT / "research/verify_terminal_correction_history.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.compute()
        expected = json.loads((ROOT / "docs/PRETERMINAL_TEST_CORRECTION_RECEIPT.json").read_text())
        module.compare(result, expected)
        self.assertEqual((result["preterminal_forecasts"], result["corrected_forecasts"]),
                         (3837, 3836))
        self.assertEqual(result["test_games"], 106)
        self.assertTrue(result["core_model_refit_after_test_inspection"])
        self.assertFalse(result["new_blind_test_claimed"])
        self.assertLess(result["previous"]["M1"]["logloss"],
                        result["corrected"]["M1"]["logloss"])
        self.assertEqual(len(result["only_removed_test_forecast_key"]), 2)
        # Reject altered historical scores, rather than only matching a phrase.
        corrupted = json.loads(json.dumps(result))
        corrupted["previous"]["M1"]["logloss"] += .01
        with self.assertRaisesRegex(ValueError, "Historical metric mismatch"):
            module.compare(corrupted, expected)

    def test_every_bundled_markdown_relative_link_resolves(self):
        # Check the exact source inventory of the ZIP, not the entire
        # machine-local repo, so private/non-bundled research is not implied.
        builder = ast.parse((ROOT / "scripts/create_submission_package.py").read_text())
        assignments = [node for node in builder.body
                       if isinstance(node, ast.Assign)
                       and any(isinstance(x, ast.Name) and x.id == "FILES"
                               for x in node.targets)]
        self.assertEqual(len(assignments), 1)
        files = set(ast.literal_eval(assignments[0].value))
        self.assertIn("docs/REVIEWER_SCIENTIFIC_LIMITS.md", files)
        self.assertIn("research/development_asof_robustness.py", files)
        checked = 0
        broken = []
        for path in sorted(f for f in files if f.endswith(".md")):
            text = (ROOT / path).read_text()
            for match in re.finditer(r"\]\(([^)]+)\)", text):
                link = match.group(1).strip().strip("<>").split('"')[0].strip()
                if not link or link.startswith("#"):
                    continue
                parts = urlparse(link)
                if parts.scheme in ("https", "http", "mailto") or parts.netloc:
                    continue
                if parts.scheme or parts.path.startswith("/"):
                    broken.append((path, link, "unexpected absolute scheme"))
                    continue
                dest = posixpath.normpath(posixpath.join(
                    posixpath.dirname(path), unquote(parts.path)
                ))
                checked += 1
                if dest not in files:
                    broken.append((path, link, dest))
        self.assertGreaterEqual(checked, 95)
        self.assertEqual(broken, [], f"Broken bundled Markdown links: {broken}")
