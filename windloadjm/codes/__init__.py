"""
windloadjm.codes — High-level normative APIs.

Modules
-------
ec1_1_4   : EN 1991-1-4:2005 (+A1:2010) — Eurocode 1, wind actions
asce7_26  : ASCE/SEI 7-22 — Chapters 26 (general) and 27 (MWFRS directional)
nsr10_b6  : NSR-10 Título B.6 (Colombia)
"""
from .ec1_1_4 import EC1WindLoad
from .asce7_26 import ASCE7WindLoad, KD_TABLE, G_RIGID
from .nsr10_b6 import (
    NSR10WindLoad,
    nsr10_basic_wind_speed,
    nsr10_zone_from_coords,
    NSR10_WIND_SPEED_BY_CITY,
    NSR10_WIND_ZONES,
    NSR10_CITY_ZONES,
)

__all__ = [
    "EC1WindLoad",
    "ASCE7WindLoad",
    "NSR10WindLoad",
    "KD_TABLE",
    "G_RIGID",
    "nsr10_basic_wind_speed",
    "nsr10_zone_from_coords",
    "NSR10_WIND_SPEED_BY_CITY",
    "NSR10_WIND_ZONES",
    "NSR10_CITY_ZONES",
]
