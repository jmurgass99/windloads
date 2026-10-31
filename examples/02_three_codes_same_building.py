"""Mismo edificio, tres normas de viento: EN 1991-1-4, ASCE 7-22 y NSR-10 B.6.

Edificio de 30 x 20 m en planta y 40 m de altura (13 plantas de 3 m más
antepecho). Se calcula el cortante basal y el momento de vuelco con cada
norma a partir de una velocidad básica comparable, y se listan las fuerzas
por planta, para ver la dispersión entre códigos antes de elegir el caso de
carga. El ejemplo `building_30x20x40.py` añade la exportación a JSON, CSV,
SAP2000 y ETABS.

Ejecutar:  python examples/02_three_codes_same_building.py
"""
from windloads import ASCE7WindLoad, EC1WindLoad, NSR10WindLoad

B, D, H = 30.0, 20.0, 40.0
STORIES = [3.0] * 13 + [1.0]


def main() -> None:
    cases = {
        "EN 1991-1-4 (v_b = 26 m/s, terreno II)": EC1WindLoad(
            vb=26.0, terrain_cat="II", building_height=H, width=B, depth=D,
            story_heights=STORIES, enclosure="closed"),
        "ASCE 7-22 (V = 40 m/s, exposición C)": ASCE7WindLoad(
            V=40.0, exposure="C", building_height=H, width=B, depth=D,
            story_heights=STORIES, risk_category="II", enclosure="enclosed"),
        "NSR-10 B.6 (Barranquilla, terreno B)": NSR10WindLoad(
            city_or_Vb="barranquilla", terrain_cat="B", building_height=H, width=B, depth=D,
            story_heights=STORIES, enclosure="cerrado"),
    }

    print(f"Edificio {B:.0f} x {D:.0f} m, H = {H:.0f} m, {len(STORIES) - 1} plantas\n")
    print(f"  {'norma':<40} {'q [Pa]':>8} {'V_b [kN]':>9} {'OTM [kN·m]':>11}")
    forces = {}
    for name, wl in cases.items():
        res = wl.compute()
        q = res.get("qp_top_Pa", res.get("qh_Pa"))
        print(f"  {name:<40} {q:8.0f} {res['Vb_kN']:9.0f} {res['OTM_kNm']:11.0f}")
        forces[name] = wl.story_forces()

    print("\nFuerzas por planta [kN] (las cuatro últimas plantas):")
    for name, sf in forces.items():
        tail = sf[-4:]
        vals = ", ".join(f"{f.Fx:.0f}" for f in tail)
        print(f"  {name:<40} {vals}")


if __name__ == "__main__":
    main()
