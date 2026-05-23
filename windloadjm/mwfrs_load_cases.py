# -*- coding: utf-8 -*-
"""Cuatro casos de carga del MWFRS (ASCE 7-22 §27.3.5, Figura 27.3-8).

Para el diseno del sistema principal resistente a fuerzas de viento (MWFRS) de
edificios rigidos hay que considerar 4 combinaciones de presion/torsion, no solo
la fuerza total. Esto captura la torsion en planta por distribucion asimetrica.

  Caso 1: 100% P en cada eje principal por separado (sin torsion).
  Caso 2: 75% P en un eje + momento torsor M_T = 0.75·P·e, e = ±0.15·B.
  Caso 3: 75% P en ambos ejes simultaneamente (sin torsion).
  Caso 4: 56.3% P en ambos ejes + torsion en ambos, e = ±0.15·B.

B es la dimension en planta normal a la direccion del viento analizado.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

_E = 0.15  # excentricidad relativa (15% del ancho)


@dataclass(frozen=True)
class WindLoadCase:
    name: str
    Px_kN: float          # fuerza MWFRS en X
    Py_kN: float          # fuerza MWFRS en Y
    Mt_kNm: float         # momento torsor en planta


def mwfrs_load_cases(Px_kN: float, Py_kN: float, Bx_m: float, By_m: float) -> List[WindLoadCase]:
    """Genera los 4 casos de carga del MWFRS (ASCE 7 Fig 27.3-8).

    Args:
        Px_kN, Py_kN: fuerza total de viento de diseno en cada eje principal.
        Bx_m, By_m: dimension normal al viento para la torsion de cada eje
            (Bx para la fuerza Px, By para Py).
    """
    ex = _E * Bx_m
    ey = _E * By_m
    cases: List[WindLoadCase] = []
    # Caso 1: 100% en cada eje, sin torsion (dos sub-casos).
    cases.append(WindLoadCase("1-X", Px_kN, 0.0, 0.0))
    cases.append(WindLoadCase("1-Y", 0.0, Py_kN, 0.0))
    # Caso 2: 75% + torsion, un eje a la vez.
    cases.append(WindLoadCase("2-X", 0.75 * Px_kN, 0.0, 0.75 * Px_kN * ex))
    cases.append(WindLoadCase("2-Y", 0.0, 0.75 * Py_kN, 0.75 * Py_kN * ey))
    # Caso 3: 75% en ambos ejes, sin torsion.
    cases.append(WindLoadCase("3", 0.75 * Px_kN, 0.75 * Py_kN, 0.0))
    # Caso 4: 56.3% en ambos + torsion combinada.
    Mt4 = 0.563 * (Px_kN * ex + Py_kN * ey)
    cases.append(WindLoadCase("4", 0.563 * Px_kN, 0.563 * Py_kN, Mt4))
    return cases


def envelope(cases: List[WindLoadCase]) -> dict:
    """Maximos absolutos de Px, Py y Mt sobre todos los casos (para el diseno)."""
    return {
        "Px_max_kN": max(abs(c.Px_kN) for c in cases),
        "Py_max_kN": max(abs(c.Py_kN) for c in cases),
        "Mt_max_kNm": max(abs(c.Mt_kNm) for c in cases),
    }


__all__ = ["WindLoadCase", "mwfrs_load_cases", "envelope"]
