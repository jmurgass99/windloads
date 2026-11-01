"""
Plano DXF con aplicación de cargas de viento por zona.

Entrada:
    - WindCalculationResult: dict-like con `qz_kPa` o `qz_Pa` y opcionalmente Cp por cara.
    - Plant (planta del edificio): lista de vértices [(x, y), ...] en metros.

Salida:
    DXF con:
        - Contorno del edificio (capa W-OUTLINE)
        - Flechas en cada cara con valor q_z·C_p en kN/m² (capa W-PRESS)
        - Cuadro de zonas con leyenda de colores (capa W-LEGEND)
        - Cajetín — reutiliza templates_construction (si está instalado)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import ezdxf
except ImportError as _exc:  # pragma: no cover
    ezdxf = None  # type: ignore
    _EZDXF_ERR = _exc
else:
    _EZDXF_ERR = None


# Mapa de capas (ACI colors)
LAYERS = {
    "W-OUTLINE": 7,    # contorno
    "W-PRESS":   1,    # flechas presión
    "W-SUCT":    5,    # succión
    "W-LEGEND":  3,    # cuadro
    "W-TEXT":    2,    # rótulos
    "W-TITLE":   7,    # cajetín
}


@dataclass
class WindZoneLoad:
    """Carga de viento por cara/zona del edificio."""
    face: str               # "windward", "leeward", "side", o etiqueta libre
    cp: float               # coeficiente de presión externa
    pressure_kPa: float     # q_z·Cp signado (+ presión, − succión)


@dataclass
class WindPlanInput:
    plant_m: list[tuple[float, float]]       # vértices (cerrado o no)
    qz_kPa: float                            # presión dinámica base
    zone_loads: list[WindZoneLoad] = field(default_factory=list)
    code: str = "ASCE7-22"
    project: str = "Project"
    units: str = "M"


# ---- API principal ----------------------------------------------------

def build_wind_plan_dxf(inp: WindPlanInput, path: str | Path) -> Any:
    """Construye y guarda el DXF. Devuelve el Drawing ezdxf."""
    if ezdxf is None:  # pragma: no cover
        raise ImportError(
            f"ezdxf no instalado: {_EZDXF_ERR}. `pip install windloads[dxf]`."
        )
    doc = ezdxf.new(dxfversion="R2010", setup=True)
    doc.header["$INSUNITS"] = 6 if inp.units.upper() == "M" else 4

    for name, color in LAYERS.items():
        doc.layers.add(name=name, color=color)

    msp = doc.modelspace()

    _draw_outline(msp, inp.plant_m)
    _draw_face_arrows(msp, inp.plant_m, inp.zone_loads, inp.qz_kPa)
    _draw_legend(msp, inp.plant_m, inp.zone_loads, inp.qz_kPa, inp.code)
    _draw_title_block(msp, inp.plant_m, inp.project, inp.code)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return doc


def from_wind_result(
    result: Mapping[str, Any] | Any,
    plant_m: Sequence[tuple[float, float]],
    *,
    project: str = "Project",
    code: str = "ASCE7-22",
    cp_by_face: Mapping[str, float] | None = None,
) -> WindPlanInput:
    """
    Construye un `WindPlanInput` a partir de un resultado de `codes_multi`.
    Acepta dict {qz_kPa: ..} o dataclass con atributo `qz_kPa`.
    """
    qz = _extract_qz_kPa(result)
    cps = cp_by_face or {"windward": 0.8, "leeward": -0.5, "side_left": -0.7, "side_right": -0.7}
    zones = [
        WindZoneLoad(face=name, cp=cp, pressure_kPa=qz * cp)
        for name, cp in cps.items()
    ]
    return WindPlanInput(
        plant_m=list(plant_m),
        qz_kPa=qz,
        zone_loads=zones,
        code=code,
        project=project,
    )


# ---- helpers ----------------------------------------------------------

def _extract_qz_kPa(result: Any) -> float:
    if hasattr(result, "qz_kPa"):
        return float(getattr(result, "qz_kPa"))
    if isinstance(result, Mapping):
        if "qz_kPa" in result:
            return float(result["qz_kPa"])
        if "qz_Pa" in result:
            return float(result["qz_Pa"]) / 1000.0
    raise ValueError("No se pudo extraer qz_kPa del resultado.")


def _draw_outline(msp: Any, plant: Sequence[tuple[float, float]]) -> None:
    pts = list(plant)
    if pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "W-OUTLINE"})


def _bbox(plant: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in plant]
    ys = [p[1] for p in plant]
    return min(xs), min(ys), max(xs), max(ys)


def _draw_face_arrows(
    msp: Any,
    plant: Sequence[tuple[float, float]],
    loads: Iterable[WindZoneLoad],
    qz_kPa: float,
) -> None:
    """
    Distribuye flechas en las caras del polígono (aproximación a 4 caras:
    windward=cara con menor x, leeward=mayor x, side_left=menor y, side_right=mayor y).
    """
    xmin, ymin, xmax, ymax = _bbox(plant)
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    arrow_len = 0.25 * max(xmax - xmin, ymax - ymin)
    if arrow_len <= 0:
        arrow_len = 1.0

    face_to_point = {
        "windward":   ((xmin, cy), (-1, 0)),
        "leeward":    ((xmax, cy), (+1, 0)),
        "side_left":  ((cx, ymin), (0, -1)),
        "side_right": ((cx, ymax), (0, +1)),
    }

    for load in loads:
        anchor, direction = face_to_point.get(
            load.face, ((cx, cy), (1, 0))
        )
        # Presión (+): la flecha nace FUERA de la cara (anchor + n·L, n normal
        # exterior) y termina en la cara, apuntando hacia el edificio.
        # Succión (−): nace en la cara y apunta hacia fuera.
        # Antes de 1.2.0 el signo estaba invertido: las flechas de presión
        # nacían dentro del edificio y salían hacia fuera.
        out_pt = (anchor[0] + direction[0] * arrow_len,
                  anchor[1] + direction[1] * arrow_len)
        if load.pressure_kPa >= 0:
            start, end = out_pt, anchor
        else:
            start, end = anchor, out_pt
        layer = "W-PRESS" if load.pressure_kPa >= 0 else "W-SUCT"
        msp.add_line(start, end, dxfattribs={"layer": layer})
        # Punta de flecha (V)
        _add_arrowhead(msp, start, end, layer)
        # Etiqueta
        label = f"{load.face}: {load.pressure_kPa:+.2f} kN/m² (Cp={load.cp:+.2f})"
        msp.add_text(label, dxfattribs={"layer": "W-TEXT", "height": arrow_len * 0.08}).set_placement(
            (start[0], start[1] - arrow_len * 0.12)
        )


def _add_arrowhead(msp: Any, start: tuple[float, float], end: tuple[float, float], layer: str) -> None:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    # perpendicular
    px, py = -uy, ux
    head = length * 0.15
    p1 = (end[0] - ux * head + px * head * 0.6, end[1] - uy * head + py * head * 0.6)
    p2 = (end[0] - ux * head - px * head * 0.6, end[1] - uy * head - py * head * 0.6)
    msp.add_line(end, p1, dxfattribs={"layer": layer})
    msp.add_line(end, p2, dxfattribs={"layer": layer})


def _draw_legend(
    msp: Any,
    plant: Sequence[tuple[float, float]],
    loads: list[WindZoneLoad],
    qz_kPa: float,
    code: str,
) -> None:
    xmin, ymin, xmax, ymax = _bbox(plant)
    w = xmax - xmin
    x0 = xmax + 0.1 * w
    y0 = ymax
    box_h = 0.05 * w if w > 0 else 0.5
    box_w = 0.4 * w if w > 0 else 4.0
    text_h = box_h * 0.35

    msp.add_lwpolyline(
        [(x0, y0), (x0 + box_w, y0), (x0 + box_w, y0 - box_h * (len(loads) + 2)),
         (x0, y0 - box_h * (len(loads) + 2)), (x0, y0)],
        dxfattribs={"layer": "W-LEGEND"},
    )
    msp.add_text(
        f"VIENTO — {code}  qz = {qz_kPa:.3f} kN/m²",
        dxfattribs={"layer": "W-TEXT", "height": text_h},
    ).set_placement((x0 + 0.05 * box_w, y0 - box_h * 0.7))

    for i, load in enumerate(loads, start=1):
        y = y0 - box_h * (i + 1) + box_h * 0.3
        msp.add_text(
            f"{load.face:>12s}  Cp={load.cp:+.2f}  p={load.pressure_kPa:+.3f} kN/m²",
            dxfattribs={"layer": "W-TEXT", "height": text_h},
        ).set_placement((x0 + 0.05 * box_w, y))


def _draw_title_block(
    msp: Any,
    plant: Sequence[tuple[float, float]],
    project: str,
    code: str,
) -> None:
    xmin, ymin, xmax, ymax = _bbox(plant)
    w = max(xmax - xmin, 1.0)
    x0, y0 = xmin, ymin - 0.2 * w
    h = 0.1 * w
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h), (x0, y0)],
        dxfattribs={"layer": "W-TITLE"},
    )
    msp.add_text(
        f"{project} — Wind plan ({code})",
        dxfattribs={"layer": "W-TEXT", "height": h * 0.3},
    ).set_placement((x0 + w * 0.05, y0 - h * 0.6))


__all__ = [
    "LAYERS",
    "WindZoneLoad",
    "WindPlanInput",
    "build_wind_plan_dxf",
    "from_wind_result",
]
