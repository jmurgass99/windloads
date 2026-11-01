"""Presión pico q_p(z) de EN 1991-1-4 §4.3-4.5 en las cinco categorías de terreno y comprobación a mano de la cascada a 10 m.

v_b = 26 m/s (c_dir = c_season = 1, ρ = 1,25 kg/m³, terreno llano c_o = 1). `TerrainProfile` aplica
c_r(z) = k_r·ln(z/z0) con k_r = 0,19·(z0/0,05)^0,07 (4.4-4.5), z_min de la Tabla 4.1,
I_v = 1/ln(z/z0) (4.7 con k_I = 1) y q_p = [1 + 7·I_v]·½·ρ·v_m² (4.8). Se tabula q_p y el factor de
exposición c_e = q_p/q_b de 2 a 100 m y se rehace a mano la cadena en terreno II a 10 m (el mismo caso
que el test dorado `test_golden_ec1_qp_cascade.py`: 993,84 Pa y c_e = 2,352).

Ejecutar:  python examples/ec1_peak_velocity_pressure_profile_terrain_categories_0_to_iv_and_hand_check_of_the_cascade_at_10_m.py
"""
import math

from windloads import TerrainProfile

VB = 26.0
RHO = 1.25
CATS = {"0": (0.003, 1.0), "I": (0.01, 1.0), "II": (0.05, 2.0), "III": (0.3, 5.0), "IV": (1.0, 10.0)}


def main() -> None:
    qb = 0.5 * RHO * VB ** 2
    print(f"v_b = {VB} m/s, q_b = ½·ρ·v_b² = {qb:.1f} Pa")
    print("\nq_p(z) [Pa] y c_e = q_p/q_b por categoría (Tabla 4.1: z0 / z_min)")
    print(f"  {'z [m]':>6}" + "".join(f"  {c + ' (' + str(z0) + ')':>13}" for c, (z0, _) in CATS.items()))
    profiles = {c: TerrainProfile("EC1", c) for c in CATS}
    for z in (2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 100.0):
        row = ""
        for c in CATS:
            qp = profiles[c].ec1_peak_velocity_pressure(z, VB, RHO)
            row += f"  {qp:7.0f} {qp / qb:5.2f}"
        print(f"  {z:6.0f}{row}")

    # Mano: terreno II, z = 10 m
    z0, zmin, z = 0.05, 2.0, 10.0
    kr = 0.19 * (z0 / 0.05) ** 0.07
    cr = kr * math.log(z / z0)
    vm = cr * VB
    Iv = 1.0 / math.log(z / z0)
    qp_hand = (1 + 7 * Iv) * 0.5 * RHO * vm ** 2
    qp_lib = profiles["II"].ec1_peak_velocity_pressure(z, VB, RHO)
    print("\nComprobación a mano, terreno II, z = 10 m:")
    print(f"  k_r = 0,19·(0,05/0,05)^0,07 = {kr:.4f};  c_r = k_r·ln(10/0,05) = {cr:.5f};  v_m = c_r·v_b = {vm:.3f} m/s")
    print(f"  I_v = 1/ln(200) = {Iv:.5f};  q_p = (1 + 7·I_v)·½·ρ·v_m² = {qp_hand:.2f} Pa  (TerrainProfile: {qp_lib:.2f} Pa, "
          f"diferencia {qp_lib - qp_hand:+.1e} Pa);  c_e = {qp_hand / qb:.4f}")

    q10 = {c: profiles[c].ec1_peak_velocity_pressure(10.0, VB, RHO) for c in CATS}
    print(f"\nA 10 m la categoría 0 da {q10['0'] / q10['IV']:.2f} veces la q_p de la categoría IV; "
          f"de II a III la presión baja un {100 * (1 - q10['III'] / q10['II']):.0f} %.")
    q3 = profiles["IV"].ec1_peak_velocity_pressure(3.0, VB, RHO)
    print(f"Por debajo de z_min la presión es constante: categoría IV, q_p(3 m) = q_p(10 m) = {q3:.0f} Pa.")
    print("No incluye el coeficiente de orografía (ver el ejemplo orography_*), ni c_dir/c_season distintos de 1, "
          "ni el anejo nacional: v_b,0 y los parámetros de la Tabla 4.1 son los recomendados.")


if __name__ == "__main__":
    main()
