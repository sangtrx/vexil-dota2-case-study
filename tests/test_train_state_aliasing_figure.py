"""Freeze the TRAIN-only state-aliasing illustration and its evidence scope."""
import unittest
from pathlib import Path

import numpy as np

from research.render_train_state_aliasing_figure import (
    evidence, render, MATCH_A, MATCH_B
)


class TrainStateAliasingFigureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train, cls.rows, cls.probs = evidence()

    def test_both_cases_are_training_only(self):
        self.assertEqual(list(self.rows.match_id), [MATCH_A, MATCH_B])
        self.assertTrue((self.rows.partition == "train").all())
        self.assertTrue((self.rows.patch == 59).all())
        self.assertEqual(self.train.match_id.nunique(), 291)

    def test_similar_economy_has_different_objective_state(self):
        a, b = self.rows.iloc[0], self.rows.iloc[1]
        self.assertEqual(round(abs(a.gold_k - b.gold_k) * 1000), 28)
        self.assertEqual(round(abs(a.xp_k - b.xp_k) * 1000), 102)
        self.assertEqual((int(a.tower_delta), int(b.tower_delta)), (0, -1))
        self.assertEqual((int(a.roshan_delta), int(b.roshan_delta)), (2, -1))

    def test_original_train_model_pins_predictions(self):
        np.testing.assert_allclose(self.probs, [0.603123, 0.604641],
                                   rtol=0, atol=0.00003)
        self.assertEqual(list(self.rows.radiant_win), [1, 1])

    def test_rendered_training_figure_exists(self):
        path = Path(__file__).resolve().parents[1] / "docs/figures/train_matched_state_aliasing.png"
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 25000)


if __name__ == "__main__":
    unittest.main()
