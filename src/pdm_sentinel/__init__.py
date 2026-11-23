"""PdM Sentinel: open-source predictive maintenance engine."""
from .machines import MACHINES, MachineSpec, SensorSpec
from .detectors import Finding, detect_all
from .health import Health, score_machine
from .pipeline import PlantReport, MachineResult, analyze_frame, analyze_plant
from .simulator import simulate_machine, simulate_plant

__version__ = "0.1.0"
