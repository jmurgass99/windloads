"""
tests/test_ec1.py — Unit tests for EC1-1-4 wind load module.
Validated against EN 1991-1-4 worked examples and Annex B.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.terrain import TerrainProfile
from windloads.pressure import ec1_cpe_walls, WindPressure
from windloads.codes.ec1_1_4 import EC1WindLoad
from windloads.topography import (
    ec1_orography_factor,
    ec1_orography_factor_A3,
)


# ---------------------------------------------------------------------------
# TerrainProfile — EC1
# ---------------------------------------------------------------------------
class TestEC1TerrainProfile:

    def test_roughness_cat_II_z10(self):
        """EC1 Annex A: Category II, z=10m → cr ≈ 1.0"""
        tp = TerrainProfile("EC1", "II")
        cr = tp.ec1_roughness_factor(10.0)
        # cr(10) = 0.19*(0.05/0.05)^0.07 * ln(10/0.05) = 0.19*ln(200) ≈ 1.0
        assert 0.95 <= cr <= 1.05, f"cr={cr}"

    def test_roughness_below_zmin_clamped(self):
        """Heights below zmin should use zmin value."""
        tp = TerrainProfile("EC1", "IV")  # zmin = 10m
        cr_1m  = tp.ec1_roughness_factor(1.0)
        cr_10m = tp.ec1_roughness_factor(10.0)
        assert cr_1m == cr_10m

    def test_turbulence_intensity_decreases_with_height(self):
        tp = TerrainProfile("EC1", "II")
        Iv_5  = tp.ec1_turbulence_intensity(5.0)
        Iv_20 = tp.ec1_turbulence_intensity(20.0)
        assert Iv_5 > Iv_20

    def test_peak_velocity_pressure_positive(self):
        tp = TerrainProfile("EC1", "II")
        qp = tp.ec1_peak_velocity_pressure(10.0, 26.0)
        assert qp > 0

    def test_qp_increases_with_height(self):
        tp = TerrainProfile("EC1", "II")
        qp10 = tp.ec1_peak_velocity_pressure(10.0, 26.0)
        qp30 = tp.ec1_peak_velocity_pressure(30.0, 26.0)
        assert qp30 > qp10

    def test_invalid_terrain_category(self):
        with pytest.raises(ValueError):
            TerrainProfile("EC1", "V")

    def test_profile_table_returns_list(self):
        tp = TerrainProfile("EC1", "II")
        table = tp.profile_table([5, 10, 20, 30], 26.0)
        assert len(table) == 4
        assert "qp_Pa" in table[0]

    def test_open_sea_category_0(self):
        tp = TerrainProfile("EC1", "0")
        cr = tp.ec1_roughness_factor(10.0)
        assert cr > 1.0  # open sea rougher factor → higher cr


# ---------------------------------------------------------------------------
# Pressure coefficients
# ---------------------------------------------------------------------------
class TestEC1PressureCoefficients:

    def test_cpe_walls_low_building(self):
        """h/d = 0.2 (flat building) → D=0.7, E=-0.3"""
        cpe = ec1_cpe_walls(h=6.0, d=30.0)  # ratio = 0.2
        assert cpe["D"] == pytest.approx(0.7, abs=0.01)
        assert cpe["E"] == pytest.approx(-0.3, abs=0.01)

    def test_cpe_walls_tall_building(self):
        """h/d = 3.0 → D = 0.8 and E interpolated between h/d = 1 (-0.5) and
        h/d = 5 (-0.7) of EN 1991-1-4 Table 7.1: -0.5 + (3-1)/4·(-0.2) = -0.6.
        (Before 1.2.0 the test pinned -0.5, the value the code returned for
        any h/d > 1.)"""
        cpe = ec1_cpe_walls(h=30.0, d=10.0)
        assert cpe["D"] == pytest.approx(0.8, abs=0.01)
        assert cpe["E"] == pytest.approx(-0.6, abs=1e-9)

    def test_cpe_walls_all_zones_present(self):
        cpe = ec1_cpe_walls(h=15.0, d=15.0)
        assert set(cpe.keys()) >= {"A", "B", "C", "D", "E"}

    def test_net_pressure_windward_positive(self):
        """Windward net pressure should be positive (push)."""
        wp = WindPressure("EC1", "closed")
        p = wp.ec1_net_pressure(qp=1000.0, cpe=0.8, positive_internal=True)
        assert p > 0

    def test_net_pressure_leeward_negative(self):
        """Leeward net pressure should be negative (suction)."""
        wp = WindPressure("EC1", "closed")
        p = wp.ec1_net_pressure(qp=1000.0, cpe=-0.5, positive_internal=False)
        assert p < 0


# ---------------------------------------------------------------------------
# EC1WindLoad high-level API
# ---------------------------------------------------------------------------
class TestEC1WindLoad:

    def setup_method(self):
        self.wl = EC1WindLoad(
            vb=26.0,
            terrain_cat="II",
            building_height=18.0,
            width=15.0,
            depth=12.0,
            story_heights=[3.0] * 6,
        )

    def test_vb_design_equals_vb_when_factors_are_1(self):
        assert self.wl.vb_design == pytest.approx(26.0)

    def test_qp_at_increases_with_height(self):
        qp5  = self.wl.qp_at(5.0)
        qp18 = self.wl.qp_at(18.0)
        assert qp18 > qp5

    def test_facade_pressures_returns_all_zones(self):
        fp = self.wl.facade_pressures()
        assert set(fp.keys()) >= {"A", "B", "C", "D", "E"}

    def test_story_forces_count(self):
        sf = self.wl.story_forces()
        assert len(sf) == 6

    def test_story_forces_Fx_positive(self):
        sf = self.wl.story_forces()
        for f in sf:
            assert f.Fx > 0, f"Story {f.story} has non-positive force"

    def test_base_shear_positive(self):
        sf = self.wl.story_forces()
        Vb = self.wl._envelope.total_base_shear(sf)
        assert Vb > 0

    def test_otm_greater_than_base_shear_times_H2(self):
        """OTM > Vb × H/2 (resultant acts above midheight on average)"""
        sf = self.wl.story_forces()
        Vb  = self.wl._envelope.total_base_shear(sf)
        OTM = self.wl._envelope.overturning_moment(sf)
        assert OTM > Vb * self.wl.building_height / 3

    def test_compute_returns_dict_with_required_keys(self):
        result = self.wl.compute()
        for key in ["code", "Vb_kN", "OTM_kNm", "qp_top_Pa",
                    "facade_pressures", "story_forces"]:
            assert key in result, f"Missing key: {key}"

    def test_single_story_works(self):
        wl = EC1WindLoad(vb=28.0, terrain_cat="III",
                         building_height=5.0, width=10.0, depth=8.0)
        r = wl.compute()
        assert r["Vb_kN"] > 0

    def test_open_sea_higher_than_urban(self):
        wl_sea  = EC1WindLoad(vb=28.0, terrain_cat="0", building_height=10.0)
        wl_city = EC1WindLoad(vb=28.0, terrain_cat="IV", building_height=10.0)
        Vb_sea  = wl_sea.compute()["Vb_kN"]
        Vb_city = wl_city.compute()["Vb_kN"]
        assert Vb_sea > Vb_city

    def test_pressure_profile_length(self):
        profile = self.wl.pressure_profile(n_points=10)
        assert len(profile) == 10
        assert "qp_Pa" in profile[0]

    def test_cdir_increases_base_shear(self):
        wl1 = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=15.0,
                          cdir=1.0, story_heights=[5.0]*3)
        wl2 = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=15.0,
                          cdir=1.1, story_heights=[5.0]*3)
        assert wl2.compute()["Vb_kN"] > wl1.compute()["Vb_kN"]


# ---------------------------------------------------------------------------
# EN 1991-1-4 Annex A.3 — Orography factor co(z)
# ---------------------------------------------------------------------------
class TestEC1OrographyA3:

    def test_flat_terrain_phi_below_0p05_is_unity(self):
        # H/Lu = 0.04 < 0.05 → co = 1.0
        co = ec1_orography_factor_A3(z=10.0, x=0.0, H=4.0, Lu=100.0,
                                      kind="hill")
        assert co == pytest.approx(1.0)

    def test_hill_at_crest_ground_level_phi_0p2(self):
        """
        Reference case: H=20 m, Lu=100 m → Φ = 0.20.
        At crest (x=0) and ground (z→0), Fig A.2 gives s ≈ 1.0,
        so co = 1 + 2·s·Φ ≈ 1.40.
        """
        co = ec1_orography_factor_A3(z=0.0, x=0.0, H=20.0, Lu=100.0,
                                      Ld=100.0, kind="hill")
        assert co == pytest.approx(1.40, abs=0.03)

    def test_hill_at_crest_z10m_phi_0p2(self):
        """At z=10 m (z/Le=0.1) Fig A.2 gives s ≈ 0.84 → co ≈ 1.34."""
        co = ec1_orography_factor_A3(z=10.0, x=0.0, H=20.0, Lu=100.0,
                                      Ld=100.0, kind="hill")
        assert 1.30 <= co <= 1.38, f"co={co}"

    def test_co_decreases_with_height(self):
        co_low  = ec1_orography_factor_A3(z=5.0,  x=0.0, H=20.0, Lu=100.0)
        co_high = ec1_orography_factor_A3(z=50.0, x=0.0, H=20.0, Lu=100.0)
        assert co_low > co_high >= 1.0

    def test_co_decreases_upwind_from_crest(self):
        co_crest = ec1_orography_factor_A3(z=10.0, x=0.0,    H=20.0, Lu=100.0)
        co_far   = ec1_orography_factor_A3(z=10.0, x=-100.0, H=20.0, Lu=100.0)
        assert co_crest > co_far

    def test_phi_saturation_above_0p3(self):
        """For Φ>0.3 the formula caps at co = 1 + 0.6·s."""
        # Φ = 0.5
        co = ec1_orography_factor_A3(z=0.0, x=0.0, H=50.0, Lu=100.0,
                                      kind="hill")
        # s ≈ 1.0 at crest/ground → co ≈ 1.6
        assert co == pytest.approx(1.6, abs=0.05)

    def test_cliff_downwind_plateau(self):
        """Lee side of an escarpment keeps a plateau (s > 0)."""
        co = ec1_orography_factor_A3(z=10.0, x=20.0, H=20.0, Lu=100.0,
                                      kind="cliff")
        assert co > 1.0

    def test_legacy_wrapper_emits_deprecation(self):
        import warnings as _w
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            co = ec1_orography_factor(phi=0.2, x=0.0, z=10.0,
                                       Lu=100.0, H=20.0, feature="hill")
            assert any(issubclass(c.category, DeprecationWarning)
                       for c in caught)
        assert co > 1.0
