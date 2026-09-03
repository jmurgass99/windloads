"""Tests de rigor normativo para WindLoadJm (Bloque A).

A.1: Coeficiente orográfico c_o en report_ec1.py.
     - La omisión de c_o en colinas (Phi = 0.3..0.5) subestima q_p en ~59%.
     - report_ec1 debe admitir c_o (o calcularlo con topography.py) o declarar
       la limitación explícita de terreno plano en la memoria.
A.2: Factor estructural Cs_Cd en ec1_1_4.py.
     - EN 1991-1-4 §6.2(1) Nota 1a solo permite Cs_Cd = 1.0 incondicional para H <= 15 m.
     - Para H > 15 m, se debe exigir justificación explícita o advertir limitación.
"""
from __future__ import annotations

import pytest
from windloadjm.topography import ec1_orography_factor_A3
from windloadjm.report_ec1 import EC1ReportInput, generar_reporte_ec1
from windloadjm.codes.ec1_1_4 import EC1WindLoad


def test_orography_factor_numerical_impact():
    """Demuestra cuantitativamente el impacto de c_o en colinas típicas.

    Phi = 0.3 -> c_o = 1.5528 -> qp se multiplica por 2.411 (+141.1%).
    Asumir c_o = 1.0 en silencio subestima la presión en -58.5%.
    """
    co_03 = ec1_orography_factor_A3(z=10.0, x=0.0, H=60.0, Lu=200.0, kind="hill")
    assert co_03 == pytest.approx(1.5528, rel=0.01)
    ratio_qp_03 = co_03 ** 2
    assert ratio_qp_03 == pytest.approx(2.411, rel=0.01)

    co_05 = ec1_orography_factor_A3(z=10.0, x=0.0, H=100.0, Lu=200.0, kind="hill")
    assert co_05 == pytest.approx(1.5740, rel=0.01)
    ratio_qp_05 = co_05 ** 2
    assert ratio_qp_05 == pytest.approx(2.4775, rel=0.01)


def test_report_ec1_declares_orography_limitation_when_absent():
    """Si no se suministra c_o, la memoria debe declarar LIMITACIÓN explícita."""
    inp = EC1ReportInput(vb_0_m_s=26.0, H_m=12.0, B_m=15.0, L_m=20.0, terrain_category=2)
    md = generar_reporte_ec1(inp)
    assert "c_o" in md
    assert "LIMITACIÓN" in md or "limitación" in md or "terreno plano" in md.lower()


def test_report_ec1_incorporates_explicit_co():
    """Si se pasa c_o explícito, vm y qp deben responder a c_o y c_o^2."""
    inp_flat = EC1ReportInput(vb_0_m_s=26.0, H_m=10.0, B_m=15.0, L_m=20.0, terrain_category=2, c_o=1.0)
    inp_hill = EC1ReportInput(vb_0_m_s=26.0, H_m=10.0, B_m=15.0, L_m=20.0, terrain_category=2, c_o=1.50)

    md_flat = generar_reporte_ec1(inp_flat)
    md_hill = generar_reporte_ec1(inp_hill)

    assert "c_o = 1.500" in md_hill
    # Extraer q_p de ambas memorias
    import re
    m_flat = re.search(r"q_p\(z\)\s*=\s*([\d\.]+)\s*Pa", md_flat)
    m_hill = re.search(r"q_p\(z\)\s*=\s*([\d\.]+)\s*Pa", md_hill)
    assert m_flat and m_hill
    qp_flat = float(m_flat.group(1))
    qp_hill = float(m_hill.group(1))

    # Extraer v_m de ambas memorias
    m_vm_flat = re.search(r"v_m\(z\)\s*=\s*([\d\.]+)\s*m/s", md_flat)
    m_vm_hill = re.search(r"v_m\(z\)\s*=\s*([\d\.]+)\s*m/s", md_hill)
    assert m_vm_flat and m_vm_hill
    vm_flat = float(m_vm_flat.group(1))
    vm_hill = float(m_vm_hill.group(1))

    # Con c_o = 1.50, vm sube exactamente 1.5x
    assert vm_hill == pytest.approx(vm_flat * 1.50, rel=0.01)
    # Y qp sube según EN 1991-1-4 Eq 4.8 con Iv(z) amortiguado por co en denominador
    assert qp_hill > qp_flat * 1.80


def test_ec1_structural_factor_cscd_declared_scope():
    """Para H <= 15 m, Cs_Cd = 1.0 está justificado por EN 1991-1-4 §6.2(1) Nota 1a.

    Para H > 15 m, Cs_Cd = 1.0 sin comprobar altura afirma la condición en silencio.
    El objeto debe reportar si Cs_Cd cuenta con justificación o requiere verificación.
    """
    # Caso 1: Edificio bajo (H = 12 m <= 15 m)
    low_rise = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=12.0)
    summary_low = low_rise.compute()
    assert summary_low["Cs_Cd"] == 1.0
    assert "justified" in summary_low.get("Cs_Cd_status", "").lower() or summary_low.get("Cs_Cd_justified") is True

    # Caso 2: Edificio alto (H = 30 m > 15 m) sin Cs_Cd explícito
    high_rise = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=30.0)
    summary_high = high_rise.compute()
    assert summary_high.get("Cs_Cd_justified") is False or "requiere" in summary_high.get("Cs_Cd_status", "").lower()
