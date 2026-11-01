"""Separación Semántica -> Malla de Paneles de Envolvente (EnvelopeZoneMapping) para WindLoads.

Mapea niveles de planta (`story_to_panels`) y zonas de cubierta (`roof_to_zones` F/G/H/I)
a paneles discretos 3D, preservando velocidades básicas, rugosidad de terreno y coeficientes
de presión externa/interna EN 1991-1-4 / ASCE 7 al refinar la malla vertical y de cubierta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .codes.ec1_1_4 import EC1WindLoad


@dataclass
class EnvelopeZoneMapping:
    """Mapeo Planta/Cubierta Semántica -> Paneles Discretos de Viento."""
    story_to_panels: Dict[int, List[int]] = field(default_factory=dict)
    panel_to_story: Dict[int, int] = field(default_factory=dict)
    roof_to_zones: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class WindFacadePanel:
    index: int
    story: int
    zone: str
    z_mid_m: float
    height_m: float
    width_m: float
    qp_kPa: float
    cpe: float
    cpi: float
    net_force_kN: float


def build_building_wind_mesh(
    vb_m_s: float = 28.0,
    terrain_cat: str = "II",
    width_B_m: float = 24.0,
    depth_d_m: float = 18.0,
    story_heights_m: List[float] | None = None,
    subdivisions_per_story: int = 2,
    cpi: float = 0.2,
) -> Tuple[List[WindFacadePanel], EnvelopeZoneMapping, Dict[str, float]]:
    """Subdivide cada planta en `subdivisions_per_story` franjas y evalúa presiones EN 1991-1-4."""
    heights = story_heights_m or [4.0, 3.5, 3.5, 3.5, 3.5]
    div = max(1, int(subdivisions_per_story))
    total_H = sum(heights)

    ec1 = EC1WindLoad(
        vb=vb_m_s,
        terrain_cat=terrain_cat,
        building_height=total_H,
        width=width_B_m,
        depth=depth_d_m,
    )
    fp = ec1.facade_pressures()
    cpe_windward = float(fp.get("cpe", {}).get("D", 0.8)) if isinstance(fp.get("cpe"), dict) else 0.8
    cpe_leeward = float(fp.get("cpe", {}).get("E", -0.5)) if isinstance(fp.get("cpe"), dict) else -0.5

    mapping = EnvelopeZoneMapping()
    panels: List[WindFacadePanel] = []
    z_cursor = 0.0

    for st_idx, h_story in enumerate(heights, start=1):
        dh = h_story / div
        mapping.story_to_panels[st_idx] = []
        for _ in range(div):
            z_mid = z_cursor + 0.5 * dh
            qp_pa = float(ec1.qp_at(max(z_mid, 1.0)))
            qp_kpa = qp_pa / 1000.0
            area = width_B_m * dh

            # Panel barlovento (Zona D) y sotavento (Zona E)
            for zone, cpe in (("D", cpe_windward), ("E", cpe_leeward)):
                idx = len(panels)
                f_kn = qp_kpa * (cpe - cpi) * area
                panels.append(
                    WindFacadePanel(
                        index=idx,
                        story=st_idx,
                        zone=zone,
                        z_mid_m=z_mid,
                        height_m=dh,
                        width_m=width_B_m,
                        qp_kPa=qp_kpa,
                        cpe=cpe,
                        cpi=cpi,
                        net_force_kN=f_kn,
                    )
                )
                mapping.story_to_panels[st_idx].append(idx)
                mapping.panel_to_story[idx] = st_idx
            z_cursor += dh

    # Zonas de cubierta plana F, G, H, I
    qp_top_kpa = float(ec1.qp_at(total_H)) / 1000.0
    for zone, cpe_r in (("F", -1.8), ("G", -1.2), ("H", -0.7), ("I", -0.2)):
        idx = len(panels)
        area_r = (width_B_m * depth_d_m) / 4.0
        panels.append(
            WindFacadePanel(
                index=idx,
                story=len(heights),
                zone=zone,
                z_mid_m=total_H,
                height_m=0.0,
                width_m=width_B_m * 0.5,
                qp_kPa=qp_top_kpa,
                cpe=cpe_r,
                cpi=cpi,
                net_force_kN=qp_top_kpa * (cpe_r - cpi) * area_r,
            )
        )
        mapping.roof_to_zones[zone] = [idx]

    base_shear_kn = sum(
        p.net_force_kN if p.zone == "D" else -p.net_force_kN
        for p in panels
        if p.zone in ("D", "E")
    )
    summary = {
        "total_height_m": total_H,
        "qp_top_kPa": qp_top_kpa,
        "base_shear_kN": base_shear_kn,
        "panel_count": float(len(panels)),
    }
    return panels, mapping, summary
