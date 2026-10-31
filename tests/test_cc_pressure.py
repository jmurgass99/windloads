"""
tests/test_cc_pressure.py -- Tests for C&C pressure curves (ASCE 7-22 Ch. 30).

WL-002: Validates GCp curves, zone behaviour, area effects, and net pressures
for Components & Cladding per ASCE 7-22 Tables 30.3-1 and 30.3-2A.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.cc_pressure import (
    corner_distance_a,
    get_GCp,
    get_cc_pressure,
    get_cc_pressure_all_zones,
    pressure_vs_area_curve,
    _A_LO_M2,
    _A_HI_M2,
    _MIN_DESIGN_PRESSURE_PA,
)
from windloads.exceptions import ConfigurationError, GeometryError


# =========================================================================
# GCp interpolation tests
# =========================================================================
class TestGCpInterpolation:
    """Validate GCp log-interpolation against ASCE 7-22 Fig. 30.3-1/2A."""

    def test_wall_zone4_at_A_lo(self):
        """At 10 ft^2, wall zone 4 neg should be -1.10."""
        g = get_GCp("4", _A_LO_M2, "wall", "neg")
        assert g == pytest.approx(-1.10, abs=0.01)

    def test_wall_zone4_at_A_hi(self):
        """At 500 ft^2, wall zone 4 neg should be -0.80."""
        g = get_GCp("4", _A_HI_M2, "wall", "neg")
        assert g == pytest.approx(-0.80, abs=0.01)

    def test_wall_zone5_at_A_lo(self):
        """Zone 5 (corner) has stronger suction than zone 4 at small area."""
        g4 = get_GCp("4", _A_LO_M2, "wall", "neg")
        g5 = get_GCp("5", _A_LO_M2, "wall", "neg")
        assert g5 < g4   # -1.40 < -1.10

    def test_roof_zone3_at_A_lo(self):
        """Roof corner (zone 3) at 10 ft^2: GCp_neg = -3.20."""
        g = get_GCp("3", _A_LO_M2, "flat", "neg")
        assert g == pytest.approx(-3.20, abs=0.01)

    def test_roof_zone1_at_A_hi(self):
        """Roof interior (zone 1) at 500 ft^2: GCp_neg = -1.10."""
        g = get_GCp("1", _A_HI_M2, "flat", "neg")
        assert g == pytest.approx(-1.10, abs=0.01)

    def test_interpolation_midpoint(self):
        """At midpoint of log-area range, GCp should be between lo and hi."""
        A_mid = math.sqrt(_A_LO_M2 * _A_HI_M2)  # geometric mean
        g = get_GCp("4", A_mid, "wall", "neg")
        assert -1.10 < g < -0.80

    def test_positive_GCp_wall(self):
        """Positive GCp for walls at A_lo = +1.00."""
        g = get_GCp("4", _A_LO_M2, "wall", "pos")
        assert g == pytest.approx(1.00, abs=0.01)

    def test_below_A_lo_saturates(self):
        """Areas below 10 ft^2 should clamp to the 10ft^2 value."""
        g_tiny = get_GCp("4", 0.1, "wall", "neg")
        g_lo = get_GCp("4", _A_LO_M2, "wall", "neg")
        assert g_tiny == pytest.approx(g_lo)

    def test_above_A_hi_saturates(self):
        """Areas above 500 ft^2 should clamp to the 500ft^2 value."""
        g_huge = get_GCp("4", 100.0, "wall", "neg")
        g_hi = get_GCp("4", _A_HI_M2, "wall", "neg")
        assert g_huge == pytest.approx(g_hi)


# =========================================================================
# Zone comparison: interior vs corner
# =========================================================================
class TestZoneComparison:
    """Corner zones must produce more severe pressures than interior zones."""

    def test_wall_corner_more_severe_neg(self):
        """Wall zone 5 (corner) should have stronger suction than zone 4."""
        for A in [_A_LO_M2, 5.0, _A_HI_M2]:
            g4 = get_GCp("4", A, "wall", "neg")
            g5 = get_GCp("5", A, "wall", "neg")
            assert g5 <= g4, f"Zone 5 should be <= zone 4 at A={A}"

    def test_roof_corner_more_severe_than_interior(self):
        """Roof zone 3 (corner) has stronger suction than zone 1 (interior)."""
        for A in [_A_LO_M2, 5.0, _A_HI_M2]:
            g1 = get_GCp("1", A, "flat", "neg")
            g3 = get_GCp("3", A, "flat", "neg")
            assert g3 < g1

    def test_roof_edge_between_interior_and_corner(self):
        """Roof zone 2 (edge) suction is between zone 1 and zone 3."""
        g1 = get_GCp("1", 2.0, "flat", "neg")
        g2 = get_GCp("2", 2.0, "flat", "neg")
        g3 = get_GCp("3", 2.0, "flat", "neg")
        assert g3 < g2 < g1


# =========================================================================
# Area effects: small vs large
# =========================================================================
class TestAreaEffects:
    """Larger effective wind area should reduce absolute GCp magnitude."""

    def test_wall_area_reduction(self):
        """Larger A -> |GCp| decreases for walls."""
        small = abs(get_GCp("5", _A_LO_M2, "wall", "neg"))
        large = abs(get_GCp("5", _A_HI_M2, "wall", "neg"))
        assert large < small

    def test_roof_area_reduction(self):
        """Larger A -> |GCp| decreases for roofs."""
        small = abs(get_GCp("3", _A_LO_M2, "flat", "neg"))
        large = abs(get_GCp("3", _A_HI_M2, "flat", "neg"))
        assert large < small

    def test_positive_GCp_area_reduction(self):
        """Positive GCp also decreases with area."""
        small = get_GCp("4", _A_LO_M2, "wall", "pos")
        large = get_GCp("4", _A_HI_M2, "wall", "pos")
        assert large < small  # 0.70 < 1.00


# =========================================================================
# Full C&C pressure via get_cc_pressure
# =========================================================================
class TestGetCCPressure:
    """Test the integrated C&C pressure calculation."""

    # Standard test case: V=44.7 m/s (100 mph), Exp. C, h=12m
    _V = 44.7
    _EXP = "C"
    _H = 12.0

    def test_returns_tuple(self):
        result = get_cc_pressure("4", "wall", 5.0, self._H, self._EXP, self._V)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_positive_pressure_is_positive(self):
        p_pos, p_neg = get_cc_pressure(
            "4", "wall", 5.0, self._H, self._EXP, self._V)
        assert p_pos > 0

    def test_negative_pressure_is_negative(self):
        p_pos, p_neg = get_cc_pressure(
            "4", "wall", 5.0, self._H, self._EXP, self._V)
        assert p_neg < 0

    def test_corner_more_severe_than_interior(self):
        """Corner zone 5 should yield larger absolute suction than zone 4."""
        _, p_neg_4 = get_cc_pressure(
            "4", "wall", 2.0, self._H, self._EXP, self._V)
        _, p_neg_5 = get_cc_pressure(
            "5", "wall", 2.0, self._H, self._EXP, self._V)
        assert abs(p_neg_5) > abs(p_neg_4)

    def test_small_area_more_severe(self):
        """Smaller tributary area gives larger pressures."""
        _, p_neg_small = get_cc_pressure(
            "5", "wall", 1.0, self._H, self._EXP, self._V)
        _, p_neg_large = get_cc_pressure(
            "5", "wall", 40.0, self._H, self._EXP, self._V)
        assert abs(p_neg_small) > abs(p_neg_large)

    def test_exposure_D_higher_than_B(self):
        """Open terrain (D) produces higher pressures than suburban (B)."""
        _, p_neg_B = get_cc_pressure(
            "4", "wall", 5.0, self._H, "B", self._V)
        _, p_neg_D = get_cc_pressure(
            "4", "wall", 5.0, self._H, "D", self._V)
        assert abs(p_neg_D) > abs(p_neg_B)

    def test_partially_enclosed_more_severe(self):
        """Partially enclosed building has higher GCpi -> more severe."""
        _, p_neg_enc = get_cc_pressure(
            "4", "wall", 5.0, self._H, self._EXP, self._V, enclosure="enclosed")
        _, p_neg_pe = get_cc_pressure(
            "4", "wall", 5.0, self._H, self._EXP, self._V,
            enclosure="partially_enclosed")
        assert abs(p_neg_pe) > abs(p_neg_enc)

    def test_minimum_pressure_enforced(self):
        """Very low wind speed should still give at least minimum pressure."""
        p_pos, p_neg = get_cc_pressure(
            "1", "flat", 30.0, 5.0, "B", 10.0)  # very low V
        # At least one of them should be at minimum if the raw value is small
        assert p_pos >= _MIN_DESIGN_PRESSURE_PA or abs(p_neg) >= _MIN_DESIGN_PRESSURE_PA

    def test_roof_pressures(self):
        """Flat roof zones should return valid pressure tuples."""
        for zone in ["1", "2", "3"]:
            p_pos, p_neg = get_cc_pressure(
                zone, "flat", 5.0, self._H, self._EXP, self._V)
            assert p_pos > 0
            assert p_neg < 0


# =========================================================================
# All-zones helper
# =========================================================================
class TestAllZones:
    def test_wall_all_zones(self):
        result = get_cc_pressure_all_zones(
            "wall", 5.0, 12.0, "C", 44.7)
        assert "4" in result
        assert "5" in result

    def test_roof_all_zones(self):
        result = get_cc_pressure_all_zones(
            "flat", 5.0, 12.0, "C", 44.7)
        assert set(result.keys()) == {"1", "2", "3"}


# =========================================================================
# Pressure-vs-area curve generation
# =========================================================================
class TestPressureCurve:
    def test_curve_length(self):
        curve = pressure_vs_area_curve(
            "4", "wall", 12.0, "C", 44.7, n_points=10)
        assert len(curve) == 10

    def test_curve_has_required_keys(self):
        curve = pressure_vs_area_curve("4", "wall", 12.0, "C", 44.7)
        for pt in curve:
            assert "A_eff_m2" in pt
            assert "GCp_pos" in pt
            assert "GCp_neg" in pt
            assert "p_pos_Pa" in pt
            assert "p_neg_Pa" in pt


# =========================================================================
# Corner distance 'a'
# =========================================================================
class TestCornerDistance:
    def test_basic_computation(self):
        a = corner_distance_a(20.0, 10.0)
        # a = min(0.10*20, 0.4*10) = min(2, 4) = 2
        # a_min = max(0.04*20, 0.9) = max(0.8, 0.9) = 0.9
        # a = max(2, 0.9) = 2
        assert a == pytest.approx(2.0)

    def test_minimum_clamp(self):
        """For very small buildings, a should not go below a_min."""
        a = corner_distance_a(5.0, 2.0)
        # a = min(0.5, 0.8) = 0.5
        # a_min = max(0.2, 0.9) = 0.9
        # a = max(0.5, 0.9) = 0.9
        assert a == pytest.approx(0.9)


# =========================================================================
# Input validation
# =========================================================================
class TestValidation:
    def test_invalid_zone(self):
        with pytest.raises(ConfigurationError):
            get_GCp("X", 5.0, "wall", "neg")

    def test_invalid_roof_type(self):
        with pytest.raises(ConfigurationError):
            get_GCp("1", 5.0, "hip_roof", "neg")

    def test_zero_area(self):
        with pytest.raises(GeometryError):
            get_GCp("4", 0.0, "wall", "neg")

    def test_negative_height(self):
        with pytest.raises(GeometryError):
            get_cc_pressure("4", "wall", 5.0, -1.0, "C", 40.0)

    def test_invalid_exposure(self):
        with pytest.raises(ConfigurationError):
            get_cc_pressure("4", "wall", 5.0, 10.0, "E", 40.0)

    def test_invalid_enclosure(self):
        with pytest.raises(ConfigurationError):
            get_cc_pressure("4", "wall", 5.0, 10.0, "C", 40.0,
                            enclosure="invalid")
