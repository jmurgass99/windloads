"""Tests para EnvelopeZoneMapping en WindLoads."""
from windloads.geometry_mapping import build_building_wind_mesh


def test_envelope_zone_mapping_refinement():
    panels_1, map_1, sum_1 = build_building_wind_mesh(
        vb_m_s=28.0, terrain_cat="II", subdivisions_per_story=1
    )
    panels_4, map_4, sum_4 = build_building_wind_mesh(
        vb_m_s=28.0, terrain_cat="II", subdivisions_per_story=4
    )

    assert len(map_1.story_to_panels[1]) == 2
    assert len(map_4.story_to_panels[1]) == 8
    assert set(map_4.roof_to_zones.keys()) == {"F", "G", "H", "I"}
    assert sum_4["base_shear_kN"] > 100.0
    assert abs(sum_1["base_shear_kN"] - sum_4["base_shear_kN"]) / sum_4["base_shear_kN"] < 0.05
