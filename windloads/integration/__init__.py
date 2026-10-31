"""Integraciones cross-satelite WindLoads."""
from .fastsap_bridge import (
    WindLoadAssignment, WindBridgeResult,
    apply_wind_loads_to_sap, distribute_pressure_to_joints,
)
__all__ = [
    "WindLoadAssignment", "WindBridgeResult",
    "apply_wind_loads_to_sap", "distribute_pressure_to_joints",
]
