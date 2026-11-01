"""Coeficiente de orografía c_o de EN 1991-1-4 Anexo A.3 a lo largo de una colina y de un escarpe, y K_zt de ASCE 7 Fig. 26.8-1.

EN 1991-1-4 A.3: Φ = H/L_u, L_e de la Tabla A.2, c_o = 1 + 2·s·Φ (0,05 < Φ < 0,3) o 1 + 0,6·s (Φ > 0,3), con el
factor de posición s de las Expresiones (A.4)-(A.13): barlovento (cualquier relieve), sotavento de escarpe
(Figura A.2) y sotavento de colina (Figura A.3). Caso: H = 40 m, L_u = L_d = 200 m (Φ = 0,2, L_e = 200 m),
emplazamiento a z = 10 m sobre el terreno. Se rehace a mano s en dos puntos de sotavento.

ASCE 7 Fig. 26.8-1 (ASCE 7-10): K_zt = (1 + K1·K2·K3)² con K1/(H/L_h), γ y μ de la figura para cresta 2-D,
escarpe 2-D y colina 3-D; caso H = 30 m, L_h = 100 m (H/L_h = 0,3), exposición C, z = 10 m.

Ejecutar:  python examples/orography_factor_en1991_annex_a3_hill_and_escarpment_profiles_hand_check_and_asce7_kzt_ridge_escarpment_hill.py
"""
import math

from windloads.topography import asce7_Kzt_simple, ec1_orography_factor_A3

H, LU, Z = 40.0, 200.0, 10.0


def a_crest(zl: float) -> float:
    return 0.1552 * zl ** 4 - 0.8575 * zl ** 3 + 1.8133 * zl ** 2 - 1.9115 * zl + 1.0124


def main() -> None:
    phi = H / LU
    print(f"EN 1991-1-4 A.3: H = {H} m, L_u = L_d = {LU} m, Φ = {phi}, L_e = {LU} m, z = {Z} m")
    print(f"  {'x [m]':>6} {'x/L':>6} {'c_o colina':>11} {'c_o escarpe':>12}")
    for x in (-300, -200, -100, -50, 0, 20, 50, 100, 200, 400, 700):
        h = ec1_orography_factor_A3(z=Z, x=x, H=H, Lu=LU, Ld=LU, kind="hill")
        c = ec1_orography_factor_A3(z=Z, x=x, H=H, Lu=LU, kind="cliff")
        print(f"  {x:6.0f} {x / LU:6.2f} {h:11.4f} {c:12.4f}")

    zl = Z / LU
    B = -0.3056 * zl ** 2 + 1.0212 * zl - 1.7637
    s_hill = a_crest(zl) * math.exp(B * 0.5)
    print("\nA mano, colina a sotavento x = 100 m (X/L_d = 0,5; z/L_e = 0,05):")
    print(f"  (A.12) A = {a_crest(zl):.5f}; (A.13) B = {B:.5f}; s = A·e^(B·0,5) = {s_hill:.5f};"
          f" c_o = 1 + 2·s·0,2 = {1 + 2 * s_hill * phi:.5f}"
          f" (función {ec1_orography_factor_A3(z=Z, x=100, H=H, Lu=LU, Ld=LU):.5f})")
    lz, lx = math.log10(0.1), math.log10(0.25)        # z/L_e < 0,1 → se usa 0,1
    a = -1.3420 * lz ** 3 - 0.8222 * lz ** 2 + 0.4609 * lz - 0.0791
    b = -1.0196 * lz ** 3 - 0.8910 * lz ** 2 + 0.5343 * lz - 0.1156
    c = 0.8030 * lz ** 3 + 0.4236 * lz ** 2 - 0.5738 * lz + 0.1606
    s_cliff = a * lx ** 2 + b * lx + c
    print("A mano, escarpe a sotavento x = 50 m (X/L_e = 0,25; z/L_e = 0,05 → 0,1 en A.8-A.10):")
    print(f"  A = {a:.4f}, B = {b:.4f}, C = {c:.4f}; s = A·log²(0,25) + B·log(0,25) + C = {s_cliff:.5f};"
          f" c_o = {1 + 2 * s_cliff * phi:.5f} (función {ec1_orography_factor_A3(z=Z, x=50, H=H, Lu=LU, kind='cliff'):.5f})")
    c0 = ec1_orography_factor_A3(z=Z, x=0, H=H, Lu=LU)
    print(f"En la cresta c_o = {c0:.3f}: la presión pico crece del orden de c_o² = {c0 ** 2:.2f} veces (más exactamente "
          "q_p ∝ c_o·(c_o + 7·I_v), porque I_v se divide por c_o).")

    print("\nASCE 7 Fig. 26.8-1, H = 30 m, L_h = 100 m, exposición C, z = 10 m:")
    print(f"  {'x [m]':>6} {'cresta 2-D':>11} {'escarpe 2-D':>12} {'colina 3-D':>11}")
    for x in (-150, -100, -50, 0, 50, 100, 200, 300):
        vals = [asce7_Kzt_simple(30.0, 100.0, x, 10.0, f, "C") for f in ("ridge", "escarpment", "hill")]
        print(f"  {x:6.0f} {vals[0]:11.3f} {vals[1]:12.3f} {vals[2]:11.3f}")
    k_hand = (1 + 1.45 * 0.3 * 1.0 * math.exp(-3 * 0.1)) ** 2
    print(f"  A mano en la cresta 2-D: K1 = 1,45·0,3 = 0,435; K3 = e^(−3·0,1) = {math.exp(-0.3):.4f}; "
          f"K_zt = (1 + 0,435·{math.exp(-0.3):.4f})² = {k_hand:.4f}")
    k_esc = asce7_Kzt_simple(30.0, 100.0, 200.0, 10.0, "escarpment", "C")
    print(f"  A 200 m a sotavento el escarpe conserva K_zt = {k_esc:.3f} (μ = 4) mientras la cresta y la colina ya "
          "valen 1,000 (μ = 1,5).")


if __name__ == "__main__":
    main()
