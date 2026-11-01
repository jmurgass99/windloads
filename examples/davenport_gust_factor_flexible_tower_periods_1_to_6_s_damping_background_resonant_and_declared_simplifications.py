"""Factor de ráfaga G_f de estructuras flexibles (ASCE 7, Davenport) para periodos de 1 a 6 s, y las simplificaciones del módulo.

`gust_factor_davenport` calcula G_f = 0,925·(1 + 1,7·I_z·√(g_Q²Q² + g_R²R²)) / (1 + 1,7·g_v·I_z) con g_Q = g_v = 3,4,
g_R = √(2 ln(3600 n₁)) + 0,577/√(2 ln(3600 n₁)), R_n = 7,47·N₁/(1 + 10,3·N₁)^(5/3), N₁ = n₁·L_z/V_z y
R_h con η = 4,6·n₁·h/V_z. I_z, L_z y V_z son ENTRADAS (no se calculan con la Tabla 26.11-1). Simplificaciones:
* Q usa (h + h) donde la norma escribe (B + h): equivale a suponer B = h;
* R = √(R_n·R_h/β) omite R_B·(0,53 + 0,47·R_L) (en la forma de ASCE 7-05, consultada en un ejemplo resuelto y no
  en el texto de ASCE 7-22). Como R_B ≤ 1 y 0,53 + 0,47·R_L ≤ 1, el módulo sobrestima R: el ejemplo calcula ese
  factor para una planta de 30 × 30 m para ver cuánto.

Caso: torre de h = 150 m, I_z = 0,20, L_z = 180 m, V_z = 40 m/s, β = 1 % y 2 %.

Ejecutar:  python examples/davenport_gust_factor_flexible_tower_periods_1_to_6_s_damping_background_resonant_and_declared_simplifications.py
"""
import math

from windloads.davenport import DavenportInput, gust_factor_davenport

H, IZ, LZ, VZ = 150.0, 0.20, 180.0, 40.0


def r_l(eta: float) -> float:
    return 1 / eta - (1 - math.exp(-2 * eta)) / (2 * eta ** 2) if eta > 0 else 1.0


def main() -> None:
    print(f"h = {H} m, I_z = {IZ}, L_z = {LZ} m, V_z = {VZ} m/s")
    print(f"  {'T [s]':>5} {'n1 [Hz]':>8} {'Q':>6} {'R β=1%':>7} {'G_f 1%':>7} {'R β=2%':>7} {'G_f 2%':>7}")
    rows = []
    for T in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0):
        r1 = gust_factor_davenport(DavenportInput(T, H, 0.01, IZ, LZ, VZ))
        r2 = gust_factor_davenport(DavenportInput(T, H, 0.02, IZ, LZ, VZ))
        rows.append((T, r1, r2))
        print(f"  {T:5.1f} {1 / T:8.3f} {r1.Q_background:6.3f} {r1.R_resonant:7.3f} {r1.G_f:7.3f} {r2.R_resonant:7.3f} {r2.G_f:7.3f}")
    print(f"El amortiguamiento del 2 % reduce G_f a T = 6 s de {rows[-1][1].G_f:.3f} a {rows[-1][2].G_f:.3f} "
          f"({100 * (rows[-1][2].G_f / rows[-1][1].G_f - 1):+.1f} %); a T = 1 s la parte resonante pesa menos "
          f"({100 * (rows[0][2].G_f / rows[0][1].G_f - 1):+.1f} %).")

    T, B, L = 4.0, 30.0, 30.0
    n1 = 1 / T
    rb = r_l(4.6 * n1 * B / VZ)
    rl = r_l(15.4 * n1 * L / VZ)
    factor = math.sqrt(rb * (0.53 + 0.47 * rl))
    print(f"\nTérmino omitido, T = {T} s, planta {B:.0f} × {L:.0f} m: R_B = {rb:.3f}, R_L = {rl:.3f}, "
          f"√(R_B·(0,53 + 0,47·R_L)) = {factor:.3f}: el R del módulo es {1 / factor:.2f} veces el de la forma completa.")
    q_full = math.sqrt(1 / (1 + 0.63 * ((B + H) / LZ) ** 0.63))
    q_mod = rows[3][1].Q_background
    side = "inseguro" if q_full > q_mod else "seguro"
    print(f"Q con (B + h) = {B + H:.0f} m sería {q_full:.3f} frente a {q_mod:.3f} con (h + h): con B < h la parte de fondo "
          f"queda del lado {side} ({100 * (q_mod / q_full - 1):+.1f} %).")
    print("Es un cálculo de predimensionamiento: R del lado seguro, Q del lado inseguro si B < h. Para un edificio esbelto "
          "real hay que evaluar I_z, L_z y V_z con la tabla de la norma y usar la forma completa o un ensayo en túnel.")


if __name__ == "__main__":
    main()
