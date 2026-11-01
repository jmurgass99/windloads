"""Memoria ASCE 7-22 §26-27 MWFRS Directional Procedure (Capitulo 27).

Calcula presion velocidad q_z, coeficientes y presion neta de diseno para
sistemas principales (MWFRS) de edificio rigido con techo plano o inclinado.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

from ..pressure import asce7_leeward_Cp

try:
    from handcalcs.decorator import handcalc
    _HAS_HANDCALCS = True
except ImportError:
    _HAS_HANDCALCS = False
    def handcalc(*args, **kwargs):
        def deco(f): return f
        return deco


# Tabla 26.10-1: Coeficiente exposicion Kz
def _kz(z, exposure):
    """Coeficiente exposicion Kz ASCE 7-22 Tabla 26.10-1."""
    if exposure == "B":
        alpha, zg = 7.0, 365.76
    elif exposure == "C":
        alpha, zg = 9.5, 274.32
    elif exposure == "D":
        alpha, zg = 11.5, 213.36
    else:
        raise ValueError(f"exposure debe ser B|C|D, recibido {exposure}")
    z_use = max(z, 4.572)  # 15 ft = 4.572 m
    return 2.01 * (z_use / zg) ** (2.0 / alpha)


@dataclass
class MWFRSResult:
    """Resultado calculo MWFRS ASCE 7-22."""
    K_z: float
    q_z_kN_m2: float       # presion velocidad
    GCpf_wind: float        # coef presion barlovento promedio
    p_design_kN_m2: float   # presion neta diseno
    latex: str = ""
    notes: list[str] = field(default_factory=list)


@handcalc(override="long", precision=4)
def _q_z(K_z, K_zt, K_d, K_e, V_ms):
    q_z = 0.613 * K_z * K_zt * K_d * K_e * (V_ms ** 2) / 1000
    return q_z


@handcalc(override="long", precision=3)
def _net_pressure_walls(q_z, G, Cp_wind, Cp_lee, GCpi_pos, GCpi_neg):
    p_wind_pos = q_z * (G * Cp_wind - GCpi_pos)
    p_wind_neg = q_z * (G * Cp_wind - GCpi_neg)
    p_lee_pos = q_z * (G * Cp_lee - GCpi_pos)
    p_lee_neg = q_z * (G * Cp_lee - GCpi_neg)
    return p_wind_pos, p_wind_neg, p_lee_pos, p_lee_neg


def mwfrs_directional_memo(V_ms, z, exposure="C", K_zt=1.0, K_d=0.85,
                                K_e=1.0, building_class="II",
                                L_over_B=1.0, G=0.85, enclosed=True):
    """Genera memoria MWFRS directional ASCE 7-22 (paredes barlovento+sotavento).

    Args:
        V_ms: velocidad basica viento (m/s) MRI segun categoria riesgo
        z: altura sobre nivel terreno donde se evalua (m)
        exposure: B|C|D
        K_zt: factor topografia (default 1.0 terreno plano)
        K_d: factor direccional (Tabla 26.6-1: 0.85 edificios MWFRS)
        K_e: factor elevacion sobre nivel del mar (Tabla 26.9-1)
        building_class: I|II|III|IV (informativo)
        L_over_B: relacion L/B planta (para Cp sotavento Tabla 27.3-1)
        G: factor rafaga (0.85 rigido tipico)
        enclosed: True=cerrado (GCpi +/-0.18), False=parcialmente cerrado (+/-0.55)

    Returns:
        (latex, MWFRSResult)
    """
    if V_ms <= 0:
        raise ValueError("V_ms debe ser positivo")
    if z <= 0:
        raise ValueError("z debe ser positivo")
    if exposure not in {"B", "C", "D"}:
        raise ValueError("exposure invalido")
    if L_over_B <= 0:
        raise ValueError("L_over_B debe ser positivo")

    K_z = _kz(z, exposure)
    out_q = _q_z(K_z, K_zt, K_d, K_e, V_ms)
    # Sin handcalcs el decorador es la identidad y devuelve solo el numero.
    latex_q, q_z = out_q if _HAS_HANDCALCS else ("", out_q)

    # Cp Fig. 27.3-1: barlovento 0.8; sotavento -0.5 (L/B<=1), -0.3 (2),
    # -0.2 (>=4) con interpolacion lineal (antes de 1.2.0 una sola recta de
    # -0.5 a -0.2 entre 1 y 4: -0.4 en L/B = 2 en vez de -0.3).
    Cp_wind = 0.8
    Cp_lee = asce7_leeward_Cp(L_over_B)

    GCpi_pos = 0.18 if enclosed else 0.55
    GCpi_neg = -0.18 if enclosed else -0.55

    out_p = _net_pressure_walls(
        q_z, G, Cp_wind, Cp_lee, GCpi_pos, GCpi_neg,
    )
    latex_p, (p_wp, p_wn, p_lp, p_ln) = out_p if _HAS_HANDCALCS else ("", out_p)

    # Envolvente para diseno: maxima magnitud sobre cualquier superficie
    p_design = max(abs(p_wp), abs(p_wn), abs(p_lp), abs(p_ln))

    return latex_q + "\n\n" + latex_p, MWFRSResult(
        K_z=float(K_z),
        q_z_kN_m2=float(q_z),
        GCpf_wind=float(G * Cp_wind),
        p_design_kN_m2=float(p_design),
        latex=latex_q + "\n\n" + latex_p,
        notes=[
            f"K_z(z={z:.1f}m, exp={exposure}) = {K_z:.3f}",
            f"q_z = {q_z*1000:.0f} N/m2 ({q_z:.3f} kN/m2)",
            f"Cp barlovento = {Cp_wind:.2f}, Cp sotavento = {Cp_lee:.2f}",
            f"GCpi = {'+/-0.18' if enclosed else '+/-0.55'}",
            f"p_diseno (combo critico) = {p_design:.3f} kN/m2",
        ],
    )
