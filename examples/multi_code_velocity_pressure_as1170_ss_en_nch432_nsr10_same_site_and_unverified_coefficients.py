"""Presión de velocidad del mismo emplazamiento con los módulos multicódigo: AS 1170.2, SS EN 1991-1-4, NCh 432 y NSR-10.

Funciones de `codes_multi` y `nch432`, con los coeficientes que traen:
* AS 1170.2: V_site = V_R·M_d·M_z,cat·M_s·M_t y q = ½·1,2·V_site²; la tabla M_z,cat del módulo NO está
  contrastada con AS/NZS 1170.2 (en ella, terreno 2 a 10 m da 0,91).
* SS EN 1991-1-4: q_p = c_e·q_b con c_r, I_v de EN 1991-1-4 §4; v_b,0 = 26 m/s por defecto, sin contrastar con el
  anejo de Singapur. Se compara con `TerrainProfile` (método independiente del paquete): deben coincidir.
* NCh 432: q = 0,613·K_z·K_d·V²·I con exposiciones A-D de α = 4 / 4,5 / 7 / 9 — constantes SIN CONTRASTAR con
  NCh 432:2010; se muestra junto al K_z que darían las constantes de ASCE 7-05 (B: α = 7, z_g = 365,76 m).
* NSR-10: `evaluate_nsr10_wind` usa exposiciones B/C/D de ASCE 7-05 e I en q_z; `NSR10WindLoad` usa las
  categorías A-D de `windloads.terrain` (A ≈ D de ASCE, B ≈ C, C ≈ B, D con α = 5 y z_g = 457 m): se comprueba
  la equivalencia.

Ejecutar:  python examples/multi_code_velocity_pressure_as1170_ss_en_nch432_nsr10_same_site_and_unverified_coefficients.py
"""
from windloads import NSR10WindLoad, TerrainProfile
from windloads.codes_multi import (
    AS1170WindInput,
    NSR10WindInput,
    SSENWindInput,
    evaluate_as1170,
    evaluate_nsr10_wind,
    evaluate_ss_en_wind,
)
from windloads.nch432 import NCh432Input, evaluate_nch432

H = 20.0


def main() -> None:
    print(f"Altura z = {H} m\n")
    print("AS 1170.2, V_R = 45 m/s (M_d = M_s = M_t = 1):")
    for cat in ("1", "2", "3", "4"):
        r = evaluate_as1170(AS1170WindInput(V_R_m_s=45.0, height_m=H, terrain_category=cat))
        print(f"  TC{cat}: M_z,cat = {r.Mzcat:.3f}  V_site = {r.Vsite_m_s:5.2f} m/s  q = {r.qz_kPa:.3f} kPa")

    print("\nSS EN 1991-1-4, v_b = 26 m/s, frente a TerrainProfile (EN 1991-1-4 §4):")
    for cat in ("I", "II", "III", "IV"):
        ss = evaluate_ss_en_wind(SSENWindInput(Vb_0_m_s=26.0, height_m=H, terrain_category=cat))
        tp = TerrainProfile("EC1", cat).ec1_peak_velocity_pressure(H, 26.0) / 1000.0
        print(f"  {cat:>3}: c_e = {ss['ce']:.3f}  q_p = {ss['qp_kPa']:.4f} kPa   TerrainProfile {tp:.4f} kPa  "
              f"(diferencia {ss['qp_kPa'] - tp:+.1e})")

    print("\nNCh 432 (V_b = 32 m/s, clase II) con las constantes del módulo y K_z con α/z_g de ASCE 7-05:")
    asce705 = {"B": (7.0, 365.76), "C": (9.5, 274.32), "D": (11.5, 213.36)}
    for exp in ("A", "B", "C", "D"):
        r = evaluate_nch432(NCh432Input(Vb_m_s=32.0, h_m=H, importance_class="II", exposure=exp))
        ref = ""
        if exp in asce705:
            a, zg = asce705[exp]
            kz = 2.01 * (H / zg) ** (2 / a)
            ref = f"   K_z ASCE 7-05 {exp}: {kz:.3f} ({100 * (r.Kz / kz - 1):+.0f} %)"
        print(f"  {exp}: K_z = {r.Kz:.3f}  q_z = {r.qz_kN_m2:.3f} kN/m²{ref}")

    print("\nNSR-10, V = 33 m/s, I = 1,15: evaluate_nsr10_wind (B/C/D) frente a NSR10WindLoad (categorías A-D):")
    pairs = {"D": "A", "C": "B", "B": "C"}
    for exp, cat in pairs.items():
        a = evaluate_nsr10_wind(NSR10WindInput(V_m_s=33.0, height_m=H, exposure=exp, importance=1.15))
        wl = NSR10WindLoad(33.0, cat, building_height=H, importance_factor=1.15)
        print(f"  exposición {exp} → q_z = {a['qz_kPa']:.4f} kPa   NSR10WindLoad categoría {cat} → "
              f"q_z = {wl.qz_at(H) / 1000:.4f} kPa  (cociente {wl.qz_at(H) / 1000 / a['qz_kPa']:.4f})")
    print("Las dos rutas NSR-10 coinciden con esa equivalencia de letras (el z_g de codes_multi está redondeado al "
          "metro); la categoría D de NSR10WindLoad (α = 5, z_g = 457 m) no tiene pareja en las exposiciones B/C/D.")


if __name__ == "__main__":
    main()
