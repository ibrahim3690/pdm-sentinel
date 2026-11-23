"""Anomaly detection: threshold rules, statistical outliers, drift, and trend."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .machines import MachineSpec

SEVERITIES = ("info", "warning", "critical")


@dataclass(frozen=True)
class Finding:
    machine_id: str
    sensor: str
    kind: str          # threshold | outlier | drift | trend
    severity: str      # info | warning | critical
    value: float
    unit: str
    message: str
    timestamp: str


def _severity_for(value: float, spec) -> str | None:
    """Classify one value against its sensor bands."""
    if value < spec.crit_low or value > spec.crit_high:
        return "critical"
    if value < spec.warn_low or value > spec.warn_high:
        return "warning"
    return None


def check_thresholds(df: pd.DataFrame, spec: MachineSpec) -> list[Finding]:
    """Flag the worst excursion per sensor against its fixed bands."""
    findings: list[Finding] = []
    for sensor in spec.sensors:
        series = df[sensor.name]
        # worst excursion = value furthest outside its normal band
        dist = np.maximum.reduce(
            [np.zeros(len(series)), series - sensor.normal_max, sensor.normal_min - series]
        )
        if dist.max() <= 0:
            continue
        idx = int(dist.argmax())
        value = float(series.iloc[idx])
        sev = _severity_for(value, sensor)
        if sev is None:
            continue
        side = "HIGH" if value > sensor.normal_max else "LOW"
        ts = str(df["timestamp"].iloc[idx]) if "timestamp" in df else ""
        findings.append(
            Finding(
                machine_id=spec.machine_id,
                sensor=sensor.name,
                kind="threshold",
                severity=sev,
                value=round(value, 3),
                unit=sensor.unit,
                message=f"{spec.display_name} {sensor.name} is {side}: "
                        f"{value:.2f} {sensor.unit} (normal {sensor.normal_min}-"
                        f"{sensor.normal_max} {sensor.unit})",
                timestamp=ts,
            )
        )
    return findings


def check_outliers(df: pd.DataFrame, spec: MachineSpec, z: float = 4.0,
                   baseline_frac: float = 0.3) -> list[Finding]:
    """Z-score outliers against the early (healthy) baseline window."""
    findings: list[Finding] = []
    base_n = max(10, int(len(df) * baseline_frac))
    for sensor in spec.sensors:
        series = df[sensor.name].to_numpy(dtype=float)
        base = series[:base_n]
        mu, sigma = base.mean(), base.std()
        if sigma < 1e-9:
            continue
        zscores = np.abs(series[base_n:] - mu) / sigma
        if len(zscores) == 0 or zscores.max() < z:
            continue
        idx = int(zscores.argmax()) + base_n
        value = float(series[idx])
        ts = str(df["timestamp"].iloc[idx]) if "timestamp" in df else ""
        findings.append(
            Finding(
                machine_id=spec.machine_id,
                sensor=sensor.name,
                kind="outlier",
                severity="warning",
                value=round(value, 3),
                unit=sensor.unit,
                message=f"{spec.display_name} {sensor.name} deviates "
                        f"{zscores.max():.1f} sigma from its baseline",
                timestamp=ts,
            )
        )
    return findings


def check_drift(df: pd.DataFrame, spec: MachineSpec, window: int = 30) -> list[Finding]:
    """EWMA drift: smoothed value leaves the normal band and stays out."""
    findings: list[Finding] = []
    for sensor in spec.sensors:
        ewma = df[sensor.name].ewm(span=window).mean()
        out_high = ewma > sensor.normal_max
        out_low = ewma < sensor.normal_min
        if not (out_high.any() or out_low.any()):
            continue
        if out_high.any():
            idx = int(np.argmax(out_high.to_numpy()))
            value = float(ewma.iloc[-1])
            side = "above"
        else:
            idx = int(np.argmax(out_low.to_numpy()))
            value = float(ewma.iloc[-1])
            side = "below"
        ts = str(df["timestamp"].iloc[idx]) if "timestamp" in df else ""
        findings.append(
            Finding(
                machine_id=spec.machine_id,
                sensor=sensor.name,
                kind="drift",
                severity="warning",
                value=round(value, 3),
                unit=sensor.unit,
                message=f"{spec.display_name} {sensor.name} is drifting {side} "
                        f"its normal band (smoothed {value:.2f} {sensor.unit})",
                timestamp=ts,
            )
        )
    return findings


def trend_slopes(df: pd.DataFrame, spec: MachineSpec, tail: int = 120) -> dict[str, float]:
    """Linear slope of the recent tail per sensor, in units per sample.

    Positive/negative sign matters relative to which side of the band is
    nearer, so health scoring interprets magnitude and direction together.
    """
    slopes: dict[str, float] = {}
    for sensor in spec.sensors:
        y = df[sensor.name].tail(tail).to_numpy(dtype=float)
        if len(y) < 5:
            slopes[sensor.name] = 0.0
            continue
        slopes[sensor.name] = float(np.polyfit(np.arange(len(y)), y, 1)[0])
    return slopes


def detect_all(df: pd.DataFrame, spec: MachineSpec) -> list[Finding]:
    """Run every detector and merge, worst-first, deduplicated by (sensor, kind)."""
    seen: set[tuple[str, str]] = set()
    rank = {"critical": 0, "warning": 1, "info": 2}
    out: list[Finding] = []
    all_findings = check_thresholds(df, spec) + check_outliers(df, spec) + check_drift(df, spec)
    for f in sorted(all_findings, key=lambda f: rank[f.severity]):
        key = (f.sensor, f.kind)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out
