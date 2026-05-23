"""
WindLoadJm — Wind Load Calculation Library
==========================================
Multi-code wind load calculations: EC1-1-4, ASCE 7-22, NSR-10 B.6

Usage
-----
>>> from windloadjm import EC1WindLoad, ASCE7WindLoad, NSR10WindLoad
>>> wl = EC1WindLoad(vb=26.0, terrain_cat='II', building_height=30.0)
>>> summary = wl.compute()
"""
from ._brand import NAME, SLUG, EXE, APPDATA_DIR, ORG, REPO, URL, TAGLINE
from .codes.ec1_1_4 import EC1WindLoad
from .codes.asce7_26 import ASCE7WindLoad
from .codes.nsr10_b6 import NSR10WindLoad
from .terrain import TerrainProfile
from .pressure import WindPressure
from .envelope import MWFRSEnvelope
from .components import (
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
)
from .export import (
    StoryPressure,
    LoadPattern,
    WindLoadCase,
    JointMap,
    from_envelope,
    to_json,
    to_csv,
    to_sap_s2k,
    to_etabs_e2k,
    standard_directions,
)

__all__ = [
    "EC1WindLoad",
    "ASCE7WindLoad",
    "NSR10WindLoad",
    "TerrainProfile",
    "WindPressure",
    "MWFRSEnvelope",
    # C&C
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
    # Export
    "StoryPressure",
    "LoadPattern",
    "WindLoadCase",
    "JointMap",
    "from_envelope",
    "to_json",
    "to_csv",
    "to_sap_s2k",
    "to_etabs_e2k",
    "standard_directions",
    # Brand
    "NAME", "SLUG", "EXE", "APPDATA_DIR", "ORG", "REPO", "URL", "TAGLINE",
    # Exceptions
    "WindLoadError", "CodeError", "GeometryError",
    "ConfigurationError", "DependencyError",
]
__version__ = "1.1.0"

# Exception hierarchy
from .exceptions import (  # noqa: E402
    WindLoadError, CodeError, GeometryError,
    ConfigurationError, DependencyError,
)
