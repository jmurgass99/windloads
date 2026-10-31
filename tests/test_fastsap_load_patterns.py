"""Tests del exportador FastSAPWindPatternExporter (windloads -> fastsap).

Cubre dos defectos del OAPI:
  1. Conversion de unidades kN -> N (SAP usa N internamente, igual que el
     bridge probado `apply_wind_loads_to_sap`).
  2. Los fallos OAPI deben reportarse, no tragarse en silencio.
"""
from __future__ import annotations

import pytest

from windloads.integration.fastsap_load_patterns import (
    WindLoadPattern,
    FastSAPWindPatternExporter,
)


class _StubSapModel:
    """SapModel-like que registra llamadas y permite forzar fallos."""

    def __init__(self, fail_on=None, raise_on=None):
        self.calls = []
        self._fail_on = set(fail_on or ())      # joints que devuelven ret != 0
        self._raise_on = set(raise_on or ())    # joints que lanzan excepcion
        outer = self

        class _LoadPatterns:
            @staticmethod
            def Add(name, type_, *a):
                outer.calls.append(("Add", name, type_))
                return 0

        class _PointObj:
            @staticmethod
            def SetLoadForce(name, pattern, f_vec, *a):
                outer.calls.append(("SetLoadForce", name, pattern, tuple(f_vec)))
                if name in outer._raise_on:
                    raise RuntimeError(f"COM error en {name}")
                return 1 if name in outer._fail_on else 0

        self.LoadPatterns = _LoadPatterns
        self.PointObj = _PointObj


def test_export_converts_kN_to_N_for_sap():
    """5 kN en un joint debe llegar a SAP como 5000 N."""
    sap = _StubSapModel()
    exp = FastSAPWindPatternExporter(client=sap, dry_run=False)

    exp.export([WindLoadPattern(name="WX", joint_loads={"J1": (5.0, 0.0, 0.0)})])

    set_calls = [c for c in sap.calls if c[0] == "SetLoadForce"]
    assert len(set_calls) == 1
    f_vec = set_calls[0][3]
    assert f_vec[0] == pytest.approx(5000.0)   # 5 kN -> 5000 N
    assert f_vec[1] == pytest.approx(0.0)
    assert f_vec[2] == pytest.approx(0.0)


def test_export_reports_failed_oapi_calls():
    """Un SetLoadForce que devuelve ret != 0 debe quedar registrado en 'failed'."""
    sap = _StubSapModel(fail_on={"J_BAD"})
    exp = FastSAPWindPatternExporter(client=sap, dry_run=False)

    res = exp.export([
        WindLoadPattern(name="WX", joint_loads={"J_OK": (5.0, 0, 0),
                                                 "J_BAD": (5.0, 0, 0)})
    ])

    assert res["applied"] == 1
    assert "J_BAD" in res["failed"]
    assert "J_OK" not in res["failed"]


def test_export_creates_pattern_as_OTHER_not_WIND():
    """El pattern debe crearse como 8=OTHER (cargas externas), no 6=WIND.

    Tipo WIND puede disparar la auto-generacion de viento de SAP y sumarse a las
    cargas manuales (doble conteo). Alinea con apply_wind_loads_to_sap.
    """
    sap = _StubSapModel()
    exp = FastSAPWindPatternExporter(client=sap, dry_run=False)

    exp.export([WindLoadPattern(name="WX", joint_loads={"J1": (5.0, 0, 0)})])

    add_calls = [c for c in sap.calls if c[0] == "Add"]
    assert len(add_calls) == 1
    assert add_calls[0][2] == 8   # eLoadPatternType OTHER, no 6=WIND


def test_export_does_not_swallow_exceptions_silently():
    """Una excepcion COM debe reflejarse en 'failed', no perderse."""
    sap = _StubSapModel(raise_on={"J_RAISE"})
    exp = FastSAPWindPatternExporter(client=sap, dry_run=False)

    res = exp.export([
        WindLoadPattern(name="WX", joint_loads={"J_RAISE": (5.0, 0, 0)})
    ])

    assert res["applied"] == 0
    assert "J_RAISE" in res["failed"]
    assert "COM error" in res["failed"]["J_RAISE"]
