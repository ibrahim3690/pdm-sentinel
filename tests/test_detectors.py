import unittest

from pdm_sentinel.detectors import check_thresholds, detect_all
from pdm_sentinel.machines import MACHINES
from pdm_sentinel.simulator import simulate_machine


class DetectorTests(unittest.TestCase):
    def test_clean_data_produces_no_threshold_findings(self):
        df = simulate_machine("belt", periods=300, seed=11, with_fault=False)
        findings = check_thresholds(df, MACHINES["belt"])
        self.assertEqual(findings, [])

    def test_phase_loss_is_flagged_critical(self):
        df = simulate_machine("ac_motor", periods=400, seed=13, with_fault=True)
        findings = detect_all(df, MACHINES["ac_motor"])
        crit = [f for f in findings if f.sensor == "current_r" and f.severity == "critical"]
        self.assertTrue(crit, "phase loss should raise a critical current_r finding")
        self.assertIn("AC Motor", crit[0].message)

    def test_finding_names_device_sensor_and_value(self):
        df = simulate_machine("dc_motor", periods=400, seed=17, with_fault=True)
        findings = detect_all(df, MACHINES["dc_motor"])
        vib = [f for f in findings if f.sensor == "vibration"]
        self.assertTrue(vib, "bearing wear should flag vibration")
        self.assertEqual(vib[0].machine_id, "dc_motor")
        self.assertGreater(vib[0].value, 0)
        self.assertTrue(vib[0].unit)

    def test_dedup_keeps_one_finding_per_sensor_kind(self):
        df = simulate_machine("pump", periods=400, seed=19, with_fault=True)
        findings = detect_all(df, MACHINES["pump"])
        keys = [(f.sensor, f.kind) for f in findings]
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
