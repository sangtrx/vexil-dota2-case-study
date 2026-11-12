"""Strict no-network PIT and structural feature tests."""
from __future__ import annotations

import copy
import math
import unittest

from research.edge_features import (
    SPECS, STRUCTURAL_COLUMNS, _sided_player_gold, structural_snapshot
)
from tests.test_notebook_contracts import match_fixture


class StructuralFeatureContracts(unittest.TestCase):
    def setup_game(self):
        m=match_fixture()
        # Radiant advantage in earned gold, zero at t=0, rising thereafter.
        m["radiant_gold_adv"]=[float(t*150) for t in range(36)]
        for j,player in enumerate(m["players"]):
            multiplier=(j+2) if j<5 else (j-2)
            player["gold_t"]=[max(0,100*multiplier+minute*200*multiplier)
                              for minute in range(36)]
        return m

    def test_fixed_family_has_no_result_or_final_features(self):
        self.assertEqual(len(SPECS),5)
        forbidden={"radiant_win","duration","net_worth","total_gold",
                   "gold_per_min","total_xp","kills","purchase"}
        for name,cols in SPECS.items():
            self.assertEqual(len(cols),len(set(cols)))
            self.assertTrue(forbidden.isdisjoint(cols),name)
            self.assertEqual(cols[:3],("gold_k","minute10","gold_x_time"))

    def test_sums_and_shares_match_mechanics(self):
        m=self.setup_game()
        r,d=_sided_player_gold(m,10)
        x=structural_snapshot(m,10)
        self.assertAlmostEqual(x["econ_share_gap"],
                               100*(sum(r)-sum(d))/(sum(r)+sum(d)+1000))
        self.assertAlmostEqual(x["top2_share_gap"],
            sum(sorted(r,reverse=True)[:2])/sum(r)
            -sum(sorted(d,reverse=True)[:2])/sum(d))
        self.assertAlmostEqual(x["core_gold_gap_share"],
            (sum(sorted(r,reverse=True)[:2])-sum(sorted(d,reverse=True)[:2]))/
            (sum(r)+sum(d)+1000))
        self.assertAlmostEqual(x["relative_shock5"],750/(1500+3000))
        self.assertAlmostEqual(x["signed_lead_persistence10"],1.)

    def test_truncation_and_poison_future_and_final_fields(self):
        m=self.setup_game()
        before=structural_snapshot(m,10)
        altered=copy.deepcopy(m)
        altered["radiant_gold_adv"]=altered["radiant_gold_adv"][:11]+[-999999]*25
        for player in altered["players"]:
            player["gold_t"]=player["gold_t"][:11]+[999999999]*25
            player["net_worth"]=10**9
            player["total_gold"]=10**10
            player["hero_damage"]=10**10
        altered["radiant_win"]=not m["radiant_win"]
        altered["duration"]=-1234
        after=structural_snapshot(altered,10)
        self.assertEqual(before,after)

    def test_side_swap_antisymmetry(self):
        m=self.setup_game()
        right=copy.deepcopy(m)
        for player in right["players"]:
            slot=player["player_slot"]
            player["player_slot"]=slot+128 if slot<128 else slot-128
        right["radiant_gold_adv"]=[-x for x in m["radiant_gold_adv"]]
        x=structural_snapshot(m,10)
        y=structural_snapshot(right,10)
        for name in STRUCTURAL_COLUMNS:
            self.assertAlmostEqual(x[name],-y[name],msg=name)

    def test_no_future_fill_for_missing_player_gold(self):
        m=self.setup_game()
        m["players"][0]["gold_t"]=m["players"][0]["gold_t"][:7]
        x=structural_snapshot(m,10)
        self.assertTrue(math.isnan(x["econ_share_gap"]))
        self.assertTrue(math.isnan(x["top2_share_gap"]))
        self.assertTrue(math.isnan(x["core_gold_gap_share"]))
        self.assertTrue(math.isfinite(x["relative_shock5"]))

    def test_zero_economy_and_zero_lead(self):
        m=self.setup_game()
        for player in m["players"]:player["gold_t"]=[0]*36
        m["radiant_gold_adv"]=[0]*36
        x=structural_snapshot(m,0)
        self.assertEqual(x["econ_share_gap"],0.)
        self.assertTrue(math.isnan(x["top2_share_gap"]))
        self.assertTrue(math.isnan(x["core_gold_gap_share"]))
        self.assertEqual(x["relative_shock5"],0.)
        self.assertEqual(x["signed_lead_persistence10"],0.)

    def test_nonpositive_or_duplicate_slot_is_missing(self):
        m=self.setup_game()
        m["players"][1]["player_slot"]=m["players"][0]["player_slot"]
        x=structural_snapshot(m,10)
        self.assertTrue(math.isnan(x["econ_share_gap"]))

if __name__=="__main__":
    unittest.main()
