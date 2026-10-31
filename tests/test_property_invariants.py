"""Property-based tests de invariantes físicas de cargas de viento.

Usa hypothesis para generar casos aleatorios y verificar propiedades
fundamentales que SIEMPRE deben cumplirse independientemente de los
parámetros particulares.
"""
from __future__ import annotations
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st, assume, settings


pytestmark = [pytest.mark.property]


# -----------------------------------------------------------------------------
# Strategies — parámetros físicamente plausibles
# -----------------------------------------------------------------------------

valid_vb = st.floats(min_value=15.0, max_value=70.0)           # m/s básico EC1
valid_V_mph = st.floats(min_value=85.0, max_value=200.0)       # mph ASCE7
valid_height = st.floats(min_value=3.0, max_value=200.0)        # m
valid_width = st.floats(min_value=3.0, max_value=200.0)
valid_terrain = st.integers(min_value=0, max_value=4)
valid_exposure = st.sampled_from(["B", "C", "D"])
valid_zone = st.integers(min_value=1, max_value=5)
valid_qh = st.floats(min_value=0.1, max_value=5.0)             # kPa


# -----------------------------------------------------------------------------
# Invariantes EC1
# -----------------------------------------------------------------------------

@given(vb=valid_vb, height=valid_height, width=valid_width,
        depth=valid_width, terrain=valid_terrain)
@settings(max_examples=30, deadline=2000)
def test_ec1_qp_positive(vb, height, width, depth, terrain):
    """qp(z) siempre > 0 para inputs físicamente válidos."""
    try:
        from windloads.services.ec1 import EC1Input, compute_ec1
    except ImportError:
        pytest.skip("services.ec1 no disponible")
    res = compute_ec1(EC1Input(vb=vb, height=height, width=width, depth=depth,
                                  terrain_category=terrain))
    assert res.qp_at_height > 0
    assert res.vm_at_height > 0


@given(vb=valid_vb, h1=valid_height, h2=valid_height,
        terrain=valid_terrain)
@settings(max_examples=20, deadline=2000)
def test_ec1_qp_increases_with_height(vb, h1, h2, terrain):
    """Para el MISMO terrain category, qp crece con z."""
    assume(h1 < h2)
    try:
        from windloads.services.ec1 import EC1Input, compute_ec1
    except ImportError:
        pytest.skip("services.ec1 no disponible")
    r1 = compute_ec1(EC1Input(vb=vb, height=h1, width=20, depth=20,
                                 terrain_category=terrain))
    r2 = compute_ec1(EC1Input(vb=vb, height=h2, width=20, depth=20,
                                 terrain_category=terrain))
    assert r2.qp_at_height >= r1.qp_at_height - 1e-9


# -----------------------------------------------------------------------------
# Invariantes ASCE 7
# -----------------------------------------------------------------------------

@given(V=valid_V_mph, height=st.floats(min_value=15, max_value=300),
        exposure=valid_exposure)
@settings(max_examples=30, deadline=2000)
def test_asce7_qz_positive(V, height, exposure):
    try:
        from windloads.services.asce7 import ASCE7Input, compute_asce7
    except ImportError:
        pytest.skip("services.asce7 no disponible")
    res = compute_asce7(ASCE7Input(V=V, height_ft=height,
                                       width_ft=50, depth_ft=80,
                                       exposure=exposure))
    assert res.qz_at_height_psf > 0


@given(V=valid_V_mph, h=valid_height)
@settings(max_examples=20, deadline=2000)
def test_asce7_higher_V_higher_qz(V, h):
    """qz crece monotónicamente con V² (manteniendo todo lo demás)."""
    try:
        from windloads.services.asce7 import ASCE7Input, compute_asce7
    except ImportError:
        pytest.skip("services.asce7 no disponible")
    base = compute_asce7(ASCE7Input(V=V, height_ft=h*3.28, width_ft=50,
                                       depth_ft=80, exposure="C"))
    higher = compute_asce7(ASCE7Input(V=V*1.5, height_ft=h*3.28, width_ft=50,
                                         depth_ft=80, exposure="C"))
    assert higher.qz_at_height_psf > base.qz_at_height_psf


# -----------------------------------------------------------------------------
# Invariantes Components & Cladding
# -----------------------------------------------------------------------------

@given(qh=valid_qh)
@settings(max_examples=20)
def test_cc_zone_3_more_negative_than_zone_1(qh):
    """GCp negativo más severo en zona 3 (esquinas) que zona 1 (interior)."""
    try:
        from windloads.services.components import CCInput, compute_cc
    except ImportError:
        pytest.skip("services.components no disponible")
    z1 = compute_cc(CCInput(zone=1, qh_kPa=qh))
    z3 = compute_cc(CCInput(zone=3, qh_kPa=qh))
    assert z3.GCp_negative <= z1.GCp_negative + 1e-9
    assert z3.p_negative_kPa <= z1.p_negative_kPa + 1e-9


# -----------------------------------------------------------------------------
# Invariantes NSR-10
# -----------------------------------------------------------------------------

@given(h=st.floats(min_value=5, max_value=100))
@settings(max_examples=15, deadline=2000)
def test_nsr10_barranquilla_higher_than_bogota(h):
    """Barranquilla (costa) tiene viento > Bogotá (altiplano) — invariante geográfica."""
    try:
        from windloads.services.nsr10 import NSR10Input, compute_nsr10
    except ImportError:
        pytest.skip("services.nsr10 no disponible")
    bog = compute_nsr10(NSR10Input(city="Bogotá", height_m=h,
                                      width_m=20, depth_m=40))
    bq = compute_nsr10(NSR10Input(city="Barranquilla", height_m=h,
                                     width_m=20, depth_m=40))
    assert bq.V_basic_kmh > bog.V_basic_kmh
    assert bq.qz_kPa > bog.qz_kPa
