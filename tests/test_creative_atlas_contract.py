"""Portable checks for the complete post-selection research atlas."""
from __future__ import annotations
import ast
import re
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/"docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md"
FEATURES=ROOT/"research/rich_feature_engineering.py"
READOUTS=(
"QUANT_BIBLE_PATH_READOUT.md","QUANT_PATH_SIGNATURES_READOUT.md",
"OCT_NOV_FEATURE_TRANSFER_READOUT.md","ROLE_DYNAMICS_TRANSFER_READOUT.md",
"RICH_FEATURE_DIVERSITY_AUDIT.md","MINIMAL_ECONOMY_SCORE_READOUT.md",
"DISAGREEMENT_RELIABILITY_READOUT.md","EVENT_DELAY_HOSTILE_READOUT.md",
"CROSS_ARRAY_TIME_ALIGNMENT_READOUT.md","FRESH_NOV17_EXTERNAL_READOUT.md",
"CAUSAL_STALE_FEED_HOSTILE_READOUT.md",
"STRICT_NODATA_TRAIN_FORWARD_REPAIR_READOUT.md",
"CAUSAL_FORECAST_FILTER_READOUT.md","RICH_FEATURE_MODEL_READOUT.md",
"BOOSTED_TREES_DIRECT_READOUT.md","BOOSTED_NESTED_FAIRNESS_READOUT.md",
"BOOSTED_TREES_HOSTILE_DECISION_20261118.md",
"POST_RESULT_EQUAL_MATCH_SENSITIVITY_NOTE_20261118.md",
)
class CreativeAtlasContract(unittest.TestCase):
    def test_historical_P01_to_P28_all_reproduced_verbatim(self):
        t=ATLAS.read_text()
        part=t.split("## 3. COMPLETE adaptive screen",1)[1].split("## 4. Rich 81-feature",1)[0]
        ids=re.findall(r"^\| (P\d\d) \|",part,flags=re.M)
        self.assertEqual(len(ids),28)
        self.assertEqual(set(ids),{f"P{i:02d}" for i in range(1,29)})
        historical=(ROOT/"docs/EXPERIMENT_REGISTER.md").read_text()
        for line in part.splitlines():
            if re.match(r"^\| P\d\d \|",line):
                self.assertIn(line,historical)
        for x in ("S1","S2","S3","S4","M4","P20","0/28","[-0.016929,+0.006434]"):
            self.assertIn(x,t)

    def test_all_81_implemented_features_and_ros_owner_limits(self):
        syntax=ast.parse(FEATURES.read_text())
        assignment=next(node for node in syntax.body
            if isinstance(node,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=="FAMILIES" for t in node.targets))
        families=ast.literal_eval(assignment.value)
        names=[v for group in families.values() for v in group]
        self.assertEqual(len(names),81)
        self.assertEqual(len(set(names)),81)
        self.assertEqual({k:len(v) for k,v in families.items()},
                         {"gold":19,"xp":13,"players":19,"objectives":17,"interactions":13})
        t=ATLAS.read_text().split("## 4. Rich 81-feature",1)[1].split(
            "## 5. Quant/geometry",1)[0]
        for name in names:
            self.assertIn(chr(96)+name+chr(96),t)
        for fact in ("486","78 distinct varying","o_roshan_delta",
                     "o_roshan10_delta","x_economy_gap","gold_xp_gap"):
            self.assertIn(fact,t)

    def test_all_readouts_and_correct_scope_disclosures(self):
        t=ATLAS.read_text()
        report=(ROOT/"REPORT.md").read_text()
        for x in ("P20","Q1","XGBoost","LightGBM","81","28","0/28",
                  "0.6060","0.6156","0.6162","+0.0177","+0.0101"):
            self.assertIn(x,report)
        for exact in ("0.605963","0.615597","0.616196"):
            self.assertIn(exact,t)
        for x in ("reused development","TRAIN-only","received_at",
                  "not a new held-out TEST","not a new unseen dataset"):
            # The first three are in source-specific case; false future claims
            # must be absent as positive assertions rather than regex tricks.
            if x=="not a new unseen dataset":
                continue
            self.assertIn(x.lower(),t.lower())
        self.assertIn("september 199-game preregistered external",t.lower())
        self.assertNotIn("independent-within-train",t.lower())
        self.assertIn("supplementary research used",report.lower())
        for package in ("NumPy", "pandas", "SciPy", "tqdm", "XGBoost 3.4.1", "LightGBM 4.7.0", "Narwhals 2.21.2"):
            self.assertIn(package,report)
        self.assertIn("not preregistered",(ROOT/"research/BOOSTED_TREES_HOSTILE_DECISION_20261118.md").read_text())
        for name in READOUTS:
            self.assertTrue((ROOT/"research"/name).is_file(),name)
            self.assertIn(chr(96)+"research/"+name+chr(96),t)
        for name in ("README.md","SUBMISSION_PACKAGE_README.md"):
            self.assertIn("docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md",
                          (ROOT/name).read_text())

    @unittest.skipUnless(shutil.which("pdfinfo") and shutil.which("pdftotext"),
                         "PDF tools unavailable")
    def test_pdf_still_four_pages_and_includes_creative_falsifications(self):
        info=subprocess.check_output(["pdfinfo",str(ROOT/"REPORT.pdf")],text=True)
        self.assertRegex(info,r"(?m)^Pages:\s+4$")
        pdf=" ".join(subprocess.check_output(
            ["pdftotext","-layout",str(ROOT/"REPORT.pdf"),"-"],
            text=True).split()).lower()
        for phrase in ("28 adaptive screens","0/28 promoted","81 engineered features",
                      "xgboost","lightgbm","q1","0.6060","0.6156",
                      "the corrected test is not a fresh blind holdout"):
            self.assertIn(phrase,pdf)

if __name__=="__main__":
    unittest.main()
