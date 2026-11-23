"""Synthetic sensor data generator.

Produces realistic multivariate time series for each machine, with optional
named fault scenarios injected part-way through the run. The generator is
deterministic for a given seed so tests and demos are reproducible.

This data stands in for real sensor feeds while developing or evaluating the
engine; swap it for real CSVs with the same column layout.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .machines import MACHINES, MachineSpec

# Fault scenarios: machine_id -> (fault_name, description)
FAULT_SCENARIOS: dict[str, tuple[str, str]] = {
    "ac_motor": ("phase_loss", "phase R current collapses toward zero"),
    "dc_motor": ("bearing_wear", "vibration ramps up steadily"),
    "belt": ("belt_slip", "speed and tension drop below normal"),
    "pump": ("cavitation", "pressure oscillates with growing amplitude"),
}

_BASELINES: dict[str, dict[str, float]] = {
    "ac_motor": {
        "temperature": 55.0, "vibration": 2.2,
        "current_r": 12.0, "current_s": 12.0, "current_t": 12.0,
        "voltage_r": 400.0, "voltage_s": 400.0, "voltage_t": 400.0,
    },
    "dc_motor": {"voltage": 230.0, "current": 4.0, "vibration": 1.8},
    "belt": {"tension": 500.0, "alignment": 1.0, "speed": 3.0},
    "pump": {"pressure": 4.0, "flow": 50.0, "temperature": 35.0},
}


def _baseline_frame(spec: MachineSpec, periods: int, rng: np.random.Generator) -> pd.DataFrame:
    cols: dict[str, np.ndarray] = {}
    bases = _BASELINES[spec.machine_id]
    for sensor in spec.sensors:
        center = bases[sensor.name]
        noise = 0.03 * (sensor.normal_max - sensor.normal_min)
        drift = rng.uniform(-0.02, 0.02) * (sensor.normal_max - sensor.normal_min)
        trend = np.linspace(0.0, drift, periods)
        cols[sensor.name] = center + trend + rng.normal(0.0, noise, periods)
    return pd.DataFrame(cols)


def _inject_fault(df: pd.DataFrame, machine_id: str, fault_start: int, rng: np.random.Generator) -> None:
    """Mutate df in place so the fault develops from fault_start onward."""
    n = len(df)
    ramp = np.linspace(0.0, 1.0, n - fault_start)

    if machine_id == "ac_motor":  # phase loss
        df.loc[fault_start:, "current_r"] = 12.0 * (1.0 - 0.97 * ramp)
        df.loc[fault_start:, "temperature"] = df.loc[fault_start:, "temperature"] + 18.0 * ramp
    elif machine_id == "dc_motor":  # bearing wear
        df.loc[fault_start:, "vibration"] = 1.8 + 6.5 * ramp
        df.loc[fault_start:, "current"] = df.loc[fault_start:, "current"] + 1.5 * ramp
    elif machine_id == "belt":  # belt slip
        df.loc[fault_start:, "speed"] = 3.0 - 1.4 * ramp + rng.normal(0.0, 0.05, n - fault_start)
        df.loc[fault_start:, "tension"] = 500.0 - 220.0 * ramp
    elif machine_id == "pump":  # cavitation
        osc = np.sin(np.linspace(0.0, 6.0 * np.pi, n - fault_start)) * (0.3 + 2.6 * ramp)
        df.loc[fault_start:, "pressure"] = 4.0 + osc


def simulate_machine(
    machine_id: str,
    periods: int = 500,
    interval_s: int = 60,
    seed: int = 42,
    with_fault: bool = True,
    fault_fraction: float = 0.6,
    start: str = "2026-01-01",
) -> pd.DataFrame:
    """Simulate one machine. Returns a DataFrame with a timestamp column."""
    if machine_id not in MACHINES:
        raise KeyError(f"unknown machine {machine_id!r}")
    rng = np.random.default_rng(seed + hash(machine_id) % 1000)
    spec = MACHINES[machine_id]

    df = _baseline_frame(spec, periods, rng)
    if with_fault:
        _inject_fault(df, machine_id, int(periods * fault_fraction), rng)

    ts = pd.date_range(start=start, periods=periods, freq=f"{interval_s}s")
    df.insert(0, "timestamp", ts)
    return df.round(4)


def simulate_plant(
    periods: int = 500, interval_s: int = 60, seed: int = 42, with_faults: bool = True
) -> dict[str, pd.DataFrame]:
    """Simulate every registered machine. Returns machine_id -> DataFrame."""
    return {
        mid: simulate_machine(mid, periods, interval_s, seed, with_faults)
        for mid in MACHINES
}
