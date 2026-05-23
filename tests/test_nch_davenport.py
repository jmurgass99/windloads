"""Tests NCh 432 + Davenport."""
import pytest

from windloadjm.nch432 import NCh432Input, evaluate_nch432
from windloadjm.davenport import DavenportInput, gust_factor_davenport


class TestNCh432:
    def test_qz_creciente_con_altura(self):
        r1 = evaluate_nch432(NCh432Input(Vb_m_s=32, h_m=10))
        r2 = evaluate_nch432(NCh432Input(Vb_m_s=32, h_m=50))
        assert r2.qz_kN_m2 > r1.qz_kN_m2

    def test_importancia_aumenta_q(self):
        rI = evaluate_nch432(NCh432Input(Vb_m_s=32, h_m=20, importance_class="I"))
        rIII = evaluate_nch432(NCh432Input(Vb_m_s=32, h_m=20, importance_class="III"))
        assert rIII.qz_kN_m2 > rI.qz_kN_m2


class TestDavenport:
    def test_Gf_positivo(self):
        r = gust_factor_davenport(DavenportInput(
            natural_period_s=2.0, height_m=80, Vz_m_per_s=30,
        ))
        assert r.G_f > 1.0  # flexible → amplificación dinámica

    def test_Q_R_son_valores_validos(self):
        r = gust_factor_davenport(DavenportInput(
            natural_period_s=2.0, height_m=80, Vz_m_per_s=30,
        ))
        assert 0 <= r.Q_background <= 2.0
        assert r.R_resonant >= 0
