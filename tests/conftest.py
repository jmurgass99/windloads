"""Configuración compartida de pytest para WindLoadJm."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def rng_seed_42():
    import numpy as np
    return np.random.default_rng(42)


@pytest.fixture
def examples_dir() -> Path:
    return REPO_ROOT / "examples"
