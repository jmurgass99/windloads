"""Los cuatro casos de carga del MWFRS de ASCE 7 (Fig. 27.3-8): torsión con excentricidad del 15 % y envolvente.

`mwfrs_load_cases(Px, Py, Bx, By)`: caso 1, 100 % en cada eje por separado; caso 2, 75 % en un eje con
M_T = 0,75·P·e, e = 0,15·B; caso 3, 75 % en los dos ejes a la vez; caso 4, 56,3 % en ambos con
M_T = 0,563·(P_x·e_x + P_y·e_y). B es la dimensión en planta normal al viento de ese eje. Las fuerzas totales salen
de `ASCE7WindLoad` en las dos direcciones del mismo edificio (30 × 20 m, h = 35 m, V = 50 m/s, exposición C).

Ejecutar:  python examples/asce7_four_mwfrs_load_cases_figure_27_3_8_torsion_with_15_percent_eccentricity_and_envelope.py
"""
from windloads import ASCE7WindLoad
from windloads.mwfrs_load_cases import envelope, mwfrs_load_cases

LX, LY, H, V = 30.0, 20.0, 35.0, 50.0   # planta: 30 m en X, 20 m en Y


def main() -> None:
    # Viento según X: normal a la fachada de 20 m (B = 20, L = 30); según Y: B = 30, L = 20.
    wx = ASCE7WindLoad(V=V, exposure="C", building_height=H, width=LY, depth=LX, story_heights=[3.5] * 10)
    wy = ASCE7WindLoad(V=V, exposure="C", building_height=H, width=LX, depth=LY, story_heights=[3.5] * 10)
    Px, Py = wx.compute()["Vb_kN"], wy.compute()["Vb_kN"]
    Bx, By = LY, LX
    print(f"P_x = {Px:.0f} kN (B_x = {Bx:.0f} m, L/B = {LX / LY:.2f}),  P_y = {Py:.0f} kN (B_y = {By:.0f} m, L/B = {LY / LX:.2f})")
    cases = mwfrs_load_cases(Px, Py, Bx, By)
    print(f"  {'caso':>5} {'P_x [kN]':>9} {'P_y [kN]':>9} {'M_T [kN·m]':>11}")
    for c in cases:
        print(f"  {c.name:>5} {c.Px_kN:9.0f} {c.Py_kN:9.0f} {c.Mt_kNm:11.0f}")
    env = envelope(cases)
    m2x = 0.75 * Px * 0.15 * Bx
    m4 = 0.563 * (Px * 0.15 * Bx + Py * 0.15 * By)
    print(f"\nA mano: caso 2-X M_T = 0,75·{Px:.0f}·0,15·{Bx:.0f} = {m2x:.0f} kN·m; caso 4 M_T = 0,563·({Px:.0f}·{0.15 * Bx:.1f} + "
          f"{Py:.0f}·{0.15 * By:.1f}) = {m4:.0f} kN·m")
    gov = max(cases, key=lambda c: abs(c.Mt_kNm))
    print(f"Envolvente: P_x máx = {env['Px_max_kN']:.0f} kN, P_y máx = {env['Py_max_kN']:.0f} kN, "
          f"M_T máx = {env['Mt_max_kNm']:.0f} kN·m (caso {gov.name}).")
    print("La envolvente de máximos por separado no es una combinación: cada caso se analiza con su P_x, P_y y M_T "
          "simultáneos y con los dos signos de la excentricidad.")


if __name__ == "__main__":
    main()
