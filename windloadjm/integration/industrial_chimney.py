"""Bridge WindLoadJm -> IndustrialJm: viento sobre chimenea industrial."""
from __future__ import annotations

import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class ChimneyWindInput:
    H_m: float
    D_m: float
    vb_m_s: float
    terrain_category: int = 2
    code: str = "EU"


@dataclass(frozen=True)
class ChimneyWindResult:
    qz_top_kPa: float
    F_arrastre_kN: float
    M_base_kNm: float
    vortex_critical: bool


def viento_chimenea(inp: ChimneyWindInput) -> ChimneyWindResult:
    import math
    qz = 0.5 * 1.25 * inp.vb_m_s ** 2 / 1000.0
    Cf = 0.7   # cilindro
    A_proy = inp.D_m * inp.H_m
    F = Cf * qz * A_proy
    M = F * inp.H_m / 2.0
    # criterio Strouhal (St=0.20 cilindros)
    f_n = 3.5 / inp.H_m if inp.H_m > 0 else 1.0
    v_cr = f_n * inp.D_m / 0.20
    crit = inp.vb_m_s > 0.8 * v_cr
    try:  # delega a IndustrialJm si esta
        from industrialjm.chimneys import vortex_check  # noqa: F401
    except ImportError:
        warnings.warn("IndustrialJm no disponible - usando criterio simplificado")
    return ChimneyWindResult(qz, F, M, crit)


__all__ = ["ChimneyWindInput", "ChimneyWindResult", "viento_chimenea"]
