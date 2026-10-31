"""Punto 18 - Memoria Mathcad-style: factor de rafaga G_f (Davenport).

ASCE 7-22 Eq. 26.11-10 para estructuras flexibles (T > 1 s). Reutiliza el
calculo canonico ``windloads.davenport.gust_factor_davenport`` para Q (fondo)
y R (resonante), y re-expresa la ecuacion final de G_f con handcalcs. El valor
reportado proviene de la misma formula renderizada (latex y numero coinciden) y
los tests verifican que iguala al motor canonico (anti-deriva).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log, sqrt
from typing import List

try:
    from handcalcs.decorator import handcalc
    _HAS_HANDCALCS = True
except ImportError:  # pragma: no cover - entorno sin handcalcs
    _HAS_HANDCALCS = False

    def handcalc(*args, **kwargs):
        def deco(f):
            return f
        return deco

from windloads.davenport import DavenportInput, gust_factor_davenport


@dataclass
class GustFactorMemoResult:
    """Factor de rafaga G_f y componentes de respuesta."""
    G_f: float
    Q: float          # respuesta de fondo (background)
    R: float          # respuesta resonante
    latex: str = ""
    notes: List[str] = field(default_factory=list)


@handcalc(override="long", precision=4)
def _gust_factor_eq(I_z, Q, R, g_Q, g_R, g_v):
    g_RQ = (g_Q ** 2 * Q ** 2 + g_R ** 2 * R ** 2) ** 0.5
    G_f = 0.925 * (1.0 + 1.7 * I_z * g_RQ) / (1.0 + 1.7 * g_v * I_z)
    return G_f


def gust_factor_memo(
    natural_period_s: float,
    height_m: float,
    damping_ratio: float = 0.01,
    intensity_turbulence: float = 0.30,
    Lz_m: float = 100.0,
    Vz_m_per_s: float = 35.0,
):
    """Genera la memoria del factor de rafaga G_f (Davenport, ASCE 7-22).

    Args:
        natural_period_s: periodo fundamental de la estructura [s] (> 0).
        height_m: altura de referencia [m] (> 0).
        damping_ratio: razon de amortiguamiento (0.01 acero tipico).
        intensity_turbulence: intensidad de turbulencia I_z.
        Lz_m: escala integral de turbulencia [m].
        Vz_m_per_s: velocidad media a la altura de referencia [m/s].

    Returns:
        ``(latex, GustFactorMemoResult)`` siguiendo el patron de memos de
        WindLoads.
    """
    if natural_period_s <= 0:
        raise ValueError("natural_period_s debe ser > 0")
    if height_m <= 0:
        raise ValueError("height_m debe ser > 0")
    if damping_ratio <= 0:
        raise ValueError("damping_ratio debe ser > 0")

    inp = DavenportInput(
        natural_period_s=natural_period_s,
        height_m=height_m,
        damping_ratio=damping_ratio,
        intensity_turbulence=intensity_turbulence,
        Lz_m=Lz_m,
        Vz_m_per_s=Vz_m_per_s,
    )
    res = gust_factor_davenport(inp)  # Q, R canonicos

    # Factores pico identicos a davenport.py (g_Q = g_v = 3.4; g_R cerrado)
    f1 = 1.0 / natural_period_s
    g_Q = 3.4
    g_v = 3.4
    g_R = sqrt(2.0 * log(3600.0 * f1)) + 0.5772 / sqrt(2.0 * log(3600.0 * f1))

    out = _gust_factor_eq(
        intensity_turbulence, res.Q_background, res.R_resonant, g_Q, g_R, g_v
    )
    latex, G_f_val = out if _HAS_HANDCALCS else ("", out)

    result = GustFactorMemoResult(
        G_f=float(G_f_val),
        Q=float(res.Q_background),
        R=float(res.R_resonant),
        latex=latex,
        notes=[
            f"f_1 = 1/T = {f1:.4f} Hz",
            f"Q (fondo) = {res.Q_background:.4f}, R (resonante) = {res.R_resonant:.4f}",
            f"g_R = {g_R:.4f} (g_Q = g_v = 3.4)",
            f"G_f = {G_f_val:.4f}",
        ],
    )
    return latex, result


__all__ = ["GustFactorMemoResult", "gust_factor_memo"]
