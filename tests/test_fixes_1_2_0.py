"""Correcciones de la 1.2.0, cada una con su oráculo calculado a mano o por un
método independiente (fórmula de la norma reescrita en el test).

Fuentes: EN 1991-1-4:2005+A1:2010 (Tabla 7.1, §7.2.2, Fig. 7.4, Tablas 7.3a,
7.4a y 7.4b, Anexo A.3 Expr. A.4-A.13, Anexo E Tabla E.5 y Expr. E.18-E.19);
ASCE 7-10 Fig. 26.8-1; ASCE 7-16 Fig. 27.3-1 (copia escaneada); Arroyo Amell
y Ramos Castillo (2015) para las velocidades de la NSR-10.
"""
from __future__ import annotations

import math
import tomllib
from pathlib import Path

import pytest

from windloads import EC1WindLoad, __version__
from windloads.envelope import StoryWindForce
from windloads.exceptions import ConfigurationError
from windloads.pressure import (
    asce7_Cp_walls,
    asce7_leeward_Cp,
    ec1_cpe_walls,
    ec1_lack_of_correlation_factor,
    ec1_windward_reference_height,
)
from windloads.terrain import TerrainProfile


def _qp_ec1(z: float, vb: float, z0: float, zmin: float, rho: float = 1.25) -> float:
    """q_p(z) de EN 1991-1-4 (4.8) reescrito: k_r = 0,19·(z0/0,05)^0,07."""
    ze = max(z, zmin)
    kr = 0.19 * (z0 / 0.05) ** 0.07
    ln = math.log(ze / z0)
    vm = kr * ln * vb
    return (1.0 + 7.0 / ln) * 0.5 * rho * vm * vm


# --------------------------------------------------------------- Tabla 7.1
class TestEC1WallCoefficients:
    @pytest.mark.parametrize("h,d", [(5.0, 20.0), (12.0, 12.0), (50.0, 10.0)])
    def test_zone_A_is_minus_1_2_for_every_h_over_d(self, h, d):
        # Tabla 7.1: cpe,10 de la zona A = -1,2 en las tres filas (antes -1,0).
        assert ec1_cpe_walls(h, d)["A"] == pytest.approx(-1.2)

    def test_zone_E_interpolated_between_1_and_5(self):
        # E: -0,5 (h/d = 1) -> -0,7 (h/d = 5); h/d = 2 -> -0,55; h/d >= 5 -> -0,7.
        assert ec1_cpe_walls(20.0, 10.0)["E"] == pytest.approx(-0.55)
        assert ec1_cpe_walls(70.0, 10.0)["E"] == pytest.approx(-0.7)

    def test_lack_of_correlation_factor(self):
        # §7.2.2(3): 0,85 (h/d <= 1), 1,0 (h/d >= 5), lineal: h/d = 3 -> 0,925.
        assert ec1_lack_of_correlation_factor(5.0, 10.0) == pytest.approx(0.85)
        assert ec1_lack_of_correlation_factor(30.0, 10.0) == pytest.approx(0.925)
        assert ec1_lack_of_correlation_factor(60.0, 10.0) == pytest.approx(1.0)

    def test_reference_height_rules_figure_7_4(self):
        # h <= b: ze = h en toda la fachada.
        assert ec1_windward_reference_height(3.0, 10.0, 20.0) == 10.0
        # b < h <= 2b: ze = b hasta z = b y ze = h encima.
        assert ec1_windward_reference_height(15.0, 30.0, 20.0) == 20.0
        assert ec1_windward_reference_height(25.0, 30.0, 20.0) == 30.0
        # h > 2b: ze = b abajo, ze = h en los b superiores, franjas en medio.
        assert ec1_windward_reference_height(10.0, 60.0, 20.0) == 20.0
        assert ec1_windward_reference_height(30.0, 60.0, 20.0) == 30.0
        assert ec1_windward_reference_height(45.0, 60.0, 20.0) == 60.0


