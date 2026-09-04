"""Tests IDEAS_20 grupos A/B/C en WindLoadJm."""
import pytest


def test_cp_arco():
    from windloadjm.cp_techos_complejos import (
        TechoComplejoInput, cp_techo_complejo, cp_arco,
    )
    cp = cp_arco(0.2, "EU")
    assert "cumbrera" in cp
    res = cp_techo_complejo(TechoComplejoInput(tipo="arco", f_h_ratio=0.2, code="EU"))
    assert res.cp_zonas


def test_cp_multi_agua_diente():
    from windloadjm.cp_techos_complejos import TechoComplejoInput, cp_techo_complejo
    r1 = cp_techo_complejo(TechoComplejoInput(
        tipo="multi_agua", n_aguas=3, alpha_deg=15, code="US",
    ))
    assert len(r1.cp_zonas) == 6
    r2 = cp_techo_complejo(TechoComplejoInput(
        tipo="diente_sierra", n_aguas=4, code="EU",
    ))
    assert "primera_pendiente" in r2.cp_zonas


def test_cp_tipo_invalido():
    from windloadjm.cp_techos_complejos import TechoComplejoInput, cp_techo_complejo
    with pytest.raises(ValueError):
        cp_techo_complejo(TechoComplejoInput(tipo="ZZZ"))


def test_report_ec1():
    from windloadjm.report_ec1 import EC1ReportInput, generar_reporte_ec1
    md = generar_reporte_ec1(EC1ReportInput(
        vb_0_m_s=27, H_m=20, B_m=15, L_m=30, terrain_category=2,
    ))
    assert "EN 1991" in md
    assert "v_b" in md


def test_fastsap_wind_pattern_dry_run():
    from windloadjm.integration.fastsap_load_patterns import (
        WindLoadPattern, FastSAPWindPatternExporter,
    )
    p1 = WindLoadPattern(name="WX", joint_loads={"J1": (10, 0, 0), "J2": (10, 0, 0)})
    exp = FastSAPWindPatternExporter(dry_run=True)
    r = exp.export([p1])
    assert r["dry_run"] is True
    assert r["n_loads"] == 2


def test_fastsap_wind_pattern_mock():
    from unittest.mock import MagicMock
    from windloadjm.integration.fastsap_load_patterns import (
        WindLoadPattern, FastSAPWindPatternExporter,
    )
    mock = MagicMock()
    exp = FastSAPWindPatternExporter(client=mock, dry_run=False)
    r = exp.export([WindLoadPattern(name="WX", joint_loads={"J1": (5, 0, 0)})])
    assert r["dry_run"] is False
