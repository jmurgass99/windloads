# -*- coding: utf-8 -*-
"""test_wind_bridge_units.py — Pruebas de unidades físicas para el puente WindLoadJm.

Verifica rigurosamente la conversión dimensional:
    presión en Pa [N/m^2] -> q_kPa = p_Pa / 1000.0 [kN/m^2]
    carga lineal w [kN/m] = q_kPa * tributary_width_m

Cálculo a mano independiente (Derivación analítica):
  - Caso 1: p = 1250.0 Pa, B_trib = 4.0 m
    q = 1250.0 / 1000.0 = 1.25 kN/m^2
    w = 1.25 kN/m^2 * 4.0 m = 5.000 kN/m
  - Caso 2: p = -900.0 Pa (succión), B_trib = 2.6 m
    q = -900.0 / 1000.0 = -0.90 kN/m^2
    w = -0.90 * 2.6 = -2.340 kN/m
"""
from __future__ import annotations

import math
import pytest

from jmstructural_common.model import (
    Element,
    Material,
    Model,
    Node,
    Restraint,
    SectionRef,
)
from windloadjm.sap_bridge import apply_wind_to_model, wind_to_load_pattern


class TestWindBridgePhysicalUnits:
    def test_wind_pressure_pa_to_linear_load_kn_per_m_hand_calculation(self) -> None:
        """Verifica la conversión exacta Pa -> kN/m contra cálculo a mano."""
        p_Pa = 1250.0
        b_trib_m = 4.0
        frame_ids = ["BEAM_1", "BEAM_2"]

        # Derivación a mano independiente:
        # 1 Pa = 1 N/m^2 = 10^-3 kN/m^2
        # w = 1250 N/m^2 * (1 kN / 1000 N) * 4.0 m = 5.0 kN/m
        expected_w_kN_m = 5.0

        pattern, elem_loads = wind_to_load_pattern(
            pressure_Pa=p_Pa,
            tributary_width_m=b_trib_m,
            frame_ids=frame_ids,
            pattern_name="W_X",
            direction="GlobalX",
        )

        assert pattern.name == "W_X"
        assert pattern.kind == "Wind"
        assert pattern.self_weight_multiplier == 0.0
        assert len(elem_loads) == 2
        for el in elem_loads:
            assert el.pattern == "W_X"
            assert el.direction == "GlobalX"
            assert pytest.approx(el.w_kN_m, rel=1e-9) == expected_w_kN_m

    def test_wind_suction_negative_sign_preservation(self) -> None:
        """Verifica que la succión negativa preserve rigurosamente el signo y la magnitud."""
        p_Pa = -900.0
        b_trib_m = 2.6
        frame_ids = ["ROOF_1"]

        # w = (-900 / 1000) * 2.6 = -2.34 kN/m
        expected_w_kN_m = -2.34

        pattern, elem_loads = wind_to_load_pattern(
            pressure_Pa=p_Pa,
            tributary_width_m=b_trib_m,
            frame_ids=frame_ids,
            pattern_name="W_SUCC",
            direction="-GlobalZ",
        )

        assert len(elem_loads) == 1
        assert pytest.approx(elem_loads[0].w_kN_m, rel=1e-9) == expected_w_kN_m

    def test_apply_wind_to_canonical_model_preserves_invariants(self) -> None:
        """Verifica que apply_wind_to_model integre la carga sin alterar la topología."""
        n1 = Node("N1", 0.0, 0.0, 0.0)
        n2 = Node("N2", 5.0, 0.0, 0.0)
        mat = Material("A36", 200000.0, 0.3, 250.0, 7850.0)
        sec = SectionRef("IPE200", "I")
        el = Element("B1", "N1", "N2", sec, "A36")
        res = Restraint("N1", True, True, True, True, True, True)
        
        base_model = Model(
            nodes=(n1, n2),
            restraints=(res,),
            materials=(mat,),
            sections=(sec,),
            elements=(el,),
        )

        updated_model = apply_wind_to_model(
            model=base_model,
            pressure_Pa=800.0,
            tributary_width_m=3.5,
            frame_ids=["B1"],
            pattern_name="WIND_Y",
            direction="GlobalY",
        )

        # w = 0.800 kN/m^2 * 3.5 m = 2.80 kN/m
        assert any(p.name == "WIND_Y" for p in updated_model.patterns)
        assert len(updated_model.element_loads) == 1
        assert updated_model.element_loads[0].element_id == "B1"
        assert pytest.approx(updated_model.element_loads[0].w_kN_m, rel=1e-9) == 2.80

    def test_invalid_tributary_width_raises_value_error(self) -> None:
        """Ancho tributario <= 0 debe ser rechazado defensivamente."""
        with pytest.raises(ValueError, match="tributary_width_m"):
            wind_to_load_pattern(pressure_Pa=1000.0, tributary_width_m=0.0, frame_ids=["B1"])
        with pytest.raises(ValueError, match="tributary_width_m"):
            wind_to_load_pattern(pressure_Pa=1000.0, tributary_width_m=-2.0, frame_ids=["B1"])
