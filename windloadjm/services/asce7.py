"""Servicio ASCE 7-22 — Capítulos 26-27 (MWFRS directional)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ASCE7Input:
    V: float                # basic wind speed mph
    height_ft: float
    width_ft: float
    depth_ft: float
    exposure: str = "C"     # B, C, D
    Kd: float = 0.85
    Kzt: float = 1.0
    Ke: float = 1.0
    G: float = 0.85         # gust factor
    GCpi: float = 0.18      # enclosed
    risk_category: str = "II"


@dataclass(frozen=True)
class ASCE7Result:
    qz_at_height_psf: float
    qh_psf: float
    Kz_at_height: float
    Cp_windward: float
    Cp_leeward: float
    p_windward_psf: float
    p_leeward_psf: float
    summary: dict


def compute_asce7(inp: ASCE7Input) -> ASCE7Result:
    """ASCE 7-22 §26-27 directional procedure. Intenta API interna real
    y si no, usa placeholder analítico."""
    try:
        from windloadjm import ASCE7WindLoad
        load = ASCE7WindLoad(
            V=inp.V, h=inp.height_ft, b=inp.width_ft, d=inp.depth_ft,
            exposure=inp.exposure, Kd=inp.Kd, Kzt=inp.Kzt,
        )
        qz = getattr(load, "qz_at_height", None) or _placeholder_qz(inp)
        return _build_asce_result(inp, qz_at_h=qz)
    except Exception:
        return _build_asce_result(inp, qz_at_h=_placeholder_qz(inp))


def _placeholder_qz(inp: ASCE7Input) -> float:
    """qz simplificado ASCE7-22 eq 26.10-1: qz = 0.00256·Kz·Kzt·Kd·Ke·V²."""
    z_ft = max(inp.height_ft, 15)
    # Kz dependiente de exposure (alpha, zg)
    table = {"B": (7.0, 1200), "C": (9.5, 900), "D": (11.5, 700)}
    alpha, zg = table.get(inp.exposure, (9.5, 900))
    Kz = 2.01 * (z_ft / zg) ** (2 / alpha)
    qz = 0.00256 * Kz * inp.Kzt * inp.Kd * inp.Ke * inp.V ** 2
    return qz


def _build_asce_result(inp: ASCE7Input, qz_at_h: float) -> ASCE7Result:
    qh = qz_at_h
    Cp_w = 0.8
    Cp_l = -0.5
    p_w = qh * inp.G * Cp_w - qh * inp.GCpi
    p_l = qh * inp.G * Cp_l - qh * (-inp.GCpi)
    table = {"B": (7.0, 1200), "C": (9.5, 900), "D": (11.5, 700)}
    alpha, zg = table.get(inp.exposure, (9.5, 900))
    Kz_h = 2.01 * (max(inp.height_ft, 15) / zg) ** (2 / alpha)
    return ASCE7Result(
        qz_at_height_psf=qz_at_h, qh_psf=qh, Kz_at_height=Kz_h,
        Cp_windward=Cp_w, Cp_leeward=Cp_l,
        p_windward_psf=p_w, p_leeward_psf=p_l,
        summary={
            "code": "ASCE 7-22",
            "qh_psf": round(qh, 2),
            "net_psf": round(p_w - p_l, 2),
        },
    )
