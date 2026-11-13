"""Offline adversarial tests for the current OpenDota source canary."""
from __future__ import annotations
import copy
import unittest

import pandas as pd

from research.current_source_canary import _equal_number, compare_payloads, sample
from test_notebook_contracts import N, match_fixture


def source_fixture():
    m=match_fixture()
    m.update(match_id=123, start_time=1700000000, series_id=77, patch=60)
    for player in m["players"]:
        player["purchase_log"]=[]
    return m


class CurrentSourceCanaryTest(unittest.TestCase):
    def test_identical_source_and_auxiliary_reparse(self):
        m=source_fixture()
        result=compare_payloads(m,copy.deepcopy(m),N)
        self.assertEqual(result["feature_mismatches"],{})
        self.assertTrue(result["raw_digest_unchanged"])
        fresh=copy.deepcopy(m)
        fresh["unrelated_api_field"]="Changed by upstream OpenDota reparse"
        changed=compare_payloads(m,fresh,N)
        self.assertFalse(changed["raw_digest_unchanged"])
        self.assertFalse(changed["feature_mismatches"])

    def test_gold_or_item_reparse_detected(self):
        original=source_fixture()
        corrupted=copy.deepcopy(original)
        t=25
        # Shift player gold and aggregate gold by same amount, preserving
        # internal source alignment but changing a point-in-time input.
        corrupted["players"][0]["gold_t"][t]+=100
        corrupted["radiant_gold_adv"][t]+=100
        changed=compare_payloads(original,corrupted,N)
        self.assertGreater(changed["feature_mismatches"].get("gold_k",0),0)
        corrupted=copy.deepcopy(original)
        corrupted["players"][0]["purchase_log"].append(
            {"time":610,"key":"blink"})
        changed=compare_payloads(original,corrupted,N)
        self.assertGreater(changed["feature_mismatches"].get("major_item_diff",0)
                           +changed["feature_mismatches"].get("blink_bkb_diff",0),0)

    def test_source_clock_and_label_drift_fail(self):
        old=source_fixture()
        bad=copy.deepcopy(old)
        bad["radiant_win"]=not old["radiant_win"]
        with self.assertRaises(ValueError):
            compare_payloads(old,bad,N)
        bad=copy.deepcopy(old)
        bad["players"][0]["times"][1]=59
        with self.assertRaises(ValueError):
            compare_payloads(old,bad,N)

    def test_numeric_comparison_does_not_collapse_nan_bool(self):
        self.assertTrue(_equal_number(float("nan"),float("nan")))
        self.assertFalse(_equal_number(float("nan"),2.))
        self.assertFalse(_equal_number(True,2.))
        self.assertTrue(_equal_number(1.,1.0000000001))

    def test_sample_patch_balance_and_order_invariance(self):
        rows=[]
        for patch in (59,60):
            for i in range(25):
                rows.append(dict(patch=patch,start_time=1000*patch+i,
                                 match_id=patch*10000+i))
        a=pd.DataFrame(rows)
        x=sample(a,per_patch=5)
        y=sample(a.sample(frac=1,random_state=7),per_patch=5)
        self.assertEqual(x,y)
        self.assertEqual(len(x),10)
        self.assertEqual(len(set(x)),10)
        with self.assertRaises(ValueError):
            sample(a[a.patch==60],per_patch=5)


if __name__=="__main__":
    unittest.main()
