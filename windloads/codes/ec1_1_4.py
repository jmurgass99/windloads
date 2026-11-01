"""
ec1_1_4.py — High-level API for EN 1991-1-4 wind load calculations.

Reference: EN 1991-1-4:2005 + A1:2010
"""
from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass
from ..terrain import TerrainProfile
from ..terrain._impl import _EC1_TERRAIN
from ..pressure import WindPressure, ec1_cpe_walls
from ..envelope import MWFRSEnvelope


def ec1_structural_factor_cscd(
    h: float,
    b: float,
    d: float,
    vm_zs: float,
    Iv_zs: float,
    z_s: float | None = None,
    z0: float = 0.05,
    n1_x: float | None = None,
    delta_s: float = 0.05,
) -> dict[str, float]:
    """Structural factor ``c_s c_d`` per EN 1991-1-4 §6.3.1 & Annex B (Procedure 1).

    Implements:
      - Eq. (B.1): Turbulence length scale L(z_s) = L_t · (z_s / z_t)^α
      - Eq. (B.3): Background factor B² = 1 / [1 + 0.9 · ((b + h) / L(z_s))^0.63]
      - Eq. (F.2): Fundamental flexural frequency n_{1,x} = 46 / h [Hz] (if not supplied)
      - Eq. (B.2): Non-dimensional power spectral density S_L(z_s, n_{1,x})
      - Eqs. (B.6)–(B.8): Aerodynamic admittance R_h, R_b and resonance response factor R²
      - Eqs. (B.4)–(B.5): Up-crossing frequency ν and peak factor k_p
      - Eqs. (6.1)–(6.3): c_s, c_d, and combined c_s c_d
    """
    if z_s is None:
        z_s = max(0.6 * h, 2.0)
    z_t = 200.0
    L_t = 300.0
    alpha = 0.67 + 0.05 * math.log(max(z0, 1e-4))
    L_zs = L_t * (max(z_s, 1.0) / z_t) ** alpha

    B2 = 1.0 / (1.0 + 0.9 * ((b + h) / L_zs) ** 0.63)

    if n1_x is None or n1_x <= 0.0:
        n1_x = 46.0 / max(h, 1.0)

    f_L = n1_x * L_zs / max(vm_zs, 1e-6)
    S_L = (6.8 * f_L) / ((1.0 + 10.2 * f_L) ** (5.0 / 3.0))

    eta_h = 4.6 * h * f_L / L_zs
    eta_b = 4.6 * b * f_L / L_zs
    R_h = (1.0 / eta_h - (1.0 - math.exp(-2.0 * eta_h)) / (2.0 * eta_h**2)) if eta_h > 1e-6 else 1.0
    R_b = (1.0 / eta_b - (1.0 - math.exp(-2.0 * eta_b)) / (2.0 * eta_b**2)) if eta_b > 1e-6 else 1.0

    # Logarithmic decrement of damping δ = δ_s + δ_a (Annex F §F.5)
    delta = max(delta_s, 0.01)
    R2 = (math.pi**2 / (2.0 * delta)) * S_L * R_h * R_b

    nu = n1_x * math.sqrt(R2 / max(B2 + R2, 1e-12))
    nu = max(nu, 0.08)
    T_avg = 600.0
    ln_nuT = max(2.0 * math.log(nu * T_avg), 1e-6)
    k_p = max(math.sqrt(ln_nuT) + 0.6 / math.sqrt(ln_nuT), 3.0)

    denom = 1.0 + 7.0 * Iv_zs
    c_s = (1.0 + 7.0 * Iv_zs * math.sqrt(B2)) / denom
    c_d = (1.0 + 2.0 * k_p * Iv_zs * math.sqrt(B2 + R2)) / (1.0 + 7.0 * Iv_zs * math.sqrt(B2))
    cs_cd = (1.0 + 2.0 * k_p * Iv_zs * math.sqrt(B2 + R2)) / denom

    return {
        "cs_cd": float(cs_cd),
        "c_s": float(c_s),
        "c_d": float(c_d),
        "B2": float(B2),
        "R2": float(R2),
        "k_p": float(k_p),
        "nu_Hz": float(nu),
        "n1_x_Hz": float(n1_x),
        "L_zs_m": float(L_zs),
        "z_s_m": float(z_s),
    }


