# windloads

Cargas de viento multinorma: EN 1991-1-4, ASCE 7-22, NSR-10 B.6 y NCh 432. Velocidad básica por mapa y ciudad, rugosidad y topografía, presión de velocidad de pico, coeficientes de presión exterior e interior (muros, cubiertas planas, a un agua y a dos aguas, marquesinas, cubiertas complejas, seguidores solares), casos de carga MWFRS, componentes y revestimientos, factor de ráfaga de Davenport, desprendimiento de vórtices y comprobaciones aeroelásticas, generador de velocidades por periodo de retorno y exportación de fuerzas por planta a JSON, CSV, SAP2000 y ETABS.

[![CI](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Dependencias: `numpy`, `pydantic`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/windloads.git
```

Extras: `api` (REST), `ui` (Streamlit), `memos` (handcalcs), `dxf` (ezdxf), `test`.

## Inicio rápido

Edificio de 30 x 20 m y 40 m de altura con tres normas:

```python
from windloads import EC1WindLoad, ASCE7WindLoad, NSR10WindLoad

stories = [3.0] * 13 + [1.0]
ec1 = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=40, width=30, depth=20,
                  story_heights=stories, enclosure="closed")
res = ec1.compute()
print(res["qp_top_Pa"], res["Vb_kN"], res["OTM_kNm"])     # presión de pico, cortante basal, vuelco
forces = ec1.story_forces()                                 # fuerza por planta

asce = ASCE7WindLoad(V=40.0, exposure="C", building_height=40, width=30, depth=20,
                     story_heights=stories, risk_category="II", enclosure="enclosed")
nsr = NSR10WindLoad(city_or_Vb="barranquilla", terrain_cat="B", building_height=40, width=30, depth=20,
                    story_heights=stories, enclosure="cerrado")
```

Exportación a programas de análisis:

```python
from windloads import EC1WindLoad, WindLoadCase, from_envelope, to_json, to_csv, to_sap_s2k, to_etabs_e2k

ec1 = EC1WindLoad(vb=26.0, terrain_cat="II", building_height=40, width=30, depth=20,
                  story_heights=[3.0] * 13 + [1.0], enclosure="closed")
pattern = from_envelope(ec1.story_forces(), name="WX+", direction="+X")
case = WindLoadCase(name="EC1_30x20x40", code="EC1", building={"B": 30, "D": 20, "H": 40, "stories": 13},
                    patterns=[pattern], meta={"vb_ms": 26.0, "terrain": "II"})
print(to_sap_s2k(pattern)[:200])        # fragmento .s2k para SAP2000; to_etabs_e2k, to_json y to_csv análogos
```

`examples/building_30x20x40.py` ejecuta el caso completo con las tres normas, componentes y revestimientos, y escribe JSON, CSV, `.s2k` y `.e2k` en `examples/out/`. `examples/02_three_codes_same_building.py` compara cortante basal y vuelco entre normas.

## Módulos

| Módulo | Contenido |
|---|---|
| `codes/` (`ec1_1_4`, `asce7_26`, `nsr10_b6`, `nch432`), `codes_multi` | Implementación por norma y despacho multinorma |
| `terrain`, `topography`, `vb_atlas`, `vb_map`, `mri_generator` | Exposición, topografía, mapas de velocidad y periodo de retorno |
| `pressure`, `cp_catalog`, `cp_techos_complejos`, `cc_pressure`, `solar_trackers` | Presiones y coeficientes |
| `envelope`, `mwfrs_load_cases`, `components` | Envolventes y casos de carga |
| `davenport`, `vortex_shedding`, `aeroelastic`, `cfd_pre` | Dinámica del viento |
| `export`, `report_ec1`, `memos/` | Exportación, informe y memorias |
| `sap_bridge` | Envío de patrones a SAP2000 (requiere `fastsap`, opcional) |
| `api/` | REST con FastAPI |

## Validación

Tests golden con la cascada q_p de EN 1991-1-4 y fichas de la norma, ASCE 7-22, NSR-10 y NCh 432, más propiedades con hypothesis (353 tests).

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).
