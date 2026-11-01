"""Informe Markdown de EN 1991-1-4 (`generar_reporte_ec1`): sin y con coeficiente de orografía, y z_min de la categoría.

El informe escribe k_r, c_r(z), v_m(z) y q_p(z) a la altura H con z_eff = max(H, z_min) de la Tabla 4.1 (hasta 1.2.0
usaba max(H, 10 m) para todas las categorías, con lo que en edificios de menos de 10 m sobrestimaba q_p). Sin
`c_o` declara la limitación de terreno llano; con `c_o` lo aplica a v_m y a I_v. Aquí c_o sale de
`ec1_orography_factor_A3` para una nave en la cresta de una loma (H = 25 m, L_u = 125 m → Φ = 0,2). Los
apartados 5 y 6 del informe son texto genérico: no calcula coeficientes de presión ni combinaciones.

Caso: nave de H = 7 m, 20 × 40 m, v_b,0 = 26 m/s, categoría II.

Ejecutar:  python examples/report_ec1_markdown_with_orography_factor_from_annex_a3_and_zmin_of_the_terrain_category.py
"""
import os
import re
from pathlib import Path

from windloads import TerrainProfile
from windloads.report_ec1 import EC1ReportInput, generar_reporte_ec1
from windloads.topography import ec1_orography_factor_A3

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))


def qp_of(md: str) -> float:
    return float(re.search(r"q_p\(z\)\s*=\s*([\d\.]+)\s*Pa", md).group(1))


def main() -> None:
    flat = generar_reporte_ec1(EC1ReportInput(vb_0_m_s=26.0, H_m=7.0, B_m=20.0, L_m=40.0, terrain_category=2))
    co = ec1_orography_factor_A3(z=7.0, x=0.0, H=25.0, Lu=125.0, kind="hill")
    hill = generar_reporte_ec1(EC1ReportInput(vb_0_m_s=26.0, H_m=7.0, B_m=20.0, L_m=40.0, terrain_category=2, c_o=co))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reporte_ec1_llano.md").write_text(flat, encoding="utf-8")
    (OUT / "reporte_ec1_loma.md").write_text(hill, encoding="utf-8")
    print(flat)
    q_flat, q_hill = qp_of(flat), qp_of(hill)
    q_ref = TerrainProfile("EC1", "II").ec1_peak_velocity_pressure(7.0, 26.0)
    q_old = TerrainProfile("EC1", "II").ec1_peak_velocity_pressure(10.0, 26.0)
    print(f"Comprobación: TerrainProfile q_p(7 m) = {q_ref:.2f} Pa (informe {q_flat:.2f} Pa); con la regla anterior "
          f"(z = 10 m) habría dado {q_old:.2f} Pa ({100 * (q_old / q_ref - 1):+.0f} %).")
    print(f"En la cresta de la loma c_o = {co:.4f} (Anexo A.3) → q_p = {q_hill:.2f} Pa, {q_hill / q_flat:.2f} veces el terreno llano.")
    lines = [ln for ln in hill.splitlines() if "c_o" in ln]
    print(f"Línea de orografía del informe con c_o: {lines[0]}")
    print("Ficheros: reporte_ec1_llano.md y reporte_ec1_loma.md en examples/out/.")


if __name__ == "__main__":
    main()
