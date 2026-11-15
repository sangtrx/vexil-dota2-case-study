"""Static report-to-figure packaging checks, no model rerun or network."""
from __future__ import annotations

import shutil
import struct
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReportDeliveryContractTest(unittest.TestCase):
    def test_full_experiment_register(self):
        import re
        text = (ROOT / "docs/EXPERIMENT_REGISTER.md").read_text(encoding="utf8")
        candidates = re.findall(r"^\| (P\d{2}) \|", text, flags=re.M)
        self.assertEqual(len(candidates), 28)
        self.assertEqual(set(candidates), {f"P{i:02d}" for i in range(1,29)})
        for pr in range(3,12):
            self.assertIn(f"| [#{pr}](https://github.com/sangtrx/vexil-dota2-win-probability/pull/{pr}) |", text)
        self.assertIn("https://github.com/sangtrx/vexil-dota2-win-probability/pull/", text)
        for phrase in ("0/28", "previously inspected", "M4", "S2",
                       "stage gate", "24,126", "not a second", "[-0.016929,+0.006434]"):
            self.assertIn(phrase.lower(),text.lower())

    def test_fable_handoff_truth_and_historical_provenance(self):
        report=(ROOT/"REPORT.md").read_text(encoding="utf8")
        readme=(ROOT/"README.md").read_text(encoding="utf8")
        register=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text(encoding="utf8")
        self.assertIn("[−0.0304,+0.0014]",report)
        self.assertIn("[-0.0304, +0.0014]",readme)
        self.assertNotIn("[-0.0303, +0.0014]",readme)
        for token in ("28-way adjusted","[−0.0169,+0.0064]","pre-correction",
                      "reused validation","at least 38","none of the 28"):
            self.assertIn(token.lower(),report.lower())
        self.assertIn("[-0.016929,+0.006434]",register)
        self.assertIn("Claude Sonnet/Fable with review",report)
        self.assertIn("AI reviews are not independent human peer review",report)
        self.assertIn("10 hours of active work",report)
        self.assertIn("No third-party Dota predictor was copied",report)
        self.assertNotIn("https://github.com/sangtrx/vexil-dota2-assessment",report)
        self.assertIn("vexil-dota2-win-probability/blob/main/",report)
        self.assertIn("Original commits and PRs",readme)

    def test_reviewer_text_matches_scientific_boundaries(self):
        import json
        notebook=json.loads((ROOT / "live_dota2_win_probability.ipynb").read_text())
        text="\n".join("".join(c["source"]) for c in notebook["cells"]
                       if c["cell_type"]=="markdown")
        report=(ROOT / "REPORT.md").read_text()
        readme=(ROOT / "README.md").read_text()
        pkg=(ROOT / "SUBMISSION_PACKAGE_README.md").read_text()
        self.assertIn("strictly before match end", text)
        self.assertNotIn("through match end", text)
        self.assertIn("60*t < duration", text)
        self.assertIn("strict pre-terminal", report)
        self.assertIn("10 hours", text)
        self.assertIn("10 hours", report)
        self.assertIn("10 hours", readme)
        self.assertIn("10 active work hours", pkg)
        self.assertIn("106", report)
        self.assertIn("3,836", pkg)

    def test_report_figures_and_rendered_pdf_are_present(self):
        markdown = (ROOT / "REPORT.md").read_text(encoding="utf8")
        for relative in (
            "docs/figures/heldout_reliability.png",
            "docs/figures/time_value_scenarios.png",
            "docs/figures/phase_error_audit.png",
        ):
            self.assertIn("](" + relative + ")", markdown)
            source = (ROOT / relative).read_bytes()
            self.assertEqual(source[:8], bytes([137, 80, 78, 71, 13, 10, 26, 10]))
            width, height = struct.unpack(">II", source[16:24])
            self.assertGreater(width, 600)
            self.assertGreater(height, 400)
            self.assertGreater(len(source), 25000)
        self.assertIn("**Result:**", markdown)
        self.assertIn("**Assistance disclosure:**", markdown)
        self.assertIn("**Time spent:**", markdown)
        self.assertIn("not** an independent held-out test", markdown)
        self.assertTrue((ROOT/"REPORT.pdf").read_bytes().startswith(b"%PDF-"))
        if shutil.which("pdfinfo"):
            info = subprocess.check_output(["pdfinfo", str(ROOT/"REPORT.pdf")],text=True)
            pages = [int(x.split(":",1)[1]) for x in info.splitlines()
                     if x.startswith("Pages:")]
            self.assertEqual(len(pages), 1)
            self.assertLessEqual(pages[0],4)
        if shutil.which("pdfinfo"):
            annotations=subprocess.check_output(["pdfinfo","-url",str(ROOT/"REPORT.pdf")],text=True)
            self.assertNotIn("file:///",annotations)
            self.assertIn("https://github.com/",annotations)
        if shutil.which("pdfimages"):
            listings = subprocess.check_output(["pdfimages","-list",str(ROOT/"REPORT.pdf")],text=True)
            actual_lines = [x for x in listings.splitlines() if x.lstrip()[:1].isdigit()]
            self.assertGreaterEqual(len(actual_lines),3)


if __name__ == "__main__":
    unittest.main()
