"""windloads.sap_bridge
======================
Puente puro de datos entre WindLoads y el modelo canónico (jmstructural-common / fastsap).

Produce estructuras de datos puras (LoadPattern, ElementLoad, Model) sin llamadas COM.
Garantiza la conversión estricta de unidades:
    presión en Pa -> q_kPa = p_Pa / 1000.0
    carga lineal w [kN/m] = q_kPa * tributary_width_m
"""
from __future__ import annotations
from typing import Sequence

from windloads._common.model import ElementLoad, LoadPattern, Model


def wind_to_load_pattern(
    pressure_Pa: float,
    tributary_width_m: float,
    frame_ids: Sequence[str],
    pattern_name: str = "WIND_X",
    direction: str = "GlobalX",
) -> tuple[LoadPattern, tuple[ElementLoad, ...]]:
    """Transforma la presión eólica en un LoadPattern y sus ElementLoad asociados.

    Args:
        pressure_Pa: Presión neta de viento en Pascales (Pa).
        tributary_width_m: Ancho tributario en metros (m).
        frame_ids: Identificadores de las barras que reciben la carga.
        pattern_name: Nombre del patrón de carga.
        direction: Dirección de la carga ("GlobalX", "GlobalY", "GlobalZ", "Local2", etc.).

    Returns:
        Tupla (LoadPattern, tuple[ElementLoad, ...]).
    """
    if tributary_width_m <= 0.0:
        raise ValueError(f"tributary_width_m debe ser > 0, obtenido {tributary_width_m}")

    # Conversión: 1 Pa = 10^-3 kPa = 10^-3 kN/m2.
    # w (kN/m) = pressure (Pa) / 1000.0 * tributary_width_m
    w_kN_m = (pressure_Pa / 1000.0) * tributary_width_m

    pattern = LoadPattern(name=pattern_name, kind="Wind", self_weight_multiplier=0.0)
    element_loads = tuple(
        ElementLoad(
            element_id=fid,
            w_kN_m=w_kN_m,
            direction=direction,
            pattern=pattern_name,
        )
        for fid in frame_ids
    )

    return pattern, element_loads


def apply_wind_to_model(
    model: Model,
    pressure_Pa: float,
    tributary_width_m: float,
    frame_ids: Sequence[str],
    pattern_name: str = "WIND_X",
    direction: str = "GlobalX",
) -> Model:
    """Aplica la carga de viento calculada sobre un Model canónico existente."""
    pattern, new_elem_loads = wind_to_load_pattern(
        pressure_Pa=pressure_Pa,
        tributary_width_m=tributary_width_m,
        frame_ids=frame_ids,
        pattern_name=pattern_name,
        direction=direction,
    )

    existing_patterns = list(model.patterns)
    if not any(p.name == pattern_name for p in existing_patterns):
        existing_patterns.append(pattern)

    combined_elem_loads = tuple(list(model.element_loads) + list(new_elem_loads))

    return Model(
        nodes=model.nodes,
        restraints=model.restraints,
        materials=model.materials,
        sections=model.sections,
        elements=model.elements,
        patterns=tuple(existing_patterns),
        nodal_loads=model.nodal_loads,
        element_loads=combined_elem_loads,
        mass_source=model.mass_source,
        cases=model.cases,
        reactions=model.reactions,
    )


__all__ = ["wind_to_load_pattern", "apply_wind_to_model"]
