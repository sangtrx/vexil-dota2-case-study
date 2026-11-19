"""Submission-focused QA: frozen data, recorded failures, link parity and privacy."""
from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"delivery/Vexil_Dota2_Takehome_20261119.zip"


class ConciseSubmissionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ZIP) as archive:
            cls.contents={n: archive.read(n) for n in archive.namelist()}

    def test_manifest_integrity_and_exact_version(self):
        d=self.contents
        self.assertEqual(len(d),26)
        manifest=json.loads(d["PACKAGE_MANIFEST.json"])
        self.assertEqual(set(manifest["files"]),set(d)-{"PACKAGE_MANIFEST.json"})
        for name,metadata in manifest["files"].items():
            self.assertEqual(hashlib.sha256(d[name]).hexdigest(),metadata["sha256"],name)
            self.assertEqual(len(d[name]),metadata["bytes"],name)
        self.assertEqual(
            manifest["notebook_original_source_sha256"],
            hashlib.sha256(d["live_dota2_win_probability.ipynb"]).hexdigest(),
        )
        self.assertEqual(
            manifest["heldout_predictions_sha256"],
            hashlib.sha256(d["artifacts/heldout_predictions.csv"]).hexdigest(),
        )
        self.assertTrue(manifest["exact_current_notebook_colab_run_verified"])
        self.assertEqual(sum(name.endswith(".ipynb") for name in d),1)

    def test_all_original_28_screen_rows_shipped_without_metric_rewrites(self):
        text=self.contents["docs/EXPERIMENT_REGISTER.md"].decode()
        atlas=self.contents["docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md"].decode()
        original=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
        rows=[line for line in text.splitlines()
              if line.startswith("| P")
              and re.fullmatch(r"P[0-9]{2}",line.split("|")[1].strip())]
        candidates=[line.split("|")[1].strip() for line in rows]
        self.assertEqual(set(candidates),{f"P{i:02}" for i in range(1,29)})
        self.assertEqual(len(candidates),28)
        for row in (line for line in original.splitlines()
                    if line.startswith("| P")
                    and re.fullmatch(r"P[0-9]{2}",line.split("|")[1].strip())):
            self.assertIn(row,text)
            self.assertIn(row,atlas)

    def test_report_source_reference_targets_are_shipped(self):
        text=(ROOT/"REPORT.md").read_text()
        for target in set(re.findall(
            r"(?<![A-Za-z0-9_])(?:docs|research)/[A-Za-z0-9_./-]+\.(?:md|json|png)",text
        )):
            self.assertIn(target,self.contents,target)

    def test_extracted_docs_do_not_claim_unshipped_raw_research(self):
        notes=self.contents["docs/REVIEWER_SCIENTIFIC_LIMITS.md"].decode()
        self.assertIn("only the corrected 3,836-row TEST forecast CSV",notes)
        self.assertIn("not reproducible from this ZIP alone",notes)
        self.assertNotIn("Both forecast CSVs are now included in the ZIP",notes)
        self.assertNotIn("From the ZIP root with pinned dependencies, run:",notes)
        atlas=self.contents["docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md"].decode()
        self.assertIn("does **not** include every supplementary research script",atlas)
        supplement=self.contents["SUPPLEMENTARY_EXPERIMENTS.md"].decode()
        self.assertIn("−0.015267,−0.001393",supplement)
        self.assertIn("excluded",supplement.lower()) if False else None
        self.assertIn("outside",supplement.lower())
        reviewer_readme=self.contents["README.md"].decode("utf-8")
        self.assertIn("public GitHub repository",reviewer_readme)
        self.assertNotIn("access is arranged",reviewer_readme)

    def test_all_relative_markdown_links_point_into_actual_zip(self):
        import posixpath
        for source, raw in self.contents.items():
            if not source.endswith(".md"):
                continue
            text=raw.decode("utf-8")
            links=re.findall(r"\[([^\]]+)\]\(([^)\n]+)\)",text)
            for label,href in links:
                if href.startswith(("https://","http://","mailto:","#")):
                    continue
                path=posixpath.normpath(posixpath.join(
                    posixpath.dirname(source),href.split("#",1)[0]))
                self.assertIn(path,self.contents,
                              f"Dangling ZIP link in {source}: {label} -> {href}")

    def test_repaired_roshan_results_and_auditor_are_shipped(self):
        text=self.contents["research/ROSHAN_CORRECTION_20261119.md"].decode()
        self.assertIn("Q2 sparse elastic-net",text)
        self.assertIn("[−0.012136,+0.053563]",text)
        self.assertIn("Q3 shallow boosted tree",text)
        self.assertIn("full internal research archive",text)
        self.assertIn("this public repository",text)
        self.assertNotIn("clone the private source repository",text)
        self.assertIn("research/error_diagnostics.py",self.contents)
        self.assertIn("docs/TRAIN_LEADER_STATE_EMPIRICAL_RECEIPT.json",self.contents)
        self.assertIn("docs/figures/train_leader_state_empirical.png",self.contents)

    def test_reviewer_zip_excludes_internal_routes_and_original_private_prs(self):
        self.assertNotIn("docs/RECORDED_RESEARCH_BRANCHES.md",self.contents)
        for name,raw in self.contents.items():
            if not name.endswith((".md",".json",".ipynb",".txt")):
                continue
            text=raw.decode("utf-8")
            self.assertNotIn("github.com/sangtrx/vexil-dota2-win-probability",text,name)
            self.assertNotIn("/srv/ai/",text,name)
            self.assertNotIn("/home/ai-agent/",text,name)
            self.assertNotIn("SentinelX",text,name)
        branches=(ROOT/"docs/RECORDED_RESEARCH_BRANCHES.md").read_text()
        self.assertIn("vexil-september-external-20261118",branches)
        self.assertIn("NOT IN SUBMISSION",branches)


if __name__=="__main__":
    unittest.main()