class TestEC1StoryForces:
    def test_base_shear_h_le_b_matches_hand_calculation(self):
        """H = 12 m (4 x 3 m), b = 20 m, d = 12 m, terreno II, vb = 26 m/s.

        h <= b -> ze = h en toda la fachada; h/d = 1 -> cpe,D = +0,8,
        cpe,E = -0,5, f = 0,85. q_p(12) = 1043,28 Pa (fórmula reescrita).
        V_b = 0,85·(0,8 + 0,5)·q_p(12)·20·12 / 1000 = 276,68 kN.
        Antes de 1.2.0: sum q_p(z_top)·(0,8 + 0,3)·20·3 / 1000 = 235,1 kN (-15 %).
        """
        wl = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=12.0,
                         width=20.0, depth=12.0, story_heights=[3.0] * 4)
        qp12 = _qp_ec1(12.0, 26.0, 0.05, 2.0)
        assert qp12 == pytest.approx(1043.28, abs=0.01)
        expected = 0.85 * (0.8 + 0.5) * qp12 * 20.0 * 12.0 / 1000.0
        assert wl.compute()["Vb_kN"] == pytest.approx(expected, abs=0.05)

    def test_tall_building_uses_strips_and_leeward_qp_h(self):
        """H = 60 m (20 x 3 m), b = 15 m, d = 15 m (h/d = 4, h > 2b), terreno III."""
        H, b, d, vb = 60.0, 15.0, 15.0, 27.0
        wl = EC1WindLoad(vb=vb, terrain_cat="III", building_height=H,
                         width=b, depth=d, story_heights=[3.0] * 20, Cs_Cd=1.0)
        cpe_E = -0.5 + (4.0 - 1.0) / 4.0 * (-0.2)          # -0,65
        f = 0.85 + (4.0 - 1.0) / 4.0 * 0.15                # 0,9625
        qp_h = _qp_ec1(H, vb, 0.3, 5.0)
        total = 0.0
        for i in range(20):
            z_top = 3.0 * (i + 1)
            ze = b if z_top <= b else (H if z_top >= H - b else z_top)
            total += f * (0.8 * _qp_ec1(ze, vb, 0.3, 5.0) - cpe_E * qp_h) * b * 3.0 / 1000.0
        assert wl.compute()["Vb_kN"] == pytest.approx(total, rel=1e-3)

    def test_dominant_opening_is_rejected_instead_of_ignored(self):
        with pytest.raises(ConfigurationError):
            EC1WindLoad(vb=26.0, terrain_cat="II", building_height=10.0,
                        enclosure="open_one_face")


# --------------------------------------------------------------- ASCE 7 Cp
class TestASCE7Leeward:
    @pytest.mark.parametrize("LB,cp", [(0.5, -0.5), (1.0, -0.5), (1.5, -0.4),
                                        (2.0, -0.3), (3.0, -0.25), (4.0, -0.2), (6.0, -0.2)])
    def test_leeward_cp_linear_interpolation(self, LB, cp):
        # Fig. 27.3-1: -0,5 (0-1), -0,3 (2), -0,2 (>= 4), interpolación lineal.
        assert asce7_leeward_Cp(LB) == pytest.approx(cp)

    def test_asce7_Cp_walls_uses_interpolation(self):
        # L/B = 30/20 = 1,5 -> -0,4 (antes -0,3, del lado inseguro).
        assert asce7_Cp_walls(30.0, 20.0, 10.0)["leeward"] == pytest.approx(-0.4)

    def test_mwfrs_memo_without_handcalcs(self, monkeypatch):
        """Sin handcalcs la memoria lanzaba TypeError al desempaquetar un float.

        Oráculo: Kz(10 m, C) = 2,01·(10/274,32)^(2/9,5); q = 0,613·Kz·0,85·40²/1000.
        L/B = 2 -> Cp_l = -0,3; p_diseño = max |q·(G·Cp ∓ GCpi)| = q·(0,85·0,8 + 0,18).
        """
        import importlib
        import sys
        import windloads.memos.asce7_mwfrs as mod
        monkeypatch.setitem(sys.modules, "handcalcs", None)
        monkeypatch.setitem(sys.modules, "handcalcs.decorator", None)
        mod2 = importlib.reload(mod)
        try:
            assert mod2._HAS_HANDCALCS is False
            _, r = mod2.mwfrs_directional_memo(V_ms=40.0, z=10.0, exposure="C",
                                               L_over_B=2.0)
            Kz = 2.01 * (10.0 / 274.32) ** (2.0 / 9.5)
            q = 0.613 * Kz * 0.85 * 40.0 ** 2 / 1000.0
            assert r.q_z_kN_m2 == pytest.approx(q, rel=1e-9)
            assert r.p_design_kN_m2 == pytest.approx(q * (0.85 * 0.8 + 0.18), rel=1e-9)
            assert "Cp sotavento = -0.30" in r.notes[2]
        finally:
            monkeypatch.undo()
            importlib.reload(mod)


