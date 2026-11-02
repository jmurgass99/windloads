"""
nsr10_b6.py — High-level API for NSR-10 Título B.6 wind load calculations.

Reference: NSR-10 Título B — Cargas (Colombia, 2010 + updates)
§B.6: Presión del viento sobre estructuras
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from ..terrain import TerrainProfile
from ..terrain._impl import NSR10_ASCE7_EXPOSURE_MAP
from ..pressure import WindPressure
from ..envelope import MWFRSEnvelope


# ---------------------------------------------------------------------------
# NSR-10 §B.6.3 — Basic wind speed by Colombian region [m/s]
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
    # Insular (Decreto 1711 de 2021, regiones 6 y 7, combinaciones B.2.3)
    "san_andres":       44.0,
    "providencia":      49.0,
    # Default
    "default":          27.0,
}


# ---------------------------------------------------------------------------
# NSR-10 §B.6.4 — Wind threat zones (Figura B.6.4-1 as modified by
# Decreto 1711 de 2021, Anexo Técnico): 7 regions, with one speed for the
# load combinations of B.2.3 and another for those of B.2.4.
#   Región   B.2.3            B.2.4
#     1     17 m/s ( 60 km/h)  22 m/s ( 75 km/h)
#     2     22 m/s ( 80 km/h)  28 m/s (100 km/h)
#     3     28 m/s (100 km/h)  35 m/s (125 km/h)
#     4     33 m/s (120 km/h)  42 m/s (150 km/h)
#     5     36 m/s (130 km/h)  46 m/s (165 km/h)
#     6     44 m/s (160 km/h)  56 m/s (200 km/h)   Isla de San Andrés
#     7     49 m/s (175 km/h)  61 m/s (220 km/h)   Providencia y Santa Catalina
# Zonas no estudiadas: 28 m/s (B.2.3) y 35 m/s (B.2.4).
# ---------------------------------------------------------------------------
NSR10_WIND_ZONES: dict[int, float] = {
    1: 17.0,   # 60 km/h — baja amenaza
    2: 22.0,   # 80 km/h
    3: 28.0,   # 100 km/h
    4: 33.0,   # 120 km/h
    5: 36.0,   # 130 km/h — costa Caribe
    6: 44.0,   # 160 km/h — Isla de San Andrés
    7: 49.0,   # 175 km/h — Providencia y Santa Catalina
}

NSR10_WIND_ZONES_B24: dict[int, float] = {
    1: 22.0,   # 75 km/h
    2: 28.0,   # 100 km/h
    3: 35.0,   # 125 km/h
    4: 42.0,   # 150 km/h
    5: 46.0,   # 165 km/h
    6: 56.0,   # 200 km/h
    7: 61.0,   # 220 km/h
}


NSR10_CITY_ZONES: dict[str, int] = {
    # Caribe (zona alta) — costa norte
    "barranquilla":     5,
    "cartagena":        5,
    "santa_marta":      5,
    "riohacha":         5,
    "valledupar":       4,
    "monteria":         4,
    "sincelejo":        4,
    # Insular
    "san_andres":       6,
    "providencia":      7,
    "santa_catalina":   7,
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
    "mocoa":            2,
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


_NSR10_ZONE_BBOXES: list[tuple[float, float, float, float, int]] = [
    # Zona 7: Providencia y Santa Catalina (≈13,35 N)
    (13.0, 13.5, -82.0, -81.0, 7),
    # Zona 6: Isla de San Andrés (≈12,55 N)
    (12.0, 13.0, -82.0, -81.0, 6),
    # Zona 5: Guajira + costa Caribe (Atlántico, norte Magdalena, Bolívar norte)
    (10.0, 12.7, -75.8, -71.0, 5),
    # Zona 4: Caribe interior (Córdoba, Sucre, Cesar, sur Bolívar, Santanderes, Arauca, Casanare)
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

_COLOMBIA_BBOX = (-4.5, 13.5, -82.0, -66.5)


def _normalize_city_key(city: str) -> str:
    """Normalize a city name to the dict key format used in this module."""
    return (
        city.lower().strip().replace(" ", "_")
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )


def nsr10_zone_from_coords(lat: float, lon: float) -> int:
    """
    Classify a (lat, lon) point into one of the NSR-10 wind threat zones
    per NSR-10 §B.6.4, Figura B.6.4-1.
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
    return 3


