"""Strict checks that post-Fable scientific claims match existing evidence."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FableScienceRepairContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = (ROOT/"REPORT.md").read_text()
        cls.readme = (ROOT/"README.md").read_text()
        cls.forward = json.loads((ROOT/"docs/FORWARD_100_EVIDENCE.json").read_text())
        cls.null = json.loads((
            ROOT/"research/GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json"
        ).read_text())

    def test_exact_gold_support_semantics_not_fabricated_neighborhood(self):
        import json
        nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        source="".join(nb["cells"][20]["source"])
        self.assertIn("gold_k >= 2",source)
        self.assertIn("include **all Radiant leads ≥2k**",self.report)
        self.assertIn("not* observations near exactly +2k",self.report)
        self.assertNotIn("The +2k state appears in",self.report)

    def test_additive_null_forward_folds_and_patch_subfit_pinned(self):
        losses=[z["delta_logloss"] for z in self.null["folds"]]
        self.assertEqual(len(losses),4)
        self.assertEqual(sum(x<0 for x in losses),1)
        self.assertEqual(sum(x>0 for x in losses),3)
        for x in ("won only **1/4**","[−0.0148,+0.0090]","250 patch-59",
                  "41 patch-60","+0.301","+0.029"):
            self.assertIn(x,self.report)
        by_patch=self.null["patch_and_cluster_influence"]["patch_subfit"]
        self.assertEqual([by_patch[k]["games"] for k in ("59","60")],[250,41])
        self.assertAlmostEqual(by_patch["59"]["fit_D"],0.3006750974392104,12)
        self.assertAlmostEqual(by_patch["60"]["fit_D"],0.029226674475972825,12)
        self.assertFalse(self.null["model_promotion_permitted"])

    def test_empirical_story_uses_only_train_counters(self):
        c=json.loads((
            ROOT/"docs/TRAIN_LEADER_STATE_EMPIRICAL_RECEIPT.json"
        ).read_text())
        records={(int(z["abs_lead_lower_k"]),z["minute"]):z for z in c["cells"]}
        self.assertEqual((records[(2,10)]["eventual_leader_wins"],
                          records[(2,10)]["games"]),(66,82))
        self.assertEqual((records[(2,30)]["eventual_leader_wins"],
                          records[(2,30)]["games"]),(11,25))
        self.assertTrue(c["not_a_model_selection_gate"])
        self.assertTrue(c["not_causal"])
        self.assertIn("not a causal time effect",self.report)
        self.assertIn("docs/figures/train_leader_state_empirical.png",self.report)
        self.assertNotIn("docs/figures/train_matched_state_aliasing.png",self.report)

    def test_post_inspection_not_mislabeled_preregistered_blind(self):
        import json
        nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        self.assertIn("Pre-registered original TEST",
                      "".join(nb["cells"][28]["source"]))
        self.assertIn("not to the corrected post-inspection TEST values",self.report)
        self.assertIn("not preregistered blind results",
                      (ROOT/"docs/TEAM_LEAGUE_DEPENDENCE.md").read_text())
        self.assertIn("after the original TEST was opened",self.report)

    def test_colab_preinstalled_stack_not_claimed_pinned(self):
        receipt=json.loads((ROOT/"docs/COLAB_16CELL_RUN_RECEIPT.json").read_text())
        self.assertEqual(receipt["runtime"]["numpy"],"2.4.6")
        self.assertEqual(receipt["runtime"]["scikit_learn"],"1.6.1")
        self.assertIn("NumPy 2.4.6 / scikit-learn 1.6.1",self.report)
        self.assertIn("NumPy 2.2.6 / scikit-learn 1.7.2",self.report)
        self.assertIn("Colab\u0027s already loaded scientific libraries",self.readme)
        self.assertFalse(receipt["cloud_csv_byte_equality_verified"])

    def test_phase_uncertainty_and_november_negative_not_hidden(self):
        s=self.forward["forward_scores"]["phase_descriptive"]["0-9"]
        self.assertAlmostEqual(s["brier_M0"],0.2442106731707893)
        self.assertAlmostEqual(s["brier_M1"],0.24392514896856357)
        self.assertAlmostEqual(s["ece_M0"],0.04959713082061086)
        self.assertAlmostEqual(s["ece_M1"],0.08115121989176531)
        for term in ("eight phase × metric comparisons are unadjusted",
                     "0.24421→0.24393","0.0496→0.0812",
                     "not independent confirmation",
                     "about 0.00455 worse"):
            self.assertIn(term,self.report)

    def test_pdf_has_all_new_science_anchors_and_no_disclosure_rewrite(self):
        pdf=" ".join(subprocess.check_output(
            ["pdftotext","-layout",str(ROOT/"REPORT.pdf"),"-"],text=True
        ).split())
        for term in ("66/82","11/25","1/4","250 patch-59",
                     "41 patch-60","0.24421→0.24393","Colab retained",
                     "No third-party Dota predictor was copied"):
            self.assertIn(term,pdf)
        self.assertEqual(
            int(subprocess.check_output(
                ["pdfinfo",str(ROOT/"REPORT.pdf")],text=True
            ).split("Pages:")[1].split()[0]),4
        )


if __name__ == "__main__":
    unittest.main()
