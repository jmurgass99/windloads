# -*- coding: utf-8 -*-
"""Cuatro casos de carga MWFRS — ASCE 7-22 §27.3.5 / Fig 27.3-8."""
import pytest

from windloads.mwfrs_load_cases import WindLoadCase, envelope, mwfrs_load_cases


@pytest.fixture
def cases():
    # Px=1000 kN, Py=800 kN, Bx=40 m, By=30 m
    return mwfrs_load_cases(1000.0, 800.0, 40.0, 30.0)


class TestCases:
    def test_genera_seis_subcasos(self, cases):
        # Caso 1 (X,Y) + Caso 2 (X,Y) + Caso 3 + Caso 4 = 6 sub-casos.
        assert len(cases) == 6
        assert {c.name for c in cases} == {"1-X", "1-Y", "2-X", "2-Y", "3", "4"}

    def test_caso1_sin_torsion_full(self, cases):
        c = next(c for c in cases if c.name == "1-X")
        assert c.Px_kN == 1000.0 and c.Py_kN == 0.0 and c.Mt_kNm == 0.0

    def test_caso2_75pct_con_torsion(self, cases):
        c = next(c for c in cases if c.name == "2-X")
        assert c.Px_kN == pytest.approx(0.75 * 1000.0)
        # M_T = 0.75·P·(0.15·Bx) = 0.75·1000·6 = 4500
        assert c.Mt_kNm == pytest.approx(0.75 * 1000.0 * 0.15 * 40.0)

    def test_caso3_ambos_ejes_sin_torsion(self, cases):
        c = next(c for c in cases if c.name == "3")
        assert c.Px_kN == pytest.approx(750.0) and c.Py_kN == pytest.approx(600.0)
        assert c.Mt_kNm == 0.0

    def test_caso4_563pct_y_torsion_combinada(self, cases):
        c = next(c for c in cases if c.name == "4")
        assert c.Px_kN == pytest.approx(0.563 * 1000.0)
        Mt = 0.563 * (1000.0 * 0.15 * 40.0 + 800.0 * 0.15 * 30.0)
        assert c.Mt_kNm == pytest.approx(Mt)


class TestEnvelope:
    def test_envolvente(self, cases):
        env = envelope(cases)
        assert env["Px_max_kN"] == pytest.approx(1000.0)   # caso 1 gobierna fuerza
        assert env["Mt_max_kNm"] > 0                        # la torsion proviene de casos 2/4
