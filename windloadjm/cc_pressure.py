"""
cc_pressure.py -- Components & Cladding pressure curves A-G (ASCE 7-22 Ch. 30).

Implements the full C&C pressure calculation per ASCE 7-22 Chapter 30 for
enclosed and partially-enclosed low-rise buildings (h <= 18.3 m / 60 ft).

Key references
--------------
- Table 30.3-1 : Walls -- Zones 4 (interior) and 5 (corner)
- Table 30.3-2A: Flat roofs (theta <= 7 deg) -- Zones 1, 2, 3
- Fig. 30.3-1  : GCp curves as a function of effective wind area
- Eq. 30.3-1   : p = qh * (GCp - GCpi)
- Section 30.3.2: Effective wind area definition

The GCp values are log-interpolated between the tabulated reference areas
(10 ft^2 and 500 ft^2) following the standard ASCE 7 curve methodology.

Zones
-----
Walls:
    Zone 4 -- Interior wall (away from edges by distance 'a')
    Zone 5 -- Corner wall strip (within distance 'a' from building edge)

Flat Roofs (theta <= 7 deg):
    Zone 1 -- Interior
    Zone 2 -- Edge strip
    Zone 3 -- Corner

The corner distance 'a' is defined in Section 30.3.1:
    a = min(0.10*B, 0.4*h)  but not less than max(0.04*B, 0.9 m)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .exceptions import ConfigurationError, GeometryError


# =========================================================================
# GCp tabulated values from ASCE 7-22 Table 30.3-1 (walls) and 30.3-2A (roofs)
# Tuple format: (GCp_at_10ft2, GCp_at_500ft2)
# 10 ft^2 = 0.929 m^2,  500 ft^2 = 46.45 m^2
# =========================================================================
_A_LO_M2 = 10 * 0.092903     # 10 ft^2 in m^2
_A_HI_M2 = 500 * 0.092903    # 500 ft^2 in m^2

# Table 30.3-1: Walls, h <= 60 ft (18.3 m)
_TABLE_30_3_1: dict[str, dict[str, tuple[float, float]]] = {
    "4": {"pos": (1.00, 0.70), "neg": (-1.10, -0.80)},
    "5": {"pos": (1.00, 0.70), "neg": (-1.40, -0.80)},
}

# Table 30.3-2A: Flat roofs, theta <= 7 deg, h <= 60 ft
_TABLE_30_3_2A: dict[str, dict[str, tuple[float, float]]] = {
    "1": {"pos": (0.30, 0.20), "neg": (-1.70, -1.10)},
    "2": {"pos": (0.30, 0.20), "neg": (-2.30, -1.60)},
    "3": {"pos": (0.30, 0.20), "neg": (-3.20, -2.30)},
}

# ASCE 7-22 Section 30.2.2: minimum design pressure
_MIN_DESIGN_PRESSURE_PA = 16 * 47.8803   # 16 psf ~ 766 Pa

# GCpi values per enclosure classification (ASCE 7-22 Table 26.13-1)
_GCPI: dict[str, float] = {
    "enclosed": 0.18,
    "partially_enclosed": 0.55,
    "open": 0.00,
}


def _log_interp(A_eff: float, val_lo: float, val_hi: float) -> float:
    """Log-linear interpolation of GCp between reference areas."""
    if A_eff <= _A_LO_M2:
        return val_lo
    if A_eff >= _A_HI_M2:
        return val_hi
    frac = (math.log10(A_eff) - math.log10(_A_LO_M2)) / \
           (math.log10(_A_HI_M2) - math.log10(_A_LO_M2))
    return val_lo + frac * (val_hi - val_lo)


def _get_table(roof_type: str) -> dict[str, dict[str, tuple[float, float]]]:
    """Select the correct GCp table for the given roof/surface type."""
    if roof_type == "wall":
        return _TABLE_30_3_1
    if roof_type in ("flat", "flat_roof"):
        return _TABLE_30_3_2A
    raise ConfigurationError(
        f"roof_type must be 'wall' or 'flat'. Got '{roof_type}'")


def _valid_zones(roof_type: str) -> list[str]:
    """Return valid zone IDs for a given surface type."""
    if roof_type == "wall":
        return ["4", "5"]
    return ["1", "2", "3"]


def corner_distance_a(B: float, h: float) -> float:
    """
    Width 'a' of the corner/edge strip (ASCE 7-22 Section 30.3.1):
        a = min(0.10*B, 0.4*h)   but not less than max(0.04*B, 0.9 m)

    Parameters
    ----------
    B : float
        Least horizontal dimension of the building [m].
    h : float
        Mean roof height [m].

    Returns
    -------
    float : corner strip width [m]
    """
    if B <= 0 or h <= 0:
        raise GeometryError("Building dimensions B and h must be positive.")
    a = min(0.10 * B, 0.4 * h)
    a_min = max(0.04 * B, 0.9)
    return max(a, a_min)


def get_GCp(zone: str, A_eff: float, roof_type: str = "wall",
            sign: str = "neg") -> float:
    """
    Log-interpolated GCp for C&C per ASCE 7-22 Chapter 30.

    Parameters
    ----------
    zone : str
        Zone identifier: '4' or '5' for walls; '1', '2', '3' for flat roofs.
    A_eff : float
        Effective wind area [m^2]. Must be > 0.
    roof_type : str
        'wall' for Table 30.3-1, 'flat' for Table 30.3-2A.
    sign : str
        'pos' for positive pressure or 'neg' for suction.

    Returns
    -------
    float : GCp value (includes gust effect; do NOT multiply by G).
    """
    if A_eff <= 0:
        raise GeometryError("Effective wind area A_eff must be positive.")
    table = _get_table(roof_type)
    if zone not in table:
        raise ConfigurationError(
            f"Zone '{zone}' not valid for '{roof_type}'. "
            f"Valid zones: {list(table)}")
    if sign not in ("pos", "neg"):
        raise ConfigurationError("sign must be 'pos' or 'neg'.")
    val_lo, val_hi = table[zone][sign]
    return _log_interp(A_eff, val_lo, val_hi)


def get_cc_pressure(
    zone: str,
    roof_type: str,
    A_eff: float,
    h: float,
    exposure: str,
    V: float,
    Kd: float = 0.85,
    Kzt: float = 1.0,
    enclosure: str = "enclosed",
) -> tuple[float, float]:
    """
    Net C&C design pressure for a component per ASCE 7-22 Eq. 30.3-1.

    Computes velocity pressure qh at mean roof height, then applies:
        p = qh * (GCp - GCpi)

    The function returns a (p_positive, p_negative) tuple representing the
    worst-case positive (inward) and negative (suction) pressures in Pa.

    Parameters
    ----------
    zone : str
        C&C zone: '4','5' (walls) or '1','2','3' (flat roofs).
    roof_type : str
        'wall' or 'flat'.
    A_eff : float
        Effective wind area of the component [m^2].
    h : float
        Mean roof height [m].
    exposure : str
        Exposure category: 'B', 'C', or 'D'.
    V : float
        Basic wind speed [m/s].
    Kd : float
        Directionality factor (default 0.85).
    Kzt : float
        Topographic factor (default 1.0, flat terrain).
    enclosure : str
        'enclosed', 'partially_enclosed', or 'open'.

    Returns
    -------
    tuple[float, float]
        (p_positive_Pa, p_negative_Pa)
        p_positive: worst inward pressure (positive value)
        p_negative: worst suction (negative value)

    Notes
    -----
    - GCpi is taken from ASCE 7-22 Table 26.13-1.
    - Velocity pressure: qh = 0.613 * Kz * Kzt * Kd * V^2  (Eq. 26.10-1)
    - Kz from ASCE 7-22 Table 26.10-1 (power-law profile).
    - Minimum design pressure per Section 30.2.2 = 16 psf (766 Pa).
    """
    # --- Validate inputs ---
    if A_eff <= 0:
        raise GeometryError("A_eff must be positive.")
    if h <= 0:
        raise GeometryError("Building height h must be positive.")
    if V <= 0:
        raise ConfigurationError("Wind speed V must be positive.")
    exposure = exposure.upper()
    if exposure not in ("B", "C", "D"):
        raise ConfigurationError(
            f"Exposure must be 'B', 'C', or 'D'. Got '{exposure}'.")
    if enclosure not in _GCPI:
        raise ConfigurationError(
            f"Enclosure must be one of {list(_GCPI)}. Got '{enclosure}'.")

    # --- Compute Kz at mean roof height (Table 26.10-1) ---
    _EXP_PARAMS = {
        "B": {"alpha": 7.0, "zg": 365.76},
        "C": {"alpha": 9.5, "zg": 274.32},
        "D": {"alpha": 11.5, "zg": 213.36},
    }
    params = _EXP_PARAMS[exposure]
    z_eff = max(h, 4.57)  # 15 ft minimum per ASCE 7
    Kz = 2.01 * (z_eff / params["zg"]) ** (2.0 / params["alpha"])

    # --- Velocity pressure at roof height (Eq. 26.10-1) ---
    qh = 0.613 * Kz * Kzt * Kd * V ** 2

    # --- GCp from curves ---
    GCp_pos = get_GCp(zone, A_eff, roof_type, "pos")
    GCp_neg = get_GCp(zone, A_eff, roof_type, "neg")
    GCpi = _GCPI[enclosure]

    # --- Net pressures (Eq. 30.3-1) ---
    # Worst positive: (+GCp) combined with (-GCpi)
    p_pos = qh * (GCp_pos - (-GCpi))
    # Worst suction: (-GCp) combined with (+GCpi)
    p_neg = qh * (GCp_neg - GCpi)

    # --- Minimum design pressure (Section 30.2.2) ---
    if 0 < p_pos < _MIN_DESIGN_PRESSURE_PA:
        p_pos = _MIN_DESIGN_PRESSURE_PA
    if -_MIN_DESIGN_PRESSURE_PA < p_neg < 0:
        p_neg = -_MIN_DESIGN_PRESSURE_PA

    return (round(p_pos, 1), round(p_neg, 1))


def get_cc_pressure_all_zones(
    roof_type: str,
    A_eff: float,
    h: float,
    exposure: str,
    V: float,
    Kd: float = 0.85,
    Kzt: float = 1.0,
    enclosure: str = "enclosed",
) -> dict[str, tuple[float, float]]:
    """
    Compute C&C pressures for all zones of a given surface type.

    Returns a dict mapping zone ID to (p_positive, p_negative) tuples.
    Useful for generating complete pressure tables for design.

    Parameters
    ----------
    Same as get_cc_pressure, but without `zone` (iterates all zones).

    Returns
    -------
    dict[str, tuple[float, float]]
        Mapping of zone -> (p_positive_Pa, p_negative_Pa).
    """
    zones = _valid_zones(roof_type)
    results: dict[str, tuple[float, float]] = {}
    for z in zones:
        results[z] = get_cc_pressure(
            z, roof_type, A_eff, h, exposure, V, Kd, Kzt, enclosure)
    return results


def pressure_vs_area_curve(
    zone: str,
    roof_type: str,
    h: float,
    exposure: str,
    V: float,
    Kd: float = 0.85,
    Kzt: float = 1.0,
    enclosure: str = "enclosed",
    n_points: int = 20,
) -> list[dict]:
    """
    Generate GCp and pressure curves as a function of effective wind area.

    Produces a list of points sampling the GCp curve from A_LO to A_HI,
    suitable for plotting the characteristic A-G curves of ASCE 7-22 Ch. 30.

    Parameters
    ----------
    zone : str
        C&C zone identifier.
    roof_type : str
        'wall' or 'flat'.
    h, exposure, V, Kd, Kzt, enclosure : same as get_cc_pressure.
    n_points : int
        Number of sample points along the area axis (default 20).

    Returns
    -------
    list[dict]
        Each dict has keys: A_eff_m2, GCp_pos, GCp_neg, p_pos_Pa, p_neg_Pa.
    """
    import numpy as np
    areas = np.logspace(
        math.log10(_A_LO_M2 * 0.5),
        math.log10(_A_HI_M2 * 1.5),
        n_points,
    )
    curve: list[dict] = []
    for A in areas:
        GCp_p = get_GCp(zone, float(A), roof_type, "pos")
        GCp_n = get_GCp(zone, float(A), roof_type, "neg")
        p_pos, p_neg = get_cc_pressure(
            zone, roof_type, float(A), h, exposure, V, Kd, Kzt, enclosure)
        curve.append({
            "A_eff_m2": round(float(A), 3),
            "GCp_pos": round(GCp_p, 4),
            "GCp_neg": round(GCp_n, 4),
            "p_pos_Pa": p_pos,
            "p_neg_Pa": p_neg,
        })
    return curve
