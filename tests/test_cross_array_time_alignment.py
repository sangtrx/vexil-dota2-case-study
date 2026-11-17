import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from cross_array_time_alignment import check_single_game


def toy():
    players=[]
    for slot in [0,1,2,3,4,128,129,130,131,132]:
        players.append({"player_slot":slot,"times":[0,60,120],
                        "gold_t":[1,2,3],"xp_t":[0,4,9]})
    return {"duration":169,"radiant_gold_adv":[0,0,0],
            "radiant_xp_adv":[0,0,0],"players":players}


class CrossArrayTimeValidation(unittest.TestCase):
    def test_exact_matched_arrays(self):
        d=check_single_game(toy())
        self.assertEqual(d["raw_snapshots"],3)
        self.assertEqual(d["terminal_or_postterminal_array_slots"],0)

    def test_first_sample_shift_is_rejected(self):
        d=toy()
        d["players"][0]["times"]=[60,120,180]
        with self.assertRaisesRegex(AssertionError,"timestamp"):
            check_single_game(d)

    def test_single_game_player_shift_rejected(self):
        d=toy()
        d["players"][0]["gold_t"][1]=999
        with self.assertRaisesRegex(AssertionError,"gold advantage"):
            check_single_game(d)

    def test_team_xp_mismatch_rejected(self):
        d=toy()
        d["radiant_xp_adv"][1]=10
        with self.assertRaisesRegex(AssertionError,"XP advantage"):
            check_single_game(d)

    def test_extra_postterminal_array_slot_is_flagged_not_hidden(self):
        d=toy()
        d["duration"]=100
        d2=check_single_game(d)
        self.assertEqual(d2["terminal_or_postterminal_array_slots"],1)

if __name__=="__main__":
    unittest.main()
