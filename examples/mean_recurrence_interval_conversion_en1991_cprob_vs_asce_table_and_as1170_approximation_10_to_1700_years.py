"""Conversión de la velocidad básica a otros periodos de retorno: c_prob de EN 1991-1-4, tabla «ASCE» y aproximación AS 1170.2.

`velocity_for_MRI` multiplica V_50 por un factor que depende del código:
* EN 1991-1-4 §4.2(2)P Nota 4, Expresión (4.2), con K = 0,2 y n = 0,5 (valores recomendados):
  c_prob = [(1 − K·ln(−ln(1 − p))) / (1 − K·ln(−ln(0,98)))]^n, p = 1/T. Se comprueba a mano en T = 100 años.
* «ASCE»: tabla interna `_ASCE_TABLE` atribuida a ASCE 7-22 Tabla C26.5-2, SIN CONTRASTAR. Su factor en
  T = 50 años no es 1, de modo que con una entrada definida como V_50 devuelve V(50) ≠ V_50: el ejemplo lo
  calcula y lo muestra. No la uses sin revisar contra el comentario de la norma.
* AS 1170.2: aproximación (ln T / ln 50)^0,55, no la Tabla 3.1 de la norma.

Ejecutar:  python examples/mean_recurrence_interval_conversion_en1991_cprob_vs_asce_table_and_as1170_approximation_10_to_1700_years.py
"""
import math

from windloads.mri_generator import MRI_for_target_velocity, MRIInput, velocity_for_MRI

V50 = 26.0


def main() -> None:
    print(f"V_50 = {V50} m/s")
    print(f"  {'T [años]':>8} {'EN c_prob':>10} {'V EN':>6} {'ASCE f':>7} {'V ASCE':>7} {'AS f':>6} {'V AS':>6}")
    for T in (10, 25, 50, 100, 300, 700, 1700):
        en = velocity_for_MRI(MRIInput(V50, T, "EU"))
        us = velocity_for_MRI(MRIInput(V50, T, "ASCE"))
        au = velocity_for_MRI(MRIInput(V50, T, "AS"))
        print(f"  {T:8d} {en.factor:10.4f} {en.V_target_ms:6.2f} {us.factor:7.3f} {us.V_target_ms:7.2f} "
              f"{au.factor:6.3f} {au.V_target_ms:6.2f}")

    p = 1 / 100
    cprob = math.sqrt((1 - 0.2 * math.log(-math.log(1 - p))) / (1 - 0.2 * math.log(-math.log(0.98))))
    lib = velocity_for_MRI(MRIInput(V50, 100, "EU")).factor
    print(f"\nA mano, EN T = 100 años: c_prob = √[(1 − 0,2·ln(−ln 0,99))/(1 − 0,2·ln(−ln 0,98))] = {cprob:.5f} "
          f"(función {lib:.5f}); la presión crece con c_prob² = {cprob ** 2:.4f}.")
    f50 = velocity_for_MRI(MRIInput(V50, 50, "ASCE")).factor
    print(f"Tabla «ASCE»: factor en T = 50 años = {f50:.2f}, no 1: con V_50 = {V50} m/s devuelve "
          f"V(50) = {V50 * f50:.1f} m/s ({100 * (f50 - 1):+.0f} %). Incoherente con su propia definición de entrada.")
    T_inv = MRI_for_target_velocity(V50, 28.0, "EU")
    print(f"Inversa (bisección, EN): V = 28 m/s corresponde a T ≈ {T_inv:.0f} años con V_50 = {V50} m/s.")


if __name__ == "__main__":
    main()
