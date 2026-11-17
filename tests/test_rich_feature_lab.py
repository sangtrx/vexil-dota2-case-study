"""Source timing and mirrored 81-feature research QA, independent of raw cache."""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
import rich_feature_engineering as eng
import rich_feature_models as mdl


def synthetic_match():
    players=[]
    for slot in [0,1,2,3,4,128,129,130,131,132]:
        pos=slot<5
        gold=[0,100+slot%6,220+slot%6,430+slot%6]
        xp=[0,90+slot%6,140+slot%6,380+slot%6]
        lh=[0,1+slot%5,3+slot%5,6+slot%5]
        dn=[0,0,1,2]
        players.append({
            "player_slot":slot,"gold_t":gold,"xp_t":xp,
            "lh_t":lh,"dn_t":dn,
            "kills_log":[{"time":75,"key":"npc_dota_hero_a"}] if slot==0 else [],
            "radiant_win":pos,"gold_per_min":5000,  # poisoned final stat
        })
    return {
        "match_id":999,"radiant_win":True,"duration":12000,
        "radiant_gold_adv":[-100,220,500,18000],
        "radiant_xp_adv":[-50,190,600,25000],
        "players":players,
        "objectives":[
            {"time":60,"type":"building_kill","key":"npc_dota_badguys_tower1_top"},
            {"time":85,"type":"CHAT_MESSAGE_ROSHAN_KILL","player_slot":0},
            {"time":155,"type":"CHAT_MESSAGE_AEGIS","player_slot":128},
            {"time":230,"type":"building_kill","key":"npc_dota_goodguys_tower3_mid"},
        ],
    }


class RichFeatureQA(unittest.TestCase):
    def test_exact_registry_counts_and_projected_model_inputs(self):
        self.assertEqual(len(eng.RICH),81)
        self.assertEqual({k:len(v) for k,v in eng.FAMILIES.items()},
                         {"gold":19,"xp":13,"players":19,"objectives":17,"interactions":13})
        self.assertEqual(len(mdl.MODELS["Q2_sparse"]),84)
        self.assertEqual(len(mdl.MODELS["Q3_tree"]),84)
        self.assertEqual(set(mdl.CANDIDATES),{"Q2_sparse","Q3_tree"})

    def test_no_terminal_fields_or_future_times_in_feature_view(self):
        raw=synthetic_match()
        t=1
        before=eng.project_asof(raw,t)
        self.assertNotIn("radiant_win",before)
        self.assertNotIn("duration",before)
        self.assertNotIn("gold_per_min",before["players"][0])
        self.assertEqual(len(before["radiant_gold_adv"]),2)
        self.assertTrue(all(e["time"]<=60 for e in before["objectives"]))
        a=eng.features_from_asof(before)
        altered=json.loads(json.dumps(raw))
        altered["radiant_win"]=False
        altered["duration"]=-5
        altered["radiant_gold_adv"][2:]=[-9999999,+9999999]
        altered["radiant_xp_adv"][2:]=[9999999,-9999999]
        altered["objectives"].append({"time":180,"type":"building_kill",
                         "key":"npc_dota_badguys_tower2_mid"})
        for p in altered["players"]:
            p["gold_per_min"]=-99999999
            p["gold_t"][2:]=[-1000,1000000]
            p["xp_t"][2:]=[99999,1000000]
            p["kills_log"].append({"time":230,"key":"future"})
        b=eng.features_from_asof(eng.project_asof(altered,t))
        self.assertEqual(a,b)
        self.assertEqual(set(a),set(eng.RICH))

    def test_symmetry_and_event_side(self):
        raw=synthetic_match()
        for minute in [0,1,2,3]:
            v=eng.project_asof(raw,minute)
            a=eng.features_from_asof(v)
            flipped=eng.features_from_asof(eng.mirror_view(v))
            for key in eng.RICH:
                self.assertAlmostEqual(a[key],-flipped[key],delta=1e-8,msg=key)
        a=eng.features_from_asof(eng.project_asof(raw,1))
        raw["objectives"][0]["time"]=180
        b=eng.features_from_asof(eng.project_asof(raw,1))
        self.assertNotEqual(a["o_tower_delta"],b["o_tower_delta"])

    def test_bad_inputs_fail_closed(self):
        raw=synthetic_match()
        for minute in (-1,4):
            with self.assertRaises(ValueError):
                eng.project_asof(raw,minute)
        raw["players"][0]["gold_t"]=[]
        with self.assertRaises(ValueError):
            eng.project_asof(raw,1)

    def test_frozen_train_artifact_and_scientific_receipt_only(self):
        self.assertEqual(hashlib.sha256(eng.SOURCE.read_bytes()).hexdigest(),eng.TRAIN_SHA)
        provenance=json.loads(eng.PROVENANCE.read_text())
        self.assertEqual(provenance["raw_games_read"],291)
        self.assertEqual(provenance["minute_prefixes_checked"],10675)
        self.assertEqual(provenance["original_gold_lead_parity"],10675)
        self.assertEqual(
            hashlib.sha256(eng.FEATURES.read_bytes()).hexdigest(),
            provenance["frozen_feature_csv_sha256"])
        df=pd.read_csv(eng.FEATURES,nrows=3)
        self.assertTrue(set(eng.RICH).issubset(df.columns))
        self.assertFalse(df[eng.RICH].isna().any().any())
        res=json.loads(mdl.RECEIPT.read_text())
        self.assertEqual(res["new_feature_count"],81)
        self.assertEqual(res["wide_input_count"],84)
        self.assertEqual(res["games_evaluated"],137)
        self.assertEqual(res["rows_evaluated"],5081)
        self.assertEqual(res["group_count"],70)
        self.assertFalse(res["original_VAL_or_TEST_labels_loaded"])
        self.assertFalse(res["original_submission_changed"])
        self.assertTrue(set(res["future_candidate_gate"])=={"Q2_sparse","Q3_tree"})

    def test_duplicate_and_unobservable_features_are_disclosed(self):
        frame=pd.read_csv(eng.FEATURES)
        varying=[c for c in eng.RICH if frame[c].nunique(dropna=False)>1]
        constant=set(eng.RICH)-set(varying)
        self.assertEqual(constant,{"o_roshan_delta","o_roshan10_delta"})
        self.assertTrue((frame["o_roshan_delta"]==0).all())
        self.assertTrue((frame["o_roshan10_delta"]==0).all())
        self.assertTrue(np.array_equal(
            frame["gold_xp_gap"].to_numpy(),
            frame["x_economy_gap"].to_numpy()))
        distinct={frame[c].round(10).to_numpy().tobytes() for c in varying}
        self.assertEqual(len(varying),79)
        self.assertEqual(len(distinct),78)
        quality=(ROOT/"research/RICH_FEATURE_DIVERSITY_AUDIT.md").read_text()
        self.assertIn("486/486",quality)
        self.assertIn("78 distinct, varying",quality)

    def test_bounded_wide_models_not_promoted(self):
        r=json.loads(mdl.RECEIPT.read_text())
        self.assertEqual(
            r["future_candidate_gate"],
            {"Q2_sparse":False,"Q3_tree":False})
        for name in ("Q2_sparse","Q3_tree"):
            for rival in ("M1_interaction","Q1_path"):
                self.assertGreater(r["comparisons"][name][rival]["delta_logloss"],0)
                self.assertEqual(
                    r["comparisons"][name][rival]["better_forward_folds"],1)


if __name__=="__main__":
    unittest.main()
