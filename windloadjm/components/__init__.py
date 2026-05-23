"""Components & Cladding (ASCE 7 Ch. 30 / EC1 7).

Subpackage que re-exporta toda la API publica de la implementacion
historica (_impl.py) para garantizar backward compat con:

    from windloadjm.components import ComponentsAndCladding, asce7_GCp, ...
"""
from __future__ import annotations

from ._impl import (  # noqa: F401
    # Core ASCE7 / EC1 helpers
    ComponentsAndCladding,
    asce7_GCp,
    asce7_cc_pressure,
    asce7_corner_distance_a,
    ec1_cpe_local,
    ec1_cc_pressure,
    ec1_zone_width_e,
    # Sloped / curved / parapet / mansard roofs
    gable_roof_GCp,
    gable_roof_zones,
    monoslope_roof_GCp,
    domed_roof_GCp,
    mansard_roof_GCp,
    parapet_pressure,
    ec1_gable_cpe,
    ec1_monopitch_cpe,
    ec1_cylindrical_cpe,
    # Constants used by callers / tests
    MIN_DESIGN_PRESSURE_PA,
)

__all__ = [
    "ComponentsAndCladding",
    "asce7_GCp",
    "asce7_cc_pressure",
    "asce7_corner_distance_a",
    "ec1_cpe_local",
    "ec1_cc_pressure",
    "ec1_zone_width_e",
    "gable_roof_GCp",
    "gable_roof_zones",
    "monoslope_roof_GCp",
    "domed_roof_GCp",
    "mansard_roof_GCp",
    "parapet_pressure",
    "ec1_gable_cpe",
    "ec1_monopitch_cpe",
    "ec1_cylindrical_cpe",
    "MIN_DESIGN_PRESSURE_PA",
]
