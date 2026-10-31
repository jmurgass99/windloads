"""Tests viento multi-código."""
from windloads.codes_multi import (
    AS1170WindInput, NSR10WindInput, SSENWindInput,
    evaluate_as1170, evaluate_nsr10_wind, evaluate_ss_en_wind,
)


class TestAS1170:
    def test_qz_creciente_altura(self):
        r1 = evaluate_as1170(AS1170WindInput(V_R_m_s=45, height_m=10))
        r2 = evaluate_as1170(AS1170WindInput(V_R_m_s=45, height_m=50))
        assert r2.qz_kPa > r1.qz_kPa

    def test_categoria_terreno_afecta(self):
        rural = evaluate_as1170(AS1170WindInput(V_R_m_s=45, height_m=20,
                                                  terrain_category="2"))
        urban = evaluate_as1170(AS1170WindInput(V_R_m_s=45, height_m=20,
                                                  terrain_category="4"))
        assert rural.Mzcat > urban.Mzcat


class TestNSR10:
    def test_qz_positivo(self):
        r = evaluate_nsr10_wind(NSR10WindInput(V_m_s=35, height_m=30))
        assert r["qz_kPa"] > 0
        assert r["Kz"] > 0


class TestSSEN:
    def test_ce_creciente(self):
        a = evaluate_ss_en_wind(SSENWindInput(height_m=10))
        b = evaluate_ss_en_wind(SSENWindInput(height_m=50))
        assert b["ce"] > a["ce"]
