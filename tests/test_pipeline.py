import tempfile
import unittest
from pathlib import Path

from pdm_sentinel.pipeline import analyze_plant, load_csvs, run_directory
from pdm_sentinel.report import render_html
from pdm_sentinel.simulator import simulate_plant
from pdm_sentinel.cli import main


class PipelineTests(unittest.TestCase):
    def test_end_to_end(self):
        data = simulate_plant(periods=400, seed=37)
        report = analyze_plant(data)
        self.assertEqual(len(report.machines), 4)
        self.assertTrue(report.alerts, "fault scenarios should produce alerts")
        for m in report.machines:
            self.assertTrue(m.spec.display_name)
            self.assertEqual(set(m.latest), {s.name for s in m.spec.sensors})

    def test_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mid, df in simulate_plant(periods=120, seed=41).items():
                df.to_csv(Path(tmp) / f"{mid}.csv", index=False)
            loaded = load_csvs(tmp)
            self.assertEqual(set(loaded), {"ac_motor", "dc_motor", "belt", "pump"})
            report = run_directory(tmp)
            self.assertEqual(len(report.machines), 4)

    def test_html_report_mentions_machines_and_alerts(self):
        report = analyze_plant(simulate_plant(periods=300, seed=43))
        html = render_html(report)
        for name in ("AC Motor", "DC Motor", "Drive Belt", "Coolant Pump"):
            self.assertIn(name, html)
        self.assertIn("Alerts", html)

    def test_cli_simulate_then_analyze(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = str(Path(tmp) / "data")
            self.assertEqual(main(["simulate", "--out", data_dir, "--periods", "150"]), 0)
            html_path = str(Path(tmp) / "report.html")
            rc = main(["analyze", "--data", data_dir, "--report", html_path])
            self.assertEqual(rc, 0)
            self.assertTrue(Path(html_path).exists())


if __name__ == "__main__":
    unittest.main()
