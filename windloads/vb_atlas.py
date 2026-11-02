"""
windloads.vb_atlas — Extended basic wind speed atlas (Vb [m/s]).

Hard-coded tables of basic wind speed by city for three normative
families:

  * Chile        — NCh 432.Of2010 (mapa de viento básico Anexo A)
  * Colombia     — NSR-10 Título B §B.6.4 (figura B.6.4-1)
  * España (UE)  — CTE DB-SE-AE 2009 §3.3 / EN 1991-1-4 Anexo N
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class VbEntry:
    city: str
    country: str       # ISO 3166-1 alpha-2 ("CL", "CO", "ES")
    code: str          # "NCh 432", "NSR-10", "CTE-DB-SE-AE"
    Vb_m_s: float      # basic wind speed [m/s]
    averaging: str     # "3 s gust", "10 min mean", etc.
    note: str = ""


# ----------------------------------------------------------- Chile (30)
_CHILE: list[VbEntry] = [
    VbEntry("Arica",          "CL", "NCh 432", 30.0, "3 s gust"),
    VbEntry("Iquique",        "CL", "NCh 432", 30.0, "3 s gust"),
    VbEntry("Antofagasta",    "CL", "NCh 432", 30.0, "3 s gust"),
    VbEntry("Calama",         "CL", "NCh 432", 32.0, "3 s gust"),
    VbEntry("Copiapo",        "CL", "NCh 432", 32.0, "3 s gust"),
    VbEntry("La Serena",      "CL", "NCh 432", 35.0, "3 s gust"),
    VbEntry("Coquimbo",       "CL", "NCh 432", 36.0, "3 s gust"),
    VbEntry("Valparaiso",     "CL", "NCh 432", 40.0, "3 s gust"),
    VbEntry("Vina del Mar",   "CL", "NCh 432", 40.0, "3 s gust"),
    VbEntry("Santiago",       "CL", "NCh 432", 32.0, "3 s gust"),
    VbEntry("San Antonio",    "CL", "NCh 432", 38.0, "3 s gust"),
    VbEntry("Rancagua",       "CL", "NCh 432", 32.0, "3 s gust"),
    VbEntry("Curico",         "CL", "NCh 432", 33.0, "3 s gust"),
    VbEntry("Talca",          "CL", "NCh 432", 33.0, "3 s gust"),
    VbEntry("Chillan",        "CL", "NCh 432", 35.0, "3 s gust"),
    VbEntry("Concepcion",     "CL", "NCh 432", 45.0, "3 s gust",
            "Costa Bío-Bío; valor mayor por exposición."),
    VbEntry("Los Angeles",    "CL", "NCh 432", 38.0, "3 s gust"),
    VbEntry("Temuco",         "CL", "NCh 432", 38.0, "3 s gust"),
    VbEntry("Valdivia",       "CL", "NCh 432", 40.0, "3 s gust"),
    VbEntry("Osorno",         "CL", "NCh 432", 40.0, "3 s gust"),
    VbEntry("Puerto Montt",   "CL", "NCh 432", 42.0, "3 s gust"),
    VbEntry("Castro",         "CL", "NCh 432", 42.0, "3 s gust"),
    VbEntry("Coyhaique",      "CL", "NCh 432", 45.0, "3 s gust"),
    VbEntry("Punta Arenas",   "CL", "NCh 432", 50.0, "3 s gust",
            "Patagonia, vientos extremos."),
    VbEntry("Puerto Natales", "CL", "NCh 432", 50.0, "3 s gust"),
    VbEntry("Ovalle",         "CL", "NCh 432", 33.0, "3 s gust"),
    VbEntry("Quillota",       "CL", "NCh 432", 35.0, "3 s gust"),
    VbEntry("Los Andes",      "CL", "NCh 432", 32.0, "3 s gust"),
    VbEntry("Linares",        "CL", "NCh 432", 33.0, "3 s gust"),
    VbEntry("Ancud",          "CL", "NCh 432", 42.0, "3 s gust"),
]

# ----------------------------------------------------------- Colombia (30)
# Sincronizado con las regiones de amenaza eólica NSR-10 Figura B.6.4-1
_COLOMBIA: list[VbEntry] = [
    VbEntry("Bogota",        "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Medellin",      "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Cali",          "CO", "NSR-10", 33.0, "3 s gust", "Valle / Región 4"),
    VbEntry("Barranquilla",  "CO", "NSR-10", 36.0, "3 s gust", "Región 5 — Costa Caribe (130 km/h)"),
    VbEntry("Cartagena",     "CO", "NSR-10", 36.0, "3 s gust", "Región 5 — Costa Caribe (130 km/h)"),
    VbEntry("Bucaramanga",   "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Pereira",       "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Manizales",     "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Ibague",        "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Santa Marta",   "CO", "NSR-10", 36.0, "3 s gust", "Región 5 — Costa Caribe (130 km/h)"),
    VbEntry("Pasto",         "CO", "NSR-10", 22.0, "3 s gust", "Región 2 (80 km/h)"),
    VbEntry("Cucuta",        "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Villavicencio", "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Monteria",      "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Valledupar",    "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Sincelejo",     "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Riohacha",      "CO", "NSR-10", 36.0, "3 s gust", "Región 5 — Guajira (130 km/h)"),
    VbEntry("Quibdo",        "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Armenia",       "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Popayan",       "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Tunja",         "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Florencia",     "CO", "NSR-10", 22.0, "3 s gust", "Región 2 (80 km/h)"),
    VbEntry("Neiva",         "CO", "NSR-10", 28.0, "3 s gust", "Región 3 (100 km/h)"),
    VbEntry("Yopal",         "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Mocoa",         "CO", "NSR-10", 22.0, "3 s gust", "Región 2 (80 km/h)"),
    VbEntry("Arauca",        "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Leticia",       "CO", "NSR-10", 17.0, "3 s gust", "Región 1 — Amazonía (60 km/h)"),
    VbEntry("Tumaco",        "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("Buenaventura",  "CO", "NSR-10", 33.0, "3 s gust", "Región 4 (120 km/h)"),
    VbEntry("San Andres",    "CO", "NSR-10", 44.0, "3 s gust", "Región 6 — Isla de San Andrés (160 km/h; Decreto 1711 de 2021, B.2.3)"),
]

# ----------------------------------------------------------- Espana (30)
_ESPANA: list[VbEntry] = [
    VbEntry("Madrid",        "ES", "CTE-DB-SE-AE", 26.0, "10 min mean",
            "Zona A"),
    VbEntry("Barcelona",     "ES", "CTE-DB-SE-AE", 27.0, "10 min mean",
            "Zona B"),
    VbEntry("Valencia",      "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Sevilla",       "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Zaragoza",      "ES", "CTE-DB-SE-AE", 29.0, "10 min mean",
            "Zona C (Cierzo)"),
    VbEntry("Malaga",        "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Murcia",        "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Palma",         "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Las Palmas",    "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Bilbao",        "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Alicante",      "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Cordoba",       "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Valladolid",    "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Vigo",          "ES", "CTE-DB-SE-AE", 29.0, "10 min mean",
            "Zona C - costa Atlántica"),
    VbEntry("Gijon",         "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Granada",       "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("A Coruna",      "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Vitoria",       "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Pamplona",      "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Santander",     "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Logrono",       "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Toledo",        "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Salamanca",     "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Burgos",        "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Caceres",       "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Badajoz",       "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("Albacete",      "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
    VbEntry("San Sebastian", "ES", "CTE-DB-SE-AE", 27.0, "10 min mean"),
    VbEntry("Tenerife",      "ES", "CTE-DB-SE-AE", 29.0, "10 min mean"),
    VbEntry("Cadiz",         "ES", "CTE-DB-SE-AE", 26.0, "10 min mean"),
]

_VB_ATLAS: list[VbEntry] = _CHILE + _COLOMBIA + _ESPANA


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().strip()


def vb_for(city: str,
           country: str | None = None,
           code: str | None = None) -> float | None:
    """Return Vb [m/s] for ``city`` (optionally filtered by country/code)."""
    target = _norm(city)
    country_u = country.upper() if country else None
    for e in _VB_ATLAS:
        if _norm(e.city) != target:
            continue
        if country_u and e.country != country_u:
            continue
        if code and code.lower() not in e.code.lower():
            continue
        return e.Vb_m_s
    return None


def list_vb(country: str | None = None) -> list[VbEntry]:
    if country is None:
        return list(_VB_ATLAS)
    cu = country.upper()
    return [e for e in _VB_ATLAS if e.country == cu]


__all__ = ["VbEntry", "vb_for", "list_vb"]
