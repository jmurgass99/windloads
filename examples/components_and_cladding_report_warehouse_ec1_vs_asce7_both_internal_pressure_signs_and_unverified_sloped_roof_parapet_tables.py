"""Informe de componentes y revestimientos de una nave con `ComponentsAndCladding`: EN 1991-1-4 frente a ASCE 7.

Nave de B = 30 m (lado menor) y h = 8 m. EN 1991-1-4: q_p(8 m) en terreno II con v_b = 26 m/s, zonas de muro A, B,
D, E y de cubierta plana F, G, H, I con c_pe,1/c_pe,10 (Tablas 7.1 y 7.2). El informe usa UN solo c_pi (por
defecto +0,2): la presión hacia dentro de la zona D pide c_pi = −0,3, así que el ejemplo ejecuta los dos signos
y se queda con el pésimo. ASCE 7: q_h a 8 m con V = 45 m/s, exposición C, GCpi ±0,18 ya combinados por zona.

Las tablas de cubierta inclinada, cúpula y mansarda de ASCE 7 del paquete (Fig. 30.3-2B/2C/2D, «30.7-1») llevan
FIXME en el código y no se han contrastado; el ajuste de antepecho K_p = min(1 + 0,5·h_p, 1,5) no es el
procedimiento de §30.9. Se muestran como lo que son: estimaciones.

Ejecutar:  python examples/components_and_cladding_report_warehouse_ec1_vs_asce7_both_internal_pressure_signs_and_unverified_sloped_roof_parapet_tables.py
"""
from windloads import ComponentsAndCladding, TerrainProfile

B, H = 30.0, 8.0
AREAS = [1.0, 10.0]


def main() -> None:
    qp = TerrainProfile("EC1", "II").ec1_peak_velocity_pressure(H, 26.0)
    plus = ComponentsAndCladding("EC1", qp, B, H, cpi=0.2)
    minus = ComponentsAndCladding("EC1", qp, B, H, cpi=-0.3)
    print(f"EN 1991-1-4: q_p({H:.0f} m) = {qp:.0f} Pa; franja e/10 = {plus.corner_strip_width_m:.2f} m")
    print(f"  {'zona':>5} {'A [m²]':>6} {'c_pe':>6} {'w c_pi=+0,2':>12} {'w c_pi=−0,3':>12} {'pésima':>8}")
    rows_p = plus.wall_report(AREAS) + plus.roof_report(AREAS)
    rows_m = minus.wall_report(AREAS) + minus.roof_report(AREAS)
    worst_ec1 = {}
    for rp, rm in zip(rows_p, rows_m):
        w = max(rp["w_net_Pa"], rm["w_net_Pa"], key=abs)
        worst_ec1[(rp["zone"], rp["A_m2"])] = w
        print(f"  {rp['zone']:>5} {rp['A_m2']:6.0f} {rp['cpe']:6.2f} {rp['w_net_Pa']:12.0f} {rm['w_net_Pa']:12.0f} {w:8.0f}")
    gain = rows_m[2]["w_net_Pa"] / rows_p[2]["w_net_Pa"]
    print(f"  Zona D a 1 m²: con c_pi = −0,3 la presión es {gain:.2f} veces la del informe por defecto (c_pi = +0,2).")

    qh = TerrainProfile("ASCE7", "C").asce7_velocity_pressure(H, 45.0)
    cc = ComponentsAndCladding("ASCE7", qh, B, H, enclosure="enclosed")
    s = cc.summary(AREAS)
    print(f"\nASCE 7: q_h({H:.0f} m) = {qh:.0f} Pa; franja a = {s['corner_strip_a_m']} m")
    for r in s["walls"] + s["roof"]:
        print(f"  zona {r['zone']} ({r['surface']:>4}) A = {r['A_eff_m2']:4.0f} m²: GCp {r['GCp_pos']:+.2f}/{r['GCp_neg']:+.2f} "
              f"→ p = {r['p_pos_Pa']:+6.0f} / {r['p_neg_Pa']:+6.0f} Pa")

    print("\nEstimaciones con tablas sin contrastar (ASCE 7, A = 1 m²):")
    g = cc.gable_report(20.0, [1.0])
    print("  dos aguas 20°: " + ", ".join(f"{r['zone']} {r['p_neg_Pa']:.0f}" for r in g) + " Pa")
    d = cc.domed_report(0.2, [1.0])
    print("  cúpula f/D = 0,2: " + ", ".join(f"{r['zone']} {r['p_neg_Pa']:.0f}" for r in d) + " Pa")
    p = cc.parapet_adjustment(1.0)
    print(f"  antepecho h_p = 1 m: K_p = {p['K_p']} (aproximación propia), GCp −1,10 → {p['GCp_parapet_neg']}")


if __name__ == "__main__":
    main()
