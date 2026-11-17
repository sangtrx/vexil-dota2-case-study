import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from all_family_models import INPUTS,CANDIDATES,BASE,OTHER
from all_family_features import FAMILY,COLS
from quant_path_signature_models import verify_original_artifacts


class FiveCandidateContract(unittest.TestCase):
    def test_precommitted_family_count(self):
        self.assertEqual(CANDIDATES,("R","O","C","I","ALL"))
        self.assertEqual(len(INPUTS["ALL"]),12)
        self.assertEqual(sum(map(len,FAMILY.values())),9)

    def test_controls_are_original(self):
        self.assertEqual(INPUTS["M1_interaction"],["gold_k","minute10","gold_x_time"])
        self.assertEqual(len(INPUTS[OTHER]),5)

    def test_family_sets_are_predeclared(self):
        for k in FAMILY:
            self.assertEqual(INPUTS[k],INPUTS[BASE]+list(FAMILY[k]))
        self.assertEqual(INPUTS["ALL"],INPUTS[BASE]+list(COLS))

    def test_original_application_artifacts_locked(self):
        got=verify_original_artifacts()
        self.assertEqual(len(got),3)


if __name__=="__main__":
    unittest.main()
