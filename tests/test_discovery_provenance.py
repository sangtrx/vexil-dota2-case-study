"""Verify that reviewer replay is grounded in the original 13-Nov cohort.

Checks run from the shipped ZIP; no Git metadata, external API or raw match
payload is required. The historical discovery request counts remain an
author-recorded provenance claim, NOT independent network telemetry.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_ID_SHA256 = "f2be53e16ae29df1f62aa9907187fdba846d9af9fb7a3f69e7dd7504be43b776"
MANIFEST_SHA256 = "e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea"


def notebook_source(file_name):
    nb = json.loads((ROOT / file_name).read_text(encoding="utf8"))
    return "\n".join("".join(c.get("source", []))
                     for c in nb["cells"] if c["cell_type"] == "code")


def ordered_frozen_ids(source):
    match = re.search(r"FROZEN_MATCH_IDS\s*=\s*(\([\d,\s]+\))", source)
    if not match:
        raise AssertionError("Frozen match IDs absent or malformed")
    ids = ast.literal_eval(match.group(1))
    if not isinstance(ids, tuple):
        raise AssertionError("Expected tuple of fixed game IDs")
    return ids


class DiscoveryProvenanceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = notebook_source("live_dota2_win_probability.ipynb")
        cls.original = notebook_source("research/frozen_original_notebook_source.json")

    def test_unchanged_500_ids_match_historical_source_digest(self):
        current = ordered_frozen_ids(self.current)
        original = ordered_frozen_ids(self.original)
        self.assertEqual(current, original)
        self.assertEqual(len(current), 500)
        self.assertEqual(len(set(current)), 500)
        actual = hashlib.sha256(json.dumps(list(current)).encode("utf8")).hexdigest()
        self.assertEqual(actual, ORIGINAL_ID_SHA256)
        self.assertIn(MANIFEST_SHA256, self.current)
        self.assertIn(MANIFEST_SHA256, self.original)

    def test_original_pagination_and_frozen_run_are_both_present_and_explained(self):
        for source in (self.current, self.original):
            for token in ('api.get("/proMatches"', '"less_than_match_id"',
                          "for rec in page[:3]:", "COHORT_N",
                          "def collect_matches(api, frozen=()):",
                          "collect_matches(api, FROZEN_MATCH_IDS)",
                          '"/matches/"'):
                self.assertIn(token, source)
        provenance = (ROOT / "docs/DISCOVERY_PROVENANCE.md").read_text()
        readme = (ROOT / "README.md").read_text()
        guide = (ROOT / "SUBMISSION_PACKAGE_README.md").read_text()
        report = (ROOT / "REPORT.md").read_text()
        for token in ("3258a762", "705 API calls", "49 cache hits",
                      "46 excluded candidates", "first observed transition",
                      "not independently notarized", "are not bundled",
                      ORIGINAL_ID_SHA256, MANIFEST_SHA256):
            self.assertIn(token, provenance)
        for text in (readme, guide, report):
            self.assertIn("docs/DISCOVERY_PROVENANCE.md", text)
        self.assertIn("Raw historical discovery pages were not archived", report)


if __name__ == "__main__":
    unittest.main()
