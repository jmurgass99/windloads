"""Plano DXF de cargas de viento por cara (`integration.dxf_wind_plan`) con coeficientes de EN 1991-1-4 y comprobación de las flechas.

Planta de 40 × 16 m (viento según x sobre la cara de 16 m), h = 12 m, terreno III, v_b = 27 m/s: q_p(12 m) y
c_pe,10 de la Tabla 7.1 (D barlovento, E sotavento, A lateral, la zona más desfavorable). `build_wind_plan_dxf`
dibuja el contorno (capa W-OUTLINE), una flecha por cara con su rótulo (W-PRESS si presiona, W-SUCT si succiona),
una leyenda (W-LEGEND/W-TEXT) y un cajetín. Hasta 1.2.0 las flechas salían al revés (las de presión nacían dentro
del edificio); el ejemplo lee el DXF con ezdxf y comprueba hacia dónde apunta cada una. Necesita el extra `dxf`.

Ejecutar:  python examples/dxf_wind_plan_pressure_and_suction_arrows_by_face_from_ec1_coefficients_entity_counts_and_arrow_check.py
"""
import os
from collections import Counter
from pathlib import Path

from windloads import TerrainProfile
from windloads.pressure import ec1_cpe_walls

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
LX, LY, H = 40.0, 16.0, 12.0


def main() -> None:
    try:
        import ezdxf
        from windloads.integration.dxf_wind_plan import build_wind_plan_dxf, from_wind_result
    except ImportError as exc:
        print(f"Extra 'dxf' no instalado ({exc}); pip install windloads[dxf]")
        return
    qp = TerrainProfile("EC1", "III").ec1_peak_velocity_pressure(H, 27.0) / 1000.0
    cpe = ec1_cpe_walls(H, LX)
    cps = {"windward": cpe["D"], "leeward": cpe["E"], "side_left": cpe["A"], "side_right": cpe["A"]}
    print(f"q_p(12 m) = {qp:.3f} kN/m²; h/d = {H / LX:.2f}: c_pe D = {cpe['D']:.2f}, E = {cpe['E']:.2f}, A = {cpe['A']:.2f}")
    inp = from_wind_result({"qz_kPa": qp}, [(0, 0), (LX, 0), (LX, LY), (0, LY)], project="Nave 40x16",
                           code="EN 1991-1-4", cp_by_face=cps)
    for z in inp.zone_loads:
        print(f"  {z.face:<10} c_pe = {z.cp:+.2f}  p = q_p·c_pe = {z.pressure_kPa:+.3f} kN/m²")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "plano_viento_nave_40x16.dxf"
    build_wind_plan_dxf(inp, path)

    msp = ezdxf.readfile(path).modelspace()
    counts = Counter(f"{e.dxftype()}@{e.dxf.layer}" for e in msp)
    print(f"DXF {path.name}: " + ", ".join(f"{k} ×{v}" for k, v in sorted(counts.items())))

    def main_arrow(layer, x_face):
        lines = [e for e in msp.query(f'LINE[layer=="{layer}"]')
                 if abs(e.dxf.start.x - x_face) < 1e-6 or abs(e.dxf.end.x - x_face) < 1e-6]
        return max(lines, key=lambda e: (e.dxf.end - e.dxf.start).magnitude)

    a = main_arrow("W-PRESS", 0.0)
    ok_p = a.dxf.start.x < 0.0 and abs(a.dxf.end.x) < 1e-9
    print(f"Barlovento (x = 0): flecha de ({a.dxf.start.x:.1f}, {a.dxf.start.y:.1f}) a ({a.dxf.end.x:.1f}, {a.dxf.end.y:.1f}) → "
          f"{'apunta hacia el edificio (presión)' if ok_p else 'MAL ORIENTADA'}")
    s = main_arrow("W-SUCT", LX)
    ok_s = abs(s.dxf.start.x - LX) < 1e-9 and s.dxf.end.x > LX
    print(f"Sotavento (x = {LX:.0f}): flecha de ({s.dxf.start.x:.1f}, {s.dxf.start.y:.1f}) a ({s.dxf.end.x:.1f}, {s.dxf.end.y:.1f}) → "
          f"{'sale del edificio (succión)' if ok_s else 'MAL ORIENTADA'}")
    print("El plano es esquemático: una flecha por cara con el c_pe dado, sin las zonas A/B/C a lo largo de las laterales "
          "ni las de cubierta; solo reconoce las caras windward/leeward/side_left/side_right de la caja envolvente (otra "
          "etiqueta se dibuja en el centro de la planta).")


if __name__ == "__main__":
    main()
