"""Tests para vortex_shedding."""
import pytest

from windloads.vortex_shedding import (
    VortexInput, evaluate_vortex_shedding,
)


def test_resonancia_dentro_banda():
    # Chimenea D=2m, f1=0.5 Hz, Vb=30 m/s, St=0.18
    # v_crit = 0.5·2/0.18 = 5.56 m/s, Vb=30 → fuera de banda
    r = evaluate_vortex_shedding(VortexInput(
        D_m=2.0, f1_Hz=0.5, Vb_m_s=30.0,
    ))
    assert r.v_critical_m_s > 0
    assert not r.is_in_resonance_band

    # Subir Vb hasta poner en banda
    r2 = evaluate_vortex_shedding(VortexInput(
        D_m=2.0, f1_Hz=0.5, Vb_m_s=6.0,
    ))
    assert r2.is_in_resonance_band


def test_input_invalido():
    with pytest.raises(ValueError):
        evaluate_vortex_shedding(VortexInput(D_m=0, f1_Hz=1, Vb_m_s=10))


def test_scruton_positivo():
    r = evaluate_vortex_shedding(VortexInput(
        D_m=1.0, f1_Hz=1.0, Vb_m_s=20.0,
    ))
    assert r.Sc_scruton > 0

def test_custom_mass_scruton():
    # Verify that passing custom mass m_e_kg_m correctly changes Scruton number
    r_default = evaluate_vortex_shedding(VortexInput(
        D_m=1.0, f1_Hz=1.0, Vb_m_s=20.0,
    ))
    r_custom = evaluate_vortex_shedding(VortexInput(
        D_m=1.0, f1_Hz=1.0, Vb_m_s=20.0, m_e_kg_m=200.0,
    ))
    assert r_default.Sc_scruton == pytest.approx(1.92)
    assert r_custom.Sc_scruton == pytest.approx(3.84)