# --------------------------------------------------------------- Anexo A.3
class TestOrographyAnnexA3:
    def test_hill_downwind_expression_A11(self):
        """Colina H = 20, Lu = Ld = 100 (Φ = 0,2, Le = 100), z = 10, x = +50.

        z/Le = 0,1; X/Ld = 0,5. (A.12) A = 0,83854; (A.13)
        B = -0,3056·0,01 + 1,0212·0,1 - 1,7637 = -1,66464; s = A·e^(B·0,5) = 0,36480;
        c_o = 1 + 2·0,36480·0,2 = 1,14592. (Antes: s ≈ 0,01 -> c_o ≈ 1,00.)
        """
        from windloads.topography import ec1_orography_factor_A3
        A = 0.1552e-4 - 0.8575e-3 + 1.8133e-2 - 0.19115 + 1.0124
        B = -0.3056 * 0.01 + 1.0212 * 0.1 - 1.7637
        s = A * math.exp(B * 0.5)
        co = ec1_orography_factor_A3(z=10.0, x=50.0, H=20.0, Lu=100.0, Ld=100.0, kind="hill")
        assert co == pytest.approx(1.0 + 2.0 * s * 0.2, abs=1e-9)
        assert co == pytest.approx(1.14592, abs=1e-5)

    def test_hill_is_continuous_across_the_crest(self):
        from windloads.topography import ec1_orography_factor_A3
        up = ec1_orography_factor_A3(z=0.0, x=-0.01, H=20.0, Lu=100.0, Ld=100.0)
        down = ec1_orography_factor_A3(z=0.0, x=0.01, H=20.0, Lu=100.0, Ld=100.0)
        assert down == pytest.approx(up, abs=1e-3)
        assert down > 1.39   # antes 1,004 justo a sotavento de la cresta

    def test_cliff_downwind_expression_A7_and_steep_Le(self):
        """Escarpe H = 50, Lu = 100 (Φ = 0,5 > 0,3): Le = H/0,3 = 166,67 (Tabla A.2).

        z = Le/10, x = 0,2·Le -> log(z/Le) = -1: A = -0,0202, B = -0,5213,
        C = 0,3550; s = A·log(0,2)² + B·log(0,2) + C = 0,70950; c_o = 1 + 0,6·s.
        """
        from windloads.topography import ec1_orography_factor_A3
        lx = math.log10(0.2)
        a = 1.3420 - 0.8222 - 0.4609 - 0.0791
        b = 1.0196 - 0.8910 - 0.5343 - 0.1156
        c = -0.8030 + 0.4236 + 0.5738 + 0.1606
        s = a * lx * lx + b * lx + c
        Le = 50.0 / 0.3
        co = ec1_orography_factor_A3(z=Le / 10.0, x=0.2 * Le, H=50.0, Lu=100.0, kind="cliff")
        assert co == pytest.approx(1.0 + 0.6 * s, abs=1e-9)
        assert co == pytest.approx(1.42570, abs=1e-5)

    def test_s_is_zero_outside_the_upwind_range(self):
        # (A.4): s = 0 para X/Lu < -1,5 -> c_o = 1.
        from windloads.topography import ec1_orography_factor_A3
        assert ec1_orography_factor_A3(z=5.0, x=-200.0, H=20.0, Lu=100.0) == 1.0


