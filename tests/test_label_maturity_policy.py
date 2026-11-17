"""Edge cases and failure-closed behavior for outcome availability."""
import unittest

from research.label_maturity_policy import outcome_known_by


class OutcomeAvailabilityTest(unittest.TestCase):
    def test_live_missing_received_at_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "received_at required"):
            outcome_known_by(start_time=100, duration=60, fit_time=500)

    def test_completion_proxy_only_if_explicit(self):
        self.assertFalse(outcome_known_by(start_time=100, duration=61,
                                          fit_time=160, require_received_at=False))
        self.assertTrue(outcome_known_by(start_time=100, duration=60,
                                         fit_time=160, require_received_at=False))

    def test_late_received_at_blocks_completed_game(self):
        self.assertFalse(outcome_known_by(start_time=100, duration=60,
                                          fit_time=170, received_at=180))
        self.assertTrue(outcome_known_by(start_time=100, duration=60,
                                         fit_time=180, received_at=180))

    def test_early_received_at_never_precedes_game_completion(self):
        self.assertFalse(outcome_known_by(start_time=100, duration=60,
                                          fit_time=150, received_at=130))

    def test_lag_is_explicit_and_conservative(self):
        self.assertFalse(outcome_known_by(start_time=100, duration=60,
                                          fit_time=179, received_at=175,
                                          availability_lag_seconds=5))
        self.assertTrue(outcome_known_by(start_time=100, duration=60,
                                         fit_time=180, received_at=175,
                                         availability_lag_seconds=5))

    def test_invalid_timestamps_fail_closed(self):
        inputs = (
            {"duration": 0}, {"duration": -1}, {"start_time": -1},
            {"fit_time": -1}, {"availability_lag_seconds": -1},
            {"received_at": 90}, {"received_at": 101.5},
            {"fit_time": 170.2}, {"duration": True},
        )
        for patch in inputs:
            with self.subTest(patch=patch):
                kw = dict(start_time=100, duration=60, fit_time=180,
                          received_at=180)
                kw.update(patch)
                with self.assertRaises((TypeError, ValueError)):
                    outcome_known_by(**kw)


if __name__ == "__main__":
    unittest.main()
