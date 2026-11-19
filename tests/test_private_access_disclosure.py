from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ExternalAccessTruthfulness(unittest.TestCase):
    def test_report_does_not_claim_access_already_granted(self):
        text=(ROOT/"REPORT.md").read_text()
        self.assertIn("Original research commits and branches are retained",text)
        self.assertNotIn("reviewer access granted",text.lower())
        self.assertNotIn("no reviewer access granted",text.lower())
        self.assertNotIn("private PR discussions",text)
        self.assertNotIn("reviewer access provided separately",text)

    def test_readme_does_not_claim_access_already_granted(self):
        text=(ROOT/"README.md").read_text()
        self.assertIn("Original GitHub PR discussions remain in a separately private repo",text)
        self.assertNotIn("reviewer access granted separately",text)
        self.assertIn("this public GitHub repository",text)
        self.assertNotIn("this private research repository",text)

    def test_curated_source_history_is_kept_not_rewritten(self):
        text=(ROOT/"HISTORY.md").read_text()
        self.assertIn("The original research commits date from 13–15 November 2026",text)
        self.assertIn("docs/REVIEWER_HISTORY_MAP.md",text)
        self.assertIn("not backdated experiments",text)
        provenance=(ROOT/"docs/CURATION_PROVENANCE.md").read_text()
        self.assertIn("No commits are backdated",provenance)
        # This is a portable text/length check in ZIP-only QA. A fresh
        # Git clone separately verifies that the genuine original source
        # commit is an ancestor of the new main.
        source_main="5bff687aca176b82912a53d10f67ecaa7a73832a"
        self.assertEqual(len(source_main),40)
        self.assertIn(source_main,provenance)
        self.assertNotIn(source_main+"04",provenance)
        source_match=re.search(r"original research main was \*\*([0-9a-f]+)\*\*",provenance)
        self.assertIsNotNone(source_match)
        self.assertEqual(source_match.group(1),source_main)
        self.assertIn("original private research",provenance.lower())
        branch_index=(ROOT/"docs/REVIEWER_HISTORY_MAP.md").read_text()
        self.assertIn("All fourteen original PR #3–#16 head branches",branch_index)
        for n in range(3,17):
            self.assertIn(f"Actual PR #{n}",branch_index)
        self.assertIn("DRAFT / HOLD",branch_index)
        self.assertIn("This repository is **public**",branch_index)
        self.assertNotIn("This repository is **private**",branch_index)
        research_index=(ROOT/"docs/RECORDED_RESEARCH_BRANCHES.md").read_text()
        branch_rows=[line for line in research_index.splitlines()
                     if line.startswith("| "+chr(96))]
        self.assertEqual(len(branch_rows),18)
        self.assertIn("vexil-october-historical-holdout-20261117",research_index)
        self.assertIn("vexil-prospective-holdout-20261117",research_index)
        self.assertNotIn("This repository should remain private",research_index)


if __name__=="__main__":
    unittest.main()
