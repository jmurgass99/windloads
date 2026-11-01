"""Puente de datos al modelo canónico (`windloads.sap_bridge`): presión de viento → carga lineal en pilares de un pórtico.

`wind_to_load_pattern(p_Pa, b_trib, frames)` crea un `LoadPattern` de tipo Wind y una `ElementLoad` por barra con
w = p/1000·b_trib [kN/m]; `apply_wind_to_model` devuelve un `Model` nuevo (inmutable) con el patrón añadido una sola
vez y las cargas sumadas, sin llamadas COM. Caso: nave con pórticos cada 6 m, pilares de 7 m, EN 1991-1-4 terreno II,
v_b = 26 m/s, h/d = 7/30 → c_pe,D = +0,70 y c_pe,E = −0,30 (Tabla 7.1). La presión interior se omite: se cancela en
el empuje total del pórtico, no en los momentos de cada pilar, así que hay que añadirla como caso aparte. El empuje
horizontal total se comprueba a mano.

Ejecutar:  python examples/canonical_model_sap_bridge_wind_pressure_to_frame_line_loads_pa_to_kn_per_m_portal_frame.py
"""
from windloads import TerrainProfile
from windloads._common.model import Element, Material, Model, Node, Restraint, SectionRef
from windloads.pressure import ec1_cpe_walls
from windloads.sap_bridge import apply_wind_to_model, wind_to_load_pattern

H, SPAN, BAY = 7.0, 30.0, 6.0


def main() -> None:
    qp = TerrainProfile("EC1", "II").ec1_peak_velocity_pressure(H, 26.0)
    cpe = ec1_cpe_walls(H, SPAN)
    p_ww, p_lw = qp * cpe["D"], qp * cpe["E"]
    print(f"q_p(7 m) = {qp:.1f} Pa; c_pe,D = {cpe['D']:.2f}, c_pe,E = {cpe['E']:.2f} → p = {p_ww:.1f} / {p_lw:.1f} Pa")

    nodes = (Node("N1", 0, 0, 0), Node("N2", 0, 0, H), Node("N3", SPAN, 0, H), Node("N4", SPAN, 0, 0))
    sec = SectionRef("IPE450", "I")
    mat = Material("S275", 210000.0, 0.3, 275.0, 7850.0)
    elems = (Element("COL_W", "N1", "N2", sec, "S275"), Element("BEAM", "N2", "N3", sec, "S275"),
             Element("COL_L", "N4", "N3", sec, "S275"))
    base = Model(nodes=nodes, restraints=(Restraint("N1", True, True, True, True, True, True),
                                          Restraint("N4", True, True, True, True, True, True)),
                 materials=(mat,), sections=(sec,), elements=elems)

    pat, loads = wind_to_load_pattern(p_ww, BAY, ["COL_W"], pattern_name="W_X", direction="GlobalX")
    print(f"Barlovento: patrón {pat.name} ({pat.kind}), w = {loads[0].w_kN_m:.3f} kN/m = {p_ww:.1f}/1000·{BAY}")
    m1 = apply_wind_to_model(base, p_ww, BAY, ["COL_W"], "W_X", "GlobalX")
    # Sotavento: succión (p < 0) hacia fuera de la nave, que en el pilar de x = 30 m también es +X.
    m2 = apply_wind_to_model(m1, -p_lw, BAY, ["COL_L"], "W_X", "GlobalX")
    print(f"Modelo: {len(m2.patterns)} patrón(es) {[p.name for p in m2.patterns]}, {len(m2.element_loads)} cargas de barra:")
    total = 0.0
    for el in m2.element_loads:
        total += el.w_kN_m * H
        print(f"  {el.element_id:<6} w = {el.w_kN_m:+.3f} kN/m  {el.direction}  ({el.pattern})")
    hand = (p_ww - p_lw) / 1000 * BAY * H
    print(f"Empuje horizontal total = Σ w·H = {total:.2f} kN; a mano (p_D − p_E)·6·7/1000 = {hand:.2f} kN")
    print(f"El modelo base no cambia (inmutable): {len(base.element_loads)} cargas. Falta la cubierta (zonas F-I) y c_s·c_d.")


if __name__ == "__main__":
    main()
