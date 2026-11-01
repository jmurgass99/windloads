"""Capa de servicios (`windloads.services`): EC1, ASCE 7, NSR-10 y C&C delegan en los motores; comprobación cruzada y unidades.

Hasta 1.2.0 los servicios de ASCE 7 y NSR-10 llamaban a APIs inexistentes y caían siempre en cálculos propios
(NSR-10 con q_z = ½·ρ·(K_z·V)²·I y K_z inventado; ASCE 7 con Cp de sotavento fijo y la presión interior restada con
signos opuestos en la neta), y el de C&C devolvía una tabla fija sin área. Ahora:
* `compute_ec1` → `TerrainProfile` y Tabla 7.1 (kPa, m/s; v_m es la velocidad media);
* `compute_asce7` → unidades imperiales (mph, ft, psf), K_z con constantes de ASCE 7-16, neta q_h·G·(Cp_w − Cp_l);
* `compute_nsr10` → `nsr10_basic_wind_speed` + `NSR10WindLoad` (I sobre q_z);
* `compute_cc` → `asce7_GCp` con el área eficaz (presión exterior q_h·GCp, sin GCpi).
El ejemplo vuelve a calcular cada resultado con el motor o a mano y convierte unidades para comparar ASCE 7 en SI.

Ejecutar:  python examples/services_layer_ec1_asce7_nsr10_components_delegate_to_the_engines_cross_check_and_units.py
"""
from windloads import TerrainProfile, asce7_GCp
from windloads.codes.nsr10_b6 import NSR10WindLoad
from windloads.services.asce7 import ASCE7Input, compute_asce7
from windloads.services.components import CCInput, compute_cc
from windloads.services.ec1 import EC1Input, compute_ec1
from windloads.services.nsr10 import NSR10Input, compute_nsr10

PSF = 47.880258     # Pa por psf
MPH = 0.44704       # m/s por mph
FT = 0.3048


def main() -> None:
    r = compute_ec1(EC1Input(vb=26.0, height=24.0, width=20.0, depth=12.0, terrain_category=2))
    qp = TerrainProfile("EC1", "II").ec1_peak_velocity_pressure(24.0, 26.0) / 1000
    print(f"EC1: q_p(24 m) = {r.qp_at_height:.4f} kPa (motor {qp:.4f}), v_m = {r.vm_at_height:.2f} m/s, "
          f"c_pe D/E = {r.cp_windward}/{r.cp_leeward:.3f} (h/d = 2), neta {r.summary['p_net_windward_minus_leeward_kPa']} kPa")

    a = compute_asce7(ASCE7Input(V=110.0, height_ft=80.0, width_ft=100.0, depth_ft=150.0, exposure="C"))
    qh_si = TerrainProfile("ASCE7", "C").asce7_velocity_pressure(80 * FT, 110 * MPH) / PSF
    print(f"ASCE 7: q_h = {a.qh_psf:.2f} psf (TerrainProfile en SI → {qh_si:.2f} psf), L/B = 1,5 → Cp_l = {a.Cp_leeward:.2f}, "
          f"neta = {a.summary['net_psf']} psf = q_h·0,85·{0.8 - a.Cp_leeward:.2f} ({a.qh_psf * 0.85 * (0.8 - a.Cp_leeward):.2f})")
    print(f"        barlovento máx. {a.p_windward_psf:.2f} psf (con −GCpi), succión de sotavento máx. {a.p_leeward_psf:.2f} psf (con +GCpi)")

    n = compute_nsr10(NSR10Input(city="Cali", height_m=30.0, width_m=25.0, depth_m=25.0, Iw=1.15))
    wl = NSR10WindLoad("cali", "B", building_height=30.0, width=25.0, depth=25.0, importance_factor=1.15)
    print(f"NSR-10 Cali: V = {n.V_basic_kmh:.1f} km/h, q_h = {n.qz_kPa:.4f} kPa (NSR10WindLoad {wl.qh / 1000:.4f}, incluye I = 1,15), "
          f"neta {n.p_net_kPa:.4f} kPa = q_h·0,85·1,3")

    for zone, area in ((4, 0.5), (5, 5.0), (3, 20.0)):
        c = compute_cc(CCInput(zone=zone, area_m2=area, qh_kPa=1.2))
        surface = "wall" if zone in (4, 5) else "roof"
        ref = asce7_GCp(str(zone), area, surface, "neg")
        print(f"C&C zona {zone}, A = {area:4.1f} m²: GCp− = {c.GCp_negative:.3f} (asce7_GCp {ref:.3f}), "
              f"p− = {c.p_negative_kPa:.3f} kPa; {c.notes[-1]}")


if __name__ == "__main__":
    main()
