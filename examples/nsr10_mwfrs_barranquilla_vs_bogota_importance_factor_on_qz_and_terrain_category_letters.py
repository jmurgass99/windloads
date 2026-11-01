"""NSR-10 B.6 con `NSR10WindLoad`: el mismo edificio en Barranquilla y en Bogotá, el factor de importancia sobre q_z y las letras de terreno.

La NSR-10 adoptó el procedimiento de ASCE 7-05 (Arroyo y Ramos, 2015), donde q_z = 0,613·K_z·K_zt·K_d·V²·I: el
factor de importancia multiplica la presión. Hasta 1.2.0 el paquete lo aplicaba a V (q ∝ I²: +32 % en vez de +15 %
para I = 1,15). Las categorías de terreno de `NSR10WindLoad` son A-D de `windloads.terrain` y NO las letras de la
norma (que, al seguir ASCE 7-05, usa B, C y D): A ≈ D de ASCE (costa), B ≈ C (abierto), C ≈ B (suburbano).
Las velocidades por ciudad salen de `NSR10_WIND_SPEED_BY_CITY`, sin contrastar (45 m/s en Barranquilla supera los
36 m/s de la región 5): el ejemplo calcula también con la velocidad de la zona.

Caso: edificio de 8 plantas de 3 m (h = 24 m), B = 20 m, L = 30 m, cerrado.

Ejecutar:  python examples/nsr10_mwfrs_barranquilla_vs_bogota_importance_factor_on_qz_and_terrain_category_letters.py
"""
from windloads import NSR10WindLoad
from windloads.codes.nsr10_b6 import NSR10_CITY_ZONES, NSR10_WIND_ZONES

H, B, L = 24.0, 20.0, 30.0
ST = [3.0] * 8


def main() -> None:
    print(f"h = {H} m, B = {B} m, L = {L} m")
    print(f"  {'caso':<42} {'V [m/s]':>8} {'q_h [Pa]':>9} {'V_b [kN]':>9} {'OTM [kN·m]':>11}")
    vb = {}
    for city, cat in (("barranquilla", "A"), ("barranquilla", "B"), ("bogota", "C")):
        for source in ("tabla de ciudad", "zona"):
            v = city if source == "tabla de ciudad" else NSR10_WIND_ZONES[NSR10_CITY_ZONES[city]]
            wl = NSR10WindLoad(v, cat, building_height=H, width=B, depth=L, story_heights=ST)
            r = wl.compute()
            vb[(city, cat, source)] = r["Vb_kN"]
            label = f"{city} terreno {cat} ({source})"
            print(f"  {label:<42} {r['Vb_basic_ms']:8.1f} {r['qh_Pa']:9.0f} {r['Vb_kN']:9.0f} {r['OTM_kNm']:11.0f}")

    ratio = vb[("barranquilla", "A", "tabla de ciudad")] / vb[("barranquilla", "A", "zona")]
    print(f"En Barranquilla la tabla de ciudad (45 m/s) da {ratio:.2f} veces el cortante de la región 5 (36 m/s).")

    w1 = NSR10WindLoad(27.0, "B", building_height=H, width=B, depth=L, story_heights=ST, importance_factor=1.0)
    w2 = NSR10WindLoad(27.0, "B", building_height=H, width=B, depth=L, story_heights=ST, importance_factor=1.15)
    w3 = NSR10WindLoad(27.0, "B", building_height=H, width=B, depth=L, story_heights=ST, importance_factor=0.87)
    print(f"\nFactor de importancia con V = 27 m/s: q_h(I = 1,15)/q_h(I = 1) = {w2.qh / w1.qh:.4f}, "
          f"q_h(0,87)/q_h(1) = {w3.qh / w1.qh:.4f}; V_b {w1.compute()['Vb_kN']:.0f} → {w2.compute()['Vb_kN']:.0f} kN.")
    print(f"  Vb_design = √I·V = {w2.Vb_design:.3f} m/s es una velocidad equivalente para reproducir q_z·I, no una "
          "velocidad de la norma; con la regla anterior (I·V) la relación habría sido 1,3225.")
    a = NSR10WindLoad(30.0, "A", building_height=H).qh
    d = NSR10WindLoad(30.0, "D", building_height=H).qh
    print(f"Categorías extremas con V = 30 m/s: A (costa) q_h = {a:.0f} Pa, D (α = 5) q_h = {d:.0f} Pa ({a / d:.2f} veces).")


if __name__ == "__main__":
    main()
