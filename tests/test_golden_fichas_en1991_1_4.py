"""Golden tests EN 1991-1-4 (viento) anclados a fichas del master
(``_EXTRACCION_DOCUMENTOS/fichas``).

Fichas ancla
------------
* **W00483 — CTE DB SE-AE** (Documento Basico Acciones en la Edificacion):
  presion dinamica basica por zonas qb(A/B/C) = 0.42/0.45/0.52 kN/m2,
  tabla de coeficiente de exposicion ce(z) y ejemplo resuelto
  ``pw = ce x qb = 2.0 x 0.45 = 0.90 kN/m2`` (zona B, z=10 m, "rugosidad IV").
* **W01630 — IAP-11** (RD 1359/2011), Cap. 5 Viento: cadena
  ``qb = 0.5*rho*vb^2`` con rho=1.25 kg/m3 y ``qp(z) = ce(z)*qb``;
  mapa de Espana vb,0 en {26, 27, 29} m/s.
* **W00249 — Ejemplos Diamonds acero**: Ej.1 con viento EN 1991-1-4
  (v0=26 m/s, terreno I) y coeficientes de presion interior
  ``c_pi = +0.2 / -0.3``.
* **W01375 — Task 5 pasarela bowstring Mataro**: ``w_y = 1.4 kN/m2``
  (IAP-11 4.2) — evaluada abajo; la cadena completa NO es anclable
  (ver ``TestW01375EnvolventeIAP11``).

Equivalencia normativa usada
----------------------------
El grado de aspereza III del CTE (Anejo D.2: k=0.19, L=0.05 m, Z=2 m) es
identico a la categoria de terreno II de EN 1991-1-4 (kr=0.19, z0=0.05 m,
zmin=2 m), y el grado IV del CTE (k=0.22, L=0.3 m, Z=5 m) es el homologo de
la categoria III de EN 1991-1-4 (z0=0.3 m, zmin=5 m; kr=0.19*(0.3/0.05)^0.07
= 0.21539 frente al k=0.22 redondeado del CTE). ce(z) del CTE =
F*(F + 7*k) con F = k*ln(max(z,Z)/L) es exactamente
(1 + 7*Iv)*cr^2 = qp/qb de EN 1991-1-4 con co=kI=1.

REGLA DE ORO de la campana: no fiarse de los numeros impresos. Todos los
oraculos de este fichero se recalcularon a mano (formulas EN 1991-1-4
Ec. 4.4, 4.5, 4.7, 4.8, 4.10 transcritas de la norma, sin llamar a
``windloads`` para generar el oraculo) antes de anclarlos.

ERRATAS DOCUMENTADAS (no ancladas al valor impreso)
---------------------------------------------------
1. **W00483, tabla ce "rugosidad IV"** (z=5:1.6, 10:2.0, 15:2.3, 20:2.5,
   30:2.9): los valores recalculados con CTE Anejo D.2 para grado IV son
   1.34, 1.78, 2.07, 2.28, 2.59 — la fila impresa coincide en realidad con
   la tabla 3.4 del CTE para grado III en z=3, 6, 9, 12, 24 m (1.6, 2.0,
   2.3, 2.5, 2.9): extraccion con grado y alturas desplazados.
2. **W00483, ejemplo pw = 2.0 x 0.45 = 0.90 kN/m2**: hereda la errata
   anterior (ce(10) correcto de grado IV es 1.78, no 2.0). Recalculado:
   CTE analitico 0.456*1.783 = 0.81 kN/m2; motor EN 1991-1-4 terreno III
   qp(10) = 778.75 Pa = 0.78 kN/m2. Se ancla el recalculado (test
   ``test_errata_pw_090_no_reproducible``).
3. **W00483, qb zonas B y C**: impresos 0.45 y 0.52 kN/m2; recalculados
   0.5*1.25*27^2 = 455.625 Pa y 0.5*1.25*29^2 = 525.625 Pa (0.456/0.526
   kN/m2). El propio CTE redondea hacia abajo (-1.2%/-1.1%). Se ancla el
   recalculado exacto.

DISCREPANCIA DE DATOS (documentada, NO anclada, NO corregida)
-------------------------------------------------------------
``windloads/vb_atlas.py`` asigna Barcelona = 27 m/s con nota "Zona B" y
Cadiz = 26 m/s; la ficha W00483 describe Zona B = costa atlantica (27) y
Zona C = costa mediterranea (29), lo que situaria Barcelona (costa
mediterranea) en Zona C = 29 m/s y Cadiz (costa atlantica) en Zona B = 27.
Sin el mapa oficial (CTE Figura D.1) no es adjudicable desde las fichas;
se deja documentado y solo se anclan Madrid (Zona A, sin conflicto) y el
conjunto de valores {26, 27, 29}.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from windloads.terrain import TerrainProfile
from windloads.pressure import ec1_cpe_walls, WindPressure
from windloads.codes.ec1_1_4 import EC1WindLoad
from windloads.memos.ec1_pressure_memo import ec1_peak_pressure_memo
from windloads.vb_atlas import vb_for, list_vb


# ---------------------------------------------------------------------------
# Oraculos a mano (hard-coded; ver scratch oracle_en1991_1_4.py de la sesion)
# ---------------------------------------------------------------------------
QB_ZONA_A_Pa = 422.500    # 0.5*1.25*26^2
QB_ZONA_B_Pa = 455.625    # 0.5*1.25*27^2
QB_ZONA_C_Pa = 525.625    # 0.5*1.25*29^2

CR_II_Z10 = 1.0066803     # 0.19*ln(10/0.05)
IV_II_Z10 = 0.1887392     # 1/ln(10/0.05)
CE_II_Z10 = 2.35229       # (1+7*Iv)*cr^2

QP_Z10_VB27_TIII_Pa = 778.75    # zona B, terreno III (ejemplo W00483 recalc)
QP_Z10_VB27_T0_Pa = 1359.83     # cota inferior envolvente W01375
QP_Z10_VB29_TI_Pa = 1455.20     # cota superior envolvente W01375


class TestQbZonasVientoW00483W01630:
    """qb = 0.5*rho*vb^2 — EN 1991-1-4 Ec. 4.10 (rho=1.25 kg/m3).

    Ancla W01630 (IAP-11 Cap.5: "qb = 0.5*1.25*vb^2 [N/m2]") y los valores
    zonales de W00483 (CTE DB SE-AE fig. 3.1): zona A 26 m/s -> 0.42 kN/m2,
    zona B 27 m/s -> 0.45, zona C 29 m/s -> 0.52. Oraculo a mano:
      0.625*676 = 422.5 Pa; 0.625*729 = 455.625 Pa; 0.625*841 = 525.625 Pa.
    """

    def test_qb_zona_A_26ms(self):
        _, r = ec1_peak_pressure_memo(v_b=26.0, c_e=1.0)
        assert r.q_b_Pa == pytest.approx(QB_ZONA_A_Pa, rel=1e-9)
        # Valor impreso en W00483: 0.42 kN/m2 (coincide al centesimo)
        assert abs(r.q_b_Pa / 1000.0 - 0.42) < 0.005

    def test_qb_zona_B_27ms_recalculado(self):
        _, r = ec1_peak_pressure_memo(v_b=27.0, c_e=1.0)
        assert r.q_b_Pa == pytest.approx(QB_ZONA_B_Pa, rel=1e-9)
        # W00483 imprime 0.45 kN/m2: redondeo del CTE hacia abajo (-1.2%).
        # Se ancla el recalculado 0.4556; el impreso queda a 0.0056 kN/m2.
        assert abs(r.q_b_Pa / 1000.0 - 0.45) < 0.01

    def test_qb_zona_C_29ms_recalculado(self):
        _, r = ec1_peak_pressure_memo(v_b=29.0, c_e=1.0)
        assert r.q_b_Pa == pytest.approx(QB_ZONA_C_Pa, rel=1e-9)
        # W00483 imprime 0.52 kN/m2 (recalc 0.5256; redondeo CTE -1.1%).
        assert abs(r.q_b_Pa / 1000.0 - 0.52) < 0.01

    def test_qp_igual_ce_por_qb(self):
        """qp(z) = ce(z)*qb — W01630 (IAP-11 Cap.5) / EN 1991-1-4 4.5(1).

        Oraculo a mano: 2.35229 * 455.625 = 1071.76 Pa.
        """
        _, r = ec1_peak_pressure_memo(v_b=27.0, c_e=CE_II_Z10)
        assert r.q_p_Pa == pytest.approx(1071.76, abs=0.05)


class TestExposicionTerrenoIIvsCTE:
    """Perfil de exposicion EN 1991-1-4 4.3/4.4 en terreno II, z=10 m.

    Oraculo a mano (Ec. 4.4/4.5/4.7):
      kr = 0.19*(0.05/0.05)^0.07 = 0.19
      cr(10) = 0.19*ln(200) = 1.00668
      Iv(10) = 1/ln(200) = 0.18874
      ce(10) = (1+7*0.18874)*1.00668^2 = 2.35229
    Oraculo cruzado independiente: CTE tabla 3.4 (W00483) grado III
    (equivalente exacto del terreno II EN): z=9 -> 2.3, z=12 -> 2.5;
    interpolado z=10 -> 2.367. Diferencia 0.6% (redondeo a un decimal
    de la tabla del CTE).
    """

    def setup_method(self):
        self.tp = TerrainProfile("EC1", "II")

    def test_cr_terreno_II_z10(self):
        assert self.tp.ec1_roughness_factor(10.0) == pytest.approx(
            CR_II_Z10, abs=1e-4)

    def test_Iv_terreno_II_z10(self):
        assert self.tp.ec1_turbulence_intensity(10.0) == pytest.approx(
            IV_II_Z10, abs=1e-4)

    def test_ce_terreno_II_z10_contra_tabla_CTE(self):
        qb = 0.5 * 1.25 * 27.0 ** 2
        ce = self.tp.ec1_peak_velocity_pressure(10.0, 27.0) / qb
        assert ce == pytest.approx(CE_II_Z10, abs=5e-4)
        # Oraculo cruzado tabla 3.4 CTE grado III interpolada en z=10
        assert abs(ce - 2.367) < 0.05


class TestEjemploW00483Recalculado:
    """Ejemplo resuelto de W00483: pw = ce*qb, zona B (vb=27), z=10 m.

    La ficha imprime pw = 2.0 x 0.45 = 0.90 kN/m2 con "rugosidad IV".
    ERRATA documentada (cabecera del modulo): ce=2.0 no corresponde al
    grado IV en z=10 (recalculado CTE D.2: 1.783; tabla impresa desplazada
    desde el grado III). Se ancla el RECALCULADO con el motor EN 1991-1-4
    en terreno III (homologo del grado IV CTE):

      kr = 0.19*(0.3/0.05)^0.07 = 0.21539
      cr(10) = 0.21539*ln(10/0.3) = 0.75528
      vm = 0.75528*27 = 20.392 m/s
      Iv = 1/ln(10/0.3) = 0.28518
      qp = (1+7*0.28518)*0.5*1.25*20.392^2 = 778.75 Pa = 0.779 kN/m2
    """

    def setup_method(self):
        self.wl = EC1WindLoad(vb=27.0, terrain_cat="III",
                              building_height=10.0, width=40.0, depth=40.0)

    def test_qp_z10_zona_B_terreno_III_recalculado(self):
        assert self.wl.qp_at(10.0) == pytest.approx(
            QP_Z10_VB27_TIII_Pa, abs=0.05)

    def test_errata_pw_090_no_reproducible(self):
        """El 0.90 kN/m2 impreso NO se reproduce con la cadena correcta.

        Guardia de la errata: si algun dia qp(10) diera 0.90 kN/m2, la
        implementacion habria dejado de seguir EN 1991-1-4 Ec. 4.8.
        Recalculados honestos: 0.78 (EN terreno III) / 0.81 (CTE D.2
        grado IV con k=0.22). Diferencia contra el impreso: -13%/-10%.
        """
        qp_kPa = self.wl.qp_at(10.0) / 1000.0
        assert abs(qp_kPa - 0.90) > 0.10
        assert qp_kPa == pytest.approx(0.77875, abs=5e-4)


class TestCadenaCompletaFachada:
    """Cadena completa vb -> qb -> qp(z) -> presion de fachada con cpe.

    Edificio h=10 m, d=40 m (h/d=0.25), zona B (vb=27 m/s), terreno III
    (grado IV CTE, W00483). cpe,10 de EN 1991-1-4 Tabla 7.1 con h/d<=0.25:
    D=+0.7, E=-0.3, A=-1.2, B=-0.8, C=-0.5. cpi = +0.2/-0.3 (EN 1991-1-4
    7.2.9(6) Nota 2, confirmado en ficha W00249: "c_pi=+-0.3/0.2").

    Oraculo a mano con qp = 778.75 Pa (ver TestEjemploW00483Recalculado):
      w_net = qp*(cpe - cpi)
      zona D: (0.7-0.2)*qp = +0.389 kPa ; (0.7+0.3)*qp = +0.779 kPa
      zona E: (-0.3-0.2)*qp = -0.389 kPa ; (-0.3+0.3)*qp = 0.000 kPa
      zona A: (-1.2-0.2)*qp = -1.090 kPa ; (-1.2+0.3)*qp = -0.701 kPa
      (hasta 1.2.0 este golden fijaba A = -1.0, que no es el valor de la
      Tabla 7.1: cpe,10 de la zona A es -1.2 para todo h/d)
      zona B: -0.779 / -0.389 kPa
      zona C: -0.545 / -0.156 kPa
    """

    ORACULO_kPa = {
        # zona: (cpe, w_net con cpi=+0.2, w_net con cpi=-0.3)
        "D": (+0.7, +0.389, +0.779),
        "E": (-0.3, -0.389, 0.000),
        "A": (-1.2, -1.090, -0.701),
        "B": (-0.8, -0.779, -0.389),
        "C": (-0.5, -0.545, -0.156),
    }

    def test_cpe_tabla_7_1_hd_025(self):
        cpe = ec1_cpe_walls(h=10.0, d=40.0)
        for zona, (cpe_esp, _, _) in self.ORACULO_kPa.items():
            assert cpe[zona] == pytest.approx(cpe_esp, abs=0.01), zona

    def test_fachada_completa_todas_las_zonas(self):
        wl = EC1WindLoad(vb=27.0, terrain_cat="III",
                         building_height=10.0, width=40.0, depth=40.0)
        fp = wl.facade_pressures()
        for zona, (cpe_esp, w_pos, w_neg) in self.ORACULO_kPa.items():
            assert fp[zona]["cpe"] == pytest.approx(cpe_esp, abs=0.01), zona
            assert fp[zona]["w_net_pos_kPa"] == pytest.approx(
                w_pos, abs=0.002), zona
            assert fp[zona]["w_net_neg_kPa"] == pytest.approx(
                w_neg, abs=0.002), zona

    def test_w_net_barlovento_presion_maxima(self):
        """w_net,D con cpi=-0.3 = qp*(0.7+0.3) = qp — oraculo 778.75 Pa."""
        wp = WindPressure("EC1", "closed")
        q = QP_Z10_VB27_TIII_Pa
        w = wp.ec1_net_pressure(qp=q, cpe=0.7, positive_internal=False)
        assert w == pytest.approx(778.75, abs=0.05)

    def test_cpi_w00249(self):
        """cpi = +0.2 / -0.3 (W00249 Ej.1; EN 1991-1-4 7.2.9(6) Nota 2).

        Oraculo a mano con qp=1000 Pa, cpe=+0.8:
          cpi=+0.2 -> w = 1000*(0.8-0.2) = 600 Pa
          cpi=-0.3 -> w = 1000*(0.8+0.3) = 1100 Pa
        """
        wp = WindPressure("EC1", "closed")
        assert wp.ec1_net_pressure(1000.0, 0.8, True) == pytest.approx(600.0)
        assert wp.ec1_net_pressure(1000.0, 0.8, False) == pytest.approx(1100.0)


class TestW01375EnvolventeIAP11:
    """Evaluacion del w_y = 1.4 kN/m2 de la ficha W01375 (pasarela Mataro).

    La ficha cita "w_y=1.4 kN/m2 (IAP-11 4.2)" SIN los parametros de la
    cadena (zona de viento, tipo de entorno, altura de referencia, cf), y
    sus derivados impresos no cierran con sus propios datos:
      * lineales 0.36 kN/m (tablero) y 0.15 kN/m (arco) implican franjas
        expuestas de 0.257 m y 0.107 m — frente a canto HEB600 = 0.6 m y
        diametro CHS = 0.508 m (factores 2.3x-4.7x sin justificar);
      * F_Y = +-15.20 kN no se recupera con ninguna combinacion de las
        longitudes del modelo (0.36*47.5 + 0.15*50.7 = 24.7 kN != 15.2).
    => INSATISFACIBLE como golden de cadena completa.

    Lo que SI es anclable: el valor 1.4 kN/m2 esta dentro de la envolvente
    de qp(10 m) que produce la cadena EN 1991-1-4/IAP-11 con los dos
    escenarios plausibles del emplazamiento (Mataro, frente maritimo):
      cota inferior: vb=27 (zona B), terreno 0 -> qp = 1359.83 Pa
      cota superior: vb=29 (zona C), terreno I -> qp = 1455.20 Pa
    Oraculos a mano:
      terreno 0: kr=0.19*(0.003/0.05)^0.07=0.15604; cr=0.15604*ln(3333.3)
        =1.26578; Iv=1/8.11173=0.12328; qp=(1.86295)*0.625*(34.176)^2
        = 1359.83 Pa
      terreno I: kr=0.19*(0.01/0.05)^0.07=0.16976; cr=0.16976*ln(1000)
        =1.17260; Iv=1/6.90776=0.14477; qp=(2.01336)*0.625*(34.005)^2
        = 1455.20 Pa
    """

    def test_qp_cota_inferior_zona_B_terreno_0(self):
        tp = TerrainProfile("EC1", "0")
        qp = tp.ec1_peak_velocity_pressure(10.0, 27.0)
        assert qp == pytest.approx(QP_Z10_VB27_T0_Pa, abs=0.1)

    def test_qp_cota_superior_zona_C_terreno_I(self):
        tp = TerrainProfile("EC1", "I")
        qp = tp.ec1_peak_velocity_pressure(10.0, 29.0)
        assert qp == pytest.approx(QP_Z10_VB29_TI_Pa, abs=0.1)

    def test_wy_ficha_dentro_de_envolvente(self):
        """1.360 <= 1.4 <= 1.455 kN/m2 — coherente pero indeterminado."""
        lo = TerrainProfile("EC1", "0").ec1_peak_velocity_pressure(10.0, 27.0)
        hi = TerrainProfile("EC1", "I").ec1_peak_velocity_pressure(10.0, 29.0)
        assert lo / 1000.0 <= 1.4 <= hi / 1000.0


class TestVbAtlasEspanaW00483:
    """Atlas vb Espana contra las zonas del CTE (ficha W00483).

    Solo se anclan hechos sin conflicto (ver DISCREPANCIA en cabecera):
    Madrid = zona A interior = 26 m/s, y que todo el atlas ES toma valores
    del conjunto zonal {26, 27, 29} m/s (fig. 3.1 CTE / mapa IAP-11
    W01630 "26-29 m/s").
    """

    def test_madrid_zona_A_26ms(self):
        assert vb_for("Madrid", "ES") == pytest.approx(26.0)

    def test_atlas_ES_solo_valores_zonales_CTE(self):
        vbs = {e.Vb_m_s for e in list_vb("ES")}
        assert vbs <= {26.0, 27.0, 29.0}

    def test_zonas_consistentes_con_qb_ficha(self):
        """vb zonal <-> qb impreso en W00483 (tolerancia redondeo CTE 1.2%).

        Oraculo a mano: 0.5*1.25*vb^2 para vb en {26,27,29} =
        {422.5, 455.625, 525.625} Pa vs impresos {420, 450, 520} N/m2.
        """
        impresos = {26.0: 420.0, 27.0: 450.0, 29.0: 520.0}
        for vb, qb_ficha in impresos.items():
            qb_recalc = 0.5 * 1.25 * vb ** 2
            assert abs(qb_recalc - qb_ficha) / qb_recalc < 0.013
