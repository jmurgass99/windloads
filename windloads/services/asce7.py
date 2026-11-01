"""Servicio ASCE 7 — Capítulos 26-27 (MWFRS direccional), unidades imperiales.

Antes de 1.2.0 intentaba construir ``ASCE7WindLoad`` con argumentos que no
existen (siempre caía en el cálculo de reserva), usaba Cp de sotavento −0,5
para cualquier L/B y restaba la presión interior con signos opuestos en
barlovento y sotavento, de modo que ``net_psf`` salía 0,36·q_h menor que
q_h·G·(Cp_w − Cp_l) (−33 % con L/B ≤ 1).
"""
from __future__ import annotations
from dataclasses import dataclass

from ..exceptions import ConfigurationError
from ..pressure import asce7_leeward_Cp

# ASCE 7-16 Table 26.11-1 (alpha, zg [ft]); ASCE 7-22 adjusted the profile.
_EXPOSURE_FT = {"B": (7.0, 1200.0), "C": (9.5, 900.0), "D": (11.5, 700.0)}


@dataclass(frozen=True)
class ASCE7Input:
    V: float                # basic wind speed mph
    height_ft: float        # mean roof height h
    width_ft: float         # B, normal to wind
    depth_ft: float         # L, parallel to wind
    exposure: str = "C"     # B, C, D
    Kd: float = 0.85
    Kzt: float = 1.0
    Ke: float = 1.0
    G: float = 0.85         # gust factor (rigid)
    GCpi: float = 0.18      # enclosed
    risk_category: str = "II"


@dataclass(frozen=True)
class ASCE7Result:
    qz_at_height_psf: float     # q_h (Kz at the mean roof height)
    qh_psf: float
    Kz_at_height: float
    Cp_windward: float
    Cp_leeward: float
    p_windward_psf: float       # q_h·(G·Cp_w + GCpi): maximum inward pressure
    p_leeward_psf: float        # q_h·(G·Cp_l − GCpi): maximum suction
    summary: dict


def _kz_ft(z_ft: float, exposure: str) -> float:
    alpha, zg = _EXPOSURE_FT[exposure]
    return 2.01 * (max(z_ft, 15.0) / zg) ** (2.0 / alpha)


def compute_asce7(inp: ASCE7Input) -> ASCE7Result:
    """ASCE 7 §26-27: q_h = 0.00256·Kz·Kzt·Kd·Ke·V² [psf] y presiones de muro.

    Cp de barlovento 0,8 y de sotavento según L/B (Fig. 27.3-1, interpolado);
    todo a q_h (conservador para barlovento). ``summary['net_psf']`` es la
    presión neta del MWFRS, q_h·G·(Cp_w − Cp_l): la presión interior se
    cancela en la resultante.
    """
    exposure = inp.exposure.upper()
    if exposure not in _EXPOSURE_FT:
        raise ConfigurationError(f"exposure debe ser B, C o D, recibido {inp.exposure!r}")
    Kz_h = _kz_ft(inp.height_ft, exposure)
    qh = 0.00256 * Kz_h * inp.Kzt * inp.Kd * inp.Ke * inp.V ** 2
    Cp_w = 0.8
    Cp_l = asce7_leeward_Cp(inp.depth_ft / inp.width_ft)
    p_w = qh * (inp.G * Cp_w + inp.GCpi)
    p_l = qh * (inp.G * Cp_l - inp.GCpi)
    net = qh * inp.G * (Cp_w - Cp_l)
    return ASCE7Result(
        qz_at_height_psf=qh, qh_psf=qh, Kz_at_height=Kz_h,
        Cp_windward=Cp_w, Cp_leeward=Cp_l,
        p_windward_psf=p_w, p_leeward_psf=p_l,
        summary={
            "code": "ASCE 7 (Kz con constantes de ASCE 7-16)",
            "qh_psf": round(qh, 2),
            "L_over_B": round(inp.depth_ft / inp.width_ft, 3),
            "net_psf": round(net, 2),
        },
    )
