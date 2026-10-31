"""Tests unitarios para el preprocesador CFD OpenFOAM en WindLoads."""

import pytest
from fastapi.testclient import TestClient
from windloads.cfd_pre import (
    CfdWindTunnelInput,
    create_cfd_openfoam_pre,
)
from windloads.api.app import app

client = TestClient(app)


def test_cfd_pre_generation_valid():
    """Prueba que el generador CFD cree correctamente todos los archivos de OpenFOAM."""
    inp = CfdWindTunnelInput(
        domain_length_m=200.0,
        domain_width_m=80.0,
        domain_height_m=60.0,
        building_length_m=20.0,
        building_width_m=20.0,
        building_height_m=12.0,
        building_center_x_m=80.0,
        building_center_y_m=40.0,
        grid_cells_x=50,
        grid_cells_y=20,
        grid_cells_z=15,
        solver="simpleFoam",
        endTime=1000
    )
    res = create_cfd_openfoam_pre(inp)
    
    # 1. blockMeshDict check
    assert "convertToMeters 1;" in res.blockMeshDict
    assert "200.0 80.0 60.0" in res.blockMeshDict
    assert "hex (0 1 2 3 4 5 6 7) (50 20 15)" in res.blockMeshDict
    assert "inlet" in res.blockMeshDict
    assert "outlet" in res.blockMeshDict
    
    # 2. controlDict check
    assert "application     simpleFoam;" in res.controlDict
    assert "endTime         1000;" in res.controlDict
    
    # 3. snappyHexMeshDict check
    assert "castellatedMesh true;" in res.snappyHexMeshDict
    assert "building.obj" in res.snappyHexMeshDict
    
    # 4. OBJ file check (vertices of the building box)
    # x_min = 80 - 10 = 70.0, x_max = 80 + 10 = 90.0
    # y_min = 40 - 10 = 30.0, y_max = 40 + 10 = 50.0
    # z_max = 12.0
    assert "v 70.000 30.000 0.000" in res.building_obj
    assert "v 90.000 50.000 12.000" in res.building_obj
    assert "f 1 2 3 4" in res.building_obj
    
    # 5. Summary check
    assert "200.0m" in res.mesh_summary
    assert "15000 celdas" in res.mesh_summary


def test_cfd_pre_out_of_bounds_errors():
    """Verifica que se eleven excepciones si las dimensiones del edificio exceden el dominio."""
    # Edificio sale en X
    with pytest.raises(ValueError, match="El edificio sale de los límites"):
        create_cfd_openfoam_pre(CfdWindTunnelInput(
            domain_length_m=100.0,
            building_length_m=50.0,
            building_center_x_m=80.0,  # 80 + 25 = 105 > 100
        ))
        
    # Edificio sale en Y
    with pytest.raises(ValueError, match="El edificio sale de los límites"):
        create_cfd_openfoam_pre(CfdWindTunnelInput(
            domain_width_m=50.0,
            building_width_m=20.0,
            building_center_y_m=45.0,  # 45 + 10 = 55 > 50
        ))
        
    # Edificio excede la altura
    with pytest.raises(ValueError, match="El edificio es más alto que la altura del túnel"):
        create_cfd_openfoam_pre(CfdWindTunnelInput(
            domain_height_m=30.0,
            building_height_m=35.0,
        ))


def test_api_openfoam_pre_endpoint():
    """Prueba de integración del endpoint FastAPI para OpenFOAM CFD preprocessor."""
    payload = {
        "domain_length_m": 250.0,
        "domain_width_m": 90.0,
        "domain_height_m": 70.0,
        "building_length_m": 25.0,
        "building_width_m": 25.0,
        "building_height_m": 15.0,
        "building_center_x_m": 90.0,
        "building_center_y_m": 45.0,
        "grid_cells_x": 40,
        "grid_cells_y": 15,
        "grid_cells_z": 12,
        "solver": "pisoFoam",
        "endTime": 500,
        "writeInterval": 50
    }
    response = client.post("/api/wind/openfoam-pre", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "blockMeshDict" in data
    assert "controlDict" in data
    assert "snappyHexMeshDict" in data
    assert "building_obj" in data
    assert "mesh_summary" in data
    assert "pisoFoam" in data["controlDict"]
