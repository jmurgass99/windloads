"""Servicio: exportar presiones por planta a JSON/CSV (y cabeceras SAP/ETABS).

Los destinos "sap" y "etabs" solo escriben la definición del patrón de carga,
sin cargas: para las cargas por planta usa ``windloads.export.to_sap_s2k`` /
``to_etabs_e2k``. Antes de 1.2.0, sin ``pressures_per_story`` el servicio
inventaba presiones (0,8 − 0,05·i kPa); ahora es obligatorio.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportInput:
    target: str                # "json" | "csv" | "sap" | "etabs"
    height_m: float
    width_m: float
    n_stories: int = 5
    pressures_per_story: list[float] | None = None   # kPa por piso


@dataclass(frozen=True)
class ExportResult:
    content: str
    target: str
    metadata: dict


def export_to(inp: ExportInput) -> ExportResult:
    """Genera contenido exportable (sin escribir a disco)."""
    import json
    if inp.pressures_per_story is None:
        raise ValueError("pressures_per_story es obligatorio (kPa por planta, "
                         "de abajo arriba); el servicio no inventa presiones")
    pps = list(inp.pressures_per_story)
    if len(pps) != inp.n_stories:
        raise ValueError(f"pressures_per_story tiene {len(pps)} valores y "
                         f"n_stories = {inp.n_stories}")
    if inp.target == "json":
        payload = {"stories": [
            {"id": i + 1, "z_m": (i + 1) * (inp.height_m / inp.n_stories),
             "pressure_kPa": pps[i]}
            for i in range(inp.n_stories)
        ]}
        content = json.dumps(payload, indent=2)
    elif inp.target == "csv":
        lines = ["story,z_m,pressure_kPa"]
        for i, p in enumerate(pps):
            z = (i + 1) * inp.height_m / inp.n_stories
            lines.append(f"{i+1},{z:.2f},{p:.4f}")
        content = "\n".join(lines)
    elif inp.target == "sap":
        lines = ["TABLE: \"LOAD PATTERN DEFINITIONS\""]
        lines.append('   LoadPat=WIND   DesignType=Wind   SelfWtMult=0')
        content = "\n".join(lines)
    elif inp.target == "etabs":
        lines = ["$ Load Pattern", "  LOAD \"WIND\" TYPE WIND"]
        content = "\n".join(lines)
    else:
        raise ValueError(f"Target inválido: {inp.target}")
    return ExportResult(content=content, target=inp.target,
                        metadata={"n_stories": inp.n_stories,
                                  "height_m": inp.height_m})
