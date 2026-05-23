"""Tests Vb map."""
from windloadjm.vb_map import list_locations, lookup_Vb


def test_lookup_existente_case_insensitive():
    a = lookup_Vb("Santiago")
    b = lookup_Vb("santiago")
    c = lookup_Vb("SANTIAGO")
    assert a == b == c
    assert a is not None
    assert a.country == "CL"


def test_lookup_acentos_tolerante():
    a = lookup_Vb("Concepción")
    b = lookup_Vb("Concepcion")
    assert a == b


def test_lookup_inexistente_devuelve_none():
    assert lookup_Vb("Pueblito Fantasma") is None


def test_list_por_pais():
    cl = list_locations("CL")
    assert len(cl) >= 4
    assert all(l.country == "CL" for l in cl)


def test_list_completo():
    assert len(list_locations()) >= 20
