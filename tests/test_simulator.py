import unittest

import pandas as pd

from pdm_sentinel.machines import MACHINES
from pdm_sentinel.simulator import simulate_machine, simulate_plant


class SimulatorTests(unittest.TestCase):
    def test_columns_match_spec(self):
        df = simulate_machine("ac_motor", periods=120, seed=1)
        expected = {"timestamp"} | {s.name for s in MACHINES["ac_motor"].sensors}
        self.assertEqual(set(df.columns), expected)
        self.assertEqual(len(df), 120)

    def test_deterministic(self):
        a = simulate_machine("pump", periods=100, seed=7)
        b = simulate_machine("pump", periods=100, seed=7)
        pd.testing.assert_frame_equal(a, b)

    def test_healthy_data_stays_in_normal_band(self):
        for machine_id in MACHINES:
            df = simulate_machine(machine_id, periods=200, seed=3, with_fault=False)
            for s in MACHINES[machine_id].sensors:
                self.assertTrue(
                    df[s.name].between(s.warn_low, s.warn_high).all(),
                    f"{machine_id}.{s.name} escaped warn band without a fault",
                )

    def test_phase_loss_fault_injected(self):
        df = simulate_machine("ac_motor", periods=200, seed=5, with_fault=True)
        self.assertLess(df["current_r"].iloc[-1], 2.0)

    def test_all_machines_simulate(self):
        plant = simulate_plant(periods=50, seed=9)
        self.assertEqual(set(plant), set(MACHINES))


if __name__ == "__main__":
    unittest.main()
