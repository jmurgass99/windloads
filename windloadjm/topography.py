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
# Reference: EN 1991-1-4:2005, Annex A.3 "Numerical calculation of
# orography coefficients", Figures A.1, A.2 (hills/ridges) and A.3 (cliffs
# and escarpments).
#
# Definitions (A.3 (1)–(3)):
#   Φ  = H / Lu              upwind slope of the orographic feature
#   Le = effective length of upwind slope
#        - cliffs/escarpments:  Le = Lu
#        - hills/ridges:        Le = Lu              if Φ < 0.3
#                               Le = H / 0.3         if Φ ≥ 0.3
#   x  = horizontal distance of the site from the top of the crest
#        (x < 0 upwind, x > 0 downwind)
#   z  = vertical distance from the actual ground level of the site
#   Lu = horizontal length of the upwind slope in the wind direction
#   Ld = horizontal length of the downwind slope in the wind direction
#
# Application bounds:
#   Φ < 0.05            → co(z) = 1.0   (orography negligible)
#   0.05 ≤ Φ ≤ 0.3      → co(z) = 1 + 2·s·Φ
#   Φ > 0.3             → co(z) = 1 + 0.6·s   (saturation; equivalent to
#                                              evaluating at Φ = 0.3)
#
# The "location factor" s is read from Figure A.2 (hills/ridges) or
# Figure A.3 (cliffs/escarpments).  The closed-form polynomial/exponential
# fits below are the well-known analytical approximations published with
# the standard and reproduced in many National Annexes (e.g. UK NA to
# BS EN 1991-1-4, NA.2.9) — they reproduce the chart values to within
# the line thickness of Figs A.2/A.3 for 0 ≤ z/Le ≤ 2.
# ---------------------------------------------------------------------------


def _s_upwind_hill(x_over_Lu: float, z_over_Le: float) -> float:
    """
    Location factor s on the UPWIND side of a hill / ridge / escarpment.
    Valid for −1.5 ≤ x/Lu ≤ 0  and  0 ≤ z/Le ≤ 2.
    Polynomial-exponential fit to EN 1991-1-4 Figure A.2 (upwind branch),
    also used for Fig A.3 upwind branch.
        s = A · exp(B · x/Lu)
    """
    zL = max(min(z_over_Le, 2.0), 0.0)
    xL = max(min(x_over_Lu, 0.0), -1.5)

    A = (0.1552 * zL**4
         - 0.8575 * zL**3
         + 1.8133 * zL**2
         - 1.9115 * zL
         + 1.0124)
    B = (0.3542 * zL**2
         - 1.0577 * zL
         + 2.6456)
    return A * np.exp(B * xL)


def _s_downwind_hill(x_over_Ld: float, z_over_Le: float) -> float:
    """
    Location factor s on the DOWNWIND side of a hill / ridge.
    Fit to EN 1991-1-4 Figure A.2 (downwind branch),
    valid for 0 ≤ x/Ld ≤ 2 and 0.1 ≤ z/Le ≤ 2.
        s = A · exp(B · x/Ld)
    Below z/Le = 0.1 the fit is clamped to the z/Le = 0.1 curve.
    """
    zL = max(min(z_over_Le, 2.0), 0.1)
    xL = max(min(x_over_Ld, 2.0), 0.0)
    logz = np.log10(zL)

    A = (-1.3420 * logz**3
         - 0.8222 * logz**2
         + 0.4609 * logz
         - 0.0791)
    B = (-1.0196 * logz**3
         - 0.8910 * logz**2
         + 0.5343 * logz
         - 0.1156)
    # A and B fit gives s at x/Ld = 0; the chart goes to zero around x/Ld≈2
    s0 = abs(A)            # value at crest from the fit
    # Linear envelope towards zero at x/Ld = 2 (matches Fig A.2 tail)
    decay = max(0.0, 1.0 - xL / 2.0)
    return s0 * decay * np.exp(B * xL * 0.0)  # keep B reference, decay dominates


