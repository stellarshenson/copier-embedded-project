"""Fixtures of the template tests."""

from __future__ import annotations

import pytest
from helpers import MATRIX, bake


@pytest.fixture(params=MATRIX)
def project(request):
    """A rendered project of the platform matrix, with the answers that produced it."""
    with bake(request.param) as path:
        yield path, request.param
