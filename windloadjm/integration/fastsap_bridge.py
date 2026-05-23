"""Bridge windloadjm -> fastsap: aplica cargas de viento ASCE 7-22 a SAP2000.

Asume que el usuario tiene un modelo SAP2000 abierto con:
  - Joints definidos en la fachada barlovento y sotavento
  - Un Load Pattern tipo WIND ya creado (o se crea con create_load_pattern_if_missing)
  - Niveles identificables por altura z

El bridge convierte presiones [kN/m2] en cargas concentradas [kN] aplicadas
a los joints, distribuyendo el area tributaria de cada joint segun:
  F_joint = p_z * A_tributaria
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Iterable

log = logging.getLogger("windloadjm.fastsap_bridge")


@dataclass(frozen=True)
class WindLoadAssignment:
    """Asignacion de carga puntual a un joint."""
    joint_name: str
    Fx_kN: float
    Fy_kN: float = 0.0
    Fz_kN: float = 0.0
    Mx_kNm: float = 0.0
    My_kNm: float = 0.0
    Mz_kNm: float = 0.0


@dataclass
class WindBridgeResult:
    """Resultado de la aplicacion de cargas."""
    n_joints_loaded: int
    total_Fx_kN: float
    total_Fy_kN: float
    load_pattern: str
    notes: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


def _create_wind_pattern_if_missing(sap, pattern_name, fatal=False):
    """Crea load pattern tipo OTHER si no existe. Devuelve True si se creo."""
    sm = sap.SapModel
    try:
        names_ret = sm.LoadPatterns.GetNameList()
        # Tupla SAP: (count, NamesArray, ret)
        existing = list(names_ret[1]) if isinstance(names_ret, tuple) and len(names_ret) >= 2 else []
        if pattern_name in existing:
            return False
        # eLoadPatternType OTHER = 8
        try:
            ret = sm.LoadPatterns.Add(pattern_name, 8, 0.0, True)
        except Exception:
            ret = sm.LoadPatterns.Add(pattern_name, 8)
        if isinstance(ret, tuple):
            ret_code = int(ret[0])
        else:
            ret_code = int(ret)
        if ret_code != 0 and fatal:
            raise RuntimeError(f"LoadPatterns.Add({pattern_name}) devolvio {ret_code}")
        log.info("Load pattern '%s' creado", pattern_name)
        return True
    except Exception as exc:
        if fatal:
            raise
        log.warning("create_wind_pattern_if_missing fallo: %s", exc)
        return False


def apply_wind_loads_to_sap(sap, assignments,
                                load_pattern="WIND_ASCE7",
                                replace_existing=True,
                                fatal=False):
    """Aplica una lista de WindLoadAssignment a un modelo SAP2000.

    Args:
        sap: cliente con .SapModel (fastsap.SapClient u objeto duck-typed).
        assignments: iterable de WindLoadAssignment.
        load_pattern: nombre del load pattern destino.
        replace_existing: si True, sobrescribe cargas previas del mismo pattern.
        fatal: si True, levanta excepcion al primer fallo.

    Returns:
        WindBridgeResult con applied/failed/totales.
    """
    sm = sap.SapModel
    assignments = list(assignments)
    if not assignments:
        raise ValueError("assignments no puede estar vacio")

    _create_wind_pattern_if_missing(sap, load_pattern, fatal=fatal)

    result = WindBridgeResult(
        n_joints_loaded=0, total_Fx_kN=0.0, total_Fy_kN=0.0,
        load_pattern=load_pattern,
    )

    for a in assignments:
        f_vec = [
            float(a.Fx_kN) * 1000,    # SAP usa N internamente
            float(a.Fy_kN) * 1000,
            float(a.Fz_kN) * 1000,
            float(a.Mx_kNm) * 1000,
            float(a.My_kNm) * 1000,
            float(a.Mz_kNm) * 1000,
        ]
        try:
            # PointObj.SetLoadForce(Name, LoadPat, F[6], Replace=False,
            #                         CSys="Global", ItemType=0)
            ret = sm.PointObj.SetLoadForce(
                a.joint_name, load_pattern, f_vec,
                bool(replace_existing), "Global", 0,
            )
            ret_code = int(ret) if not isinstance(ret, tuple) else int(ret[0])
            if ret_code != 0:
                msg = f"SetLoadForce devolvio {ret_code}"
                result.failed[a.joint_name] = msg
                if fatal:
                    raise RuntimeError(f"{a.joint_name}: {msg}")
                continue
            result.applied.append(a.joint_name)
            result.total_Fx_kN += a.Fx_kN
            result.total_Fy_kN += a.Fy_kN
        except Exception as exc:
            result.failed[a.joint_name] = str(exc)
            if fatal:
                raise
            log.warning("apply_wind_loads(%s): %s", a.joint_name, exc)

    result.n_joints_loaded = len(result.applied)
    result.notes.append(
        f"Aplicadas {result.n_joints_loaded}/{len(assignments)} cargas, "
        f"sumF = ({result.total_Fx_kN:.1f}, {result.total_Fy_kN:.1f}) kN"
    )
    return result


def distribute_pressure_to_joints(joints, pressure_kN_m2, tributary_area_m2,
                                       direction="X"):
    """Convierte una presion uniforme + areas tributarias en assignments.

    Args:
        joints: iterable de nombres de joints (str).
        pressure_kN_m2: presion uniforme aplicar (kN/m2).
        tributary_area_m2: lista de areas tributarias por joint (m2),
            misma longitud que joints.
        direction: 'X' | 'Y' | 'Z' (sentido +).

    Returns:
        Lista de WindLoadAssignment.
    """
    joints = list(joints)
    areas = list(tributary_area_m2)
    if len(joints) != len(areas):
        raise ValueError(f"joints ({len(joints)}) y areas ({len(areas)}) deben tener misma longitud")
    if direction not in {"X", "Y", "Z"}:
        raise ValueError(f"direction debe ser X|Y|Z, recibido {direction}")

    out = []
    for j, A in zip(joints, areas):
        F = pressure_kN_m2 * A
        if direction == "X":
            out.append(WindLoadAssignment(joint_name=j, Fx_kN=F))
        elif direction == "Y":
            out.append(WindLoadAssignment(joint_name=j, Fy_kN=F))
        else:
            out.append(WindLoadAssignment(joint_name=j, Fz_kN=F))
    return out
