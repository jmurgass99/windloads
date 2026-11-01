"""Desprendimiento de torbellinos en una chimenea de acero según EN 1991-1-4 Anexo E (aproximación 1), con los factores calculados a mano.

Chimenea de acero sin forro: b = 1,0 m, altura ℓ = 30 m, n₁ = 1,2 Hz, masa equivalente m_e = 250 kg/m y
δ_s = 0,012 (el valor de la base de la Figura D.3 para chimeneas de acero sin forro), terreno II, v_b = 26 m/s.
Pasos: v_crit = b·n/St con St = 0,18 (E.2, Tabla E.1); criterio E.1.2(2): hay que estudiarlo si v_crit ≤ 1,25·v_m
(E.1); Re = b·v_crit/ν con ν = 15·10⁻⁶ m²/s (E.5); Sc = 2·δ_s·m_e/(ρ·b²) (E.4); c_lat,0 de la Figura E.2,
leída aquí como recta en escala logarítmica entre 0,7 (Re = 3·10⁵) y 0,2 (Re = 5·10⁵); K_w de la Tabla E.5 para una
ménsula con L_j = 6·b; K = 0,13 (Tabla E.5) y y_F,max/b = (1/St²)·(1/Sc)·K·K_w·c_lat (E.7).
El paquete no evalúa c_lat con Re ni la reducción de la Tabla E.3: se le pasan c_lat y K_w calculados aquí.

Ejecutar:  python examples/vortex_shedding_steel_chimney_en1991_annex_e_critical_velocity_scruton_kw_clat_by_reynolds_and_amplitude_e7.py
"""
import math

from windloads import TerrainProfile
from windloads.vortex_shedding import check_vortex_shedding

B, L, N1, ME, DELTA = 1.0, 30.0, 1.2, 250.0, 0.012


def main() -> None:
    St = 0.18
    v_crit = B * N1 / St
    vm = TerrainProfile("EC1", "II").ec1_mean_wind_velocity(L, 26.0)
    print(f"v_crit = b·n/St = {B}·{N1}/{St} = {v_crit:.2f} m/s; v_m(30 m) = {vm:.1f} m/s; 1,25·v_m = {1.25 * vm:.1f} m/s")
    print(f"  → {'hay que estudiarlo' if v_crit <= 1.25 * vm else 'no hace falta estudiarlo'} (E.1: v_crit > 1,25·v_m lo exime)")
    Re = B * v_crit / 15e-6
    lg = (math.log10(Re) - math.log10(3e5)) / (math.log10(5e5) - math.log10(3e5))
    clat = 0.7 if Re <= 3e5 else (0.2 if Re >= 5e5 else 0.7 - 0.5 * lg)
    print(f"Re = {Re:.3g} → c_lat,0 = {clat:.3f} (zona de transición de la Figura E.2; el valor fijo del paquete es 0,2)")
    Sc = 2 * DELTA * ME / (1.25 * B ** 2)
    lam = L / B
    Lj_b = 6.0
    Kw = 3 * Lj_b / lam * (1 - Lj_b / lam + (Lj_b / lam) ** 2 / 3)
    print(f"Sc = 2·{DELTA}·{ME}/(1,25·1²) = {Sc:.2f};  K_w = 3·(6/{lam:.0f})·[1 − 6/{lam:.0f} + (6/{lam:.0f})²/3] = {Kw:.4f} (≤ 0,6)")

    y_hand = B / St ** 2 / Sc * 0.13 * Kw * clat
    r = check_vortex_shedding(D=B, fn=N1, V=v_crit, m_per_m=ME, delta_s=DELTA, St=St, K=0.13, K_w=Kw, clat=clat)
    print(f"y_F,max = b·(1/St²)(1/Sc)·K·K_w·c_lat = {y_hand * 1000:.1f} mm (paquete {r.y_max_m * 1000:.1f} mm), y/b = {r.y_over_D:.4f}")
    print(f"  Hipótesis L_j = 6·b válida si y/b < 0,1 (Tabla E.4): {'sí' if r.y_over_D < 0.1 else 'NO, hay que iterar'}.")
    y_b = r.y_over_D
    for it in range(1, 30):
        Lj = 6.0 if y_b < 0.1 else (12.0 if y_b > 0.6 else 4.8 + 12.0 * y_b)
        Kw_i = min(3 * Lj / lam * (1 - Lj / lam + (Lj / lam) ** 2 / 3), 0.6)
        y_new = check_vortex_shedding(D=B, fn=N1, V=v_crit, m_per_m=ME, delta_s=DELTA, St=St, K=0.13,
                                      K_w=Kw_i, clat=clat).y_over_D
        if abs(y_new - y_b) < 1e-5:
            break
        y_b = y_new
    print(f"  Iteración con L_j/b = 4,8 + 12·y/b (Tabla E.4): converge en {it} pasos a L_j/b = {Lj:.3f}, K_w = {Kw_i:.4f}, "
          f"y_F,max = {y_new * B * 1000:.1f} mm.")
    r = check_vortex_shedding(D=B, fn=N1, V=v_crit, m_per_m=ME, delta_s=DELTA, St=St, K=0.13, K_w=Kw_i, clat=clat)
    r_def = check_vortex_shedding(D=B, fn=N1, V=v_crit, m_per_m=ME, delta_s=DELTA)
    print(f"Con los valores por defecto (K_w = 0,6, c_lat = 0,2): y = {r_def.y_max_m * 1000:.1f} mm, "
          f"{100 * (r_def.y_max_m / r.y_max_m - 1):+.0f} % respecto al cálculo con c_lat por Reynolds.")
    Fw = ME * (2 * math.pi * N1) ** 2 * r.y_max_m
    print(f"Fuerza de inercia en la punta (E.6, Φ = 1): F_w = m·(2πn)²·y = {Fw:.0f} N/m.")
    print(f"Rango de enganche del paquete: {r.V_range_lo:.2f}-{r.V_range_hi:.2f} m/s (±30 % con Sc < 5; criterio propio, "
          "no de la norma).")


if __name__ == "__main__":
    main()
