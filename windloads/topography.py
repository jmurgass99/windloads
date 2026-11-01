"""
topography.py — Topographic factors for wind load calculations.

EC1-1-4 §4.3.3 and Annex A.3 — Orography factor co(z)
ASCE 7-22 §26.8                — Topographic factor Kzt
"""
from __future__ import annotations
import warnings
import numpy as np


# ---------------------------------------------------------------------------
# EN 1991-1-4 Annex A.3 — Orography factor co(z)
# ---------------------------------------------------------------------------
# Reference: EN 1991-1-4:2005+A1:2010, Annex A.3 "Numerical calculation of
# orography coefficients": Expressions (A.1)-(A.3) for co, Table A.2 for the
# effective length Le, Figure A.2 (cliffs and escarpments), Figure A.3 (hills
# and ridges) and the empirical Expressions (A.4)-(A.13) for the location
# factor s, which this module implements literally:
#
#   Φ  = H / Lu              upwind slope of the orographic feature
#   Le = Lu        if 0.05 < Φ < 0.3 (shallow)
#   Le = H / 0.3   if Φ > 0.3        (steep)        — Table A.2, any feature
#   x  = horizontal distance of the site from the top of the crest
#        (x < 0 upwind, x > 0 downwind)
#   z  = vertical distance from the ground level of the site
#
#   co = 1                 for Φ < 0.05      (A.1)
#   co = 1 + 2·s·Φ         for 0.05 < Φ < 0.3 (A.2)
#   co = 1 + 0.6·s         for Φ > 0.3       (A.3)
#
# Before 1.2.0 the downwind branches were not the EN expressions: the hill
# branch used the cliff coefficient A of (A.8) with a linear decay (s ≈ 0.02
# just downwind of the crest near the ground instead of s ≈ 1.0), the cliff
# branch used 1/(1 + 0.8·x/Le), and cliffs always took Le = Lu.
# ---------------------------------------------------------------------------


def _A_crest(z_over_Le: float) -> float:
    """Expression (A.5) = (A.12): s at the crest as a function of z/Le."""
    zL = z_over_Le
    return (0.1552 * zL**4
            - 0.8575 * zL**3
            + 1.8133 * zL**2
            - 1.9115 * zL
            + 1.0124)


def _s_upwind_hill(x_over_Lu: float, z_over_Le: float) -> float:
    """
    Location factor s on the UPWIND side of any orography, Expressions
    (A.4)-(A.6): s = A·exp(B·X/Lu) for -1.5 <= X/Lu <= 0 and 0 <= z/Le <= 2;
    s = 0 for X/Lu < -1.5 or z/Le > 2.
    """
    if x_over_Lu < -1.5 or z_over_Le > 2.0:
        return 0.0
    zL = max(z_over_Le, 0.0)
    xL = min(x_over_Lu, 0.0)
    A = _A_crest(zL)
    B = (0.3542 * zL**2
         - 1.0577 * zL
         + 2.6456)
    return float(A * np.exp(B * xL))


def _s_downwind_hill(x_over_Ld: float, z_over_Le: float) -> float:
    """
    Location factor s on the DOWNWIND side of a hill or ridge, Expressions
    (A.11)-(A.13): s = A·exp(B·X/Ld) with A from (A.12) and
    B = -0.3056·(z/Le)² + 1.0212·(z/Le) - 1.7637, for 0 <= X/Ld <= 2 and
    0 <= z/Le <= 2; s = 0 for X/Ld > 2 or z/Le > 2.
    """
    if x_over_Ld > 2.0 or z_over_Le > 2.0:
        return 0.0
    zL = max(z_over_Le, 0.0)
    xL = max(x_over_Ld, 0.0)
    A = _A_crest(zL)
    B = (-0.3056 * zL**2
         + 1.0212 * zL
         - 1.7637)
    return float(A * np.exp(B * xL))


def _s_cliff_downwind_A7(x_over_Le: float, z_over_Le: float) -> float:
    """Expression (A.7) with (A.8)-(A.10), log = log10, z/Le >= 0.1."""
    lz = np.log10(max(z_over_Le, 0.1))
    lx = np.log10(x_over_Le)
    A = (-1.3420 * lz**3 - 0.8222 * lz**2 + 0.4609 * lz - 0.0791)
    B = (-1.0196 * lz**3 - 0.8910 * lz**2 + 0.5343 * lz - 0.1156)
    C = (0.8030 * lz**3 + 0.4236 * lz**2 - 0.5738 * lz + 0.1606)
    return float(A * lx**2 + B * lx + C)


def _s_downwind_cliff(x_over_Le: float, z_over_Le: float) -> float:
    """
    Location factor s on the DOWNWIND side of a cliff or escarpment,
    Expressions (A.7)-(A.10), valid for 0.1 <= X/Le <= 3.5 and
    0.1 <= z/Le <= 2 (values for z/Le = 0.1 are used below it).
    For 0 <= X/Le < 0.1 it interpolates linearly between X/Le = 0, where
    s = A of (A.5) (evaluated here at the actual z/Le, continuous with the
    upwind branch at the crest), and X/Le = 0.1. s = 0 for X/Le > 3.5 or
    z/Le > 2.
    """
    if x_over_Le > 3.5 or z_over_Le > 2.0:
        return 0.0
    xL = max(x_over_Le, 0.0)
    if xL >= 0.1:
        return _s_cliff_downwind_A7(xL, z_over_Le)
    s0 = _A_crest(max(z_over_Le, 0.0))
    s01 = _s_cliff_downwind_A7(0.1, z_over_Le)
    return float(s0 + (s01 - s0) * xL / 0.1)


