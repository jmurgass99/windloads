"""
terrain.py — Terrain and exposure parameters for wind load calculations.

Covers:
  - EC1-1-4 §4.3: Terrain categories 0, I, II, III, IV
  - ASCE 7-22 §26.7: Exposure categories B, C, D
  - NSR-10 §B.6.5: Categorías de terreno A, B, C, D
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# EC1-1-4 Terrain Categories — Table 4.1
# ---------------------------------------------------------------------------
_EC1_TERRAIN: dict[str, dict] = {
    "0": {
        "description": "Sea or coastal area exposed to the open sea",
        "z0": 0.003,   # roughness length [m]
        "zmin": 1.0,   # min height [m]
    },
    "I": {
        "description": "Lakes or flat and horizontal area with negligible vegetation",
        "z0": 0.01,
        "zmin": 1.0,
    },
    "II": {
        "description": "Area with low vegetation (grass) and isolated obstacles",
        "z0": 0.05,
        "zmin": 2.0,
    },
    "III": {
        "description": "Area with regular cover of vegetation or buildings",
        "z0": 0.3,
        "zmin": 5.0,
    },
    "IV": {
        "description": "Area in which at least 15% of the surface is covered with buildings",
        "z0": 1.0,
        "zmin": 10.0,
    },
}

# ---------------------------------------------------------------------------
# ASCE 7-22 Exposure Categories — §26.7
# ---------------------------------------------------------------------------
_ASCE7_EXPOSURE: dict[str, dict] = {
    "B": {
        "description": "Urban/suburban areas, wooded areas (z0 ~ 0.3 m)",
        "alpha": 7.0,      # power law exponent (1/alpha)
        "zg": 365.76,      # gradient height [m]
        "At": 0.84,        # factor for Kz at z<=15ft
        "Bt": 1.0,         # turbulence factor
        "alpha_bar": 1/7,
        "b_bar": 0.45,
        "c": 0.30,
        "l_bar": 97.54,
        "eps_bar": 1/3,
    },
    "C": {
        "description": "Open terrain with scattered obstructions < 9 m",
        "alpha": 9.5,
        "zg": 274.32,
        "At": 1.00,
        "Bt": 1.0,
        "alpha_bar": 1/9.5,
        "b_bar": 0.65,
        "c": 0.20,
        "l_bar": 152.4,
        "eps_bar": 1/6.5,
    },
    "D": {
        "description": "Flat, unobstructed areas: water surfaces, salt flats",
        "alpha": 11.5,
        "zg": 213.36,
        "At": 1.07,
        "Bt": 1.0,
        "alpha_bar": 1/11.5,
        "b_bar": 0.80,
        "c": 0.15,
        "l_bar": 198.12,
        "eps_bar": 1/9,
    },
}

# ---------------------------------------------------------------------------
# NSR-10 B.6 Terrain Categories (similar to ASCE 7-16 with Colombian values)
# ---------------------------------------------------------------------------
_NSR10_TERRAIN: dict[str, dict] = {
    "A": {
        "description": "Zona costera o lacustre expuesta al viento libre",
        "Kz_15": 1.03, "alpha": 11.5, "zg": 213.36,
    },
    "B": {
        "description": "Zona con obstrucciones dispersas (cultivos, praderas)",
        "Kz_15": 0.85, "alpha": 9.5, "zg": 274.32,
    },
    "C": {
        "description": "Zona suburbana o con vegetación densa",
        "Kz_15": 0.62, "alpha": 7.0, "zg": 365.76,
    },
    "D": {
        "description": "Centro urbano con edificios altos",
        "Kz_15": 0.49, "alpha": 5.0, "zg": 457.20,
    },
}


@dataclass
class TerrainProfile:
    """
    Terrain parameters for wind speed profile calculations.

    Parameters
    ----------
    code : str
        Building code: 'EC1', 'ASCE7', 'NSR10'
    category : str
        Terrain/exposure category per selected code.
    z_ref : float, optional
        Reference height for reporting [m]. Default 10 m.
    """
    code: str
    category: str
    z_ref: float = 10.0

    def __post_init__(self) -> None:
        self.code = self.code.upper()
        self.category = self.category.upper() if self.code != "EC1" else self.category
        self._validate()

    def _validate(self) -> None:
        valid = {"EC1": _EC1_TERRAIN, "ASCE7": _ASCE7_EXPOSURE, "NSR10": _NSR10_TERRAIN}
        if self.code not in valid:
            raise ValueError(f"code must be one of {list(valid)}. Got '{self.code}'")
        if self.category not in valid[self.code]:
            raise ValueError(
                f"Category '{self.category}' not valid for {self.code}. "
                f"Valid: {list(valid[self.code])}"
            )

    # ------------------------------------------------------------------
    # EC1 methods — EN 1991-1-4 §4.3
    # ------------------------------------------------------------------
    def ec1_roughness_factor(self, z: float) -> float:
        """
        cr(z) — roughness factor (EC1 §4.3.2).
        cr(z) = kr · ln(z/z0)  for z >= zmin
        """
        if self.code != "EC1":
            raise RuntimeError("ec1_roughness_factor only available for EC1 code.")
        p = _EC1_TERRAIN[self.category]
        z0, zmin = p["z0"], p["zmin"]
        z0_II = _EC1_TERRAIN["II"]["z0"]
        kr = 0.19 * (z0 / z0_II) ** 0.07  # terrain factor
        z_eff = max(z, zmin)
        return kr * np.log(z_eff / z0)

    def ec1_orography_factor(self) -> float:
        """co(z) — orography factor (EC1 §4.3.3). Default 1.0 (flat terrain)."""
        return 1.0

    def ec1_mean_wind_velocity(self, z: float, vb: float) -> float:
        """
        vm(z) = cr(z) · co(z) · vb  [m/s]  (EC1 Eq. 4.3)
        """
        return self.ec1_roughness_factor(z) * self.ec1_orography_factor() * vb

    def ec1_turbulence_intensity(self, z: float) -> float:
        """
        Iv(z) = sigma_v / vm(z)  (EC1 §4.4)
        Iv(z) = kI / (co · ln(z/z0))
        """
        p = _EC1_TERRAIN[self.category]
        z0, zmin = p["z0"], p["zmin"]
        kI = 1.0  # turbulence factor (default)
        z_eff = max(z, zmin)
        return kI / (self.ec1_orography_factor() * np.log(z_eff / z0))

    def ec1_peak_velocity_pressure(self, z: float, vb: float,
                                    rho: float = 1.25) -> float:
        """
        qp(z) = [1 + 7·Iv(z)] · 0.5 · rho · vm²(z)  [Pa]  (EC1 Eq. 4.8)

        Parameters
        ----------
        z : float  height above ground [m]
        vb : float  basic wind velocity [m/s]
        rho : float  air density [kg/m³], default 1.25
        """
        vm = self.ec1_mean_wind_velocity(z, vb)
        Iv = self.ec1_turbulence_intensity(z)
        return (1 + 7 * Iv) * 0.5 * rho * vm**2

    # ------------------------------------------------------------------
    # ASCE 7 methods — §26.10 (Kz velocity pressure exposure coefficient)
    # ------------------------------------------------------------------
    def asce7_Kz(self, z: float) -> float:
        """
        Kz — velocity pressure exposure coefficient (ASCE 7-22 Table 26.10-1).
        Kz = 2.01 * (z/zg)^(2/alpha)  for z >= 15 ft (4.57 m)
        """
        if self.code != "ASCE7":
            raise RuntimeError("asce7_Kz only available for ASCE7 code.")
        p = _ASCE7_EXPOSURE[self.category]
        zg, alpha = p["zg"], p["alpha"]
        z_m = max(z, 4.57)  # 15 ft minimum
        return 2.01 * (z_m / zg) ** (2 / alpha)

    def asce7_velocity_pressure(self, z: float, V: float,
                                 Kd: float = 0.85, Kzt: float = 1.0) -> float:
        """
        qz = 0.613 · Kz · Kzt · Kd · V²  [Pa]   (ASCE 7 Eq. 26.10-1)

        Parameters
        ----------
        z : float  height [m]
        V : float  basic wind speed [m/s]
        Kd : float  directionality factor (default 0.85 for buildings)
        Kzt : float  topographic factor (default 1.0 flat)
        """
        Kz = self.asce7_Kz(z)
        return 0.613 * Kz * Kzt * Kd * V**2

    # ------------------------------------------------------------------
    # NSR-10 B.6 methods
    # ------------------------------------------------------------------
    def nsr10_Kz(self, z: float) -> float:
        """
        Kz per NSR-10 §B.6.5 (power law similar to ASCE 7-16).
        """
        if self.code != "NSR10":
            raise RuntimeError("nsr10_Kz only available for NSR10 code.")
        p = _NSR10_TERRAIN[self.category]
        zg, alpha = p["zg"], p["alpha"]
        z_m = max(z, 4.57)
        return 2.01 * (z_m / zg) ** (2 / alpha)

    def nsr10_velocity_pressure(self, z: float, Vb: float,
                                 Kd: float = 0.85, Kzt: float = 1.0) -> float:
        """
        qz = 0.613 · Kz · Kzt · Kd · Vb²  [Pa]  (NSR-10 §B.6.6)
        """
        Kz = self.nsr10_Kz(z)
        return 0.613 * Kz * Kzt * Kd * Vb**2

    def profile_table(self, heights: list[float], vb_or_V: float,
                       **kwargs) -> list[dict]:
        """
        Return a table of wind parameters at each height.

        Parameters
        ----------
        heights : list of floats  [m]
        vb_or_V : float  basic wind speed [m/s]

        Returns
        -------
        list of dicts with keys: z, Kz_or_cr, qz
        """
        rows = []
        for z in heights:
            if self.code == "EC1":
                cr = self.ec1_roughness_factor(z)
                qp = self.ec1_peak_velocity_pressure(z, vb_or_V, **kwargs)
                rows.append({"z_m": z, "cr": round(cr, 4), "qp_Pa": round(qp, 2)})
            elif self.code == "ASCE7":
                Kz = self.asce7_Kz(z)
                qz = self.asce7_velocity_pressure(z, vb_or_V, **kwargs)
                rows.append({"z_m": z, "Kz": round(Kz, 4), "qz_Pa": round(qz, 2)})
            else:
                Kz = self.nsr10_Kz(z)
                qz = self.nsr10_velocity_pressure(z, vb_or_V, **kwargs)
                rows.append({"z_m": z, "Kz": round(Kz, 4), "qz_Pa": round(qz, 2)})
        return rows
