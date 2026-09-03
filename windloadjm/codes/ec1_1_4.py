"""
ec1_1_4.py — High-level API for EN 1991-1-4 wind load calculations.

Reference: EN 1991-1-4:2005 + A1:2010
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from ..terrain import TerrainProfile
from ..pressure import WindPressure, ec1_cpe_walls
from ..envelope import MWFRSEnvelope


@dataclass
class EC1WindLoad:
    """
    Complete EC1-1-4 wind load calculation for a rectangular building.

    Parameters
    ----------
    vb : float
        Basic wind velocity vb,0 [m/s] (from national annex wind map).
    terrain_cat : str
        Terrain category: '0', 'I', 'II', 'III', or 'IV'.
    building_height : float
        Total building height H [m].
    width : float
        Building width B [m] (perpendicular to wind).
    depth : float
        Building depth D [m] (parallel to wind).
    story_heights : list[float], optional
        List of individual story heights [m] bottom-to-top.
        If not provided, assumed a single uniform story of height H.
    enclosure : str
        'closed' or 'open_one_face' (internal pressure classification).
    cdir : float
        Directional factor (default 1.0, national annex).
    cseason : float
        Season factor (default 1.0).
    Cs_Cd : float
        Structural factor (default 1.0 for rigid buildings with T < 1 s).

    Examples
    --------
    >>> wl = EC1WindLoad(vb=26.0, terrain_cat='II',
    ...                  building_height=18.0, width=15.0, depth=12.0,
    ...                  story_heights=[3.0, 3.0, 3.0, 3.0, 3.0, 3.0])
    >>> summary = wl.compute()
    >>> print(f"Base shear: {summary['Vb_kN']} kN")
    """
    vb: float
    terrain_cat: str
    building_height: float
    width: float = 20.0
    depth: float = 15.0
    story_heights: list[float] | None = None
    enclosure: str = "closed"
    cdir: float = 1.0
    cseason: float = 1.0
    Cs_Cd: float | None = None
    rho: float = 1.25  # air density [kg/m³]

    def __post_init__(self) -> None:
        if self.story_heights is None:
            self.story_heights = [self.building_height]

        # EN 1991-1-4 §6.2: Factor estructural Cs_Cd
        if self.Cs_Cd is not None:
            self._Cs_Cd_val = float(self.Cs_Cd)
            self._Cs_Cd_status = "explicit_user_input"
            self._Cs_Cd_justified = True
        elif self.building_height <= 15.0:
            self._Cs_Cd_val = 1.0
            self._Cs_Cd_status = "justified_low_rise_h_le_15m (EN 1991-1-4 §6.2(1) Nota 1a)"
            self._Cs_Cd_justified = True
        else:
            self._Cs_Cd_val = 1.0
            self._Cs_Cd_status = "unverified_default_h_gt_15m (requiere cálculo dinámico §6.3 o Anexo B/C)"
            self._Cs_Cd_justified = False

        self._terrain = TerrainProfile(code="EC1", category=self.terrain_cat)
        self._envelope = MWFRSEnvelope(
            code="EC1",
            story_heights=self.story_heights,
            B=self.width,
            D=self.depth,
        )

    @property
    def vb_design(self) -> float:
        """Design basic wind velocity: vb = cdir · cseason · vb,0 [m/s]"""
        return self.cdir * self.cseason * self.vb

    def qp_at(self, z: float) -> float:
        """Peak velocity pressure qp(z) [Pa] at height z."""
        return self._terrain.ec1_peak_velocity_pressure(
            z, self.vb_design, self.rho
        )

    def facade_pressures(self) -> dict:
        """
        Net wind pressures on all wall zones at reference height H [kPa].

        Returns
        -------
        dict keyed by wall zone (A-E) with sub-keys:
          cpe, w_net_pos_kPa, w_net_neg_kPa
        """
        qp_h = self.qp_at(self.building_height)
        wp = WindPressure(code="EC1", enclosure=self.enclosure)
        return wp.ec1_wall_pressures(qp_h, self.building_height, self.depth)

    def story_forces(self) -> list:
        """Story-level wind forces [kN] per floor."""
        return self._envelope.ec1_story_forces(
            self._terrain, self.vb_design, self._Cs_Cd_val
        )

    def pressure_profile(self, n_points: int = 20) -> list[dict]:
        """
        qp(z) profile from 0 to H at n_points heights.

        Returns list of {'z_m': ..., 'vm_ms': ..., 'qp_Pa': ..., 'qp_kPa': ...}
        """
        heights = np.linspace(0.1, self.building_height, n_points)
        profile = []
        for z in heights:
            vm = self._terrain.ec1_mean_wind_velocity(z, self.vb_design)
            qp = self.qp_at(z)
            profile.append({
                "z_m": round(z, 2),
                "cr": round(self._terrain.ec1_roughness_factor(z), 4),
                "Iv": round(self._terrain.ec1_turbulence_intensity(z), 4),
                "vm_ms": round(vm, 2),
                "qp_Pa": round(qp, 2),
                "qp_kPa": round(qp / 1000, 4),
            })
        return profile

    def compute(self) -> dict:
        """
        Full EC1-1-4 wind load calculation.

        Returns
        -------
        dict with keys:
          - code, terrain_cat, vb_design, H, B, D
          - qp_top_Pa  (peak pressure at roof)
          - facade_pressures  (all wall zones)
          - story_forces  (per floor)
          - Vb_kN  (total base shear)
          - OTM_kNm  (overturning moment at base)
        """
        sf = self.story_forces()
        fp = self.facade_pressures()
        return {
            "code": "EC1-1-4:2005",
            "terrain_category": self.terrain_cat,
            "vb_0_ms": self.vb,
            "vb_design_ms": round(self.vb_design, 2),
            "H_m": self.building_height,
            "B_m": self.width,
            "D_m": self.depth,
            "qp_top_Pa": round(self.qp_at(self.building_height), 2),
            "Cs_Cd": self._Cs_Cd_val,
            "Cs_Cd_status": self._Cs_Cd_status,
            "Cs_Cd_justified": self._Cs_Cd_justified,
            "facade_pressures": fp,
            "Vb_kN": self._envelope.total_base_shear(sf),
            "OTM_kNm": self._envelope.overturning_moment(sf),
            "story_forces": [
                {"story": f.story, "z_top_m": f.z_top,
                 "qp_Pa": f.qp_or_qz, "Fx_kN": f.Fx}
                for f in sf
            ],
        }
