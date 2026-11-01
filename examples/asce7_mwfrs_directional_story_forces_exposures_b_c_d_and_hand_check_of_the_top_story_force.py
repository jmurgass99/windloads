"""MWFRS de ASCE 7 por el procedimiento direccional (Cap. 27): fuerzas por planta en exposiciones B, C y D y comprobación a mano.

`ASCE7WindLoad.story_forces` usa en cada planta la presión neta barlovento − sotavento:
p = q_z·G·0,8 − q_h·G·Cp_l (la presión interior se cancela), con q_z a la cota superior de la planta, q_h a la
altura media de cubierta, G = 0,85 (rígido) y Cp_l de la Fig. 27.3-1 interpolado con L/B. K_z con las constantes de
ASCE 7-16 (el ajuste de perfil de ASCE 7-22 no está incorporado). Caso: edificio de 10 plantas de 3,5 m
(h = 35 m), B = 30 m (normal al viento), L = 45 m (L/B = 1,5 → Cp_l = −0,4), V = 50 m/s, cerrado.

Ejecutar:  python examples/asce7_mwfrs_directional_story_forces_exposures_b_c_d_and_hand_check_of_the_top_story_force.py
"""
from windloads import ASCE7WindLoad

H, B, L, V = 35.0, 30.0, 45.0, 50.0


def main() -> None:
    print(f"h = {H} m, B = {B} m, L = {L} m (L/B = {L / B}), V = {V} m/s, K_d = 0,85, G = 0,85")
    res = {}
    for exp in ("B", "C", "D"):
        wl = ASCE7WindLoad(V=V, exposure=exp, building_height=H, width=B, depth=L, story_heights=[3.5] * 10)
        res[exp] = (wl, wl.compute())
    print(f"  {'exp.':>4} {'q_h [Pa]':>9} {'V_b [kN]':>9} {'OTM [kN·m]':>11} {'Cp_l':>6}")
    for exp, (wl, r) in res.items():
        print(f"  {exp:>4} {r['qh_Pa']:9.0f} {r['Vb_kN']:9.0f} {r['OTM_kNm']:11.0f} {r['facade_pressures']['leeward']['Cp']:6.2f}")

    wl, r = res["C"]
    top = wl.story_forces()[-1]
    qz, qh = wl.qz_at(top.z_top), wl.qh
    p = qz * 0.85 * 0.8 - qh * 0.85 * (-0.4)
    F = p * B * 3.5 / 1000
    print(f"\nA mano, exposición C, planta 10 (z = {top.z_top:.0f} m = h): q_z = q_h = {qh:.1f} Pa;")
    print(f"  p = q_z·0,85·0,8 + q_h·0,85·0,4 = {p:.1f} Pa; F = p·B·3,5 = {F:.2f} kN (paquete {top.Fx:.2f} kN)")
    first = wl.story_forces()[0]
    print(f"  Planta 1 (z = 3,5 m → K_z con 4,57 m): F = {first.Fx:.2f} kN; el sotavento a q_h pesa "
          f"{100 * (qh * 0.85 * 0.4) / (wl.qz_at(first.z_top) * 0.85 * 0.8 + qh * 0.85 * 0.4):.0f} % de esa presión.")
    rb, rd = res["B"][1]["Vb_kN"], res["D"][1]["Vb_kN"]
    print(f"La exposición D da {rd / rb:.2f} veces el cortante de la B en este edificio.")
    print("Solo muros de barlovento y sotavento: la cubierta, el caso de torsión (Fig. 27.3-8, ver el ejemplo de los "
          "cuatro casos) y el factor de ráfaga flexible (Davenport) van aparte.")


if __name__ == "__main__":
    main()
