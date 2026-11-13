"""Independent oracle mutation tests; no network or Kaggle."""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from research.independent_delivery_audit import (
    _json_match_filename, load_provenance, proper_scores, bootstrap_delta,
    independent_metric_oracle,
)


def example_predictions():
    return pd.DataFrame([
        {"match_id":11,"minute":0,"radiant_win":0,"p_model":.2,"p_baseline":.4},
        {"match_id":11,"minute":1,"radiant_win":0,"p_model":.3,"p_baseline":.4},
        {"match_id":12,"minute":0,"radiant_win":1,"p_model":.8,"p_baseline":.6},
        {"match_id":12,"minute":1,"radiant_win":1,"p_model":.7,"p_baseline":.6},
    ])


class IndependentRedteamTest(unittest.TestCase):
    def test_proper_score_matches_hand_calculation(self):
        f=proper_scores(example_predictions())
        self.assertAlmostEqual(f.iloc[0].logloss_model, -np.log(.8))
        self.assertAlmostEqual(f.iloc[0].logloss_baseline, -np.log(.6))
        self.assertAlmostEqual(f.iloc[0].brier_model, .04)
        self.assertAlmostEqual(f.iloc[2].brier_model, .04)
        self.assertLess(f.logloss_model.mean(), f.logloss_baseline.mean())

    def test_reject_duplicate_keys_corrupt_labels_and_probabilities(self):
        f=example_predictions()
        for variant in [
            pd.concat([f,f.iloc[[0]]],ignore_index=True),
            f.assign(radiant_win=[0,1,2,0]),
            f.assign(p_model=[.2,.3,np.nan,.7]),
            f.assign(p_baseline=[.4,.4,1.02,.6]),
            f.assign(p_baseline=[.4,.4,-.1,.6]),
            f.assign(p_model=[.2,.3,float("inf"),.7]),
        ]:
            with self.subTest(case=str(variant.iloc[0].to_dict())):
                with self.assertRaises(ValueError):
                    proper_scores(variant)

    def test_cluster_resampling_is_order_invariant_and_paired(self):
        f=proper_scores(example_predictions())
        f["series_cluster"]=["a","a","b","b"]
        x=bootstrap_delta(f,"series_cluster","logloss",n_boot=1200,seed=19)
        y=bootstrap_delta(f.sample(frac=1,random_state=57),
                          "series_cluster","logloss",n_boot=1200,seed=19)
        self.assertEqual(x,y)
        self.assertEqual(x["clusters"],2)
        self.assertEqual(x["minutes"],4)
        self.assertTrue(x["ci95"][0] <= x["delta"] <= x["ci95"][1])
        with self.assertRaises(ValueError):
            bootstrap_delta(f[f.series_cluster=="a"],"series_cluster","logloss")

    def test_oracle_detects_tampered_original_metric(self):
        f=proper_scores(example_predictions())
        # Ensure all report phases have rows by adding age-offset copies.
        frames=[]
        for offset in (0, 10, 20, 30):
            v=f.copy()
            v["minute"]+=offset
            frames.append(v)
        all_phases=pd.concat(frames,ignore_index=True)
        all_phases["match_id"] += (all_phases.minute // 10)*1000
        all_phases=proper_scores(all_phases[["match_id","minute","radiant_win","p_model","p_baseline"]])
        scores=[]
        for phase,sub in [("overall",all_phases),
                          ("0–9",all_phases[all_phases.minute<10]),
                          ("10–19",all_phases[(all_phases.minute>=10)&(all_phases.minute<20)]),
                          ("20–29",all_phases[(all_phases.minute>=20)&(all_phases.minute<30)]),
                          ("30+",all_phases[all_phases.minute>=30])]:
            for name in ("logloss","brier"):
                scores.append({"phase":phase,"metric":name,
                               "model":float(sub[name+"_model"].mean()),
                               "baseline":float(sub[name+"_baseline"].mean()),
                               "difference":float((sub[name+"_model"]-sub[name+"_baseline"]).mean())})
        original=pd.DataFrame(scores)
        independent_metric_oracle(all_phases,original)
        mutated=original.copy()
        mutated.loc[(mutated.phase=="overall")&(mutated.metric=="logloss"),"model"]+=.001
        with self.assertRaises(ValueError):
            independent_metric_oracle(all_phases,mutated)

    def test_source_provenance_checks_cache_identity_patch_time(self):
        metadata=pd.DataFrame([dict(match_id=101,patch=60,series_id=123,
                                    start_time=1234567,partition="test")])
        payload=dict(match_id=101,patch=60,start_time=1234567,duration=1800,
                     leagueid=7,radiant_win=True)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/_json_match_filename(101)
            def write(value):
                with gzip.open(path,"wt",encoding="utf8") as h:json.dump(value,h)
            write(payload)
            got=load_provenance(metadata,Path(tmp))
            self.assertEqual(int(got.iloc[0].estimated_end_time),1234567+1800)
            for change in [
                {"match_id":202}, {"patch":59}, {"start_time":1234570}
            ]:
                corrupt=copy.deepcopy(payload);corrupt.update(change);write(corrupt)
                with self.subTest(change=change),self.assertRaises(ValueError):
                    load_provenance(metadata,Path(tmp))


if __name__=="__main__":
    unittest.main()
