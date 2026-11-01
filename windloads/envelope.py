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
    qp_or_qz: float # EC1: qp(ze) windward; ASCE 7 / NSR-10: qz(z_top) [Pa]
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
                          Cs_Cd: float = 1.0,
                          rho: float = 1.25) -> list[StoryWindForce]:
        """
        Story-level wind forces from the wall pressures of EN 1991-1-4 §7.2.2
        (zones D and E acting simultaneously, §5.3 with Aref = B·h_story):

            F_story = cs·cd · f_corr · (cpe,D · qp(ze) − cpe,E · qp(h)) · B · h_story

        * ze is the reference height of the windward wall (Figure 7.4:
          ze = h if h <= b; ze = b below z = b and h above when b < h <= 2b;
          strips at the story top in the middle region when h > 2b), with
          b = B the crosswind dimension;
        * the leeward wall uses qp(h) (recommended procedure, Note to 7.2.2(1));
        * f_corr is the lack-of-correlation factor of §7.2.2(3): 0.85 for
          h/d <= 1, 1.0 for h/d >= 5, linear in between;
        * internal pressure cancels for the whole building and is not included.

        Before 1.2.0 the force used qp(z_top)·(cpe,D + 0.3): the leeward cpe was
        computed but not used, the internal-pressure coefficient (-0.3) was
        subtracted on the windward face only, and the lack of correlation and
        the ze rules were ignored.

        Parameters
        ----------
        terrain_profile : TerrainProfile  (must be code='EC1')
        vb : float  basic wind velocity [m/s]
        Cs_Cd : float  structural factor (default 1.0 for rigid)
        rho : float  air density [kg/m³]

        Returns
        -------
        list of StoryWindForce objects; ``qp_or_qz`` is qp(ze) of the windward
        wall [Pa].
        """
        from .pressure import (
            ec1_cpe_walls,
            ec1_lack_of_correlation_factor,
            ec1_windward_reference_height,
        )

        cpe = ec1_cpe_walls(self.H, self.D)
        cpe_windward = cpe["D"]
        cpe_leeward = cpe["E"]
        f_corr = ec1_lack_of_correlation_factor(self.H, self.D)
        qp_h = terrain_profile.ec1_peak_velocity_pressure(self.H, vb, rho)

        results = []
        floors = self._floors_z
        for i, h in enumerate(self.story_heights):
            z_bot = floors[i]
            z_top = floors[i + 1]
            z_mid = 0.5 * (z_bot + z_top)

            ze = ec1_windward_reference_height(z_top, self.H, self.B)
            qp_ze = terrain_profile.ec1_peak_velocity_pressure(ze, vb, rho)

            w_net = f_corr * (cpe_windward * qp_ze - cpe_leeward * qp_h)
            A_trib = self.B * h        # tributary area [m²]
            Fx = Cs_Cd * w_net * A_trib / 1000  # [kN]

            results.append(StoryWindForce(
                story=i + 1,
                z_bot=z_bot,
                z_top=z_top,
                z_mid=z_mid,
                qp_or_qz=round(qp_ze, 2),
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
