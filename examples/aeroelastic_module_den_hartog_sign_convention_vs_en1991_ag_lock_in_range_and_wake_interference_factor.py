"""Módulo `aeroelastic`: convenio de signo de Den Hartog frente al a_G de EN 1991-1-4, rango de enganche e interferencia de estela.

`galloping_critical_velocity(m, fn, b, ρ, c_a_prime)` usa el coeficiente de Den Hartog H = dC_L/dα + C_D, NEGATIVO
cuando hay galope, y devuelve v = 2·Sc·n·b/|H|; si H ≥ 0 devuelve +inf («estable»). El a_G de la Tabla E.7 de
EN 1991-1-4 tiene el signo contrario (positivo = propenso). El ejemplo demuestra la trampa: pasar el a_G = 1,2 de un
cuadrado devuelve +inf, y pasar H = −1,2 devuelve lo mismo que `vortex_shedding.check_galloping(aG=1.2)`.
`lock_in_range` da [0,8; 1,2]·v_crit (banda propia del módulo, no de la norma) y `wake_buffeting` un factor de
interferencia 1,5 → 1,0 entre a/b = 3 y 20 para cilindros en tándem, también propio. Para dos cilindros
exentos con a/b < 3, EN 1991-1-4 E.3 da el galope de interferencia, v_CIG = 3,5·n·b·√((a/b)·Sc/a_IG) con
a_IG = 3 (Expresión E.23): se calcula aparte para comparar.

Ejecutar:  python examples/aeroelastic_module_den_hartog_sign_convention_vs_en1991_ag_lock_in_range_and_wake_interference_factor.py
"""
import math

from windloads.aeroelastic import galloping_critical_velocity, lock_in_range, wake_buffeting
from windloads.vortex_shedding import check_galloping, scruton_number

M, N, B, RHO, DELTA = 150.0, 2.0, 0.5, 1.25, 0.015


def main() -> None:
    en = check_galloping(D=B, fn=N, V=20.0, m_per_m=M, delta_s=DELTA, aG=1.2)
    wrong = galloping_critical_velocity(M, N, B, RHO, c_a_prime=1.2, delta=DELTA)
    right = galloping_critical_velocity(M, N, B, RHO, c_a_prime=-1.2, delta=DELTA)
    print("Cuadrado, a_G = 1,2 (Tabla E.7), m = 150 kg/m, n = 2 Hz, b = 0,5 m, δ = 0,015:")
    print(f"  vortex_shedding.check_galloping(aG=1.2)             v_CG = {en.V_CG:.2f} m/s")
    print(f"  aeroelastic.galloping_critical_velocity(+1.2)       v = {wrong} (lo trata como estable)")
    print(f"  aeroelastic.galloping_critical_velocity(H = −1.2)   v = {right:.2f} m/s")
    same = math.isclose(right, en.V_CG, rel_tol=1e-3)
    print(f"  Con el signo de Den Hartog ambas funciones {'coinciden' if same else 'NO coinciden'}; con el a_G tal cual "
          "la función de aeroelastic concluye lo contrario.")

    lo, hi, inside = lock_in_range(St=0.18, fn=1.2, b=1.0, U_mean=6.5)
    print(f"\nRango de enganche (banda ±20 %, criterio del módulo): {lo:.2f}-{hi:.2f} m/s; U = 6,5 m/s dentro: {inside}.")

    print("\nDos chimeneas de b = 1 m, n = 1,2 Hz, m = 250 kg/m, δ = 0,012 (Sc con E.4):")
    Sc = scruton_number(250.0, 0.012, 1.0)
    print(f"  {'a/b':>5} {'factor módulo':>14} {'crítico':>8} {'v_CIG (E.23) [m/s]':>19}")
    for a_b in (1.5, 2.0, 2.5, 3.0, 5.0, 10.0, 20.0):
        w = wake_buffeting(distance=a_b * 1.0, b=1.0, configuration="tandem")
        vcig = 3.5 * 1.2 * 1.0 * math.sqrt(a_b * Sc / 3.0) if a_b < 3 else float("nan")
        vtxt = f"{vcig:19.2f}" if a_b < 3 else f"{'— (a/b ≥ 3)':>19}"
        print(f"  {a_b:5.1f} {w.interference_factor:14.3f} {str(w.is_critical):>8} {vtxt}")
    print("El factor del módulo no es una magnitud de la norma: úsalo solo como alerta. Con a/b < 3 la referencia de "
          "EN 1991-1-4 es la velocidad crítica v_CIG de E.3, que el paquete no calcula.")


if __name__ == "__main__":
    main()
