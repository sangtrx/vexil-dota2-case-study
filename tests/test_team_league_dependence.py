"""Offline tests for the post-TEST non-selecting team/league dependence audit."""
from __future__ import annotations

import ast
from collections import Counter
import copy
import json
import math
from pathlib import Path
import unittest

from research import team_league_dependency_audit as audit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_METADATA_SHA = "74fdc9479bd8dc4f70eac72f776d24a7708e7d7119f1ec6b18af43c954c701fe"
EXPECTED_NOTEBOOK_SHA = "e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f"


class TeamLeagueDependenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = audit.load_metadata()
        cls.rows = audit.load_frozen_predictions(cls.metadata)
        cls.receipt = audit.audit()

    def test_frozen_source_hashes_and_author_metadata_receipt(self):
        self.assertEqual(audit.digest(audit.METADATA), EXPECTED_METADATA_SHA)
        self.assertEqual(audit.digest(audit.FORECASTS), audit.FORECAST_SHA)
        self.assertEqual(
            audit.digest(ROOT / "live_dota2_win_probability.ipynb"), EXPECTED_NOTEBOOK_SHA)
        self.assertEqual(
            self.receipt["source"]["group_metadata_sha256"], EXPECTED_METADATA_SHA)
        self.assertTrue(self.receipt["not_new_blind_test"])
        self.assertTrue(self.receipt["does_not_fit_or_select_models"])

    def test_all_500_join_and_maturity_boundary_unchanged(self):
        self.assertEqual(len(self.metadata), 500)
        self.assertEqual(Counter(v["partition"] for v in self.metadata.values()),
                         {"train": 291, "validation": 103, "test": 106})
        # Missing original team identifiers stay missing, never imputed.
        unknown_team_games = [m for m in self.metadata.values()
                              if not m["radiant_team_id"] or not m["dire_team_id"]]
        self.assertEqual(len(unknown_team_games), 21)
        self.assertTrue(all(m["partition"] == "train" for m in unknown_team_games))
        self.assertEqual(self.metadata[8741939284]["series_id"], "0")

    def test_test_rows_and_independent_proper_loss_recomputation(self):
        self.assertEqual(len(self.rows), 3836)
        self.assertEqual(len({r["match_id"] for r in self.rows}), 106)
        self.assertAlmostEqual(audit.mean_delta(self.rows, "delta_ll"),
                               -0.012429726921359421, places=12)
        self.assertAlmostEqual(audit.mean_delta(self.rows, "delta_brier"),
                               -0.00355934396794912, places=12)

    def test_series_league_team_counts_and_overlap(self):
        c = self.receipt["cohort"]
        self.assertEqual(c["test_positive_series_or_singletons"], 54)
        self.assertEqual(c["test_distinct_leagues"], 9)
        self.assertEqual(c["test_distinct_known_team_ids"], 65)
        self.assertEqual(c["known_test_teams_also_in_train"], 52)
        self.assertEqual(c["known_test_teams_also_in_validation"], 46)
        self.assertEqual(c["test_top_two_league_game_count"], 49)
        self.assertEqual(sum(c["test_games_by_league_id"].values()), 106)
        self.assertAlmostEqual(c["known_test_team_id_overlap_train_fraction"], .8)

    def test_posthoc_group_bootstrap_not_used_to_claim_superiority(self):
        r = self.receipt["post_hoc_resampling"]
        for name, clusters in (("match_logloss", 106), ("match_brier", 106),
                               ("series_logloss", 54), ("series_brier", 54)):
            self.assertEqual(r[name]["clusters"], clusters)
            self.assertEqual(r[name]["draws"], 30000)
            self.assertEqual(r[name]["seed"], 20261116)
        self.assertTrue(r["match_logloss"]["both_sides_of_zero"])
        self.assertTrue(r["match_brier"]["both_sides_of_zero"])
        self.assertTrue(r["series_logloss"]["both_sides_of_zero"])
        self.assertFalse(r["series_brier"]["both_sides_of_zero"])
        self.assertAlmostEqual(r["series_logloss"]["interval_95"][1],
                               0.00008547043640661712, places=12)
        self.assertTrue(self.receipt["do_not_use_to_promote_model"])

    def test_leave_league_out_is_influence_not_model_selection(self):
        s = self.receipt["post_hoc_leave_one_league_out"]
        self.assertEqual(len(s), 9)
        self.assertTrue(all(x["delta_logloss"] < 0 for x in s))
        worse = [x for x in s if x["within_league_delta_logloss"] > 0]
        self.assertEqual([x["excluded_league_id"] for x in worse], ["17909"])
        self.assertEqual(worse[0]["excluded_games"], 8)
        self.assertAlmostEqual(worse[0]["within_league_delta_logloss"],
                               0.02852172617424942, places=12)

    def test_corrupt_group_mapping_is_rejected(self):
        changed = copy.deepcopy(self.metadata)
        first_test = next(k for k, v in changed.items() if v["partition"] == "test")
        changed[first_test]["partition"] = "train"
        with self.assertRaisesRegex(ValueError, "Unexpected match"):
            audit.load_frozen_predictions(changed)

    def test_model_coefficients_cannot_use_group_identity_as_predictors(self):
        notebook = json.loads((ROOT / "live_dota2_win_probability.ipynb").read_text())
        source = "".join(notebook["cells"][12]["source"])
        assignments = ast.parse(source)
        sets = next(ast.literal_eval(n.value)
                    for n in assignments.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "SETS" for t in n.targets))
        self.assertEqual(sets["M0_gold_only"], ["gold_k"])
        self.assertEqual(sets["M1_time_value"], ["gold_k", "minute10", "gold_x_time"])
        self.assertTrue(all("team" not in f and "league" not in f
                            for predictors in sets.values() for f in predictors))
        # Only selected differences are evaluated; audit contains no fitting step.
        self.assertNotIn("sklearn", audit.__dict__)

    def test_receipt_byte_replay_and_honest_caveats(self):
        existing = audit.RECEIPT.read_bytes()
        recomputed = (json.dumps(self.receipt, indent=2, sort_keys=True,
                                 ensure_ascii=False) + "\n").encode("utf-8")
        self.assertEqual(existing, recomputed)
        self.assertFalse(self.receipt["raw_match_json_included"])
        self.assertIn("Only nine selected", " ".join(self.receipt["limitations"]))
        readout = (ROOT / "docs/TEAM_LEAGUE_DEPENDENCE.md").read_text()
        self.assertIn("POST-HOC", readout)
        self.assertIn("cannot create a second blind TEST", readout)
        self.assertIn("not proof of test leakage", readout)
        self.assertIn("MacKinnon", readout)


if __name__ == "__main__":
    unittest.main()
