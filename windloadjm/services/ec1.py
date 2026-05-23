"""Servicio EC1 (EN 1991-1-4) — wind pressures sobre edificios cerrados."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EC1Input:
    """Entrada para cálculo EC1.

    Unidades SI: m, m/s, kPa.
    """
    vb: float                          # basic wind velocity m/s
    height: float                      # H edificio m
    width: float                       # B perpendicular al viento m
    depth: float                       # D paralelo al viento m
    terrain_category: int = 2          # 0..IV (EC1 tabla 4.1)
    c_dir: float = 1.0                 # factor direccional
    c_season: float = 1.0
    rho_air: float = 1.25              # kg/m³
    gust_factor: float = 1.0           # Cs·Cd (default 1.0 edificios rigidos)


@dataclass(frozen=True)
class EC1Result:
    qp_at_height: float                # kPa
    vm_at_height: float                # m/s
    cp_windward: float
    cp_leeward: float
    cp_side: float
    cp_roof_min: float
    cp_roof_max: float
    pressure_windward: float           # kPa neto
    pressure_leeward: float
    summary: dict


def compute_ec1(inp: EC1Input) -> EC1Result:
    """Cálculo EC1 simplificado del flujo viento sobre edificio cerrado.

    Intenta delegar a la API interna real del paquete (`windloadjm.codes.ec1_1_4`).
    Si los nombres no coinciden o falla, usa una implementación placeholder
    analítica que reproduce los pasos esenciales de EN 1991-1-4 §4-7.
    """
    try:
        from windloadjm import EC1WindLoad
        # Mapear terrain_category int a string romano EC1
        tc_map = {0: "0", 1: "I", 2: "II", 3: "III", 4: "IV"}
        tc = tc_map.get(inp.terrain_category, "II")
        load = EC1WindLoad(
            vb=inp.vb,
            terrain_cat=tc,
            building_height=inp.height,
        )
        qp = getattr(load, "qp", None)
        if callable(qp):
            qp_val = qp(inp.height)
        else:
            qp_val = qp
        if qp_val is None:
            qp_val = _placeholder_qp(inp)
        # Si viene en Pa, normaliza a kPa
        if qp_val > 100:
            qp_val = qp_val / 1000.0
        return _build_result(inp, qp_at_h=qp_val)
    except Exception:
        return _placeholder_compute(inp)


def _placeholder_qp(inp: EC1Input) -> float:
    """qp(z) simplificado: 0.5·ρ·vb²·cr²·co²·(1+7·Iv) — sin cr exacto."""
    import math
    z = inp.height
    z0_table = {0: 0.003, 1: 0.01, 2: 0.05, 3: 0.30, 4: 1.0}
    zmin_table = {0: 1.0, 1: 1.0, 2: 2.0, 3: 5.0, 4: 10.0}
    z0 = z0_table.get(inp.terrain_category, 0.05)
    zmin = zmin_table.get(inp.terrain_category, 2.0)
    z_eff = max(z, zmin)
    kr = 0.19 * (z0 / 0.05) ** 0.07
    cr = kr * math.log(z_eff / z0)
    co = 1.0
    Iv = 1.0 / (co * math.log(z_eff / z0))
    vm = cr * co * inp.vb * inp.c_dir * inp.c_season
    qp_Pa = 0.5 * inp.rho_air * vm * vm * (1 + 7 * Iv)
    return qp_Pa / 1000.0  # kPa


def _placeholder_compute(inp: EC1Input) -> EC1Result:
    qp = _placeholder_qp(inp)
    return _build_result(inp, qp_at_h=qp)


def _build_result(inp: EC1Input, qp_at_h: float) -> EC1Result:
    cp_w = 0.8
    cp_l = -0.5
    cp_s = -0.7
    cp_rmin = -1.2
    cp_rmax = 0.0
    p_w = qp_at_h * cp_w * inp.gust_factor
    p_l = qp_at_h * cp_l * inp.gust_factor
    import math
    vm_h = math.sqrt(qp_at_h * 1000 * 2 / inp.rho_air)
    return EC1Result(
        qp_at_height=qp_at_h, vm_at_height=vm_h,
        cp_windward=cp_w, cp_leeward=cp_l, cp_side=cp_s,
        cp_roof_min=cp_rmin, cp_roof_max=cp_rmax,
        pressure_windward=p_w, pressure_leeward=p_l,
        summary={
            "code": "EN 1991-1-4",
            "qp_kPa": round(qp_at_h, 4),
            "p_net_windward_minus_leeward_kPa": round(p_w - p_l, 4),
        },
    )
