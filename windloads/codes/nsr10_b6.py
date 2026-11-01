"""
nsr10_b6.py — High-level API for NSR-10 Título B.6 wind load calculations.

Reference: NSR-10 Título B — Cargas (Colombia, 2010 + updates)
§B.6: Presión del viento sobre estructuras

NSR-10 follows ASCE 7-98/02 methodology adapted for Colombian conditions.
Key difference: wind speed maps based on Colombian meteorological data.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from ..terrain import TerrainProfile
from ..pressure import WindPressure
from ..envelope import MWFRSEnvelope


# ---------------------------------------------------------------------------
# NSR-10 §B.6.3 — Basic wind speed by Colombian region [m/s]
# Velocidad básica del viento (50-year MRI, open terrain, 10 m height)
# ---------------------------------------------------------------------------
NSR10_WIND_SPEED_BY_CITY: dict[str, float] = {
    # Caribe coast — high wind
    "barranquilla":     45.0,
    "cartagena":        45.0,
    "santa_marta":      40.0,
    "valledupar":       35.0,
    "riohacha":         45.0,
    "monteria":         30.0,
    # Pacific coast
    "buenaventura":     30.0,
    "tumaco":           30.0,
    # Andean interior
    "bogota":           27.0,
    "medellin":         27.0,
    "cali":             27.0,
    "manizales":        27.0,
    "pereira":          27.0,
    "armenia":          27.0,
    "bucaramanga":      30.0,
    "cucuta":           35.0,
    "ibague":           27.0,
    "neiva":            30.0,
    "pasto":            27.0,
    "popayan":          27.0,
    "tunja":            30.0,
    # Llanos / Orinoquia
    "villavicencio":    27.0,
    "yopal":            30.0,
    # Amazon
    "leticia":          25.0,
    # Default
    "default":          27.0,
}


# ---------------------------------------------------------------------------
# NSR-10 §B.6.5 — Wind threat zones (Figura B.6.5-1)
# Colombia is divided into 5 wind hazard zones. Each zone has an associated
# basic wind speed V (50-year MRI, open terrain, 10 m height).
#
# Arroyo Amell y Ramos Castillo (2015), Ingeniería y Ciencia 11(21):177-195,
# doi:10.17230/ingciencia.11.21.9, p. 181: la NSR-10 distingue 5 regiones,
# de 17 m/s (60 km/h) en la región 1 a 36 m/s (130 km/h) en la región 5, y
# 28 m/s (100 km/h) para buena parte del territorio. Las zonas 2 y 4 (80 y
# 120 km/h) siguen SIN CONTRASTAR con la Figura B.6.4-1. Antes de 1.2.0 la
# zona 5 valía 140 km/h ≈ 39 m/s.
#   Zona 1 :  60 km/h  ≈ 17 m/s   (baja amenaza — Amazonía, sur Andino)
#   Zona 2 :  80 km/h  ≈ 22 m/s   (sin contrastar)
#   Zona 3 : 100 km/h  ≈ 28 m/s   (interior Andino general)
#   Zona 4 : 120 km/h  ≈ 33 m/s   (sin contrastar)
#   Zona 5 : 130 km/h  ≈ 36 m/s   (costa Caribe, Guajira)
# Se conservan también los valores específicos por capital del mapa anterior
# (que pueden exceder estos mínimos zonales) para no perder precisión.
# ---------------------------------------------------------------------------
NSR10_WIND_ZONES: dict[int, float] = {
    1: 17.0,   # 60 km/h — baja amenaza
    2: 22.0,   # 80 km/h
    3: 28.0,   # 100 km/h
    4: 33.0,   # 120 km/h
    5: 36.0,   # 130 km/h — alta amenaza (costa Caribe)
}


# ---------------------------------------------------------------------------
# Asignación de zona por ciudad principal (NSR-10 Figura B.6.5-1)
# FIXME: confirmar zona exacta de cada municipio contra la figura oficial.
# ---------------------------------------------------------------------------
NSR10_CITY_ZONES: dict[str, int] = {
    # Caribe (zona alta) — costa norte
    "barranquilla":     5,
    "cartagena":        5,
    "santa_marta":      5,
    "riohacha":         5,
    "valledupar":       4,
    "monteria":         4,
    "sincelejo":        4,
    # Pacífico
    "buenaventura":     4,
    "tumaco":           4,
    "quibdo":           3,
    # Andina interior
    "bogota":           3,
    "medellin":         3,
    "cali":             3,
    "manizales":        3,
    "pereira":          3,
    "armenia":          3,
    "ibague":           3,
    "pasto":            2,
    "popayan":          3,
    "tunja":            3,
    "bucaramanga":      4,
    "cucuta":           4,
    "neiva":            3,
    "florencia":        2,
    # Llanos / Orinoquía
    "villavicencio":    3,
    "yopal":            4,
    "arauca":           4,
    "puerto_carreno":   3,
    # Amazonía (zona baja)
    "leticia":          1,
    "mitu":             1,
    "inirida":          2,
    "san_jose_del_guaviare": 2,
}


# ---------------------------------------------------------------------------
# Bounding boxes aproximados para las 5 zonas (lat, lon en grados)
# (lat_min, lat_max, lon_min, lon_max, zone_id)
# Se evalúan en orden — el primer bbox que contiene el punto gana, por eso
# los bbox de zonas altas (costa) van primero. Esta es una aproximación de
# la Figura B.6.5-1 mediante rectángulos; para precisión total usar la figura.
# FIXME: aproximación gruesa — sustituir por polígonos por departamento si se
# requiere mayor exactitud.
# ---------------------------------------------------------------------------
_NSR10_ZONE_BBOXES: list[tuple[float, float, float, float, int]] = [
    # Zona 5: Guajira + costa Caribe (Atlántico, norte Magdalena, Bolívar norte)
    (10.0, 12.7, -75.8, -71.0, 5),
    # Zona 4: Caribe interior (Córdoba, Sucre, Cesar, sur Bolívar, Santanderes,
    # norte de Boyacá, Arauca, Casanare)
    (7.5, 11.0, -76.5, -69.5, 4),
    # Zona 4: Pacífico sur costa (Buenaventura, Tumaco)
    (1.0, 4.5, -79.5, -77.0, 4),
    # Zona 2: Sur Andino (Nariño interior, Putumayo, Caquetá norte)
    (0.5, 2.5, -77.5, -75.0, 2),
    # Zona 1: Amazonía (Amazonas, Vaupés, sur Caquetá/Putumayo)
    (-4.5, 1.5, -75.0, -66.5, 1),
    # Zona 2: Guainía / oriente Vichada
    (1.5, 4.5, -69.0, -66.5, 2),
    # Zona 3: Andina central + Llanos centrales (resto del país)
    (1.0, 8.0, -77.5, -69.5, 3),
]

# Bounding box global de Colombia
_COLOMBIA_BBOX = (-4.5, 13.5, -82.0, -66.5)  # lat_min, lat_max, lon_min, lon_max


def _normalize_city_key(city: str) -> str:
    """Normalize a city name to the dict key format used in this module."""
    return (
        city.lower().strip().replace(" ", "_")
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )


def nsr10_zone_from_coords(lat: float, lon: float) -> int:
    """
    Classify a (lat, lon) point into one of the 5 NSR-10 wind threat zones
    per NSR-10 §B.6.5, Figura B.6.5-1.

    Uses a coarse bounding-box approximation of the official figure. Boxes
    are evaluated in order from highest to lowest hazard so that the more
    conservative classification wins at boundaries.

    Parameters
    ----------
    lat : float  Latitude in decimal degrees (positive North).
    lon : float  Longitude in decimal degrees (negative West for Colombia).

    Returns
    -------
    zone_id : int  Zone identifier in {1, 2, 3, 4, 5}.

    Raises
    ------
    ValueError  If the coordinates fall outside Colombia's bounding box.
    """
    lat_min, lat_max, lon_min, lon_max = _COLOMBIA_BBOX
    if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
        raise ValueError(
            f"Coordinates ({lat}, {lon}) fall outside Colombia "
            f"(approx. bbox lat∈[{lat_min},{lat_max}], lon∈[{lon_min},{lon_max}])."
        )
    for bb_lat_min, bb_lat_max, bb_lon_min, bb_lon_max, zone in _NSR10_ZONE_BBOXES:
        if bb_lat_min <= lat <= bb_lat_max and bb_lon_min <= lon <= bb_lon_max:
            return zone
    # Fallback conservador: zona Andina interior
    return 3


def nsr10_basic_wind_speed(
    city: str | None = None,
    *,
    zone: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> float:
    """
    Return the basic wind speed [m/s] per NSR-10 §B.6.5 (Figura B.6.5-1).

    Resolution order:
      1. ``city``  — explicit Colombian capital/municipality name.
      2. ``zone``  — explicit NSR-10 wind zone id (1..5).
      3. ``lat``/``lon`` — geographic coordinates; classified via
         :func:`nsr10_zone_from_coords`.

    For backward compatibility, calling ``nsr10_basic_wind_speed("Bogotá")``
    still works. When resolving by city, the legacy per-capital table
    (``NSR10_WIND_SPEED_BY_CITY``) is consulted first; if absent, the city's
    assigned zone (``NSR10_CITY_ZONES``) is used.

    Parameters
    ----------
    city : str, optional  Colombian city (case-insensitive, accents optional).
    zone : int, optional  NSR-10 wind zone id in {1,2,3,4,5}.
    lat, lon : float, optional  Geographic coordinates (decimal degrees).

    Returns
    -------
    Vb [m/s]

    Raises
    ------
    ValueError  If ``zone`` is not in {1..5}, or if (lat, lon) is outside Colombia.
    TypeError   If no resolution input is provided.
    """
    # 1) by city
    if city is not None:
        key = _normalize_city_key(city)
        if key in NSR10_WIND_SPEED_BY_CITY:
            return NSR10_WIND_SPEED_BY_CITY[key]
        if key in NSR10_CITY_ZONES:
            return NSR10_WIND_ZONES[NSR10_CITY_ZONES[key]]
        return NSR10_WIND_SPEED_BY_CITY["default"]

    # 2) by zone
    if zone is not None:
        if zone not in NSR10_WIND_ZONES:
            raise ValueError(f"Invalid NSR-10 wind zone {zone!r}; expected 1..5.")
        return NSR10_WIND_ZONES[zone]

    # 3) by coordinates
    if lat is not None and lon is not None:
        z = nsr10_zone_from_coords(lat, lon)
        return NSR10_WIND_ZONES[z]

    raise TypeError(
        "nsr10_basic_wind_speed requires one of: city, zone, or (lat, lon)."
    )


@dataclass
class NSR10WindLoad:
    """
    Complete NSR-10 §B.6 wind load calculation for rectangular buildings.

    Parameters
    ----------
    city_or_Vb : str | float
        Colombian city name OR direct basic wind speed [m/s].
    terrain_cat : str
        NSR-10 terrain category: 'A', 'B', 'C', or 'D'.
    building_height : float
        Total building height H [m].
    width : float
        Building width B [m] perpendicular to wind.
    depth : float
        Building depth D [m] parallel to wind.
    story_heights : list[float], optional
        Individual story heights [m] bottom-to-top.
    enclosure : str
        'cerrado', 'parcialmente_abierto', or 'abierto'.
    importance_factor : float
        Importance factor I (groups I to IV: 0.87, 1.0, 1.15, 1.15 — values
        of ASCE 7-05, not checked against NSR-10 Tabla B.6.5-1). It
        multiplies the velocity pressure, qz = 0.613·Kz·Kzt·Kd·V²·I, as in
        ASCE 7-05 (adopted by NSR-10, Arroyo y Ramos 2015). Before 1.2.0 it
        multiplied V, so qz grew with I²: +32 % instead of +15 % for
        I = 1.15 and −24 % instead of −13 % for I = 0.87.

    Examples
    --------
    >>> wl = NSR10WindLoad("barranquilla", terrain_cat='B',
    ...                    building_height=15.0, width=12.0, depth=10.0,
    ...                    story_heights=[3.0]*5)
    >>> r = wl.compute()
    >>> print(f"Vb = {r['Vb_design_ms']} m/s  →  Base shear: {r['Vb_kN']} kN")
    """
    city_or_Vb: str | float
    terrain_cat: str
    building_height: float
    width: float = 15.0
    depth: float = 12.0
    story_heights: list[float] | None = None
    enclosure: str = "cerrado"
    importance_factor: float = 1.0
    Kzt: float = 1.0
    Kd: float = 0.85
    G: float = 0.85

    def __post_init__(self) -> None:
        self.terrain_cat = self.terrain_cat.upper()
        if isinstance(self.city_or_Vb, str):
            self._Vb_basic = nsr10_basic_wind_speed(self.city_or_Vb)
            self._city = self.city_or_Vb
        else:
            self._Vb_basic = float(self.city_or_Vb)
            self._city = "user_defined"

        if self.story_heights is None:
            self.story_heights = [self.building_height]

        self._terrain = TerrainProfile(code="NSR10", category=self.terrain_cat)
        self._envelope = MWFRSEnvelope(
            code="NSR10",
            story_heights=self.story_heights,
            B=self.width,
            D=self.depth,
        )

    @property
    def Vb_design(self) -> float:
        """
        Equivalent speed √I · Vb,basic [m/s]: with it 0.613·Kz·Kzt·Kd·Vb_design²
        equals qz·I, the velocity pressure of ASCE 7-05 Eq. 6-15 that NSR-10
        adopted. It is not a wind speed of the code; I applies to qz.
        """
        return self.importance_factor ** 0.5 * self._Vb_basic

    def qz_at(self, z: float) -> float:
        """Velocity pressure qz [Pa] at height z."""
        return self._terrain.nsr10_velocity_pressure(
            z, self.Vb_design, Kd=self.Kd, Kzt=self.Kzt
        )

    @property
    def qh(self) -> float:
        """Velocity pressure at building height [Pa]."""
        return self.qz_at(self.building_height)

    def facade_pressures(self) -> dict:
        """Net MWFRS wall pressures [kPa]."""
        wp = WindPressure(code="NSR10", enclosure=self.enclosure)
        return wp.nsr10_wall_pressures(
            self.qh, self.qh, self.depth, self.width,
            self.building_height, self.G
        )

    def story_forces(self) -> list:
        """Story-level wind forces [kN] per floor."""
        return self._envelope.asce7_story_forces(
            self._terrain, self.Vb_design,
            Kd=self.Kd, Kzt=self.Kzt,
            G=self.G, enclosure=self.enclosure
        )

    def compute(self) -> dict:
        """
        Full NSR-10 §B.6 wind load calculation.

        Returns
        -------
        dict with all key parameters and results.
        """
        sf = self.story_forces()
        fp = self.facade_pressures()
        return {
            "code": "NSR-10 Título B.6",
            "city": self._city,
            "terrain_category": self.terrain_cat,
            "Vb_basic_ms": self._Vb_basic,
            "importance_factor_Iw": self.importance_factor,
            "Vb_design_ms": round(self.Vb_design, 2),
            "Kd": self.Kd,
            "Kzt": self.Kzt,
            "G": self.G,
            "enclosure": self.enclosure,
            "H_m": self.building_height,
            "B_m": self.width,
            "D_m": self.depth,
            "qh_Pa": round(self.qh, 2),
            "facade_pressures": fp,
            "Vb_kN": self._envelope.total_base_shear(sf),
            "OTM_kNm": self._envelope.overturning_moment(sf),
            "story_forces": [
                {"story": f.story, "z_top_m": f.z_top,
                 "qz_Pa": f.qp_or_qz, "Fx_kN": f.Fx}
                for f in sf
            ],
        }
