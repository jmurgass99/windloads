"""
vortex_shedding.py -- Vortex shedding lock-in and galloping checks.

Implements aeroelastic instability checks for slender structures following:
  - Eurocode EN 1991-1-4 Annex E (vortex shedding and galloping)
  - General structural dynamics references

Vortex Shedding
----------------
When wind flows past a bluff body, alternating vortices are shed at a
frequency f_s = St * V / D (Strouhal relationship). If f_s approaches
the natural frequency f_n of the structure, resonant oscillations occur
("lock-in").

Critical velocity for lock-in:
    V_cr = f_n * D / St

where:
    f_n  : natural frequency of the structure [Hz]
    D    : cross-wind dimension of the cross-section [m]
    St   : Strouhal number, EN 1991-1-4 Table E.1 (0.18 for circular sections at
           all Re; rectangles from Figure E.1, 0.12 for d/b = 1)

Scruton number (mass-damping parameter):
    Sc = 2 * m * delta_s / (rho * D^2)

where:
    m       : mass per unit length [kg/m]
    delta_s : logarithmic decrement of structural damping [-]
    rho     : air density [kg/m^3]

Resonant amplitude (EN 1991-1-4 Annex E.1):
    y_max = (1/St^2) * (1/Sc) * K * K_w * clat * D

where:
    K    : mode shape factor, Table E.5 (0.13 cantilever, 0.10 simply
           supported, 0.11 fixed-fixed); the default is 0.13
    K_w  : effective correlation length factor, Expression (E.8), <= 0.6
    clat : lateral force coefficient, Table E.2 / Figure E.2 (circular 0.7
           for Re <= 3e5, 0.2 for 5e5 to 5e6, 0.3 above 1e7; rectangle
           0.5 <= d/b <= 10: 1.1)

Galloping (EN 1991-1-4 Annex E.2)
----------------------------------
Galloping onset velocity (Expression E.18):
    V_CG = 2 * Sc * f_n * D / aG

where:
    aG : factor of galloping instability, Table E.7 (positive for sections
         prone to galloping; aG = 10 if unknown). Examples of Table E.7:
         rectangle d/b = 1: 1.2, d/b = 1.5: 1.7, d/b = 2: 2; d/b = 1/2: 0.7;
         ice on cables: 1.0; hexagon: 1.0.

EN 1991-1-4 E.2.2(2), Expression (E.19), requires V_CG > 1.25 * v_m.

Backward compatibility
-----------------------
The legacy API (VortexInput, evaluate_vortex_shedding) is retained at the
bottom of this module.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from .exceptions import ConfigurationError, GeometryError


# =========================================================================
# Default Strouhal numbers for common cross-sections
# =========================================================================
STROUHAL_NUMBERS: dict[str, float] = {
    # EN 1991-1-4 Table E.1: circular 0.18 (0.20 before 1.2.0), square
    # (d/b = 1, Figure E.1) 0.12. The other entries were not checked.
    "circular": 0.18,
    "square": 0.12,
    "rectangular": 0.12,
    "hexagonal": 0.14,
    "octagonal": 0.15,
    "H_section": 0.10,
    "L_section": 0.15,
}

# Lateral force coefficient clat for vortex-induced vibration amplitude
_CLAT: dict[str, float] = {
    "circular": 0.20,      # Figure E.2, 5e5 <= Re <= 5e6 (0.7 below 3e5)
    "square": 1.10,        # Table E.2, rectangle 0.5 <= d/b <= 10
    "rectangular": 1.10,   # Table E.2 (1.00 before 1.2.0)
    "hexagonal": 0.50,
    "octagonal": 0.40,
}


class VortexResult(NamedTuple):
    """Result of a vortex shedding assessment."""
    V_cr: float             # critical wind speed for lock-in [m/s]
    Sc: float               # Scruton number [-]
    lock_in: bool           # True if V_mean is within lock-in range
    V_range_lo: float       # lower bound of lock-in range [m/s]
    V_range_hi: float       # upper bound of lock-in range [m/s]
    y_max_m: float          # estimated resonant amplitude [m]
    y_over_D: float         # amplitude / diameter ratio [-]


class GallopingResult(NamedTuple):
    """Result of a galloping assessment."""
    V_CG: float             # onset velocity for galloping [m/s]
    Sc: float               # Scruton number [-]
    at_risk: bool           # True if V_CG <= 1.25*V_mean (E.19 not met)
    safety_ratio: float     # V_CG / (1.25*V_mean): >1 means E.19 is met


def _validate_positive(**kwargs: float) -> None:
    """Raise GeometryError if any value is not positive."""
    for name, val in kwargs.items():
        if val <= 0:
            raise GeometryError(f"{name} must be positive. Got {val}")


def scruton_number(m_per_m: float, delta_s: float, D: float,
                   rho_air: float = 1.25) -> float:
    """
    Scruton number (mass-damping parameter):
        Sc = 2 * m * delta_s / (rho * D^2)

    Parameters
    ----------
    m_per_m : float
        Mass per unit length [kg/m].
    delta_s : float
        Logarithmic decrement of structural damping [-].
    D : float
        Cross-wind dimension [m].
    rho_air : float
        Air density [kg/m^3] (default 1.25).

    Returns
    -------
    float : Scruton number (dimensionless).
    """
    _validate_positive(m_per_m=m_per_m, D=D, rho_air=rho_air)
    if delta_s < 0:
        raise ConfigurationError("Structural damping delta_s must be >= 0.")
    return 2.0 * m_per_m * delta_s / (rho_air * D ** 2)


def critical_velocity(fn: float, D: float, St: float = 0.18) -> float:
    """
    Critical wind speed for vortex shedding lock-in:
        V_cr = f_n * D / St

    Parameters
    ----------
    fn : float
        Natural frequency of the structure [Hz].
    D : float
        Cross-wind dimension [m].
    St : float
        Strouhal number (default 0.18, circular sections, EN 1991-1-4 Table E.1).

    Returns
    -------
    float : critical velocity [m/s].
    """
    _validate_positive(fn=fn, D=D, St=St)
    return fn * D / St


def check_vortex_shedding(
    D: float,
    fn: float,
    V: float,
    m_per_m: float,
    delta_s: float,
    rho_air: float = 1.25,
    St: float = 0.18,
    section: str = "circular",
    K: float = 0.13,
    K_w: float = 0.6,
    clat: float | None = None,
) -> VortexResult:
    """
    Complete vortex shedding lock-in check per EN 1991-1-4 Annex E.

    Parameters
    ----------
    D : float
        Cross-wind dimension of the cross section [m].
    fn : float
        Natural frequency of the structure [Hz].
    V : float
        Mean wind speed at the structure height [m/s].
    m_per_m : float
        Mass per unit length [kg/m].
    delta_s : float
        Logarithmic decrement of structural damping [-].
        Typical: steel 0.01-0.02, concrete 0.02-0.05, composite 0.03.
    rho_air : float
        Air density [kg/m^3] (default 1.25).
    St : float
        Strouhal number (default 0.18 for circular sections, Table E.1).
    section : str
        Cross-section shape for clat lookup: 'circular', 'square',
        'rectangular', 'hexagonal', 'octagonal'.
    K : float
        Mode shape factor of EN 1991-1-4 Table E.5: 0.13 for a cantilever in
        its first mode (default), 0.10 simply supported, 0.11 fixed-fixed.
        Before 1.2.0 the default was 1.0, which overstated y_max 7.7 times.
    K_w : float
        Effective correlation length factor, Expression (E.8): <= 0.6
        (default 0.6, the upper bound).
    clat : float, optional
        Lateral force coefficient. If None it is taken from ``section``:
        circular 0.2 (Figure E.2, valid only for 5e5 <= Re <= 5e6; it is 0.7
        for Re <= 3e5), rectangular/square 1.1 (Table E.2). Pass the value of
        Figure E.2 / Table E.3 for the actual Reynolds number and v_crit/v_m.

    Returns
    -------
    VortexResult
        Named tuple with V_cr, Sc, lock_in flag, lock-in range,
        estimated amplitude y_max, and y/D ratio.
    """
    _validate_positive(D=D, fn=fn, V=V, m_per_m=m_per_m, rho_air=rho_air, St=St)

    V_cr = critical_velocity(fn, D, St)
    Sc = scruton_number(m_per_m, delta_s, D, rho_air)

    # Lock-in range: typically +/- 20% of V_cr for circular,
    # wider for sharp-edged sections.
    # EN 1991-1-4 E.1.3.2: range is approximately 0.8*V_cr to 1.2*V_cr
    # For low Scruton numbers, the range can widen.
    bandwidth = 0.3 if Sc < 5 else 0.2
    V_lo = V_cr * (1.0 - bandwidth)
    V_hi = V_cr * (1.0 + bandwidth)

    lock_in = V_lo <= V <= V_hi

    # Resonant amplitude (EN 1991-1-4 Annex E.1, Eq. E.7)
    # y_max = (1/St^2) * (1/Sc) * K * K_w * clat * D
    if clat is None:
        clat = _CLAT.get(section, 0.20)
    if Sc > 0:
        y_max = (1.0 / St ** 2) * (1.0 / Sc) * K * K_w * clat * D
    else:
        # Sc = 0 means no damping: amplitude is theoretically infinite
        y_max = float("inf")

    y_over_D = y_max / D if D > 0 else float("inf")

    return VortexResult(
        V_cr=round(V_cr, 3),
        Sc=round(Sc, 3),
        lock_in=lock_in,
        V_range_lo=round(V_lo, 3),
        V_range_hi=round(V_hi, 3),
        y_max_m=round(y_max, 6),
        y_over_D=round(y_over_D, 6),
    )


def check_galloping(
    D: float,
    fn: float,
    V: float,
    m_per_m: float,
    delta_s: float,
    aG: float,
    rho_air: float = 1.25,
) -> GallopingResult:
    """
    Galloping onset check per EN 1991-1-4 Annex E.2.

    Galloping is an aeroelastic instability where a non-circular section
    oscillates transversely with increasing amplitude once the wind speed
    exceeds the critical galloping velocity V_CG.

    Parameters
    ----------
    D : float
        Cross-wind dimension of the cross section [m].
    fn : float
        Natural frequency of the structure [Hz].
    V : float
        Mean wind speed at the structure height [m/s].
    m_per_m : float
        Mass per unit length [kg/m].
    delta_s : float
        Logarithmic decrement of structural damping [-].
    aG : float
        Factor of galloping instability of EN 1991-1-4 Table E.7 (positive
        for sections prone to galloping). Examples: rectangle d/b = 1: 1.2,
        d/b = 2: 2, d/b = 1/2: 0.7; ice on cables: 1.0; aG = 10 when no
        value is known (E.2.2(1)).
    rho_air : float
        Air density [kg/m^3] (default 1.25).

    Returns
    -------
    GallopingResult
        Named tuple with V_CG, Sc, at_risk flag and safety ratio. ``at_risk``
        is True when Expression (E.19), V_CG > 1.25·v_m, is NOT met; before
        1.2.0 it only compared V_CG with v_m (without the 1.25 margin).

    Notes
    -----
    The den Hartog criterion states that galloping occurs when the
    aerodynamic derivative dC_L/d_alpha + C_D < 0, which is captured
    by the factor aG. The onset velocity is:

        V_CG = 2 * Sc * f_n * D / aG

    If V_mean >= V_CG, galloping oscillations will grow unbounded (in
    linear theory) until limited by nonlinear effects.
    """
    _validate_positive(D=D, fn=fn, V=V, m_per_m=m_per_m, rho_air=rho_air)
    if aG <= 0:
        raise ConfigurationError(
            "Galloping factor aG must be positive. "
            "If aG <= 0, the section is aerodynamically stable against galloping.")

    Sc = scruton_number(m_per_m, delta_s, D, rho_air)

    # EN 1991-1-4 Annex E.2, Eq. E.18
    V_CG = 2.0 * Sc * fn * D / aG

    # EN 1991-1-4 E.2.2(2), Expression (E.19): V_CG > 1.25 * v_m
    at_risk = V_CG <= 1.25 * V
    safety_ratio = V_CG / (1.25 * V) if V > 0 else float("inf")

    return GallopingResult(
        V_CG=round(V_CG, 3),
        Sc=round(Sc, 3),
        at_risk=at_risk,
        safety_ratio=round(safety_ratio, 3),
    )


# =========================================================================
# Legacy backward-compatible API
# =========================================================================
# Retained for backward compatibility with existing callers that used
# the original VortexInput / evaluate_vortex_shedding interface.

ST_TABLE = {
    "circular": 0.18,
    "square_sharp": 0.12,
    "rectangular_2_1": 0.06,
    "octagonal": 0.18,
}


@dataclass(frozen=True)
class VortexInput:
    """Legacy input dataclass (retained for backward compat)."""
    D_m: float
    f1_Hz: float
    Vb_m_s: float
    section_shape: str = "circular"
    damping_ratio_logarithmic: float = 0.012
    m_e_kg_m: float = 100.0


@dataclass(frozen=True)
class _LegacyVortexResult:
    """Legacy result dataclass (retained for backward compat)."""
    v_critical_m_s: float
    is_in_resonance_band: bool
    Sc_scruton: float
    galloping_risk: bool


def evaluate_vortex_shedding(inp: VortexInput) -> _LegacyVortexResult:
    """Legacy entry point (retained for backward compat)."""
    if inp.D_m <= 0 or inp.f1_Hz <= 0 or inp.Vb_m_s <= 0:
        raise ValueError("Parametros geometricos y de viento deben ser > 0")
    St = ST_TABLE.get(inp.section_shape, 0.18)
    v_crit = inp.f1_Hz * inp.D_m / St
    in_band = 0.5 <= (v_crit / inp.Vb_m_s) <= 1.25

    rho_air = 1.25
    m_e = inp.m_e_kg_m
    Sc = 2.0 * inp.damping_ratio_logarithmic * m_e / (rho_air * inp.D_m ** 2)

    a_g = -3.0
    v_crit_gallop = 2 * Sc * inp.f1_Hz * inp.D_m / abs(a_g)
    gallop_risk = v_crit_gallop < inp.Vb_m_s

    return _LegacyVortexResult(
        v_critical_m_s=v_crit, is_in_resonance_band=in_band,
        Sc_scruton=Sc, galloping_risk=gallop_risk,
    )


__all__ = [
    # New API
    "STROUHAL_NUMBERS",
    "VortexResult",
    "GallopingResult",
    "scruton_number",
    "critical_velocity",
    "check_vortex_shedding",
    "check_galloping",
    # Legacy API
    "VortexInput",
    "ST_TABLE",
    "evaluate_vortex_shedding",
]
