"""Coeficientes de presión exterior de muros, EN 1991-1-4 Tabla 7.1 (zonas A-E), su variación con h/d y presiones netas con c_pi.

`ec1_cpe_walls(h, d)` devuelve c_pe,10 (A −1,2; B −0,8; C −0,5; D +0,7…+0,8; E −0,3…−0,7, con interpolación lineal
en h/d); `ec1_cpe_local` interpola entre c_pe,1 y c_pe,10 con log10(A) (Figura 7.2). Caso de la ficha W00483
(CTE DB SE-AE, grado IV ≡ terreno III): nave de h = 10 m, d = 40 m, b = 40 m, v_b = 27 m/s → q_p(10) = 778,75 Pa;
con c_pi = +0,2 y −0,3 (§7.2.9(6) Nota 2) se obtiene la presión neta pésima de cada zona.

Ejecutar:  python examples/ec1_wall_pressure_coefficients_table_7_1_zones_a_to_e_vs_h_over_d_local_cpe1_and_net_pressures_with_cpi.py
"""
from windloads import EC1WindLoad, ec1_cpe_local, ec1_zone_width_e
from windloads.pressure import ec1_cpe_walls, ec1_lack_of_correlation_factor


def main() -> None:
    print("Tabla 7.1 interpolada (c_pe,10) y factor de falta de correlación §7.2.2(3):")
    print(f"  {'h/d':>5} {'A':>6} {'B':>6} {'C':>6} {'D':>6} {'E':>6} {'D−E':>6} {'f':>6}")
    for hd in (0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0):
        c = ec1_cpe_walls(hd * 10.0, 10.0)
        f = ec1_lack_of_correlation_factor(hd * 10.0, 10.0)
        print(f"  {hd:5.2f} {c['A']:6.2f} {c['B']:6.2f} {c['C']:6.2f} {c['D']:6.2f} {c['E']:6.2f} "
              f"{c['D'] - c['E']:6.2f} {f:6.3f}")

    h, d, b = 10.0, 40.0, 40.0
    wl = EC1WindLoad(vb=27.0, terrain_cat="III", building_height=h, width=b, depth=d)
    qp = wl.qp_at(h)
    e = ec1_zone_width_e(b, h)
    print(f"\nNave W00483: h = {h} m, d = {d} m, b = {b} m, terreno III, v_b = 27 m/s → q_p(10) = {qp:.2f} Pa")
    print(f"  e = min(b, 2h) = {e:.0f} m: zona A = e/5 = {e / 5:.0f} m, B hasta e = {e:.0f} m, C el resto ({d - e:.0f} m)")
    fp = wl.facade_pressures()
    print(f"  {'zona':>4} {'c_pe,10':>8} {'w c_pi=+0,2':>12} {'w c_pi=−0,3':>12} {'pésima [kPa]':>13}")
    for zone, v in fp.items():
        worst = max(v["w_net_pos_kPa"], v["w_net_neg_kPa"], key=abs)
        print(f"  {zone:>4} {v['cpe']:8.2f} {v['w_net_pos_kPa']:12.3f} {v['w_net_neg_kPa']:12.3f} {worst:13.3f}")
    hand_A = qp * (-1.2 - 0.2) / 1000
    print(f"  A mano zona A: q_p·(−1,2 − 0,2) = {hand_A:.3f} kPa (fila A: {fp['A']['w_net_pos_kPa']:.3f}). "
          f"Hasta 1.2.0 la zona A usaba −1,0 y salía {qp * (-1.0 - 0.2) / 1000:.3f} kPa.")

    print("\nc_pe local de la zona A según el área cargada (Figura 7.2):")
    for A in (0.5, 1.0, 2.0, 5.0, 10.0, 20.0):
        print(f"  A = {A:4.1f} m²: c_pe = {ec1_cpe_local('A', A):6.3f}")
    print("Para elementos de más de 10 m² vale c_pe,10; por debajo de 1 m², c_pe,1. Los muros con abertura dominante "
          "(c_pi = 0,75 o 0,90·c_pe de esa cara, §7.2.9(3)) no están implementados: EC1WindLoad los rechaza.")


if __name__ == "__main__":
    main()
