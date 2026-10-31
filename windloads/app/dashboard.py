"""Streamlit dashboard interactivo para WindLoads.

Ejecutar:
    streamlit run windloads/app/dashboard.py

Permite a usuarios no-Python:
    1. Elegir norma (EC1 / ASCE 7 / NSR-10).
    2. Introducir geometría y parámetros.
    3. Ver cargas calculadas + descargar JSON/CSV.

Usa el service layer de Mejora A. Si los servicios no están, fallback
al placeholder con un aviso.
"""
from __future__ import annotations
import json

try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit requerido: pip install windloads[ui]"
    )


def _ec1_panel():
    st.subheader("EC1 (EN 1991-1-4) — Wind on enclosed buildings")
    col1, col2 = st.columns(2)
    with col1:
        vb = st.number_input("vb (m/s)", value=25.0, min_value=10.0, max_value=80.0)
        height = st.number_input("Altura (m)", value=30.0, min_value=3.0)
        width = st.number_input("Ancho (m)", value=20.0, min_value=3.0)
    with col2:
        depth = st.number_input("Fondo (m)", value=40.0, min_value=3.0)
        terrain = st.selectbox("Terrain category", [0, 1, 2, 3, 4], index=2)
        c_dir = st.number_input("c_dir", value=1.0)

    if st.button("Calcular EC1"):
        try:
            from windloads.services.ec1 import EC1Input, compute_ec1
        except ImportError:
            st.error("services.ec1 no disponible. Instala windloads[api].")
            return
        res = compute_ec1(EC1Input(vb=vb, height=height, width=width,
                                      depth=depth, terrain_category=terrain,
                                      c_dir=c_dir))
        st.metric("qp(z) [kPa]", f"{res.qp_at_height:.3f}")
        st.metric("vm(z) [m/s]", f"{res.vm_at_height:.2f}")
        st.metric("p_windward [kPa]", f"{res.pressure_windward:.3f}")
        st.metric("p_leeward [kPa]", f"{res.pressure_leeward:.3f}")
        st.json(res.summary)
        st.download_button("Descargar JSON",
                            data=json.dumps(res.summary, indent=2),
                            file_name="ec1_result.json")


def _asce7_panel():
    st.subheader("ASCE 7-22 — Directional procedure")
    col1, col2 = st.columns(2)
    with col1:
        V = st.number_input("V (mph)", value=115.0, min_value=85.0, max_value=200.0)
        h_ft = st.number_input("Altura (ft)", value=100.0)
        b_ft = st.number_input("Ancho B (ft)", value=60.0)
    with col2:
        d_ft = st.number_input("Fondo D (ft)", value=120.0)
        expo = st.selectbox("Exposure", ["B", "C", "D"], index=1)
        Kzt = st.number_input("Kzt (topo)", value=1.0)

    if st.button("Calcular ASCE7"):
        try:
            from windloads.services.asce7 import ASCE7Input, compute_asce7
        except ImportError:
            st.error("services.asce7 no disponible.")
            return
        res = compute_asce7(ASCE7Input(V=V, height_ft=h_ft, width_ft=b_ft,
                                          depth_ft=d_ft, exposure=expo, Kzt=Kzt))
        st.metric("qh (psf)", f"{res.qh_psf:.2f}")
        st.metric("Kz", f"{res.Kz_at_height:.3f}")
        st.metric("p_windward (psf)", f"{res.p_windward_psf:.2f}")
        st.metric("p_leeward (psf)", f"{res.p_leeward_psf:.2f}")
        st.json(res.summary)


def _nsr10_panel():
    st.subheader("NSR-10 §B.6 — Colombia")
    cities = ["Bogotá", "Barranquilla", "Medellín", "Cali", "Cartagena",
              "Bucaramanga", "Manizales", "Pereira"]
    city = st.selectbox("Ciudad", cities)
    h_m = st.number_input("Altura (m)", value=30.0, min_value=3.0)
    b_m = st.number_input("Ancho (m)", value=20.0, min_value=3.0)
    d_m = st.number_input("Fondo (m)", value=40.0, min_value=3.0)
    expo = st.selectbox("Exposición", ["A", "B", "C", "D"], index=1)

    if st.button("Calcular NSR-10"):
        try:
            from windloads.services.nsr10 import NSR10Input, compute_nsr10
        except ImportError:
            st.error("services.nsr10 no disponible.")
            return
        res = compute_nsr10(NSR10Input(city=city, height_m=h_m,
                                          width_m=b_m, depth_m=d_m,
                                          exposure=expo))
        st.metric("V básico (km/h)", f"{res.V_basic_kmh:.0f}")
        st.metric("qz (kPa)", f"{res.qz_kPa:.4f}")
        st.metric("p neto (kPa)", f"{res.p_net_kPa:.4f}")
        st.json(res.summary)


def main():
    st.set_page_config(page_title="WindLoads", layout="wide")
    st.title("WindLoads — Wind Load Calculator (Multi-code)")
    st.caption("EC1 (EN 1991-1-4) · ASCE 7-22 · NSR-10 §B.6")
    tab1, tab2, tab3 = st.tabs(["EC1", "ASCE 7", "NSR-10"])
    with tab1:
        _ec1_panel()
    with tab2:
        _asce7_panel()
    with tab3:
        _nsr10_panel()
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Dashboard demo del service layer. Para integración programática usa "
        "`windloads.services` o la REST API (`uvicorn windloads.api:app`)."
    )


if __name__ == "__main__":
    main()
