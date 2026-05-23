"""Tests MWFRS ASCE 7-22 memo."""
from __future__ import annotations
import pytest

handcalcs = pytest.importorskip("handcalcs")
from windloadjm.memos import mwfrs_directional_memo


def test_mwfrs_typical_building():
    """Edificio tipico 30 m altura, exposicion C, V=50 m/s."""
    latex, res = mwfrs_directional_memo(
        V_ms=50.0, z=30.0, exposure="C", K_zt=1.0, K_d=0.85,
        L_over_B=1.5, enclosed=True,
    )
    assert res.q_z_kN_m2 > 0
    assert res.K_z > 1.0  # z=30m > 15ft datum, exp C, K_z > 1
    assert res.p_design_kN_m2 > 0
    assert "\\" in latex


def test_mwfrs_higher_exposure_higher_Kz():
    _, b = mwfrs_directional_memo(V_ms=50, z=30, exposure="B")
    _, c = mwfrs_directional_memo(V_ms=50, z=30, exposure="C")
    _, d = mwfrs_directional_memo(V_ms=50, z=30, exposure="D")
    assert b.K_z < c.K_z < d.K_z


def test_mwfrs_higher_velocity_higher_pressure():
    _, slow = mwfrs_directional_memo(V_ms=30, z=20, exposure="C")
    _, fast = mwfrs_directional_memo(V_ms=60, z=20, exposure="C")
    # q_z escala con V^2 -> fast/slow ~ 4
    ratio = fast.q_z_kN_m2 / slow.q_z_kN_m2
    assert 3.5 < ratio < 4.5


def test_mwfrs_partially_enclosed_higher_pressure():
    _, enc = mwfrs_directional_memo(V_ms=50, z=20, exposure="C", enclosed=True)
    _, part = mwfrs_directional_memo(V_ms=50, z=20, exposure="C", enclosed=False)
    assert part.p_design_kN_m2 > enc.p_design_kN_m2


def test_mwfrs_invalid_inputs():
    with pytest.raises(ValueError):
        mwfrs_directional_memo(V_ms=-10, z=20, exposure="C")
    with pytest.raises(ValueError):
        mwfrs_directional_memo(V_ms=50, z=-5, exposure="C")
    with pytest.raises(ValueError):
        mwfrs_directional_memo(V_ms=50, z=20, exposure="X")
    with pytest.raises(ValueError):
        mwfrs_directional_memo(V_ms=50, z=20, exposure="C", L_over_B=0)
