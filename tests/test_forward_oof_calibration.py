import importlib.util
import inspect
import json
import hashlib
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from scipy.special import expit, logit

SRC=Path(__file__).resolve().parents[1] / "research/forward_oof_calibration.py"
SPEC=importlib.util.spec_from_file_location("calibration",SRC)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def game_fixture(duration=665):
    n=(duration-1)//60+1
    times=[i*60 for i in range(n)]
    players=[]
    for slot in list(range(5))+list(range(128,133)):
        # Changes with minute; team advantage recomputed exactly.
        players.append({
            "player_slot":slot, "times":times[:],
            "gold_t":[1000+t*(20 if slot<128 else 15) for t in range(n)],
            "xp_t":[500+t*(17 if slot<128 else 11) for t in range(n)],
        })
    gold=[sum((1 if p["player_slot"]<128 else -1)*p["gold_t"][t]
              for p in players) for t in range(n)]
    xp=[sum((1 if p["player_slot"]<128 else -1)*p["xp_t"][t]
            for p in players) for t in range(n)]
    return {
        "match_id":33,"duration":duration,"start_time":10000,"patch":59,
        "series_id":77, "radiant_win":True,"players":players,
        "radiant_gold_adv":gold,"radiant_xp_adv":xp,
    }


class CalibrationContracts(unittest.TestCase):
    def test_source_reader_cannot_fetch_test_labels(self):
        # Additional source-level guard. Real 394-game integration is executed
        # separately against frozen cached OpenDota JSON.
        text=inspect.getsource(MOD.load_development)
        self.assertIn('if item["partition"] == "test":',text)
        self.assertLess(text.index('if item["partition"] == "test":'),
                        text.index('with gzip.open(file, "rt", encoding="utf-8") as f:'))

    def test_game_features_strict_preterminal(self):
        g=game_fixture(duration=660)
        m={"match_id":33,"start_time":10000,"patch":59,"series_id":77,"partition":"train"}
        rows=MOD.parse_game_features(g,m)
        self.assertEqual(len(rows),11)
        self.assertEqual(rows[0]["minute"],0)
        self.assertEqual(rows[-1]["minute"],10)
        self.assertEqual(rows[-1]["gold_k"],0.25)
        self.assertEqual(rows[-1]["minute10"],1)
        self.assertAlmostEqual(rows[-1]["gold_x_time"],.25*np.log1p(1))

    def test_exact_boundary_excludes_terminal(self):
        g=game_fixture(duration=600)
        m={"match_id":33,"start_time":10000,"patch":59,"series_id":77,"partition":"train"}
        rows=MOD.parse_game_features(g,m)
        self.assertEqual(rows[-1]["minute"],9)

    def test_bad_clock_fails_closed(self):
        g=game_fixture()
        g["players"][0]["times"][3]=125
        with self.assertRaises(ValueError):
            MOD.parse_game_features(g, {"match_id":33,"start_time":10000,
                                         "patch":59,"series_id":77,"partition":"train"})

    def test_bad_economy_fails_closed(self):
        g=game_fixture()
        g["radiant_gold_adv"][2]+=1
        with self.assertRaises(ValueError):
            MOD.parse_game_features(g, {"match_id":33,"start_time":10000,
                                         "patch":59,"series_id":77,"partition":"train"})

    def test_bad_match_identity_or_result_fails_closed(self):
        g=game_fixture()
        with self.assertRaises(ValueError):
            MOD.parse_game_features(g,{"match_id":32,"start_time":10000,
                                       "patch":59,"series_id":77,"partition":"train"})
        g["radiant_win"]=1
        with self.assertRaises(ValueError):
            MOD.parse_game_features(g,{"match_id":33,"start_time":10000,
                                       "patch":59,"series_id":77,"partition":"train"})

    def test_intercept_root_and_fixed_slope(self):
        p=np.asarray([0.15,0.3,0.6,0.8],dtype=float)
        y=np.asarray([0,1,1,1])
        b=MOD.find_intercept_offset(p,y)
        after=expit(logit(p)+b)
        self.assertAlmostEqual(float(np.mean(after)),float(y.mean()),places=11)
        self.assertGreater(b,0)
        np.testing.assert_allclose(logit(after)-logit(p),b,rtol=0,atol=1e-12)
        self.assertEqual(b,MOD.find_intercept_offset(p,y))

    def test_intercept_is_zero_when_mean_is_already_correct(self):
        p=np.asarray([.3,.7])
        y=np.asarray([0,1])
        self.assertAlmostEqual(MOD.find_intercept_offset(p,y),0,places=10)

    def test_reject_invalid_calibration_probabilities(self):
        for p in ([0,1],[0.2,float("nan")],[-0.1,.7]):
            with self.assertRaises(ValueError):
                MOD.find_intercept_offset(p,[0,1])

    def test_same_probability_bootstrap_delta_is_exact_zero(self):
        df=pd.DataFrame({
            "match_id":[11,11,12,12],"series_id":[9,9,10,10],
            "y":[0,0,1,1],"p_uncal":[.2,.3,.8,.7],
            "p_offset":[.2,.3,.8,.7]
        })
        stat=MOD.paired_bootstrap(df,draws=50)
        self.assertEqual(stat["groups"],2)
        self.assertAlmostEqual(stat["difference_cal_minus_original_brier"],0,places=13)
        self.assertEqual(stat["series_bootstrap_95ci_brier"],[0,0])

    def test_ece_for_perfect_probabilistic_forecast(self):
        y=np.asarray([0,0,1,1])
        p=np.asarray([0.5,0.5,0.5,0.5])
        self.assertAlmostEqual(MOD.ece10(y,p),0)
        self.assertGreater(MOD.ece10(y,np.asarray([.1,.1,.1,.1])),0)

    def test_full_split_manifest_binding_detects_partition_tamper(self):
        from tempfile import TemporaryDirectory
        import shutil
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"manifest.csv"
            shutil.copyfile(MOD.ROOT/"research/calibration_frozen_manifest.csv",path)
            self.assertEqual(MOD.verify_split_manifest_bytes(path),
                             MOD.SPLIT_MANIFEST_FILE_SHA)
            text=path.read_text()
            self.assertIn(",train",text)
            path.write_text(text.replace(",train",",test",1))
            with self.assertRaises(ValueError):
                MOD.verify_split_manifest_bytes(path)

    def test_series_safe_cut_amendment_and_embargo(self):
        import pandas as pd
        manifest=pd.read_csv(MOD.ROOT/"research/calibration_frozen_manifest.csv")
        info,cuts=MOD.series_safe_cutpoints(manifest)
        self.assertEqual(cuts,[154,176,220,252,291])
        _,old_fourth=MOD.series_safe_cutpoints(manifest,
                                fractions=(0.45,0.65,0.75,0.84))
        self.assertEqual(old_fourth,[154,176,220,247,291])

    def test_posthoc_offset_ci_and_variant_receipt_not_a_promotion(self):
        d=json.loads((MOD.ROOT/"research/CALIBRATION_SENSITIVITY_RECEIPT.json").read_text())
        self.assertEqual(d["original_test_games_read"],0)
        self.assertTrue(d["do_not_select_best_variant"])
        self.assertTrue(d["reanalysis_occurred_after_first_val_results"])
        lo,hi=d["variations"]["original_executed_grid"]["series_bootstrap_offset"]["offset_95ci"]
        self.assertLess(lo,0)
        self.assertGreater(hi,0)
        self.assertEqual(d["variations"]["exclude_5_train_overlaps_at_val"]
                         ["excluded_incomplete_train_games"],5)

    def test_receipt_declares_no_test_or_promotion(self):
        receipt=MOD.RECEIPT_PATH
        if not receipt.exists():
            self.skipTest("Receipt not generated yet")
        d=json.loads(receipt.read_text())
        self.assertEqual(d["evidence_class"],
                         "TRAIN_ONLY_OFFSET_REUSED_VAL_EXPLORATORY_NO_TEST_ACCESS")
        self.assertEqual(d["inputs"]["test_games_read"],0)
        self.assertTrue(d["test_untouched"])
        self.assertTrue(d["selected_model_unchanged"])
        self.assertEqual(d["selection"]["oof_train_games"],137)
        self.assertEqual(d["selection"]["oof_rows"],5081)
        self.assertEqual(d["reused_validation"]["M1_original"]["games"],103)


if __name__ == "__main__":
    unittest.main()