@dataclass
class EC1WindLoad:
    """
    Complete EC1-1-4 wind load calculation for a rectangular building.
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
    c_o: float = 1.0
    orography_params: dict | None = None
    compute_cscd_annex_b: bool = False
    n1_x_Hz: float | None = None
    delta_s: float = 0.05

    def __post_init__(self) -> None:
        if self.enclosure != "closed":
            from ..exceptions import ConfigurationError
            raise ConfigurationError(
                f"enclosure={self.enclosure!r} not implemented: only 'closed' "
                "(cpi +0.2/-0.3). With a dominant opening cpi = 0.75 or 0.90 "
                "x cpe of that face (EN 1991-1-4 §7.2.9(3)).")
        if self.story_heights is None:
            self.story_heights = [self.building_height]

        self._terrain = TerrainProfile(
            code="EC1",
            category=self.terrain_cat,
            c_o=self.c_o,
            orography_params=self.orography_params,
        )

        # EN 1991-1-4 §6.2 & §6.3: Factor estructural Cs_Cd
        self._cscd_details: dict[str, float] | None = None
        if self.Cs_Cd is not None:
            self._Cs_Cd_val = float(self.Cs_Cd)
            self._Cs_Cd_status = "explicit_user_input"
            self._Cs_Cd_justified = True
        elif self.compute_cscd_annex_b:
            p = _EC1_TERRAIN[self.terrain_cat]
            z_s = max(0.6 * self.building_height, p["zmin"])
            vm_zs = self._terrain.ec1_mean_wind_velocity(z_s, self.vb_design)
            Iv_zs = self._terrain.ec1_turbulence_intensity(z_s)
            self._cscd_details = ec1_structural_factor_cscd(
                h=self.building_height,
                b=self.width,
                d=self.depth,
                vm_zs=vm_zs,
                Iv_zs=Iv_zs,
                z_s=z_s,
                z0=p["z0"],
                n1_x=self.n1_x_Hz,
                delta_s=self.delta_s,
            )
            self._Cs_Cd_val = round(self._cscd_details["cs_cd"], 4)
            self._Cs_Cd_status = "computed_en1991_1_4_annex_b"
            self._Cs_Cd_justified = True
        elif self.building_height <= 15.0:
            self._Cs_Cd_val = 1.0
            self._Cs_Cd_status = "justified_low_rise_h_le_15m (EN 1991-1-4 §6.2(1) Nota 1a)"
            self._Cs_Cd_justified = True
        else:
            self._Cs_Cd_val = 1.0
            self._Cs_Cd_status = "unverified_default_h_gt_15m (requiere cálculo dinámico §6.3 o Anexo B/C)"
            self._Cs_Cd_justified = False

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
        """
        qp_h = self.qp_at(self.building_height)
        wp = WindPressure(code="EC1", enclosure=self.enclosure)
        return wp.ec1_wall_pressures(qp_h, self.building_height, self.depth)

    def story_forces(self) -> list:
        """Story-level wind forces [kN] per floor."""
        return self._envelope.ec1_story_forces(
            self._terrain, self.vb_design, self._Cs_Cd_val, self.rho
        )

    def pressure_profile(self, n_points: int = 20) -> list[dict]:
        """
        qp(z) profile from 0 to H at n_points heights.
        """
        heights = np.linspace(0.1, self.building_height, n_points)
        profile = []
        for z in heights:
            vm = self._terrain.ec1_mean_wind_velocity(z, self.vb_design)
            qp = self.qp_at(z)
            profile.append({
                "z_m": round(float(z), 2),
                "cr": round(self._terrain.ec1_roughness_factor(float(z)), 4),
                "co": round(self._terrain.ec1_orography_factor(float(z)), 4),
                "Iv": round(self._terrain.ec1_turbulence_intensity(float(z)), 4),
                "vm_ms": round(vm, 2),
                "qp_Pa": round(qp, 2),
                "qp_kPa": round(qp / 1000, 4),
            })
        return profile

    def compute(self) -> dict:
        """
        Full EC1-1-4 wind load calculation.
        """
        sf = self.story_forces()
        fp = self.facade_pressures()
        out = {
            "code": "EC1-1-4:2005",
            "terrain_category": self.terrain_cat,
            "vb_0_ms": self.vb,
            "vb_design_ms": round(self.vb_design, 2),
            "H_m": self.building_height,
            "B_m": self.width,
            "D_m": self.depth,
            "qp_top_Pa": round(self.qp_at(self.building_height), 2),
            "co_top": round(self._terrain.ec1_orography_factor(self.building_height), 4),
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
        if self._cscd_details is not None:
            out["Cs_Cd_details"] = self._cscd_details
        return out