# --------------------------------------------------------------- ASCE Kzt
class TestASCE7Kzt:
    def test_ridge_exposure_C_at_crest(self):
        # H/Lh = 0,3: K1 = 1,45·0,3 = 0,435 (tabla de la figura: 0,43); Kzt = 1,435².
        from windloads.topography import asce7_Kzt_simple
        assert asce7_Kzt_simple(30.0, 100.0, 0.0, 0.0, "ridge", "C") == pytest.approx(1.435 ** 2)

    def test_escarpment_downwind_uses_mu_4_and_gamma_2_5(self):
        # x/Lh = 1 -> K2 = 1 - 1/4 = 0,75 (tabla: 0,75); z/Lh = 0,1 -> K3 = e^-0,25 (tabla 0,78).
        from windloads.topography import asce7_Kzt_simple
        k = asce7_Kzt_simple(30.0, 100.0, 100.0, 10.0, "escarpment", "C")
        assert k == pytest.approx((1 + 0.85 * 0.3 * 0.75 * math.exp(-0.25)) ** 2)

    def test_steep_3d_hill_caps_H_over_Lh_and_uses_2H(self):
        # H/Lh = 0,6 > 0,5: K1 = 1,05·0,5; Lh -> 2H = 120 m; K3 = e^(-4·12/120).
        from windloads.topography import asce7_Kzt_simple
        k = asce7_Kzt_simple(60.0, 100.0, 0.0, 12.0, "hill", "C")
        assert k == pytest.approx((1 + 0.525 * math.exp(-0.4)) ** 2)

    def test_low_feature_in_exposure_B_is_ignored(self):
        # §26.8.1(5): H >= 18 m en exposición B; con H = 10 m, Kzt = 1.
        from windloads.topography import asce7_Kzt_simple
        assert asce7_Kzt_simple(10.0, 40.0, 0.0, 0.0, "ridge", "B") == 1.0


# --------------------------------------------------------------- Anexo E
class TestVortexDefaults:
    def test_mode_shape_factor_default_is_cantilever_0_13(self):
        """(E.7): y/b = (1/St²)(1/Sc)·K·Kw·c_lat con K = 0,13 (Tabla E.5).

        D = 1, m = 300, δ = 0,03 -> Sc = 14,4; St = 0,18 (Tabla E.1); c_lat = 0,2:
        y = (1/0,0324)/14,4·0,13·0,6·0,2 = 0,033436 m (antes, con K = 1 y St = 0,20: 0,2083 m).
        """
        from windloads.vortex_shedding import check_vortex_shedding
        r = check_vortex_shedding(D=1.0, fn=1.0, V=5.0, m_per_m=300.0, delta_s=0.03)
        assert r.V_cr == pytest.approx(1.0 / 0.18, abs=1e-3)
        assert r.y_max_m == pytest.approx(1.0 / 0.18 ** 2 / 14.4 * 0.13 * 0.6 * 0.2, abs=1e-6)

    def test_circular_strouhal_is_0_18_and_clat_can_be_given(self):
        # Tabla E.1: St = 0,18 para secciones circulares (antes 0,20). c_lat explícito
        # (Figura E.2 para el Re real) escala la amplitud linealmente.
        from windloads.vortex_shedding import STROUHAL_NUMBERS, check_vortex_shedding, critical_velocity
        assert STROUHAL_NUMBERS["circular"] == pytest.approx(0.18)
        assert critical_velocity(1.2, 1.0) == pytest.approx(1.2 / 0.18)
        a = check_vortex_shedding(D=1.0, fn=1.0, V=5.0, m_per_m=300.0, delta_s=0.03)
        b = check_vortex_shedding(D=1.0, fn=1.0, V=5.0, m_per_m=300.0, delta_s=0.03, clat=0.7)
        assert b.y_max_m / a.y_max_m == pytest.approx(0.7 / 0.2, rel=1e-4)

    def test_rectangular_lateral_force_coefficient_1_1(self):
        from windloads.vortex_shedding import check_vortex_shedding
        r = check_vortex_shedding(D=1.0, fn=1.0, V=5.0, m_per_m=300.0, delta_s=0.03,
                                  St=0.12, section="rectangular")
        assert r.y_max_m == pytest.approx(1.0 / 0.12 ** 2 / 14.4 * 0.13 * 0.6 * 1.1, abs=1e-6)


