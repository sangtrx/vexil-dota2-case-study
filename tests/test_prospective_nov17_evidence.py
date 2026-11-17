"""No-refitting evidence checks for the prospectively locked Nov-17 follow-up.

These are regression/consistency tests, NOT statistical independence proofs.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/PROSPECTIVE_NOV17_HOLDOUT_EVIDENCE.json"
COLLECTION = ROOT / "docs/PROSPECTIVE_NOV17_COLLECTION_RECEIPT.json"
LISTING = ROOT / "docs/PROSPECTIVE_NOV17_AMENDED_LISTING.json"
FROZEN_TEST = ROOT / "artifacts/heldout_predictions.csv"
FROZEN_NOTEBOOK = ROOT / "live_dota2_win_probability.ipynb"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


class ExternalHoldoutEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = json.loads(EVIDENCE.read_text())
        cls.c = json.loads(COLLECTION.read_text())
        cls.l = json.loads(LISTING.read_text())

    def test_sample_immutable_and_underpowered(self):
        self.assertTrue(self.c["complete"])
        self.assertEqual(self.c["requested_count"], 22)
        self.assertEqual(self.c["accepted_count"], 22)
        self.assertEqual(self.c["exclusions"], {})
        self.assertEqual(self.e["games"], 22)
        self.assertEqual(self.e["minute_rows"], 952)
        self.assertEqual(self.e["series_or_singleton_clusters"], 9)
        self.assertEqual(self.e["patch_counts"], {"60": 22})
        self.assertEqual(sorted(self.e["league_counts"].values()), [7, 15])
        self.assertTrue(self.e["underpowered_or_descriptive_only"])
        self.assertTrue(self.e["no_model_promotion_authorized"])
        self.assertTrue(self.e["no_forward_training"])
        self.assertTrue(self.e["no_recalibration"])
        self.assertTrue(self.e["received_at_unverified"])
        self.assertEqual(self.e["original_500_and_previous_100_overlap"], 0)
        self.assertEqual(self.e["source_model_coeff_fingerprints"],
                         self.l["model_fingerprints"])
        self.assertEqual(self.e["listing_sha256"], sha(LISTING.read_bytes()))
        self.assertEqual(self.e["collection_receipt_sha256"],
                         sha(COLLECTION.read_bytes()))
        self.assertEqual(self.c["frozen_listing_sha256"],
                         self.e["listing_sha256"])

    def test_exact_raw_game_payload_hashes(self):
        accepted = self.c["accepted"]
        self.assertEqual(len(accepted), 22)
        self.assertEqual(len({r["match_id"] for r in accepted}),22)
        for row in accepted:
            mid = row["match_id"]
            f = ROOT / "research/prospective_nov17_accepted_raw" / f"{mid}.json.gz"
            zipped = f.read_bytes()
            self.assertEqual(sha(zipped), row["raw_gzip_sha256"])
            raw = gzip.decompress(zipped)
            self.assertEqual(sha(raw), row["raw_json_sha256"])
            game = json.loads(raw)
            self.assertEqual(game["match_id"],mid)
            self.assertTrue(isinstance(game.get("radiant_win"),bool))

    def test_independent_metric_oracle(self):
        """Plain math, not repo original/prospective scoring functions."""
        sums = [0., 0., 0., 0.]
        keys = set()
        mids = set()
        with (ROOT/"artifacts/prospective_nov17_predictions.csv").open() as f:
            for row in csv.DictReader(f):
                mid=int(row["match_id"]);minute=int(row["minute"])
                key=(mid,minute)
                self.assertNotIn(key, keys)
                keys.add(key)
                mids.add(mid)
                y=int(row["radiant_win"])
                a=float(row["p_M0"]);b=float(row["p_M1"])
                self.assertIn(y,(0,1))
                self.assertTrue(0<a<1 and 0<b<1)
                loss=lambda p: -y*math.log(p)-(1-y)*math.log1p(-p)
                for i,v in enumerate((loss(a), loss(b), (a-y)**2, (b-y)**2)):
                    sums[i]+=v
        self.assertEqual(len(keys),952)
        self.assertEqual(len(mids),22)
        for value,expected in zip([x/len(keys) for x in sums],
           (self.e["M0"]["logloss"],self.e["M1"]["logloss"],
            self.e["M0"]["brier"],self.e["M1"]["brier"])):
            self.assertAlmostEqual(value,expected,places=12)
        self.assertLess(self.e["M1_minus_M0"]["logloss"],0)
        self.assertLess(self.e["M1_minus_M0"]["brier"],0)
        self.assertGreater(self.e["M1"]["ece10"],self.e["M0"]["ece10"])
        self.assertLess(self.e["M1_minus_M0"]["logloss_ci_95_match"][0],0)
        self.assertGreater(self.e["M1_minus_M0"]["logloss_ci_95_match"][1],0)

    def test_unmodified_original_reviewer_science(self):
        self.assertEqual(sha(FROZEN_NOTEBOOK.read_bytes()),
           "466dce5d64adf081fb20642df210f903794745714675e225415c0aa8770f8304")
        self.assertEqual(sha(FROZEN_TEST.read_bytes()),
           "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441")
        readout=(ROOT/"docs/PROSPECTIVE_NOV17_HOLDOUT_READOUT.md").read_text()
        self.assertIn("22 matches", readout)
        self.assertIn("9 series", readout)
        self.assertIn("underpowered", readout.lower())
        self.assertIn("do not", readout.lower())


if __name__ == "__main__":
    unittest.main()
