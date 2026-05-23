"""Tests del bridge windloadjm -> fastsap con mock COM."""
from __future__ import annotations
from types import SimpleNamespace
import pytest

from windloadjm.integration import (
    WindLoadAssignment, apply_wind_loads_to_sap,
    distribute_pressure_to_joints,
)


def _make_mock_sap(existing_patterns=("DEAD",), fail_on=None):
    fail_on = set(fail_on or set())
    calls = []
    state = {"patterns": list(existing_patterns)}

    class _LoadPatterns:
        @staticmethod
        def GetNameList():
            return (len(state["patterns"]), list(state["patterns"]), 0)
        @staticmethod
        def Add(name, type_, self_weight=0.0, add_combos=True):
            state["patterns"].append(name)
            calls.append(("LoadPatterns.Add", name, type_))
            return 0

    class _PointObj:
        @staticmethod
        def SetLoadForce(name, pattern, f_vec, replace, csys, item_type):
            calls.append(("SetLoadForce", name, pattern, tuple(f_vec)))
            if name in fail_on:
                return 1
            return 0

    class _SapModel:
        LoadPatterns = _LoadPatterns
        PointObj = _PointObj

    sap = SimpleNamespace(SapModel=_SapModel)
    return sap, calls, state


def test_distribute_pressure_basic():
    asss = distribute_pressure_to_joints(
        joints=["J1", "J2", "J3"],
        pressure_kN_m2=1.5,
        tributary_area_m2=[2.0, 4.0, 2.0],
        direction="X",
    )
    assert len(asss) == 3
    assert asss[0].Fx_kN == 3.0   # 1.5 * 2
    assert asss[1].Fx_kN == 6.0   # 1.5 * 4
    assert asss[2].Fx_kN == 3.0


def test_distribute_pressure_invalid_inputs():
    with pytest.raises(ValueError):
        distribute_pressure_to_joints(["J1"], 1.0, [1.0, 2.0])  # lengths mismatch
    with pytest.raises(ValueError):
        distribute_pressure_to_joints(["J1"], 1.0, [1.0], direction="Q")


def test_apply_wind_loads_basic_creates_pattern():
    sap, calls, state = _make_mock_sap(existing_patterns=("DEAD",))
    asss = distribute_pressure_to_joints(
        ["J1", "J2"], 2.0, [1.0, 1.5], direction="X",
    )
    res = apply_wind_loads_to_sap(sap, asss, load_pattern="WIND_NEW")
    assert "WIND_NEW" in state["patterns"]      # pattern creado
    assert res.n_joints_loaded == 2
    assert abs(res.total_Fx_kN - (2.0 + 3.0)) < 0.01


def test_apply_wind_loads_skips_existing_pattern_creation():
    sap, calls, _ = _make_mock_sap(existing_patterns=("WIND_EXIST",))
    res = apply_wind_loads_to_sap(
        sap,
        [WindLoadAssignment(joint_name="J1", Fx_kN=10.0)],
        load_pattern="WIND_EXIST",
    )
    # No deberia haber LoadPatterns.Add call
    add_calls = [c for c in calls if c[0] == "LoadPatterns.Add"]
    assert add_calls == []


def test_apply_wind_loads_partial_failure_collected():
    sap, _, _ = _make_mock_sap(fail_on={"J_BAD"})
    asss = [
        WindLoadAssignment(joint_name="J1", Fx_kN=10.0),
        WindLoadAssignment(joint_name="J_BAD", Fx_kN=15.0),
        WindLoadAssignment(joint_name="J3", Fx_kN=5.0),
    ]
    res = apply_wind_loads_to_sap(sap, asss, load_pattern="WIND_X", fatal=False)
    assert "J1" in res.applied and "J3" in res.applied
    assert "J_BAD" in res.failed
    assert res.n_joints_loaded == 2


def test_apply_wind_loads_empty_raises():
    sap, _, _ = _make_mock_sap()
    with pytest.raises(ValueError):
        apply_wind_loads_to_sap(sap, [], load_pattern="WIND")


def test_apply_wind_loads_converts_kN_to_N_for_SAP():
    """SAP usa N internamente; el bridge debe multiplicar por 1000."""
    sap, calls, _ = _make_mock_sap()
    apply_wind_loads_to_sap(
        sap, [WindLoadAssignment(joint_name="J1", Fx_kN=5.0)],
        load_pattern="WIND_X",
    )
    set_calls = [c for c in calls if c[0] == "SetLoadForce"]
    assert len(set_calls) == 1
    f_vec = set_calls[0][3]
    assert abs(f_vec[0] - 5000.0) < 0.01  # 5 kN -> 5000 N
