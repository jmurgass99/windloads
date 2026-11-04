# windloads

**Español** · [English](README.en.md)

Cargas de viento sobre edificios en Python, con EN 1991-1-4, ASCE 7 y NSR-10 B.6.

[![CI](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- Presión de velocidad pico q_p(z) de EN 1991-1-4 por categoría de terreno, con orografía (Anexo A.3), y q_z de ASCE 7.
- Coeficientes de presión de muros y cubiertas (Tablas 7.1 a 7.4) y de componentes y revestimientos de ASCE 7.
- Fuerzas por planta, cortante basal y vuelco de un edificio rectangular, y los cuatro casos de torsión de ASCE 7.
- Factor de ráfaga de Davenport, desprendimiento de torbellinos y galope (Anexo E).
- Exportación a JSON, CSV, SAP2000 (.s2k), ETABS (.e2k) y DXF; memorias de cálculo con `handcalcs`; API REST opcional.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/windloads.git
```

Extras opcionales: `api`, `memos`, `dxf`, `ui`. Dependencias base: `numpy` y `pydantic`.

## Ejemplo

Presión pico a 10 m en terreno categoría II, con v_b = 26 m/s y ρ = 1,25 kg/m³:

```python
from windloads import TerrainProfile

perfil = TerrainProfile("EC1", "II")
qp = perfil.ec1_peak_velocity_pressure(10.0, 26.0, 1.25)
print(round(qp, 1))   # 993.8 Pa
```

La carpeta [`examples/`](examples) tiene 33 scripts más; casi todos rehacen el resultado a mano con la fórmula de la norma.

## Qué no hace

- Edificios de forma no rectangular, cubiertas abovedadas o estructuras de celosía. Las tablas de cubiertas complejas, cúpulas y seguidores solares son orientativas y no salen de ninguna norma verificada.
- Análisis dinámico de edificios esbeltos: c_s·c_d vale 1 por defecto y el factor de Davenport está simplificado.
- Elegir la velocidad básica del emplazamiento: las tablas por ciudad no están contrastadas. Usa el mapa oficial y pasa la velocidad como número.
- ASCE 7-22 al pie de la letra: K_z usa las constantes de ASCE 7-16.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test,api,memos,dxf]"
pytest -q
```

`tests/test_examples.py` ejecuta todos los ejemplos. En Windows, si la consola no es UTF-8, usa `python -X utf8 examples/<nombre>.py`.

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
