"""Tests Cp catalog + solar trackers."""
import pytest

from windloads.cp_catalog import CP_CATALOG, list_geometries, lookup_cp
from windloads.solar_trackers import SolarTrackerInput, evaluate_solar_tracker


class TestCp:
    def test_catalog_no_vacio(self):
        assert len(CP_CATALOG) > 5

    def test_lookup_box_asce7(self):
        e = lookup_cp("box_LB1", "ASCE7")
        assert e is not None and e.Cp_windward == 0.80

    def test_list_geometries(self):
        gs = list_geometries()
        assert "flat_roof" in gs and "cylinder" in gs


class TestSolarTracker:
    def test_stow_mode(self):
        r = evaluate_solar_tracker(SolarTrackerInput(tilt_deg=0))
        assert r.critical_mode == "stow_lift_max"
        assert r.moment_kNm_per_m == 0.0

    def test_operating_mode(self):
        r = evaluate_solar_tracker(SolarTrackerInput(tilt_deg=30))
        assert r.critical_mode == "operating_torsion_max"
        assert r.moment_kNm_per_m > 0
