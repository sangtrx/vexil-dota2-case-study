"""Offline research-contract tests. No OpenDota calls or Kaggle credentials."""
from __future__ import annotations
import ast
import copy
import json
import math
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
NB = json.loads((ROOT / "live_dota2_win_probability.ipynb").read_text(encoding="utf-8"))
SEED = 20261113


def source_at(cell_number: int) -> str:
    return "".join(NB["cells"][cell_number]["source"])


def load_definitions() -> dict:
    """Load only the notebook's definitions, never its API/data/model execution cells."""
    namespace = dict(
        np=np, pd=pd, requests=requests, re=re, math=math, json=json,
        Counter=Counter, Path=Path, tempfile=tempfile, SEED=SEED,
        hashlib=__import__("hashlib"), gzip=__import__("gzip"),
        time=__import__("time"), copy=copy,
        Pipeline=Pipeline, SimpleImputer=SimpleImputer,
        StandardScaler=StandardScaler, LogisticRegression=LogisticRegression,
    )
    for cell_no in (4, 7, 8, 10, 12, 14, 16):
        tree = ast.parse(source_at(cell_no), filename=f"cell_{cell_no}")
        nodes = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                nodes.append(node)
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if any(n in {"BASE_URL", "N_MATCHES", "MIN_PATCH_COUNT",
                             "MAX_PRO_PAGES", "FROZEN_MATCH_IDS",
                             "FEATURE_COLUMNS", "SETS"} for n in names):
                    nodes.append(node)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), f"cell_{cell_no}", "exec"), namespace)
    return namespace


N = load_definitions()


def match_fixture() -> dict:
    gold = [float(t * 120) for t in range(36)]
    xp = [float(t * 90) for t in range(36)]
    players = []
    for slot in list(range(5)) + list(range(128, 133)):
        players.append({
            "player_slot": slot,
            "gold_t": [1000 + 10 * t for t in range(36)],
            "xp_t": [700 + 20 * t for t in range(36)],
            "lh_t": [t for t in range(36)],
            "kills_log": ([{"time": -4, "key": "enemy"},
                           {"time": 600, "key": "enemy"},
                           {"time": 601, "key": "enemy"}] if slot == 0 else []),
            "kills": 999999, "net_worth": 1_000_000,
        })
    return dict(match_id=1, duration=2150, radiant_win=True,
                radiant_gold_adv=gold, radiant_xp_adv=xp,
                players=players,
                objectives=[
                    {"type": "building_kill", "key": "npc_dota_badguys_tower1_mid", "time": -5},
                    {"type": "building_kill", "key": "npc_dota_goodguys_tower1_top", "time": 600},
                    {"type": "building_kill", "key": "npc_dota_badguys_tower2_mid", "time": 601},
                    {"type": "CHAT_MESSAGE_ROSHAN_KILL", "team": 2, "time": 600},
                    {"type": "CHAT_MESSAGE_ROSHAN_KILL", "team": 3, "time": 601},
                    {"type": "building_kill", "key": "npc_dota_badguys_melee_rax_mid", "time": 602},
                    {"type": "building_kill", "key": "npc_dota_badguys_tower1_invalid", "time": None},
                ])


