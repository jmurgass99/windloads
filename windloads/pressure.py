"""
pressure.py — External and internal pressure coefficients for wind loads.

Covers:
  - EC1-1-4 §7: pressure coefficients cpe for walls and roofs
  - ASCE 7-22 §27: Cp for MWFRS (directional method)
  - Internal pressure: GCpi for enclosed / partially enclosed buildings
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# EC1-1-4 §7.2 — External pressure coefficients for vertical walls
# Table 7.1 (rectangular plan)
# ---------------------------------------------------------------------------
def ec1_cpe_walls(h: float, d: float) -> dict[str, float]:
    """
    External pressure coefficient cpe,10 for vertical walls (EC1 §7.2.2).
    """
    ratio = h / d
    if ratio <= 0.25:
        d_cpe, e_cpe = 0.7, -0.3
    elif ratio <= 1.0:
        t = (ratio - 0.25) / 0.75
        d_cpe = 0.7 + t * (0.8 - 0.7)
        e_cpe = -0.3 + t * (-0.5 - (-0.3))
    elif ratio <= 5.0:
        t = (ratio - 1.0) / 4.0
        d_cpe = 0.8
        e_cpe = -0.5 + t * (-0.7 - (-0.5))
    else:
        d_cpe, e_cpe = 0.8, -0.7
    return {"A": -1.2, "B": -0.8, "C": -0.5, "D": d_cpe, "E": e_cpe}


def ec1_lack_of_correlation_factor(h: float, d: float) -> float:
    """
    Lack-of-correlation factor between windward (D) and leeward (E) walls,
    EN 1991-1-4 §7.2.2(3) Note: 1.0 for h/d >= 5, 0.85 for h/d <= 1,
    linear interpolation in between.
    """
    ratio = h / d
    if ratio <= 1.0:
        return 0.85
    if ratio >= 5.0:
        return 1.0
    return 0.85 + (ratio - 1.0) / 4.0 * 0.15


def ec1_windward_reference_height(z: float, h: float, b: float) -> float:
    """
    Reference height ze of the windward wall at height z (EN 1991-1-4 §7.2.2(1),
    Figure 7.4), b = crosswind dimension.
    """
    if h <= b:
        return h
    if z <= b:
        return b
    if h <= 2.0 * b or z >= h - b:
        return h
    return z


# ---------------------------------------------------------------------------
# ASCE 7-22 §27.3 — Cp for MWFRS (directional method)
# Figure 27.3-1: walls and roofs
# ---------------------------------------------------------------------------
def asce7_Cp_walls(L: float, B: float, h: float) -> dict[str, float]:
    """
    External pressure coefficients Cp for MWFRS walls (ASCE 7-22 Fig. 27.3-1).
    """
    return {
        "windward": 0.8,
        "leeward": asce7_leeward_Cp(L / B),
        "side": -0.7,
    }


def asce7_leeward_Cp(L_over_B: float) -> float:
    """
    Leeward wall Cp of Fig. 27.3-1 (ASCE 7-16 / 7-22): -0.5 for 0 <= L/B <= 1,
    -0.3 for L/B = 2 and -0.2 for L/B >= 4, with linear interpolation in between.
    """
    if L_over_B <= 1.0:
        return -0.5
    if L_over_B <= 2.0:
        return -0.5 + (L_over_B - 1.0) * 0.2
    if L_over_B <= 4.0:
        return -0.3 + (L_over_B - 2.0) / 2.0 * 0.1
    return -0.2


def asce7_Cp_roof_flat(h: float, L: float) -> dict[str, float]:
    """
    Cp for flat roof MWFRS (ASCE 7-22 Fig. 27.3-1, θ < 10°) as a function of
    horizontal distance from the windward edge (`0 to h/2`, `h/2 to h`,
    `h to 2h`, `> 2h`) and ratio ``h/L``.

    For ``h/L <= 0.5``:
      - 0 to h/2  : -0.9  (and -0.18 minimum magnitude case)
      - h/2 to h  : -0.9  (and -0.18)
      - h to 2h   : -0.5  (and -0.18)
      - > 2h      : -0.3  (and -0.18)
    For ``h/L >= 1.0``:
      - 0 to h/2  : -1.3  (and -0.18)
      - > h/2     : -0.7  (and -0.18)
    Linear interpolation is applied for ``0.5 < h/L < 1.0`` per Fig. 27.3-1 Note 7.
    """
    h_L = h / L if L > 0 else 1.0
    if h_L <= 0.5:
        cp_0_h2 = -0.9
        cp_h2_h = -0.9
        cp_h_2h = -0.5
        cp_gt_2h = -0.3
    elif h_L >= 1.0:
        cp_0_h2 = -1.3
        cp_h2_h = -0.7
        cp_h_2h = -0.7
        cp_gt_2h = -0.7
    else:
        t = (h_L - 0.5) / 0.5
        cp_0_h2 = -0.9 + t * (-1.3 - (-0.9))
        cp_h2_h = -0.9 + t * (-0.7 - (-0.9))
        cp_h_2h = -0.5 + t * (-0.7 - (-0.5))
        cp_gt_2h = -0.3 + t * (-0.7 - (-0.3))

    return {
        "zone_0_to_h_half": round(cp_0_h2, 4),
        "zone_h_half_to_h": round(cp_h2_h, 4),
        "zone_h_to_2h": round(cp_h_2h, 4),
        "zone_gt_2h": round(cp_gt_2h, 4),
        "min_case_cp": -0.18,
        # Legacy aliases kept for compatibility
        "windward_first_10ft": round(cp_0_h2, 4),
        "windward_beyond": round(cp_h2_h, 4),
        "leeward": round(cp_gt_2h, 4),
    }


# ---------------------------------------------------------------------------
# Internal pressure coefficients (GCpi)
# ---------------------------------------------------------------------------
_EC1_CPI: dict[str, float] = {
    "closed": 0.2,
    "closed_neg": -0.3,
    "open_one_face": 0.7,
    "open_all": 0.0,
}

_ASCE7_GCPI: dict[str, tuple[float, float]] = {
    "enclosed": (0.18, -0.18),
    "partially_enclosed": (0.55, -0.55),
    "open": (0.0, 0.0),
}

_NSR10_GCPI: dict[str, tuple[float, float]] = {
    "cerrado": (0.18, -0.18),
    "parcialmente_abierto": (0.55, -0.55),
    "abierto": (0.0, 0.0),
}


@dataclass
class WindPressure:
    """
    Compute wind pressures on building surfaces.
    """
    code: str
    enclosure: str = "enclosed"

    def __post_init__(self) -> None:
        self.code = self.code.upper()

    def ec1_net_pressure(self, qp: float, cpe: float,
                          positive_internal: bool = True) -> float:
        cpi = _EC1_CPI["closed" if positive_internal else "closed_neg"]
        we = qp * cpe
        wi = qp * cpi
        return we - wi

    def ec1_wall_pressures(self, qp_h: float, h: float, d: float) -> dict:
        cpe = ec1_cpe_walls(h, d)
        cpi_pos = _EC1_CPI["closed"]
        cpi_neg = _EC1_CPI["closed_neg"]
        results = {}
        for zone, cp in cpe.items():
            we = qp_h * cp
            results[zone] = {
                "cpe": cp,
                "w_net_pos_kPa": round((we - qp_h * cpi_pos) / 1000, 3),
                "w_net_neg_kPa": round((we - qp_h * cpi_neg) / 1000, 3),
            }
        return results

    def asce7_wall_pressures(self, qz: float, qh: float,
                              L: float, B: float, h: float,
                              G: float = 0.85) -> dict:
        Cp = asce7_Cp_walls(L, B, h)
        GCpi_pos, GCpi_neg = _ASCE7_GCPI[self.enclosure]
        results = {}
        for surface, cp in Cp.items():
            q = qz if surface == "windward" else qh
            p_pos = q * G * cp - qh * GCpi_pos
            p_neg = q * G * cp - qh * GCpi_neg
            results[surface] = {
                "Cp": cp,
                "p_net_pos_kPa": round(p_pos / 1000, 3),
                "p_net_neg_kPa": round(p_neg / 1000, 3),
            }
        return results

    def nsr10_wall_pressures(self, qz: float, qh: float,
                              L: float, B: float, h: float,
                              G: float = 0.85) -> dict:
        Cp = asce7_Cp_walls(L, B, h)
        GCpi_pos, GCpi_neg = _NSR10_GCPI[self.enclosure]
        results = {}
        for surface, cp in Cp.items():
            q = qz if surface == "windward" else qh
            p_pos = q * G * cp - qh * GCpi_pos
            p_neg = q * G * cp - qh * GCpi_neg
            results[surface] = {
                "Cp": cp,
                "p_net_pos_kPa": round(p_pos / 1000, 3),
                "p_net_neg_kPa": round(p_neg / 1000, 3),
            }
        return results