def ec1_orography_factor_A3(z: float, x: float, H: float, Lu: float,
                            Ld: float | None = None,
                            kind: str = "hill") -> float:
    """
    Orography factor co(z) per EN 1991-1-4 Annex A.3, Expressions (A.1)-(A.13).

    Parameters
    ----------
    z : float
        Vertical distance from the actual ground level of the site [m].
    x : float
        Horizontal distance of the site from the top of the crest [m]
        (x < 0 upwind, x > 0 downwind).
    H : float
        Effective height of the orographic feature [m].
    Lu : float
        Length of the upwind slope in the wind direction [m].
    Ld : float, optional
        Length of the downwind slope in the wind direction [m].
        Required for `kind='hill'` when x > 0.  If None and kind='hill',
        a symmetric feature (Ld = Lu) is assumed.  For cliffs/escarpments
        Ld is not used.
    kind : {'hill', 'cliff'}
        'hill'  → isolated hill or ridge   (Fig A.3)
        'cliff' → cliff or escarpment      (Fig A.2)

    Returns
    -------
    co : float
        Orography factor co(z) (≥ 1.0).

    Notes
    -----
    * Φ = H/Lu < 0.05  → co = 1.0
    * 0.05 ≤ Φ ≤ 0.3   → co = 1 + 2·s·Φ
    * Φ > 0.3          → co = 1 + 0.6·s   (saturation)
    * Effective length Le (Table A.2): Le = Lu if Φ < 0.3, Le = H/0.3 if Φ ≥ 0.3
    * s from Expressions (A.4)-(A.13): upwind (any feature), downwind of a
      cliff/escarpment (Figure A.2), downwind of a hill/ridge (Figure A.3).
    """
    if H <= 0.0 or Lu <= 0.0:
        return 1.0

    kind = kind.lower()
    if kind not in ("hill", "cliff"):
        raise ValueError("kind must be 'hill' or 'cliff'")

    phi = H / Lu
    if phi < 0.05:
        return 1.0

    # Effective length Le — EN 1991-1-4 Table A.2 (same for every feature)
    Le = Lu if phi < 0.3 else H / 0.3

    # Default symmetric hill if Ld not provided
    if kind == "hill" and Ld is None:
        Ld = Lu

    # ---- Location factor s ------------------------------------------------
    z_Le = z / Le
    if x <= 0.0:
        # Upwind branch is the same for hills and cliffs (A.4)-(A.6)
        s = _s_upwind_hill(x / Lu, z_Le)
    else:
        if kind == "hill":
            s = _s_downwind_hill(x / Ld, z_Le)
        else:  # cliff / escarpment, downwind (lee) side
            s = _s_downwind_cliff(x / Le, z_Le)

    s = max(s, 0.0)

    # ---- co(z) with EC1 bounds -------------------------------------------
    if phi <= 0.3:
        co = 1.0 + 2.0 * s * phi
    else:
        co = 1.0 + 0.6 * s          # saturation for Φ > 0.3

    return max(1.0, float(co))


