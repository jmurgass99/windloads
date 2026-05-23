"""Servicio: exportar resultados a SAP/ETABS/JSON/CSV."""
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
        pps = [0.8 - 0.05 * i for i in range(inp.n_stories)]
    else:
        pps = inp.pressures_per_story
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
