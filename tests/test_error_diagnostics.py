"""Read-only test of frozen held-out error attribution, no API or model fitting."""
from __future__ import annotations

import csv
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE_PATH=ROOT/"research"/"error_diagnostics.py"
spec=importlib.util.spec_from_file_location("vexil_error_diagnostics",MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load optional error diagnostics")
error=importlib.util.module_from_spec(spec)
spec.loader.exec_module(error)


class ErrorDiagnosticsContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=error.load_rows()
        cls.audit=error.audit(cls.rows)

    def test_snapshot_and_metrics_are_exactly_frozen(self):
        error.acceptance(self.audit)
        self.assertEqual(self.audit["overall"]["minute_rows"],3836)
        self.assertEqual(self.audit["overall"]["matches"],106)
        self.assertEqual(self.audit["minute_zero"]["minute_rows"],106)

    def test_rendered_chart_avoids_claiming_a_confirmed_phase_reversal(self):
        source=(ROOT/"research/render_error_figure.py").read_text()
        self.assertIn("Brier difference by phase (descriptive)",source)
        self.assertNotIn("Brier gain reverses at minute 30+",source)

    def test_posthoc_late_phase_worsens_brier_and_calibration(self):
        phase=self.audit["by_phase"]
        self.assertEqual([phase[k]["minute_rows"] for k in error.PHASES],
                         [1060,1060,997,719])
        self.assertGreater(phase["30+"]["delta_brier_M1_minus_M0"],0)
        self.assertGreater(phase["30+"]["M1_10bin_ECE"],
                           phase["30+"]["M0_10bin_ECE"])
        self.assertLess(phase["0-9"]["delta_brier_M1_minus_M0"],0)

    def test_influence_is_grouped_by_whole_match(self):
        top=self.audit["most_influential_5_matches"][0]
        self.assertEqual((top["match_id"],top["forecast_minutes"]), (8744971178,55))
        self.assertAlmostEqual(top["fraction_of_total_signed_gain"],.5492191868375483,places=10)
        self.assertAlmostEqual(top["all_other_matches_delta_ll"],-.005684587178237208,places=10)

    def test_serialized_receipt_parity_and_source_drift(self):
        saved=json.loads((ROOT/"docs"/"ERROR_AUDIT_RECEIPT.json").read_text(encoding="utf8"))
        self.assertEqual(saved,self.audit)
        forged=json.loads(json.dumps(saved))
        forged["source_forecasts_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Frozen"):
            error.acceptance(forged)

    def test_invalid_probabilities_and_duplicate_match_minute_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="vexil-error-audit-") as d:
            path=Path(d)/"bad.csv"
            head=["match_id","minute","p_model","p_baseline","radiant_win"]
            def write(rows):
                with path.open("w",encoding="utf8",newline="") as fh:
                    w=csv.writer(fh)
                    w.writerow(head)
                    w.writerows(rows)
            good=[8744971178,0,.55,.52,1]
            write([good,good])
            with self.assertRaisesRegex(ValueError,"duplicate"):
                error.load_rows(path)
            write([[8744971178,0,1.2,.52,1]])
            with self.assertRaisesRegex(ValueError,"Probability"):
                error.load_rows(path)
            write([good,[8744971178,1,.56,.52,0]])
            with self.assertRaisesRegex(ValueError,"time-varying"):
                error.load_rows(path)

    def test_posthoc_series_clustering_reproduces_saved_receipt(self):
        path=ROOT/"research"/"series_cluster_sensitivity.py"
        spec=importlib.util.spec_from_file_location("vexil_series_sensitivity",path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual=module.compute()  # Offline only. Never refits the model.
        self.assertEqual(actual["series_clusters"],54)
        self.assertEqual(actual["minute_rows"],3836)
        self.assertGreater(actual["series_bootstrap_delta_ll_ci"][1],0)
        self.assertLess(actual["series_bootstrap_delta_brier_ci"][1],0)

    def test_chart_and_document_are_review_artifacts_only(self):
        doc=(ROOT/"docs"/"ERROR_ANALYSIS.md").read_text(encoding="utf8")
        self.assertIn("post-hoc",doc.lower())
        self.assertIn("54.92%",doc)
        self.assertIn("no fitting",doc.lower())
        src=(ROOT/"research"/"render_error_figure.py").read_text(encoding="utf8")
        self.assertIn("ERROR_AUDIT_RECEIPT.json",src)
        png=(ROOT/"docs"/"figures"/"phase_error_audit.png").read_bytes()
        self.assertEqual(png[:8],b"\x89PNG\r\n\x1a\n")
        w,h=struct.unpack(">II",png[16:24])
        self.assertGreater(w,1000)
        self.assertGreater(h,450)


if __name__=="__main__":
    unittest.main()
