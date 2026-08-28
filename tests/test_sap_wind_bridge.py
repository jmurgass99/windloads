"""Tests for the pure-data WindLoadJm -> jmstructural-common / fastsap bridge."""
from __future__ import annotations
import pytest

from windloadjm.sap_bridge import wind_to_load_pattern, apply_wind_to_model
from jmstructural_common.model import Model, Node, Element, SectionRef, Material, LoadPattern, ElementLoad


class TestWindToLoadPatternBridge:
    def test_wind_pressure_to_element_loads_hand_derived(self) -> None:
        """Hand-derived anchor:

        Pressure q_p = 1250 Pa (1.25 kPa)
        Tributary width B = 4.0 m
        Line load w = 1.25 kPa * 4.0 m = 5.000 kN/m
        Frames = ['COL1', 'COL2', 'COL3']
        Direction = 'GlobalX'
        """
        pattern, elem_loads = wind_to_load_pattern(
            pressure_Pa=1250.0,
            tributary_width_m=4.0,
            frame_ids=["COL1", "COL2", "COL3"],
            pattern_name="WIND_X",
            direction="GlobalX",
        )

        assert pattern.name == "WIND_X"
        assert pattern.kind == "Wind"
        assert pattern.self_weight_multiplier == 0.0

        assert len(elem_loads) == 3
        for load, fid in zip(elem_loads, ["COL1", "COL2", "COL3"]):
            assert load.element_id == fid
            assert pytest.approx(load.w_kN_m, rel=1e-5) == 5.0
            assert load.direction == "GlobalX"
            assert load.pattern == "WIND_X"

    def test_apply_wind_to_canonical_model(self) -> None:
        """Applying wind bridge to a canonical Model produces an updated valid Model."""
        nodes = (
            Node("N1", 0.0, 0.0, 0.0),
            Node("N2", 0.0, 0.0, 4.0),
        )
        elements = (
            Element("C1", "N1", "N2", SectionRef("HEB300", "I"), "S355"),
        )
        model = Model(
            nodes=nodes,
            elements=elements,
            materials=(Material("S355", E_MPa=210000.0, nu=0.3, fy_MPa=355.0, rho_kg_m3=7850.0),),
            sections=(SectionRef("HEB300", "I"),),
        )

        # Apply 800 Pa wind on 5m tributary width -> w = 0.8 * 5 = 4.0 kN/m
        updated_model = apply_wind_to_model(
            model=model,
            pressure_Pa=800.0,
            tributary_width_m=5.0,
            frame_ids=["C1"],
            pattern_name="WIND_Y",
            direction="GlobalY",
        )

        assert any(p.name == "WIND_Y" for p in updated_model.patterns)
        assert len(updated_model.element_loads) == 1
        assert updated_model.element_loads[0].element_id == "C1"
        assert pytest.approx(updated_model.element_loads[0].w_kN_m, rel=1e-5) == 4.0
