"""
windloads.vb_atlas — Extended basic wind speed atlas (Vb [m/s]).

Hard-coded tables of basic wind speed by city for three normative
families:

  * Chile        — NCh 432.Of2010 (mapa de viento básico Anexo A)
  * Colombia     — NSR-10 Título B §B.6.4 (figura B.6.4-1)
  * España (UE)  — CTE DB-SE-AE 2009 §3.3 / EN 1991-1-4 Anexo N

The Vb stored here is the *basic wind speed* (3 s or 10 min gust
depending on the code; documented in the entry's ``averaging`` field)
at 10 m height, return period 50 years, terrain category II.

Source URLs :
  * Chile     https://www.inn.cl/nch432
  * Colombia  https://www.minvivienda.gov.co/normatividad/nsr-10
  * España    https://www.codigotecnico.org/  (DB SE-AE)
  * Eurocode  https://eurocodes.jrc.ec.europa.eu/

Status     : 30 cities per country (90 total) hard-coded. Values
             cross-checked against published code maps; minor
             rounding to 1 m/s.

Note       : This complements the legacy ``vb_map.py`` (kept for
             backward compatibility) by adding a country/code aware
             lookup ``vb_for(city, country, code)``.
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
_COLOMBIA: list[VbEntry] = [
    VbEntry("Bogota",        "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Medellin",      "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Cali",          "CO", "NSR-10", 33.0, "3 s gust"),
    VbEntry("Barranquilla",  "CO", "NSR-10", 40.0, "3 s gust",
            "Zona costera Caribe."),
    VbEntry("Cartagena",     "CO", "NSR-10", 36.0, "3 s gust"),
    VbEntry("Bucaramanga",   "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Pereira",       "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Manizales",     "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Ibague",        "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Santa Marta",   "CO", "NSR-10", 36.0, "3 s gust"),
    VbEntry("Pasto",         "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Cucuta",        "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Villavicencio", "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Monteria",      "CO", "NSR-10", 33.0, "3 s gust"),
    VbEntry("Valledupar",    "CO", "NSR-10", 33.0, "3 s gust"),
    VbEntry("Sincelejo",     "CO", "NSR-10", 33.0, "3 s gust"),
    VbEntry("Riohacha",      "CO", "NSR-10", 40.0, "3 s gust"),
    VbEntry("Quibdo",        "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Armenia",       "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Popayan",       "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Tunja",         "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Florencia",     "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Neiva",         "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Yopal",         "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Mocoa",         "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Arauca",        "CO", "NSR-10", 28.0, "3 s gust"),
    VbEntry("Leticia",       "CO", "NSR-10", 26.0, "3 s gust"),
    VbEntry("Tumaco",        "CO", "NSR-10", 30.0, "3 s gust"),
    VbEntry("Buenaventura",  "CO", "NSR-10", 30.0, "3 s gust"),
    VbEntry("San Andres",    "CO", "NSR-10", 50.0, "3 s gust",
            "Isla Caribe — huracanes."),
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
    """Return Vb [m/s] for ``city`` (optionally filtered by country/code).

    Lookup is accent- and case-insensitive. Returns ``None`` if no
    entry matches.
    """
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
