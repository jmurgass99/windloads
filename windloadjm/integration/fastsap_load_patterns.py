"""Bridge WindLoadJm -> FastSAP: exporta patrones de carga de viento como joint loads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WindLoadPattern:
    name: str
    joint_loads: dict      # joint_name -> (Fx, Fy, Fz) kN


class FastSAPWindPatternExporter:
    def __init__(self, client: Any = None, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run

    def export(self, patterns: list[WindLoadPattern]) -> dict:
        if self.dry_run or self.client is None:
            return {
                "patterns": [p.name for p in patterns],
                "n_patterns": len(patterns),
                "n_loads": sum(len(p.joint_loads) for p in patterns),
                "dry_run": True,
            }
        applied = 0
        for p in patterns:
            try:
                self.client.LoadPatterns.Add(p.name, 6)  # 6=WIND
                for j, (Fx, Fy, Fz) in p.joint_loads.items():
                    self.client.PointObj.SetLoadForce(j, p.name, (Fx, Fy, Fz, 0, 0, 0))
                    applied += 1
            except Exception:  # pragma: no cover
                pass
        return {"patterns": [p.name for p in patterns],
                "applied": applied, "dry_run": False}


__all__ = ["WindLoadPattern", "FastSAPWindPatternExporter"]
