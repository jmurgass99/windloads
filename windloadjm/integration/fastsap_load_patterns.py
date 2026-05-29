"""Bridge WindLoadJm -> FastSAP: exporta patrones de carga de viento como joint loads."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger("windloadjm.fastsap_load_patterns")

# SAP2000 usa N internamente; los joint_loads vienen en kN.
_KN_TO_N = 1000.0


def _ret_code(ret) -> int:
    """Normaliza el retorno OAPI (int o tupla SAP) a un codigo entero."""
    if isinstance(ret, tuple):
        return int(ret[0])
    return int(ret)


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
        failed: dict[str, str] = {}
        for p in patterns:
            # 8=OTHER: cargas de viento calculadas externamente. NO 6=WIND, que
            # puede disparar la auto-generacion de viento de SAP (doble conteo).
            # Alinea con apply_wind_loads_to_sap.
            self.client.LoadPatterns.Add(p.name, 8)
            for j, (Fx, Fy, Fz) in p.joint_loads.items():
                # SAP usa N: convertir kN -> N antes de aplicar.
                f_vec = (Fx * _KN_TO_N, Fy * _KN_TO_N, Fz * _KN_TO_N, 0, 0, 0)
                try:
                    ret = self.client.PointObj.SetLoadForce(j, p.name, f_vec)
                    if _ret_code(ret) != 0:
                        failed[j] = f"SetLoadForce devolvio {_ret_code(ret)}"
                        log.warning("SetLoadForce(%s) ret != 0", j)
                        continue
                    applied += 1
                except Exception as exc:  # registra, no traga en silencio
                    failed[j] = str(exc)
                    log.warning("SetLoadForce(%s) lanzo: %s", j, exc)
        return {"patterns": [p.name for p in patterns],
                "applied": applied, "failed": failed, "dry_run": False}


__all__ = ["WindLoadPattern", "FastSAPWindPatternExporter"]
