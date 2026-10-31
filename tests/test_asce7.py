"""
tests/test_asce7.py — Unit tests for ASCE 7-22 wind load module.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.terrain import TerrainProfile
from windloads.pressure import asce7_Cp_walls, WindPressure
from windloads.codes.asce7_26 import ASCE7WindLoad


class TestASCE7Terrain:

    def test_Kz_exposure_C_z10(self):
        """ASCE 7 Exposure C, z=10m → Kz ≈ 1.0 (Table 26.10-1)"""
        tp = TerrainProfile("ASCE7", "C")
        Kz = tp.asce7_Kz(10.0)
        assert 0.85 <= Kz <= 1.10, f"Kz={Kz}"

    def test_Kz_increases_with_height(self):
        tp = TerrainProfile("ASCE7", "C")
        assert tp.asce7_Kz(30.0) > tp.asce7_Kz(10.0)

    def test_Kz_exposure_D_greater_than_B_same_height(self):
        """Open terrain (D) → higher Kz than suburban (B)"""
        tp_D = TerrainProfile("ASCE7", "D")
        tp_B = TerrainProfile("ASCE7", "B")
        assert tp_D.asce7_Kz(10.0) > tp_B.asce7_Kz(10.0)

    def test_velocity_pressure_positive(self):
        tp = TerrainProfile("ASCE7", "C")
        qz = tp.asce7_velocity_pressure(10.0, 40.0)
        assert qz > 0

    def test_invalid_exposure(self):
        with pytest.raises(ValueError):
            TerrainProfile("ASCE7", "E")


class TestASCE7PressureCoefficients:

    def test_Cp_walls_square_building(self):
        """L/B = 1.0 → leeward Cp = -0.5"""
        Cp = asce7_Cp_walls(L=15.0, B=15.0, h=10.0)
        assert Cp["windward"] == pytest.approx(0.8)
        assert Cp["leeward"] == pytest.approx(-0.5)
        assert Cp["side"] == pytest.approx(-0.7)

    def test_Cp_walls_long_building(self):
        """L/B > 2 → leeward Cp = -0.2"""
        Cp = asce7_Cp_walls(L=50.0, B=10.0, h=10.0)
        assert Cp["leeward"] == pytest.approx(-0.2)

    def test_wall_pressures_windward_positive(self):
        """Windward net pressure should push into structure."""
        wp = WindPressure("ASCE7", "enclosed")
        results = wp.asce7_wall_pressures(
            qz=800.0, qh=800.0, L=15.0, B=15.0, h=10.0
        )
        assert results["windward"]["p_net_pos_kPa"] > 0

    def test_wall_pressures_leeward_negative(self):
        """Leeward net pressure is suction."""
        wp = WindPressure("ASCE7", "enclosed")
        results = wp.asce7_wall_pressures(
            qz=800.0, qh=800.0, L=15.0, B=15.0, h=10.0
        )
        assert results["leeward"]["p_net_neg_kPa"] < 0


class TestASCE7WindLoad:

    def setup_method(self):
        self.wl = ASCE7WindLoad(
            V=44.7,           # 100 mph ≈ 44.7 m/s
            exposure="C",
            building_height=18.0,
            width=15.0,
            depth=12.0,
            story_heights=[3.0] * 6,
        )

    def test_qh_positive(self):
        assert self.wl.qh > 0

    def test_story_forces_count(self):
        assert len(self.wl.story_forces()) == 6

    def test_base_shear_positive(self):
        r = self.wl.compute()
        assert r["Vb_kN"] > 0

    def test_exposure_D_greater_than_B(self):
        wl_D = ASCE7WindLoad(V=40.0, exposure="D", building_height=15.0,
                              story_heights=[5.0]*3)
        wl_B = ASCE7WindLoad(V=40.0, exposure="B", building_height=15.0,
                              story_heights=[5.0]*3)
        assert wl_D.compute()["Vb_kN"] > wl_B.compute()["Vb_kN"]

    def test_higher_V_gives_higher_Vb(self):
        wl1 = ASCE7WindLoad(V=30.0, exposure="C", building_height=12.0,
                             story_heights=[4.0]*3)
        wl2 = ASCE7WindLoad(V=50.0, exposure="C", building_height=12.0,
                             story_heights=[4.0]*3)
        assert wl2.compute()["Vb_kN"] > wl1.compute()["Vb_kN"]

    def test_compute_required_keys(self):
        r = self.wl.compute()
        for k in ["code", "Vb_kN", "OTM_kNm", "qh_Pa",
                  "facade_pressures", "story_forces", "Kd", "G"]:
            assert k in r

    def test_partially_enclosed_higher_than_enclosed(self):
        """Partially enclosed → higher GCpi → higher net pressures"""
        wl_enc  = ASCE7WindLoad(V=40.0, exposure="C", building_height=12.0,
                                 enclosure="enclosed", story_heights=[4.0]*3)
        wl_part = ASCE7WindLoad(V=40.0, exposure="C", building_height=12.0,
                                 enclosure="partially_enclosed", story_heights=[4.0]*3)
        # Partially enclosed should have higher total windward force
        Vb_enc  = wl_enc.compute()["Vb_kN"]
        Vb_part = wl_part.compute()["Vb_kN"]
        assert abs(Vb_part) >= abs(Vb_enc)
