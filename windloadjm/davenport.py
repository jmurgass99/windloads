"""
Davenport gust factor G_f para estructuras flexibles (T > 1 s).

ASCE 7-22 §26.11. Incluye respuesta cuasi-estática + resonante.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log, pi, sqrt


@dataclass(frozen=True)
class DavenportInput:
    natural_period_s: float
    height_m: float
    damping_ratio: float = 0.01
    intensity_turbulence: float = 0.30   # I_z típico exposición B
    Lz_m: float = 100.0                   # escala integral de turbulencia
    Vz_m_per_s: float = 35.0


@dataclass(frozen=True)
class DavenportResult:
    G_f: float
    Q_background: float
    R_resonant: float


def gust_factor_davenport(inp: DavenportInput) -> DavenportResult:
    """ASCE 7-22 Eq. 26.11-10."""
    f1 = 1.0 / inp.natural_period_s
    Iz = inp.intensity_turbulence
    h = inp.height_m
    Lz = inp.Lz_m
    Vz = inp.Vz_m_per_s
    beta = inp.damping_ratio

    # Q² (response background)
    Q2 = 1.0 / (1.0 + 0.63 * ((h + h) / Lz) ** 0.63)
    Q = sqrt(Q2)

    # R (response resonante)
    N1 = f1 * Lz / Vz
    Rn = 7.47 * N1 / (1 + 10.3 * N1) ** (5.0 / 3.0)
    eta_h = 4.6 * f1 * h / Vz
    Rh = 1.0 / eta_h - 1.0 / (2 * eta_h ** 2) * (1 - 1.0 / 2.71828 ** (-2 * eta_h)) \
         if eta_h > 0 else 1.0
    Rh = max(Rh, 0.0)
    R = sqrt(Rh * Rn / beta)

    # g_Q, g_R (peak factors)
    g_Q = 3.4
    g_v = 3.4
    g_R = sqrt(2 * log(3600 * f1)) + 0.5772 / sqrt(2 * log(3600 * f1))

    G_f = 0.925 * (
        (1 + 1.7 * Iz * sqrt(g_Q ** 2 * Q2 + g_R ** 2 * R ** 2))
        / (1 + 1.7 * g_v * Iz)
    )
    return DavenportResult(G_f=G_f, Q_background=Q, R_resonant=R)


__all__ = ["DavenportInput", "DavenportResult", "gust_factor_davenport"]
