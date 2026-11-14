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
            self.assertIn(f"/pull/{pr}", text)
        for phrase in ("0/28", "previously inspected", "M4", "S2",
                       "stage gate", "24,126", "not a second", "[-0.016929,+0.006434]"):
            self.assertIn(phrase.lower(),text.lower())

    def test_report_figures_and_rendered_pdf_are_present(self):
        markdown = (ROOT / "REPORT.md").read_text(encoding="utf8")
        for relative in (
            "docs/figures/heldout_reliability.png",
            "docs/figures/time_value_scenarios.png",
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
        self.assertIn("no longer an independent test", markdown)
        self.assertTrue((ROOT/"REPORT.pdf").read_bytes().startswith(b"%PDF-"))
        if shutil.which("pdfinfo"):
            info = subprocess.check_output(["pdfinfo", str(ROOT/"REPORT.pdf")],text=True)
            pages = [int(x.split(":",1)[1]) for x in info.splitlines()
                     if x.startswith("Pages:")]
            self.assertEqual(len(pages), 1)
            self.assertLessEqual(pages[0],4)
        if shutil.which("pdfimages"):
            listings = subprocess.check_output(["pdfimages","-list",str(ROOT/"REPORT.pdf")],text=True)
            actual_lines = [x for x in listings.splitlines() if x.lstrip()[:1].isdigit()]
            self.assertGreaterEqual(len(actual_lines),2)


if __name__ == "__main__":
    unittest.main()
