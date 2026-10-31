"""
Generador automático de velocidad para Mean Recurrence Interval (idea #17).

Convierte velocidad básica V_50 (50-yr MRI) a V_T para cualquier MRI T
usando el factor de Peterka-Shahid o el de ASCE 7-22 Appendix C:

    V_T = V_50 * (ln(T) / ln(50)) ^ k    (Peterka-Shahid)

donde k ≈ 0.55 para huracanes. ASCE 7-22 da factor tabulado por categoría
de riesgo (Risk Category I..IV). Multi-code:
- ASCE 7-22 USA: factor por Risk Cat
- EN 1991-1-4: V_T = V_50 * sqrt((1 - K*ln(-ln(1-1/T)))/(1 - K*ln(-ln(0.98)))), K=0.2
- AS 1170.2: V_R por tabla
- NSR-10 / SG: usa Eurocode
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MRIInput:
    V_basic_ms: float       # velocidad básica (50-yr)
    T_years: float          # MRI objetivo
    code: str = "ASCE"


@dataclass(frozen=True)
class MRIResult:
    V_target_ms: float
    factor: float
    code: str


# ASCE 7-22 Tabla C.26.5-2 (Risk Cat II base 700 yr -> factor)
_ASCE_TABLE = {
    10: 0.76, 25: 0.84, 50: 0.90, 100: 0.95, 300: 1.03, 700: 1.07, 1700: 1.13, 3000: 1.16,
}


def _asce_factor(T_years: float) -> float:
    keys = sorted(_ASCE_TABLE.keys())
    if T_years <= keys[0]:
        return _ASCE_TABLE[keys[0]]
    if T_years >= keys[-1]:
        return _ASCE_TABLE[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= T_years <= keys[i + 1]:
            t = (T_years - keys[i]) / (keys[i + 1] - keys[i])
            return _ASCE_TABLE[keys[i]] * (1 - t) + _ASCE_TABLE[keys[i + 1]] * t
    return 1.0


def _eurocode_factor(T_years: float, K: float = 0.2) -> float:
    """V_T / V_50 según EN 1991-1-4 §4.2(2)P NOTE."""
    # cprob = sqrt((1 - K*ln(-ln(1-p)))/(1 - K*ln(-ln(0.98))))
    # p = 1/T
    p = 1.0 / T_years
    num = 1.0 - K * math.log(-math.log(1.0 - p))
    den = 1.0 - K * math.log(-math.log(0.98))
    if den <= 0:
        return 1.0
    ratio = num / den
    if ratio <= 0:
        return 1.0
    return math.sqrt(ratio)


def velocity_for_MRI(inp: MRIInput) -> MRIResult:
    if inp.V_basic_ms <= 0:
        raise ValueError("V_basic > 0")
    if inp.T_years <= 0:
        raise ValueError("T_years > 0")
    c = inp.code.upper()
    if c in ("ASCE", "USA"):
        f = _asce_factor(inp.T_years)
    elif c in ("EU", "EUROCODE", "SG", "SS", "NSR", "CO"):
        f = _eurocode_factor(inp.T_years)
    elif c in ("AS", "AU"):
        # AS 1170.2 Table 3.1: aproximamos como Peterka-Shahid k=0.55
        f = (math.log(inp.T_years) / math.log(50.0)) ** 0.55 if inp.T_years > 1 else 0.5
    else:
        raise ValueError(f"Código desconocido: {inp.code}")
    return MRIResult(V_target_ms=inp.V_basic_ms * f, factor=f, code=inp.code)


def MRI_for_target_velocity(V_basic_ms: float, V_target_ms: float,
                            code: str = "ASCE") -> float:
    """Estima T en años cuya V_T == V_target. Búsqueda por bisección."""
    if V_basic_ms <= 0 or V_target_ms <= 0:
        raise ValueError("velocidades > 0")
    lo, hi = 1.5, 5000.0
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        v = velocity_for_MRI(MRIInput(V_basic_ms, mid, code)).V_target_ms
        if v < V_target_ms:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)
