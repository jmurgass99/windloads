"""Preprocesador OpenFOAM CFD para análisis de presiones de viento (Cp).

Genera los diccionarios de entrada necesarios (blockMeshDict, controlDict, snappyHexMeshDict)
y el archivo de geometría (OBJ) para un edificio en un túnel de viento virtual.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas de Entrada Pydantic v2
# ---------------------------------------------------------------------------

class CfdWindTunnelInput(BaseModel):
    """Parámetros para generar la simulación CFD OpenFOAM."""
    domain_length_m: float = Field(300.0, description="Longitud del túnel de viento (eje X) en m", gt=0.0)
    domain_width_m: float = Field(100.0, description="Ancho del túnel de viento (eje Y) en m", gt=0.0)
    domain_height_m: float = Field(80.0, description="Alto del túnel de viento (eje Z) en m", gt=0.0)
    
    # Dimensiones del edificio (obstáculo)
    building_length_m: float = Field(20.0, description="Longitud del edificio (eje X) en m", gt=0.0)
    building_width_m: float = Field(30.0, description="Ancho del edificio (eje Y) en m", gt=0.0)
    building_height_m: float = Field(15.0, description="Altura del edificio (eje Z) en m", gt=0.0)
    
    # Ubicación del edificio (centro en planta Z=0 en el fondo)
    building_center_x_m: float = Field(100.0, description="Posición X del centro del edificio en m", gt=0.0)
    building_center_y_m: float = Field(50.0, description="Posición Y del centro del edificio en m", gt=0.0)
    
    # Celdas del background mesh
    grid_cells_x: int = Field(60, description="Número de celdas en X para blockMesh", ge=5)
    grid_cells_y: int = Field(20, description="Número de celdas en Y para blockMesh", ge=5)
    grid_cells_z: int = Field(16, description="Número de celdas en Z para blockMesh", ge=5)
    
    # Simulación
    solver: str = Field("simpleFoam", description="Solver de OpenFOAM a utilizar: simpleFoam (RANS permanente) o pisoFoam (LES transitorio)")
    endTime: int = Field(1000, description="Pasos o tiempo de simulación máximo en iteraciones/segundos", ge=10)
    writeInterval: int = Field(100, description="Intervalo de escritura de resultados", ge=10)


# ---------------------------------------------------------------------------
# Schemas de Salida Pydantic v2
# ---------------------------------------------------------------------------

class CfdWindTunnelOutput(BaseModel):
    """Archivos y diccionarios de OpenFOAM autogenerados."""
    blockMeshDict: str
    controlDict: str
    snappyHexMeshDict: str
    building_obj: str
    mesh_summary: str


# ---------------------------------------------------------------------------
# Generadores de Texto OpenFOAM
# ---------------------------------------------------------------------------

def generate_block_mesh_dict(inp: CfdWindTunnelInput) -> str:
    """Genera el contenido del archivo system/blockMeshDict."""
    x_max = inp.domain_length_m
    y_max = inp.domain_width_m
    z_max = inp.domain_height_m
    
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
  =========                 |
  \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\\\    /   O peration     | Website:  https://openfoam.org
    \\\\  /    A nd           | Version:  10
     \\\\/     M anipulation  |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

vertices
(
    (0.0 0.0 0.0)       // 0
    ({x_max} 0.0 0.0)     // 1
    ({x_max} {y_max} 0.0)   // 2
    (0.0 {y_max} 0.0)     // 3
    (0.0 0.0 {z_max})     // 4
    ({x_max} 0.0 {z_max})   // 5
    ({x_max} {y_max} {z_max}) // 6
    (0.0 {y_max} {z_max})   // 7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({inp.grid_cells_x} {inp.grid_cells_y} {inp.grid_cells_z}) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    bottomWall
    {{
        type wall;
        faces
        (
            (0 1 2 3)
        );
    }}
    topAndSideWalls
    {{
        type patch;
        faces
        (
            (0 1 5 4)
            (3 7 6 2)
            (4 5 6 7)
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""


def generate_control_dict(inp: CfdWindTunnelInput) -> str:
    """Genera el contenido del archivo system/controlDict."""
    start_from = "startTime"
    if inp.solver == "simpleFoam":
        # RANS permanente
        deltat = 1
    else:
        # LES / PISO transitorio
        deltat = 0.005
        
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
  =========                 |
  \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\\\    /   O peration     | Website:  https://openfoam.org
    \\\\  /    A nd           | Version:  10
     \\\\/     M anipulation  |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     {inp.solver};
startFrom       {start_from};
startTime       0;
stopAt          endTime;
endTime         {inp.endTime};
deltaT          {deltat};
writeControl    timeStep;
writeInterval   {inp.writeInterval};
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression uncompressed;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

// ************************************************************************* //
"""


