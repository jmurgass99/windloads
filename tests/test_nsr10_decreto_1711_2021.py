"""Regiones de amenaza eólica de la NSR-10 según el Decreto 1711 de 2021 (Anexo Técnico, Figura B.6.4-1)."""
import pytest

from windloads.codes import (
    NSR10_WIND_ZONES,
    NSR10_WIND_ZONES_B24,
    nsr10_basic_wind_speed,
    nsr10_zone_from_coords,
)

# Tabla del mapa del decreto: región → (m/s con combinaciones B.2.3, m/s con B.2.4)
DECRETO_1711_2021 = {1: (17, 22), 2: (22, 28), 3: (28, 35), 4: (33, 42),
                     5: (36, 46), 6: (44, 56), 7: (49, 61)}


@pytest.mark.parametrize("region", sorted(DECRETO_1711_2021))
def test_zone_tables_match_decree(region):
    b23, b24 = DECRETO_1711_2021[region]
    assert NSR10_WIND_ZONES[region] == b23
    assert NSR10_WIND_ZONES_B24[region] == b24
    assert nsr10_basic_wind_speed(zone=region, combinations="B.2.4") == b24


def test_islands_regions_6_and_7():
    assert nsr10_zone_from_coords(12.55, -81.70) == 6        # San Andrés
    assert nsr10_zone_from_coords(13.35, -81.37) == 7        # Providencia
    assert nsr10_basic_wind_speed("San Andrés") == 44.0
    assert nsr10_basic_wind_speed("Providencia", use_regional_map_b641=True, combinations="B.2.4") == 61.0


def test_b24_needs_regional_map_for_cities():
    with pytest.raises(ValueError):
        nsr10_basic_wind_speed("bogota", combinations="B.2.4")
    assert nsr10_basic_wind_speed("bogota", use_regional_map_b641=True, combinations="B.2.4") == 35.0
    with pytest.raises(ValueError):
        nsr10_basic_wind_speed(zone=3, combinations="B.2.5")