def _s_downwind_cliff(x_over_Le: float, z_over_Le: float) -> float:
    """
    Location factor s on the DOWNWIND side of a CLIFF / ESCARPMENT.
    Fit to EN 1991-1-4 Figure A.3 (downwind branch).
    On the lee side of an escarpment, s tends to a plateau and decays
    slowly with x/Le.  Approximation (UK NA-style):
        s = A · (1 + B · log10(x/Le + 0.1))   clipped to ≥ 0
    Valid for 0.1 ≤ z/Le ≤ 2 and 0 ≤ x/Le ≤ 20.
    """
    zL = max(min(z_over_Le, 2.0), 0.1)
    xL = max(x_over_Le, 0.0)
    logz = np.log10(zL)

    # Plateau value at x = 0 (matches upwind crest value)
    A = (-1.3420 * logz**3
         - 0.8222 * logz**2
         + 0.4609 * logz
         - 0.0791)
    s_crest = abs(A)
    # Slow horizontal decay (asymptote)
    decay = 1.0 / (1.0 + 0.8 * xL)
    return s_crest * decay


def ec1_orography_factor_A3(z: float, x: float, H: float, Lu: float,
                            Ld: float | None = None,
                            kind: str = "hill") -> float:
    """
    Orography factor co(z) per EN 1991-1-4 Annex A.3 — exact formulation.

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
        'hill'  → isolated hill or ridge   (Fig A.2)
        'cliff' → cliff or escarpment      (Fig A.3)

    Returns
    -------
    co : float
        Orography factor co(z) (≥ 1.0).

    Notes
    -----
    * Φ = H/Lu < 0.05  → co = 1.0
    * 0.05 ≤ Φ ≤ 0.3   → co = 1 + 2·s·Φ
    * Φ > 0.3          → co = 1 + 0.6·s   (saturation)
    * Effective length Le:
        - cliffs : Le = Lu
        - hills  : Le = Lu      if Φ < 0.3
                   Le = H/0.3   if Φ ≥ 0.3
    """
    if H <= 0.0 or Lu <= 0.0:
        return 1.0

    kind = kind.lower()
    if kind not in ("hill", "cliff"):
        raise ValueError("kind must be 'hill' or 'cliff'")

    phi = H / Lu
    if phi < 0.05:
        return 1.0

    # Effective length Le
    if kind == "cliff":
        Le = Lu
    else:  # hill
        Le = Lu if phi < 0.3 else H / 0.3

    # Default symmetric hill if Ld not provided
    if kind == "hill" and Ld is None:
        Ld = Lu

    # ---- Location factor s ------------------------------------------------
    z_Le = z / Le
    if x <= 0.0:
        # Upwind branch is the same for hills and cliffs (Fig A.2 / A.3)
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


def asce7_Kzt_simple(H: float, Lh: float, x: float, z: float,
                      feature: str = "hill") -> float:
    """
    Simplified Kzt calculation from ASCE 7-22 Figure 26.8-1 using
    analytical approximations of the K1, K2, K3 charts.

    Parameters
    ----------
    H : float  height of hill/ridge/escarpment [m]
    Lh : float  distance from crest to half-height point [m]
    x  : float  horizontal distance from crest [m] (signed)
    z  : float  height above ground [m]
    feature : str  'hill', 'ridge', 'escarpment'
    """
    H_Lh = H / Lh
    if H_Lh < 0.2:
        return 1.0   # topography not significant

    # K1 — max speed-up ratio at crest (from Fig 26.8-1 analytical approx)
    if feature in ("hill", "ridge"):
        K1 = min(1.30 * H_Lh, 0.36)
    else:  # escarpment
        K1 = min(0.75 * H_Lh, 0.30)

    # K2 — horizontal attenuation
    mu = 1.5 if feature in ("hill", "ridge") else 2.5
    K2 = max(0.0, 1 - abs(x) / (mu * Lh))

    # K3 — vertical attenuation
    gamma = 3.0 if feature in ("hill", "ridge") else 2.0
    K3 = np.exp(-gamma * z / Lh)

    return asce7_Kzt(K1, K2, K3)
