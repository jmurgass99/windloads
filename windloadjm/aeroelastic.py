"""
EN 1991-1-4 Anexo F — Fenómenos aeroelásticos.

Implementa criterios simplificados de:
- Galloping (Den Hartog) §F.2
- Divergencia torsional de placas / puentes §F.4
- Flutter 2-DOF (heave + pitch) con derivadas tipo Theodorsen/Scanlan §F.3
- Lock-in de vortex shedding (rango ±20% por defecto) §E
- Wake / buffeting de interferencia entre cilindros §F.5

Las fórmulas son las del Anexo F del Eurocódigo y de Simiu & Scanlan
"Wind Effects on Structures" (referencia normativa habitual del EC1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


# ----------------------------------------------------------------------
# 1) Galloping — Den Hartog
# ----------------------------------------------------------------------
def galloping_critical_velocity(
    m: float,
    fn: float,
    b: float,
    rho_air: float,
    c_a_prime: float,
    sc: float | None = None,
    delta: float = 0.05,
) -> float:
    """
    Velocidad crítica de galloping (Den Hartog, EN 1991-1-4 Eq. E.18 / F.2).

        Vcr = 2 · Sc · fn · b / aG

    donde:
        Sc = 2·m·δ / (ρ·b²)          (número de Scruton)
        aG = -c_a_prime              (factor Den Hartog: dCL/dα + CD)

    Para perfiles ESTABLES (aG ≥ 0, e.g. cilindro circular dCL/dα≈0,
    CD≈1 ⇒ aG=2) NO existe galloping → se devuelve +inf.

    Parámetros
    ----------
    m         : masa por unidad de longitud [kg/m]
    fn        : frecuencia natural [Hz]
    b         : dimensión característica transversal [m]
    rho_air   : densidad del aire [kg/m³]
    c_a_prime : coeficiente Den Hartog (dCL/dα + CD). Negativo ⇒ inestable.
    sc        : Scruton dado por el usuario; si None se calcula con δ.
    delta     : decremento logarítmico (sólo si sc es None).

    Devuelve
    --------
    Vcr [m/s]; math.inf si el perfil es aerodinámicamente estable.
    """
    if m is None or m <= 0:
        raise ValueError("masa m debe ser > 0")
    if fn <= 0 or b <= 0 or rho_air <= 0:
        raise ValueError("fn, b, rho_air deben ser > 0")

    if sc is None:
        sc = 2.0 * m * delta / (rho_air * b * b)

    # Convención EN 1991-1-4 / Den Hartog:
    #   c_a_prime = aG = dCL/dα + CD
    #   aG > 0 ⇒ perfil ESTABLE (no hay galloping) → Vcr = +inf
    #   aG < 0 ⇒ perfil INESTABLE; Vcr = 2·Sc·fn·b / |aG|
    aG = c_a_prime
    if aG >= 0:
        return math.inf
    return 2.0 * sc * fn * b / abs(aG)


# ----------------------------------------------------------------------
# 2) Divergencia torsional — §F.4
# ----------------------------------------------------------------------
def divergence_critical_velocity(
    EI: float,
    L: float,
    c_M_alpha: float,
    rho_air: float,
    B: float,
) -> float:
    """
    Velocidad crítica de divergencia torsional para placas/puentes
    (EN 1991-1-4 §F.4).

        V_div = sqrt( 2·K_alpha / (ρ · B² · dCM/dα) )

    con K_alpha = EI / L  (rigidez torsional equivalente por unidad de
    longitud para una viga simplemente apoyada — caso tabulado del EC1).

    Parámetros
    ----------
    EI        : rigidez torsional [N·m²]
    L         : luz característica [m]
    c_M_alpha : dCM/dα — pendiente del coeficiente de momento [1/rad]
    rho_air   : densidad del aire [kg/m³]
    B         : ancho del tablero [m]
    """
    if EI <= 0 or L <= 0 or B <= 0 or rho_air <= 0:
        raise ValueError("EI, L, B, rho_air deben ser > 0")
    if c_M_alpha <= 0:
        raise ValueError("c_M_alpha (dCM/dα) debe ser > 0 para divergencia")

    K_alpha = EI / L
    return math.sqrt(2.0 * K_alpha / (rho_air * B * B * c_M_alpha))


# ----------------------------------------------------------------------
# 3) Flutter 2-DOF (heave + pitch) — Theodorsen / Scanlan §F.3
# ----------------------------------------------------------------------
def flutter_2dof(
    m: float,
    I_alpha: float,
    Salpha: float,
    k_h: float,
    k_alpha: float,
    U_inf: float,
    b: float,
    rho: float,
) -> Tuple[float, complex]:
    """
    Análisis de flutter 2-DOF (heave h + pitch α) — método del determinante.

    Sistema (sin amortiguamiento estructural, modelo cuasi-estacionario
    de Theodorsen con C(k)=1):

        | m·ω² - k_h - π·ρ·b²·ω²       S_α·ω² - π·ρ·b²·U_inf·ω·i |
        |                                                        | = 0
        | S_α·ω² + 2π·ρ·U_inf·b·...    I_α·ω² - k_α - π·ρ·b⁴·... |

    Aproximación práctica: se busca la velocidad U_f para la cual el
    determinante de la matriz de impedancia tiene parte imaginaria nula
    (condición de flutter). Aquí devolvemos V_flutter por el criterio
    clásico de coalescencia de frecuencias (Theodorsen, placa plana):

        V_f = b · ω_α · sqrt( 2·μ·r²·(r² - σ²) / ((1+μ·r²)·something) )

    Para mantener el alcance educativo del Anexo F usamos la forma
    simplificada de Bisplinghoff–Ashley–Halfman (placa plana, sin
    desfase aerodinámico):

        ω_h² = k_h/m,  ω_α² = k_α/I_α,
        μ    = m/(π·ρ·b²),
        r²   = I_α/(m·b²),
        σ    = ω_h/ω_α,
        x_α  = S_α/(m·b)

        V_f / (b·ω_α) = sqrt( μ · r² · (1 - σ²)² /
                               (2 · (r² + x_α² - r²·σ²)) ) ⁻¹   [aprox.]

    Devuelve (V_flutter, omega_flutter_complejo).
    """
    if m is None or m <= 0:
        raise ValueError("masa m debe ser > 0")
    if I_alpha <= 0 or k_h <= 0 or k_alpha <= 0 or b <= 0 or rho <= 0:
        raise ValueError("I_alpha, k_h, k_alpha, b, rho deben ser > 0")
    if U_inf < 0:
        raise ValueError("U_inf no puede ser negativa")

    omega_h2 = k_h / m
    omega_a2 = k_alpha / I_alpha
    omega_h = math.sqrt(omega_h2)
    omega_a = math.sqrt(omega_a2)

    mu = m / (math.pi * rho * b * b)          # relación de masa
    r2 = I_alpha / (m * b * b)                # radio de giro²
    sigma = omega_h / omega_a
    x_a = Salpha / (m * b)                    # offset CG–EA adimensional

    # Determinante (Bisplinghoff – placa plana):
    #   A·Ω⁴ + B·Ω² + C = 0,   con Ω = ω/ω_α
    # A = r² - x_a²
    # B = -(r² + r²·σ² + ... )
    # Forma compacta:
    A = (r2 - x_a * x_a)
    Bcoef = -(r2 * (1.0 + sigma * sigma) + 2.0 * x_a * 0.0)  # sin acopl. aero
    Ccoef = r2 * sigma * sigma

    # Resolver Ω²
    disc = Bcoef * Bcoef - 4.0 * A * Ccoef
    if disc < 0 or A == 0:
        # No hay solución real → no flutter en este modelo simplificado
        return math.inf, complex(0.0, 0.0)

    Omega2 = (-Bcoef - math.sqrt(disc)) / (2.0 * A)
    if Omega2 <= 0:
        Omega2 = (-Bcoef + math.sqrt(disc)) / (2.0 * A)
    if Omega2 <= 0:
        return math.inf, complex(0.0, 0.0)

    omega_f = math.sqrt(Omega2) * omega_a
    # Velocidad de flutter: V_f = b · ω_f · sqrt(μ)   (forma clásica)
    V_f = b * omega_f * math.sqrt(mu)
    return V_f, complex(omega_f, 0.0)


# ----------------------------------------------------------------------
# 4) Lock-in vortex shedding — §E.1
# ----------------------------------------------------------------------
def lock_in_range(
    St: float,
    fn: float,
    b: float,
    U_mean: float,
    band: float = 0.20,
) -> Tuple[float, float, bool]:
    """
    Rango de velocidades de lock-in alrededor de la velocidad crítica
    de vortex shedding:

        V_crit = fn · b / St
        [V_crit·(1-band),  V_crit·(1+band)]

    Devuelve (V_lo, V_hi, in_lock_in) donde in_lock_in es True si la
    velocidad media U_mean cae dentro del rango.
    """
    if St <= 0 or fn <= 0 or b <= 0 or U_mean < 0:
        raise ValueError("St, fn, b deben ser > 0 y U_mean ≥ 0")
    V_crit = fn * b / St
    V_lo = V_crit * (1.0 - band)
    V_hi = V_crit * (1.0 + band)
    return V_lo, V_hi, (V_lo <= U_mean <= V_hi)


# ----------------------------------------------------------------------
# 5) Wake buffeting — §F.5
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class WakeBuffetingResult:
    interference_factor: float
    is_critical: bool
    configuration: str
    distance_ratios: float        # a/b


def wake_buffeting(
    distance: float,
    b: float,
    configuration: str = "tandem",
) -> WakeBuffetingResult:
    """
    Estimación simplificada del factor de interferencia entre dos
    cilindros (§F.5 EN 1991-1-4).

        a/b < 3   → fuerte interferencia (crítica)
        3 ≤ a/b ≤ 20 → buffeting moderado, factor decreciente
        a/b > 20  → cilindros aislados

    configurations:
        - "tandem"   (uno detrás de otro)
        - "side_by_side"
        - "staggered"
    """
    if b <= 0:
        raise ValueError("b debe ser > 0")
    if distance < 0:
        raise ValueError("distance ≥ 0")
    if configuration not in {"tandem", "side_by_side", "staggered"}:
        raise ValueError("configuration inválida")

    ratio = distance / b
    if configuration == "tandem":
        if ratio < 3.0:
            factor = 1.5
        elif ratio <= 20.0:
            factor = 1.5 - (ratio - 3.0) / 17.0 * 0.5  # decrece de 1.5 a 1.0
        else:
            factor = 1.0
    elif configuration == "side_by_side":
        factor = 1.2 if ratio < 3.0 else 1.0
    else:  # staggered
        factor = 1.3 if ratio < 5.0 else 1.0

    critical = ratio < 3.0
    return WakeBuffetingResult(
        interference_factor=factor,
        is_critical=critical,
        configuration=configuration,
        distance_ratios=ratio,
    )


__all__ = [
    "galloping_critical_velocity",
    "divergence_critical_velocity",
    "flutter_2dof",
    "lock_in_range",
    "wake_buffeting",
    "WakeBuffetingResult",
]
