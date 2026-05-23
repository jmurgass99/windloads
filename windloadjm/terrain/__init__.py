"""Terrain categories y exposure factors por norma.

Subpackage que re-exporta la API publica historica de terrain.py.
"""
from __future__ import annotations

from ._impl import TerrainProfile  # noqa: F401

__all__ = ["TerrainProfile"]
