"""
NCh 432 (Chile, edición 2010) — viento.

Velocidad básica Vb por zona (m/s) + factor topográfico.
Presión de diseño q_z = 0.613 · Kz · Kd · V² · I  (SI)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class NCh432Input:
    Vb_m_s: float                # velocidad básica zona
    h_m: float                    # altura sobre el terreno
    importance_class: Literal["I", "II", "III", "IV"] = "II"
    exposure: Literal["A", "B", "C", "D"] = "B"


@dataclass(frozen=True)
class NCh432Result:
    qz_kN_m2: float
    Kz: float
    Kd: float
    I_factor: float


# Tabla NCh 432 §6
_I_FACTOR = {"I": 0.87, "II": 1.0, "III": 1.15, "IV": 1.15}
# Coeficientes exposición — alpha, zg
_EXPOSURE = {
    "A": (4.0, 300),       # zona urbana muy densa
    "B": (4.5, 365),       # zona urbana suburbana (común Chile)
    "C": (7.0, 274),       # campo abierto
    "D": (9.0, 213),       # costa
}


def evaluate_nch432(inp: NCh432Input) -> NCh432Result:
    alpha, zg = _EXPOSURE[inp.exposure]
    z = max(inp.h_m, 5.0)
    Kz = 2.01 * (z / zg) ** (2.0 / alpha)
    Kd = 0.85  # factor direccionalidad para edificios principales
    I = _I_FACTOR[inp.importance_class]

    V = inp.Vb_m_s
    qz_Pa = 0.613 * Kz * Kd * V ** 2 * I
    return NCh432Result(qz_kN_m2=qz_Pa / 1000.0, Kz=Kz, Kd=Kd, I_factor=I)


__all__ = ["NCh432Input", "NCh432Result", "evaluate_nch432"]
