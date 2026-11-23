"""Machine and sensor specifications for the monitored assets.

Every numeric band follows the same nesting:
    crit_low < warn_low < normal_min < normal_max < warn_high < crit_high
Readings outside the normal band but inside the warn band produce warnings;
outside the warn band they produce critical findings.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorSpec:
    name: str
    unit: str
    normal_min: float
    normal_max: float
    warn_low: float
    warn_high: float
    crit_low: float
    crit_high: float


@dataclass(frozen=True)
class MachineSpec:
    machine_id: str
    display_name: str
    sensors: tuple[SensorSpec, ...]

    def sensor(self, name: str) -> SensorSpec:
        for s in self.sensors:
            if s.name == name:
                return s
        raise KeyError(f"{self.machine_id} has no sensor {name!r}")


def _phase(base: str, unit: str, lo: float, hi: float) -> tuple[SensorSpec, ...]:
    """Build the three phase variants of a 3-phase quantity (R/S/T)."""
    span = hi - lo
    return tuple(
        SensorSpec(
            name=f"{base}_{p}",
            unit=unit,
            normal_min=lo,
            normal_max=hi,
            warn_low=lo - 0.25 * span,
            warn_high=hi + 0.25 * span,
            crit_low=lo - 0.5 * span,
            crit_high=hi + 0.5 * span,
        )
        for p in ("r", "s", "t")
    )


MACHINES: dict[str, MachineSpec] = {
    "ac_motor": MachineSpec(
        machine_id="ac_motor",
        display_name="AC Motor (3-phase)",
        sensors=(
            SensorSpec("temperature", "°C", 40.0, 70.0, 30.0, 80.0, 20.0, 90.0),
            SensorSpec("vibration", "mm/s", 0.5, 4.5, 0.2, 7.1, 0.1, 11.0),
            *_phase("current", "A", 8.0, 16.0),
            *_phase("voltage", "V", 380.0, 420.0),
        ),
    ),
    "dc_motor": MachineSpec(
        machine_id="dc_motor",
        display_name="DC Motor",
        sensors=(
            SensorSpec("voltage", "V", 220.0, 240.0, 210.0, 250.0, 200.0, 260.0),
            SensorSpec("current", "A", 2.0, 6.0, 1.0, 8.0, 0.5, 10.0),
            SensorSpec("vibration", "mm/s", 0.5, 4.0, 0.2, 6.0, 0.1, 9.0),
        ),
    ),
    "belt": MachineSpec(
        machine_id="belt",
        display_name="Drive Belt",
        sensors=(
            SensorSpec("tension", "N", 400.0, 600.0, 320.0, 680.0, 250.0, 750.0),
            SensorSpec("alignment", "mm", 0.0, 2.0, 0.0, 3.0, 0.0, 4.5),
            SensorSpec("speed", "m/s", 2.5, 3.5, 2.0, 4.0, 1.5, 4.5),
        ),
    ),
    "pump": MachineSpec(
        machine_id="pump",
        display_name="Coolant Pump",
        sensors=(
            SensorSpec("pressure", "bar", 3.0, 5.0, 2.2, 5.8, 1.5, 6.5),
            SensorSpec("flow", "L/min", 40.0, 60.0, 30.0, 70.0, 20.0, 80.0),
            SensorSpec("temperature", "°C", 25.0, 45.0, 18.0, 52.0, 12.0, 60.0),
        ),
    ),
}