class NotebookContractsTest(unittest.TestCase):
    def test_notebook_structure_matches_brief(self):
        headings = "\n".join(source_at(i) for i,c in enumerate(NB["cells"])
                            if c["cell_type"] == "markdown")
        positions = [headings.index(h) for h in
                     ("## 1 · Setup", "## 2 · Data", "## 3 · Features",
                      "## 4 · Split", "## 5 · Models", "## 6 · Evaluation")]
        self.assertEqual(sorted(positions), positions)
        self.assertEqual(NB["nbformat"], 4)
        for i, cell in enumerate(NB["cells"]):
            if cell["cell_type"] == "code": compile(source_at(i), f"cell_{i}", "exec")

    def test_pins_colab_and_local_match(self):
        tree = ast.parse(source_at(2))
        pins = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id=="PINS" for t in node.targets):
                pins = set(ast.literal_eval(node.value))
        self.assertIsNotNone(pins)
        required = set((ROOT/"requirements.txt").read_text().split())
        self.assertTrue(pins.issubset(required))

    def test_patch_coverage_requires_two_supported_patches(self):
        f=N["patch_coverage_ok"]
        self.assertFalse(f([{"patch":60}]*499 + [{"patch":59}]))
        self.assertTrue(f([{"patch":60}]*480 + [{"patch":59}]*20))
        self.assertTrue(f([{"patch":60}]*479 + [{"patch":59}]*20 + [{"patch":58}]))

    def test_forbidden_endpoint_is_rejected_pre_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            api=N["OpenDota"](cache_dir=tmp)
            with self.assertRaises(AssertionError):
                api.get("/players/123")
            with self.assertRaises(AssertionError):
                api.get("/proMatches", {"other_endpoint_arg":1})

    def test_pre_horn_included_and_exact_cutoff(self):
        m=match_fixture()
        at10=N["snapshot_features"](m,10)
        at11=N["snapshot_features"](m,11)
        self.assertEqual(at10["tower_delta"],0)  # +1 pre-horn -1 at 600
        self.assertEqual(at10["roshan_delta"],1)  # 600 included, 601 excluded
        self.assertEqual(at10["kill_delta"],2)    # -4 and 600 included
        self.assertEqual(at11["tower_delta"],1)  # 601 enters at minute 11
        self.assertEqual(at11["roshan_delta"],0)
        self.assertEqual(at11["kill_delta"],3)

    def test_future_payload_and_label_poisoning_cannot_change_past(self):
        m=match_fixture()
        for t in (0, 1, 9, 10, 20, 30):
            original=N["snapshot_features"](m,t)
            truncated=N["prefix_truncated"](m,t)
            N["assert_same_features"](original,N["snapshot_features"](truncated,t))
            # Perturb selected downstream values even when the payload is not truncated.
            altered=copy.deepcopy(m)
            for field in ("radiant_gold_adv","radiant_xp_adv"):
                altered[field][t+1:] = [999999999]*(len(altered[field])-t-1)
            altered["radiant_win"]=not m["radiant_win"]
            altered["duration"]=111111
            for player in altered["players"]:
                player["net_worth"]=9000000
            N["assert_same_features"](original,N["snapshot_features"](altered,t))

    def test_missing_xp_carries_nan_but_never_future(self):
        m=match_fixture()
        m["radiant_xp_adv"]=None
        x=N["snapshot_features"](m,10)
        self.assertTrue(math.isnan(x["xp_k"]))
        self.assertTrue(math.isnan(x["xp_velocity5_k"]))
        self.assertEqual(x["gold_k"],1.2)

    def test_series_are_never_split(self):
        rows=[]
        for i in range(120):
            rows.append({"match_id":10000+i, "start_time":100000+i*600,
                         "series_id":700+i//3, "patch":60, "duration":2000,
                         "radiant_win":i%2})
        info=N["series_safe_split"](pd.DataFrame(rows))
        self.assertEqual(len(info),120)
        self.assertEqual(info.partition.value_counts().sum(),120)
        self.assertTrue((info.groupby("series_id").partition.nunique()==1).all())
        self.assertEqual(set(info.partition),{"train","validation","test"})

    def test_gold_baseline_has_one_predictor(self):
        cols=N["SETS"]["M0_gold_only"]
        self.assertEqual(cols,["gold_k"])
        frame=pd.DataFrame({"gold_k":np.linspace(-5,5,70),
                            "minute10":np.linspace(0,4,70),
                            "radiant_win":([0,1]*35)})
        model=N["fit_model"](frame,cols)
        self.assertEqual(model["logistic"].coef_.shape,(1,1))
        self.assertTrue(np.isfinite(model.predict_proba(frame[cols])).all())

    def test_paired_bootstrap_and_metric_identity(self):
        records=[]
        for match_id in range(20):
            for minute in range(5):
                records.append({"match_id":match_id,"minute":minute,
                                "logloss_model":0.3+match_id/100.,
                                "logloss_baseline":0.4+match_id/100.,
                                "brier_model":0.1,"brier_baseline":0.12})
        frame=pd.DataFrame(records)
        res=N["match_bootstrap"](frame,"logloss",n_boot=500)
        self.assertAlmostEqual(res["difference"],-0.1,places=10)
        self.assertAlmostEqual(res["difference_lo"],-0.1,places=10)
        self.assertAlmostEqual(res["difference_hi"],-0.1,places=10)
        self.assertEqual(res["matches"],20)
        self.assertEqual(res["rows"],100)


    def test_equal_match_weight_loss_has_aligned_metric_names(self):
        frame = pd.DataFrame({"match_id": [1,1,2,2],
                              "logloss_model": [0.1,0.3,0.3,0.5],
                              "brier_model": [0.05,0.1,0.1,0.15],
                              "logloss_baseline": [0.2,0.4,0.4,0.6],
                              "brier_baseline": [0.06,0.11,0.12,0.16]})
        model = N["equal_match_weight_loss"](frame,"model")
        baseline = N["equal_match_weight_loss"](frame,"baseline")
        self.assertEqual(set(model), {"log_loss", "brier"})
        self.assertEqual(set(baseline), {"log_loss", "brier"})
        self.assertAlmostEqual(model["log_loss"], 0.3)
        self.assertAlmostEqual(baseline["log_loss"], 0.4)

    def test_cache_reuses_payload_without_second_http_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = N["OpenDota"](cache_dir=tmp, interval=0)
            calls = []
            class Response:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return [{"match_id": 123}]
            def fake_get(url, params, timeout):
                calls.append((url,params))
                return Response()
            api.session.get = fake_get
            self.assertEqual(api.get("/proMatches"), [{"match_id":123}])
            self.assertEqual(api.get("/proMatches"), [{"match_id":123}])
            self.assertEqual(len(calls),1)
            self.assertEqual(api.cache_hits,1)

    def test_unparsed_matches_are_excluded_before_selection(self):
        old_n, old_min = N["N_MATCHES"], N["MIN_PATCH_COUNT"]
        N["N_MATCHES"], N["MIN_PATCH_COUNT"] = 4, 1
        class FakeApi:
            def get(self, path, params=None):
                if path == "/proMatches": return [{"match_id":i} for i in (7,6,5,4,3)]
                i = int(path.rsplit("/",1)[-1])
                if i == 7: return {"match_id":7, "duration":1800, "radiant_win":True, "radiant_gold_adv":None}
                return {"match_id":i,"duration":1800,"radiant_win":bool(i%2),
                        "radiant_gold_adv":[0,100],"patch":60 if i in (6,5) else 59}
        try:
            selected, exclusions = N["collect_matches"](FakeApi())
            self.assertEqual([m["match_id"] for m in selected], [6,5,4,3])
            self.assertEqual(exclusions, [(7,"unparsed_or_too_short")])
        finally:
            N["N_MATCHES"], N["MIN_PATCH_COUNT"] = old_n, old_min

    def test_short_gold_array_uses_only_last_available_past_snapshot(self):
        m = match_fixture()
        m["radiant_gold_adv"] = m["radiant_gold_adv"][:11]
        at20 = N["snapshot_features"](m,20)
        self.assertEqual(at20["gold_k"],1.2)
        N["assert_same_features"](at20,N["snapshot_features"](N["prefix_truncated"](m,20),20))


if __name__ == "__main__":
    unittest.main()
