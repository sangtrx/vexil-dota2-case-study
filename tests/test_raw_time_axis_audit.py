import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from raw_time_axis_audit import inspect_array_lengths


class RawArrayTimeAxis(unittest.TestCase):
    def data(self,n=3):
        return {"duration":125,
          "radiant_gold_adv":[0]*n,"radiant_xp_adv":[0]*n,
          "players":[{k:[0]*n for k in ("gold_t","xp_t","lh_t","dn_t")}
                     for _ in range(10)]}

    def test_duration_exact_grid(self):
        d=inspect_array_lengths(self.data())
        self.assertEqual(len(d),42)
        self.assertTrue(all(x==0 for x in d.values()))

    def test_missing_early_samples_must_not_silently_pass(self):
        d=self.data()
        d["radiant_gold_adv"].pop()
        self.assertEqual(inspect_array_lengths(d)["radiant_gold_adv"],-1)

    def test_extra_terminal_sample_is_flagged(self):
        d=self.data(4)
        out=inspect_array_lengths(d)
        self.assertEqual(out["radiant_gold_adv"],1)
        self.assertEqual(out["p9_dn_t"],1)

    def test_missing_player_or_wrong_duration_refused(self):
        d=self.data()
        d["players"].pop()
        with self.assertRaises(ValueError):
            inspect_array_lengths(d)
        d=self.data()
        d["duration"]=-1
        with self.assertRaises(ValueError):
            inspect_array_lengths(d)


if __name__=="__main__":
    unittest.main()
