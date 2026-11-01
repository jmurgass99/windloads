"""Servicio: Components and Cladding (ASCE 7 Cap. 30).

Delega en ``windloads.components.asce7_GCp`` (interpolación logarítmica con
el área eficaz). Antes de 1.2.0 devolvía una tabla fija inventada (muros
+0,9/−1,0 y −1,4; cubierta +0,5/−1,0, −1,5 y −2,0) que ignoraba el área.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..components import asce7_GCp
from ..exceptions import ConfigurationError


@dataclass(frozen=True)
class CCInput:
    """C&C pressure on a discrete element."""
    code: str = "ASCE7"        # solo "ASCE7"
    roof_type: str = "gable"   # informativo: se usa la tabla de cubierta θ <= 7°
    zone: int = 1              # 1-3 (cubierta) | 4-5 (muro)
    area_m2: float = 1.0       # área eficaz
    qh_kPa: float = 1.0
    h_over_b: float = 1.0      # informativo


@dataclass(frozen=True)
class CCResult:
    GCp_positive: float
    GCp_negative: float
    p_positive_kPa: float      # q_h·GCp+ (sin presión interior)
    p_negative_kPa: float      # q_h·GCp− (sin presión interior)
    zone: int
    notes: list[str]


def compute_cc(inp: CCInput) -> CCResult:
    """GCp de ASCE 7 Cap. 30 para el área eficaz y presiones exteriores q_h·GCp.

    Muros (zonas 4 y 5): Fig. 30.3-1. Cubierta (zonas 1, 2 y 3): tabla de
    cubierta de baja pendiente (θ <= 7°) del paquete, cuyos valores no se han
    contrastado con la zonificación de ASCE 7-16/7-22 (zonas 1', 1, 2, 3).
    La presión interior (±GCpi) no se incluye: usa
    ``windloads.components.asce7_cc_pressure`` para la presión neta.
    """
    if inp.code.upper() != "ASCE7":
        raise ConfigurationError("compute_cc solo implementa ASCE7")
    if inp.zone in (4, 5):
        surface = "wall"
    elif inp.zone in (1, 2, 3):
        surface = "roof"
    else:
        raise ConfigurationError(f"zone debe ser 1-5, recibido {inp.zone!r}")
    pos = asce7_GCp(str(inp.zone), inp.area_m2, surface, "pos")
    neg = asce7_GCp(str(inp.zone), inp.area_m2, surface, "neg")
    notes = [
        f"Código: {inp.code}, superficie={surface}, zona={inp.zone}",
        f"qh = {inp.qh_kPa:.3f} kPa, área eficaz = {inp.area_m2:.2f} m²",
        "Presiones exteriores q_h·GCp; falta restar/sumar q_h·GCpi.",
    ]
    if surface == "roof":
        notes.append(f"roof_type={inp.roof_type!r}: se usa la tabla θ <= 7° (sin contrastar).")
    return CCResult(
        GCp_positive=pos, GCp_negative=neg,
        p_positive_kPa=inp.qh_kPa * pos, p_negative_kPa=inp.qh_kPa * neg,
        zone=inp.zone, notes=notes,
    )
