"""Coeficientes Cp para techos complejos: abovedados, multi-aguas, dientes de sierra."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechoComplejoInput:
    tipo: str                   # 'arco' | 'multi_agua' | 'diente_sierra'
    f_h_ratio: float = 0.2      # f/H abovedado
    n_aguas: int = 2
    alpha_deg: float = 15.0
    code: str = "EU"            # EU/AU/SG/US/CO


@dataclass(frozen=True)
class TechoComplejoResult:
    cp_zonas: dict
    code: str


def cp_arco(f_h: float, code: str) -> dict:
    """Techo arco: f/h define el regimen."""
    # ASCE 7 / EN 1991-1-4
    if f_h <= 0.1:
        return {"barlovento": -0.9, "cumbrera": -0.7, "sotavento": -0.5}
    if f_h <= 0.25:
        return {"barlovento": 0.2, "cumbrera": -0.8, "sotavento": -0.4}
    return {"barlovento": 0.6, "cumbrera": -0.8, "sotavento": -0.4}


def cp_multi_agua(n_aguas: int, alpha_deg: float, code: str) -> dict:
    base = {-30: -0.8, 0: -0.5, 30: 0.4, 60: 0.7}
    closest = min(base.keys(), key=lambda a: abs(a - alpha_deg))
    cp_barl = base[closest]
    zonas = {}
    for i in range(n_aguas):
        zonas[f"agua_{i+1}_barl"] = cp_barl - 0.1 * i
        zonas[f"agua_{i+1}_sotav"] = -0.5 - 0.1 * i
    return zonas


def cp_diente_sierra(n_aguas: int, alpha_deg: float, code: str) -> dict:
    return {
        "primera_pendiente": 0.3,
        "primera_vertical": -1.0,
        "intermedia_pendiente": -0.4,
        "intermedia_vertical": -0.7,
        "ultima_pendiente": -0.6,
    }


def cp_techo_complejo(inp: TechoComplejoInput) -> TechoComplejoResult:
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    if inp.tipo == "arco":
        zonas = cp_arco(inp.f_h_ratio, inp.code)
    elif inp.tipo == "multi_agua":
        zonas = cp_multi_agua(inp.n_aguas, inp.alpha_deg, inp.code)
    elif inp.tipo == "diente_sierra":
        zonas = cp_diente_sierra(inp.n_aguas, inp.alpha_deg, inp.code)
    else:
        raise ValueError(f"tipo desconocido: {inp.tipo}")
    return TechoComplejoResult(zonas, inp.code)


__all__ = ["TechoComplejoInput", "TechoComplejoResult",
           "cp_arco", "cp_multi_agua", "cp_diente_sierra", "cp_techo_complejo"]
