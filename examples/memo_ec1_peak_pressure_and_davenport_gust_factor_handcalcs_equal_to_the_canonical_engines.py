"""Memorias handcalcs de presión pico EN 1991-1-4 y de factor de ráfaga de Davenport, comparadas con los motores del paquete.

`ec1_peak_pressure_memo(v_b, c_e)` escribe q_b = ½·ρ·v_b² y q_p = c_e·q_b; c_e es una ENTRADA (Figura 4.2), así que
aquí se toma de `TerrainProfile` (c_e = q_p/q_b) y se comprueba que la memoria reproduce q_p. `gust_factor_memo`
reescribe la ecuación final de G_f con handcalcs reutilizando Q y R de `gust_factor_davenport`: el G_f de la memoria
debe coincidir con el del motor (mismas simplificaciones, ver el ejemplo davenport_*).

Casos: v_b = 27 m/s, terreno III, z = 10, 20 y 40 m; torre de 120 m con T = 3,5 s, β = 1,5 %, I_z = 0,22,
L_z = 170 m, V_z = 38 m/s.

Ejecutar:  python examples/memo_ec1_peak_pressure_and_davenport_gust_factor_handcalcs_equal_to_the_canonical_engines.py
"""
from windloads import TerrainProfile
from windloads.davenport import DavenportInput, gust_factor_davenport
from windloads.memos import ec1_peak_pressure_memo, gust_factor_memo


def main() -> None:
    tp = TerrainProfile("EC1", "III")
    qb = 0.5 * 1.25 * 27.0 ** 2
    print(f"q_b = ½·1,25·27² = {qb:.2f} Pa")
    for z in (10.0, 20.0, 40.0):
        qp = tp.ec1_peak_velocity_pressure(z, 27.0)
        latex, r = ec1_peak_pressure_memo(v_b=27.0, c_e=qp / qb)
        print(f"  z = {z:4.0f} m: c_e = {r.c_e:.4f}, memoria q_p = {r.q_p_Pa:8.2f} Pa, TerrainProfile {qp:8.2f} Pa, "
              f"LaTeX {len(latex)} caracteres")
    print("  La memoria no calcula c_e: hay que dárselo (Figura 4.2 o TerrainProfile).")

    latex, g = gust_factor_memo(natural_period_s=3.5, height_m=120.0, damping_ratio=0.015,
                                intensity_turbulence=0.22, Lz_m=170.0, Vz_m_per_s=38.0)
    canon = gust_factor_davenport(DavenportInput(3.5, 120.0, 0.015, 0.22, 170.0, 38.0))
    print(f"\nFactor de ráfaga: memoria G_f = {g.G_f:.5f}, motor {canon.G_f:.5f} "
          f"({'coinciden' if abs(g.G_f - canon.G_f) < 1e-12 else 'NO coinciden'}); Q = {g.Q:.4f}, R = {g.R:.4f}")
    for n in g.notes:
        print(f"  {n}")


if __name__ == "__main__":
    main()
