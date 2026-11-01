"""
tests/test_vortex_shedding.py -- Tests for vortex shedding and galloping checks.

WL-003: Validates lock-in detection, Scruton number, resonant amplitude,
and galloping onset per EN 1991-1-4 Annex E.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.vortex_shedding import (
    STROUHAL_NUMBERS,
    check_vortex_shedding,
    check_galloping,
    critical_velocity,
    scruton_number,
    VortexResult,
    GallopingResult,
)
from windloads.exceptions import ConfigurationError, GeometryError


# =========================================================================
# Scruton number
# =========================================================================
class TestScrutonNumber:
    """Validate the Scruton number computation."""

    def test_basic_scruton(self):
        """Known case: m=500 kg/m, delta_s=0.02, D=2m, rho=1.25."""
        Sc = scruton_number(500.0, 0.02, 2.0, rho_air=1.25)
        # Sc = 2*500*0.02 / (1.25*4) = 20 / 5 = 4.0
        assert Sc == pytest.approx(4.0)

    def test_heavy_structure_high_scruton(self):
        """Heavier structure -> higher Scruton number."""
        Sc_light = scruton_number(200.0, 0.02, 2.0)
        Sc_heavy = scruton_number(1000.0, 0.02, 2.0)
        assert Sc_heavy > Sc_light

    def test_high_damping_high_scruton(self):
        """More damping -> higher Scruton number."""
        Sc_low = scruton_number(500.0, 0.01, 2.0)
        Sc_high = scruton_number(500.0, 0.05, 2.0)
        assert Sc_high > Sc_low

    def test_zero_damping_gives_zero(self):
        Sc = scruton_number(500.0, 0.0, 2.0)
        assert Sc == pytest.approx(0.0)


# =========================================================================
# Critical velocity
# =========================================================================
class TestCriticalVelocity:
    """Validate V_cr = f_n * D / St."""

    def test_chimney_D2_fn05(self):
        """Chimney: D=2m, fn=0.5Hz, St=0.20 -> V_cr = 0.5*2/0.2 = 5.0 m/s."""
        V_cr = critical_velocity(0.5, 2.0, St=0.20)
        assert V_cr == pytest.approx(5.0)

    def test_rectangular_St_0p12(self):
        """Rectangular section: St=0.12 gives higher V_cr than circular."""
        V_circ = critical_velocity(0.5, 2.0, St=0.20)
        V_rect = critical_velocity(0.5, 2.0, St=0.12)
        assert V_rect > V_circ  # lower St -> higher V_cr

    def test_higher_fn_higher_Vcr(self):
        V1 = critical_velocity(0.5, 2.0)
        V2 = critical_velocity(1.0, 2.0)
        assert V2 > V1


# =========================================================================
# Vortex shedding check -- slender chimney benchmark
# =========================================================================
class TestVortexSheddingChimney:
    """
    Benchmark case: slender circular chimney.
    D = 2 m, fn = 0.5 Hz, St = 0.20
    V_cr = 0.5 * 2 / 0.2 = 5.0 m/s
    """

    def test_Vcr_chimney(self):
        # Default St = 0.18 (EN 1991-1-4 Table E.1, circular, all Re):
        # V_cr = 0.5*2/0.18 = 5.556 m/s (5.0 m/s with the old default 0.20).
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02)
        assert result.V_cr == pytest.approx(0.5 * 2.0 / 0.18, abs=1e-3)

    def test_lock_in_at_Vcr(self):
        """Wind at V_cr should trigger lock-in."""
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02)
        assert result.lock_in is True

    def test_no_lock_in_far_from_Vcr(self):
        """Wind far above V_cr should not be in lock-in range."""
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=25.0,
            m_per_m=500.0, delta_s=0.02)
        assert result.lock_in is False

    def test_no_lock_in_well_below_Vcr(self):
        """Wind far below V_cr should not be in lock-in range."""
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=1.0,
            m_per_m=500.0, delta_s=0.02)
        assert result.lock_in is False

    def test_amplitude_is_finite(self):
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02)
        assert result.y_max_m > 0
        assert math.isfinite(result.y_max_m)

    def test_y_over_D_ratio(self):
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02)
        # both fields are rounded to 6 decimals in VortexResult
        assert result.y_over_D == pytest.approx(result.y_max_m / 2.0, abs=1e-6)


# =========================================================================
# High Scruton number -> reduced amplitude, no practical lock-in concern
# =========================================================================
class TestHighScruton:
    """High Scruton (Sc > 10) structures resist vortex-induced vibrations."""

    def test_high_scruton_small_amplitude(self):
        """Heavy, well-damped structure -> very small resonant amplitude."""
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=5000.0,  # heavy
            delta_s=0.05,     # well-damped
            section="circular")
        assert result.Sc > 10
        # Amplitude should be very small relative to diameter
        assert result.y_over_D < 0.1

    def test_scruton_above_10(self):
        """Verify Sc is indeed above 10 for heavy+damped case."""
        Sc = scruton_number(5000.0, 0.05, 2.0)
        # Sc = 2*5000*0.05 / (1.25*4) = 500/5 = 100
        assert Sc > 10

    def test_heavy_structure_narrower_bandwidth(self):
        """High Scruton -> narrower lock-in bandwidth (0.2 vs 0.3)."""
        result = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=5000.0, delta_s=0.05)
        # Bandwidth should be 0.2 (Sc>5)
        expected_lo = result.V_cr * 0.8
        expected_hi = result.V_cr * 1.2
        assert result.V_range_lo == pytest.approx(expected_lo, abs=0.01)
        assert result.V_range_hi == pytest.approx(expected_hi, abs=0.01)


# =========================================================================
# Rectangular section with different Strouhal
# =========================================================================
class TestRectangularSection:
    def test_rectangular_St(self):
        result = check_vortex_shedding(
            D=1.5, fn=1.0, V=12.5,
            m_per_m=300.0, delta_s=0.03,
            St=0.12, section="rectangular")
        assert result.V_cr == pytest.approx(1.0 * 1.5 / 0.12, rel=1e-3)

    def test_rectangular_higher_clat(self):
        """Rectangular sections have clat=1.0 vs circular clat=0.2,
        so amplitude should be much larger for same Sc."""
        r_circ = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02,
            St=0.20, section="circular")
        r_rect = check_vortex_shedding(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02,
            St=0.20, section="rectangular")
        assert r_rect.y_max_m > r_circ.y_max_m


# =========================================================================
# Galloping checks
# =========================================================================
class TestGalloping:
    """Galloping onset velocity per EN 1991-1-4 Annex E.2."""

    def test_galloping_result_type(self):
        result = check_galloping(
            D=2.0, fn=0.5, V=10.0,
            m_per_m=500.0, delta_s=0.02, aG=2.0)
        assert isinstance(result, GallopingResult)

    def test_rectangular_aG_2(self):
        """
        Rectangular prism aG=2:
        Sc = 2*500*0.02 / (1.25*4) = 4.0
        V_CG = 2*4.0*0.5*2.0 / 2.0 = 4.0 m/s
        """
        result = check_galloping(
            D=2.0, fn=0.5, V=10.0,
            m_per_m=500.0, delta_s=0.02, aG=2.0)
        assert result.V_CG == pytest.approx(4.0)
        assert result.at_risk is True  # V=10 > V_CG=4

    def test_galloping_safe_when_V_below_VCG(self):
        """If V < V_CG, structure is safe from galloping."""
        result = check_galloping(
            D=2.0, fn=0.5, V=2.0,
            m_per_m=500.0, delta_s=0.02, aG=2.0)
        assert result.at_risk is False
        assert result.safety_ratio > 1.0

    def test_high_scruton_raises_VCG(self):
        """Higher Scruton number raises V_CG (harder to trigger galloping)."""
        r_light = check_galloping(
            D=2.0, fn=0.5, V=10.0,
            m_per_m=200.0, delta_s=0.02, aG=2.0)
        r_heavy = check_galloping(
            D=2.0, fn=0.5, V=10.0,
            m_per_m=2000.0, delta_s=0.02, aG=2.0)
        assert r_heavy.V_CG > r_light.V_CG

    def test_safety_ratio_semantics(self):
        """Safety ratio > 1 means safe; < 1 means at risk."""
        result = check_galloping(
            D=2.0, fn=0.5, V=10.0,
            m_per_m=500.0, delta_s=0.02, aG=2.0)
        if result.at_risk:
            assert result.safety_ratio < 1.0
        else:
            assert result.safety_ratio >= 1.0

    def test_VCG_vs_Vmean_known_values(self):
        """
        Test case: D=1.0m, fn=1.0Hz, m=300 kg/m, delta_s=0.03, aG=2.0
        Sc = 2*300*0.03 / (1.25*1.0) = 18/1.25 = 14.4
        V_CG = 2*14.4*1.0*1.0 / 2.0 = 14.4 m/s
        """
        result = check_galloping(
            D=1.0, fn=1.0, V=12.0,
            m_per_m=300.0, delta_s=0.03, aG=2.0)
        assert result.V_CG == pytest.approx(14.4, abs=0.1)
        # EN 1991-1-4 (E.19) requires V_CG > 1.25·v_m = 15.0 m/s: 14.4 does
        # not meet it, so the section IS at risk (before 1.2.0 this test
        # pinned at_risk=False by comparing 14.4 with 12 without the 1.25).
        assert result.at_risk is True
        assert result.safety_ratio == pytest.approx(14.4 / 15.0, abs=1e-3)

    def test_galloping_D_section_high_aG(self):
        """D-section with aG=10: very low V_CG -> likely at risk."""
        result = check_galloping(
            D=2.0, fn=0.5, V=5.0,
            m_per_m=500.0, delta_s=0.02, aG=10.0)
        # V_CG = 2*4.0*0.5*2.0 / 10.0 = 0.8 m/s
        assert result.V_CG == pytest.approx(0.8, abs=0.01)
        assert result.at_risk is True


# =========================================================================
# Input validation
# =========================================================================
class TestValidation:
    def test_negative_D_raises(self):
        with pytest.raises(GeometryError):
            check_vortex_shedding(D=-1.0, fn=0.5, V=5.0,
                                   m_per_m=500.0, delta_s=0.02)

    def test_zero_fn_raises(self):
        with pytest.raises(GeometryError):
            check_vortex_shedding(D=2.0, fn=0.0, V=5.0,
                                   m_per_m=500.0, delta_s=0.02)

    def test_negative_aG_raises(self):
        with pytest.raises(ConfigurationError):
            check_galloping(D=2.0, fn=0.5, V=5.0,
                            m_per_m=500.0, delta_s=0.02, aG=-1.0)

    def test_negative_mass_raises(self):
        with pytest.raises(GeometryError):
            scruton_number(-100.0, 0.02, 2.0)

    def test_negative_damping_raises(self):
        with pytest.raises(ConfigurationError):
            scruton_number(500.0, -0.01, 2.0)
