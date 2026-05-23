"""
Tests EN 1991-1-4 Anexo F — fenómenos aeroelásticos.
"""
import math

import pytest

from windloadjm.aeroelastic import (
    divergence_critical_velocity,
    flutter_2dof,
    galloping_critical_velocity,
    lock_in_range,
    wake_buffeting,
)


# ----------------------------------------------------------------------
# Galloping
# ----------------------------------------------------------------------
def test_galloping_circular_cylinder_stable_returns_inf():
    """Cilindro circular: aG = +2 (estable) ⇒ no hay galloping."""
    Vcr = galloping_critical_velocity(
        m=10.0, fn=1.5, b=0.5, rho_air=1.25, c_a_prime=2.0, sc=10.0
    )
    assert math.isinf(Vcr)


def test_galloping_d_section_unstable_finite_vcr():
    """Sección rectangular tipo D: aG < 0 (inestable) ⇒ Vcr finita."""
    # c_a_prime = -3 ⇒ aG = -3 < 0 ⇒ inestable → Vcr = 2·Sc·fn·b/|aG|
    Vcr = galloping_critical_velocity(
        m=10.0, fn=1.5, b=0.5, rho_air=1.25, c_a_prime=-3.0, sc=10.0
    )
    # Vcr = 2·Sc·fn·b/|aG| = 2·10·1.5·0.5/3 = 5.0
    assert math.isfinite(Vcr)
    assert Vcr == pytest.approx(5.0, rel=1e-6)


def test_galloping_null_mass_raises():
    with pytest.raises(ValueError):
        galloping_critical_velocity(
            m=0.0, fn=1.0, b=0.3, rho_air=1.25, c_a_prime=-3.0
        )


def test_galloping_scruton_computed_from_delta():
    """Si no se pasa Sc, se calcula con δ. Verifica fórmula."""
    Vcr = galloping_critical_velocity(
        m=20.0, fn=2.0, b=0.4, rho_air=1.25,
        c_a_prime=-3.0, sc=None, delta=0.1,
    )
    # Sc = 2·20·0.1/(1.25·0.16) = 4/0.2 = 20
    # Vcr = 2·20·2·0.4 / 3 = 32/3 ≈ 10.667
    assert Vcr == pytest.approx(32.0 / 3.0, rel=1e-6)


# ----------------------------------------------------------------------
# Divergencia torsional
# ----------------------------------------------------------------------
def test_divergence_plate_tabulated_case():
    """
    Caso tabulado: placa-puente con EI=1e8, L=50, B=10, dCM/dα=π, ρ=1.25.
      K_α = EI/L = 2e6
      V_div = sqrt(2·2e6 / (1.25·100·π))
            = sqrt(4e6 / 392.7)
            ≈ 100.9 m/s
    """
    V_div = divergence_critical_velocity(
        EI=1e8, L=50.0, c_M_alpha=math.pi, rho_air=1.25, B=10.0
    )
    expected = math.sqrt(4e6 / (1.25 * 100.0 * math.pi))
    assert V_div == pytest.approx(expected, rel=1e-6)
    assert 90.0 < V_div < 110.0


def test_divergence_invalid_cma_raises():
    with pytest.raises(ValueError):
        divergence_critical_velocity(
            EI=1e8, L=50.0, c_M_alpha=-1.0, rho_air=1.25, B=10.0
        )


# ----------------------------------------------------------------------
# Flutter 2-DOF (Theodorsen — placa plana)
# ----------------------------------------------------------------------
def test_flutter_2dof_flat_plate_benchmark():
    """
    Benchmark Theodorsen placa plana (caso académico):
      m=10, I_α=2, S_α=0, k_h=1000, k_α=4000, b=0.5, ρ=1.25.
    Se espera ω_f real y V_f finita > 0.
    """
    V_f, omega_f = flutter_2dof(
        m=10.0, I_alpha=2.0, Salpha=0.0,
        k_h=1000.0, k_alpha=4000.0,
        U_inf=0.0, b=0.5, rho=1.25,
    )
    assert math.isfinite(V_f)
    assert V_f > 0.0
    assert omega_f.real > 0.0


def test_flutter_2dof_zero_mass_raises():
    with pytest.raises(ValueError):
        flutter_2dof(
            m=0.0, I_alpha=1.0, Salpha=0.0, k_h=1.0, k_alpha=1.0,
            U_inf=10.0, b=0.5, rho=1.25,
        )


# ----------------------------------------------------------------------
# Lock-in vortex shedding
# ----------------------------------------------------------------------
def test_lock_in_range_circular_cylinder_St_018():
    """
    St=0.18, fn=2 Hz, b=0.3 m ⇒ V_crit=fn·b/St=2·0.3/0.18≈3.33 m/s
    Rango ±20% ⇒ [2.667, 4.0]
    """
    V_lo, V_hi, in_band = lock_in_range(
        St=0.18, fn=2.0, b=0.3, U_mean=3.5
    )
    V_crit = 2.0 * 0.3 / 0.18
    assert V_lo == pytest.approx(V_crit * 0.8, rel=1e-6)
    assert V_hi == pytest.approx(V_crit * 1.2, rel=1e-6)
    assert in_band is True


def test_lock_in_outside_range():
    _, _, in_band = lock_in_range(St=0.18, fn=2.0, b=0.3, U_mean=10.0)
    assert in_band is False


# ----------------------------------------------------------------------
# Wake buffeting
# ----------------------------------------------------------------------
def test_wake_buffeting_close_tandem_critical():
    res = wake_buffeting(distance=1.0, b=1.0, configuration="tandem")
    assert res.is_critical is True
    assert res.interference_factor > 1.0


def test_wake_buffeting_far_tandem_isolated():
    res = wake_buffeting(distance=30.0, b=1.0, configuration="tandem")
    assert res.is_critical is False
    assert res.interference_factor == pytest.approx(1.0, rel=1e-6)


def test_wake_buffeting_invalid_config_raises():
    with pytest.raises(ValueError):
        wake_buffeting(distance=5.0, b=1.0, configuration="weird")
