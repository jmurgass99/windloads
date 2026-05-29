"""Punto 44 - Memoria Mathcad-style: presion de viento EC1 (EN 1991-1-4 §4.5).

Contraparte europea de la memoria MWFRS (ASCE). Presion basica de velocidad
``q_b = 0.5*rho*v_b^2`` y presion pico ``q_p(z) = c_e(z)*q_b``. El factor de
exposicion c_e (EN 1991-1-4 Fig. 4.2, funcion de la categoria de terreno y la
altura) se recibe como entrada para no duplicar la maquinaria de terreno del
calculador ``EC1WindLoad``.

Unidades: rho en kg/m^3, v_b en m/s, presiones en Pa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class EC1PressureMemoResult:
    """Presiones de viento EC1."""
    q_b_Pa: float       # presion basica de velocidad
    q_p_Pa: float       # presion pico de velocidad q_p(z)
    rho: float
    v_b: float
    c_e: float
    latex: str = ""
    notes: List[str] = field(default_factory=list)


@handcalc(override="long", precision=3)
def _ec1_pressure_calc(rho, v_b, c_e):
    q_b = 0.5 * rho * v_b ** 2
    q_p = c_e * q_b
    return q_b, q_p


def ec1_peak_pressure_memo(v_b: float, c_e: float, rho: float = 1.25):
    """Genera la memoria de presion de viento EC1 (EN 1991-1-4 §4.5).

    Args:
        v_b: velocidad basica del viento [m/s] (> 0).
        c_e: factor de exposicion c_e(z) (EN 1991-1-4 Fig. 4.2) (> 0).
        rho: densidad del aire [kg/m^3] (1.25 recomendado).

    Returns:
        ``(latex, EC1PressureMemoResult)`` siguiendo el patron de memos de
        WindLoadJm.
    """
    if v_b <= 0:
        raise ValueError("v_b debe ser > 0")
    if c_e <= 0:
        raise ValueError("c_e debe ser > 0")
    if rho <= 0:
        raise ValueError("rho debe ser > 0")

    out = _ec1_pressure_calc(rho, v_b, c_e)
    latex, (q_b, q_p) = out if _HAS_HANDCALCS else ("", out)

    result = EC1PressureMemoResult(
        q_b_Pa=float(q_b),
        q_p_Pa=float(q_p),
        rho=rho,
        v_b=v_b,
        c_e=c_e,
        latex=latex,
        notes=[
            f"q_b = 0.5*rho*v_b^2 = {q_b:.1f} Pa ({q_b / 1000:.4f} kN/m2)",
            f"q_p = c_e*q_b = {q_p:.1f} Pa ({q_p / 1000:.4f} kN/m2)",
            f"rho = {rho:.3f} kg/m3, v_b = {v_b:.1f} m/s, c_e = {c_e:.3f}",
        ],
    )
    return latex, result


__all__ = ["EC1PressureMemoResult", "ec1_peak_pressure_memo"]
