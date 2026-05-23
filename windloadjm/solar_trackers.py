"""
Cargas viento sobre solar trackers (paneles fotovoltaicos seguidores).

ASCE 7-22 §29.4.4 introduce coeficientes específicos para arreglos
fotovoltaicos. SEAOC PV2 (2017) da guía detallada.

Modos de carga crítica:
    - stow position (panel horizontal): lift máximo
    - operating (panel inclinado β): momento de torsión máximo
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin


@dataclass(frozen=True)
class SolarTrackerInput:
    panel_chord_m: float = 2.0       # cuerda del panel
    panel_span_m: float = 30.0       # longitud por mesa
    tilt_deg: float = 0.0            # 0 = stow horizontal
    height_m: float = 2.0            # altura sobre el suelo
    Vb_m_per_s: float = 35.0
    GCp_lift: float = 1.5            # SEAOC PV2 Tabla 29.4
    GCp_moment: float = 1.0


@dataclass(frozen=True)
class SolarTrackerResult:
    qz_Pa: float
    lift_force_kN_per_m: float
    moment_kNm_per_m: float
    critical_mode: str


def evaluate_solar_tracker(inp: SolarTrackerInput) -> SolarTrackerResult:
    z = max(inp.height_m, 2.0)
    qz = 0.613 * 1.0 * 0.85 * inp.Vb_m_per_s ** 2  # Pa (ASCE 7 simplificado)

    # Lift por unidad de longitud
    if abs(inp.tilt_deg) < 5:  # stow
        F_lift = inp.GCp_lift * qz * inp.panel_chord_m / 1000.0
        M_torsion = 0.0
        mode = "stow_lift_max"
    else:
        beta = radians(inp.tilt_deg)
        F_lift = (inp.GCp_lift * cos(beta) ** 2 * qz
                   * inp.panel_chord_m) / 1000.0
        M_torsion = (inp.GCp_moment * sin(beta) * cos(beta) * qz
                      * inp.panel_chord_m ** 2) / 1000.0
        mode = "operating_torsion_max"

    return SolarTrackerResult(
        qz_Pa=qz,
        lift_force_kN_per_m=F_lift,
        moment_kNm_per_m=M_torsion,
        critical_mode=mode,
    )


__all__ = ["SolarTrackerInput", "SolarTrackerResult", "evaluate_solar_tracker"]
