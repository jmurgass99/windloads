"""Verifica que el split de components/terrain mantiene backward compat."""
from __future__ import annotations


def test_components_imports():
    """Cualquier import de components debe seguir funcionando."""
    from windloadjm import components  # noqa
    import windloadjm.components as c
    assert hasattr(c, "__path__"), "components debe ser subpackage"


def test_terrain_imports():
    from windloadjm import terrain  # noqa
    import windloadjm.terrain as t
    assert hasattr(t, "__path__"), "terrain debe ser subpackage"


def test_components_star_import_still_works():
    import importlib
    mod = importlib.import_module("windloadjm.components")
    public = [n for n in dir(mod) if not n.startswith("_")]
    assert len(public) >= 1


def test_terrain_star_import_still_works():
    import importlib
    mod = importlib.import_module("windloadjm.terrain")
    public = [n for n in dir(mod) if not n.startswith("_")]
    assert len(public) >= 1


def test_components_known_symbols_present():
    from windloadjm.components import (  # noqa
        ComponentsAndCladding, asce7_GCp, asce7_cc_pressure,
        ec1_cpe_local, gable_roof_GCp, parapet_pressure,
    )


def test_terrain_known_symbols_present():
    from windloadjm.terrain import TerrainProfile  # noqa
