"""
Mapa de velocidad básica de viento Vb por ciudad — referencias normativas
ASCE 7-22, NCh 432, NSR-10 §B.6.4, EN 1991-1-4 §4.2.

Implementación inicial con ciudades capitales/grandes — extender con
shapefiles de zonas de viento de cada norma cuando se priorice.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindLocation:
    city: str
    country: str
    Vb_m_s: float        # velocidad básica de viento (10 min, 10 m, R=50 años)
    standard: str        # "ASCE 7-22" | "NCh 432" | "NSR-10" | "EN 1991-1-4"


_TABLE: list[WindLocation] = [
    WindLocation("Santiago",      "CL", 32.0, "NCh 432"),
    WindLocation("Concepción",    "CL", 45.0, "NCh 432"),
    WindLocation("Valparaíso",    "CL", 40.0, "NCh 432"),
    WindLocation("Antofagasta",   "CL", 30.0, "NCh 432"),
    WindLocation("Bogotá",        "CO", 26.0, "NSR-10"),
    WindLocation("Medellín",      "CO", 26.0, "NSR-10"),
    WindLocation("Cali",          "CO", 33.0, "NSR-10"),
    WindLocation("Cartagena",     "CO", 33.0, "NSR-10"),
    WindLocation("Barranquilla",  "CO", 40.0, "NSR-10"),
    WindLocation("Madrid",        "ES", 26.0, "EN 1991-1-4"),
    WindLocation("Barcelona",     "ES", 29.0, "EN 1991-1-4"),
    WindLocation("Bilbao",        "ES", 27.0, "EN 1991-1-4"),
    WindLocation("Sevilla",       "ES", 26.0, "EN 1991-1-4"),
    WindLocation("Miami",         "US", 76.0, "ASCE 7-22"),  # huracán
    WindLocation("Houston",       "US", 67.0, "ASCE 7-22"),
    WindLocation("New York",      "US", 49.0, "ASCE 7-22"),
    WindLocation("San Francisco", "US", 38.0, "ASCE 7-22"),
    WindLocation("Lima",          "PE", 33.0, "NTE E.020"),
    WindLocation("Quito",         "EC", 30.0, "NEC-SE"),
    WindLocation("Buenos Aires",  "AR", 32.0, "CIRSOC 102"),
]


def lookup_Vb(city: str) -> WindLocation | None:
    """Lookup case-insensitive, accent-tolerant simplificado."""
    import unicodedata

    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
        return s.lower().strip()

    needle = _norm(city)
    for loc in _TABLE:
        if _norm(loc.city) == needle:
            return loc
    return None


def list_locations(country: str | None = None) -> list[WindLocation]:
    if country is None:
        return list(_TABLE)
    return [l for l in _TABLE if l.country == country.upper()]


__all__ = ["WindLocation", "lookup_Vb", "list_locations"]
