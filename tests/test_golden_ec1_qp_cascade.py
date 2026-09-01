"""Golden EN 1991-1-4 — cascada completa c_r → v_m → I_v → q_p.

Oráculo: el TEXTO DE LA NORMA (EN 1991-1-4:2005+A1:2010), no fichas del máster
ni la ejecución de ``windloadjm``. Toda la cadena se deriva a mano abajo y los
valores literales resultantes son los que se asertan (ningún assert re-deriva
la fórmula con constantes del propio módulo bajo prueba).

Artículos citados
-----------------
* §4.3.2 (Ec. 4.4 y 4.5): c_r(z) = k_r·ln(z/z0) para z_min ≤ z ≤ z_max, con
  k_r = 0.19·(z0/z0,II)^0.07 y z0,II = 0.05 m. Tabla 4.1 da z0/z_min por
  categoría de terreno.
* §4.3.1 (Ec. 4.3): v_m(z) = c_r(z)·c_o(z)·v_b.
* §4.3.3: c_o(z) = 1.0 en terreno sin orografía (valor por defecto).
* §4.4 (Ec. 4.7): I_v(z) = σ_v/v_m = k_I/(c_o(z)·ln(z/z0)), con k_I = 1.0
  (valor recomendado de la norma).
* §4.5 (Ec. 4.8): q_p(z) = [1 + 7·I_v(z)]·½·ρ·v_m²(z), con ρ = 1.25 kg/m³
  (valor recomendado; §4.5 (1) Nota 2).
* §4.5 (Ec. 4.9) y Figura 4.2: c_e(z) = q_p(z)/q_b con q_b = ½·ρ·v_b².

CASO A — terreno II, z = 10 m, v_b = 26 m/s (derivación a mano)
---------------------------------------------------------------
Terreno II (Tabla 4.1): z0 = 0.05 m, z_min = 2 m; z0,II = 0.05 m.

1. k_r = 0.19·(0.05/0.05)^0.07 = 0.19·1 = **0.19**                     (§4.3.2)
2. ln(z/z0) = ln(10/0.05) = ln(200) = 5.2983174
   c_r(10)  = 0.19 · 5.2983174 = **1.0066803**                         (Ec. 4.4)
3. v_m(10)  = 1.0066803 · 1.0 · 26 = **26.173688 m/s**                 (Ec. 4.3)
4. I_v(10)  = 1.0/(1.0 · 5.2983174) = **0.1887392**                    (Ec. 4.7)
5. 1 + 7·I_v = 1 + 1.3211741 = 2.3211741
   ½·ρ·v_m² = 0.5 · 1.25 · 26.173688² = 0.625 · 685.06192 = 428.16370 Pa
   q_p(10)  = 2.3211741 · 428.16370 = **993.84 Pa** (0.99384 kN/m²)    (Ec. 4.8)
6. Factor de exposición (magnitud con nombre propio en la norma):
   q_b = ½·ρ·v_b² = 0.5·1.25·26² = 422.5 Pa
   c_e(10) = 993.84/422.5 = **2.3523**                                 (Ec. 4.9)

   HONESTIDAD: c_e NO es un anclaje independiente. c_e = q_p/q_b es
   algebraicamente idéntico a (1+7·I_v)·c_r², la misma expresión que evalúa el
   módulo; dividir por q_b no aporta información externa. La comparación con la
   Figura 4.2 (que para terreno II y z=10 m se recuerda en ≈2.35) queda como
   CROSS-CHECK GRÁFICO NO VERIFICADO: no se dispuso de un ejemplar de
   EN 1991-1-4 en esta sesión. La única corroboración externa realmente
   disponible en el repo es la equivalencia CTE↔EN ya documentada en
   ``tests/test_golden_fichas_en1991_1_4.py``.

CASO B — puntos que DISCRIMINAN (el caso A casi no lo hace)
-----------------------------------------------------------
En terreno II a z=10 m resulta c_r ≈ 1.007, así que una implementación que
ignorase c_r por completo (v_m = v_b) erraría solo un 0.7 %. Dos puntos extra,
también derivados a mano, cierran esa puerta:

* Terreno II, z = 30 m:  c_r = 0.19·ln(30/0.05) = 0.19·6.3969303
  = **1.2154166**  → discrimina la dependencia logarítmica con z.
* Terreno III (Tabla 4.1: z0 = 0.3 m), z = 10 m:
  k_r = 0.19·(0.3/0.05)^0.07 = 0.19·1.1336281 = **0.2153893**
  c_r = 0.2153893·ln(10/0.3) = 0.2153893·3.5065579 = **0.7552752**
  → discrimina el exponente 0.07 de k_r (con k_r fijo a 0.19 daría 0.6662).

NOTA — todos los valores anteriores se derivaron a mano ANTES de ejecutar el
código y coincidieron; no hay caracterización en este fichero.
"""
import math

