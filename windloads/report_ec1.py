"""Reporte EC1 (EN 1991-1-4) - Acciones de viento completas en markdown."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EC1ReportInput:
    vb_0_m_s: float          # velocidad basica de referencia
    H_m: float
    B_m: float
    L_m: float
    terrain_category: int = 2
    estructura: str = "edificio rectangular"
    c_o: float | None = None # Coeficiente orográfico (None -> 1.0 declarado como limitación)


def generar_reporte_ec1(inp: EC1ReportInput) -> str:
    z0 = {0: 0.003, 1: 0.01, 2: 0.05, 3: 0.3, 4: 1.0}.get(inp.terrain_category, 0.05)
    kr = 0.19 * (z0 / 0.05) ** 0.07
    import math
    cr = kr * math.log(max(inp.H_m, 10) / z0)

    if inp.c_o is not None:
        co = float(inp.c_o)
        co_line = f"- c_o = {co:.4f} (EN 1991-1-4 §4.3.3 / Anexo A.3)"
    else:
        co = 1.0
        co_line = "- c_o = 1.000 (LIMITACIÓN: Terreno plano sin efecto orográfico según EN 1991-1-4 §4.3.3. En colinas/acantilados usar windloads.topography.ec1_orography_factor_A3)"

    vm = cr * co * inp.vb_0_m_s
    # Intensidad de turbulencia Iv(z) = kr / (co * ln(z/z0))
    iv = kr / (co * cr) if (co * cr) > 0 else 0.0
    qp = 0.5 * 1.25 * (vm ** 2) * (1 + 7 * iv) if cr > 0 else 0.0

    return (
        f"# Reporte EC1 - Acciones de Viento (EN 1991-1-4)\n\n"
        f"## 1. Velocidad basica\n- v_b,0 = {inp.vb_0_m_s} m/s\n"
        f"- v_b = c_dir * c_season * v_b,0 = {inp.vb_0_m_s} m/s\n\n"
        f"## 2. Categoria de terreno y orografia\n- Categoria {inp.terrain_category}, z0 = {z0} m\n"
        f"{co_line}\n\n"
        f"## 3. Velocidad media a z=H\n- k_r = {kr:.4f}\n- c_r(z) = {cr:.4f}\n- v_m(z) = {vm:.2f} m/s\n\n"
        f"## 4. Presion de calculo de la velocidad punta\n- q_p(z) = {qp:.2f} Pa = {qp/1000:.3f} kPa\n\n"
        f"## 5. Coeficientes de presion externa (EC1 §7.2)\n"
        f"- Estructura: {inp.estructura}\n"
        f"- Tablas A/B/D/E segun forma. Aplicar cp_ext * q_p para presiones netas.\n\n"
        f"## 6. Combinaciones\n- W_d = gamma_Q * q_p * c_pe * A\n"
    )


__all__ = ["EC1ReportInput", "generar_reporte_ec1"]
