# WindLoads — Testing Guide

## Filosofía

Código matemático puro debería ser muy testeable. Gate inicial **75%**
(más alto que otros satélites). Property-based testing para invariantes
físicas (qp positivo, qz monotónico con V, etc.).

## Markers

| Marker | Descripción |
|---|---|
| `unit` | Test rápido sin deps externas (<100ms) |
| `integration` | Requiere stack completo |
| `slow` | Duración > 5s |
| `property` | Property-based con hypothesis |

## Comandos

```bash
# Suite rápida
pytest -m "not slow"

# Solo property tests
pytest -m property

# Con coverage
.\scripts\run_coverage.ps1 -Open
```

## Streamlit dashboard

```bash
pip install windloads[ui]
streamlit run windloads/app/dashboard.py
```

## Invariantes verificadas (hypothesis)

- `qp_EC1(z) > 0` para todo input válido
- `qp_EC1` monotónica creciente con `z`
- `qz_ASCE7(V) > 0` para todo input válido
- `qz_ASCE7` creciente con `V²`
- `GCp_zone_3 <= GCp_zone_1` (zonas esquina más severas)
- `V_NSR-10(Barranquilla) > V_NSR-10(Bogotá)` (invariante geográfica)
