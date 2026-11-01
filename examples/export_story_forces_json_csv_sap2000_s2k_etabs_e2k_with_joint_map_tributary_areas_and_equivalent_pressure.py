"""Exportación de fuerzas por planta a JSON, CSV, SAP2000 (.s2k) y ETABS (.e2k), con reparto a nudos por área tributaria.

Edificio de 30 × 20 m y 40 m (13 plantas de 3 m + antepecho de 1 m), EN 1991-1-4, terreno II, v_b = 26 m/s.
`from_envelope` convierte las fuerzas de `EC1WindLoad.story_forces` en un `LoadPattern`; con `tributary_widths_m`
publica la presión neta equivalente F·1000/(B·h_planta) (hasta 1.2.0 ignoraba el ancho y repetía q_p). `JointMap`
reparte cada fuerza entre nudos con pesos que suman 1; `to_sap_s2k` / `to_etabs_e2k` escriben fragmentos de
texto que hay que revisar e integrar en un modelo propio (no se han importado en SAP2000 ni ETABS en este
ejemplo). Se comprueba que la suma por nudos devuelve la fuerza de planta y que el vuelco del patrón (fuerzas en
la cota superior de cada planta, como se exportan) excede al del cálculo (centro de planta) en Σ F·h/2.

Ejecutar:  python examples/export_story_forces_json_csv_sap2000_s2k_etabs_e2k_with_joint_map_tributary_areas_and_equivalent_pressure.py
"""
import json
import os
import re
from pathlib import Path

from windloads import EC1WindLoad, JointMap, WindLoadCase, from_envelope, to_csv, to_etabs_e2k, to_json, to_sap_s2k

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
B, D, H = 30.0, 20.0, 40.0
STORIES = [3.0] * 13 + [1.0]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wl = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=H, width=B, depth=D, story_heights=STORIES)
    res = wl.compute()
    sf = wl.story_forces()
    pat = from_envelope(sf, name="WX+", direction="+X", tributary_widths_m=B)
    case = WindLoadCase(name="EC1_30x20x40", code="EC1", building={"B": B, "D": D, "H": H}, patterns=[pat],
                        meta={"vb_ms": 26.0, "terrain": "II"})
    to_json(case, OUT / "EC1_30x20x40.json")
    to_csv(case, OUT / "EC1_30x20x40.csv")
    print(f"V_b = {res['Vb_kN']} kN; patrón WX+: suma {pat.base_shear_kN:.2f} kN")
    p1 = pat.pressures_by_level[0]
    print(f"Planta 1: F = {p1.Fx_kN} kN → presión equivalente {p1.pressure_Pa:.1f} Pa = F·1000/(30·3) "
          f"({p1.Fx_kN * 1000 / (B * 3.0):.1f}); q_p(z_e) = {sf[0].qp_or_qz} Pa")

    corner, edge = 9.0, 18.0     # m² tributarios por fachada de 30 m: 2 esquinas + 2 intermedios
    jm = JointMap.by_tributary_area({s.story: [("C1", corner), ("E1", edge), ("E2", edge), ("C2", corner)]
                                     for s in pat.pressures_by_level})
    s2k = to_sap_s2k(pat, jm)
    e2k = to_etabs_e2k(pat, joint_map=jm)
    (OUT / "EC1_30x20x40.s2k").write_text(s2k, encoding="utf-8")
    (OUT / "EC1_30x20x40.e2k").write_text(e2k, encoding="utf-8")
    loads = [float(m) for m in re.findall(r"Joint=\w+\s+LoadPat=WX\+\s+CoordSys=GLOBAL\s+F1=([-\d\.]+)", s2k)]
    first4 = loads[:4]
    weights = ", ".join(f"{j} {w:.3f}" for j, w in jm.per_story[1])
    print(f".s2k planta 1: {first4} kN, suma {sum(first4):.4f} = F de planta {p1.Fx_kN}; pesos {weights}")
    print(f"Total de cargas en nudos del .s2k: {sum(loads):.2f} kN ({len(loads)} líneas)")
    print("Fragmentos:")
    print("  " + next(ln for ln in s2k.splitlines() if "Joint=C1" in ln).strip())
    print("  " + next(ln for ln in e2k.splitlines() if "STORYLOAD" in ln).strip())
    extra = sum(s.Fx * (s.z_top - s.z_mid) for s in sf)
    print(f"Vuelco: patrón (cota superior) {pat.overturning_moment_kNm:.1f} kN·m, cálculo (centro de planta) {res['OTM_kNm']:.1f} kN·m; "
          f"diferencia {pat.overturning_moment_kNm - res['OTM_kNm']:.1f} = Σ F·h/2 = {extra:.1f} kN·m")
    data = json.loads((OUT / "EC1_30x20x40.json").read_text(encoding="utf-8"))
    print(f"JSON: {len(data['patterns'][0]['pressures_by_level'])} niveles; ficheros .json, .csv, .s2k y .e2k en examples/out/")


if __name__ == "__main__":
    main()
