"""Fuerzas de viento por planta de EN 1991-1-4 en un edificio bajo (h ≤ b): z_e = h, falta de correlación y cálculo a mano.

`EC1WindLoad.story_forces` aplica §7.2.2 con las zonas D y E a la vez:
F_planta = c_s·c_d · f · (c_pe,D·q_p(z_e) − c_pe,E·q_p(h)) · b · h_planta, con z_e de la Figura 7.4 (aquí h ≤ b, así
que z_e = h en toda la fachada), sotavento con q_p(h) y f = 0,85 para h/d ≤ 1 (§7.2.2(3)); la presión interior se
cancela. Caso: oficinas de 4 plantas de 3 m (h = 12 m), b = 20 m, d = 12 m, terreno II, v_b = 26 m/s → h/d = 1,
c_pe,D = +0,8, c_pe,E = −0,5. Se compara con la regla anterior a 1.2.0, q_p(z_superior)·(c_pe,D + 0,3), que ignoraba
el sotavento, restaba un c_pi solo en barlovento y no aplicaba z_e ni f.

Ejecutar:  python examples/ec1_mwfrs_low_rise_story_forces_reference_height_and_lack_of_correlation_hand_check_vs_previous_rule.py
"""
import math

from windloads import EC1WindLoad, TerrainProfile

H, B, D, VB = 12.0, 20.0, 12.0, 26.0


def qp_hand(z: float) -> float:
    ln = math.log(max(z, 2.0) / 0.05)
    vm = 0.19 * ln * VB
    return (1 + 7 / ln) * 0.5 * 1.25 * vm * vm


def main() -> None:
    wl = EC1WindLoad(vb=VB, terrain_cat="II", building_height=H, width=B, depth=D, story_heights=[3.0] * 4)
    res = wl.compute()
    print(f"Edificio b × d × h = {B:.0f} × {D:.0f} × {H:.0f} m, terreno II, v_b = {VB} m/s; c_s·c_d = {res['Cs_Cd']} "
          f"({res['Cs_Cd_status']})")
    q12 = qp_hand(H)
    print(f"q_p(12 m) a mano = {q12:.2f} Pa (paquete {wl.qp_at(H):.2f} Pa)")
    tp = TerrainProfile("EC1", "II")
    print(f"  {'planta':>6} {'z_top':>6} {'z_e':>5} {'F [kN]':>8} {'a mano':>8} {'regla anterior':>15}")
    old_total = 0.0
    for f in wl.story_forces():
        hand = 0.85 * (0.8 * q12 + 0.5 * q12) * B * 3.0 / 1000
        old = tp.ec1_peak_velocity_pressure(f.z_top, VB) * (0.8 + 0.3) * B * 3.0 / 1000
        old_total += old
        print(f"  {f.story:6d} {f.z_top:6.1f} {H:5.1f} {f.Fx:8.2f} {hand:8.2f} {old:15.2f}")
    vb_hand = 0.85 * 1.3 * q12 * B * H / 1000
    print(f"Cortante basal: {res['Vb_kN']:.2f} kN (a mano 0,85·1,3·q_p(12)·20·12 = {vb_hand:.2f} kN); "
          f"regla anterior {old_total:.2f} kN ({100 * (old_total / res['Vb_kN'] - 1):+.1f} %).")
    print(f"Momento de vuelco en la base: {res['OTM_kNm']:.1f} kN·m (fuerzas en el centro de cada planta).")
    print("Con z_e = h la presión de barlovento es uniforme; la regla anterior la reducía en las plantas bajas "
          "(q_p(3 m) < q_p(12 m)), del lado inseguro en edificios anchos y bajos.")


if __name__ == "__main__":
    main()
