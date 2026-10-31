"""Tests for MRI generator."""
import pytest
from windloads.mri_generator import MRIInput, velocity_for_MRI, MRI_for_target_velocity


def test_factor_increases_with_T_asce():
    r10 = velocity_for_MRI(MRIInput(V_basic_ms=40, T_years=10))
    r700 = velocity_for_MRI(MRIInput(V_basic_ms=40, T_years=700))
    assert r700.factor > r10.factor
    assert r700.V_target_ms > r10.V_target_ms


def test_eurocode_factor_T50_equal_v50():
    # Para T=50, cprob ~ 1
    r = velocity_for_MRI(MRIInput(V_basic_ms=30, T_years=50, code="EU"))
    assert r.factor == pytest.approx(1.0, abs=0.05)


def test_multi_code():
    for code in ("ASCE", "EU", "AS", "NSR", "SG"):
        r = velocity_for_MRI(MRIInput(V_basic_ms=30, T_years=100, code=code))
        assert r.V_target_ms > 0
    with pytest.raises(ValueError):
        velocity_for_MRI(MRIInput(V_basic_ms=30, T_years=100, code="ZZ"))


def test_inverse_MRI():
    r = velocity_for_MRI(MRIInput(V_basic_ms=40, T_years=300, code="ASCE"))
    T = MRI_for_target_velocity(40, r.V_target_ms, code="ASCE")
    assert T == pytest.approx(300, rel=0.10)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        velocity_for_MRI(MRIInput(V_basic_ms=-1, T_years=100))
    with pytest.raises(ValueError):
        velocity_for_MRI(MRIInput(V_basic_ms=30, T_years=0))
