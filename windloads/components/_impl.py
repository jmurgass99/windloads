"""
components.py — Components & Cladding (C&C) wind pressures.

Covers:
  - ASCE 7-22 Chapter 30: Components & Cladding for low- and mid-rise buildings.
    Walls   → Zones 4 (interior) and 5 (corner).
    Roofs   → Zones 1 (interior), 2 (edge), 3 (corner) for flat / low-slope.
  - EN 1991-1-4 §7.2.2/§7.2.3: Zones A-E (walls) and F-I (flat roofs).
    Local cpe,1 vs global cpe,10 are interpolated as a function of the
    loaded area A (Figure 7.2):
        cpe = cpe,1                       for A ≤ 1 m²
        cpe = cpe,1 − (cpe,1 − cpe,10)·log10(A)   for 1 < A < 10 m²
        cpe = cpe,10                      for A ≥ 10 m²

Notation
--------
A_eff   : effective wind area / tributary area for the element [m²]
GCp     : (gust factor * external pressure coeff) per ASCE 7 Fig. 30.3-1/-2
GCpi    : internal pressure coeff (enclosed = ±0.18, partially enc. = ±0.55)
p       : net design pressure  =  qh · (GCp − GCpi)        [Pa]

References (ASCE 7-22)
----------------------
Fig. 30.3-1  : Walls, h ≤ 18.3 m (60 ft) — Zones 4 & 5
Fig. 30.3-2A : Gable/hip roofs θ ≤ 7° — Zones 1, 2, 3 (and 2e/3e for edges)
Fig. 30.3-2B : Monoslope roofs 3° < θ ≤ 30° — Zones 1, 2, 3
Fig. 30.3-2C : Gable roofs 7° < θ ≤ 45° — Zones 1, 2e, 2n, 2r, 3
Fig. 30.3-2D : Mansard roofs θ ≤ 45° (treated as gable on sloped surfaces)
Fig. 30.7-1  : Domed roofs — function of rise/diameter ratio f/D
§30.9        : Parapets — adjustment of GCp on adjacent windward zones
§30.3.2      : Effective wind area definition
§30.2.2      : Minimum design pressure 16 psf ≈ 766 Pa

EN 1991-1-4 references
----------------------
§7.2.4 / Tab. 7.4a-b : Duopitch (gable) roofs
§7.2.5 / Tab. 7.5    : Multi-span roofs
§7.2.7               : Cylindrical and spherical (domed) roofs
§7.2.8 / Tab. 7.7    : Hipped (four-slope / mansard-like) roofs
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..exceptions import CodeError, ConfigurationError, GeometryError


# =========================================================================
# ASCE 7-22 Chapter 30 — GCp values at the two reference areas
# Values are (GCp_at_A=10ft²≈0.93m², GCp_at_A=500ft²≈46.45m²)
# Positive value = pressure toward surface; negative = suction (away).
# Source: ASCE 7-22 Fig. 30.3-1 (walls) and Fig. 30.3-2A (low-slope roofs).
# =========================================================================
_ASCE7_GCP_WALLS: dict[str, dict[str, tuple[float, float]]] = {
    # Zone 4 — interior wall zone
    "4": {"pos": (1.00, 0.70), "neg": (-1.10, -0.80)},
    # Zone 5 — wall corner zone (within distance "a" from edge)
    "5": {"pos": (1.00, 0.70), "neg": (-1.40, -0.80)},
}

_ASCE7_GCP_ROOF_LOW_SLOPE: dict[str, dict[str, tuple[float, float]]] = {
    # Low-slope roof, θ ≤ 7° (Fig. 30.3-2A) — values for h ≤ 18.3 m
    "1": {"pos": (0.30, 0.20), "neg": (-1.70, -1.10)},   # interior
    "2": {"pos": (0.30, 0.20), "neg": (-2.30, -1.60)},   # edge
    "3": {"pos": (0.30, 0.20), "neg": (-3.20, -2.30)},   # corner
}

# Tributary area bounds [m²] for the log-interpolation
_A_LO = 10 * 0.092903        # 10 ft² ≈ 0.929 m²
_A_HI = 500 * 0.092903       # 500 ft² ≈ 46.45 m²

# ASCE 7-22 §30.2.2 — minimum design pressure
MIN_DESIGN_PRESSURE_PA = 16 * 47.8803   # 16 psf ≈ 766 Pa


def asce7_GCp(zone: str,
              A_eff: float,
              surface: str = "wall",
              sign: str = "neg") -> float:
    """
    Log-interpolated external pressure coefficient (GCp) per ASCE 7-22 Ch. 30.

    Parameters
    ----------
    zone   : '4', '5' (walls) or '1', '2', '3' (low-slope roofs)
    A_eff  : effective wind area of the element [m²]
    surface: 'wall' or 'roof'
    sign   : 'pos' (positive pressure) or 'neg' (suction)

    Returns
    -------
    GCp : float (already includes the gust effect — do NOT multiply by G)

    Reference: ASCE 7-22 Fig. 30.3-1 (walls) / Fig. 30.3-2A (roofs).
    """
    table = _ASCE7_GCP_WALLS if surface == "wall" else _ASCE7_GCP_ROOF_LOW_SLOPE
    if zone not in table:
        raise ValueError(f"Unknown C&C zone '{zone}' for surface '{surface}'. "
                         f"Valid: {list(table)}")
    gcp_lo, gcp_hi = table[zone][sign]
    # Log-interpolation between A_lo (≈0.93 m²) and A_hi (≈46.45 m²)
    if A_eff <= _A_LO:
        return gcp_lo
    if A_eff >= _A_HI:
        return gcp_hi
    # Linear in log(A): GCp(A) = GCp_lo + (GCp_hi-GCp_lo)·(logA-logAlo)/(logAhi-logAlo)
    frac = (math.log10(A_eff) - math.log10(_A_LO)) / \
           (math.log10(_A_HI) - math.log10(_A_LO))
    return gcp_lo + frac * (gcp_hi - gcp_lo)


def asce7_corner_distance_a(B: float, h: float) -> float:
    """
    Width 'a' of the corner/edge strip for C&C zones (ASCE 7-22 §30.3.1):
        a = min(0.10·B, 0.4·h)   but not less than min(0.04·B, 0.9 m)

    Parameters
    ----------
    B : least horizontal dimension of the building [m]
    h : mean roof height [m]
    """
    a = min(0.10 * B, 0.4 * h)
    a_min = max(0.04 * B, 0.9)
    return max(a, a_min)


def asce7_cc_pressure(zone: str,
                      A_eff: float,
                      qh: float,
                      surface: str = "wall",
                      enclosure: str = "enclosed") -> dict:
    """
    Net C&C design pressure (ASCE 7-22 Eq. 30.3-1):
        p = qh · (GCp − GCpi)

    Returns both positive and negative envelope values plus the controlling
    design value (max absolute).

    Parameters
    ----------
    zone     : C&C zone string ('4', '5', '1', '2', '3')
    A_eff    : effective wind area [m²]
    qh       : velocity pressure at mean roof height [Pa]
    surface  : 'wall' or 'roof'
    enclosure: 'enclosed' | 'partially_enclosed' | 'open'

    Returns
    -------
    dict with keys: GCp_pos, GCp_neg, p_pos_Pa, p_neg_Pa, p_design_Pa
    """
    GCpi_map = {"enclosed": 0.18, "partially_enclosed": 0.55, "open": 0.00}
    if enclosure not in GCpi_map:
        raise ConfigurationError(f"enclosure must be one of {list(GCpi_map)}")
    GCpi = GCpi_map[enclosure]

    GCp_pos = asce7_GCp(zone, A_eff, surface, "pos")
    GCp_neg = asce7_GCp(zone, A_eff, surface, "neg")

    # Worst positive pressure: (+GCp) combined with (−GCpi)
    p_pos = qh * (GCp_pos - (-GCpi))
    # Worst suction: (−GCp) combined with (+GCpi)
    p_neg = qh * (GCp_neg - (+GCpi))

    # ASCE 7-22 §30.2.2 minimum
    if abs(p_pos) < MIN_DESIGN_PRESSURE_PA and p_pos > 0:
        p_pos = MIN_DESIGN_PRESSURE_PA
    if abs(p_neg) < MIN_DESIGN_PRESSURE_PA and p_neg < 0:
        p_neg = -MIN_DESIGN_PRESSURE_PA

    return {
        "zone": zone,
        "surface": surface,
        "A_eff_m2": round(A_eff, 3),
        "GCp_pos": round(GCp_pos, 3),
        "GCp_neg": round(GCp_neg, 3),
        "GCpi": GCpi,
        "p_pos_Pa": round(p_pos, 1),
        "p_neg_Pa": round(p_neg, 1),
        "p_design_Pa": round(max(abs(p_pos), abs(p_neg)), 1),
    }


# =========================================================================
# EN 1991-1-4 §7.2 — cpe,1 (local) vs cpe,10 (global) for walls and roofs
# Values from Tables 7.1 (walls) and 7.2 (flat roofs, sharp eaves).
# Tuples are (cpe,1, cpe,10).
# =========================================================================
_EC1_CPE_WALLS: dict[str, tuple[float, float]] = {
    # Vertical walls, EN 1991-1-4 Table 7.1 — h/d = 1 row (E is -0.7 at
    # h/d = 5 and -0.3 at h/d <= 0.25; use pressure.ec1_cpe_walls for that)
    "A": (-1.4, -1.2),    # side wall, first e/5 from the windward edge
    "B": (-1.1, -0.8),    # side wall, next 4e/5
    "C": (-0.5, -0.5),    # side wall, beyond e
    "D": (1.0, 0.8),      # windward
    "E": (-0.5, -0.5),    # leeward
}

_EC1_CPE_FLAT_ROOF: dict[str, tuple[float, float]] = {
    # Flat roof, sharp eaves (Table 7.2)
    "F": (-2.5, -1.8),    # corner
    "G": (-2.0, -1.2),    # edge
    "H": (-1.2, -0.7),    # interior
    "I_neg": (-0.2, -0.2),
    "I_pos": (+0.2, +0.2),
}


def ec1_cpe_local(zone: str, A: float, surface: str = "wall") -> float:
    """
    EC1-1-4 §7.2.1 / Fig. 7.2 — log interpolation between cpe,1 and cpe,10:
        cpe = cpe,1                                          A ≤ 1 m²
        cpe = cpe,1 − (cpe,1 − cpe,10) · log10(A)            1 < A < 10 m²
        cpe = cpe,10                                         A ≥ 10 m²

    Parameters
    ----------
    zone : 'A'..'E' for walls, 'F'..'I_pos'/'I_neg' for flat roofs
    A    : loaded area of the element [m²]
    surface: 'wall' or 'flat_roof'

    Returns
    -------
    cpe : float
    """
    table = _EC1_CPE_WALLS if surface == "wall" else _EC1_CPE_FLAT_ROOF
    if zone not in table:
        raise ValueError(f"Zone '{zone}' not valid for {surface}. "
                         f"Valid: {list(table)}")
    cpe1, cpe10 = table[zone]
    if A <= 1.0:
        return cpe1
    if A >= 10.0:
        return cpe10
    return cpe1 - (cpe1 - cpe10) * math.log10(A)


def ec1_zone_width_e(b: float, h: float) -> float:
    """
    EC1-1-4 §7.2.2 (1) — Reference dimension for wall/roof zoning:
        e = min(b, 2·h)
    where b is the crosswind width and h is the building height.
    """
    return min(b, 2.0 * h)


def ec1_cc_pressure(zone: str,
                    A: float,
                    qp: float,
                    cpi: float = 0.2,
                    surface: str = "wall") -> dict:
    """
    EN 1991-1-4 §5.2 — Net pressure on a C&C element:
        we = qp · cpe(A)
        wi = qp · cpi
        w_net = we − wi

    Parameters
    ----------
    zone : zone letter (A..E walls, F..I roof)
    A    : loaded area of the element [m²]
    qp   : peak velocity pressure at reference height [Pa]
    cpi  : internal pressure coefficient (default +0.2; use −0.3 for suction)
    surface : 'wall' or 'flat_roof'

    Returns
    -------
    dict with cpe, we_Pa, wi_Pa, w_net_Pa
    """
    cpe = ec1_cpe_local(zone, A, surface)
    we = qp * cpe
    wi = qp * cpi
    return {
        "zone": zone,
        "surface": surface,
        "A_m2": round(A, 3),
        "cpe": round(cpe, 3),
        "cpi": cpi,
        "we_Pa": round(we, 1),
        "wi_Pa": round(wi, 1),
        "w_net_Pa": round(we - wi, 1),
    }


# =========================================================================
# Convenience: complete C&C report for a rectangular building
# =========================================================================
@dataclass
class ComponentsAndCladding:
    """
    Components & Cladding pressure report for a rectangular building.

    Parameters
    ----------
    code        : 'ASCE7' or 'EC1'
    qh_or_qp    : velocity pressure at mean roof height [Pa]
    B           : least horizontal dimension [m]
    h           : mean roof height [m]
    enclosure   : enclosure classification (ASCE 7)
    cpi         : internal pressure coefficient (EC1, default +0.2)
    """
    code: str
    qh_or_qp: float
    B: float
    h: float
    enclosure: str = "enclosed"
    cpi: float = 0.2

    def __post_init__(self) -> None:
        self.code = self.code.upper()
        if self.code not in ("ASCE7", "EC1"):
            raise ConfigurationError("code must be 'ASCE7' or 'EC1'")

    @property
    def corner_strip_width_m(self) -> float:
        """Width 'a' (ASCE 7) or 'e/10' (EC1) of the corner strip [m]."""
        if self.code == "ASCE7":
            return asce7_corner_distance_a(self.B, self.h)
        e = ec1_zone_width_e(self.B, self.h)
        return e / 10.0

    def wall_report(self, A_eff_list: list[float]) -> list[dict]:
        """Tabulate wall C&C pressures for each tributary area in A_eff_list."""
        rows = []
        zones = ["4", "5"] if self.code == "ASCE7" else ["A", "B", "D", "E"]
        for A in A_eff_list:
            for z in zones:
                if self.code == "ASCE7":
                    rows.append(asce7_cc_pressure(z, A, self.qh_or_qp,
                                                  "wall", self.enclosure))
                else:
                    rows.append(ec1_cc_pressure(z, A, self.qh_or_qp,
                                                self.cpi, "wall"))
        return rows

    def roof_report(self, A_eff_list: list[float]) -> list[dict]:
        """Tabulate flat-roof C&C pressures for each tributary area."""
        rows = []
        zones = ["1", "2", "3"] if self.code == "ASCE7" \
            else ["F", "G", "H", "I_neg"]
        for A in A_eff_list:
            for z in zones:
                if self.code == "ASCE7":
                    rows.append(asce7_cc_pressure(z, A, self.qh_or_qp,
                                                  "roof", self.enclosure))
                else:
                    rows.append(ec1_cc_pressure(z, A, self.qh_or_qp,
                                                self.cpi, "flat_roof"))
        return rows

    # -----------------------------------------------------------------
    # Curved / sloped / parapet / mansard roof reports (ASCE 7-22 / EC1)
    # -----------------------------------------------------------------
    def gable_report(self,
                     theta_deg: float,
                     A_eff_list: list[float]) -> list[dict]:
        """Tabulate C&C pressures on a gable roof for the given pitch."""
        rows: list[dict] = []
        if self.code == "ASCE7":
            zones = gable_roof_zones(theta_deg)
            for A in A_eff_list:
                for z in zones:
                    GCp_neg = gable_roof_GCp(theta_deg, A, z, sign="neg")
                    GCp_pos = gable_roof_GCp(theta_deg, A, z, sign="pos")
                    rows.append(_pack_pressure_row(
                        z, "gable_roof", A, GCp_pos, GCp_neg,
                        self.qh_or_qp, self.enclosure))
        else:
            for A in A_eff_list:
                for z in ("F", "G", "H", "I", "J"):
                    cpe = ec1_gable_cpe(theta_deg, z, A)
                    rows.append(_pack_ec1_row(
                        z, "gable_roof", A, cpe, self.qh_or_qp, self.cpi))
        return rows

    def monoslope_report(self,
                         theta_deg: float,
                         A_eff_list: list[float]) -> list[dict]:
        """Tabulate C&C pressures on a monoslope roof."""
        rows: list[dict] = []
        if self.code == "ASCE7":
            for A in A_eff_list:
                for z in ("1", "2", "3"):
                    GCp_neg = monoslope_roof_GCp(theta_deg, A, z, sign="neg")
                    GCp_pos = monoslope_roof_GCp(theta_deg, A, z, sign="pos")
                    rows.append(_pack_pressure_row(
                        z, "monoslope_roof", A, GCp_pos, GCp_neg,
                        self.qh_or_qp, self.enclosure))
        else:
            # EC1 §7.2.4 monopitch — Table 7.3a, θ = 0°, suction branch
            for A in A_eff_list:
                for z in ("F", "G", "H"):
                    cpe = ec1_monopitch_cpe(theta_deg, z, A)
                    rows.append(_pack_ec1_row(
                        z, "monoslope_roof", A, cpe, self.qh_or_qp, self.cpi))
        return rows

    def domed_report(self,
                     f_over_D: float,
                     A_eff_list: list[float]) -> list[dict]:
        """Tabulate C&C pressures on a domed/curved roof."""
        rows: list[dict] = []
        if self.code == "ASCE7":
            for A in A_eff_list:
                for z in ("A", "B", "C"):   # windward / centre / leeward
                    GCp_neg = domed_roof_GCp(f_over_D, A, z, sign="neg")
                    GCp_pos = domed_roof_GCp(f_over_D, A, z, sign="pos")
                    rows.append(_pack_pressure_row(
                        z, "domed_roof", A, GCp_pos, GCp_neg,
                        self.qh_or_qp, self.enclosure))
        else:
            for A in A_eff_list:
                for z in ("A", "B", "C"):
                    cpe = ec1_cylindrical_cpe(f_over_D, z)
                    rows.append(_pack_ec1_row(
                        z, "domed_roof", A, cpe, self.qh_or_qp, self.cpi))
        return rows

    def mansard_report(self,
                       theta_deg: float,
                       A_eff_list: list[float]) -> list[dict]:
        """Tabulate C&C pressures on a mansard roof (ASCE 7-22 Fig. 30.3-2D)."""
        rows: list[dict] = []
        if self.code == "ASCE7":
            for A in A_eff_list:
                for z in ("1", "2", "3"):
                    GCp_neg = mansard_roof_GCp(theta_deg, A, z, sign="neg")
                    GCp_pos = mansard_roof_GCp(theta_deg, A, z, sign="pos")
                    rows.append(_pack_pressure_row(
                        z, "mansard_roof", A, GCp_pos, GCp_neg,
                        self.qh_or_qp, self.enclosure))
        else:
            # EC1 §7.2.8 hipped roof — fallback to gable Tab 7.4 values
            return self.gable_report(theta_deg, A_eff_list)
        return rows

    def parapet_adjustment(self, h_parapet: float) -> dict:
        """
        Effect of a perimeter parapet on adjacent windward roof zones
        (ASCE 7-22 §30.9). Returns the multiplier applied to GCp on the
        windward edge / corner zones and the resulting amplified GCp.
        """
        return parapet_pressure(h_parapet, self.qh_or_qp,
                                GCp_main_neg=-1.10)

    def summary(self,
                A_eff_list: list[float] | None = None) -> dict:
        """Full C&C summary report."""
        if A_eff_list is None:
            A_eff_list = [1.0, 5.0, 10.0, 25.0, 50.0]
        return {
            "code": self.code,
            "qh_or_qp_Pa": round(self.qh_or_qp, 1),
            "B_m": self.B,
            "h_m": self.h,
            "corner_strip_a_m": round(self.corner_strip_width_m, 3),
            "enclosure_or_cpi": self.enclosure if self.code == "ASCE7" else self.cpi,
            "walls": self.wall_report(A_eff_list),
            "roof": self.roof_report(A_eff_list),
        }


# =========================================================================
# Helpers — common to the new sloped / curved / mansard / parapet families
# =========================================================================
def _log_interp_area(A_eff: float,
                     gcp_lo: float,
                     gcp_hi: float,
                     A_lo: float = _A_LO,
                     A_hi: float = _A_HI) -> float:
    """Standard ASCE 7 log-interpolation between A_lo and A_hi."""
    if A_eff <= A_lo:
        return gcp_lo
    if A_eff >= A_hi:
        return gcp_hi
    frac = (math.log10(A_eff) - math.log10(A_lo)) / \
           (math.log10(A_hi) - math.log10(A_lo))
    return gcp_lo + frac * (gcp_hi - gcp_lo)


def _pack_pressure_row(zone: str, surface: str, A: float,
                       GCp_pos: float, GCp_neg: float,
                       qh: float, enclosure: str) -> dict:
    """Build the same dict shape as asce7_cc_pressure()."""
    GCpi_map = {"enclosed": 0.18, "partially_enclosed": 0.55, "open": 0.0}
    GCpi = GCpi_map.get(enclosure, 0.18)
    p_pos = qh * (GCp_pos + GCpi)
    p_neg = qh * (GCp_neg - GCpi)
    if 0 < p_pos < MIN_DESIGN_PRESSURE_PA:
        p_pos = MIN_DESIGN_PRESSURE_PA
    if -MIN_DESIGN_PRESSURE_PA < p_neg < 0:
        p_neg = -MIN_DESIGN_PRESSURE_PA
    return {
        "zone": zone, "surface": surface,
        "A_eff_m2": round(A, 3),
        "GCp_pos": round(GCp_pos, 3),
        "GCp_neg": round(GCp_neg, 3),
        "GCpi": GCpi,
        "p_pos_Pa": round(p_pos, 1),
        "p_neg_Pa": round(p_neg, 1),
        "p_design_Pa": round(max(abs(p_pos), abs(p_neg)), 1),
    }


def _pack_ec1_row(zone: str, surface: str, A: float,
                  cpe: float, qp: float, cpi: float) -> dict:
    we = qp * cpe
    wi = qp * cpi
    return {
        "zone": zone, "surface": surface, "A_m2": round(A, 3),
        "cpe": round(cpe, 3), "cpi": cpi,
        "we_Pa": round(we, 1), "wi_Pa": round(wi, 1),
        "w_net_Pa": round(we - wi, 1),
    }


# =========================================================================
# ASCE 7-22 Fig. 30.3-2C — Gable roof, θ ∈ (7°, 45°]
#   Zones: 1 (interior), 2e (eaves), 2n (ridge), 2r (overhang/rake), 3 (corner)
# Values are (GCp_at_10ft², GCp_at_500ft²) for each pitch band and sign.
# Conservative envelopes drawn from ASCE 7-22 Commentary C30.
# FIXME: verify exact tabulated values in Fig. 30.3-2C for each pitch band
# =========================================================================
_ASCE7_GCP_GABLE: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
    # 7° < θ ≤ 20°  (low-pitched gable)
    "low": {
        "1":  {"pos": (0.50, 0.30), "neg": (-1.20, -0.80)},
        "2e": {"pos": (0.50, 0.30), "neg": (-2.00, -1.40)},
        "2n": {"pos": (0.50, 0.30), "neg": (-1.80, -1.20)},
        "2r": {"pos": (0.50, 0.30), "neg": (-2.20, -1.50)},
        "3":  {"pos": (0.50, 0.30), "neg": (-2.80, -2.00)},
    },
    # 20° < θ ≤ 27°  (medium pitch)
    "med": {
        "1":  {"pos": (0.60, 0.40), "neg": (-1.00, -0.70)},
        "2e": {"pos": (0.60, 0.40), "neg": (-1.80, -1.20)},
        "2n": {"pos": (0.60, 0.40), "neg": (-1.60, -1.10)},
        "2r": {"pos": (0.60, 0.40), "neg": (-2.00, -1.40)},
        "3":  {"pos": (0.60, 0.40), "neg": (-2.20, -1.60)},
    },
    # 27° < θ ≤ 45°  (steep pitch)
    "high": {
        "1":  {"pos": (0.80, 0.50), "neg": (-0.90, -0.60)},
        "2e": {"pos": (0.80, 0.50), "neg": (-1.20, -0.80)},
        "2n": {"pos": (0.80, 0.50), "neg": (-1.20, -0.80)},
        "2r": {"pos": (0.80, 0.50), "neg": (-1.40, -1.00)},
        "3":  {"pos": (0.80, 0.50), "neg": (-1.50, -1.10)},
    },
}


def _gable_band(theta_deg: float) -> str:
    if theta_deg <= 7.0:
        # Hand off to low-slope table by caller; here we still return 'low'
        return "low"
    if theta_deg <= 20.0:
        return "low"
    if theta_deg <= 27.0:
        return "med"
    if theta_deg <= 45.0:
        return "high"
    raise CodeError(
        f"theta_deg={theta_deg} outside Fig. 30.3-2C range (<=45 deg)")


def gable_roof_zones(theta_deg: float) -> tuple[str, ...]:
    """Zone IDs defined for gable roofs at the given pitch band."""
    if theta_deg <= 7.0:
        return ("1", "2", "3")
    return ("1", "2e", "2n", "2r", "3")


def gable_roof_GCp(theta_deg: float,
                   area_eff_m2: float,
                   zone: str,
                   sign: str = "neg") -> float:
    """
    GCp for gable / hip roofs per ASCE 7-22 Fig. 30.3-2A (θ≤7°) and
    Fig. 30.3-2C (7° < θ ≤ 45°). Log-interpolated in effective wind area.
    """
    if theta_deg <= 7.0:
        # Fall back to low-slope table
        return asce7_GCp(zone if zone in _ASCE7_GCP_ROOF_LOW_SLOPE else "2",
                         area_eff_m2, "roof", sign)
    band = _gable_band(theta_deg)
    table = _ASCE7_GCP_GABLE[band]
    if zone not in table:
        raise ValueError(f"Zone '{zone}' invalid for gable roof. "
                         f"Valid: {list(table)}")
    gcp_lo, gcp_hi = table[zone][sign]
    return _log_interp_area(area_eff_m2, gcp_lo, gcp_hi)


# =========================================================================
# ASCE 7-22 Fig. 30.3-2B — Monoslope roof, 3° < θ ≤ 30°
# Conservative two-band envelope.
# FIXME: verify Fig. 30.3-2B tabulated GCp values
# =========================================================================
_ASCE7_GCP_MONOSLOPE: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
    "low": {   # 3° < θ ≤ 10°
        "1": {"pos": (0.30, 0.20), "neg": (-1.40, -0.90)},
        "2": {"pos": (0.30, 0.20), "neg": (-2.10, -1.40)},
        "3": {"pos": (0.30, 0.20), "neg": (-2.80, -2.00)},
    },
    "high": {  # 10° < θ ≤ 30°
        "1": {"pos": (0.40, 0.30), "neg": (-1.30, -0.80)},
        "2": {"pos": (0.40, 0.30), "neg": (-1.80, -1.20)},
        "3": {"pos": (0.40, 0.30), "neg": (-2.90, -2.00)},
    },
}


def monoslope_roof_GCp(theta_deg: float,
                       area_eff_m2: float,
                       zone: str,
                       sign: str = "neg") -> float:
    """GCp for monoslope (shed) roofs per ASCE 7-22 Fig. 30.3-2B."""
    if theta_deg <= 3.0:
        # Treat as flat — Fig. 30.3-2A
        return asce7_GCp(zone, area_eff_m2, "roof", sign)
    if theta_deg <= 10.0:
        band = "low"
    elif theta_deg <= 30.0:
        band = "high"
    else:
        raise ValueError(
            f"theta_deg={theta_deg} outside Fig. 30.3-2B range (≤30°)")
    table = _ASCE7_GCP_MONOSLOPE[band]
    if zone not in table:
        raise ValueError(f"Zone '{zone}' invalid for monoslope roof.")
    gcp_lo, gcp_hi = table[zone][sign]
    return _log_interp_area(area_eff_m2, gcp_lo, gcp_hi)


# =========================================================================
# ASCE 7-22 Fig. 30.7-1 — Domed roofs (rise/diameter ratio f/D)
# Three zones: A (windward base), B (centre/apex), C (leeward base).
# Linearised envelopes for 0.05 ≤ f/D ≤ 0.5.
# FIXME: verify exact Cp distribution from Fig. 30.7-1
# =========================================================================
def domed_roof_GCp(f_over_D: float,
                   area_eff_m2: float,
                   zone: str,
                   sign: str = "neg") -> float:
    """
    Approximate GCp on a domed/arched roof per ASCE 7-22 Fig. 30.7-1.
    Zones: 'A' windward base, 'B' centre, 'C' leeward base.
    """
    if not 0.0 < f_over_D <= 0.6:
        raise ValueError(
            f"f/D={f_over_D} outside reasonable dome range (0,0.6]")
    # Base Cp at each zone (gust effect G=0.85 applied to get GCp envelope)
    # Linear in f/D between 0.05 and 0.5
    fd = max(0.05, min(0.5, f_over_D))
    t = (fd - 0.05) / (0.5 - 0.05)
    if zone == "A":
        # Windward: from -0.9 (f/D=0.05) to +0.4 (f/D=0.5) — sign flips
        cp_pos = -0.10 + t * (0.40 - (-0.10))
        cp_neg = -0.90 + t * (-0.20 - (-0.90))
    elif zone == "B":
        cp_pos = 0.0
        cp_neg = -1.10 + t * (-0.70 - (-1.10))
    elif zone == "C":
        cp_pos = 0.0
        cp_neg = -0.50 + t * (-0.30 - (-0.50))
    else:
        raise ValueError(f"Zone '{zone}' invalid for dome (use A/B/C)")
    G = 0.85
    val = G * (cp_pos if sign == "pos" else cp_neg)
    # Area reduction: small for curved roofs, apply mild log-interp
    # toward 80 % of the 10ft² value at 500ft².
    return _log_interp_area(area_eff_m2, val, val * 0.85)


# =========================================================================
# Mansard roof — ASCE 7-22 Fig. 30.3-2D
# Sloped surfaces treated like gable; the top flat surface treated as flat.
# =========================================================================
def mansard_roof_GCp(theta_deg: float,
                     area_eff_m2: float,
                     zone: str,
                     sign: str = "neg") -> float:
    """
    GCp for the sloped surfaces of a mansard roof (Fig. 30.3-2D).
    Top flat portion: use the regular low-slope table directly.
    """
    if theta_deg <= 0 or theta_deg > 75:
        raise GeometryError("Mansard slope must be in (0, 75] deg")
    # For the top flat surface zone numbering is identical to low-slope
    if theta_deg < 3.0:
        return asce7_GCp(zone, area_eff_m2, "roof", sign)
    # Sloped surfaces → reuse gable values (Fig. 30.3-2D notes this equivalence)
    eq_zone_map = {"1": "1", "2": "2e", "3": "3"}
    g_zone = eq_zone_map.get(zone, zone)
    return gable_roof_GCp(min(theta_deg, 45.0), area_eff_m2, g_zone, sign)


# =========================================================================
# Parapets — ASCE 7-22 §30.9
# A perimeter parapet of height hp [m] applied above a low roof produces
# an additional GCp on the windward edge / corner zones, computed as
#       GCp_p = GCp_main · K_p
# with K_p increasing with hp (capped at hp ≈ 1.5 m for practical use).
# =========================================================================
def parapet_pressure(h_parapet: float,
                     qz: float,
                     GCp_main_neg: float = -1.10,
                     GCp_main_pos: float = +0.90) -> dict:
    """
    Parapet pressure adjustment per ASCE 7-22 §30.9.

    Approximation:
        K_p = min(1.0 + 0.5 · hp,  1.5)        hp in metres
        GCp_p_neg = GCp_main_neg · K_p
        GCp_p_pos = GCp_main_pos · K_p
        p_parapet = qz · GCp_p

    Parameters
    ----------
    h_parapet     : parapet height above roof [m]
    qz            : velocity pressure at top of parapet [Pa]
    GCp_main_neg  : main suction GCp on adjacent edge zone (default -1.1)
    GCp_main_pos  : main positive GCp on adjacent edge zone (default +0.9)
    """
    if h_parapet < 0:
        raise ValueError("Parapet height must be ≥ 0")
    Kp = min(1.0 + 0.5 * h_parapet, 1.5)
    GCp_neg = GCp_main_neg * Kp
    GCp_pos = GCp_main_pos * Kp
    p_neg = qz * GCp_neg
    p_pos = qz * GCp_pos
    return {
        "h_parapet_m": round(h_parapet, 3),
        "K_p": round(Kp, 3),
        "GCp_parapet_neg": round(GCp_neg, 3),
        "GCp_parapet_pos": round(GCp_pos, 3),
        "p_parapet_neg_Pa": round(p_neg, 1),
        "p_parapet_pos_Pa": round(p_pos, 1),
        "p_design_Pa": round(max(abs(p_pos), abs(p_neg)), 1),
    }


# =========================================================================
# EN 1991-1-4 §7.2.5 — Duopitch roofs, Table 7.4a (wind θ = 0°) and
# Table 7.4b (wind θ = 90°); §7.2.4 — Monopitch roofs, Table 7.3a (θ = 0°
# and θ = 180°). Recommended values, positive pitch angles 5° to 75°.
#
# Each entry is (cpe,10, cpe,1); where the table gives a single value it is
# used for both. At θ = 0° the tables give a suction branch ("neg") and a
# pressure branch ("pos") for 5° to 45°; for zones or pitches with a single
# value both branches carry it. Values transcribed from EN 1991-1-4:2005+A1:2010
# pages 42 and 45-46. Before 1.2.0 these tables were an unverified mixture
# (e.g. duopitch 15° F = -1.3/-2.0, which is the θ = 90° value, and 45°
# F = 0.0 → +0.7 between 1 and 10 m², mixing the two branches).
# =========================================================================
_EC1_DUO_0 = {
    # pitch: zone: {"neg": (cpe10, cpe1), "pos": (cpe10, cpe1)}
    5.0: {"F": {"neg": (-1.7, -2.5), "pos": (0.0, 0.0)},
          "G": {"neg": (-1.2, -2.0), "pos": (0.0, 0.0)},
          "H": {"neg": (-0.6, -1.2), "pos": (0.0, 0.0)},
          "I": {"neg": (-0.6, -0.6), "pos": (-0.6, -0.6)},
          "J": {"neg": (-0.6, -0.6), "pos": (0.2, 0.2)}},
    15.0: {"F": {"neg": (-0.9, -2.0), "pos": (0.2, 0.2)},
           "G": {"neg": (-0.8, -1.5), "pos": (0.2, 0.2)},
           "H": {"neg": (-0.3, -0.3), "pos": (0.2, 0.2)},
           "I": {"neg": (-0.4, -0.4), "pos": (0.0, 0.0)},
           "J": {"neg": (-1.0, -1.5), "pos": (0.0, 0.0)}},
    30.0: {"F": {"neg": (-0.5, -1.5), "pos": (0.7, 0.7)},
           "G": {"neg": (-0.5, -1.5), "pos": (0.7, 0.7)},
           "H": {"neg": (-0.2, -0.2), "pos": (0.4, 0.4)},
           "I": {"neg": (-0.4, -0.4), "pos": (0.0, 0.0)},
           "J": {"neg": (-0.5, -0.5), "pos": (0.0, 0.0)}},
    45.0: {"F": {"neg": (0.0, 0.0), "pos": (0.7, 0.7)},
           "G": {"neg": (0.0, 0.0), "pos": (0.7, 0.7)},
           "H": {"neg": (0.0, 0.0), "pos": (0.6, 0.6)},
           "I": {"neg": (-0.2, -0.2), "pos": (0.0, 0.0)},
           "J": {"neg": (-0.3, -0.3), "pos": (0.0, 0.0)}},
    60.0: {"F": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)},
           "G": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)},
           "H": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)},
           "I": {"neg": (-0.2, -0.2), "pos": (-0.2, -0.2)},
           "J": {"neg": (-0.3, -0.3), "pos": (-0.3, -0.3)}},
    75.0: {"F": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)},
           "G": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)},
           "H": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)},
           "I": {"neg": (-0.2, -0.2), "pos": (-0.2, -0.2)},
           "J": {"neg": (-0.3, -0.3), "pos": (-0.3, -0.3)}},
}

_EC1_DUO_90 = {
    # pitch: zone: (cpe10, cpe1) — Table 7.4b (zones F, G, H, I)
    5.0: {"F": (-1.6, -2.2), "G": (-1.3, -2.0), "H": (-0.7, -1.2), "I": (-0.6, -0.6)},
    15.0: {"F": (-1.3, -2.0), "G": (-1.3, -2.0), "H": (-0.6, -1.2), "I": (-0.5, -0.5)},
    30.0: {"F": (-1.1, -1.5), "G": (-1.4, -2.0), "H": (-0.8, -1.2), "I": (-0.5, -0.5)},
    45.0: {"F": (-1.1, -1.5), "G": (-1.4, -2.0), "H": (-0.9, -1.2), "I": (-0.5, -0.5)},
    60.0: {"F": (-1.1, -1.5), "G": (-1.2, -2.0), "H": (-0.8, -1.0), "I": (-0.5, -0.5)},
    75.0: {"F": (-1.1, -1.5), "G": (-1.2, -2.0), "H": (-0.8, -1.0), "I": (-0.5, -0.5)},
}

_EC1_MONO_0 = {
    # Table 7.3a, θ = 0° (zones F, G, H)
    5.0: {"F": {"neg": (-1.7, -2.5), "pos": (0.0, 0.0)},
          "G": {"neg": (-1.2, -2.0), "pos": (0.0, 0.0)},
          "H": {"neg": (-0.6, -1.2), "pos": (0.0, 0.0)}},
    15.0: {"F": {"neg": (-0.9, -2.0), "pos": (0.2, 0.2)},
           "G": {"neg": (-0.8, -1.5), "pos": (0.2, 0.2)},
           "H": {"neg": (-0.3, -0.3), "pos": (0.2, 0.2)}},
    30.0: {"F": {"neg": (-0.5, -1.5), "pos": (0.7, 0.7)},
           "G": {"neg": (-0.5, -1.5), "pos": (0.7, 0.7)},
           "H": {"neg": (-0.2, -0.2), "pos": (0.4, 0.4)}},
    45.0: {"F": {"neg": (0.0, 0.0), "pos": (0.7, 0.7)},
           "G": {"neg": (0.0, 0.0), "pos": (0.7, 0.7)},
           "H": {"neg": (0.0, 0.0), "pos": (0.6, 0.6)}},
    60.0: {"F": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)},
           "G": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)},
           "H": {"neg": (0.7, 0.7), "pos": (0.7, 0.7)}},
    75.0: {"F": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)},
           "G": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)},
           "H": {"neg": (0.8, 0.8), "pos": (0.8, 0.8)}},
}

_EC1_MONO_180 = {
    # Table 7.3a, θ = 180° (zones F, G, H)
    5.0: {"F": (-2.3, -2.5), "G": (-1.3, -2.0), "H": (-0.8, -1.2)},
    15.0: {"F": (-2.5, -2.8), "G": (-1.3, -2.0), "H": (-0.9, -1.2)},
    30.0: {"F": (-1.1, -2.3), "G": (-0.8, -1.5), "H": (-0.8, -0.8)},
    45.0: {"F": (-0.6, -1.3), "G": (-0.5, -0.5), "H": (-0.7, -0.7)},
    60.0: {"F": (-0.5, -1.0), "G": (-0.5, -0.5), "H": (-0.5, -0.5)},
    75.0: {"F": (-0.5, -1.0), "G": (-0.5, -0.5), "H": (-0.5, -0.5)},
}


def _ec1_pitch_pair(theta: float, table: dict, zone: str,
                    branch: str | None = None) -> tuple[float, float]:
    """(cpe10, cpe1) linearly interpolated in pitch; clamped to 5°-75°."""
    def _get(pitch: float) -> tuple[float, float]:
        v = table[pitch][zone]
        return v[branch] if branch is not None else v
    pitches = sorted(table.keys())
    if theta <= pitches[0]:
        return _get(pitches[0])
    if theta >= pitches[-1]:
        return _get(pitches[-1])
    for p_lo, p_hi in zip(pitches[:-1], pitches[1:]):
        if p_lo <= theta <= p_hi:
            t = (theta - p_lo) / (p_hi - p_lo)
            lo, hi = _get(p_lo), _get(p_hi)
            return (lo[0] + t * (hi[0] - lo[0]), lo[1] + t * (hi[1] - lo[1]))
    return _get(pitches[-1])


def _ec1_area_interp(cpe10: float, cpe1: float, A: float) -> float:
    """EN 1991-1-4 Figure 7.2: cpe = cpe,1 − (cpe,1 − cpe,10)·log10(A)."""
    if A <= 1.0:
        return cpe1
    if A >= 10.0:
        return cpe10
    return cpe1 - (cpe1 - cpe10) * math.log10(A)


def ec1_gable_cpe(theta_deg: float, zone: str, A: float,
                  wind_dir: int = 0, case: str = "neg") -> float:
    """
    cpe for duopitch roofs, EN 1991-1-4 Tables 7.4a (θ = 0°, zones F-J) and
    7.4b (θ = 90°, zones F-I), positive pitch 5° to 75° (clamped outside),
    linear interpolation in pitch and log interpolation in area.

    wind_dir : 0 (Table 7.4a) or 90 (Table 7.4b).
    case     : θ = 0° only — 'neg' (suction branch, default) or 'pos'
               (pressure branch); Note 1 to Table 7.4a asks for both.
    Negative pitches and the flat-roof rule for -5° < α < 5° are not covered.
    """
    if wind_dir == 0:
        if zone not in ("F", "G", "H", "I", "J"):
            raise ValueError(f"Zone '{zone}' invalid for EC1 duopitch roof (θ=0°).")
        if case not in ("neg", "pos"):
            raise ValueError("case must be 'neg' or 'pos'")
        cpe10, cpe1 = _ec1_pitch_pair(theta_deg, _EC1_DUO_0, zone, case)
    elif wind_dir == 90:
        if zone not in ("F", "G", "H", "I"):
            raise ValueError(f"Zone '{zone}' invalid for EC1 duopitch roof (θ=90°).")
        cpe10, cpe1 = _ec1_pitch_pair(theta_deg, _EC1_DUO_90, zone)
    else:
        raise ValueError("wind_dir must be 0 or 90 for duopitch roofs")
    return _ec1_area_interp(cpe10, cpe1, A)


def ec1_monopitch_cpe(theta_deg: float, zone: str, A: float,
                      wind_dir: int = 0, case: str = "neg") -> float:
    """
    cpe for monopitch roofs, EN 1991-1-4 Table 7.3a (zones F, G, H for
    θ = 0° and θ = 180°), positive pitch 5° to 75° (clamped outside).

    wind_dir : 0 (wind on the low eave) or 180 (wind on the high eave).
    case     : θ = 0° only — 'neg' (suction branch, default) or 'pos'.
    Table 7.3b (θ = 90°, zones Fup/Flow/G/H/I) is not implemented.
    """
    if zone not in ("F", "G", "H"):
        raise ValueError(f"Zone '{zone}' invalid for EC1 monopitch roof.")
    if wind_dir == 0:
        if case not in ("neg", "pos"):
            raise ValueError("case must be 'neg' or 'pos'")
        cpe10, cpe1 = _ec1_pitch_pair(theta_deg, _EC1_MONO_0, zone, case)
    elif wind_dir == 180:
        cpe10, cpe1 = _ec1_pitch_pair(theta_deg, _EC1_MONO_180, zone)
    else:
        raise ValueError("wind_dir must be 0 or 180 for monopitch roofs")
    return _ec1_area_interp(cpe10, cpe1, A)


# =========================================================================
# EN 1991-1-4 §7.2.7 — Cylindrical / spherical (domed) roofs.
# Simplified envelope as a function of f/d (rise / diameter).
# FIXME: verify against EN 1991-1-4 Fig. 7.11/7.12
# =========================================================================
def ec1_cylindrical_cpe(f_over_d: float, zone: str) -> float:
    """
    cpe for domed roofs (zones A windward, B centre, C leeward) per EN 1991-1-4
    §7.2.7. Linear envelope between f/d=0.05 and f/d=0.5.
    """
    if not 0.0 < f_over_d <= 0.5:
        raise ValueError("f/d must be in (0, 0.5]")
    t = (max(0.05, f_over_d) - 0.05) / (0.5 - 0.05)
    if zone == "A":
        return -0.8 + t * (0.4 - (-0.8))   # -0.8 → +0.4
    if zone == "B":
        return -1.2 + t * (-0.7 - (-1.2))  # -1.2 → -0.7
    if zone == "C":
        return -0.4 + t * (-0.4 - (-0.4))  # ~ -0.4
    raise ValueError(f"Zone '{zone}' invalid (use A/B/C).")
