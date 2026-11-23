"""End-to-end pipeline: load sensor CSVs, detect anomalies, score health."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .detectors import Finding, detect_all
from .health import Health, score_machine
from .machines import MACHINES, MachineSpec


@dataclass
class MachineResult:
    spec: MachineSpec
    health: Health
    findings: list[Finding]
    latest: dict[str, float]   # sensor -> most recent reading


@dataclass
class PlantReport:
    machines: list[MachineResult]

    @property
    def findings(self) -> list[Finding]:
        return [f for m in self.machines for f in m.findings]

    @property
    def alerts(self) -> list[Finding]:
        """Findings worth paging a human about."""
        return [f for f in self.findings if f.severity in ("warning", "critical")]


def analyze_frame(df: pd.DataFrame, spec: MachineSpec) -> MachineResult:
    findings = detect_all(df, spec)
    health = score_machine(df, spec, findings)
    latest = {s.name: round(float(df[s.name].iloc[-1]), 3) for s in spec.sensors}
    return MachineResult(spec=spec, health=health, findings=findings, latest=latest)


def analyze_plant(data: dict[str, pd.DataFrame]) -> PlantReport:
    """Analyze machine_id -> DataFrame for every known machine id present."""
    results = []
    for machine_id, df in data.items():
        if machine_id not in MACHINES:
            raise KeyError(f"unknown machine {machine_id!r}")
        results.append(analyze_frame(df, MACHINES[machine_id]))
    return PlantReport(machines=results)


def load_csvs(data_dir: str | Path, pattern: str = "{machine_id}.csv") -> dict[str, pd.DataFrame]:
    """Load one CSV per machine from a directory, parsing the timestamp column."""
    data_dir = Path(data_dir)
    data: dict[str, pd.DataFrame] = {}
    for path in sorted(data_dir.glob("*.csv")):
        machine_id = path.stem
        df = pd.read_csv(path, parse_dates=["timestamp"])
        data[machine_id] = df
    if not data:
        raise FileNotFoundError(f"no CSV files in {data_dir}")
    return data


def run_directory(data_dir: str | Path) -> PlantReport:
    return analyze_plant(load_csvs(data_dir))
