"""Offline integrity checks for post-result Roshan-team parser correction."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research"
OLD_TRAIN = R / "frozen_original_train_features.csv.gz"
CORRECTED = R / "RICH_FEATURE_TRAIN_ONLY_ROSHAN_CORRECTED.csv.gz"
PROVENANCE = R / "RICH_FEATURE_RAW_PROVENANCE_ROSHAN_CORRECTED.json"
QRECEIPT = R / "RICH_FEATURE_MODEL_ROSHAN_CORRECTED_RECEIPT.json"
BRECEIPT = R / "ROSHAN_CORRECTED_BOOSTED_RECEIPT.json"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class CorrectedRoshanReceiptTest(unittest.TestCase):
    def test_corrected_features_keep_original_train_and_restore_side(self):
        p = json.loads(PROVENANCE.read_text())
        self.assertEqual(digest(CORRECTED), p["frozen_feature_csv_sha256"])
        self.assertEqual(digest(OLD_TRAIN), p["source_train_sha256"])
        self.assertEqual((p["raw_games_read"], p["minute_prefixes_checked"]), (291, 10675))
        self.assertFalse(p["inputs_from_live_received_at_confirmed"])
        self.assertTrue(p["no_validation_test_match_payloads_read"])
        a = pd.read_csv(OLD_TRAIN)
        b = pd.read_csv(CORRECTED)
        self.assertEqual(len(a), len(b))
        self.assertEqual(b.match_id.nunique(), 291)
        for col in ("match_id","minute","radiant_win","partition","series_id"):
            np.testing.assert_array_equal(a[col].to_numpy(), b[col].to_numpy())
        for col in ("gold_k","minute10","gold_x_time"):
            np.testing.assert_allclose(a[col].to_numpy(), b[col].to_numpy(), atol=1e-10, rtol=0)
        self.assertEqual(int((b.o_roshan_delta != 0).sum()), 3624)
        self.assertEqual(int((b.o_roshan10_delta != 0).sum()), 3655)
        self.assertGreater(int(b.o_roshan_delta.nunique()), 2)
        np.testing.assert_allclose(b.x_economy_gap, b.gold_xp_gap, atol=1e-12, rtol=0)

    def test_corrected_models_are_train_only_and_not_promoted(self):
        q = json.loads(QRECEIPT.read_text())
        b = json.loads(BRECEIPT.read_text())
        provenance = json.loads(PROVENANCE.read_text())
        corrected_sha = digest(CORRECTED)
        self.assertEqual(q["scope"], "POST_RESULT_TRAIN_ONLY_NOT_FRESH_TEST")
        self.assertFalse(q["original_VAL_or_TEST_labels_loaded"])
        self.assertFalse(q["original_submission_changed"])
        self.assertFalse(b["original_val_or_test_loaded"])
        self.assertFalse(b["prospective_new_cohort"])
        self.assertFalse(b["employer_promotion_authorized"])
        self.assertEqual((q["rows_evaluated"],q["games_evaluated"],q["group_count"]), (5081,137,70))
        self.assertEqual(q["engineered_train_sha256"], corrected_sha)
        self.assertEqual(b["source_rich_train_sha256"], corrected_sha)
        self.assertEqual(b["source_291_raw_payload_hash"], provenance["source_payload_bytes_sha256"])
        self.assertEqual(q["future_candidate_gate"], {"Q2_sparse":False,"Q3_tree":False})
        self.assertFalse(b["future_candidate_gate_only"]["XGB84"])
        self.assertFalse(b["future_candidate_gate_only"]["LGB84"])
        self.assertAlmostEqual(q["comparisons"]["Q2_sparse"]["M1_interaction"]["delta_logloss"], .017733283387370524)
        self.assertAlmostEqual(q["comparisons"]["Q3_tree"]["M1_interaction"]["delta_logloss"], .01012862732399102)
        self.assertAlmostEqual(b["scores"]["XGB84"]["logloss_minute"], .621254, places=6)
        self.assertAlmostEqual(b["scores"]["LGB84"]["logloss_minute"], .624856, places=6)
        self.assertEqual(digest(ROOT/"live_dota2_win_probability.ipynb"),
                         "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f")
        self.assertEqual(digest(ROOT/"artifacts/heldout_predictions.csv"),
                         "03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441")


if __name__ == "__main__":
    unittest.main()