def nsr10_basic_wind_speed(
    city: str | None = None,
    *,
    zone: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
    use_regional_map_b641: bool = False,
    combinations: str = "B.2.3",
) -> float:
    """
    Return the basic wind speed [m/s] per NSR-10 §B.6.4 (Figura B.6.4-1).

    When ``use_regional_map_b641=True``, city lookup uses the normative regional
    map zones (`NSR10_CITY_ZONES` -> `NSR10_WIND_ZONES`, e.g., Region 3 = 28 m/s,
    Region 5 = 36 m/s) directly. When ``use_regional_map_b641=False`` (default),
    the per-capital table (`NSR10_WIND_SPEED_BY_CITY`) takes precedence for
    backward compatibility.

    ``combinations`` selects the column of the Decreto 1711 de 2021 map:
    ``"B.2.3"`` (default, the historical NSR-10 speeds) or ``"B.2.4"``. The
    B.2.4 column only applies to the regional zones (``zone``, ``lat``/``lon``,
    or a city with ``use_regional_map_b641=True``); the per-city table has a
    single value and raises ``ValueError`` if asked for B.2.4.
    """
    if combinations not in ("B.2.3", "B.2.4"):
        raise ValueError(f"combinations must be 'B.2.3' or 'B.2.4', got {combinations!r}.")
    zones = NSR10_WIND_ZONES if combinations == "B.2.3" else NSR10_WIND_ZONES_B24
    if city is not None:
        key = _normalize_city_key(city)
        if use_regional_map_b641 and key in NSR10_CITY_ZONES:
            return zones[NSR10_CITY_ZONES[key]]
        if use_regional_map_b641:
            return zones[3]
        if combinations == "B.2.4":
            raise ValueError("The per-city table has no B.2.4 column; pass use_regional_map_b641=True.")
        if key in NSR10_WIND_SPEED_BY_CITY:
            return NSR10_WIND_SPEED_BY_CITY[key]
        if key in NSR10_CITY_ZONES:
            return NSR10_WIND_ZONES[NSR10_CITY_ZONES[key]]
        return NSR10_WIND_SPEED_BY_CITY["default"]

    if zone is not None:
        if zone not in zones:
            raise ValueError(f"Invalid NSR-10 wind zone {zone!r}; expected 1..7.")
        return zones[zone]

    if lat is not None and lon is not None:
        z = nsr10_zone_from_coords(lat, lon)
        return zones[z]

    raise TypeError(
        "nsr10_basic_wind_speed requires one of: city, zone, or (lat, lon)."
    )


@dataclass
class NSR10WindLoad:
    """
    Complete NSR-10 §B.6 wind load calculation for rectangular buildings.
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
    use_asce7_exposure_convention: bool = False
    use_regional_map_b641: bool = False

    def __post_init__(self) -> None:
        self.terrain_cat = self.terrain_cat.upper()
        if isinstance(self.city_or_Vb, str):
            self._Vb_basic = nsr10_basic_wind_speed(
                self.city_or_Vb, use_regional_map_b641=self.use_regional_map_b641
            )
            self._city = self.city_or_Vb
        else:
            self._Vb_basic = float(self.city_or_Vb)
            self._city = "user_defined"

        if self.story_heights is None:
            self.story_heights = [self.building_height]

        internal_cat = (
            NSR10_ASCE7_EXPOSURE_MAP.get(self.terrain_cat, self.terrain_cat)
            if self.use_asce7_exposure_convention
            else self.terrain_cat
        )
        self._terrain = TerrainProfile(code="NSR10", category=internal_cat)
        self._envelope = MWFRSEnvelope(
            code="NSR10",
            story_heights=self.story_heights,
            B=self.width,
            D=self.depth,
        )

    @property
    def Vb_design(self) -> float:
        return self.importance_factor ** 0.5 * self._Vb_basic

    def qz_at(self, z: float) -> float:
        return self._terrain.nsr10_velocity_pressure(
            z, self.Vb_design, Kd=self.Kd, Kzt=self.Kzt
        )

    @property
    def qh(self) -> float:
        return self.qz_at(self.building_height)

    def facade_pressures(self) -> dict:
        wp = WindPressure(code="NSR10", enclosure=self.enclosure)
        return wp.nsr10_wall_pressures(
            self.qh, self.qh, self.depth, self.width,
            self.building_height, self.G
        )

    def story_forces(self) -> list:
        return self._envelope.asce7_story_forces(
            self._terrain, self.Vb_design,
            Kd=self.Kd, Kzt=self.Kzt,
            G=self.G, enclosure=self.enclosure
        )

    def compute(self) -> dict:
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
