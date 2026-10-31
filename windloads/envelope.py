"""
envelope.py — MWFRS envelope method and story-level force distribution.

Distributes wind pressures into floor-level forces for structural analysis.
Supports EC1-1-4 and ASCE 7-22 envelope method.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field


@dataclass
class StoryWindForce:
    """Wind force resultant at a story level."""
    story: int
    z_bot: float    # bottom height [m]
    z_top: float    # top height [m]
    z_mid: float    # centroid height [m]
    qp_or_qz: float # peak pressure at story centroid [Pa]
    Fx: float       # horizontal force (windward direction) [kN]
    Fy: float = 0.0 # horizontal force (perpendicular) [kN]


@dataclass
class MWFRSEnvelope:
    """
    MWFRS (Main Wind Force Resisting System) envelope.

    Computes story-level wind forces for a rectangular building
    using either EC1 or ASCE 7 pressure distributions.

    Parameters
    ----------
    code        : 'EC1' or 'ASCE7' or 'NSR10'
    story_heights : list of story heights from ground up [m]
                   e.g. [3.5, 3.5, 3.5] for a 3-story building
    B           : building width perpendicular to wind [m]
    D           : building depth parallel to wind [m]
    """
    code: str
    story_heights: list[float]
    B: float  # width [m]
    D: float  # depth [m]

    def __post_init__(self) -> None:
        self.code = self.code.upper()
        self._floors_z = np.cumsum([0.0] + list(self.story_heights))
        self.H = float(self._floors_z[-1])  # total height

    # ------------------------------------------------------------------
    # EC1 story forces
    # ------------------------------------------------------------------
    def ec1_story_forces(self, terrain_profile,
                          vb: float,
                          Cs_Cd: float = 1.0) -> list[StoryWindForce]:
        """
        Compute story-level wind forces using EC1-1-4 §5.3.

        Parameters
        ----------
        terrain_profile : TerrainProfile  (must be code='EC1')
        vb : float  basic wind velocity [m/s]
        Cs_Cd : float  structural factor (default 1.0 for rigid)

        Returns
        -------
        list of StoryWindForce objects
        """
        from .pressure import ec1_cpe_walls

        cpe = ec1_cpe_walls(self.H, self.D)
        cpe_windward = cpe["D"]
        cpe_leeward  = cpe["E"]

        results = []
        floors = self._floors_z
        for i, h in enumerate(self.story_heights):
            z_bot = floors[i]
            z_top = floors[i + 1]
            z_mid = 0.5 * (z_bot + z_top)

            # reference height = z_top (conservative per EC1 §7.2.2)
            qp = terrain_profile.ec1_peak_velocity_pressure(z_top, vb)

            # Net pressure: windward + leeward (combined)
            w_net = qp * (cpe_windward - (-0.3))  # typical internal
            # Force on story tributary area
            A_trib = self.B * h        # tributary area [m²]
            Fx = Cs_Cd * w_net * A_trib / 1000  # [kN]

            results.append(StoryWindForce(
                story=i + 1,
                z_bot=z_bot,
                z_top=z_top,
                z_mid=z_mid,
                qp_or_qz=round(qp, 2),
                Fx=round(Fx, 2),
            ))
        return results

    # ------------------------------------------------------------------
    # ASCE 7 / NSR-10 story forces
    # ------------------------------------------------------------------
    def asce7_story_forces(self, terrain_profile,
                            V: float,
                            Kd: float = 0.85,
                            Kzt: float = 1.0,
                            G: float = 0.85,
                            enclosure: str = "enclosed") -> list[StoryWindForce]:
        """
        Compute story-level wind forces using ASCE 7-22 §27.3 directional method.

        Parameters
        ----------
        terrain_profile : TerrainProfile  (code='ASCE7' or 'NSR10')
        V : float  basic wind speed [m/s]
        Kd : float  directionality factor
        Kzt : float  topographic factor
        G : float  gust factor (0.85 for rigid)
        enclosure : str  'enclosed' | 'partially_enclosed' | 'open'
        """
        from .pressure import asce7_Cp_walls, _ASCE7_GCPI, _NSR10_GCPI

        Cp = asce7_Cp_walls(self.D, self.B, self.H)
        GCpi_map = _ASCE7_GCPI if self.code == "ASCE7" else _NSR10_GCPI
        GCpi_pos, _ = GCpi_map[enclosure]

        # qh at mean roof height
        fn = terrain_profile.asce7_velocity_pressure if self.code == "ASCE7" \
             else terrain_profile.nsr10_velocity_pressure
        qh = fn(self.H, V, Kd=Kd, Kzt=Kzt)

        results = []
        floors = self._floors_z
        for i, h in enumerate(self.story_heights):
            z_top = floors[i + 1]
            z_mid = 0.5 * (floors[i] + z_top)

            qz = fn(z_top, V, Kd=Kd, Kzt=Kzt)

            # Windward: varies with height (use qz)
            p_ww = qz * G * Cp["windward"] - qh * GCpi_pos
            # Leeward: uniform at qh
            p_lw = qh * G * Cp["leeward"] - qh * GCpi_pos

            p_net = p_ww - p_lw   # combined net
            A_trib = self.B * h
            Fx = p_net * A_trib / 1000  # kN

            results.append(StoryWindForce(
                story=i + 1,
                z_bot=floors[i],
                z_top=z_top,
                z_mid=z_mid,
                qp_or_qz=round(qz, 2),
                Fx=round(Fx, 2),
            ))
        return results

    def total_base_shear(self, story_forces: list[StoryWindForce]) -> float:
        """Total base shear Vb [kN]."""
        return round(sum(f.Fx for f in story_forces), 2)

    def overturning_moment(self, story_forces: list[StoryWindForce]) -> float:
        """Overturning moment at base OTM [kN·m]."""
        return round(sum(f.Fx * f.z_mid for f in story_forces), 2)

    def summary(self, story_forces: list[StoryWindForce]) -> dict:
        """Summary of wind load results."""
        return {
            "code": self.code,
            "H_m": self.H,
            "B_m": self.B,
            "D_m": self.D,
            "n_stories": len(story_forces),
            "Vb_kN": self.total_base_shear(story_forces),
            "OTM_kNm": self.overturning_moment(story_forces),
            "story_forces": [
                {
                    "story": f.story,
                    "z_top_m": f.z_top,
                    "qp_Pa": f.qp_or_qz,
                    "Fx_kN": f.Fx,
                }
                for f in story_forces
            ],
        }
