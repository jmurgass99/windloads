"""
export.py — Serialise wind load results into formats consumable by FastSAP,
SAP2000 (.s2k) and ETABS (.e2k).

Data model
----------
StoryPressure   one floor in one direction
LoadPattern     a collection of StoryPressure for a given direction (+X, -X, +Y, -Y)
WindLoadCase    several patterns sharing a code / building geometry

Serialisers
-----------
to_json(case, path)           — JSON dump (FastSAP-friendly)
to_csv(case, path)            — flat CSV table (one row per story·pattern)
to_sap_s2k(pattern)           — SAP2000 .s2k text snippet (LOAD PATTERNS +
                                JOINT LOADS section, story_id assumed)
to_etabs_e2k(pattern)         — ETABS .e2k text snippet (LOADPATTERN +
                                FRAME LOADS)

Notes
-----
* Forces are stored in kN and the .s2k/.e2k snippets use kN, m.
* The story_id and joint mapping must be filled-in by the caller using their
  own model — the snippets here only define the load pattern and per-story
  resultant. Lateral distribution to joints is handled downstream.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class StoryPressure:
    """Per-story wind force resultant."""
    story: int                # 1-based story number (1 = first floor above ground)
    z_top_m: float            # top elevation of the story [m]
    pressure_Pa: float        # net equivalent pressure, or qp/qz if no width given [Pa]
    Fx_kN: float              # horizontal resultant force in load direction [kN]
    label: str = ""           # optional human label


@dataclass
class LoadPattern:
    """A wind load pattern: direction + list of story resultants."""
    name: str                                       # e.g. 'WX+', 'WY-'
    direction: str                                  # '+X', '-X', '+Y', '-Y'
    pressures_by_level: list[StoryPressure] = field(default_factory=list)
    pattern_type: str = "WIND"                     # SAP/ETABS load type
    self_weight_multiplier: float = 0.0

    @property
    def base_shear_kN(self) -> float:
        return float(sum(p.Fx_kN for p in self.pressures_by_level))

    @property
    def overturning_moment_kNm(self) -> float:
        # Each story force is applied at its top floor (z_top), as the
        # .s2k/.e2k snippets do; MWFRSEnvelope.overturning_moment uses z_mid,
        # so this value is larger by sum(F·h_story/2).
        return float(sum(p.Fx_kN * p.z_top_m for p in self.pressures_by_level))


@dataclass
class JointMap:
    """Map story-level fuerza -> conjunto de nudos que la reciben.

    Two construction modes are offered:

    * :meth:`uniform`  — pass ``{story_index: [joint_names]}``; the story
      force is divided in equal parts among the joints.
    * :meth:`by_tributary_area` — pass ``{story_index: [(joint, area_or_weight), ...]}``;
      the story force is split pro-rata according to the supplied weights.

    The internal representation ``per_story`` is always a dict of
    ``{story_index: [(joint_name, weight_fraction), ...]}`` where the
    weight fractions on a given story sum to 1.0.

    Example
    -------
    >>> jm = JointMap.uniform({1: ["J1", "J2", "J3", "J4"]})
    >>> jm.per_story[1]
    [('J1', 0.25), ('J2', 0.25), ('J3', 0.25), ('J4', 0.25)]
    >>> jm2 = JointMap.by_tributary_area({1: [("J1", 6.0), ("J2", 2.0)]})
    >>> jm2.per_story[1]
    [('J1', 0.75), ('J2', 0.25)]
    """
    per_story: dict[int, list[tuple[str, float]]]

    @classmethod
    def uniform(cls, joints_per_story: dict[int, list[str]]) -> "JointMap":
        per_story: dict[int, list[tuple[str, float]]] = {}
        for story, joints in joints_per_story.items():
            if not joints:
                per_story[story] = []
                continue
            w = 1.0 / len(joints)
            per_story[story] = [(j, w) for j in joints]
        return cls(per_story=per_story)

    @classmethod
    def by_tributary_area(
        cls, joints_with_area: dict[int, list[tuple[str, float]]]
    ) -> "JointMap":
        per_story: dict[int, list[tuple[str, float]]] = {}
        for story, items in joints_with_area.items():
            total = float(sum(w for _, w in items))
            if total <= 0:
                per_story[story] = [(j, 0.0) for j, _ in items]
                continue
            per_story[story] = [(j, float(w) / total) for j, w in items]
        return cls(per_story=per_story)


@dataclass
class WindLoadCase:
    """A complete wind study (one code, several directional patterns)."""
    name: str
    code: str                                      # 'EC1' | 'ASCE7' | 'NSR10'
    building: dict                                 # B, D, H, story_heights …
    patterns: list[LoadPattern] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Builders — convert envelope output (StoryWindForce) into LoadPattern
# ---------------------------------------------------------------------------
def from_envelope(story_forces, name: str, direction: str,
                  tributary_widths_m: float | None = None) -> LoadPattern:
    """
    Convert a list of StoryWindForce (envelope.py) into a LoadPattern.

    Parameters
    ----------
    story_forces        : iterable of StoryWindForce (has .story, .z_top,
                          .qp_or_qz, .Fx)
    name                : pattern name (e.g. 'WX+')
    direction           : '+X', '-X', '+Y', '-Y'
    tributary_widths_m  : optional loaded width B [m]. When given,
                          pressure_Pa is the equivalent net pressure
                          Fx·1000 / (B·(z_top − z_bot)) that reproduces Fx on
                          the story strip. If None, pressure_Pa is the
                          velocity pressure qp_or_qz of the story (not a net
                          pressure). Before 1.2.0 the width was ignored and
                          qp_or_qz was always reported.
    """
    pressures = []
    for sf in story_forces:
        h_story = float(sf.z_top) - float(getattr(sf, "z_bot", 0.0))
        if tributary_widths_m and tributary_widths_m > 0 and h_story > 0:
            pressure = sf.Fx * 1000.0 / (tributary_widths_m * h_story)
        else:
            pressure = sf.qp_or_qz
        pressures.append(StoryPressure(
            story=sf.story,
            z_top_m=float(sf.z_top),
            pressure_Pa=float(pressure),
            Fx_kN=float(sf.Fx),
            label=f"S{sf.story}",
        ))
    return LoadPattern(
        name=name,
        direction=direction,
        pressures_by_level=pressures,
    )


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def to_json(case: WindLoadCase, path: str | Path | None = None,
            indent: int = 2) -> str:
    """Serialise a WindLoadCase as JSON. Writes to *path* if given."""
    payload = {
        "name": case.name,
        "code": case.code,
        "building": case.building,
        "meta": case.meta,
        "patterns": [
            {
                "name": p.name,
                "direction": p.direction,
                "pattern_type": p.pattern_type,
                "self_weight_multiplier": p.self_weight_multiplier,
                "base_shear_kN": round(p.base_shear_kN, 2),
                "overturning_moment_kNm": round(p.overturning_moment_kNm, 2),
                "pressures_by_level": [asdict(s) for s in p.pressures_by_level],
            }
            for p in case.patterns
        ],
    }
    text = json.dumps(payload, indent=indent, ensure_ascii=False)
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def to_csv(case: WindLoadCase, path: str | Path) -> Path:
    """Flat CSV: one row per (pattern, story)."""
    path = Path(path)
    fieldnames = ["case", "code", "pattern", "direction",
                  "story", "z_top_m", "pressure_Pa", "Fx_kN"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for p in case.patterns:
            for s in p.pressures_by_level:
                w.writerow({
                    "case": case.name,
                    "code": case.code,
                    "pattern": p.name,
                    "direction": p.direction,
                    "story": s.story,
                    "z_top_m": round(s.z_top_m, 3),
                    "pressure_Pa": round(s.pressure_Pa, 2),
                    "Fx_kN": round(s.Fx_kN, 2),
                })
    return path


# ---------------------------------------------------------------------------
# SAP2000 .s2k snippet
# ---------------------------------------------------------------------------
def to_sap_s2k(pattern: LoadPattern,
               joint_map: "JointMap | dict[int, int] | None" = None) -> str:
    """
    Generate a SAP2000 .s2k text snippet that defines:
      * the load pattern in TABLE: "LOAD PATTERN DEFINITIONS"
      * one or more JOINT LOAD lines per story in TABLE: "JOINT LOADS - FORCE"

    Parameters
    ----------
    pattern   : LoadPattern instance.
    joint_map : optional. May be:
                  * a :class:`JointMap` instance — the story horizontal force
                    is distributed among joints using the stored weights and
                    one ``Joint=...`` line is emitted per joint.
                  * a legacy ``{story_number: joint_id}`` dict — one joint per
                    story receives the full story force.
                  * ``None`` — the literal placeholder ``<STORY_n_JOINT>`` is
                    emitted so the caller can search/replace it (regression
                    compatible).

    Notes
    -----
    Forces are written in kN. Direction +X writes Fx (F1), +Y writes Fy (F2),
    negative directions flip the sign.
    """
    dir_axis = pattern.direction[-1].upper()   # 'X' or 'Y'
    sign = -1.0 if pattern.direction.startswith("-") else +1.0
    comp = {"X": "F1", "Y": "F2"}[dir_axis]    # SAP joint-load component

    lines: list[str] = []
    lines.append(f"; ---- LoadPattern {pattern.name} (Wind, {pattern.direction}) ----")
    lines.append('TABLE:  "LOAD PATTERN DEFINITIONS"')
    lines.append(
        f'   LoadPat={pattern.name}   DesignType={pattern.pattern_type}   '
        f'SelfWtMult={pattern.self_weight_multiplier:.4f}'
    )
    lines.append("")
    lines.append('TABLE:  "JOINT LOADS - FORCE"')
    for s in pattern.pressures_by_level:
        story_force = sign * s.Fx_kN
        if isinstance(joint_map, JointMap):
            distribution = joint_map.per_story.get(s.story, [])
            if not distribution:
                # Fall back to placeholder if the story is not in the map
                lines.append(
                    f'   Joint=<STORY_{s.story}_JOINT>   LoadPat={pattern.name}   '
                    f'CoordSys=GLOBAL   {comp}={story_force:.4f}   F3=0   '
                    f'M1=0   M2=0   M3=0'
                )
                continue
            for joint_name, weight in distribution:
                f = story_force * weight
                lines.append(
                    f'   Joint={joint_name}   LoadPat={pattern.name}   '
                    f'CoordSys=GLOBAL   {comp}={f:.4f}   F3=0   M1=0   M2=0   M3=0'
                )
        elif isinstance(joint_map, dict):
            joint = str(joint_map.get(s.story, f"<STORY_{s.story}_JOINT>"))
            lines.append(
                f'   Joint={joint}   LoadPat={pattern.name}   CoordSys=GLOBAL   '
                f'{comp}={story_force:.4f}   F3=0   M1=0   M2=0   M3=0'
            )
        else:
            lines.append(
                f'   Joint=<STORY_{s.story}_JOINT>   LoadPat={pattern.name}   '
                f'CoordSys=GLOBAL   {comp}={story_force:.4f}   F3=0   '
                f'M1=0   M2=0   M3=0'
            )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ETABS .e2k snippet
# ---------------------------------------------------------------------------
def to_etabs_e2k(pattern: LoadPattern,
                 story_name_map: dict[int, str] | None = None,
                 joint_map: "JointMap | None" = None) -> str:
    """
    Generate an ETABS .e2k snippet defining a wind load pattern and the
    per-story diaphragm loads.

    Parameters
    ----------
    pattern         : LoadPattern instance.
    story_name_map  : optional ``{story_number: 'Story1'}`` mapping. If
                      omitted, ``'Story{n}'`` is used.
    joint_map       : optional :class:`JointMap`. When provided, each story's
                      horizontal force is split among its joints and emitted
                      as ``STORYLOAD <story> POINT <joint>`` lines (one per
                      joint). When omitted, a single ``STORYLOAD ... TYPE
                      "FORCE"`` diaphragm line is emitted (regression
                      compatible).
    """
    dir_axis = pattern.direction[-1].upper()
    sign = -1.0 if pattern.direction.startswith("-") else +1.0
    fcomp = {"X": "FX", "Y": "FY"}[dir_axis]

    lines: list[str] = []
    lines.append(f'$ ---- LoadPattern {pattern.name} (Wind, {pattern.direction}) ----')
    lines.append('$ LOAD PATTERNS')
    lines.append(
        f'  LOADPATTERN "{pattern.name}"  TYPE  "WIND"  '
        f'SELFWEIGHT  {pattern.self_weight_multiplier:.3f}'
    )
    lines.append("")
    lines.append('$ STORY FORCES')
    for s in pattern.pressures_by_level:
        story_name = (story_name_map.get(s.story, f"Story{s.story}")
                      if story_name_map else f"Story{s.story}")
        story_force = sign * s.Fx_kN
        if isinstance(joint_map, JointMap):
            distribution = joint_map.per_story.get(s.story, [])
            if not distribution:
                lines.append(
                    f'  STORYLOAD "{story_name}"  LOADPAT "{pattern.name}"  '
                    f'TYPE  "FORCE"   DIR "{fcomp}"  VALUE {story_force:.4f}'
                )
                continue
            for joint_name, weight in distribution:
                f = story_force * weight
                lines.append(
                    f'  STORYLOAD "{story_name}"  LOADPAT "{pattern.name}"  '
                    f'TYPE  "POINT"  POINT "{joint_name}"  '
                    f'DIR "{fcomp}"  VALUE {f:.4f}'
                )
        else:
            lines.append(
                f'  STORYLOAD "{story_name}"  LOADPAT "{pattern.name}"  '
                f'TYPE  "FORCE"   DIR "{fcomp}"  VALUE {story_force:.4f}'
            )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def standard_directions(story_forces) -> list[LoadPattern]:
    """
    Build the four standard wind patterns (+X, -X, +Y, -Y) from a single
    set of envelope story forces (assuming the same magnitude is applied
    in all directions — typical for symmetric rectangular buildings; the
    caller should override this when the building is asymmetric).
    """
    return [
        from_envelope(story_forces, name=f"W{d[1]}{d[0]}", direction=d)
        for d in ("+X", "-X", "+Y", "-Y")
    ]
