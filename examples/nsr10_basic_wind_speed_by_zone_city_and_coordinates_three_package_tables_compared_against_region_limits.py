"""Velocidad básica de viento en Colombia (NSR-10 B.6): zonas, ciudades y coordenadas, y las tres tablas del paquete enfrentadas.

La NSR-10 distingue 5 regiones de amenaza eólica, de 17 m/s (60 km/h) en la región 1 a 36 m/s (130 km/h) en la
región 5, con 28 m/s (100 km/h) en buena parte del territorio (Arroyo Amell y Ramos Castillo, *Ingeniería y
Ciencia* 11(21), 2015, p. 181; NSR-10 Figura B.6.4-1, que no se ha consultado directamente). El paquete
tiene TRES tablas de ciudades que no coinciden entre sí: `NSR10_WIND_SPEED_BY_CITY` (la que usa
`nsr10_basic_wind_speed`), `vb_atlas` y `vb_map`; ninguna está contrastada con la figura. Este ejemplo las
pone una al lado de otra y marca, por cálculo, las que superan el máximo de 36 m/s de la región 5. Desde la
1.3 el paquete añade una zona 6 de 50 m/s para San Andrés y Providencia que la fuente citada no recoge.

Ejecutar:  python examples/nsr10_basic_wind_speed_by_zone_city_and_coordinates_three_package_tables_compared_against_region_limits.py
"""
from windloads.codes.nsr10_b6 import (
    NSR10_CITY_ZONES,
    NSR10_WIND_ZONES,
    nsr10_basic_wind_speed,
    nsr10_zone_from_coords,
)
from windloads.vb_atlas import vb_for
from windloads.vb_map import lookup_Vb

V_MAX_REGION_5 = 36.0   # 130 km/h


def main() -> None:
    print("Zonas NSR-10 del paquete (zonas 2 y 4 sin contrastar):")
    for z, v in NSR10_WIND_ZONES.items():
        extra = "  ← no figura en la fuente citada (5 regiones, máx. 36 m/s)" if v > V_MAX_REGION_5 else ""
        print(f"  zona {z}: {v:4.1f} m/s = {v * 3.6:5.0f} km/h{extra}")

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
          "por encima de la región 5. Usa la Figura B.6.4-1 del reglamento y pasa la velocidad como número.")

    print("\nClasificación por coordenadas (rectángulos aproximados de la figura, no polígonos):")
    for name, lat, lon in (("Barranquilla", 10.96, -74.80), ("Bogotá", 4.71, -74.07),
                           ("Leticia", -4.21, -69.94), ("Tumaco", 1.80, -78.76), ("Yopal", 5.34, -72.39)):
        z = nsr10_zone_from_coords(lat, lon)
        print(f"  {name:<13} ({lat:6.2f}, {lon:7.2f}) → zona {z} → {NSR10_WIND_ZONES[z]:.0f} m/s")
    try:
        nsr10_zone_from_coords(40.4, -3.7)
    except ValueError as exc:
        print(f"  Madrid (40,4; -3,7) → ValueError: {exc}")


if __name__ == "__main__":
    main()
