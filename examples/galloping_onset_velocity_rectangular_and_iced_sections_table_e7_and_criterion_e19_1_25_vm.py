"""Galope según EN 1991-1-4 E.2: velocidad de inicio v_CG (E.18) para secciones de la Tabla E.7 y criterio v_CG > 1,25·v_m (E.19).

`check_galloping` calcula Sc = 2·δ_s·m/(ρ·b²) y v_CG = 2·Sc·n₁·b/a_G, y marca `at_risk` cuando NO se cumple
v_CG > 1,25·v_m. Hasta 1.2.0 comparaba v_CG con v_m sin el margen de 1,25. a_G de la Tabla E.7: rectángulo
d/b = 1: 1,2; d/b = 1,5: 1,7; d/b = 2: 2; d/b = 1/2: 0,7; hielo sobre cable: 1,0; a_G = 10 si no se conoce.

Caso: pórtico de señalización con dintel cajón de b = 0,50 m transversal al viento, n₁ = 2,0 Hz,
m = 150 kg/m, δ_s = 0,015, v_m = 22 m/s a la altura de la amplitud máxima.

Ejecutar:  python examples/galloping_onset_velocity_rectangular_and_iced_sections_table_e7_and_criterion_e19_1_25_vm.py
"""
from windloads.vortex_shedding import check_galloping, critical_velocity

B, N1, M, DELTA, VM = 0.50, 2.0, 150.0, 0.015, 22.0
SECTIONS = {"rectángulo d/b = 1/2": 0.7, "hielo sobre cable": 1.0, "cuadrado d/b = 1": 1.2,
            "rectángulo d/b = 1,5": 1.7, "rectángulo d/b = 2": 2.0, "desconocida (a_G = 10)": 10.0}


def main() -> None:
    Sc = 2 * DELTA * M / (1.25 * B ** 2)
    print(f"b = {B} m, n₁ = {N1} Hz, m = {M} kg/m, δ_s = {DELTA} → Sc = 2·{DELTA}·{M}/(1,25·{B}²) = {Sc:.2f}; v_m = {VM} m/s")
    print(f"  {'sección (Tabla E.7)':<24} {'a_G':>5} {'v_CG [m/s]':>11} {'v_CG/(1,25·v_m)':>16} {'riesgo':>7}")
    risky = []
    for name, aG in SECTIONS.items():
        r = check_galloping(D=B, fn=N1, V=VM, m_per_m=M, delta_s=DELTA, aG=aG)
        hand = 2 * Sc * N1 * B / aG
        assert abs(r.V_CG - round(hand, 3)) < 1e-9
        if r.at_risk:
            risky.append(name)
        print(f"  {name:<24} {aG:5.1f} {r.V_CG:11.2f} {r.safety_ratio:16.3f} {'sí' if r.at_risk else 'no':>7}")
    print(f"Secciones que no cumplen (E.19): {', '.join(risky) if risky else 'ninguna'}.")

    m_need = 1.25 * VM * 2.0 * 1.25 * B ** 2 / (2 * 2 * DELTA * N1 * B)
    print(f"Para el rectángulo d/b = 2 haría falta m ≥ 1,25·v_m·a_G·ρ·b²/(4·δ_s·n₁·b) = {m_need:.0f} kg/m "
          f"(o el amortiguamiento equivalente) para cumplir.")
    vcrit = critical_velocity(N1, B, St=0.12)
    vcg = check_galloping(D=B, fn=N1, V=VM, m_per_m=M, delta_s=DELTA, aG=1.2).V_CG
    ratio = vcg / vcrit
    print(f"Interacción con torbellinos (E.20): cuadrado, v_crit = {vcrit:.2f} m/s (St = 0,12), v_CG/v_crit = {ratio:.2f} → "
          f"{'posible interacción, consultar a un especialista' if 0.7 < ratio < 1.5 else 'fuera del intervalo 0,7-1,5'}.")


if __name__ == "__main__":
    main()
