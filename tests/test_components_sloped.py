"""
tests/test_components_sloped.py — C&C for sloped, curved, mansard and
parapet roofs (ASCE 7-22 Figs. 30.3-2B/C/D, 30.7-1, §30.9 and EN 1991-1-4
§7.2.3, §7.2.4, §7.2.7).
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.components import (
    ComponentsAndCladding,
    gable_roof_GCp,
    gable_roof_zones,
    monoslope_roof_GCp,
    domed_roof_GCp,
    mansard_roof_GCp,
    parapet_pressure,
    ec1_gable_cpe,
    ec1_monopitch_cpe,
    ec1_cylindrical_cpe,
)


# -------------------------------------------------------------------------
# ASCE 7-22 — Gable roof Fig. 30.3-2C
# -------------------------------------------------------------------------
class TestGableRoof:
    def test_gable_low_pitch_zones(self):
        # θ ≤ 7°  falls back to low-slope numbering (1/2/3)
        zones = gable_roof_zones(7.0)
        assert zones == ("1", "2", "3")

    def test_gable_steep_zones(self):
        zones = gable_roof_zones(30.0)
        assert set(zones) == {"1", "2e", "2n", "2r", "3"}

    def test_gable_7deg_corner_more_negative_than_interior(self):
        g_int = gable_roof_GCp(15.0, 0.93, "1", "neg")
        g_cor = gable_roof_GCp(15.0, 0.93, "3", "neg")
        assert g_cor < g_int  # corner is more negative (stronger suction)

    def test_gable_30deg_positive_increases_with_slope(self):
        # Steeper pitch develops positive pressure on windward slope
        gp_low = gable_roof_GCp(15.0, 0.93, "1", "pos")
        gp_steep = gable_roof_GCp(35.0, 0.93, "1", "pos")
        assert gp_steep > gp_low

    def test_gable_area_reduction(self):
        # Larger tributary area reduces |GCp|
        small = abs(gable_roof_GCp(20.0, 0.93, "3", "neg"))
        large = abs(gable_roof_GCp(20.0, 46.45, "3", "neg"))
        assert large < small

    def test_gable_invalid_slope_raises(self):
        with pytest.raises(ValueError):
            gable_roof_GCp(60.0, 1.0, "1", "neg")


# -------------------------------------------------------------------------
# ASCE 7-22 — Monoslope Fig. 30.3-2B
# -------------------------------------------------------------------------
class TestMonoslope:
    def test_monoslope_5deg_zones(self):
        g1 = monoslope_roof_GCp(5.0, 0.93, "1", "neg")
        g3 = monoslope_roof_GCp(5.0, 0.93, "3", "neg")
        assert g3 < g1 < 0.0

    def test_monoslope_25deg(self):
        g = monoslope_roof_GCp(25.0, 0.93, "2", "neg")
        assert -3.0 < g < 0.0

    def test_monoslope_out_of_range(self):
        with pytest.raises(ValueError):
            monoslope_roof_GCp(40.0, 1.0, "1", "neg")


# -------------------------------------------------------------------------
# ASCE 7-22 — Domed Fig. 30.7-1
# -------------------------------------------------------------------------
class TestDome:
    def test_dome_fD_0p2_center_suction(self):
        g = domed_roof_GCp(0.2, 1.0, "B", "neg")
        assert g < 0.0

    def test_dome_low_rise_more_suction(self):
        # Lower rise → stronger suction at apex
        g_low = domed_roof_GCp(0.05, 1.0, "B", "neg")
        g_hi = domed_roof_GCp(0.5, 1.0, "B", "neg")
        assert g_low < g_hi  # more negative

    def test_dome_invalid_fD(self):
        with pytest.raises(ValueError):
            domed_roof_GCp(0.0, 1.0, "A", "neg")
        with pytest.raises(ValueError):
            domed_roof_GCp(0.2, 1.0, "Z", "neg")


# -------------------------------------------------------------------------
# Parapet pressures — ASCE 7-22 §30.9
# -------------------------------------------------------------------------
class TestParapet:
    def test_parapet_zero_gives_unit_Kp(self):
        r = parapet_pressure(0.0, 1000.0)
        assert r["K_p"] == pytest.approx(1.0)

    def test_parapet_1p5m(self):
        r = parapet_pressure(1.5, 1000.0)
        # Kp saturates at 1.5
        assert r["K_p"] == pytest.approx(1.5)
        assert abs(r["p_parapet_neg_Pa"]) > 0

    def test_parapet_design_envelope(self):
        r = parapet_pressure(0.8, 1200.0)
        assert r["p_design_Pa"] >= abs(r["p_parapet_neg_Pa"]) - 1e-3
        assert r["p_design_Pa"] >= abs(r["p_parapet_pos_Pa"]) - 1e-3


# -------------------------------------------------------------------------
# Mansard — ASCE 7-22 Fig. 30.3-2D
# -------------------------------------------------------------------------
class TestMansard:
    def test_mansard_30deg_corner_negative(self):
        g = mansard_roof_GCp(30.0, 0.93, "3", "neg")
        assert g < 0.0

    def test_mansard_invalid_slope(self):
        with pytest.raises(ValueError):
            mansard_roof_GCp(80.0, 1.0, "1", "neg")


# -------------------------------------------------------------------------
# EN 1991-1-4 — gable, monopitch, dome
# -------------------------------------------------------------------------
class TestEC1Sloped:
    def test_ec1_gable_15deg_corner(self):
        cpe = ec1_gable_cpe(15.0, "F", 1.0)
        assert cpe < -1.0

    def test_ec1_gable_area_reduction(self):
        small = abs(ec1_gable_cpe(30.0, "F", 1.0))
        large = abs(ec1_gable_cpe(30.0, "F", 10.0))
        assert large <= small

    def test_ec1_monopitch_45deg_positive(self):
        cpe = ec1_monopitch_cpe(45.0, "H", 10.0)
        assert cpe >= 0.0

    def test_ec1_cylindrical_fd_0p2_centre(self):
        c = ec1_cylindrical_cpe(0.2, "B")
        assert c < 0.0


# -------------------------------------------------------------------------
# ComponentsAndCladding integration
# -------------------------------------------------------------------------
class TestCCIntegration:
    def test_gable_report_asce7(self):
        cc = ComponentsAndCladding("ASCE7", qh_or_qp=1000.0, B=15.0, h=8.0)
        rows = cc.gable_report(20.0, [1.0, 10.0])
        assert len(rows) == 2 * 5  # 5 zones × 2 areas
        for r in rows:
            assert r["p_design_Pa"] > 0

    def test_monoslope_report_ec1(self):
        cc = ComponentsAndCladding("EC1", qh_or_qp=1000.0, B=15.0, h=8.0)
        rows = cc.monoslope_report(15.0, [1.0, 10.0])
        assert len(rows) == 2 * 3

    def test_domed_report_asce7(self):
        cc = ComponentsAndCladding("ASCE7", qh_or_qp=1000.0, B=20.0, h=10.0)
        rows = cc.domed_report(0.2, [1.0, 10.0])
        assert len(rows) == 2 * 3

    def test_parapet_adjustment(self):
        cc = ComponentsAndCladding("ASCE7", qh_or_qp=1000.0, B=15.0, h=8.0)
        r = cc.parapet_adjustment(1.0)
        assert r["K_p"] > 1.0