# ---------------------------------------------------------------------------
# Backwards-compatible wrapper for the previous (linearised) API
# ---------------------------------------------------------------------------
def ec1_orography_factor(phi: float, x: float, z: float,
                          Lu: float, H: float,
                          feature: str = "hill") -> float:
    """
    Deprecated linearised orography factor (kept for backwards compatibility).

    The exact EN 1991-1-4 Annex A.3 implementation is
    :func:`ec1_orography_factor_A3`.  This wrapper now delegates to it,
    mapping the legacy argument order/`feature` keyword.

    Parameters retained:
        phi     — kept only for API compatibility; the real Φ is recomputed
                  inside as H/Lu (EC1 definition).  A warning is issued if
                  the supplied `phi` deviates significantly from H/Lu.
        feature — 'hill' or 'escarpment' (mapped to 'cliff').
    """
    warnings.warn(
        "ec1_orography_factor(phi, x, z, Lu, H, feature) is deprecated; "
        "use ec1_orography_factor_A3(z, x, H, Lu, Ld, kind) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    kind = "cliff" if feature.lower().startswith("esc") else "hill"
    phi_true = H / Lu if Lu > 0 else 0.0
    if phi > 0 and abs(phi - phi_true) / max(phi_true, 1e-9) > 0.25:
        warnings.warn(
            f"Supplied phi={phi:.3f} differs from H/Lu={phi_true:.3f}; "
            "using H/Lu per EN 1991-1-4 §A.3.",
            UserWarning,
            stacklevel=2,
        )
    return ec1_orography_factor_A3(z=z, x=x, H=H, Lu=Lu, Ld=Lu, kind=kind)


# ---------------------------------------------------------------------------
# ASCE 7-22 §26.8 — Topographic factor Kzt
# For hills, ridges, and escarpments
# ---------------------------------------------------------------------------
def asce7_Kzt(K1: float, K2: float, K3: float) -> float:
    """
    Topographic factor Kzt (ASCE 7-22 Eq. 26.8-1):
      Kzt = (1 + K1·K2·K3)²

    Parameters
    ----------
    K1 : float  from Figure 26.8-1 (depends on H/Lh and feature type)
    K2 : float  from Figure 26.8-1 (depends on x/Lh)
    K3 : float  from Figure 26.8-1 (depends on z/Lh)

    Returns
    -------
    Kzt : float  (≥ 1.0)

    Usage
    -----
    For flat terrain use Kzt = 1.0 directly.
    For hilly terrain, read K1, K2, K3 from ASCE 7 Figure 26.8-1.
    """
    return (1 + K1 * K2 * K3) ** 2


# ASCE 7-10 Fig. 26.8-1 (same parameters in ASCE 7-16 / 7-22 Fig. 26.8-1):
# K1/(H/Lh) by exposure, gamma, mu upwind / downwind of the crest.
_KZT_PARAMS: dict[str, dict] = {
    "ridge":      {"K1": {"B": 1.30, "C": 1.45, "D": 1.55}, "gamma": 3.0,
                   "mu_up": 1.5, "mu_down": 1.5},
    "escarpment": {"K1": {"B": 0.75, "C": 0.85, "D": 0.95}, "gamma": 2.5,
                   "mu_up": 1.5, "mu_down": 4.0},
    "hill":       {"K1": {"B": 0.95, "C": 1.05, "D": 1.15}, "gamma": 4.0,
                   "mu_up": 1.5, "mu_down": 1.5},
}


def asce7_Kzt_simple(H: float, Lh: float, x: float, z: float,
                      feature: str = "hill", exposure: str = "C") -> float:
    """
    Kzt from the equations of ASCE 7 Fig. 26.8-1:

        K1 = [K1/(H/Lh)]·(H/Lh),  K2 = 1 − |x|/(μ·Lh),  K3 = exp(−γ·z/Lh)
        Kzt = (1 + K1·K2·K3)²

    with the parameters of the figure (ASCE 7-10; the 7-16 and 7-22 figures
    were not consulted here):

        feature        K1/(H/Lh) B / C / D   γ     μ upwind  μ downwind
        'ridge'        1.30 / 1.45 / 1.55    3     1.5       1.5
        'escarpment'   0.75 / 0.85 / 0.95    2.5   1.5       4
        'hill'         0.95 / 1.05 / 1.15    4     1.5       1.5   (3-D axisym.)

    For H/Lh > 0.5, H/Lh = 0.5 is used for K1 and Lh = 2H for K2 and K3
    (Note 2). Kzt = 1 when H/Lh < 0.2 or H < 4.5 m (C, D) / 18 m (B)
    (§26.8.1 conditions 4 and 5; conditions 1-3 about isolation and location
    are the user's responsibility).

    Parameters
    ----------
    H : float  height of hill/ridge/escarpment relative to upwind terrain [m]
    Lh : float  distance upwind of crest to half-height [m]
    x  : float  horizontal distance from crest [m] (negative upwind, positive downwind)
    z  : float  height above local ground [m]
    feature : 'hill' (3-D axisymmetrical), 'ridge' (2-D) or 'escarpment' (2-D)
    exposure : 'B', 'C' or 'D'

    Before 1.2.0 this function capped K1 at 0.36 (ridge/hill) or 0.30
    (escarpment), treated a 3-D hill as a 2-D ridge, used γ = 2 and μ = 2.5
    for escarpments, ignored the exposure (Exposure B coefficients) and the
    H/Lh > 0.5 rule.
    """
    feature = feature.lower()
    if feature not in _KZT_PARAMS:
        raise ValueError("feature must be 'hill', 'ridge' or 'escarpment'")
    exposure = exposure.upper()
    if exposure not in ("B", "C", "D"):
        raise ValueError("exposure must be 'B', 'C' or 'D'")
    if H <= 0 or Lh <= 0:
        return 1.0
    H_min = 18.0 if exposure == "B" else 4.5
    H_Lh = H / Lh
    if H_Lh < 0.2 or H < H_min:
        return 1.0   # topography not significant (§26.8.1)

    p = _KZT_PARAMS[feature]
    if H_Lh > 0.5:
        H_Lh_K1 = 0.5
        Lh_eff = 2.0 * H
    else:
        H_Lh_K1 = H_Lh
        Lh_eff = Lh
    K1 = p["K1"][exposure] * H_Lh_K1
    mu = p["mu_down"] if x > 0 else p["mu_up"]
    K2 = max(0.0, 1.0 - abs(x) / (mu * Lh_eff))
    K3 = float(np.exp(-p["gamma"] * max(z, 0.0) / Lh_eff))
    return asce7_Kzt(K1, K2, K3)
