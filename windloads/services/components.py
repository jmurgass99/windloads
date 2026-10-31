"""Servicio: Components and Cladding (ASCE 7 Ch. 30 + EC1 §7)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CCInput:
    """C&C pressure on a discrete element."""
    code: str = "ASCE7"        # "ASCE7" | "EC1"
    roof_type: str = "gable"   # "gable" | "monoslope" | "domed" | "mansard" | "flat"
    zone: int = 1              # 1-3 (roof) | 4-5 (wall)
    area_m2: float = 1.0
    qh_kPa: float = 1.0
    h_over_b: float = 1.0


@dataclass(frozen=True)
class CCResult:
    GCp_positive: float
    GCp_negative: float
    p_positive_kPa: float
    p_negative_kPa: float
    zone: int
    notes: list[str]


def compute_cc(inp: CCInput) -> CCResult:
    """C&C estimación rápida (placeholder)."""
    table_GCp = {
        1: (0.5, -1.0),
        2: (0.5, -1.5),
        3: (0.5, -2.0),
        4: (0.9, -1.0),
        5: (0.9, -1.4),
    }
    pos, neg = table_GCp.get(inp.zone, (0.5, -1.0))
    p_pos = inp.qh_kPa * pos
    p_neg = inp.qh_kPa * neg
    return CCResult(
        GCp_positive=pos, GCp_negative=neg,
        p_positive_kPa=p_pos, p_negative_kPa=p_neg,
        zone=inp.zone,
        notes=[
            f"Código: {inp.code}, roof_type={inp.roof_type}, zona={inp.zone}",
            f"qh = {inp.qh_kPa:.3f} kPa, área = {inp.area_m2:.1f} m²",
        ],
    )
