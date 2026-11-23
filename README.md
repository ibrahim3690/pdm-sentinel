# PdM Sentinel

An open-source predictive maintenance engine for rotating and driven
equipment: AC motors, DC motors, drive belts, and pumps.

Sensor data goes in, and the engine produces two things per machine:

1. **A health score (0-100)** combining fixed threshold violations,
   statistical outliers, slow drift, and recent trends.
2. **Specific fault alerts** that name the device, the sensor, the observed
   value, and the normal range, so a technician knows exactly where to look.

> **Disclosure:** this project was designed and written with AI assistance
> (an AI agent wrote the code, which was then run and tested locally). It is
> released as a learning and evaluation starting point, not as a certified
> industrial safety system.

## How it works

Each machine has a spec (`src/pdm_sentinel/machines.py`) describing its
sensors and three nested bands: normal, warning, critical.

Four detectors run over the readings (`src/pdm_sentinel/detectors.py`):

- **Threshold rules** - the worst excursion outside each sensor's bands.
- **Z-score outliers** - readings far from the early healthy baseline.
- **EWMA drift** - the smoothed signal leaves its normal band and stays out.
- **Trend slope** - the recent tail heads toward a band edge (used by scoring).

Health scoring (`src/pdm_sentinel/health.py`) starts at 100, subtracts
weighted penalties per finding (capped per sensor), subtracts a trend
penalty, and grades the result: Good / Watch / Warning / Critical.

## Quick start

Requires Python 3.10+ with numpy and pandas:

```bash
pip install -r requirements.txt
```

Simulate a plant (four machines, one developing fault each), analyze it, and
render the dashboard:

```bash
export PYTHONPATH=src
python -m pdm_sentinel simulate --out data/
python -m pdm_sentinel analyze --data data/ --report report.html
```

Example output:

```
AC Motor (3-phase)     health  55.0/100  [Warning]
DC Motor               health  60.0/100  [Warning]
Drive Belt             health  58.0/100  [Warning]
Coolant Pump           health  70.0/100  [Watch]

6 active alert(s):
  [CRITICAL] AC Motor (3-phase) current_r is LOW: 0.31 A (normal 8.0-16.0 A)
  [WARNING ] DC Motor vibration is HIGH: 8.27 mm/s (normal 0.5-4.5 mm/s)
  ...
```

Or run the self-contained demo:

```bash
PYTHONPATH=src python examples/run_demo.py
```

## Using your own data

Replace the simulated CSVs with real ones. One CSV per machine, named
`<machine_id>.csv`, with a `timestamp` column plus one column per sensor
listed in the machine spec. Custom machines: add a `MachineSpec` entry in
`machines.py`.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Repository layout

```
src/pdm_sentinel/
  machines.py    sensor specs and normal/warn/critical bands
  simulator.py   deterministic synthetic data with injected fault scenarios
  detectors.py   threshold, z-score, drift, and trend detectors
  health.py      0-100 health scoring and grading
  pipeline.py    load CSVs, run detectors, score, collect alerts
  report.py      single-file HTML dashboard (no server or JS needed)
  cli.py         simulate / analyze commands
tests/           unit and end-to-end tests (stdlib unittest)
examples/        run_demo.py
```

## Fault scenarios in the simulator

| Machine  | Scenario      | Signature                                  |
|----------|---------------|--------------------------------------------|
| AC motor | phase loss    | phase R current collapses, temperature rises |
| DC motor | bearing wear  | vibration ramps up, current creeps up      |
| Belt     | belt slip     | speed and tension drop                     |
| Pump     | cavitation    | pressure oscillates with growing amplitude |

## License

MIT - see [LICENSE](LICENSE).
