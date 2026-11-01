"""Catálogo de Cp, techos complejos y seguidores solares: utilidades de orden de magnitud, NO normativas.

* `cp_catalog.CP_CATALOG`: Cp «típicos» por geometría y código, sin referencia a tabla ni condiciones.
* `cp_techos_complejos`: Cp de arco, multi-agua y diente de sierra; el argumento `code` no cambia nada y los
  valores no salen de ninguna norma identificada.
* `solar_trackers.evaluate_solar_tracker`: q_z = 0,613·0,85·V² sin K_z (la altura que se pasa no se usa) y
  GCp de entrada por defecto 1,5 / 1,0 atribuidos a SEAOC PV2 sin contrastar; §29.4.4 de ASCE 7 trata paneles
  sobre cubierta, no seguidores en suelo. El ejemplo cuantifica cuánto pesa no aplicar K_z a 2 m (exposición C).

Ejecutar:  python examples/indicative_cp_catalog_complex_roofs_and_solar_tracker_loads_declared_non_normative_with_missing_kz_check.py
"""
from windloads import TerrainProfile
from windloads.cp_catalog import CP_CATALOG, list_geometries, lookup_cp
from windloads.cp_techos_complejos import TechoComplejoInput, cp_techo_complejo
from windloads.solar_trackers import SolarTrackerInput, evaluate_solar_tracker


def main() -> None:
    print(f"Catálogo: {len(CP_CATALOG)} entradas, geometrías {', '.join(list_geometries())}")
    for g in ("box_LB1", "box_LB4", "cylinder"):
        for code in ("ASCE7", "EN1991", "AS1170"):
            e = lookup_cp(g, code)
            if e:
                print(f"  {g:<9} {code:<7} barlovento {e.Cp_windward:+.2f}  sotavento {e.Cp_leeward:+.2f}  "
                      f"lateral {e.Cp_side:+.2f}  {e.notes}")

    print("\nTechos complejos (el código no altera el resultado):")
    for code in ("EU", "US"):
        r = cp_techo_complejo(TechoComplejoInput(tipo="arco", f_h_ratio=0.2, code=code))
        print(f"  arco f/h = 0,2 [{code}]: {r.cp_zonas}")
    r = cp_techo_complejo(TechoComplejoInput(tipo="diente_sierra", n_aguas=4))
    print(f"  diente de sierra: {r.cp_zonas}")

    print("\nSeguidor solar (cuerda 2 m), V = 35 m/s:")
    for tilt in (0.0, 30.0, 60.0):
        for h in (2.0, 5.0):
            s = evaluate_solar_tracker(SolarTrackerInput(tilt_deg=tilt, height_m=h, Vb_m_per_s=35.0))
            print(f"  inclinación {tilt:4.0f}°, altura {h:.0f} m: q_z = {s.qz_Pa:6.0f} Pa, sustentación "
                  f"{s.lift_force_kN_per_m:5.2f} kN/m, momento {s.moment_kNm_per_m:5.2f} kN·m/m ({s.critical_mode})")
    kz = TerrainProfile("ASCE7", "C").asce7_Kz(2.0)
    print(f"La altura no cambia q_z: falta K_z. En exposición C, K_z(2 m) = {kz:.3f}, así que la función sobrestima q_z un "
          f"{100 * (1 / kz - 1):.0f} % a ras de suelo; en exposición B ({TerrainProfile('ASCE7', 'B').asce7_Kz(2.0):.3f}) "
          f"un {100 * (1 / TerrainProfile('ASCE7', 'B').asce7_Kz(2.0) - 1):.0f} %. Usa coeficientes de ensayo del fabricante "
          "para dimensionar un seguidor.")


if __name__ == "__main__":
    main()
