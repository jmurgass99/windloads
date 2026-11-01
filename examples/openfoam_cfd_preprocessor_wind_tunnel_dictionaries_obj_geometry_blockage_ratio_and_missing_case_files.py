"""Preprocesador de OpenFOAM (`cfd_pre`): túnel virtual para una nave, geometría OBJ, relación de bloqueo y lo que falta para correr.

`create_cfd_openfoam_pre` escribe blockMeshDict (dominio prismático con inlet, outlet, suelo y techo/laterales),
controlDict (simpleFoam o pisoFoam), snappyHexMeshDict (refinamiento 2-3 alrededor del edificio) y un OBJ de la caja
del edificio, y valida que el edificio cabe en el dominio. NO genera las condiciones de contorno (0/U, 0/p, perfil
de capa límite en la entrada), constant/ (transportProperties, turbulencia), fvSchemes, fvSolution ni el
surfaceFeaturesDict que pide el snappyHexMeshDict: es un punto de partida, no un caso ejecutable. El ejemplo guarda
los ficheros en `examples/out/openfoam_nave/`, calcula el bloqueo y las distancias en múltiplos de H y comprueba que
el punto fijo `locationInMesh (1 1 1)` queda fuera del edificio.

Ejecutar:  python examples/openfoam_cfd_preprocessor_wind_tunnel_dictionaries_obj_geometry_blockage_ratio_and_missing_case_files.py
"""
import os
from pathlib import Path

from windloads.cfd_pre import CfdWindTunnelInput, create_cfd_openfoam_pre

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))


def main() -> None:
    inp = CfdWindTunnelInput(domain_length_m=300.0, domain_width_m=160.0, domain_height_m=72.0,
                             building_length_m=16.0, building_width_m=40.0, building_height_m=12.0,
                             building_center_x_m=80.0, building_center_y_m=80.0,
                             grid_cells_x=100, grid_cells_y=54, grid_cells_z=24, solver="simpleFoam", endTime=2000)
    case = create_cfd_openfoam_pre(inp)
    base = OUT / "openfoam_nave"
    (base / "system").mkdir(parents=True, exist_ok=True)
    (base / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
    (base / "system" / "blockMeshDict").write_text(case.blockMeshDict, encoding="utf-8")
    (base / "system" / "controlDict").write_text(case.controlDict, encoding="utf-8")
    (base / "system" / "snappyHexMeshDict").write_text(case.snappyHexMeshDict, encoding="utf-8")
    (base / "constant" / "triSurface" / "building.obj").write_text(case.building_obj, encoding="utf-8")
    print(case.mesh_summary)
    written = sorted(str(p.relative_to(base)).replace(os.sep, "/") for p in base.rglob("*") if p.is_file())
    print(f"Ficheros escritos: {written}")

    H = inp.building_height_m
    blockage = inp.building_width_m * H / (inp.domain_width_m * inp.domain_height_m)
    up = inp.building_center_x_m - inp.building_length_m / 2
    down = inp.domain_length_m - (inp.building_center_x_m + inp.building_length_m / 2)
    print(f"Bloqueo = área frontal/sección del túnel = {inp.building_width_m:.0f}·{H:.0f}/({inp.domain_width_m:.0f}·"
          f"{inp.domain_height_m:.0f}) = {100 * blockage:.1f} %")
    print(f"Distancias: barlovento {up:.0f} m = {up / H:.1f}·H, sotavento {down:.0f} m = {down / H:.1f}·H, "
          f"techo {inp.domain_height_m - H:.0f} m = {(inp.domain_height_m - H) / H:.1f}·H")
    dx = inp.domain_length_m / inp.grid_cells_x
    print(f"Celda de fondo {dx:.1f} m: el edificio de {H:.0f} m tiene {H / dx:.1f} celdas de altura antes de refinar.")
    x0, y0 = inp.building_center_x_m - inp.building_length_m / 2, inp.building_center_y_m - inp.building_width_m / 2
    inside = x0 <= 1.0 <= x0 + inp.building_length_m and y0 <= 1.0 <= y0 + inp.building_width_m
    print(f"locationInMesh (1 1 1) {'cae DENTRO del edificio: snappyHexMesh se quedaría con el interior' if inside else 'queda fuera del edificio'}.")
    missing = ["0/U", "0/p", "0/k", "0/epsilon o 0/omega", "constant/transportProperties",
               "constant/momentumTransport", "system/fvSchemes", "system/fvSolution", "system/surfaceFeaturesDict"]
    print(f"Faltan para ejecutar: {', '.join(missing)}.")


if __name__ == "__main__":
    main()
