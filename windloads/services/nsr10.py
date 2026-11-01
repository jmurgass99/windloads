"""Servicio NSR-10 §B.6 — cargas de viento Colombia.

Delega en ``windloads.codes.nsr10_b6`` (velocidad por ciudad y
``NSR10WindLoad``). Antes de 1.2.0 importaba una función inexistente y caía
siempre en un cálculo propio: velocidades por ciudad distintas de las del
módulo (Cali 80 km/h, Barranquilla 160 km/h), q_z = ½·ρ·(Kz·V)²·I con un Kz
inventado (0,5/0,7/0,9/1,05) elevado al cuadrado y sin K_d.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..codes.nsr10_b6 import NSR10WindLoad, nsr10_basic_wind_speed
from ..pressure import asce7_Cp_walls


@dataclass(frozen=True)
class NSR10Input:
    city: str                  # "Bogotá", "Barranquilla", etc.
    height_m: float
    width_m: float             # B, normal al viento
    depth_m: float             # L, paralelo al viento
    exposure: str = "B"        # categorías A-D de windloads.terrain (ver README)
    Iw: float = 1.0            # factor de importancia (multiplica q_z)


@dataclass(frozen=True)
class NSR10Result:
    V_basic_kmh: float
    qz_kPa: float              # q_h a la altura del edificio, incluye I
    Cp_windward: float
    Cp_leeward: float
    p_net_kPa: float           # q_h·G·(Cp_w − Cp_l)
    summary: dict


def compute_nsr10(inp: NSR10Input) -> NSR10Result:
    """NSR-10 §B.6 (procedimiento de ASCE 7-05): q_h = 0,613·Kz·Kzt·Kd·V²·I."""
    V = nsr10_basic_wind_speed(inp.city)
    wl = NSR10WindLoad(V, inp.exposure, building_height=inp.height_m,
                       width=inp.width_m, depth=inp.depth_m,
                       importance_factor=inp.Iw)
    qh = wl.qh / 1000.0
    cp = asce7_Cp_walls(inp.depth_m, inp.width_m, inp.height_m)
    p_net = qh * wl.G * (cp["windward"] - cp["leeward"])
    return NSR10Result(
        V_basic_kmh=V * 3.6, qz_kPa=qh,
        Cp_windward=cp["windward"], Cp_leeward=cp["leeward"],
        p_net_kPa=p_net,
        summary={"code": "NSR-10 B.6", "city": inp.city,
                 "V_ms": V, "V_kmh": round(V * 3.6, 1),
                 "qz_kPa": round(qh, 4)},
    )
