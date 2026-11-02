"""Velocidad básica de viento en Colombia (NSR-10 B.6): zonas, ciudades y coordenadas, y las tres tablas del paquete enfrentadas.

La Figura B.6.4-1 de la NSR-10, en la versión del Decreto 1711 de 2021 (Anexo Técnico), distingue 7 regiones
de amenaza eólica con dos velocidades cada una: la de las combinaciones de B.2.3, de 17 m/s (60 km/h) en la
región 1 a 36 m/s (130 km/h) en la región 5 del continente, 44 m/s (160 km/h) en la isla de San Andrés
(región 6) y 49 m/s (175 km/h) en Providencia y Santa Catalina (región 7); y la de B.2.4, de 22 a 61 m/s.
`NSR10_WIND_ZONES` y `NSR10_WIND_ZONES_B24` copian esa tabla. El paquete tiene además TRES tablas de
ciudades que no coinciden entre sí: `NSR10_WIND_SPEED_BY_CITY` (la que usa `nsr10_basic_wind_speed` por
defecto), `vb_atlas` y `vb_map`. Este ejemplo las pone una al lado de otra y marca, por cálculo, las ciudades
del continente que superan los 36 m/s de la región 5.

Ejecutar:  python examples/nsr10_basic_wind_speed_by_zone_city_and_coordinates_three_package_tables_compared_against_region_limits.py
"""
from windloads.codes.nsr10_b6 import (
    NSR10_CITY_ZONES,
    NSR10_WIND_ZONES,
    NSR10_WIND_ZONES_B24,
    nsr10_basic_wind_speed,
    nsr10_zone_from_coords,
)
from windloads.vb_atlas import vb_for
from windloads.vb_map import lookup_Vb

V_MAX_REGION_5 = 36.0   # 130 km/h
# km/h tal como los imprime el mapa del decreto (los m/s están redondeados)
DECREE_KMH = {1: (60, 75), 2: (80, 100), 3: (100, 125), 4: (120, 150), 5: (130, 165), 6: (160, 200), 7: (175, 220)}


def main() -> None:
    print("Regiones NSR-10 (Decreto 1711 de 2021):  B.2.3              B.2.4")
    for z, v in NSR10_WIND_ZONES.items():
        v24 = NSR10_WIND_ZONES_B24[z]
        k23, k24 = DECREE_KMH[z]
        print(f"  región {z}: {v:4.1f} m/s ({k23:3d} km/h)   {v24:4.1f} m/s ({k24:3d} km/h)")

    cities = ["barranquilla", "cartagena", "santa_marta", "riohacha", "monteria", "bogota", "medellin",
              "cali", "bucaramanga", "cucuta", "villavicencio", "leticia", "tumaco"]
    print(f"\n  {'ciudad':<14} {'nsr10_basic':>11} {'zona→V':>9} {'vb_atlas':>9} {'vb_map':>7}  observación")
    above, disagree = [], []
    for c in cities:
        v_main = nsr10_basic_wind_speed(c)
        zone = NSR10_CITY_ZONES.get(c)
        v_zone = NSR10_WIND_ZONES[zone] if zone else None
        name = c.replace("_", " ").title()
        v_atlas = vb_for(name, "CO")
        loc = lookup_Vb(name)
        v_map = loc.Vb_m_s if loc else None
        vals = [v for v in (v_main, v_zone, v_atlas, v_map) if v is not None]
        notes = []
        if max(vals) - min(vals) > 0.5:
            notes.append(f"dispersión {max(vals) - min(vals):.0f} m/s")
            disagree.append(c)
        if v_main > V_MAX_REGION_5:
            notes.append("> 36 m/s (máx. región 5)")
            above.append(c)
        fmt = lambda v: f"{v:5.1f}" if v is not None else "  —  "
        zs = f"{zone}→{v_zone:4.1f}" if zone else "   —"
        print(f"  {name:<14} {v_main:11.1f} {zs:>9} {fmt(v_atlas):>9} {fmt(v_map):>7}  {'; '.join(notes)}")

    print(f"\n{len(disagree)} de {len(cities)} ciudades tienen valores distintos según la tabla; "
          f"{len(above)} ({', '.join(above)}) reciben de nsr10_basic_wind_speed más de 36 m/s, "
          "por encima de la región 5. Para seguir el mapa, pasa use_regional_map_b641=True o la velocidad como número.")

    print("\nClasificación por coordenadas (rectángulos aproximados de la figura, no polígonos):")
    for name, lat, lon in (("Barranquilla", 10.96, -74.80), ("Bogotá", 4.71, -74.07),
                           ("Leticia", -4.21, -69.94), ("Tumaco", 1.80, -78.76), ("Yopal", 5.34, -72.39),
                           ("San Andrés", 12.55, -81.70), ("Providencia", 13.35, -81.37)):
        z = nsr10_zone_from_coords(lat, lon)
        print(f"  {name:<13} ({lat:6.2f}, {lon:7.2f}) → zona {z} → {NSR10_WIND_ZONES[z]:.0f} m/s")
    try:
        nsr10_zone_from_coords(40.4, -3.7)
    except ValueError as exc:
        print(f"  Madrid (40,4; -3,7) → ValueError: {exc}")


if __name__ == "__main__":
    main()
