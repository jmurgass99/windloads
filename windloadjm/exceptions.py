"""Jerarquia de excepciones tipadas de WindLoadJm.

Permite al caller distinguir entre:
    - Norma fuera de aplicabilidad (CodeError) - ej. ASCE7 en edificio > 500 ft
    - Geometria invalida (GeometryError) - ej. ratio h/d fuera de tablas
    - Configuracion del calculo (ConfigurationError) - ej. exposure category invalido
    - Dependencia faltante (DependencyError) - ej. openpyxl no instalado para export Excel
"""
from __future__ import annotations


class WindLoadError(Exception):
    """Base de todas las excepciones del paquete."""


class CodeError(WindLoadError, ValueError):
    """Caso fuera del rango de aplicabilidad de la norma seleccionada.

    Ejemplos:
        - ASCE 7 26.1.2: altura > 500 ft requiere wind tunnel
        - EC1 6.3.2.2: roof types no cubiertos en Annex
        - NSR-10 B.6.2: ciudades fuera del mapa B.6.4-1
    """


class GeometryError(WindLoadError, ValueError):
    """Geometria del edificio o componente invalida.

    Ejemplos:
        - Ratio h/b fuera de tablas
        - Slope > 45 grados en cubiertas a dos aguas
        - Effective area negativa
    """


class ConfigurationError(WindLoadError, ValueError):
    """Parametro de configuracion invalido.

    Ejemplos:
        - Exposure category != A/B/C/D
        - Risk category fuera de I/II/III/IV
        - Terrain category EC1 no en {0,1,2,3,4}
    """


class DependencyError(WindLoadError):
    """Falta un paquete opcional para alguna funcionalidad."""


__all__ = [
    "WindLoadError",
    "CodeError",
    "GeometryError",
    "ConfigurationError",
    "DependencyError",
]
