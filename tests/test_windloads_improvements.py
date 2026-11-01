from __future__ import annotations

import pytest

from windloads.codes.ec1_1_4 import EC1WindLoad, ec1_structural_factor_cscd
from windloads.codes.nsr10_b6 import NSR10WindLoad, nsr10_basic_wind_speed
from windloads.pressure import asce7_Cp_roof_flat
from windloads.vb_atlas import vb_for
from windloads.vb_map import lookup_Vb


def test_ec1_structural_factor_cscd_and_orography():
    res_cscd = ec1_structural_factor_cscd(
        h=40.0,
        b=20.0,
        d=15.0,
        vm_zs=31.0,
        Iv_zs=0.15,
        z0=0.05,
        n1_x=1.1,
        delta_s=0.05,
    )
    assert res_cscd["B2"] > 0.0
    assert res_cscd["R2"] >= 0.0
    assert res_cscd["cs_cd"] > 0.85

    ec1_default = EC1WindLoad(
        vb=27.0,
        terrain_cat="II",
        building_height=40.0,
        width=20.0,
        depth=15.0,
    )
    ec1_annex_b = EC1WindLoad(
        vb=27.0,
        terrain_cat="II",
        building_height=40.0,
        width=20.0,
        depth=15.0,
        compute_cscd_annex_b=True,
        n1_x_Hz=1.1,
        delta_s=0.05,
        orography_params={"kind": "cliff", "H": 10.0, "Lu": 40.0, "x": 5.0},
    )
    out_def = ec1_default.compute()
    out_ann = ec1_annex_b.compute()
    assert out_def["Cs_Cd"] == pytest.approx(1.0)
    assert out_ann["Cs_Cd_justified"] is True
    assert out_ann["Cs_Cd_status"] == "computed_en1991_1_4_annex_b"
    assert out_ann["co_top"] > 1.0
    assert ec1_annex_b.qp_at(40.0) > ec1_default.qp_at(40.0)


def test_nsr10_regional_map_b641_and_exposure_convention():
    # Default backward-compatible table values
    assert nsr10_basic_wind_speed("Bogotá") == pytest.approx(27.0)
    assert nsr10_basic_wind_speed("Barranquilla") == pytest.approx(45.0)
    assert nsr10_basic_wind_speed(zone=6) == pytest.approx(50.0)

    # NSR-10 Fig. B.6.4-1 regional threat zone alignment across modules
    v_bog = nsr10_basic_wind_speed("Bogotá", use_regional_map_b641=True)
    v_baq = nsr10_basic_wind_speed("Barranquilla", use_regional_map_b641=True)
    v_san = nsr10_basic_wind_speed("San Andrés", use_regional_map_b641=True)
    assert v_bog == pytest.approx(lookup_Vb("Bogotá").Vb_m_s) == pytest.approx(vb_for("Bogotá", "CO"))
    assert v_baq == pytest.approx(lookup_Vb("Barranquilla").Vb_m_s) == pytest.approx(vb_for("Barranquilla", "CO"))
    assert v_san == pytest.approx(50.0)

    # Exposure convention toggle (ASCE 7 B/C/D vs legacy)
    w_legacy = NSR10WindLoad(city_or_Vb="Bogotá", terrain_cat="B", building_height=15.0)
    w_asce = NSR10WindLoad(
        city_or_Vb="Bogotá",
        terrain_cat="B",
        building_height=15.0,
        use_asce7_exposure_convention=True,
    )
    assert w_asce.qh < w_legacy.qh


def test_asce7_cp_roof_flat_distance_zones_and_interpolation():
    cp_low = asce7_Cp_roof_flat(h=8.0, L=20.0)  # h/L = 0.4
    assert cp_low["zone_0_to_h_half"] == pytest.approx(-0.9)
    assert cp_low["zone_h_half_to_h"] == pytest.approx(-0.9)
    assert cp_low["zone_h_to_2h"] == pytest.approx(-0.5)
    assert cp_low["zone_gt_2h"] == pytest.approx(-0.3)

    cp_high = asce7_Cp_roof_flat(h=24.0, L=20.0)  # h/L = 1.2
    assert cp_high["zone_0_to_h_half"] == pytest.approx(-1.3)
    assert cp_high["zone_gt_2h"] == pytest.approx(-0.7)

    cp_mid = asce7_Cp_roof_flat(h=15.0, L=20.0)  # h/L = 0.75
    assert cp_mid["zone_0_to_h_half"] == pytest.approx(-1.1)
    assert cp_mid["zone_gt_2h"] == pytest.approx(-0.5)
