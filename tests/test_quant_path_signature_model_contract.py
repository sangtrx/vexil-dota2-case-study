from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from quant_path_signature_features import FIELDS,WINDOW
from quant_path_signature_models import INPUTS,C,MODELS,M1,Q1,A,M0,TARGET_ARTIFACTS,verify_original_artifacts


class ModelContract(unittest.TestCase):
    def test_one_candidate_exact_features(self):
        self.assertEqual(WINDOW,10)
        self.assertEqual(len(FIELDS),4)
        self.assertEqual(len(set(FIELDS)),4)
        self.assertEqual(INPUTS[C],MODELS[M1]+list(FIELDS))
        self.assertEqual(len(INPUTS[C]),7)

    def test_controls_not_mutated(self):
        self.assertEqual(INPUTS[M0],MODELS[M0])
        self.assertEqual(INPUTS[A],MODELS[A])
        self.assertEqual(INPUTS[M1],MODELS[M1])
        self.assertEqual(INPUTS[Q1],MODELS[Q1])

    def test_submit_hash_immutability(self):
        self.assertEqual(verify_original_artifacts(),TARGET_ARTIFACTS)

if __name__=="__main__":
    unittest.main()
