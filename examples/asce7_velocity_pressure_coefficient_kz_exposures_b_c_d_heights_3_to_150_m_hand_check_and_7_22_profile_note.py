"""Coeficiente K_z y presión de velocidad q_z de ASCE 7 para las exposiciones B, C y D, con comprobación a mano.

`TerrainProfile("ASCE7", ...)` calcula K_z = 2,01·(z/z_g)^(2/α) con z ≥ 4,57 m (15 ft) y
q_z = 0,613·K_z·K_zt·K_d·V² [Pa], V en m/s (ráfaga de 3 s). Las constantes son las de la Tabla 26.11-1 de
ASCE 7-16 (α = 7,0 / 9,5 / 11,5; z_g = 365,76 / 274,32 / 213,36 m). ASCE 7-22 ajustó ese perfil (SEAOG,
«ASCE 7-22 wind changes», 2025: ligera reducción de K_z en B y C, sin cambio en D y hasta +20 % en
estructuras muy altas); el paquete NO incorpora ese ajuste. En ASCE 7-22 K_d pasa de q_z a las ecuaciones
de presión; el producto es el mismo.

Caso: V = 50 m/s (≈ 112 mph), K_d = 0,85, K_zt = 1.

Ejecutar:  python examples/asce7_velocity_pressure_coefficient_kz_exposures_b_c_d_heights_3_to_150_m_hand_check_and_7_22_profile_note.py
"""
from windloads import TerrainProfile

V = 50.0
EXPO = {"B": (7.0, 365.76), "C": (9.5, 274.32), "D": (11.5, 213.36)}


def main() -> None:
    tps = {e: TerrainProfile("ASCE7", e) for e in EXPO}
    print(f"V = {V} m/s, K_d = 0,85, K_zt = 1;  q_z = 0,613·K_z·K_zt·K_d·V²")
    print(f"  {'z [m]':>6}" + "".join(f"   K_z {e}  q_z {e} [Pa]" for e in EXPO))
    for z in (3.0, 4.57, 6.0, 10.0, 15.0, 20.0, 30.0, 50.0, 100.0, 150.0):
        row = "".join(f"   {tps[e].asce7_Kz(z):6.3f}  {tps[e].asce7_velocity_pressure(z, V):9.0f}" for e in EXPO)
        print(f"  {z:6.2f}{row}")

    alpha, zg = EXPO["C"]
    z = 10.0
    kz_hand = 2.01 * (z / zg) ** (2 / alpha)
    q_hand = 0.613 * kz_hand * 0.85 * V ** 2
    print("\nComprobación a mano, exposición C, z = 10 m:")
    print(f"  K_z = 2,01·(10/274,32)^(2/9,5) = {kz_hand:.4f} (TerrainProfile {tps['C'].asce7_Kz(z):.4f});"
          f"  q_z = 0,613·{kz_hand:.4f}·0,85·50² = {q_hand:.1f} Pa (TerrainProfile {tps['C'].asce7_velocity_pressure(z, V):.1f} Pa)")
    kz33 = tps["C"].asce7_Kz(33 * 0.3048)
    print(f"  Control: K_z(33 ft = 10,06 m, C) = {kz33:.3f}, el valor de referencia ≈ 1,0 de la exposición C.")

    r_bd = tps["D"].asce7_Kz(10.0) / tps["B"].asce7_Kz(10.0)
    print(f"\nA 10 m la exposición D da {r_bd:.2f} veces la presión de la B. Por debajo de 4,57 m K_z es constante "
          f"(B: {tps['B'].asce7_Kz(3.0):.3f} a 3 m y a 4,57 m).")
    print("TerrainProfile no aplica el factor de elevación K_e (solo lo acepta la memoria asce7_mwfrs): "
          "para emplazamientos altos hay que multiplicar q_z a mano.")


if __name__ == "__main__":
    main()
