"""Command line interface.

    python -m pdm_sentinel simulate --out data/
    python -m pdm_sentinel analyze --data data/
    python -m pdm_sentinel analyze --data data/ --report report.html
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .machines import MACHINES
from .pipeline import load_csvs, analyze_plant
from .report import write_html
from .simulator import simulate_machine


def _cmd_simulate(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for machine_id in MACHINES:
        df = simulate_machine(
            machine_id,
            periods=args.periods,
            interval_s=args.interval,
            seed=args.seed,
            with_fault=not args.healthy,
        )
        path = out / f"{machine_id}.csv"
        df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df)} rows)")
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    data = load_csvs(args.data)
    report = analyze_plant(data)

    for m in report.machines:
        print(f"{m.spec.display_name:<22} health {m.health.score:5.1f}/100  [{m.health.grade}]")

    alerts = report.alerts
    print(f"\n{len(alerts)} active alert(s):")
    for a in alerts:
        print(f"  [{a.severity.upper():8}] {a.message}")

    if args.report:
        write_html(report, args.report)
        print(f"\nHTML report written to {args.report}")
    return 1 if args.fail_on_alerts and alerts else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pdm_sentinel", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate", help="generate synthetic sensor CSVs")
    sim.add_argument("--out", default="data")
    sim.add_argument("--periods", type=int, default=500)
    sim.add_argument("--interval", type=int, default=60, help="seconds between samples")
    sim.add_argument("--seed", type=int, default=42)
    sim.add_argument("--healthy", action="store_true", help="no injected faults")
    sim.set_defaults(func=_cmd_simulate)

    ana = sub.add_parser("analyze", help="analyze sensor CSVs in a directory")
    ana.add_argument("--data", default="data")
    ana.add_argument("--report", default=None, help="write an HTML dashboard to this path")
    ana.add_argument("--fail-on-alerts", action="store_true",
                     help="exit 1 when any warning/critical alert is active")
    ana.set_defaults(func=_cmd_analyze)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
