"""
Cargas de viento multi-código — AS 1170.2 + NSR-10 §B.6 + SS EN 1991-1-4.

ASCE 7-22 y EN 1991-1-4 ya existen en otros módulos (windloads.codes).
Este complementa.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


# --- AS 1170.2 (2021) ---
@dataclass(frozen=True)
class AS1170WindInput:
    V_R_m_s: float                       # velocidad regional
    height_m: float
    terrain_category: Literal["1", "2", "3", "4"] = "2"
    Md: float = 1.0                       # direccionalidad
    Ms: float = 1.0                       # shielding
    Mt: float = 1.0                       # topográfico


@dataclass(frozen=True)
class AS1170WindResult:
    Vsite_m_s: float
    qz_kPa: float
    Mzcat: float


_MZCAT_AS = {  # Tabla 4.1(A) AS 1170.2
    "1": [0.99, 1.05, 1.12, 1.16, 1.20, 1.23, 1.26, 1.28, 1.30, 1.31],
    "2": [0.91, 0.91, 0.91, 0.94, 1.00, 1.05, 1.09, 1.12, 1.14, 1.16],
    "3": [0.83, 0.83, 0.83, 0.83, 0.89, 0.94, 0.97, 1.00, 1.04, 1.06],
    "4": [0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.85, 0.89, 0.94, 0.98],
}
_HEIGHTS_AS = [3, 5, 10, 15, 20, 30, 40, 50, 75, 100]


def _Mzcat_interp(h: float, cat: str) -> float:
    import bisect
    if h <= _HEIGHTS_AS[0]:
        return _MZCAT_AS[cat][0]
    if h >= _HEIGHTS_AS[-1]:
        return _MZCAT_AS[cat][-1]
    idx = bisect.bisect_left(_HEIGHTS_AS, h)
    h1, h2 = _HEIGHTS_AS[idx - 1], _HEIGHTS_AS[idx]
    v1, v2 = _MZCAT_AS[cat][idx - 1], _MZCAT_AS[cat][idx]
    return v1 + (v2 - v1) * (h - h1) / (h2 - h1)


def evaluate_as1170(inp: AS1170WindInput) -> AS1170WindResult:
    """AS 1170.2 §2.2 — V_site = V_R · M_d · M_zcat · M_s · M_t"""
    Mzcat = _Mzcat_interp(inp.height_m, inp.terrain_category)
    Vsite = inp.V_R_m_s * inp.Md * Mzcat * inp.Ms * inp.Mt
    qz = 0.5 * 1.20 * Vsite ** 2 / 1000.0   # ρ=1.20 kg/m³ → kPa
    return AS1170WindResult(Vsite_m_s=Vsite, qz_kPa=qz, Mzcat=Mzcat)


# --- NSR-10 §B.6 ---
@dataclass(frozen=True)
class NSR10WindInput:
    V_m_s: float                # velocidad básica (mapa NSR-10 Fig. B.6.4-1)
    height_m: float
    exposure: Literal["B", "C", "D"] = "C"
    importance: float = 1.0
    Kd: float = 0.85
    Kzt: float = 1.0


def evaluate_nsr10_wind(inp: NSR10WindInput) -> dict[str, float]:
    """NSR-10 §B.6.5 — qz = 0.613·Kz·Kzt·Kd·V²·I (Pa, SI)."""
    # Kz Tabla B.6.5-1
    alpha = {"B": 7.0, "C": 9.5, "D": 11.5}[inp.exposure]
    zg = {"B": 365, "C": 274, "D": 213}[inp.exposure]
    z = max(inp.height_m, 4.6 if inp.exposure == "B" else 4.6)
    Kz = 2.01 * (z / zg) ** (2.0 / alpha)
    qz_Pa = 0.613 * Kz * inp.Kzt * inp.Kd * inp.V_m_s ** 2 * inp.importance
    return {"Kz": Kz, "qz_Pa": qz_Pa, "qz_kPa": qz_Pa / 1000.0}


# --- SS EN 1991-1-4 (Singapore National Annex) ---
@dataclass(frozen=True)
class SSENWindInput:
    Vb_0_m_s: float = 26.0       # SS NA default 26 m/s
    height_m: float = 10.0
    terrain_category: Literal["I", "II", "III", "IV"] = "III"  # urban
    c_dir: float = 1.0
    c_season: float = 1.0


def evaluate_ss_en_wind(inp: SSENWindInput) -> dict[str, float]:
    """SS EN 1991-1-4 §4 — qp(z) = c_e(z) · qb."""
    Vb = inp.Vb_0_m_s * inp.c_dir * inp.c_season
    qb = 0.5 * 1.25 * Vb ** 2 / 1000.0  # kPa
    # c_e(z) Tabla 4.4 EN 1991-1-4 NA Singapore (urbano denso)
    z0 = {"I": 0.01, "II": 0.05, "III": 0.30, "IV": 1.00}[inp.terrain_category]
    z_min = {"I": 1, "II": 2, "III": 5, "IV": 10}[inp.terrain_category]
    z = max(inp.height_m, z_min)
    import math
    cr = 0.19 * (z0 / 0.05) ** 0.07 * math.log(z / z0)
    co = 1.0
    Iv = 1.0 / (co * math.log(z / z0))
    ce = (cr * co) ** 2 * (1 + 7 * Iv)
    qp = ce * qb
    return {"Vb_m_s": Vb, "qb_kPa": qb, "ce": ce, "qp_kPa": qp}


__all__ = [
    "AS1170WindInput", "AS1170WindResult", "evaluate_as1170",
    "NSR10WindInput", "evaluate_nsr10_wind",
    "SSENWindInput", "evaluate_ss_en_wind",
]
