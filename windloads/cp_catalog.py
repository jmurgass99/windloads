"""
Catálogo de coeficientes Cp típicos por geometría — ASCE 7-22 +
EN 1991-1-4 + AS/NZS 1170.2.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CpEntry:
    geometry: str
    code: str
    Cp_windward: float
    Cp_leeward: float
    Cp_side: float
    notes: str = ""


CP_CATALOG: list[CpEntry] = [
    # Edificios rectangulares (L/B = 1.0)
    CpEntry("box_LB1", "ASCE7",  0.80, -0.50, -0.70, "L/B=1.0"),
    CpEntry("box_LB1", "EN1991", 0.80, -0.50, -0.80),
    CpEntry("box_LB1", "AS1170", 0.70, -0.50, -0.65),
    # Edificios alargados (L/B = 4.0)
    CpEntry("box_LB4", "ASCE7",  0.80, -0.20, -0.70),
    CpEntry("box_LB4", "EN1991", 0.80, -0.30, -0.80),
    # Techo plano
    CpEntry("flat_roof", "ASCE7",  -0.90, -0.50, -1.30, "esquinas"),
    CpEntry("flat_roof", "EN1991", -1.20, -0.20, -1.20),
    # Techo a 2 aguas pendiente 20°
    CpEntry("gable_20deg", "ASCE7",  -0.40, -0.30, -0.50),
    CpEntry("gable_20deg", "EN1991", -0.30, -0.30, -0.40),
    # Cilindros (chimeneas)
    CpEntry("cylinder", "ASCE7",  0.80, -0.50, -0.70, "Re > 4e5"),
    CpEntry("cylinder", "EN1991", 1.00, -0.40, -0.70),
    # Marcos abiertos (truss/lattice)
    CpEntry("open_truss", "ASCE7",  1.30, -0.20, 0.0, "solidity 0.3"),
    CpEntry("open_truss", "AS1170", 1.40, -0.20, 0.0),
]


def lookup_cp(geometry: str, code: str = "ASCE7") -> CpEntry | None:
    for e in CP_CATALOG:
        if e.geometry == geometry and e.code.upper() == code.upper():
            return e
    return None


def list_geometries() -> list[str]:
    return sorted(set(e.geometry for e in CP_CATALOG))


__all__ = ["CpEntry", "CP_CATALOG", "lookup_cp", "list_geometries"]