# --------------------------------------------------------------- Tablas 7.3a / 7.4
class TestEC1PitchedRoofTables:
    def test_duopitch_theta_0(self):
        from windloads.components import ec1_gable_cpe
        assert ec1_gable_cpe(15.0, "F", 1.0) == pytest.approx(-2.0)    # cpe,1
        assert ec1_gable_cpe(15.0, "F", 10.0) == pytest.approx(-0.9)   # cpe,10 (antes -1,3)
        assert ec1_gable_cpe(30.0, "J", 10.0) == pytest.approx(-0.5)   # antes -1,0
        assert ec1_gable_cpe(30.0, "H", 10.0, case="pos") == pytest.approx(0.4)
        # 22,5°: F cpe,10 = -0,9 + 0,5·(-0,5 + 0,9) = -0,7
        assert ec1_gable_cpe(22.5, "F", 10.0) == pytest.approx(-0.7)

    def test_duopitch_theta_90(self):
        from windloads.components import ec1_gable_cpe
        assert ec1_gable_cpe(15.0, "F", 10.0, wind_dir=90) == pytest.approx(-1.3)
        assert ec1_gable_cpe(30.0, "G", 1.0, wind_dir=90) == pytest.approx(-2.0)
        with pytest.raises(ValueError):
            ec1_gable_cpe(30.0, "J", 1.0, wind_dir=90)

    def test_monopitch_theta_0_and_180(self):
        from windloads.components import ec1_monopitch_cpe
        assert ec1_monopitch_cpe(15.0, "F", 10.0) == pytest.approx(-0.9)
        assert ec1_monopitch_cpe(15.0, "F", 10.0, wind_dir=180) == pytest.approx(-2.5)
        # A = 10^0,5 m²: cpe = cpe,1 − (cpe,1 − cpe,10)·0,5 = -2,8 + 0,3·0,5 = -2,65
        assert ec1_monopitch_cpe(15.0, "F", 10 ** 0.5, wind_dir=180) == pytest.approx(-2.65)


# --------------------------------------------------------------- report_ec1
def test_report_ec1_uses_zmin_of_the_category():
    """H = 6 m, categoría II (z_min = 2 m): q_p(6) y no q_p(10)."""
    import re
    from windloads.report_ec1 import EC1ReportInput, generar_reporte_ec1
    md = generar_reporte_ec1(EC1ReportInput(vb_0_m_s=26.0, H_m=6.0, B_m=10.0,
                                            L_m=10.0, terrain_category=2))
    qp_md = float(re.search(r"q_p\(z\)\s*=\s*([\d\.]+)\s*Pa", md).group(1))
    assert qp_md == pytest.approx(_qp_ec1(6.0, 26.0, 0.05, 2.0), abs=0.01)
    assert qp_md < _qp_ec1(10.0, 26.0, 0.05, 2.0) - 50.0


# --------------------------------------------------------------- export
def test_from_envelope_backs_out_the_net_pressure_with_the_width():
    from windloads.export import from_envelope
    sf = [StoryWindForce(story=1, z_bot=0.0, z_top=3.0, z_mid=1.5, qp_or_qz=800.0, Fx=30.0)]
    # 30 kN / (20 m · 3 m) = 0,5 kPa = 500 Pa
    assert from_envelope(sf, "WX+", "+X", tributary_widths_m=20.0).pressures_by_level[0].pressure_Pa \
        == pytest.approx(500.0)
    assert from_envelope(sf, "WX+", "+X").pressures_by_level[0].pressure_Pa == pytest.approx(800.0)


def test_export_service_refuses_to_invent_pressures():
    from windloads.services.export import ExportInput, export_to
    with pytest.raises(ValueError):
        export_to(ExportInput(target="json", height_m=30.0, width_m=20.0, n_stories=5))


# --------------------------------------------------------------- DXF
def test_dxf_pressure_arrows_point_into_the_building(tmp_path):
    ezdxf = pytest.importorskip("ezdxf")
    from windloads.integration.dxf_wind_plan import (
        WindPlanInput, WindZoneLoad, build_wind_plan_dxf)
    inp = WindPlanInput(plant_m=[(0, 0), (20, 0), (20, 10), (0, 10)], qz_kPa=1.0,
                        zone_loads=[WindZoneLoad("windward", 0.8, 0.8),
                                    WindZoneLoad("leeward", -0.5, -0.5)])
    doc = build_wind_plan_dxf(inp, tmp_path / "plan.dxf")
    msp = ezdxf.readfile(tmp_path / "plan.dxf").modelspace()

    def longest(layer):
        lines = list(msp.query(f'LINE[layer=="{layer}"]'))
        return max(lines, key=lambda e: (e.dxf.end - e.dxf.start).magnitude)

    press = longest("W-PRESS")   # barlovento en x = 0: nace fuera (x < 0) y acaba en la cara
    assert press.dxf.start.x < 0.0 and press.dxf.end.x == pytest.approx(0.0)
    suct = longest("W-SUCT")     # sotavento en x = 20: nace en la cara y sale (x > 20)
    assert suct.dxf.start.x == pytest.approx(20.0) and suct.dxf.end.x > 20.0
    assert doc is not None


