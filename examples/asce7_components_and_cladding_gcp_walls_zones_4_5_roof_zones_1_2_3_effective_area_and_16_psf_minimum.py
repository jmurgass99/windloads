"""Componentes y revestimientos de ASCE 7 Cap. 30: GCp de muros (zonas 4 y 5) y cubierta (1, 2, 3) frente al área eficaz.

`asce7_cc_pressure` interpola GCp linealmente en log(A) entre 10 ft² (0,929 m²) y 500 ft² (46,45 m²), combina el
GCp positivo con −GCpi y el negativo con +GCpi (cerrado ±0,18), p = q_h·(GCp − GCpi), y aplica el mínimo de
16 psf = 766 Pa (§30.2.2). Muros: Fig. 30.3-1 (h ≤ 60 ft), +1,0→+0,7 y −1,1→−0,8 (zona 4) / −1,4→−0,8 (zona 5).
La tabla de cubierta (zonas 1-3, θ ≤ 7°) del paquete NO se ha contrastado: ASCE 7-16/7-22 cambiaron esa
zonificación (zonas 1', 1, 2, 3). El módulo `cc_pressure` duplica las tablas; se comprueba que da lo mismo.

Caso: nave de B = 30 m (lado menor), h = 10 m, V = 45 m/s, exposición C → q_h = 0,613·K_h·0,85·V².

Ejecutar:  python examples/asce7_components_and_cladding_gcp_walls_zones_4_5_roof_zones_1_2_3_effective_area_and_16_psf_minimum.py
"""
import math

from windloads import TerrainProfile, asce7_GCp, asce7_cc_pressure, asce7_corner_distance_a
from windloads.cc_pressure import get_cc_pressure

B, H, V = 30.0, 10.0, 45.0


def main() -> None:
    qh = TerrainProfile("ASCE7", "C").asce7_velocity_pressure(H, V)
    a = asce7_corner_distance_a(B, H)
    print(f"q_h = {qh:.1f} Pa; franja de esquina a = max(min(0,1·B, 0,4·h), max(0,04·B, 0,9 m)) = {a:.2f} m")
    print(f"  {'A [m²]':>7} {'GCp4+':>6} {'GCp4−':>6} {'p4 [Pa]':>16} {'GCp5−':>6} {'p5− [Pa]':>9} "
          f"{'GCp1−':>6} {'GCp3−':>6} {'p3− [Pa]':>9}")
    for A in (0.5, 0.929, 2.0, 5.0, 10.0, 20.0, 46.45, 100.0):
        w4 = asce7_cc_pressure("4", A, qh, "wall")
        w5 = asce7_cc_pressure("5", A, qh, "wall")
        r1 = asce7_cc_pressure("1", A, qh, "roof")
        r3 = asce7_cc_pressure("3", A, qh, "roof")
        print(f"  {A:7.3f} {w4['GCp_pos']:6.2f} {w4['GCp_neg']:6.2f} {w4['p_pos_Pa']:7.0f}/{w4['p_neg_Pa']:7.0f}  "
              f"{w5['GCp_neg']:6.2f} {w5['p_neg_Pa']:9.0f} {r1['GCp_neg']:6.2f} {r3['GCp_neg']:6.2f} {r3['p_neg_Pa']:9.0f}")

    A = 5.0
    frac = (math.log10(A) - math.log10(0.929)) / (math.log10(46.45) - math.log10(0.929))
    hand = -1.4 + frac * (-0.8 + 1.4)
    print(f"\nA mano, zona 5, A = 5 m²: fracción log = {frac:.4f}; GCp = −1,4 + {frac:.4f}·0,6 = {hand:.4f} "
          f"(función {asce7_GCp('5', A, 'wall', 'neg'):.4f}); p = q_h·(GCp − 0,18) = {qh * (hand - 0.18):.0f} Pa")

    low = asce7_cc_pressure("4", 50.0, 600.0, "wall")
    print(f"Mínimo de 16 psf: con q_h = 600 Pa la zona 4 a 50 m² daría 600·(0,7 + 0,18) = {600 * 0.88:.0f} Pa → "
          f"se eleva a {low['p_pos_Pa']:.0f} Pa.")

    alt = get_cc_pressure("5", "wall", 5.0, H, "C", V)
    ref = asce7_cc_pressure("5", 5.0, qh, "wall")
    print(f"cc_pressure.get_cc_pressure (calcula q_h por su cuenta): {alt} Pa frente a "
          f"({ref['p_pos_Pa']}, {ref['p_neg_Pa']}) Pa de components: {'iguales' if alt == (ref['p_pos_Pa'], ref['p_neg_Pa']) else 'DISTINTOS'}.")
    print("Las presiones de cubierta usan la tabla θ ≤ 7° del paquete sin contrastar; las de muro, la Fig. 30.3-1. "
          "Para edificios de h > 60 ft (18,3 m) el paquete no tiene tablas de C&C.")


if __name__ == "__main__":
    main()