def generate_snappy_hex_mesh_dict(inp: CfdWindTunnelInput) -> str:
    """Genera el system/snappyHexMeshDict para refinar y sustraer el edificio."""
    # Coordenadas internas para snappyHexMesh
    # Un punto que este DENTRO del tunel de viento pero FUERA del edificio
    # e.g. (1.0, 1.0, 1.0)
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
  =========                 |
  \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\\\    /   O peration     | Website:  https://openfoam.org
    \\\\  /    A nd           | Version:  10
     \\\\/     M anipulation  |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{{
    building.obj
    {{
        type triSurfaceMesh;
        name building;
    }}
}};

castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minRefinementCells 10;
    nCellsBetweenLevels 2;

    features
    (
        {{
            file "building.eMesh";
            level 3;
        }}
    );

    refinementSurfaces
    {{
        building
        {{
            level (2 3);
        }}
    }}

    resolveFeatureAngle 30;

    refinementRegions
    {{
    }}

    locationInMesh (1.0 1.0 1.0);
    allowFreeStandingZoneFaces false;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
}}

addLayersControls
{{
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetDec 1e-30;
    minArea -1;
    minTwist 0.05;
    minDeterminant 0.001;
    minFaceWeight 0.05;
    minVolRatio 0.01;
}}

writeFlags
(
);

mergeTolerance 1e-6;

// ************************************************************************* //
"""


def generate_building_obj(inp: CfdWindTunnelInput) -> str:
    """Genera la geometría del edificio en formato OBJ (triSurface para OpenFOAM)."""
    # Caja rectangular centrada en (center_x, center_y) apoyada en Z=0
    x_min = inp.building_center_x_m - inp.building_length_m / 2.0
    x_max = inp.building_center_x_m + inp.building_length_m / 2.0
    y_min = inp.building_center_y_m - inp.building_width_m / 2.0
    y_max = inp.building_center_y_m + inp.building_width_m / 2.0
    z_min = 0.0
    z_max = inp.building_height_m
    
    return f"""# Edificio autogenerado en WindLoadJm
v {x_min:.3f} {y_min:.3f} {z_min:.3f}
v {x_max:.3f} {y_min:.3f} {z_min:.3f}
v {x_max:.3f} {y_max:.3f} {z_min:.3f}
v {x_min:.3f} {y_max:.3f} {z_min:.3f}
v {x_min:.3f} {y_min:.3f} {z_max:.3f}
v {x_max:.3f} {y_min:.3f} {z_max:.3f}
v {x_max:.3f} {y_max:.3f} {z_max:.3f}
v {x_min:.3f} {y_max:.3f} {z_max:.3f}

# Caras
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""


def create_cfd_openfoam_pre(inp: CfdWindTunnelInput) -> CfdWindTunnelOutput:
    """Preprocesa y genera los diccionarios de OpenFOAM."""
    # Validaciones geométricas básicas
    if inp.building_center_x_m + inp.building_length_m / 2.0 > inp.domain_length_m:
        raise ValueError("El edificio sale de los límites del túnel de viento en X.")
    if inp.building_center_y_m + inp.building_width_m / 2.0 > inp.domain_width_m:
        raise ValueError("El edificio sale de los límites del túnel de viento en Y.")
    if inp.building_height_m > inp.domain_height_m:
        raise ValueError("El edificio es más alto que la altura del túnel de viento.")
        
    block = generate_block_mesh_dict(inp)
    control = generate_control_dict(inp)
    snappy = generate_snappy_hex_mesh_dict(inp)
    obj = generate_building_obj(inp)
    
    total_cells = inp.grid_cells_x * inp.grid_cells_y * inp.grid_cells_z
    summary = f"""### Resumen del Túnel de Viento CFD (OpenFOAM)
- **Dominio Virtual**: {inp.domain_length_m:.1f}m (L) x {inp.domain_width_m:.1f}m (W) x {inp.domain_height_m:.1f}m (H).
- **Malla Bounding Box**: {total_cells} celdas en blockMesh ({inp.grid_cells_x}x{inp.grid_cells_y}x{inp.grid_cells_z}).
- **Obstáculo (Edificio)**: {inp.building_length_m:.1f}m (L) x {inp.building_width_m:.1f}m (W) x {inp.building_height_m:.1f}m (H).
- **Ubicación**: ({inp.building_center_x_m:.1f}, {inp.building_center_y_m:.1f}).
- **Solver**: `{inp.solver}` corriendo por `{inp.endTime}` pasos/segundos.
"""
    return CfdWindTunnelOutput(
        blockMeshDict=block,
        controlDict=control,
        snappyHexMeshDict=snappy,
        building_obj=obj,
        mesh_summary=summary,
    )
