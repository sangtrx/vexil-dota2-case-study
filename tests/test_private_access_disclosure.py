from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ExternalAccessTruthfulness(unittest.TestCase):
    def test_report_does_not_claim_access_already_granted(self):
        text=(ROOT/"REPORT.md").read_text()
        self.assertIn("Original research commits and branches are retained here",text)
        self.assertIn("no reviewer access granted",text)
        self.assertNotIn("reviewer access provided separately",text)

    def test_readme_does_not_claim_access_already_granted(self):
        text=(ROOT/"README.md").read_text()
        self.assertIn("Original GitHub PR discussions remain in a separately private repo",text)
        self.assertNotIn("reviewer access granted separately",text)

    def test_curated_source_history_is_kept_not_rewritten(self):
        text=(ROOT/"HISTORY.md").read_text()
        self.assertIn("inherits the real 13–15 November original research Git commit ancestry",text)
        self.assertIn("Selected historical branch heads are mirrored",text)
        self.assertIn("not backdated experiments",text)
        provenance=(ROOT/"docs/CURATION_PROVENANCE.md").read_text()
        self.assertIn("No commits are backdated",provenance)
        self.assertIn("original private research",provenance.lower())


if __name__=="__main__":
    unittest.main()
