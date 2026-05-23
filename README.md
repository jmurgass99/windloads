# WindLoadJm — Cargas de Viento Multi-Código

[![CI](https://github.com/jmurgass99/windloadjm/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/windloadjm/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-81.3%25-brightgreen?style=flat)](https://github.com/jmurgass99/windloadjm)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

## Objetivo
Librería Python para el cálculo automatizado de cargas de viento sobre edificios y estructuras según tres códigos normativos: **EN 1991-1-4 (Eurocódigo 1)**, **ASCE 7-22 (Capítulos 26-31)** y **NSR-10 (Título B.6)**.

Este proyecto cierra el **gap #1** de FastSAP, que en su README declara explícitamente:
> *"Sin viento (EC1-1-4 / ASCE 7-22 cap. 26-31 / NSR-10 §B.6 no implementados)"*

---

## ¿Qué va a hacer?

### 1. Perfil de Velocidad de Viento por Altura
- Cálculo de la velocidad básica del viento según zona geográfica
- Perfil de presión dinámica `qz(z)` variando con la altura
- Categorías de terreno/exposición (abierto, suburbano, urbano)
- Factor topográfico para colinas, escarpes y crestas

### 2. Presiones sobre la Envolvente (MWFRS)
- Coeficientes de presión externa `Cp` por fachada (barlovento, sotavento, laterales, cubierta)
- Presión interna `GCpi` según clasificación del edificio (abierto, parcialmente cerrado, cerrado)
- Presión neta de diseño: `p = q·G·Cp - qi·GCpi`
- Método direccional (Method 1) y método de envolvente (Method 2)

### 3. Components & Cladding (C&C)
- Presiones locales para diseño de fachadas, ventanas y paneles
- Zonas: interior, borde, esquina (Zone 4, 5 según ASCE 7)
- Áreas tributarias efectivas

### 4. Combinaciones de Carga
- Generación automática de combinaciones con factores de viento
- Integración con el sistema de `loads.py` y `cases.py` de FastSAP
- Load patterns direccionales (0°, 90°, 180°, 270° + oblicuos)

### 5. Exportación
- Generación de load patterns para SAP2000/ETABS vía FastSAP
- Tablas resumen para memorias de cálculo

---

## Estructura de Módulos Planificada

```
windloadjm/
├── __init__.py
├── terrain.py              # Categorías de terreno, perfiles de velocidad, Kz
├── pressure.py             # qz, Cp (presión/succión), GCpi (interna), factor G
├── envelope.py             # MWFRS Method 1 (directional) y Method 2 (envelope)
├── components.py           # C&C para fachadas, cubiertas, zonas de borde/esquina
├── topography.py           # Factores Kzt (colinas, escarpes)
├── codes/
│   ├── __init__.py
│   ├── ec1_1_4.py          # EN 1991-1-4: qp(z), ce(z), cpe, cpi
│   ├── asce7_26.py         # ASCE 7-22: Chapters 26-31 (Kz, Kzt, Kd, V)
│   └── nsr10_b6.py         # NSR-10: Título B.6 (velocidad de diseño Colombia)
├── export.py               # Genera load patterns para FastSAP / SAP2000 / ETABS
└── tests/
    ├── test_ec1.py
    ├── test_asce7.py
    └── test_nsr10.py
```

---

## Fuentes de Información

### Normas y Códigos
| Código | Capítulos/Secciones | Contenido |
|--------|---------------------|-----------|
| **EN 1991-1-4:2005** | §4 (velocidad), §5 (presión), §6 (fuerzas), §7 (presión en superficies) | Eurocódigo de acciones del viento |
| **ASCE 7-22** | Cap. 26 (general), 27 (MWFRS directional), 28 (MWFRS envelope), 29 (other), 30 (C&C) | Estándar americano de cargas de viento |
| **NSR-10 Título B.6** | §B.6.1 a §B.6.5 | Norma colombiana de diseño por viento |

### Repositorios de Referencia (ya descargados en `Nuevos/`)
- `pfse_starterkit-main` — Contiene ejemplos de cálculo de viento ASCE 7
- `Python_For_Civil_Engineers-main` — Scripts de presión de viento

### Documentación del Máster UPC
- Los documentos de acción sísmica (`3 Seismic Action.pdf`) contienen la estructura base de cómo se definen espectros por tipo de suelo, que es análoga a cómo el viento varía por categoría de terreno.

### Integración con FastSAP
- `fastsap/loads.py` — Sistema existente de definición de cargas
- `fastsap/cases.py` — Generador de combinaciones de carga
- `fastsap/codes/` — 30+ módulos normativos (patrón a seguir)
- `fastsap/audit_rules.py` — Se creará nueva categoría J (Wind) de auditoría

---

## Criterio de Éxito
- [ ] Calcular presión de viento sobre un edificio rectangular de N pisos según los 3 códigos
- [ ] Resultados validados contra ejemplos resueltos del ASCE 7 Commentary
- [ ] Load patterns generados e importables en SAP2000/ETABS
- [ ] Suite de tests con ≥20 casos

## Ecosystem

This project is part of the **jmurgass99 structural engineering ecosystem**:

- [fastsap](https://github.com/jmurgass99/fastsap) - orquestador SAP2000/ETABS
- [dynamicsjmpro](https://github.com/jmurgass99/dynamicsjmpro) - SaaS frontend + backend
- [dynamicsjm](https://github.com/jmurgass99/dynamicsjm) - motor dinamico
- [foundationdesignjm](https://github.com/jmurgass99/foundationdesignjm) - cimentaciones
- [windloadjm](https://github.com/jmurgass99/windloadjm) - cargas de viento
- [seismicrecordsjm](https://github.com/jmurgass99/seismicrecordsjm) - records sismicos
- [slopestabilityjm](https://github.com/jmurgass99/slopestabilityjm) - estabilidad de taludes
- [steelconnectionjm](https://github.com/jmurgass99/steelconnectionjm) - conexiones de acero
- [steeloptimizerjm](https://github.com/jmurgass99/steeloptimizerjm) - optimizacion GA
- [coldformedjm](https://github.com/jmurgass99/coldformedjm) - acero conformado en frio
- [fatiguejm](https://github.com/jmurgass99/fatiguejm) - analisis de fatiga
- [firesteeljm](https://github.com/jmurgass99/firesteeljm) - analisis termico al fuego
- [dxfstructuraljm](https://github.com/jmurgass99/dxfstructuraljm) - generacion DXF

## Plano DXF de cargas de viento (Grupo G — IDEAS_20)

Genera un plano con el contorno del edificio, flechas q·Cp por cara y
cuadro/cajetín. Requiere `ezdxf` (`pip install windloadjm[dxf]`).

```python
from windloadjm.integration.dxf_wind_plan import from_wind_result, build_wind_plan_dxf

plant = [(0, 0), (20, 0), (20, 12), (0, 12)]   # planta 20×12 m
inp = from_wind_result({"qz_kPa": 1.05}, plant,
                      project="Edif. JM", code="EC1-1-4")
build_wind_plan_dxf(inp, "planta_viento.dxf")
```