import pytest

from windloadjm.terrain import TerrainProfile


RHO_EN = 1.25   # kg/m³ — valor recomendado EN 1991-1-4 §4.5
VB = 26.0       # m/s
Z = 10.0        # m


@pytest.fixture
def terreno_II() -> TerrainProfile:
    return TerrainProfile("EC1", "II")


def test_kr_y_cr_terreno_II_z10(terreno_II):
    """k_r = 0.19 y c_r(10) = 1.0066803 (EN 1991-1-4 §4.3.2, Ec. 4.4)."""
    # k_r no se expone; se comprueba vía c_r/ln(z/z0), que con z0=0.05 aísla k_r.
    cr = terreno_II.ec1_roughness_factor(Z)
    assert cr == pytest.approx(1.0066803, abs=5e-7)
    assert cr / math.log(200.0) == pytest.approx(0.19, abs=1e-9)


def test_co_por_defecto_es_1(terreno_II):
    """c_o(z) = 1.0 sin orografía (EN 1991-1-4 §4.3.3)."""
    assert terreno_II.ec1_orography_factor() == 1.0


def test_vm_terreno_II_z10(terreno_II):
    """v_m(10) = c_r·c_o·v_b = 26.173688 m/s (EN 1991-1-4 §4.3.1, Ec. 4.3)."""
    assert terreno_II.ec1_mean_wind_velocity(Z, VB) == pytest.approx(
        26.173688, abs=5e-6
    )


def test_Iv_terreno_II_z10(terreno_II):
    """I_v(10) = k_I/(c_o·ln(z/z0)) = 0.1887392 con k_I = 1.0 (§4.4, Ec. 4.7)."""
    assert terreno_II.ec1_turbulence_intensity(Z) == pytest.approx(
        0.1887392, abs=5e-7
    )


def test_qp_terreno_II_z10_golden(terreno_II):
    """q_p(10) = [1+7·I_v]·½·ρ·v_m² = 993.84 Pa (§4.5, Ec. 4.8), ρ=1.25."""
    qp = terreno_II.ec1_peak_velocity_pressure(Z, VB, rho=RHO_EN)
    assert qp == pytest.approx(993.84, abs=0.01)
    # ρ por defecto de la implementación = valor recomendado EN (1.25 kg/m³).
    assert terreno_II.ec1_peak_velocity_pressure(Z, VB) == pytest.approx(
        993.84, abs=0.01
    )


def test_ce_z10_factor_de_exposicion(terreno_II):
    """c_e(10) = q_p/q_b = 2.3523 (EN 1991-1-4 §4.5, Ec. 4.9).

    NO es un anclaje independiente: c_e = (1+7·I_v)·c_r² es la misma expresión
    del módulo dividida por q_b. La segunda aserción (≈2.35) es un cross-check
    contra la Figura 4.2 recordada, SIN verificar contra el texto de la norma.
    """
    qb = 0.5 * RHO_EN * VB**2
    assert qb == pytest.approx(422.5, abs=1e-9)
    ce = terreno_II.ec1_peak_velocity_pressure(Z, VB, rho=RHO_EN) / qb
    assert ce == pytest.approx(2.3523, abs=5e-5)   # valor exacto derivado a mano
    assert ce == pytest.approx(2.35, abs=0.05)     # cross-check Fig. 4.2 (sin verificar)


def test_cr_terreno_II_z30_discrimina_dependencia_en_z(terreno_II):
    """c_r(30) = 0.19·ln(600) = 1.2154166 (§4.3.2, Ec. 4.4)."""
    assert terreno_II.ec1_roughness_factor(30.0) == pytest.approx(
        1.2154166, abs=5e-7
    )


def test_kr_terreno_III_discrimina_exponente_007():
    """Terreno III: k_r = 0.19·(0.3/0.05)^0.07 = 0.2153893, c_r(10) = 0.7552752.

    Con k_r fijado erróneamente a 0.19 se obtendría 0.6662 (−12 %), así que
    este punto sí discrimina el exponente 0.07 de la Ec. 4.5 (§4.3.2).
    """
    tp = TerrainProfile("EC1", "III")
    cr = tp.ec1_roughness_factor(10.0)
    assert cr == pytest.approx(0.7552752, abs=5e-7)
    assert cr / math.log(10.0 / 0.3) == pytest.approx(0.2153893, abs=5e-7)
