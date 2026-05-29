"""Tests memoria de presion de viento EC1 (EN 1991-1-4 §4.5).

Presion basica q_b = 0.5*rho*v_b^2 y presion pico q_p = c_e*q_b. Forma cerrada
exacta -> verificacion directa. Complementa la memoria MWFRS (ASCE) con la
contraparte europea. Se salta si handcalcs no esta instalado.
"""
from __future__ import annotations

import pytest

handcalcs = pytest.importorskip("handcalcs")
from windloadjm.memos.ec1_pressure_memo import ec1_peak_pressure_memo


class TestEC1PressureMemo:
    def test_basic_velocity_pressure_closed_form(self):
        # q_b = 0.5*rho*v_b^2 ; rho=1.25, v_b=26 -> 0.5*1.25*676 = 422.5 Pa
        latex, res = ec1_peak_pressure_memo(v_b=26.0, c_e=1.0)
        assert res.q_b_Pa == pytest.approx(0.5 * 1.25 * 26.0 ** 2)
        assert res.q_p_Pa == pytest.approx(res.q_b_Pa)   # c_e = 1.0
        assert "\\" in latex

    def test_exposure_factor_scales_peak_pressure(self):
        _, low = ec1_peak_pressure_memo(v_b=26.0, c_e=1.0)
        _, high = ec1_peak_pressure_memo(v_b=26.0, c_e=2.5)
        assert high.q_p_Pa == pytest.approx(2.5 * low.q_p_Pa)

    def test_pressure_scales_with_velocity_squared(self):
        _, slow = ec1_peak_pressure_memo(v_b=20.0, c_e=1.0)
        _, fast = ec1_peak_pressure_memo(v_b=40.0, c_e=1.0)
        assert fast.q_b_Pa / slow.q_b_Pa == pytest.approx(4.0)   # (40/20)^2

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            ec1_peak_pressure_memo(v_b=0.0, c_e=1.0)
        with pytest.raises(ValueError):
            ec1_peak_pressure_memo(v_b=26.0, c_e=0.0)
