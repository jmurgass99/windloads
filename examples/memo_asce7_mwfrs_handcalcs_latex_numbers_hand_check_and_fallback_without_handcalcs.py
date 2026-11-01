"""Memoria del MWFRS de ASCE 7 con handcalcs (`mwfrs_directional_memo`): LaTeX, números comprobados a mano y modo sin handcalcs.

La memoria calcula K_z (exposición, z ≥ 4,572 m), q_z = 0,613·K_z·K_zt·K_d·K_e·V²/1000 [kN/m²], Cp de sotavento con
L/B (Fig. 27.3-1 interpolada) y las cuatro presiones de muro p = q_z·(G·Cp ∓ GCpi); la de diseño es la mayor en
valor absoluto. Con handcalcs instalado (`pip install windloads[memos]`) devuelve el LaTeX de cada paso; sin él
hasta 1.2.0 lanzaba TypeError al desempaquetar un número: ahora devuelve los mismos números con LaTeX vacío.
El ejemplo guarda el LaTeX en `examples/out/` y simula la ausencia de handcalcs recargando el módulo.

Caso: V = 46 m/s, z = 12 m, exposición C, L/B = 2, cerrado, K_e = 1.

Ejecutar:  python examples/memo_asce7_mwfrs_handcalcs_latex_numbers_hand_check_and_fallback_without_handcalcs.py
"""
import importlib
import os
import sys
from pathlib import Path

import windloads.memos.asce7_mwfrs as memo_mod

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))


def main() -> None:
    latex, r = memo_mod.mwfrs_directional_memo(V_ms=46.0, z=12.0, exposure="C", L_over_B=2.0)
    print(f"handcalcs disponible: {memo_mod._HAS_HANDCALCS}; LaTeX de {len(latex)} caracteres")
    for n in r.notes:
        print(f"  {n}")
    kz = 2.01 * (12.0 / 274.32) ** (2 / 9.5)
    q = 0.613 * kz * 0.85 * 46.0 ** 2 / 1000
    p = q * (0.85 * 0.8 + 0.18)
    print(f"A mano: K_z = {kz:.4f}, q_z = {q:.4f} kN/m², p_diseño = q·(0,85·0,8 + 0,18) = {p:.4f} kN/m² "
          f"(memoria {r.p_design_kN_m2:.4f})")
    if latex:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / "memoria_asce7_mwfrs.tex"
        path.write_text(latex, encoding="utf-8")
        first = next((line for line in latex.splitlines() if "=" in line), "")
        print(f"LaTeX guardado en {path.name} ({len(latex.splitlines())} líneas); primera ecuación: {first.strip()[:80]}")

    saved = {k: sys.modules.get(k) for k in ("handcalcs", "handcalcs.decorator")}
    sys.modules["handcalcs"] = None
    sys.modules["handcalcs.decorator"] = None
    try:
        no_hc = importlib.reload(memo_mod)
        latex2, r2 = no_hc.mwfrs_directional_memo(V_ms=46.0, z=12.0, exposure="C", L_over_B=2.0)
        print(f"\nSin handcalcs: _HAS_HANDCALCS = {no_hc._HAS_HANDCALCS}, LaTeX vacío = {not latex2.strip()}, "
              f"p_diseño = {r2.p_design_kN_m2:.4f} kN/m² ({'igual' if abs(r2.p_design_kN_m2 - r.p_design_kN_m2) < 1e-12 else 'DISTINTO'})")
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        importlib.reload(memo_mod)


if __name__ == "__main__":
    main()
