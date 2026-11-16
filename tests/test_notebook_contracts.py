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
        time=__import__("time"), copy=copy, os=__import__("os"),
        Pipeline=Pipeline, SimpleImputer=SimpleImputer,
        StandardScaler=StandardScaler, LogisticRegression=LogisticRegression,
    )
    for cell_no in (4, 7, 8, 10, 12, 14, 16, 24):
        tree = ast.parse(source_at(cell_no), filename=f"cell_{cell_no}")
        nodes = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                nodes.append(node)
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if any(n in {"BASE_URL", "N_MATCHES", "COHORT_N",
                             "MAX_PRO_PAGES", "FROZEN_MATCH_IDS",
                             "FEATURE_COLUMNS", "SETS", "MAJOR_ITEM_KEYS",
                             "IMPACT_ITEM_KEYS", "ITEM_ADDED_COLUMNS"} for n in names):
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
            "times": [t * 60 for t in range(36)],
            "gold_t": [1000 + 10 * t + (24 * t if slot < 128 else 0) for t in range(36)],
            "xp_t": [700 + 20 * t + (18 * t if slot < 128 else 0) for t in range(36)],
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


    def test_saved_charts_are_embedded_and_outputs_are_reviewable(self):
        """A reproducible numeric notebook without visible plots is incomplete QA."""
        import base64
        self.assertEqual(len(NB["cells"]), 29)
        original=json.loads((ROOT/"research/frozen_original_500_notebook.ipynb").read_text())
        self.assertEqual(len(original["cells"]),26)
        self.assertEqual(
            ["".join(c["source"]) for c in NB["cells"][:26]],
            ["".join(c["source"]) for c in original["cells"]])
        for cell_idx, expected in ((15,1), (20,2), (22,1)):
            cell = NB["cells"][cell_idx]
            self.assertIsNotNone(cell.get("execution_count"))
            charts = [out["data"]["image/png"] for out in cell.get("outputs", [])
                      if out.get("output_type") == "display_data"
                      and "image/png" in out.get("data", {})]
            self.assertEqual(len(charts), expected, f"missing PNG in cell {cell_idx}")
            for chart in charts:
                raw = base64.b64decode(chart if isinstance(chart, str) else "".join(chart))
                self.assertTrue(raw.startswith(bytes([137,80,78,71,13,10,26,10])))
                self.assertGreater(len(raw), 20000)
            self.assertNotIn("plt.show()", source_at(cell_idx))
        self.assertIn("train-supported points", source_at(20))
        self.assertIn("support >= 10", source_at(20))
        last = NB["cells"][24]
        self.assertIsNotNone(last.get("execution_count"))
        self.assertIn("final_predictions.head(16)", source_at(24))
        tables = [str(out["data"].get("text/html", ""))
                  for out in last.get("outputs", [])
                  if out.get("output_type") == "display_data"]
        self.assertTrue(tables)
        self.assertLess(max(map(len, tables)), 20000)

    def test_colab_zip_contains_only_derived_outputs(self):
        import zipfile
        required = (
            "match_manifest.csv", "validation_ablations.csv", "heldout_metrics.csv",
            "terminal_sensitivity.csv", "heldout_predictions.csv",
            "minute20_comeback.csv", "exploratory_item_ablation.csv",
            "exploratory_item_folds.csv", "derived_run_receipt.json",
            "calibration.png", "time_value_scenarios.png",
            "heldout_game_trajectory.png", "minute20_comeback.png"
        )
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"vexil_takehome_outputs"
            out.mkdir()
            for name in required:
                (out/name).write_text("test payload")
            (out/"secret_raw_match_cache.json").write_text("must never export")
            destination=Path(tmp)/"colab_outputs.zip"
            N["archive_derived_outputs"](out,destination)
            with zipfile.ZipFile(destination) as archive:
                names=archive.namelist()
                self.assertEqual(names,sorted(
                    "vexil_takehome_outputs/"+name for name in required))
                self.assertFalse(any("secret" in name for name in names))
            (out/"heldout_predictions.csv").unlink()
            with self.assertRaises(FileNotFoundError):
                N["archive_derived_outputs"](out,destination)

    def test_source_lineage_separates_outcomes_from_inputs(self):
        cols = ["match_id", "minute", "gold_k", "radiant_win"]
        frame = pd.DataFrame([
            {"match_id":1,"minute":0,"gold_k":0.,"radiant_win":1},
            {"match_id":1,"minute":1,"gold_k":0.02,"radiant_win":1},
            {"match_id":2,"minute":0,"gold_k":-0.1,"radiant_win":0},
        ],columns=cols)
        h=N["canonical_hash"]
        main=["match_id","minute","gold_k"]
        target=["match_id","minute","radiant_win"]
        self.assertEqual(h(frame,main),h(frame.sample(frac=1,random_state=19),main))
        changed=frame.copy()
        changed.loc[changed.match_id==1,"radiant_win"]=0
        self.assertEqual(h(frame,main),h(changed,main))
        self.assertNotEqual(h(frame,target),h(changed,target))
        changed=frame.copy()
        changed.loc[changed.minute==1,"gold_k"]+=0.0001
        self.assertNotEqual(h(frame,main),h(changed,main))
        changed=frame.copy()
        changed["gold_k"]=changed.gold_k.astype(float)
        changed.loc[changed.minute==1,"gold_k"]=float("inf")
        with self.assertRaises(ValueError):
            h(changed,main)
        with self.assertRaises(ValueError):
            h(pd.concat([frame,frame.iloc[[0]]]),main)
        with self.assertRaises(ValueError):
            h(frame,main+["gold_k"])

    def test_team_minute_axis_fail_closed(self):
        base = match_fixture()
        self.assertTrue(N["validate_minute_alignment"](base))
        self.assertEqual(N["prefix_truncated"](base, 10)["players"][0]["times"], list(range(0, 601, 60)))
        mutations = [
            ("shifted start", lambda m: m["players"][0]["times"].__setitem__(0, 60)),
            ("irregular step", lambda m: m["players"][0]["times"].__setitem__(2, 121)),
            ("missing clock", lambda m: m["players"][0].pop("times")),
            ("short clock", lambda m: m["players"][0]["times"].pop()),
            ("short team gold", lambda m: m["radiant_gold_adv"].pop()),
            ("short team xp", lambda m: m["radiant_xp_adv"].pop()),
            ("short player xp", lambda m: m["players"][0]["xp_t"].pop()),
            ("corrupt team gold", lambda m: m["radiant_gold_adv"].__setitem__(11, m["radiant_gold_adv"][11]+1)),
            ("corrupt player xp", lambda m: m["players"][0]["xp_t"].__setitem__(9, m["players"][0]["xp_t"][9]+1)),
            ("duplicate identity", lambda m: m["players"][1].__setitem__("player_slot", 0)),
            ("boolean identity", lambda m: m["players"][1].__setitem__("player_slot", True)),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                m = copy.deepcopy(base)
                mutate(m)
                N["validate_minute_alignment"](m)
        with self.assertRaises(ValueError):
            N["make_minute_table"]([dict(base, radiant_gold_adv=[0])])

    def test_live_forecast_clock_excludes_exact_terminal_minute(self):
        # A match ending at t=35*60 cannot yield a preterminal forecast at t=35.
        # The corrected notebook must also align timestamped item features.
        case=match_fixture()
        case["duration"]=2100
        strict=N["make_minute_table"]([case])
        self.assertEqual(strict.minute.min(),0)
        self.assertEqual(strict.minute.max(),34)
        self.assertEqual(len(strict),35)
        self.assertTrue((60*strict.minute < case["duration"]).all())
        case["duration"]=2150
        partial=N["make_minute_table"]([case])
        self.assertEqual(partial.minute.max(),35)
        self.assertEqual(len(partial),36)
        self.assertTrue((60*partial.minute < case["duration"]).all())
        self.assertIn('for t in range((int(game["duration"])-1)//60 + 1):',source_at(12))

    def test_invalid_numeric_events_and_player_slots(self):
        m = match_fixture()
        m["objectives"].append({"type":"building_kill","key":"npc_dota_badguys_tower1_mid","time":float("nan")})
        m["objectives"].append({"type":"CHAT_MESSAGE_ROSHAN_KILL","team":2,"time":True})
        self.assertEqual(N["objective_snapshot"](m,600), (0,0,1))
        self.assertEqual(N["objective_snapshot"](N["prefix_truncated"](m,10),600),(0,0,1))
        m["players"][0]["kills_log"].extend([
            {"time":float("nan")}, {"time":True}, {"time":float("inf")}])
        self.assertEqual(N["kill_snapshot"](m,600),2)
        self.assertEqual(N["kill_snapshot"](N["prefix_truncated"](m,10),600),2)
        m["players"][1]["player_slot"] = 0
        self.assertTrue(math.isnan(N["kill_snapshot"](m,600)))
        m = match_fixture()
        m["radiant_gold_adv"][10] = True
        self.assertEqual(N["snapshot_features"](m,10)["gold_k"], 1.08)
        m["radiant_gold_adv"][10] = float("inf")
        self.assertEqual(N["snapshot_features"](m,10)["gold_k"], 1.08)

    def test_pins_colab_and_local_match(self):
        tree = ast.parse(source_at(2))
        pins = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id=="PINS" for t in node.targets):
                pins = set(ast.literal_eval(node.value))
        self.assertIsNotNone(pins)
        required = set((ROOT/"requirements.txt").read_text().split())
        self.assertTrue(pins.issubset(required))

    def test_patch_coverage_requires_exact_two_equal_cohorts(self):
        f=N["patch_coverage_ok"]
        self.assertFalse(f([{"patch":60}]*499 + [{"patch":59}]))
        self.assertFalse(f([{"patch":60}]*480 + [{"patch":59}]*20))
        self.assertTrue(f([{"patch":60}]*250 + [{"patch":59}]*250))
        self.assertFalse(f([{"patch":60}]*200 + [{"patch":59}]*200 + [{"patch":58}]*100))

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

    def test_prefix_truncation_preserves_event_availability_flags(self):
        m=match_fixture()
        m["objectives"]=None
        m["players"][0]["kills_log"]=None
        original=N["snapshot_features"](m,10)
        truncated=N["prefix_truncated"](m,10)
        self.assertIsNone(truncated["objectives"])
        self.assertIsNone(truncated["players"][0]["kills_log"])
        self.assertTrue(math.isnan(original["tower_delta"]))
        self.assertTrue(math.isnan(original["kill_delta"]))
        N["assert_same_features"](original,N["snapshot_features"](truncated,10))

    def test_missing_event_logs_are_unknown_not_false_zero(self):
        m=match_fixture()
        no_objectives=copy.deepcopy(m)
        no_objectives["objectives"]=None
        x=N["snapshot_features"](no_objectives,10)
        self.assertTrue(math.isnan(x["tower_delta"]))
        self.assertTrue(math.isnan(x["barracks_delta"]))
        self.assertTrue(math.isnan(x["roshan_delta"]))
        present_but_empty=copy.deepcopy(m)
        present_but_empty["objectives"]=[]
        zero=N["snapshot_features"](present_but_empty,10)
        self.assertEqual(zero["tower_delta"],0)
        self.assertEqual(zero["roshan_delta"],0)
        missing_kills=copy.deepcopy(m)
        missing_kills["players"][0]["kills_log"]=None
        self.assertTrue(math.isnan(N["snapshot_features"](missing_kills,10)["kill_delta"]))
        no_players=copy.deepcopy(m)
        no_players["players"]=None
        self.assertTrue(math.isnan(N["snapshot_features"](no_players,10)["kill_delta"]))

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

    def test_item_purchase_cutoff_side_and_future_poisoning(self):
        m=match_fixture()
        for player in m["players"]: player["purchase_log"]=[]
        radiant=next(p for p in m["players"] if p["player_slot"]==0)
        dire=next(p for p in m["players"] if p["player_slot"]==128)
        radiant["purchase_log"]=[
            {"time":-8,"key":"blink"},
            {"time":600,"key":"black_king_bar"},
            {"time":601,"key":"manta"},
        ]
        dire["purchase_log"]=[{"time":601,"key":"force_staff"}]
        self.assertEqual(N["item_purchase_snapshot"](m,0),(1,1))
        self.assertEqual(N["item_purchase_snapshot"](m,9),(1,1))
        self.assertEqual(N["item_purchase_snapshot"](m,10),(2,2))
        self.assertEqual(N["item_purchase_snapshot"](m,11),(2,2))
        for t in (0,9,10,11,20,30):
            before=N["item_purchase_snapshot"](m,t)
            truncated=N["prefix_truncated"](m,t)
            self.assertEqual(before,N["item_purchase_snapshot"](truncated,t))
            altered=copy.deepcopy(m)
            altered["radiant_win"]=not m["radiant_win"]
            altered["players"][0]["net_worth"]=10000000
            altered["players"][0]["purchase_log"].append(
                {"time":60*t+10,"key":"radiance"})
            self.assertEqual(before,N["item_purchase_snapshot"](altered,t))

    def test_item_missing_purchases_are_not_fake_zero(self):
        m=match_fixture()
        self.assertTrue(all(math.isnan(x) for x in N["item_purchase_snapshot"](m,10)))
        for p in m["players"]:p["purchase_log"]=[]
        self.assertEqual(N["item_purchase_snapshot"](m,10),(0,0))
        m["players"][0]["purchase_log"].append({"time":None,"key":"blink"})
        self.assertTrue(all(math.isnan(x) for x in N["item_purchase_snapshot"](m,10)))
        self.assertEqual(N["SETS"]["M0_gold_only"],["gold_k"])
        self.assertEqual(N["SETS"]["M1_time_value"],
                         ["gold_k","minute10","gold_x_time"])
        self.assertEqual(N["ITEM_ADDED_COLUMNS"],
                         ["major_item_diff","blink_bkb_diff"])

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
        old_n, old_cohort = N["N_MATCHES"], N["COHORT_N"]
        N["N_MATCHES"], N["COHORT_N"] = 4, 2
        class FakeApi:
            def __init__(self):
                self.calls = 0
                self.details_seen = []
            def get(self, path, params=None):
                self.calls += 1
                if path == "/proMatches":
                    if not params:
                        return [{"match_id":i} for i in (9,8,7)]
                    return [{"match_id":i} for i in (6,5,4,3)]
                i = int(path.rsplit("/",1)[-1])
                self.details_seen.append(i)
                if i == 6:
                    return {"match_id":6, "duration":1800, "radiant_win":True, "radiant_gold_adv":None}
                return {"match_id":i,"duration":1800,"radiant_win":bool(i%2),
                        "radiant_gold_adv":[0,100], "patch":60 if i>=7 else 59}
        try:
            api=FakeApi()
            selected, exclusions = N["collect_matches"](api)
            self.assertEqual(set(m["match_id"] for m in selected), {4,5,7,8})
            self.assertTrue(any(mid == 6 for mid,reason in exclusions))
            self.assertTrue(N["patch_coverage_ok"](selected))
            # Discovery probes only the first valid match per page (or at most 3).
            self.assertLessEqual(api.calls, 12)
        finally:
            N["N_MATCHES"], N["COHORT_N"] = old_n, old_cohort

    def test_patch_discovery_avoids_full_payload_scan(self):
        old_n, old_cohort = N["N_MATCHES"], N["COHORT_N"]
        N["N_MATCHES"], N["COHORT_N"] = 4, 2
        class FakeApi:
            def __init__(self): self.details_seen=[]; self.calls=0
            def get(self,path,params=None):
                self.calls += 1
                if path=="/proMatches":
                    if not params:
                        return [{"match_id":i} for i in range(200,100,-1)]
                    return [{"match_id":i} for i in range(100,0,-1)]
                i=int(path.rsplit("/",1)[-1])
                self.details_seen.append(i)
                return {"match_id":i,"duration":1200,"radiant_win":bool(i%2),
                        "radiant_gold_adv":[0,10],"patch":60 if i>100 else 59}
        try:
            api=FakeApi()
            selected,_=N["collect_matches"](api)
            self.assertEqual(set(m["patch"] for m in selected),{59,60})
            self.assertLess(len(api.details_seen),20)
        finally:
            N["N_MATCHES"], N["COHORT_N"] = old_n, old_cohort


    def test_transient_unparsed_response_is_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = N["OpenDota"](cache_dir=tmp, interval=0)
            calls = []
            class Response:
                status_code=200
                def raise_for_status(self): pass
                def json(self):
                    return {"match_id": 123, "duration": 1500, "radiant_win": True,
                            "radiant_gold_adv": [0, 100] if len(calls) >= 2 else None}
            def fake_get(url, params, timeout):
                calls.append(url)
                return Response()
            api.session.get = fake_get
            self.assertIsNone(api.get("/matches/123")["radiant_gold_adv"])
            self.assertEqual(api.get("/matches/123")["radiant_gold_adv"], [0,100])
            self.assertEqual(api.get("/matches/123")["radiant_gold_adv"], [0,100])
            self.assertEqual(len(calls), 2)
            self.assertEqual(api.cache_hits, 1)

    def test_transient_429_retries_with_respectful_backoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            api=N["OpenDota"](cache_dir=tmp,interval=0,max_retries=4)
            requests_seen=[]
            waits=[]
            class Response:
                def __init__(self,code):
                    self.status_code=code
                    self.headers={"Retry-After":"11"} if code==429 else {}
                def raise_for_status(self):pass
                def json(self):return [{"match_id":123}]
            def fake_get(url,params,timeout):
                requests_seen.append(url)
                return Response(429 if len(requests_seen)<3 else 200)
            api.session.get=fake_get
            from unittest.mock import patch
            with patch.object(N["time"],"sleep",side_effect=lambda value:waits.append(value)):
                result=api.get("/proMatches")
            self.assertEqual(result,[{"match_id":123}])
            self.assertEqual(api.calls,3)
            self.assertEqual(len(requests_seen),3)
            self.assertGreaterEqual(len(waits),2)
            self.assertGreaterEqual(min(waits),11)

    def test_persistent_503_bounded_and_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            api=N["OpenDota"](cache_dir=tmp,interval=0,max_retries=2)
            class Response:
                status_code=503
                headers={}
            api.session.get=lambda url,params,timeout:Response()
            from unittest.mock import patch
            with patch.object(N["time"],"sleep",return_value=None):
                with self.assertRaisesRegex(RuntimeError,
                         "OpenDota failed after 2 bounded attempts.*HTTP 503"):
                    api.get("/matches/123")
            self.assertEqual(api.calls,2)

    def test_corrupt_cache_is_replaced_by_fresh_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = N["OpenDota"](cache_dir=tmp, interval=0)
            calls = []
            class Response:
                status_code=200
                def raise_for_status(self): pass
                def json(self): return [{"match_id": 123}]
            def fake_get(url, params, timeout):
                calls.append(url)
                return Response()
            api.session.get=fake_get
            api.get("/proMatches")
            files=list(Path(tmp).glob("*.json.gz"))
            self.assertEqual(len(files),1)
            files[0].write_bytes(b"not a gzip file")
            self.assertEqual(api.get("/proMatches"),[{"match_id":123}])
            self.assertEqual(len(calls),2)

    def test_only_http404_is_missing_match_and_decode_failure_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            api=N["OpenDota"](cache_dir=tmp, interval=0, max_retries=2)
            class Response:
                status_code=404
                def raise_for_status(self): pass
                def json(self): return {}
            api.session.get=lambda url,params,timeout: Response()
            with self.assertRaises(N["MatchNotFound"]):
                api.get("/matches/123")
            attempts=[]
            class BadResponse:
                status_code=200
                def raise_for_status(self): pass
                def json(self):
                    attempts.append(1)
                    if len(attempts)==1: raise ValueError("truncated 200 response")
                    return [{"match_id":1}]
            api.session.get=lambda url,params,timeout: BadResponse()
            from unittest.mock import patch
            with patch.object(N["time"], "sleep", return_value=None):
                self.assertEqual(api.get("/proMatches"),[{"match_id":1}])
            self.assertEqual(len(attempts),2)

    def test_older_patch_tail_in_previous_page_is_selected(self):
        old_n, old_cohort=N["N_MATCHES"],N["COHORT_N"]
        N["N_MATCHES"],N["COHORT_N"]=4,2
        class FakeApi:
            def __init__(self): self.calls=0
            def get(self,path,params=None):
                self.calls+=1
                if path=="/proMatches":
                    return ([{"match_id":i} for i in (9,8,7)] if not params
                            else [{"match_id":i} for i in (6,5,4,3)])
                mid=int(path.rsplit("/",1)[-1])
                return {"match_id":mid,"duration":1500,"radiant_win":bool(mid%2),
                        "radiant_gold_adv":[0,100],"patch":60 if mid>=8 else 59}
        try:
            api=FakeApi()
            selected,_=N["collect_matches"](api)
            self.assertEqual(set(m["match_id"] for m in selected),{6,7,8,9})
            self.assertTrue(N["patch_coverage_ok"](selected))
            self.assertLess(api.calls,15)
        finally:
            N["N_MATCHES"],N["COHORT_N"]=old_n,old_cohort

    def test_frozen_manifest_fetches_only_500_named_matches_and_no_recent_feed(self):
        old_n, old_cohort = N["N_MATCHES"], N["COHORT_N"]
        N["N_MATCHES"], N["COHORT_N"] = 4, 2
        class FrozenAPI:
            def __init__(self):
                self.paths = []
            def get(self, path, params=None):
                self.paths.append(path)
                if path == "/proMatches":
                    raise AssertionError("Frozen manifest must never page through a moving feed")
                mid = int(path.rsplit("/", 1)[-1])
                return {"match_id":mid, "duration":1200, "radiant_win":bool(mid%2),
                        "radiant_gold_adv":[0, 10], "patch":59 if mid in (11,12) else 60}
        try:
            api=FrozenAPI()
            matches, exclusions=N["collect_matches"](api, (11,12,13,14))
            self.assertEqual(len(matches),4)
            self.assertEqual(exclusions,[])
            self.assertEqual(api.paths,["/matches/11","/matches/12","/matches/13","/matches/14"])
            with self.assertRaises(ValueError):
                N["collect_matches"](FrozenAPI(),(11,11,13,14))
        finally:
            N["N_MATCHES"], N["COHORT_N"] = old_n, old_cohort

    def test_frozen_cohort_fingerprint_is_outcome_blind_and_strict(self):
        frame = pd.DataFrame([
            {"match_id":10,"start_time":1000,"patch":"59",
             "radiant_win":True},
            {"match_id":11,"start_time":1010,"patch":"60",
             "radiant_win":False},
        ])
        digest = N["manifest_identity_hash"](frame)
        self.assertEqual(len(digest),64)
        self.assertEqual(digest,N["manifest_identity_hash"](
            frame.sample(frac=1,random_state=12)))
        changed=frame.copy()
        changed["radiant_win"] = ~changed["radiant_win"]
        self.assertEqual(digest,N["manifest_identity_hash"](changed))
        changed=frame.copy()
        changed.loc[0,"start_time"] += 1
        self.assertNotEqual(digest,N["manifest_identity_hash"](changed))
        changed=frame.copy()
        changed.loc[0,"patch"] = "60"
        self.assertNotEqual(digest,N["manifest_identity_hash"](changed))
        with self.assertRaisesRegex(ValueError,"Duplicate cohort"):
            N["manifest_identity_hash"](
                pd.concat([frame,frame.iloc[[0]]],ignore_index=True))
        self.assertIn("e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea",
                      source_at(5))

    def test_frozen_manifest_rejects_wrong_source_match_id(self):
        """Patch balance cannot authenticate the requested cohort identity."""
        old_n, old_c = N["N_MATCHES"], N["COHORT_N"]
        N["N_MATCHES"], N["COHORT_N"] = 4, 2
        class SwappedAPI:
            def get(self, path, params=None):
                requested = int(path.rsplit("/", 1)[-1])
                mid = 15 if requested == 11 else requested
                return {"match_id":mid, "duration":1200,
                        "radiant_win":bool(mid % 2),
                        "radiant_gold_adv":[0, 10],
                        "patch":59 if mid in (12, 15) else 60}
        try:
            with self.assertRaisesRegex(ValueError, "requested match 11"):
                N["collect_matches"](SwappedAPI(), (11, 12, 13, 14))
            with self.assertRaisesRegex(ValueError, "requested match 123"):
                N["verify_match_identity"]("/matches/123",
                                           {"match_id": True})
            with self.assertRaisesRegex(ValueError, "Non-object"):
                N["verify_match_identity"]("/matches/123", [])
        finally:
            N["N_MATCHES"], N["COHORT_N"] = old_n, old_c

    def test_misidentified_cached_match_refetched_and_http_mismatch_fails(self):
        import gzip
        with tempfile.TemporaryDirectory() as tmp:
            api = N["OpenDota"](cache_dir=tmp, interval=0)
            requests = []
            class Response:
                status_code = 200
                def raise_for_status(self): pass
                def json(self):
                    return {"match_id":123, "duration":1200,
                            "radiant_win":True,
                            "radiant_gold_adv":[0, 100]}
            api.session.get = lambda url, params, timeout: (
                requests.append(url) or Response())
            self.assertEqual(api.get("/matches/123")["match_id"], 123)
            cached = list(Path(tmp).glob("*.json.gz"))
            self.assertEqual(len(cached), 1)
            with gzip.open(cached[0], "wt") as handle:
                json.dump({"match_id":999, "duration":1200,
                           "radiant_win":False,
                           "radiant_gold_adv":[0, 999]}, handle)
            self.assertEqual(api.get("/matches/123")["match_id"], 123)
            self.assertEqual(len(requests), 2)
            self.assertEqual(api.cache_hits, 0)
        with tempfile.TemporaryDirectory() as tmp:
            api = N["OpenDota"](cache_dir=tmp, interval=0,
                                max_retries=2)
            class WrongResponse:
                status_code = 200
                def raise_for_status(self): pass
                def json(self):
                    return {"match_id":999, "duration":1200,
                            "radiant_win":True, "radiant_gold_adv":[0, 100]}
            api.session.get = lambda url, params, timeout: WrongResponse()
            with self.assertRaisesRegex(RuntimeError, "requested match 123"):
                api.get("/matches/123")
            self.assertEqual(api.calls, 1)
            self.assertFalse(list(Path(tmp).glob("*.json.gz")))

    def test_frozen_manifest_refuses_silent_replacement_of_unparsed_match(self):
        old_n, old_cohort = N["N_MATCHES"], N["COHORT_N"]
        N["N_MATCHES"], N["COHORT_N"] = 4, 2
        class PartialAPI:
            def get(self, path, params=None):
                mid=int(path.rsplit("/",1)[-1])
                return {"match_id":mid, "duration":1800, "radiant_win":bool(mid%2),
                        "radiant_gold_adv":None if mid==12 else [0,50],
                        "patch":59 if mid in (11,12) else 60}
        try:
            with self.assertRaisesRegex(ValueError, "unusable"):
                N["collect_matches"](PartialAPI(),(11,12,13,14))
        finally:
            N["N_MATCHES"], N["COHORT_N"] = old_n, old_cohort

    def test_short_gold_array_uses_only_last_available_past_snapshot(self):
        m = match_fixture()
        m["radiant_gold_adv"] = m["radiant_gold_adv"][:11]
        at20 = N["snapshot_features"](m,20)
        self.assertEqual(at20["gold_k"],1.2)
        N["assert_same_features"](at20,N["snapshot_features"](N["prefix_truncated"](m,20),20))


    def test_kaggle_detection_overrides_colab_release_tag(self):
        # The real Kaggle Python 3.13 base image sets COLAB_RELEASE_TAG as well
        # as KAGGLE_KERNEL_RUN_TYPE; installing a new NumPy in that live kernel
        # caused an actual binary ABI failure during the first execution.
        import os
        from unittest.mock import patch
        prelude = source_at(2).split("PINS = (")[0]
        with patch.dict(os.environ, {"KAGGLE_KERNEL_RUN_TYPE": "Script",
                                         "COLAB_RELEASE_TAG": "true"}, clear=False):
            env = {}
            exec(prelude,env)
            self.assertTrue(env["ON_KAGGLE"])
            self.assertFalse(env["COLAB"])
        with patch.dict(os.environ, {"COLAB_RELEASE_TAG": "true"}, clear=True):
            env = {}
            exec(prelude,env)
            self.assertTrue(env["COLAB"])
            self.assertFalse(env["ON_KAGGLE"])


    def test_excluding_terminal_minutes_uses_each_match_own_clock(self):
        cell=next(c for c in NB["cells"] if c.get("id")=="vexil-terminal-code")
        tree=ast.parse("".join(cell["source"]))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="exclude_terminal_minutes")
        scope={"pd":pd}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"<terminal-test>","exec"),scope)
        frame=pd.DataFrame({"match_id":[1]*5+[2]*3,"minute":list(range(5))+list(range(3))})
        kept=scope["exclude_terminal_minutes"](frame,n=2)
        self.assertEqual(kept.groupby("match_id").minute.max().to_dict(),{1:2,2:0})
        self.assertEqual(len(kept),4)
        self.assertEqual(len(frame),8)
        with self.assertRaises(ValueError):
            scope["exclude_terminal_minutes"](frame,n=-1)

    def test_wilson_interval_bounds_and_extremes(self):
        cell = next(c for c in NB["cells"] if c.get("id") == "vexil-comeback-data")
        tree = ast.parse("".join(cell["source"]))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "wilson_95")
        namespace = {"math": math}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<wilson-test>", "exec"), namespace)
        low, high = namespace["wilson_95"](0, 10)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.2775328, places=6)
        low, high = namespace["wilson_95"](5, 10)
        self.assertTrue(0.23 < low < 0.24)
        self.assertTrue(0.76 < high < 0.77)
        low, high = namespace["wilson_95"](10, 10)
        self.assertAlmostEqual(high, 1.0, places=10)
        self.assertTrue(0.72 < low < 0.73)

if __name__ == "__main__":
    unittest.main()
