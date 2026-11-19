"""Regression gates for separate September evidence and the reviewer ZIP.

No network, no model refit, and no newer TEST selection.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEPT=ROOT/"research/september_external"


class SeptemberEvidenceAndPackage(unittest.TestCase):
    def test_frozen_march_test_and_notebook_remain_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT/"live_dota2_win_probability.ipynb").read_bytes()).hexdigest(),
                         "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f")
        self.assertEqual(hashlib.sha256((ROOT/"artifacts/heldout_predictions.csv").read_bytes()).hexdigest(),
                         "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441")

    def test_september_result_offline_recomputed_without_retraining(self):
        p=subprocess.run([sys.executable,str(SEPT/"verify_external_results.py")],
                         cwd=ROOT,text=True,capture_output=True,check=True)
        self.assertEqual(p.stdout.count("PASS "),16)
        self.assertIn('"gate": "PASS"',p.stdout)
        self.assertIn('"groups": 104',p.stdout)
        self.assertIn('"usable": 199',p.stdout)
        self.assertIn("[-0.07426108485146404, -0.010789504736618624]",p.stdout)

    def test_all_28_candidates_in_reviewer_feature_map(self):
        text=(ROOT/"delivery/FEATURE_SCREEN_AND_FAILURES.md").read_text()
        section=text.split("## All 28 screened feature candidates",1)[1].split(
            "## 81 engineered fields",1)[0]
        rows=re.findall(r'^\| (P\d\d) \|.*\| NO \|$',section,flags=re.M)
        self.assertEqual(len(rows),28)
        self.assertEqual(len(set(rows)),28)
        self.assertEqual(set(rows),{"P"+f"{i:02d}" for i in range(1,29)})
        self.assertIn("September",text)
        self.assertIn("Roshan",text)

    def test_cross_cohort_science_not_hidden_or_oversold(self):
        report=(ROOT/"REPORT.md").read_text()
        atlas=(ROOT/"docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md").read_text()
        history=(ROOT/"HISTORY.md").read_text()
        for text in [report,atlas,history]:
            self.assertIn("September",text)
        self.assertIn("0.5844",report)
        self.assertIn("0.5448",report)
        self.assertIn("three leagues",report)
        self.assertIn("shadow",report)
        self.assertNotIn("That is a future decision rule",report)
        self.assertIn("10 active human hours",report)
        self.assertIn("remote agents ran much of",report)
        self.assertIn("outside the required 500",atlas)

    def test_frozen_zip_has_only_one_notebook_and_verifiable_series_ci(self):
        zip_path=ROOT/"delivery/Vexil_Dota2_Takehome_20261119.zip"
        with zipfile.ZipFile(zip_path) as z:
            names=z.namelist()
            self.assertEqual(sum(n.endswith(".ipynb") for n in names),1)
            self.assertIn("FEATURE_SCREEN_AND_FAILURES.md",names)
            self.assertIn("docs/SERIES_GROUPS_TEST.json",names)
            self.assertIn("research/verify_heldout_scores.py",names)
            self.assertIn("docs/CROSS_COHORT_EVIDENCE.md",names)
            self.assertNotIn("research/september_external/external_september_predictions.csv",names)
            manifest=json.loads(z.read("PACKAGE_MANIFEST.json"))
            self.assertEqual(set(manifest["files"]),set(names)-{"PACKAGE_MANIFEST.json"})
            for name,info in manifest["files"].items():
                b=z.read(name)
                self.assertEqual(len(b),info["bytes"])
                self.assertEqual(hashlib.sha256(b).hexdigest(),info["sha256"])
            self.assertTrue(z.testzip() is None)
            with tempfile.TemporaryDirectory() as temp:
                z.extractall(temp)
                cmd=[sys.executable,
                     str(Path(temp)/"research/verify_heldout_scores.py")]
                completed=subprocess.run(cmd,cwd=temp,text=True,capture_output=True,check=True)
                d=json.loads(completed.stdout)
                self.assertEqual((d["games"],d["minutes"],d["groups"]),(106,3836,54))
                self.assertTrue(d["series_CI_logloss"][1]>0)
                self.assertFalse(d["new_blind_test"])


if __name__=="__main__":
    unittest.main()
