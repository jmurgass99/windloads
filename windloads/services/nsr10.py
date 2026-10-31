"""Servicio NSR-10 §B.6 — cargas de viento Colombia."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class NSR10Input:
    city: str                  # "Bogotá", "Barranquilla", etc.
    height_m: float
    width_m: float
    depth_m: float
    exposure: str = "B"        # A, B, C, D (NSR-10 B.6.5)
    Iw: float = 1.0            # importance


@dataclass(frozen=True)
class NSR10Result:
    V_basic_kmh: float
    qz_kPa: float
    Cp_windward: float
    Cp_leeward: float
    p_net_kPa: float
    summary: dict


def compute_nsr10(inp: NSR10Input) -> NSR10Result:
    """NSR-10 §B.6 wind on buildings."""
    try:
        from windloads.codes.nsr10_b6 import basic_wind_speed_kmh
        V = basic_wind_speed_kmh(inp.city)
    except Exception:
        V = _placeholder_V(inp.city)
    Kz = {"A": 0.5, "B": 0.7, "C": 0.9, "D": 1.05}.get(inp.exposure, 0.7)
    v_ms = V / 3.6
    qz_Pa = 0.5 * 1.25 * (Kz * v_ms) ** 2 * inp.Iw
    qz_kPa = qz_Pa / 1000
    cp_w, cp_l = 0.8, -0.5
    p_net = qz_kPa * (cp_w - cp_l)
    return NSR10Result(
        V_basic_kmh=V, qz_kPa=qz_kPa,
        Cp_windward=cp_w, Cp_leeward=cp_l,
        p_net_kPa=p_net,
        summary={"code": "NSR-10 B.6", "city": inp.city,
                 "V_kmh": V, "qz_kPa": round(qz_kPa, 4)},
    )


def _placeholder_V(city: str) -> float:
    """Fallback con un subset de ciudades NSR-10 B.6."""
    cities = {
        "Bogotá": 100.0, "Bogota": 100.0,
        "Barranquilla": 160.0,
        "Medellín": 100.0, "Medellin": 100.0,
        "Cali": 80.0,
        "Cartagena": 130.0,
    }
    return cities.get(city, 100.0)
