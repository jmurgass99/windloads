"""
tests/test_nsr10.py — Unit tests for NSR-10 B.6 wind load module.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.codes.nsr10_b6 import (
    NSR10WindLoad,
    nsr10_basic_wind_speed,
    nsr10_zone_from_coords,
    NSR10_WIND_ZONES,
)


class TestNSR10WindSpeed:

    def test_barranquilla_45(self):
        assert nsr10_basic_wind_speed("Barranquilla") == 45.0

    def test_bogota_27(self):
        assert nsr10_basic_wind_speed("Bogotá") == 27.0

    def test_case_insensitive(self):
        assert nsr10_basic_wind_speed("CALI") == nsr10_basic_wind_speed("cali")

    def test_accent_insensitive(self):
        assert nsr10_basic_wind_speed("bogota") == nsr10_basic_wind_speed("Bogotá")

    def test_unknown_city_returns_default(self):
        assert nsr10_basic_wind_speed("ciudad_inventada") == 27.0

    def test_coastal_city_higher_than_interior(self):
        coastal  = nsr10_basic_wind_speed("barranquilla")
        interior = nsr10_basic_wind_speed("bogota")
        assert coastal > interior


class TestNSR10ZoneAndCoords:

    def test_lookup_by_city_bogota(self):
        # Backward-compatible city call must still work.
        assert nsr10_basic_wind_speed(city="Bogotá") == 27.0

    def test_lookup_by_zone(self):
        assert nsr10_basic_wind_speed(zone=5) == NSR10_WIND_ZONES[5]
        assert nsr10_basic_wind_speed(zone=1) == NSR10_WIND_ZONES[1]

    def test_invalid_zone_raises(self):
        with pytest.raises(ValueError):
            nsr10_basic_wind_speed(zone=9)

    def test_lookup_by_coords_barranquilla_high_zone(self):
        # Barranquilla ≈ (10.96, -74.78) should classify as zone 5 (highest).
        z = nsr10_zone_from_coords(10.96, -74.78)
        assert z == 5
        V = nsr10_basic_wind_speed(lat=10.96, lon=-74.78)
        assert V == NSR10_WIND_ZONES[5]

    def test_lookup_by_coords_leticia_low_zone(self):
        # Leticia ≈ (-4.21, -69.94) — Amazonía, zona baja.
        z = nsr10_zone_from_coords(-4.21, -69.94)
        assert z == 1

    def test_coords_outside_colombia_raises(self):
        with pytest.raises(ValueError):
            nsr10_zone_from_coords(40.0, -3.7)   # Madrid
        with pytest.raises(ValueError):
            nsr10_basic_wind_speed(lat=0.0, lon=0.0)

    def test_no_args_raises(self):
        with pytest.raises(TypeError):
            nsr10_basic_wind_speed()

    def test_coastal_coords_higher_than_interior_coords(self):
        v_coast = nsr10_basic_wind_speed(lat=10.96, lon=-74.78)  # Barranquilla
        v_int   = nsr10_basic_wind_speed(lat=4.71,  lon=-74.07)  # Bogotá
        assert v_coast > v_int


class TestNSR10WindLoad:

    def setup_method(self):
        self.wl = NSR10WindLoad(
            city_or_Vb="barranquilla",
            terrain_cat="B",
            building_height=15.0,
            width=12.0,
            depth=10.0,
            story_heights=[3.0] * 5,
        )

    def test_Vb_design_from_city_name(self):
        assert self.wl.Vb_design == pytest.approx(45.0)

    def test_Vb_design_from_numeric(self):
        wl = NSR10WindLoad(35.0, "C", building_height=10.0)
        assert wl.Vb_design == pytest.approx(35.0)

    def test_importance_factor_increases_Vb_design(self):
        wl1 = NSR10WindLoad("bogota", "B", building_height=10.0, importance_factor=1.0)
        wl2 = NSR10WindLoad("bogota", "B", building_height=10.0, importance_factor=1.15)
        assert wl2.Vb_design > wl1.Vb_design

    def test_qh_positive(self):
        assert self.wl.qh > 0

    def test_story_forces_count(self):
        assert len(self.wl.story_forces()) == 5

    def test_base_shear_positive(self):
        r = self.wl.compute()
        assert r["Vb_kN"] > 0

    def test_coastal_higher_than_interior(self):
        wl_coast = NSR10WindLoad("barranquilla", "B", building_height=12.0,
                                  story_heights=[4.0]*3)
        wl_int   = NSR10WindLoad("bogota",       "B", building_height=12.0,
                                  story_heights=[4.0]*3)
        assert wl_coast.compute()["Vb_kN"] > wl_int.compute()["Vb_kN"]

    def test_open_terrain_higher_than_urban(self):
        wl_A = NSR10WindLoad(30.0, "A", building_height=12.0, story_heights=[4.0]*3)
        wl_D = NSR10WindLoad(30.0, "D", building_height=12.0, story_heights=[4.0]*3)
        assert wl_A.compute()["Vb_kN"] > wl_D.compute()["Vb_kN"]

    def test_compute_required_keys(self):
        r = self.wl.compute()
        for k in ["code", "city", "terrain_category", "Vb_basic_ms",
                  "Vb_design_ms", "Vb_kN", "OTM_kNm", "facade_pressures"]:
            assert k in r, f"Missing key: {k}"

    def test_otm_kNm_positive(self):
        r = self.wl.compute()
        assert r["OTM_kNm"] > 0

    def test_single_story_building(self):
        wl = NSR10WindLoad(27.0, "B", building_height=4.0)
        r = wl.compute()
        assert r["Vb_kN"] > 0
        assert len(r["story_forces"]) == 1
