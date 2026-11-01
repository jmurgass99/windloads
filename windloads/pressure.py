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
    dict with keys: A, B, C (side walls, from the windward edge),
    D (windward wall) and E (leeward wall) — EN 1991-1-4 Figure 7.5.

    Reference: EN 1991-1-4 Table 7.1 (recommended values):
        h/d      A     B     C     D     E
        5      -1.2  -0.8  -0.5  +0.8  -0.7
        1      -1.2  -0.8  -0.5  +0.8  -0.5
        <=0.25 -1.2  -0.8  -0.5  +0.7  -0.3
    with linear interpolation for intermediate h/d (Note 1 to Figure 7.5).
    For h/d > 5 the h/d = 5 row is returned (Note 2 points to 7.6-7.8 / 7.9.2).
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
    Figure 7.4), b = crosswind dimension:

      * h <= b       : ze = h for the whole wall;
      * b < h <= 2b  : ze = b for z <= b, ze = h above;
      * h > 2b       : ze = b for z <= b, ze = h for z >= h - b, and ze = z in
                       the middle region (strips; pass the top of the strip).
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

    Parameters
    ----------
    L : float  dimension parallel to wind [m]
    B : float  dimension normal to wind [m]
    h : float  mean roof height [m]

    Returns
    -------
    dict with keys: windward, leeward, side
    """
    return {
        "windward": 0.8,         # constant per ASCE 7 §27.3.1
        "leeward": asce7_leeward_Cp(L / B),
        "side": -0.7,
    }


def asce7_leeward_Cp(L_over_B: float) -> float:
    """
    Leeward wall Cp of Fig. 27.3-1 (ASCE 7-16): -0.5 for 0 <= L/B <= 1,
    -0.3 for L/B = 2 and -0.2 for L/B >= 4, with linear interpolation in
    between (the figure notes permit it). Before 1.2.0 the value jumped in
    steps (-0.3 already at L/B = 1.01, -0.2 at L/B = 2.01).
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
    Cp for flat roof MWFRS (ASCE 7-22 Fig. 27.3-1) — SIMPLIFIED, NOT CHECKED.

    Fig. 27.3-1 gives the roof Cp by horizontal distance from the windward
    edge (0 to h/2, h/2 to h, h to 2h, > 2h) and h/L; this function returns
    three lumped values that do not follow that zoning and were not checked
    against the figure. Not used by any calculator of the package.

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
    "open_one_face": 0.7,  # NOT normative and unused (see §7.2.9(3): 0.75/0.90 x cpe)
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

        Internal pressure is always cpi = +0.2 / -0.3 (EN 1991-1-4 §7.2.9(6)
        Note 2, building without a dominant face); ``self.enclosure`` is not
        used here. With a dominant opening cpi = 0.75 or 0.90 times the cpe
        of that face (§7.2.9(3)) and must be computed by the caller.
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
