"""Tests memoria factor de rafaga G_f (Davenport, ASCE 7-22 Eq. 26.11-10).

El memo re-expresa la ecuacion final con handcalcs; el test verifica que el
G_f resultante COINCIDE con la funcion canonica ``gust_factor_davenport`` ya
probada (anti-deriva). Se salta limpio si handcalcs no esta instalado (CI sin
el extra ``memos``).
"""
from __future__ import annotations

import pytest

handcalcs = pytest.importorskip("handcalcs")
from windloadjm.memos.gust_factor_memo import gust_factor_memo


class TestGustFactorMemo:
    def test_matches_canonical_davenport(self):
        from windloadjm.davenport import DavenportInput, gust_factor_davenport

        latex, res = gust_factor_memo(natural_period_s=2.0, height_m=50.0)
        canon = gust_factor_davenport(
            DavenportInput(natural_period_s=2.0, height_m=50.0)
        )
        assert res.G_f == pytest.approx(canon.G_f)          # anti-deriva real
        assert res.Q == pytest.approx(canon.Q_background)
        assert res.R == pytest.approx(canon.R_resonant)
        assert "\\" in latex

    def test_higher_damping_lower_gust(self):
        # Mas amortiguamiento -> menor respuesta resonante -> menor G_f
        _, low = gust_factor_memo(natural_period_s=2.0, height_m=50.0, damping_ratio=0.01)
        _, high = gust_factor_memo(natural_period_s=2.0, height_m=50.0, damping_ratio=0.05)
        assert high.G_f < low.G_f

    def test_flexible_structure_amplifies(self):
        # Mismo contrato que el test canonico de davenport: flexible -> G_f > 1.0,
        # Q en [0, 2], R >= 0 (sin acotar G_f por arriba: amort. bajo lo eleva).
        _, res = gust_factor_memo(natural_period_s=2.0, height_m=80.0, Vz_m_per_s=30.0)
        assert res.G_f > 1.0
        assert 0.0 <= res.Q <= 2.0
        assert res.R >= 0.0

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            gust_factor_memo(natural_period_s=0.0, height_m=50.0)
        with pytest.raises(ValueError):
            gust_factor_memo(natural_period_s=2.0, height_m=-5.0)
