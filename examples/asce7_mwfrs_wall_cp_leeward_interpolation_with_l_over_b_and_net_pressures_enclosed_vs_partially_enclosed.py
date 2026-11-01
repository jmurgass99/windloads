"""Cp de muros del MWFRS de ASCE 7 (Fig. 27.3-1): sotavento interpolado con L/B y presiones netas con GCpi.

Barlovento Cp = 0,8, lateral −0,7 y sotavento −0,5 (L/B ≤ 1), −0,3 (L/B = 2), −0,2 (L/B ≥ 4) con interpolación lineal
(valores de la Fig. 27.3-1 de ASCE 7-16, consultada en copia escaneada). Hasta 1.2.0 `asce7_Cp_walls` saltaba en
escalones: −0,3 ya en L/B = 1,01 y −0,2 en 2,01; el ejemplo reconstruye esa regla para cuantificar el cambio.
`WindPressure.asce7_wall_pressures` da p = q·G·Cp − q_h·(±GCpi) en cada muro; en la resultante del edificio la
presión interior se cancela, lo que se comprueba restando barlovento y sotavento con el mismo GCpi.

Caso: q_z = q_h = 1,20 kPa, G = 0,85, cerrado (±0,18) y parcialmente cerrado (±0,55).

Ejecutar:  python examples/asce7_mwfrs_wall_cp_leeward_interpolation_with_l_over_b_and_net_pressures_enclosed_vs_partially_enclosed.py
"""
from windloads import WindPressure
from windloads.pressure import asce7_Cp_walls


def old_step(LB: float) -> float:
    return -0.5 if LB <= 1.0 else (-0.3 if LB <= 2.0 else -0.2)


def main() -> None:
    print("Cp de sotavento frente a L/B:")
    print(f"  {'L/B':>5} {'1.2.0':>7} {'regla anterior':>15} {'diferencia neta (0,8 − Cp)':>27}")
    for LB in (0.5, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0):
        new = asce7_Cp_walls(LB * 10.0, 10.0, 10.0)["leeward"]
        old = old_step(LB)
        d = (0.8 - new) / (0.8 - old) - 1
        print(f"  {LB:5.1f} {new:7.3f} {old:15.2f} {100 * d:+26.1f} %")

    q = 1200.0
    print(f"\nPresiones de muro con q = {q:.0f} Pa, G = 0,85, L/B = 1,5:")
    for encl in ("enclosed", "partially_enclosed"):
        wp = WindPressure("ASCE7", encl)
        r = wp.asce7_wall_pressures(q, q, L=15.0, B=10.0, h=10.0)
        ww, lw = r["windward"], r["leeward"]
        net_pos = ww["p_net_pos_kPa"] - lw["p_net_pos_kPa"]
        net_neg = ww["p_net_neg_kPa"] - lw["p_net_neg_kPa"]
        print(f"  {encl:<19} barlovento {ww['p_net_pos_kPa']:+.3f}/{ww['p_net_neg_kPa']:+.3f} kPa, "
              f"sotavento {lw['p_net_pos_kPa']:+.3f}/{lw['p_net_neg_kPa']:+.3f} kPa, lateral "
              f"{r['side']['p_net_pos_kPa']:+.3f}/{r['side']['p_net_neg_kPa']:+.3f} kPa")
        print(f"  {'':<19} neta barlovento − sotavento: {net_pos:.3f} (+GCpi) y {net_neg:.3f} kPa (−GCpi) = "
              f"q·G·(0,8 + 0,4)/1000 = {q * 0.85 * 1.2 / 1000:.3f} kPa")
    print("La clasificación de cerramiento cambia la presión de cada muro (lo que dimensiona fachada y correas) pero no "
          "el cortante total del edificio.")


if __name__ == "__main__":
    main()
