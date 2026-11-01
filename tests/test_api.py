"""Tests del REST API via TestClient."""
from __future__ import annotations
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from windloads.api.app import app


client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "endpoints" in r.json()


def test_ec1_endpoint():
    r = client.post("/api/wind/ec1", json={
        "vb": 25.0, "height": 30.0, "width": 20.0, "depth": 40.0,
        "terrain_category": 2,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["qp_kPa"] > 0
    assert body["p_windward_kPa"] > 0


def test_asce7_endpoint():
    r = client.post("/api/wind/asce7", json={
        "V": 115, "height_ft": 100, "width_ft": 60, "depth_ft": 120,
        "exposure": "C",
    })
    assert r.status_code == 200
    assert r.json()["qz_psf"] > 0


def test_nsr10_endpoint():
    r = client.post("/api/wind/nsr10", json={
        "city": "Bogotá", "height_m": 30, "width_m": 20, "depth_m": 40,
    })
    assert r.status_code == 200
    assert r.json()["V_basic_kmh"] > 0


def test_cc_endpoint():
    r = client.post("/api/wind/components/cc", json={
        "code": "ASCE7", "roof_type": "gable", "zone": 3, "qh_kPa": 1.0,
    })
    assert r.status_code == 200
    assert r.json()["p_negative_kPa"] < 0


def test_export_json_endpoint():
    r = client.post("/api/export", json={
        "target": "json", "height_m": 30, "width_m": 20, "n_stories": 5,
        "pressures_per_story": [0.6, 0.7, 0.75, 0.8, 0.85],
    })
    assert r.status_code == 200
    import json
    parsed = json.loads(r.text)
    assert "stories" in parsed


def test_unknown_endpoint_404():
    assert client.get("/api/unknown").status_code == 404
