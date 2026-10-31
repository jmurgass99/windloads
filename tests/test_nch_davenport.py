"""Tests NCh 432 + Davenport."""
import pytest

from windloads.nch432 import NCh432Input, evaluate_nch432
from windloads.davenport import DavenportInput, gust_factor_davenport


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

    def test_Gf_en_rango_fisico(self):
        # Regresion del bug de signo en Rh: el factor de altura debe usar
        # (1 - e^(-2*eta)), no (1 - e^(+2*eta)). Con el bug, R~19 y G_f~13.5
        # (irreal). Corregido, un edificio flexible tipico da G_f ~0.8-2.5.
        r = gust_factor_davenport(DavenportInput(natural_period_s=2.0, height_m=50.0))
        assert r.R_resonant < 3.0
        assert 0.8 < r.G_f < 2.5

    def test_Rh_factor_decrece_con_la_altura_normalizada(self):
        # R_h fisico es decreciente en eta_h: un edificio mas alto (mayor eta_h)
        # tiene menor contribucion resonante de altura -> menor R (a igualdad de
        # lo demas). Con el signo invertido esta monotonia se rompe.
        bajo = gust_factor_davenport(DavenportInput(
            natural_period_s=2.0, height_m=30.0, Vz_m_per_s=35.0))
        alto = gust_factor_davenport(DavenportInput(
            natural_period_s=2.0, height_m=90.0, Vz_m_per_s=35.0))
        assert alto.R_resonant < bajo.R_resonant
