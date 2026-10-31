"""Tests for the extended Vb atlas (grupo F)."""
from __future__ import annotations

import pytest

from windloads.vb_atlas import vb_for, list_vb, VbEntry


def test_atlas_has_thirty_per_country():
    cl = list_vb("CL")
    co = list_vb("CO")
    es = list_vb("ES")
    assert len(cl) == 30
    assert len(co) == 30
    assert len(es) == 30
    assert all(isinstance(e, VbEntry) for e in cl + co + es)


def test_atlas_total_is_ninety():
    assert len(list_vb()) == 90


@pytest.mark.parametrize("city,country,vmin,vmax", [
    ("Santiago",     "CL", 28.0, 36.0),
    ("Concepcion",   "CL", 40.0, 50.0),
    ("Punta Arenas", "CL", 45.0, 55.0),
    ("Valdivia",     "CL", 35.0, 45.0),
    ("Arica",        "CL", 28.0, 35.0),
])
def test_vb_chile(city, country, vmin, vmax):
    v = vb_for(city, country)
    assert v is not None
    assert vmin <= v <= vmax


@pytest.mark.parametrize("city,vmin,vmax", [
    ("Bogota",       24.0, 30.0),
    ("Barranquilla", 36.0, 45.0),
    ("San Andres",   45.0, 55.0),
    ("Cali",         30.0, 36.0),
    ("Medellin",     24.0, 30.0),
])
def test_vb_colombia(city, vmin, vmax):
    v = vb_for(city, "CO")
    assert v is not None
    assert vmin <= v <= vmax


@pytest.mark.parametrize("city,vmin,vmax", [
    ("Madrid",    24.0, 28.0),
    ("Barcelona", 25.0, 30.0),
    ("Vigo",      27.0, 32.0),
    ("Zaragoza",  27.0, 32.0),
    ("Sevilla",   24.0, 28.0),
])
def test_vb_espana(city, vmin, vmax):
    v = vb_for(city, "ES", code="CTE")
    assert v is not None
    assert vmin <= v <= vmax


def test_vb_for_accent_insensitive():
    assert vb_for("Concepción", "CL") == vb_for("Concepcion", "CL")
    assert vb_for("CADIZ", "ES") == vb_for("Cadiz", "ES")


def test_vb_for_unknown_returns_none():
    assert vb_for("Atlantis", "CL") is None
    assert vb_for("Santiago", "ZZ") is None
