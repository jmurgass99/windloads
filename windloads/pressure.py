"""
pressure.py — External and internal pressure coefficients for wind loads.

Covers:
  - EC1-1-4 §7: pressure coefficients cpe for walls and roofs
  - ASCE 7-22 §27: Cp for MWFRS (directional method)
  - Internal pressure: GCpi for enclosed / partially enclosed buildings
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# EC1-1-4 §7.2 — External pressure coefficients for vertical walls
# Table 7.1 (rectangular plan)
# h/d ratio → cpe,10 for windward, leeward, side walls
# ---------------------------------------------------------------------------
def ec1_cpe_walls(h: float, d: float) -> dict[str, float]:
    """
    External pressure coefficient cpe,10 for vertical walls (EC1 §7.2.2).

    Parameters
    ----------
    h : float  building height [m]
    d : float  depth in wind direction [m]

    Returns
    -------
    dict with keys: A (windward), B (leeward), C-E (side walls)

    Reference: EN 1991-1-4 Table 7.1
    """
    ratio = h / d
    if ratio <= 0.25:
        cpe = {"A": -1.0, "B": -0.8, "C": -0.5, "D": 0.7, "E": -0.3}
    elif ratio <= 1.0:
        # linear interpolation between 0.25 and 1.0
        t = (ratio - 0.25) / 0.75
        cpe = {
            "A": -1.0,
            "B": -0.8,
            "C": -0.5,
            "D": 0.7 + t * (0.8 - 0.7),
            "E": -0.3 + t * (-0.5 - (-0.3)),
        }
    else:
        cpe = {"A": -1.0, "B": -0.8, "C": -0.5, "D": 0.8, "E": -0.5}
    return cpe


# ---------------------------------------------------------------------------
# ASCE 7-22 §27.3 — Cp for MWFRS (directional method)
# Figure 27.3-1: walls and roofs
# ---------------------------------------------------------------------------
def asce7_Cp_walls(L: float, B: float, h: float) -> dict[str, float]:
    """
    External pressure coefficients Cp for MWFRS walls (ASCE 7-22 Fig. 27.3-1).

    Parameters
    ----------
    L : float  dimension parallel to wind [m]
    B : float  dimension normal to wind [m]
    h : float  mean roof height [m]

    Returns
    -------
    dict with keys: windward, leeward, side
    """
    L_B = L / B
    # Leeward wall Cp depends on L/B
    if L_B <= 1.0:
        Cp_leeward = -0.5
    elif L_B <= 2.0:
        Cp_leeward = -0.3
    else:
        Cp_leeward = -0.2

    return {
        "windward": 0.8,         # constant per ASCE 7 §27.3.1
        "leeward": Cp_leeward,
        "side": -0.7,
    }


def asce7_Cp_roof_flat(h: float, L: float) -> dict[str, float]:
    """
    Cp for flat roof MWFRS (ASCE 7-22 Fig. 27.3-1).
    h/L ratio controls windward and leeward roof zones.

    Returns
    -------
    dict with keys: windward_10ft, windward_beyond, leeward
    """
    h_L = h / L
    if h_L <= 0.25:
        Cp_ww_10 = -0.9
        Cp_ww_be = -0.9
        Cp_lw = -0.3
    elif h_L <= 0.5:
        Cp_ww_10 = -0.9
        Cp_ww_be = -0.7
        Cp_lw = -0.5
    else:
        Cp_ww_10 = -1.3
        Cp_ww_be = -0.7
        Cp_lw = -0.7
    return {
        "windward_first_10ft": Cp_ww_10,
        "windward_beyond": Cp_ww_be,
        "leeward": Cp_lw,
    }


# ---------------------------------------------------------------------------
# Internal pressure coefficients (GCpi)
# ---------------------------------------------------------------------------
_EC1_CPI: dict[str, float] = {
    "closed": 0.2,         # positive internal pressure
    "closed_neg": -0.3,    # negative internal pressure
    "open_one_face": 0.7,  # dominant opening on windward face
    "open_all": 0.0,       # open sides
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

    Parameters
    ----------
    code : str
        'EC1', 'ASCE7', or 'NSR10'
    enclosure : str
        Building enclosure classification.
        EC1: 'closed', 'closed_neg', 'open_one_face', 'open_all'
        ASCE7: 'enclosed', 'partially_enclosed', 'open'
        NSR10: 'cerrado', 'parcialmente_abierto', 'abierto'
    """
    code: str
    enclosure: str = "enclosed"

    def __post_init__(self) -> None:
        self.code = self.code.upper()

    # ------------------------------------------------------------------
    # EC1 net pressure
    # ------------------------------------------------------------------
    def ec1_net_pressure(self, qp: float, cpe: float,
                          positive_internal: bool = True) -> float:
        """
        Net wind pressure on surface (EC1 §5.2):
          we = qp · cpe  (external)
          wi = qp · cpi  (internal)
          w_net = we - wi

        Positive = pressure on surface, negative = suction.
        """
        cpi = _EC1_CPI["closed" if positive_internal else "closed_neg"]
        we = qp * cpe
        wi = qp * cpi
        return we - wi

    def ec1_wall_pressures(self, qp_h: float, h: float, d: float) -> dict:
        """
        Net pressures on all wall zones (EC1 §7.2).
        qp_h: peak velocity pressure at reference height [Pa]
        """
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

    # ------------------------------------------------------------------
    # ASCE 7 net pressure
    # ------------------------------------------------------------------
    def asce7_wall_pressures(self, qz: float, qh: float,
                              L: float, B: float, h: float,
                              G: float = 0.85) -> dict:
        """
        Net design pressures for MWFRS walls (ASCE 7-22 §27.3):
          p = q · G · Cp - qi · (GCpi)

        Parameters
        ----------
        qz : float  velocity pressure at height z [Pa] (windward varies with z)
        qh : float  velocity pressure at mean roof height h [Pa]
        L : float   building depth parallel to wind [m]
        B : float   building width normal to wind [m]
        h : float   mean roof height [m]
        G : float   gust factor (default 0.85 for rigid buildings)
        """
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

    # ------------------------------------------------------------------
    # NSR-10 net pressure (identical formulation to ASCE 7)
    # ------------------------------------------------------------------
    def nsr10_wall_pressures(self, qz: float, qh: float,
                              L: float, B: float, h: float,
                              G: float = 0.85) -> dict:
        """
        Net design pressures for MWFRS walls (NSR-10 §B.6.6).
        Same formulation as ASCE 7-22 with NSR-10 coefficients.
        """
        Cp = asce7_Cp_walls(L, B, h)   # Same Cp table
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
