"""Check saved VAL forecasts without fitting to or scoring original TEST."""
from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("vexil_val_audit",ROOT/"scripts/verify_validation_bias.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ValidationBiasAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pd.read_csv(ROOT/"artifacts/validation_m0_m1_predictions.csv")
        cls.receipt=json.loads((ROOT/"docs/VALIDATION_BIAS_RECEIPT.json").read_text())

    def test_offline_source_predictions_match_notebook_and_bias_receipt(self):
        actual=MOD.check()
        self.assertEqual(actual["status"],"PASS_FROZEN_VALIDATION_BIAS_OFFLINE")
        self.assertEqual(actual["validation_games"],103)
        self.assertEqual(actual["validation_minutes"],3781)
        self.assertEqual(actual["series_or_singletons"],53)
        self.assertAlmostEqual(actual["validation_m1_bias"],.029950219573246027,places=13)
        self.assertTrue(actual["never_a_new_blind_test"])

    def test_val_train_test_partition_and_professional_series_are_disjoint(self):
        source=self.source
        train=pd.read_csv(ROOT/"research/frozen_original_train_features.csv.gz")
        test=pd.read_csv(ROOT/"artifacts/heldout_predictions.csv")
        groups=json.loads((ROOT/"docs/SERIES_GROUPS_TEST.json").read_text())
        ids={
          "train":set(train.match_id.astype(int)),
          "validation":set(source.match_id.astype(int)),
          "test":set(test.match_id.astype(int))
        }
        self.assertEqual({k:len(v) for k,v in ids.items()},
                         {"train":291,"validation":103,"test":106})
        self.assertFalse(ids["train"] & ids["validation"])
        self.assertFalse(ids["validation"] & ids["test"])
        self.assertFalse(ids["test"] & ids["train"])
        self.assertEqual(len(set.union(*ids.values())),500)
        s_train={int(x) for x in train.series_id if int(x)>0}
        s_val={int(x) for x in source.series_id if int(x)>0}
        s_test={int(x["series_id"]) for x in groups.values() if int(x["series_id"])>0}
        self.assertFalse(s_train&s_val)
        self.assertFalse(s_train&s_test)
        self.assertFalse(s_val&s_test)
        self.assertEqual(source.patch.astype(str).unique().tolist(),["60"])

    def test_independent_pandas_groupby_proper_scores_and_calibration(self):
        f=self.source
        y=f.radiant_win.to_numpy(dtype=float)
        for model,expected in (
            ("M0",(.5324900423908928,.18107468309068306,.03267276988310906)),
            ("M1",(.519713962581426,.1759016844633358,.029950219573246027))
        ):
            p=f["p_"+model].to_numpy(dtype=float)
            ll=(-(y*np.log(p)+(1-y)*np.log1p(-p))).mean()
            brier=((p-y)**2).mean()
            bias=(p-y).mean()
            for x,want in zip((ll,brier,bias),expected):
                self.assertAlmostEqual(float(x),want,places=12)
            self.assertAlmostEqual(bias,
                self.receipt["models"][model]["bias_predicted_minus_observed_minute"],
                places=12)
        game=f.groupby("match_id").radiant_win.first()
        self.assertEqual(int(game.sum()),50)
        self.assertEqual(len(game),103)
        self.assertAlmostEqual(float(y.mean()),.48743718592964824,places=12)

        # Independent pandas groupby oracle for the VALIDATION 10k-draw
        # series/singleton CI, with intact within-match labels and the
        # published seed. This verifies the ratio estimator rather than
        # merely re-reading its receipt or refitting a model.
        frame=f.copy()
        frame["cluster"]=np.where(
            frame.series_id.to_numpy(dtype=int)>0,
            "s"+frame.series_id.astype(str).to_numpy(),
            "m"+frame.match_id.astype(str).to_numpy())
        frame["m1_residual"]=frame.p_M1-frame.radiant_win
        series=frame.groupby("cluster",sort=True)
        n=series.size().to_numpy(dtype=float)
        total=series.m1_residual.sum().to_numpy(dtype=float)
        self.assertEqual(len(n),53)
        draws=np.random.default_rng(20261116).integers(
            0,len(n),size=(10000,len(n)))
        minutes=total[draws].sum(axis=1)/n[draws].sum(axis=1)
        want=self.receipt["models"]["M1"]["bias_minute_ci_95_series"]
        np.testing.assert_allclose(np.quantile(minutes,[.025,.975]),
                                   want,rtol=0,atol=1e-12)
        games=frame.groupby(["cluster","match_id"],sort=True).m1_residual.mean().reset_index()
        grouped=games.groupby("cluster",sort=True)
        ng=grouped.size().to_numpy(dtype=float)
        tg=grouped.m1_residual.sum().to_numpy(dtype=float)
        games_ratio=tg[draws].sum(axis=1)/ng[draws].sum(axis=1)
        want_game=self.receipt["models"]["M1"]["bias_equal_game_ci_95_series"]
        np.testing.assert_allclose(np.quantile(games_ratio,[.025,.975]),
                                   want_game,rtol=0,atol=1e-12)

    def test_validation_diagnostic_is_not_a_second_test_or_calibration_fit(self):
        r=self.receipt
        self.assertTrue(r["analysis_is_post_selection_and_descriptive"])
        self.assertTrue(r["no_TEST_recalibration_or_score"])
        self.assertTrue(r["raw_cache_required_only_for_source_reconstruction"])
        self.assertEqual(r["original_test_games_not_scored"],106)
        self.assertAlmostEqual(r["train_game_win_rate_from_frozen_csv"],149/291)
        for name in ("M0","M1"):
            ci=r["models"][name]["bias_minute_ci_95_series"]
            self.assertLess(ci[0],0)
            self.assertGreater(ci[1],0)

    def test_rejects_mutated_source_and_receipt(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"val.csv"
            p.write_bytes(MOD.SOURCE.read_bytes()+b"\n")
            with patch.object(MOD,"SOURCE",p),self.assertRaisesRegex(
                ValueError,"forecast SHA"):
                MOD.check()
            q=Path(tmp)/"receipt.json"
            data=json.loads(MOD.RECEIPT.read_text())
            data["models"]["M1"]["logloss"]-=.06
            q.write_text(json.dumps(data))
            with patch.object(MOD,"RECEIPT",q),self.assertRaisesRegex(
                ValueError,"numeric mismatch"):
                MOD.check()


if __name__=="__main__":
    unittest.main()
