import unittest

from pdm_sentinel.health import grade_for, score_machine
from pdm_sentinel.machines import MACHINES
from pdm_sentinel.detectors import detect_all
from pdm_sentinel.simulator import simulate_machine


class HealthTests(unittest.TestCase):
    def test_grades(self):
        self.assertEqual(grade_for(95), "Good")
        self.assertEqual(grade_for(80), "Watch")
        self.assertEqual(grade_for(55), "Warning")
        self.assertEqual(grade_for(20), "Critical")

    def test_healthy_machine_scores_high(self):
        df = simulate_machine("pump", periods=300, seed=23, with_fault=False)
        findings = detect_all(df, MACHINES["pump"])
        health = score_machine(df, MACHINES["pump"], findings)
        self.assertGreaterEqual(health.score, 85.0)

    def test_faulty_machine_scores_lower(self):
        df = simulate_machine("ac_motor", periods=400, seed=29, with_fault=True)
        findings = detect_all(df, MACHINES["ac_motor"])
        health = score_machine(df, MACHINES["ac_motor"], findings)
        self.assertLess(health.score, 70.0)

    def test_score_bounds(self):
        df = simulate_machine("belt", periods=400, seed=31, with_fault=True)
        findings = detect_all(df, MACHINES["belt"])
        health = score_machine(df, MACHINES["belt"], findings)
        self.assertGreaterEqual(health.score, 0.0)
        self.assertLessEqual(health.score, 100.0)


if __name__ == "__main__":
    unittest.main()
