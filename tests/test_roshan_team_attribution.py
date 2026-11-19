"""Roshan team attribution, causal minute boundary, and side symmetry.

The locked historical rich-feature CSV and model scores must remain untouched:
this checks the corrected *post-result* feature generator only.
"""
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "rich_feature_engineering",
    ROOT / "research" / "rich_feature_engineering.py",
)
rich = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rich)


def sample(events):
    return {
        "radiant_gold_adv": [0] * 26,
        "radiant_xp_adv": [0] * 26,
        "objectives": events,
        "players": [
            {
                "player_slot": slot,
                "gold_t": [10] * 26,
                "xp_t": [20] * 26,
                "lh_t": [0] * 26,
                "dn_t": [0] * 26,
                "kills_log": [],
            }
            for slot in list(range(5)) + list(range(128, 133))
        ],
    }


class RoshanTeamRegression(unittest.TestCase):
    def test_roshan_uses_team_code_not_player_slot(self):
        raw = sample([
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 125, "team": 2},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 490, "team": 3},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 600, "team": 2},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 780, "team": 3},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 180, "team": 1},
            {"type": "CHAT_MESSAGE_AEGIS", "time": 200, "player_slot": 130, "slot": 7},
        ])
        view = rich.project_asof(raw, 10)
        result = rich.features_from_asof(view)
        self.assertEqual(result["o_roshan_delta"], 1.)
        self.assertEqual(result["o_roshan10_delta"], 1.)
        self.assertEqual(result["o_aegis5_delta"], 0.)
        self.assertEqual(result["o_objective_tempo"], 1.5)

    def test_ros_positive_side_and_exclusion_future(self):
        raw = sample([
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 540, "team": 2},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 720, "team": 3},
        ])
        s9 = rich.features_from_asof(rich.project_asof(raw, 9))
        s10 = rich.features_from_asof(rich.project_asof(raw, 10))
        self.assertEqual(s9["o_roshan_delta"], 1.)
        self.assertEqual(s10["o_roshan_delta"], 1.)
        self.assertEqual(s9["o_roshan10_delta"], 1.)
        self.assertEqual(s10["o_roshan10_delta"], 1.)
        self.assertEqual(rich.project_asof(raw, 9), rich.project_asof(
            {**raw, "objectives": raw["objectives"] + [
                {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 5800, "team": 3}
            ]}, 9
        ))

    def test_roshan_mirror_inverts_team_and_all_81_signs(self):
        raw = sample([
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 305, "team": 2},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 350, "team": 2},
            {"type": "CHAT_MESSAGE_ROSHAN_KILL", "time": 395, "team": 3},
        ])
        view = rich.project_asof(raw, 10)
        reflected = rich.mirror_view(view)
        self.assertEqual([e["team"] for e in reflected["objectives"]],
                         [3, 3, 2])
        a = rich.features_from_asof(view)
        b = rich.features_from_asof(reflected)
        self.assertEqual(a["o_roshan_delta"], 1.)
        self.assertEqual(b["o_roshan_delta"], -1.)
        for k in rich.RICH:
            self.assertAlmostEqual(a[k], -b[k], places=8, msg=k)


if __name__ == "__main__":
    unittest.main()
