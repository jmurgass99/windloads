"""Tests for JointMap distribution in to_sap_s2k / to_etabs_e2k."""
import math

import pytest

from windloadjm.export import (
    JointMap,
    LoadPattern,
    StoryPressure,
    to_etabs_e2k,
    to_sap_s2k,
)


def _make_pattern():
    """3-story pattern with known forces: 10, 20, 30 kN."""
    return LoadPattern(
        name="WX+",
        direction="+X",
        pressures_by_level=[
            StoryPressure(story=1, z_top_m=3.0, pressure_Pa=500.0, Fx_kN=10.0),
            StoryPressure(story=2, z_top_m=6.0, pressure_Pa=600.0, Fx_kN=20.0),
            StoryPressure(story=3, z_top_m=9.0, pressure_Pa=700.0, Fx_kN=30.0),
        ],
    )


# -------------------------------------------------------------------- #
# JointMap construction
# -------------------------------------------------------------------- #
def test_jointmap_uniform_equal_weights():
    jm = JointMap.uniform({1: ["A", "B", "C", "D"]})
    assert len(jm.per_story[1]) == 4
    for _, w in jm.per_story[1]:
        assert w == pytest.approx(0.25)
    assert sum(w for _, w in jm.per_story[1]) == pytest.approx(1.0)


def test_jointmap_by_tributary_area_prorata():
    jm = JointMap.by_tributary_area({1: [("A", 6.0), ("B", 2.0)]})
    weights = dict(jm.per_story[1])
    assert weights["A"] == pytest.approx(0.75)
    assert weights["B"] == pytest.approx(0.25)
    assert sum(weights.values()) == pytest.approx(1.0)


# -------------------------------------------------------------------- #
# SAP .s2k snippet with uniform JointMap
# -------------------------------------------------------------------- #
def test_sap_s2k_uniform_distribution():
    pattern = _make_pattern()
    jm = JointMap.uniform({
        1: ["J1A", "J1B", "J1C", "J1D"],
        2: ["J2A", "J2B", "J2C", "J2D"],
        3: ["J3A", "J3B", "J3C", "J3D"],
    })
    text = to_sap_s2k(pattern, joint_map=jm)

    # 4 joint lines per story = 12 JOINT LOAD lines
    joint_lines = [l for l in text.splitlines() if l.strip().startswith("Joint=")]
    assert len(joint_lines) == 12

    # Each story-1 joint must receive 10/4 = 2.5 kN on F1
    for jname in ("J1A", "J1B", "J1C", "J1D"):
        assert any(f"Joint={jname}" in l and "F1=2.5000" in l for l in joint_lines)
    # Story 2: 20/4 = 5.0
    for jname in ("J2A", "J2B", "J2C", "J2D"):
        assert any(f"Joint={jname}" in l and "F1=5.0000" in l for l in joint_lines)
    # Story 3: 30/4 = 7.5
    for jname in ("J3A", "J3B", "J3C", "J3D"):
        assert any(f"Joint={jname}" in l and "F1=7.5000" in l for l in joint_lines)

    # No placeholder remains
    assert "<STORY_" not in text


def test_sap_s2k_tributary_area_prorata():
    pattern = _make_pattern()
    jm = JointMap.by_tributary_area({
        1: [("J1A", 3.0), ("J1B", 1.0)],   # 75% / 25%
        2: [("J2A", 1.0), ("J2B", 1.0)],
        3: [("J3A", 1.0), ("J3B", 1.0)],
    })
    text = to_sap_s2k(pattern, joint_map=jm)

    # Story 1 force 10 kN distributed 7.5 / 2.5
    assert "Joint=J1A" in text and "F1=7.5000" in text
    assert "Joint=J1B" in text and "F1=2.5000" in text


def test_sap_s2k_negative_direction_sign():
    pattern = _make_pattern()
    pattern.direction = "-X"
    jm = JointMap.uniform({1: ["A", "B"], 2: ["C", "D"], 3: ["E", "F"]})
    text = to_sap_s2k(pattern, joint_map=jm)
    # Story 1: -10/2 = -5.0
    assert "Joint=A" in text and "F1=-5.0000" in text


# -------------------------------------------------------------------- #
# ETABS .e2k snippet with JointMap (STORYLOAD POINT)
# -------------------------------------------------------------------- #
def test_etabs_e2k_pointload_with_jointmap():
    pattern = _make_pattern()
    jm = JointMap.uniform({
        1: ["P1", "P2", "P3", "P4"],
        2: ["P5", "P6", "P7", "P8"],
        3: ["P9", "P10", "P11", "P12"],
    })
    text = to_etabs_e2k(pattern, joint_map=jm)

    point_lines = [l for l in text.splitlines() if "POINT" in l and "STORYLOAD" in l]
    assert len(point_lines) == 12

    # Story 1 each joint = 10/4 = 2.5 kN
    for j in ("P1", "P2", "P3", "P4"):
        assert any(f'POINT "{j}"' in l and "2.5000" in l for l in point_lines)
    # Story 3 each joint = 30/4 = 7.5
    for j in ("P9", "P10", "P11", "P12"):
        assert any(f'POINT "{j}"' in l and "7.5000" in l for l in point_lines)


def test_etabs_e2k_tributary_distribution():
    pattern = _make_pattern()
    jm = JointMap.by_tributary_area({
        1: [("PA", 3.0), ("PB", 1.0)],
        2: [("PC", 1.0), ("PD", 1.0)],
        3: [("PE", 1.0), ("PF", 1.0)],
    })
    text = to_etabs_e2k(pattern, joint_map=jm)
    assert 'POINT "PA"' in text and "7.5000" in text
    assert 'POINT "PB"' in text and "2.5000" in text


# -------------------------------------------------------------------- #
# Regression: placeholder is preserved when no joint_map
# -------------------------------------------------------------------- #
def test_sap_s2k_placeholder_preserved_without_jointmap():
    pattern = _make_pattern()
    text = to_sap_s2k(pattern)
    assert "<STORY_1_JOINT>" in text
    assert "<STORY_2_JOINT>" in text
    assert "<STORY_3_JOINT>" in text


def test_etabs_e2k_storyload_force_preserved_without_jointmap():
    pattern = _make_pattern()
    text = to_etabs_e2k(pattern)
    # Diaphragm-level STORYLOAD ... TYPE "FORCE"
    assert 'TYPE  "FORCE"' in text
    assert 'POINT "' not in text


def test_sap_s2k_legacy_dict_still_works():
    """The legacy dict[int, int] signature must still be accepted."""
    pattern = _make_pattern()
    text = to_sap_s2k(pattern, joint_map={1: 101, 2: 202, 3: 303})
    assert "Joint=101" in text
    assert "Joint=202" in text
    assert "Joint=303" in text
    assert "<STORY_" not in text


# -------------------------------------------------------------------- #
# Conservation: sum of distributed forces == story force
# -------------------------------------------------------------------- #
def test_force_conservation_uniform():
    pattern = _make_pattern()
    jm = JointMap.uniform({1: ["a", "b", "c"], 2: ["d", "e"], 3: ["f"]})
    # Recompute the distribution manually and ensure sums match story totals
    for s in pattern.pressures_by_level:
        dist = jm.per_story[s.story]
        total = sum(s.Fx_kN * w for _, w in dist)
        assert total == pytest.approx(s.Fx_kN)
