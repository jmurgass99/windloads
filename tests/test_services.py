"""Tests del service layer headless."""
from __future__ import annotations
import pytest

from windloadjm.services.ec1 import EC1Input, compute_ec1, EC1Result
from windloadjm.services.asce7 import ASCE7Input, compute_asce7, ASCE7Result
from windloadjm.services.nsr10 import NSR10Input, compute_nsr10, NSR10Result
from windloadjm.services.components import CCInput, compute_cc, CCResult
from windloadjm.services.export import ExportInput, export_to, ExportResult


def test_ec1_basic():
    inp = EC1Input(vb=25.0, height=30.0, width=20.0, depth=40.0,
                   terrain_category=2)
    res = compute_ec1(inp)
    assert isinstance(res, EC1Result)
    assert res.qp_at_height > 0
    assert res.pressure_windward > 0


def test_ec1_higher_building_higher_qp():
    base = compute_ec1(EC1Input(vb=25, height=10, width=20, depth=20))
    tall = compute_ec1(EC1Input(vb=25, height=50, width=20, depth=20))
    assert tall.qp_at_height > base.qp_at_height


def test_asce7_basic():
    inp = ASCE7Input(V=115, height_ft=100, width_ft=60, depth_ft=120,
                     exposure="C")
    res = compute_asce7(inp)
    assert res.qz_at_height_psf > 0
    assert res.p_windward_psf > 0


def test_asce7_exposure_d_higher_than_b():
    base = compute_asce7(ASCE7Input(V=120, height_ft=50, width_ft=40,
                                    depth_ft=80, exposure="B"))
    coastal = compute_asce7(ASCE7Input(V=120, height_ft=50, width_ft=40,
                                       depth_ft=80, exposure="D"))
    assert coastal.qz_at_height_psf >= base.qz_at_height_psf


def test_nsr10_bogota():
    res = compute_nsr10(NSR10Input(city="Bogotá", height_m=30,
                                   width_m=20, depth_m=40))
    assert res.V_basic_kmh > 0
    assert res.p_net_kPa > 0


def test_nsr10_barranquilla_higher_than_bogota():
    b = compute_nsr10(NSR10Input(city="Bogotá", height_m=30, width_m=20,
                                 depth_m=40))
    bq = compute_nsr10(NSR10Input(city="Barranquilla", height_m=30,
                                  width_m=20, depth_m=40))
    assert bq.V_basic_kmh > b.V_basic_kmh
    assert bq.p_net_kPa > b.p_net_kPa


def test_cc_zone_3_more_negative():
    z1 = compute_cc(CCInput(zone=1, qh_kPa=1.0))
    z3 = compute_cc(CCInput(zone=3, qh_kPa=1.0))
    assert z3.GCp_negative < z1.GCp_negative
    assert z3.p_negative_kPa < z1.p_negative_kPa


def test_export_json_valid():
    res = export_to(ExportInput(target="json", height_m=30, width_m=20,
                                n_stories=5))
    import json
    parsed = json.loads(res.content)
    assert "stories" in parsed
    assert len(parsed["stories"]) == 5


def test_export_csv_has_header():
    res = export_to(ExportInput(target="csv", height_m=30, width_m=20,
                                n_stories=3))
    assert "story,z_m,pressure_kPa" in res.content


def test_export_unknown_target_raises():
    with pytest.raises(ValueError):
        export_to(ExportInput(target="xml", height_m=30, width_m=20))
