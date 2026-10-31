"""Tests de la jerarquia de excepciones."""
from __future__ import annotations
import pytest

from windloads.exceptions import (
    WindLoadError, CodeError, GeometryError,
    ConfigurationError, DependencyError,
)


def test_hierarchy():
    for cls in (CodeError, GeometryError, ConfigurationError, DependencyError):
        assert issubclass(cls, WindLoadError)


def test_can_catch_via_base():
    with pytest.raises(WindLoadError):
        raise CodeError("ASCE7 fuera de rango")
    with pytest.raises(WindLoadError):
        raise GeometryError("slope invalido")


def test_can_catch_specific():
    with pytest.raises(CodeError):
        raise CodeError("x")
    with pytest.raises(GeometryError):
        raise GeometryError("x")
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("x")
    with pytest.raises(DependencyError):
        raise DependencyError("x")


def test_reexport_from_package():
    import windloads
    assert windloads.WindLoadError is WindLoadError
    assert windloads.CodeError is CodeError
