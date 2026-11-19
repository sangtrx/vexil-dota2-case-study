"""Strict checks that post-Fable scientific claims match existing evidence."""
import json
from pathlib import Path
import subprocess
import shutil
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
        self.assertIn("0, ±3k and ±6k gold lead",self.report)
        self.assertIn("Values outside observed TRAIN support are masked",self.report)
        self.assertNotIn("The +2k state appears in",self.report)

    def test_additive_null_forward_folds_and_patch_subfit_pinned(self):
        losses=[z["delta_logloss"] for z in self.null["folds"]]
        self.assertEqual(len(losses),4)
        self.assertEqual(sum(x<0 for x in losses),1)
        self.assertEqual(sum(x>0 for x in losses),3)
        for x in ("in only **1/4 folds**", "[−0.0148,+0.0090]",
                  "+0.000405 (worse)", "[−0.003059,+0.003857]"):
            self.assertIn(x, self.report)
        readout=(ROOT/"research/GOLD_INTERACTION_NULL_READOUT.md").read_text()
        self.assertIn("**NOT VERIFIED**", readout)
        self.assertIn("Only C1–C3", readout)
        self.assertIn("+0.300675", readout)
        self.assertIn("+0.029227", readout)
        self.assertNotIn("Patch sensitivity:", self.report)
        self.assertNotIn("The decisive scientific test", self.readme)
        self.assertNotIn("The key falsification", (ROOT/"SUBMISSION_PACKAGE_README.md").read_text())
        self.assertIn("Gold + time + interaction M1", self.readme)
        self.assertNotIn("\\n\\n", (ROOT/"docs/RESEARCH_DECISION_TRAIL.md").read_text())
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
        self.assertIn("not evidence of a within-game time effect",self.report)
        self.assertIn("docs/TRAIN_LEADER_STATE_EMPIRICAL.md",self.report)
        self.assertIn("docs/figures/train_interaction_vs_additive_null.png",self.report)
        self.assertNotIn("docs/figures/train_leader_state_empirical.png",self.report)
        self.assertNotIn("docs/figures/train_matched_state_aliasing.png",self.report)

    def test_report_figure_two_is_nonselecting_stronger_null_evidence(self):
        from research.render_interaction_null_figure import audited_values, OUTPUT
        folds, delta, ci, groups = audited_values()
        self.assertEqual(len(folds), 4)
        self.assertEqual(sum(f["eval_games"] for f in folds), 137)
        self.assertEqual(sum(f["delta_logloss"] < 0 for f in folds), 1)
        self.assertEqual(groups, 70)
        self.assertAlmostEqual(delta, -0.002020073983088214, places=12)
        self.assertAlmostEqual(ci[0], -0.01480135155766235, places=12)
        self.assertAlmostEqual(ci[1], 0.00898354827703724, places=12)
        self.assertLess(ci[0], 0)
        self.assertGreater(ci[1], 0)
        self.assertTrue(OUTPUT.is_file())
        self.assertGreater(OUTPUT.stat().st_size, 10000)
        script = (ROOT/"research/render_interaction_null_figure.py").read_text()
        self.assertNotIn("heldout_predictions", script)
        self.assertNotIn("validation_m0_m1_predictions", script)
        self.assertIn("docs/figures/train_interaction_vs_additive_null.png", self.report)
        self.assertIn("M1 improved log loss in only **1/4 folds**", self.report)

    def test_train_lead_groups_are_not_within_match_time_decay(self):
        import csv
        import gzip
        source = ROOT/"research/frozen_original_train_features.csv.gz"
        mid_by_minute = {10: set(), 30: set()}
        counts = {10: [0, 0], 30: [0, 0]}
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                minute = int(row["minute"])
                gold = float(row["gold_k"])
                if minute not in mid_by_minute or not 2 <= abs(gold) < 4:
                    continue
                mid_by_minute[minute].add(int(row["match_id"]))
                outcome = int(row["radiant_win"])
                leader_won = outcome if gold > 0 else (1 - outcome)
                counts[minute][0] += leader_won
                counts[minute][1] += 1
        self.assertEqual(counts, {10: [66, 82], 30: [11, 25]})
        self.assertEqual(len(mid_by_minute[10] & mid_by_minute[30]), 7)
        self.assertIn("Only **7 games** were in both groups", self.report)
        supplemental = (ROOT/"docs/TRAIN_LEADER_STATE_EMPIRICAL.md").read_text()
        self.assertIn("only 7 match IDs qualify", supplemental)
        self.assertIn("not evidence of a within-game time effect", self.report)

    def test_post_inspection_not_mislabeled_preregistered_blind(self):
        import json
        nb=json.loads((ROOT/"live_dota2_win_probability.ipynb").read_text())
        source="".join(nb["cells"][28]["source"])
        output="\n".join("".join(o.get("text",[]))
                         for o in nb["cells"][28]["outputs"] if o["output_type"]=="stream")
        for exact in ("TEST paired log-loss CI (corrected after inspection):",
                      "TEST paired Brier CI (corrected after inspection):"):
            self.assertIn(exact,source)
            self.assertIn(exact,output)
        self.assertNotIn("Pre-registered original TEST",source)
        self.assertNotIn("Pre-registered original TEST",output)
        self.assertIn("The corrected TEST is not a fresh blind holdout",self.report)
        note=(ROOT/"docs/TEAM_LEAGUE_DEPENDENCE.md").read_text()
        self.assertIn("not blind results",note)
        self.assertIn("terminal-boundary correction followed initial TEST inspection",note)

    def test_colab_preinstalled_stack_not_claimed_pinned(self):
        import hashlib
        receipt=json.loads((ROOT/"docs/COLAB_16CELL_RUN_RECEIPT.json").read_text())
        self.assertEqual(receipt["runtime"]["numpy"],"2.4.6")
        self.assertEqual(receipt["runtime"]["scikit_learn"],"1.6.1")
        self.assertEqual(receipt["repo_frozen_16cell_notebook_sha256"],
                         "466dce5d64adf081fb20642df210f903794745714675e225415c0aa8770f8304")
        self.assertNotEqual(receipt["repo_frozen_16cell_notebook_sha256"],
                            hashlib.sha256((ROOT/"live_dota2_win_probability.ipynb").read_bytes()).hexdigest())
        self.assertIn("Colab's preinstalled scientific libraries",self.readme)
        self.assertIn("new Colab CPU Run All on 19 November",self.report)
        self.assertIn("16/16 cells, zero errors",self.report)
        self.assertIn("docs/COLAB_EXACT_SHIPPED_NOTEBOOK_RECEIPT.json",self.report)
        self.assertFalse(receipt["cloud_csv_byte_equality_verified"])

    def test_phase_uncertainty_and_november_negative_not_hidden(self):
        s=self.forward["forward_scores"]["phase_descriptive"]["0-9"]
        self.assertAlmostEqual(s["brier_M0"],0.2442106731707893)
        self.assertAlmostEqual(s["brier_M1"],0.24392514896856357)
        self.assertAlmostEqual(s["ece_M0"],0.04959713082061086)
        self.assertAlmostEqual(s["ece_M1"],0.08115121989176531)
        for term in ("Six of the eight phase intervals favour M1",
                     "unadjusted and use the same games",
                     "both intervals contain zero","68 games overlap",
                     "about 0.00455 worse"):
            self.assertIn(term,self.report)
        self.assertIn("68 games overlap",self.report)
        self.assertIn("0.517823 vs 0.518090",self.report)
        self.assertIn("not a verified label-arrival margin",self.report)
        for anchor in ("0.612312 vs 0.612086", "0.211828 vs 0.212744", "+0.03139", "+0.00748", "[−0.02828,+0.00012]", "[−0.00670,−0.00038]", "0.5943", "headline TEST scores use the original 291-game TRAIN fit"):
            self.assertIn(anchor,self.report)

    @unittest.skipUnless(shutil.which("pdftotext") and shutil.which("pdfinfo"),
                         "Poppler pdfinfo/pdftotext unavailable; other science tests still run")
    def test_pdf_has_all_new_science_anchors_and_no_disclosure_rewrite(self):
        pdf=" ".join(subprocess.check_output(
            ["pdftotext","-layout",str(ROOT/"REPORT.pdf"),"-"],text=True).split())
        for term in ("19 November 2026","66/82","11/25","1/4 folds","+0.000405",
                     "0.5429","0.1074 (worse)","+0.03139","+0.00748",
                     "[−0.00670,−0.00038]","291-game TRAIN fit",
                     "XGBoost 3.4.1", "AI reviews are not independent human peer review"):
            self.assertIn(term,pdf)
        self.assertEqual(
            int(subprocess.check_output(["pdfinfo",str(ROOT/"REPORT.pdf")],text=True
            ).split("Pages:")[1].split()[0]),4)

if __name__ == "__main__":
    unittest.main()
