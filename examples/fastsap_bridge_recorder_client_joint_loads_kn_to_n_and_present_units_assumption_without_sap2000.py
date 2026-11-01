"""Puentes hacia SAP2000 (`integration.fastsap_bridge` y `fastsap_load_patterns`) con un cliente grabador, sin SAP2000.

`distribute_pressure_to_joints` convierte presión × área tributaria en cargas de nudo [kN];
`apply_wind_loads_to_sap(sap, ...)` crea el patrón como OTHER (8) si no existe y llama a
`PointObj.SetLoadForce(nudo, patrón, F[6], Replace, "Global", 0)` multiplicando por 1000 (kN → N); y
`FastSAPWindPatternExporter` hace lo mismo desde un dict de cargas, o un recuento si `dry_run`. Aquí el «SAP2000»
es un objeto Python que graba las llamadas.

LÍMITE IMPORTANTE: la API de SAP2000 interpreta las fuerzas en las unidades ACTUALES del modelo
(SetPresentUnits), no en newtons fijos. El factor 1000 solo es correcto si el modelo está en N; en un modelo en
kN·m las cargas quedan 1000 veces mayores. Fija las unidades a N antes de llamar a estos puentes.

Ejecutar:  python examples/fastsap_bridge_recorder_client_joint_loads_kn_to_n_and_present_units_assumption_without_sap2000.py
"""
from types import SimpleNamespace

from windloads.integration import apply_wind_loads_to_sap, distribute_pressure_to_joints
from windloads.integration.fastsap_load_patterns import FastSAPWindPatternExporter, WindLoadPattern


def recorder(existing=("DEAD",), fail=()):
    calls, pats = [], list(existing)

    class LP:
        @staticmethod
        def GetNameList():
            return (len(pats), list(pats), 0)

        @staticmethod
        def Add(name, kind, *args):
            pats.append(name)
            calls.append(("LoadPatterns.Add", name, kind))
            return 0

    class PO:
        @staticmethod
        def SetLoadForce(name, pattern, f, *args):
            calls.append(("SetLoadForce", name, pattern, tuple(round(v, 1) for v in f)))
            return 1 if name in fail else 0

    model = SimpleNamespace(LoadPatterns=LP, PointObj=PO)
    return SimpleNamespace(SapModel=model), model, calls


def main() -> None:
    p = 0.85   # kN/m²
    areas = [4.5, 9.0, 9.0, 4.5]
    ass = distribute_pressure_to_joints(["5", "6", "7", "8"], p, areas, direction="X")
    print("Cargas de nudo [kN]: " + ", ".join(f"{a.joint_name}={a.Fx_kN:.3f}" for a in ass)
          + f"; suma {sum(a.Fx_kN for a in ass):.3f} = 0,85·27 = {p * sum(areas):.3f}")

    sap, _, calls = recorder(fail={"8"})
    res = apply_wind_loads_to_sap(sap, ass, load_pattern="W_X_EC1")
    print(f"apply_wind_loads_to_sap: aplicadas {res.n_joints_loaded}, fallidas {res.failed}; {res.notes[0]}")
    for c in calls[:3]:
        print(f"  llamada grabada: {c}")
    sent = [c[3][0] for c in calls if c[0] == "SetLoadForce"]
    print(f"Fuerza enviada al nudo 5: {sent[0]:.1f} (= {ass[0].Fx_kN:.3f} kN × 1000): correcto solo con el modelo en N.")

    pats = [WindLoadPattern("WX+", {"5": (3.8, 0.0, 0.0), "6": (7.7, 0.0, 0.0)}),
            WindLoadPattern("WY+", {"5": (0.0, 2.1, 0.0)})]
    print(f"\nExportador en seco: {FastSAPWindPatternExporter(dry_run=True).export(pats)}")
    _, model2, calls2 = recorder()
    out = FastSAPWindPatternExporter(client=model2).export(pats)
    print(f"Exportador con cliente: aplicadas {out['applied']}, fallidas {out['failed']}; "
          f"patrones creados {[c[1] for c in calls2 if c[0] == 'LoadPatterns.Add']} con tipo 8 (OTHER)")


if __name__ == "__main__":
    main()
