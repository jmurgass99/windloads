"""Torre de 60 m con EN 1991-1-4: alturas de referencia por franjas (Figura 7.4), fuerzas por planta, vuelco y estado de c_s·c_d.

Torre de 20 plantas de 3 m (h = 60 m), b = 20 m (transversal al viento), d = 30 m, terreno III, v_b = 27 m/s.
Como h > 2b, la fachada de barlovento se divide en una parte inferior con z_e = b (hasta 20 m), una superior con
z_e = h (los 20 m de arriba) y franjas intermedias con z_e = altura superior de cada planta. h/d = 2 → c_pe,D = +0,8,
c_pe,E = −0,55 (Tabla 7.1 interpolada) y f = 0,8875 (§7.2.2(3)). La suma por plantas se rehace en el ejemplo con
las mismas reglas escritas aparte. c_s·c_d = 1 sin justificar para h > 15 m: el resultado lo declara
«unverified_default» y hay que calcularlo con §6.3 o los Anexos B/C (el paquete no lo hace).

Ejecutar:  python examples/ec1_mwfrs_tall_building_60_m_reference_height_strips_figure_7_4_story_forces_overturning_and_cscd_status.py
"""
from windloads import EC1WindLoad, TerrainProfile

H, B, D, VB = 60.0, 20.0, 30.0, 27.0


def main() -> None:
    wl = EC1WindLoad(vb=VB, terrain_cat="III", building_height=H, width=B, depth=D, story_heights=[3.0] * 20)
    res = wl.compute()
    tp = TerrainProfile("EC1", "III")
    qh = tp.ec1_peak_velocity_pressure(H, VB)
    cE = -0.5 + (H / D - 1) / 4 * (-0.2)
    f = 0.85 + (H / D - 1) / 4 * 0.15
    print(f"h = {H:.0f} m, b = {B:.0f} m, d = {D:.0f} m (h/d = {H / D:.1f}): c_pe,E = {cE:.3f}, f = {f:.4f}, q_p(h) = {qh:.0f} Pa")
    print(f"  {'planta':>6} {'z_top':>6} {'z_e':>5} {'q_p(z_e)':>9} {'F [kN]':>8}")
    total_hand, otm_hand = 0.0, 0.0
    for s in wl.story_forces():
        ze = B if s.z_top <= B else (H if s.z_top >= H - B else s.z_top)
        F = f * (0.8 * tp.ec1_peak_velocity_pressure(ze, VB) - cE * qh) * B * 3.0 / 1000
        total_hand += F
        otm_hand += F * s.z_mid
        if s.story in (1, 3, 6, 7, 8, 10, 13, 14, 20):
            print(f"  {s.story:6d} {s.z_top:6.0f} {ze:5.0f} {s.qp_or_qz:9.0f} {s.Fx:8.2f}")
    print(f"Cortante basal {res['Vb_kN']:.1f} kN (suma independiente {total_hand:.1f} kN); vuelco {res['OTM_kNm']:.0f} kN·m "
          f"(independiente {otm_hand:.0f} kN·m); brazo equivalente {res['OTM_kNm'] / res['Vb_kN']:.1f} m.")
    flat = f * (0.8 - cE) * qh * B * H / 1000
    print(f"Con q_p(h) en toda la altura (simplificación habitual) saldría {flat:.0f} kN, "
          f"{100 * (flat / res['Vb_kN'] - 1):+.0f} % sobre el reparto por franjas.")
    print(f"c_s·c_d = {res['Cs_Cd']} → estado: {res['Cs_Cd_status']} (justificado: {res['Cs_Cd_justified']}).")


if __name__ == "__main__":
    main()