# --------------------------------------------------------------- NSR-10
class TestNSR10:
    def test_importance_factor_multiplies_qz_not_V(self):
        # ASCE 7-05 Ec. 6-15 (adoptada por la NSR-10): qz ∝ I, no I².
        from windloads import NSR10WindLoad
        q1 = NSR10WindLoad(27.0, "B", building_height=20.0, importance_factor=1.0).qh
        q2 = NSR10WindLoad(27.0, "B", building_height=20.0, importance_factor=1.15).qh
        assert q2 / q1 == pytest.approx(1.15, rel=1e-12)   # antes 1,3225

    def test_zone_5_is_130_kmh(self):
        # Arroyo y Ramos (2015): región 5 = 36 m/s (130 km/h); antes 39 m/s.
        from windloads.codes.nsr10_b6 import nsr10_basic_wind_speed
        assert nsr10_basic_wind_speed(zone=5) == pytest.approx(36.0)
        assert nsr10_basic_wind_speed(zone=1) == pytest.approx(17.0)


# --------------------------------------------------------------- servicios
class TestServicesDelegateToTheEngines:
    def test_ec1_service_equals_terrain_profile(self):
        from windloads.services.ec1 import EC1Input, compute_ec1
        r = compute_ec1(EC1Input(vb=26.0, height=20.0, width=20.0, depth=10.0,
                                 terrain_category=3, c_dir=0.9))
        tp = TerrainProfile("EC1", "III")
        assert r.qp_at_height == pytest.approx(tp.ec1_peak_velocity_pressure(20.0, 23.4) / 1000)
        assert r.vm_at_height == pytest.approx(tp.ec1_mean_wind_velocity(20.0, 23.4))
        assert r.cp_leeward == pytest.approx(-0.55)          # h/d = 2

    def test_asce7_service_net_pressure_cancels_internal(self):
        """V = 115 mph, h = 100 ft, B = 60, L = 120 (L/B = 2 -> Cp_l = -0,3), exposición C.

        Kz = 2,01·(100/900)^(2/9,5); q_h = 0,00256·Kz·0,85·115²;
        neta = q_h·0,85·(0,8 + 0,3) (antes: 0,36·q_h menos y Cp_l = -0,5).
        """
        from windloads.services.asce7 import ASCE7Input, compute_asce7
        r = compute_asce7(ASCE7Input(V=115.0, height_ft=100.0, width_ft=60.0,
                                     depth_ft=120.0, exposure="C"))
        Kz = 2.01 * (100.0 / 900.0) ** (2.0 / 9.5)
        qh = 0.00256 * Kz * 0.85 * 115.0 ** 2
        assert r.qh_psf == pytest.approx(qh)
        assert r.Cp_leeward == pytest.approx(-0.3)
        assert r.summary["net_psf"] == pytest.approx(round(qh * 0.85 * 1.1, 2))

    def test_nsr10_service_uses_module_speed_and_qz(self):
        from windloads.codes.nsr10_b6 import NSR10WindLoad
        from windloads.services.nsr10 import NSR10Input, compute_nsr10
        r = compute_nsr10(NSR10Input(city="Bogotá", height_m=30.0, width_m=20.0, depth_m=40.0))
        assert r.V_basic_kmh == pytest.approx(27.0 * 3.6)
        wl = NSR10WindLoad("bogota", "B", building_height=30.0, width=20.0, depth=40.0)
        assert r.qz_kPa == pytest.approx(wl.qh / 1000.0)
        assert r.p_net_kPa == pytest.approx(wl.qh / 1000.0 * 0.85 * (0.8 + 0.3))

    def test_cc_service_follows_the_area(self):
        from windloads.services.components import CCInput, compute_cc
        small = compute_cc(CCInput(zone=4, area_m2=0.5))
        large = compute_cc(CCInput(zone=4, area_m2=50.0))
        assert small.GCp_negative == pytest.approx(-1.1)    # Fig. 30.3-1, A <= 10 ft²
        assert large.GCp_negative == pytest.approx(-0.8)    # A >= 500 ft²


# --------------------------------------------------------------- versión
def test_single_version_everywhere():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__ == "1.2.0"
    pytest.importorskip("fastapi")
    from windloads.api.app import app
    assert app.version == __version__
