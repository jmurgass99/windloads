"""
examples/building_30x20x40.py
=============================
Reference building: rectangular, plan 30 m (B) x 20 m (D), height 40 m
(13 stories of 3.0 m + ground = 39 m, rounded to 40).

Computes wind loads under EC1-1-4, ASCE 7-22 and NSR-10 §B.6, then writes
JSON / CSV / SAP2000 (.s2k) / ETABS (.e2k) snippets.

Run from the project root:
    python examples/building_30x20x40.py
"""
from __future__ import annotations

from pathlib import Path

from windloadjm import (
    EC1WindLoad,
    ASCE7WindLoad,
    NSR10WindLoad,
    ComponentsAndCladding,
    WindLoadCase,
    from_envelope,
    to_json,
    to_csv,
    to_sap_s2k,
    to_etabs_e2k,
)


# --- Common building geometry ----------------------------------------------
B = 30.0                       # width perpendicular to wind [m]
D = 20.0                       # depth parallel to wind [m]
H = 40.0                       # total height [m]
story_heights = [3.0] * 13 + [1.0]   # 13 typical floors + 1 m parapet
out_dir = Path(__file__).resolve().parent / "out"
out_dir.mkdir(exist_ok=True)


def run_ec1() -> WindLoadCase:
    print("\n=== EN 1991-1-4 ===")
    wl = EC1WindLoad(
        vb=26.0, terrain_cat="II",
        building_height=H, width=B, depth=D,
        story_heights=story_heights, enclosure="closed",
    )
    res = wl.compute()
    print(f"  vb_design = {res['vb_design_ms']} m/s")
    print(f"  qp(H)     = {res['qp_top_Pa']} Pa")
    print(f"  Vb        = {res['Vb_kN']} kN")
    print(f"  OTM       = {res['OTM_kNm']} kN·m")

    sf = wl.story_forces()
    pattern = from_envelope(sf, name="WX+", direction="+X")
    case = WindLoadCase(
        name="EC1_30x20x40", code="EC1",
        building={"B": B, "D": D, "H": H, "stories": len(story_heights)},
        patterns=[pattern], meta={"vb_ms": 26.0, "terrain": "II"},
    )

    # C&C report
    cc = ComponentsAndCladding(code="EC1", qh_or_qp=wl.qp_at(H),
                               B=B, h=H, cpi=0.2)
    cc_summary = cc.summary([1.0, 5.0, 10.0])
    print(f"  C&C corner strip width = {cc_summary['corner_strip_a_m']} m "
          f"(e/10)")
    return case


def run_asce7() -> WindLoadCase:
    print("\n=== ASCE 7-22 ===")
    wl = ASCE7WindLoad(
        V=40.0, exposure="C",
        building_height=H, width=B, depth=D,
        story_heights=story_heights,
        risk_category="II", enclosure="enclosed",
    )
    res = wl.compute()
    print(f"  qh        = {res['qh_Pa']} Pa")
    print(f"  Vb        = {res['Vb_kN']} kN")
    print(f"  OTM       = {res['OTM_kNm']} kN·m")

    sf = wl.story_forces()
    pattern = from_envelope(sf, name="WX+", direction="+X")
    case = WindLoadCase(
        name="ASCE7_30x20x40", code="ASCE7",
        building={"B": B, "D": D, "H": H, "stories": len(story_heights)},
        patterns=[pattern], meta={"V_ms": 40.0, "exposure": "C"},
    )

    cc = ComponentsAndCladding(code="ASCE7", qh_or_qp=wl.qh,
                               B=B, h=H, enclosure="enclosed")
    cc_summary = cc.summary([1.0, 5.0, 10.0, 50.0])
    print(f"  C&C corner strip width a = {cc_summary['corner_strip_a_m']} m")
    return case


def run_nsr10() -> WindLoadCase:
    print("\n=== NSR-10 B.6 ===")
    wl = NSR10WindLoad(
        city_or_Vb="barranquilla", terrain_cat="B",
        building_height=H, width=B, depth=D,
        story_heights=story_heights, enclosure="cerrado",
    )
    res = wl.compute()
    print(f"  city      = {res['city']}  (Vb={res['Vb_basic_ms']} m/s)")
    print(f"  qh        = {res['qh_Pa']} Pa")
    print(f"  Vb        = {res['Vb_kN']} kN")
    print(f"  OTM       = {res['OTM_kNm']} kN·m")

    sf = wl.story_forces()
    pattern = from_envelope(sf, name="WX+", direction="+X")
    case = WindLoadCase(
        name="NSR10_30x20x40", code="NSR10",
        building={"B": B, "D": D, "H": H, "stories": len(story_heights)},
        patterns=[pattern], meta={"city": "barranquilla", "terrain": "B"},
    )
    return case


def dump_case(case: WindLoadCase) -> None:
    to_json(case, out_dir / f"{case.name}.json")
    to_csv(case, out_dir / f"{case.name}.csv")
    s2k = to_sap_s2k(case.patterns[0])
    (out_dir / f"{case.name}.s2k").write_text(s2k, encoding="utf-8")
    e2k = to_etabs_e2k(case.patterns[0])
    (out_dir / f"{case.name}.e2k").write_text(e2k, encoding="utf-8")
    print(f"  wrote {case.name}.{{json,csv,s2k,e2k}} -> {out_dir}")


if __name__ == "__main__":
    for case in (run_ec1(), run_asce7(), run_nsr10()):
        dump_case(case)
    print("\nAll exports done.")
