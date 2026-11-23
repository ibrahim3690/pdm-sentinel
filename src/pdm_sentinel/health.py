"""Per-machine health scoring.

Score starts at 100 and loses points for active findings and for trends that
move a sensor toward its band edge. 100-85 Good, 84-70 Watch, 69-40 Warning,
below 40 Critical.
"""
from __future__ import annotations

from dataclasses import dataclass

from .detectors import Finding, trend_slopes
from .machines import MachineSpec

import pandas as pd

_PENALTY = {"critical": 30.0, "warning": 12.0, "info": 4.0}
_MAX_PER_SENSOR = 45.0


@dataclass(frozen=True)
class Health:
    machine_id: str
    score: float
    grade: str


def grade_for(score: float) -> str:
    if score >= 85:
        return "Good"
    if score >= 70:
        return "Watch"
    if score >= 40:
        return "Warning"
    return "Critical"


def _trend_penalty(df: pd.DataFrame, spec: MachineSpec) -> float:
    """Penalize sensors whose recent slope heads out of the normal band."""
    slopes = trend_slopes(df, spec)
    penalty = 0.0
    for sensor in spec.sensors:
        slope = slopes.get(sensor.name, 0.0)
        last = float(df[sensor.name].iloc[-1])
        span = sensor.normal_max - sensor.normal_min
        if span <= 0:
            continue
        # moving toward the nearer edge at >1% of the band per sample is bad
        heading_up = slope > 0 and last > (sensor.normal_max + sensor.normal_min) / 2
        heading_down = slope < 0 and last < (sensor.normal_max + sensor.normal_min) / 2
        if (heading_up or heading_down) and abs(slope) > 0.01 * span:
            penalty += min(10.0, abs(slope) / span * 100.0)
    return penalty


def score_machine(df: pd.DataFrame, spec: MachineSpec, findings: list[Finding]) -> Health:
    """Combine findings and trends into a 0-100 health score."""
    per_sensor: dict[str, float] = {}
    for f in findings:
        if f.machine_id != spec.machine_id:
            continue
        per_sensor[f.sensor] = min(
            _MAX_PER_SENSOR, per_sensor.get(f.sensor, 0.0) + _PENALTY[f.severity]
        )
    score = 100.0 - sum(per_sensor.values()) - _trend_penalty(df, spec)
    score = max(0.0, min(100.0, score))
    return Health(machine_id=spec.machine_id, score=round(score, 1), grade=grade_for(score))
