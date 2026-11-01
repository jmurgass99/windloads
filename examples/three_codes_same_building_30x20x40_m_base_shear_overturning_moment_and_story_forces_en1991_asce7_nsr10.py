"""Mismo edificio con tres normas: EN 1991-1-4, ASCE 7 y NSR-10 B.6 (cortante basal, vuelco y fuerzas por planta).

Edificio de 30 × 20 m en planta (B = 30 m normal al viento, D = 20 m) y 40 m de altura (13 plantas de 3 m y
antepecho de 1 m). Velocidades de cada norma, que NO son equivalentes entre sí: EN 1991-1-4 v_b = 26 m/s (media
de 10 min, 50 años, terreno II); ASCE 7 V = 40 m/s (ráfaga de 3 s, exposición C, mapa de su categoría de riesgo);
NSR-10 V = 36 m/s (región 5, ráfaga de 3 s, categoría B del paquete ≈ exposición C). La comparación muestra la
dispersión que mezcla definición de velocidad, periodo de retorno, perfil y coeficientes; no es un ranking de
normas. EN 1991-1-4 aplica z_e por franjas (h = 40 m < 2b = 60 m: dos partes), c_pe,D − c_pe,E y f = 0,85+.

Ejecutar:  python examples/three_codes_same_building_30x20x40_m_base_shear_overturning_moment_and_story_forces_en1991_asce7_nsr10.py
"""
from windloads import ASCE7WindLoad, EC1WindLoad, NSR10WindLoad

B, D, H = 30.0, 20.0, 40.0
STORIES = [3.0] * 13 + [1.0]


def main() -> None:
    cases = {
        "EN 1991-1-4 (v_b = 26 m/s, terreno II)": EC1WindLoad(
            vb=26.0, terrain_cat="II", building_height=H, width=B, depth=D, story_heights=STORIES),
        "ASCE 7 (V = 40 m/s, exposición C)": ASCE7WindLoad(
            V=40.0, exposure="C", building_height=H, width=B, depth=D, story_heights=STORIES),
        "NSR-10 B.6 (V = 36 m/s, categoría B)": NSR10WindLoad(
            36.0, "B", building_height=H, width=B, depth=D, story_heights=STORIES),
    }
    print(f"Edificio {B:.0f} × {D:.0f} m, H = {H:.0f} m, {len(STORIES)} niveles de carga\n")
    print(f"  {'norma':<40} {'q(H) [Pa]':>9} {'V_b [kN]':>9} {'OTM [kN·m]':>11} {'brazo [m]':>9}")
    out = {}
    for name, wl in cases.items():
        r = wl.compute()
        q = r.get("qp_top_Pa", r.get("qh_Pa"))
        out[name] = r
        print(f"  {name:<40} {q:9.0f} {r['Vb_kN']:9.0f} {r['OTM_kNm']:11.0f} {r['OTM_kNm'] / r['Vb_kN']:9.1f}")
    vbs = [r["Vb_kN"] for r in out.values()]
    hi = max(out, key=lambda k: out[k]["Vb_kN"])
    lo = min(out, key=lambda k: out[k]["Vb_kN"])
    print(f"\nEl mayor cortante ({hi.split(' (')[0]}) es {max(vbs) / min(vbs):.2f} veces el menor ({lo.split(' (')[0]}).")

    print("\nFuerzas por planta [kN] (cuatro niveles superiores, de abajo arriba):")
    for name, wl in cases.items():
        tail = wl.story_forces()[-4:]
        print(f"  {name:<40} " + ", ".join(f"{f.Fx:.1f}" for f in tail))
    r_ec1 = out["EN 1991-1-4 (v_b = 26 m/s, terreno II)"]
    print(f"\nEN 1991-1-4: c_s·c_d = {r_ec1['Cs_Cd']} con estado «{r_ec1['Cs_Cd_status']}»: con 40 m hay que justificarlo "
          "(§6.3); ASCE 7 y NSR-10 usan G = 0,85 de edificio rígido sin comprobar la frecuencia.")


if __name__ == "__main__":
    main()
