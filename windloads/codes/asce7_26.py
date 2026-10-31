"""
asce7_26.py — High-level API for ASCE 7-22 wind load (Chapters 26-27).

Reference: ASCE/SEI 7-22, Chapters 26 (General) and 27 (MWFRS Directional)
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from ..terrain import TerrainProfile
from ..pressure import WindPressure
from ..envelope import MWFRSEnvelope


# ASCE 7-22 §26.6: Directionality factor Kd
KD_TABLE: dict[str, float] = {
    "building_mwfrs": 0.85,
    "building_cc": 0.85,
    "arched_roof": 0.85,
    "chimney_square": 0.90,
    "chimney_hex_oct": 0.95,
    "chimney_round": 0.95,
    "solid_freestanding": 0.85,
    "solid_sign": 0.85,
    "open_sign": 0.85,
    "trussed_tower_triangular": 0.85,
    "trussed_tower_square_diagonal": 0.85,
}

# ASCE 7-22 §26.11: Gust Factor G for rigid buildings
G_RIGID = 0.85   # for natural frequency ≥ 1 Hz


@dataclass
class ASCE7WindLoad:
    """
    Complete ASCE 7-22 wind load (Chapters 26-27) for a rectangular building
    using the MWFRS Directional Method (Chapter 27).

    Parameters
    ----------
    V : float
        Basic wind speed V [m/s] (from ASCE 7-22 Fig. 26.5-1A/B/C per risk category).
    exposure : str
        Exposure category: 'B', 'C', or 'D'.
    building_height : float
        Mean roof height h [m].
    width : float
        Building dimension B perpendicular to wind [m].
    depth : float
        Building dimension L parallel to wind [m].
    story_heights : list[float], optional
        Individual story heights [m] bottom-to-top.
    risk_category : str
        'I', 'II', 'III', or 'IV' (controls V from wind speed map).
    enclosure : str
        'enclosed', 'partially_enclosed', or 'open'.
    Kzt : float
        Topographic factor (default 1.0 flat terrain).
    Kd : float
        Directionality factor (default 0.85 for MWFRS).
    G : float
        Gust factor (default 0.85 for rigid buildings).

    Examples
    --------
    >>> wl = ASCE7WindLoad(V=40.0, exposure='C', building_height=18.0,
    ...                    width=15.0, depth=12.0,
    ...                    story_heights=[3.0]*6)
    >>> r = wl.compute()
    >>> print(f"Base shear: {r['Vb_kN']} kN")
    """
    V: float
    exposure: str
    building_height: float
    width: float = 20.0
    depth: float = 15.0
    story_heights: list[float] | None = None
    risk_category: str = "II"
    enclosure: str = "enclosed"
    Kzt: float = 1.0
    Kd: float = 0.85
    G: float = G_RIGID

    def __post_init__(self) -> None:
        self.exposure = self.exposure.upper()
        if self.story_heights is None:
            self.story_heights = [self.building_height]
        self._terrain = TerrainProfile(code="ASCE7", category=self.exposure)
        self._envelope = MWFRSEnvelope(
            code="ASCE7",
            story_heights=self.story_heights,
            B=self.width,
            D=self.depth,
        )

    def qz_at(self, z: float) -> float:
        """Velocity pressure qz [Pa] at height z."""
        return self._terrain.asce7_velocity_pressure(
            z, self.V, Kd=self.Kd, Kzt=self.Kzt
        )

    @property
    def qh(self) -> float:
        """Velocity pressure qh [Pa] at mean roof height."""
        return self.qz_at(self.building_height)

    def facade_pressures(self) -> dict:
        """
        Net MWFRS wall pressures [kPa] at mean roof height (conservative).

        Returns dict with keys: windward, leeward, side.
        Each has: Cp, p_net_pos_kPa, p_net_neg_kPa.
        """
        wp = WindPressure(code="ASCE7", enclosure=self.enclosure)
        qz = self.qh  # conservative: use qh for all surfaces
        return wp.asce7_wall_pressures(
            qz, self.qh, self.depth, self.width, self.building_height, self.G
        )

    def Kz_table(self) -> list[dict]:
        """
        Velocity pressure coefficient Kz table at standard heights.
        """
        heights = [0, 4.6, 6.1, 7.6, 9.1, 12.2, 15.2, 18.0, 21.3, 24.4,
                   27.4, 30.5, 36.6, 42.7, 48.8, 54.9, 61.0]
        return self._terrain.profile_table(
            [h for h in heights if h <= self.building_height + 1],
            self.V, Kd=self.Kd, Kzt=self.Kzt
        )

    def story_forces(self) -> list:
        """Story-level wind forces [kN] per floor."""
        return self._envelope.asce7_story_forces(
            self._terrain, self.V,
            Kd=self.Kd, Kzt=self.Kzt,
            G=self.G, enclosure=self.enclosure
        )

    def compute(self) -> dict:
        """
        Full ASCE 7-22 Chapter 27 MWFRS wind load calculation.

        Returns
        -------
        dict with all key parameters and results.
        """
        sf = self.story_forces()
        fp = self.facade_pressures()
        return {
            "code": "ASCE 7-22 Chapter 27 (MWFRS Directional)",
            "exposure_category": self.exposure,
            "risk_category": self.risk_category,
            "V_ms": self.V,
            "Kd": self.Kd,
            "Kzt": self.Kzt,
            "G": self.G,
            "enclosure": self.enclosure,
            "h_m": self.building_height,
            "B_m": self.width,
            "L_m": self.depth,
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
