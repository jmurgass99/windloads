"""Tests para dxf_wind_plan."""
from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from windloadjm.integration import dxf_wind_plan as dwp


def _square_plant(side: float = 20.0):
    return [(0.0, 0.0), (side, 0.0), (side, side), (0.0, side)]


def test_build_dxf_basic(tmp_path):
    out = tmp_path / "wind.dxf"
    inp = dwp.WindPlanInput(
        plant_m=_square_plant(),
        qz_kPa=1.0,
        zone_loads=[
            dwp.WindZoneLoad("windward", +0.8, +0.8),
            dwp.WindZoneLoad("leeward", -0.5, -0.5),
            dwp.WindZoneLoad("side_left", -0.7, -0.7),
            dwp.WindZoneLoad("side_right", -0.7, -0.7),
        ],
        project="Edif. demo",
        code="ASCE7-22",
    )
    doc = dwp.build_wind_plan_dxf(inp, out)
    assert out.exists()

    doc2 = ezdxf.readfile(str(out))
    layers = {l.dxf.name for l in doc2.layers}
    for required in ("W-OUTLINE", "W-PRESS", "W-SUCT", "W-LEGEND", "W-TEXT", "W-TITLE"):
        assert required in layers

    msp = doc2.modelspace()
    polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    # contorno + legend box + title block = al menos 3
    assert len(polylines) >= 3


def test_arrows_drawn(tmp_path):
    out = tmp_path / "arrows.dxf"
    inp = dwp.WindPlanInput(
        plant_m=_square_plant(),
        qz_kPa=1.0,
        zone_loads=[dwp.WindZoneLoad("windward", 0.8, 0.8)],
    )
    dwp.build_wind_plan_dxf(inp, out)
    doc2 = ezdxf.readfile(str(out))
    # presión positiva → capa W-PRESS
    press_lines = [e for e in doc2.modelspace()
                   if e.dxftype() == "LINE" and e.dxf.layer == "W-PRESS"]
    # cuerpo + 2 puntas de flecha = 3 líneas
    assert len(press_lines) == 3


def test_suction_separate_layer(tmp_path):
    out = tmp_path / "suct.dxf"
    inp = dwp.WindPlanInput(
        plant_m=_square_plant(),
        qz_kPa=1.0,
        zone_loads=[dwp.WindZoneLoad("leeward", -0.5, -0.5)],
    )
    dwp.build_wind_plan_dxf(inp, out)
    doc2 = ezdxf.readfile(str(out))
    suct = [e for e in doc2.modelspace() if e.dxf.layer == "W-SUCT"]
    assert len(suct) >= 3


def test_from_wind_result_dict():
    inp = dwp.from_wind_result(
        {"qz_kPa": 1.234},
        _square_plant(),
        project="X", code="EC1",
    )
    assert inp.qz_kPa == pytest.approx(1.234)
    assert len(inp.zone_loads) == 4
    assert inp.zone_loads[0].pressure_kPa == pytest.approx(1.234 * 0.8)


def test_from_wind_result_with_pa():
    inp = dwp.from_wind_result({"qz_Pa": 1500.0}, _square_plant())
    assert inp.qz_kPa == pytest.approx(1.5)


def test_from_wind_result_dataclass():
    class FakeRes:
        qz_kPa = 0.9
    inp = dwp.from_wind_result(FakeRes(), _square_plant(),
                                cp_by_face={"windward": 0.8, "leeward": -0.5})
    assert inp.qz_kPa == 0.9
    assert len(inp.zone_loads) == 2


def test_from_wind_result_invalid():
    with pytest.raises(ValueError):
        dwp.from_wind_result({"foo": 1}, _square_plant())
