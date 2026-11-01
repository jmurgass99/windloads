"""Servicio EC1 (EN 1991-1-4) — presiones de viento sobre edificios cerrados.

Delega en ``windloads.terrain.TerrainProfile`` (q_p, v_m) y en
``windloads.pressure.ec1_cpe_walls`` (Tabla 7.1). Antes de 1.2.0 intentaba
llamar a un atributo inexistente de ``EC1WindLoad`` y caía siempre en un
cálculo propio con coeficientes fijos (barlovento 0,8, sotavento −0,5,
lateral −0,7, cubierta −1,2) y devolvía como ``vm_at_height`` la velocidad
de pico √(2·q_p/ρ), no la velocidad media.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..exceptions import ConfigurationError
from ..pressure import ec1_cpe_walls
from ..terrain import TerrainProfile

_TC = {0: "0", 1: "I", 2: "II", 3: "III", 4: "IV"}


@dataclass(frozen=True)
class EC1Input:
    """Entrada para cálculo EC1.

    Unidades SI: m, m/s, kPa.
    """
    vb: float                          # basic wind velocity vb,0 m/s
    height: float                      # H edificio m
    width: float                       # B perpendicular al viento m
    depth: float                       # D paralelo al viento m
    terrain_category: int = 2          # 0..4 (EC1 tabla 4.1: 0, I, II, III, IV)
    c_dir: float = 1.0                 # factor direccional
    c_season: float = 1.0
    rho_air: float = 1.25              # kg/m³
    gust_factor: float = 1.0           # cs·cd (1.0 solo justificado si H <= 15 m)


@dataclass(frozen=True)
class EC1Result:
    qp_at_height: float                # kPa, q_p(H)
    vm_at_height: float                # m/s, velocidad media v_m(H)
    cp_windward: float                 # cpe,10 zona D (Tabla 7.1)
    cp_leeward: float                  # cpe,10 zona E (Tabla 7.1)
    cp_side: float                     # cpe,10 zona A (Tabla 7.1)
    cp_roof_min: float                 # cpe,10 zona F cubierta plana, aleros vivos (Tabla 7.2)
    cp_roof_max: float                 # cpe,10 zona I, rama positiva (Tabla 7.2)
    pressure_windward: float           # kPa, q_p·cpe,D·cs·cd (sin presión interior)
    pressure_leeward: float            # kPa, q_p·cpe,E·cs·cd (sin presión interior)
    summary: dict


def compute_ec1(inp: EC1Input) -> EC1Result:
    """Presión pico a la altura H y presiones exteriores de muros (EN 1991-1-4 §4.5 y §7.2.2).

    q_p y v_m se evalúan a z = H con v_b = c_dir·c_season·v_b,0 y c_o = 1. Las
    presiones de muro son exteriores (w_e = q_p·c_pe); la presión interior se
    cancela en la resultante del edificio. ``summary`` incluye la presión
    neta barlovento − sotavento sin el factor de falta de correlación.
    """
    if inp.terrain_category not in _TC:
        raise ConfigurationError(
            f"terrain_category debe ser 0..4, recibido {inp.terrain_category!r}")
    tp = TerrainProfile(code="EC1", category=_TC[inp.terrain_category])
    vb = inp.vb * inp.c_dir * inp.c_season
    qp = tp.ec1_peak_velocity_pressure(inp.height, vb, inp.rho_air) / 1000.0
    vm = tp.ec1_mean_wind_velocity(inp.height, vb)
    cpe = ec1_cpe_walls(inp.height, inp.depth)
    p_w = qp * cpe["D"] * inp.gust_factor
    p_l = qp * cpe["E"] * inp.gust_factor
    return EC1Result(
        qp_at_height=qp, vm_at_height=vm,
        cp_windward=cpe["D"], cp_leeward=cpe["E"], cp_side=cpe["A"],
        cp_roof_min=-1.8, cp_roof_max=0.2,
        pressure_windward=p_w, pressure_leeward=p_l,
        summary={
            "code": "EN 1991-1-4",
            "qp_kPa": round(qp, 4),
            "h_over_d": round(inp.height / inp.depth, 3),
            "p_net_windward_minus_leeward_kPa": round(p_w - p_l, 4),
        },
    )
