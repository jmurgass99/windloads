"""Números de Strouhal del paquete frente a la Tabla E.1 de EN 1991-1-4, la API antigua de torbellinos y la divergencia (E.24).

`STROUHAL_NUMBERS` (API nueva) y `ST_TABLE` (API antigua) tienen valores distintos; los de EN 1991-1-4 Tabla E.1 /
Figura E.1 son: circular 0,18 para todo Re, rectángulo de aristas vivas d/b = 1 → 0,12, d/b = 2 → 0,06, perfil en H
d/b = 1 → 0,11. Las secciones hexagonal y octogonal no están en la Tabla E.1. Con b = 0,6 m y n = 1,5 Hz se calcula
v_crit = b·n/St con cada valor. `evaluate_vortex_shedding` (API antigua) declara «en banda» si
0,5 ≤ v_crit/V_b ≤ 1,25 y usa un a_G = −3 fijo para el galope: criterios propios, distintos de E.1.2(2)
(estudiar si v_crit ≤ 1,25·v_m) y de E.2.

Divergencia de un panel tipo cartel (E.4.3, E.24): v_div = √(2·k_Θ/(ρ·d²·dc_M/dΘ)); `divergence_critical_velocity`
toma k_Θ = EI/L, así que se le pasa EI = k_Θ y L = 1. El flameo 2-GDL del módulo (`flutter_2dof`) no es un modelo
válido y no se usa aquí.

Ejecutar:  python examples/strouhal_numbers_by_section_vs_en1991_table_e1_legacy_vortex_api_and_divergence_velocity_e24.py
"""
import math

from windloads.aeroelastic import divergence_critical_velocity
from windloads.vortex_shedding import ST_TABLE, STROUHAL_NUMBERS, VortexInput, critical_velocity, evaluate_vortex_shedding

B, N = 0.6, 1.5
EN_E1 = {"circular": 0.18, "square": 0.12, "rectangular d/b=2": 0.06, "H_section d/b=1": 0.11}


def main() -> None:
    print(f"b = {B} m, n = {N} Hz")
    print(f"  {'sección':<20} {'paquete':>8} {'EN Tabla E.1':>13} {'v_crit [m/s]':>13}")
    for name, st in STROUHAL_NUMBERS.items():
        en = EN_E1.get(name if name != "H_section" else "H_section d/b=1")
        en_txt = f"{en:.2f}" if en is not None else "—"
        print(f"  {name:<20} {st:8.2f} {en_txt:>13} {critical_velocity(N, B, st):13.2f}")
    print("  API antigua ST_TABLE: " + ", ".join(f"{k} {v}" for k, v in ST_TABLE.items()))
    print(f"  EN rectángulo d/b = 2: St = 0,06 → v_crit = {critical_velocity(N, B, 0.06):.2f} m/s (la mitad de St, el doble de v_crit)")

    print("\nAPI antigua frente al criterio E.1.2(2), v_m = 20 m/s:")
    for f1 in (1.5, 4.0, 8.0):
        r = evaluate_vortex_shedding(VortexInput(D_m=B, f1_Hz=f1, Vb_m_s=20.0, m_e_kg_m=120.0))
        need = r.v_critical_m_s <= 1.25 * 20.0
        print(f"  n = {f1:3.1f} Hz: v_crit = {r.v_critical_m_s:6.2f} m/s, «en banda» = {str(r.is_in_resonance_band):5}, "
              f"E.1.2(2) obliga a estudiarlo = {need}, galope (a_G fijo) = {r.galloping_risk}")

    k_theta, d, dcm = 4.0e4, 3.0, 1.0
    v_hand = math.sqrt(2 * k_theta / (1.25 * d ** 2 * dcm))
    v_lib = divergence_critical_velocity(EI=k_theta, L=1.0, c_M_alpha=dcm, rho_air=1.25, B=d)
    print(f"\nDivergencia (E.24): k_Θ = {k_theta:.0f} N·m/rad por metro, d = {d} m, dc_M/dΘ = {dcm} (dato supuesto):")
    print(f"  v_div = √(2·k_Θ/(ρ·d²·dc_M/dΘ)) = {v_hand:.2f} m/s (función {v_lib:.2f} m/s). E.4.2 exige además b/d < 0,25 "
          "y frecuencias de torsión bajas para que el panel sea propenso; si lo es, hay que consultar a un especialista.")


if __name__ == "__main__":
    main()
