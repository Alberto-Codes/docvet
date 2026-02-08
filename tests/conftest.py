"""Shared test fixtures for docvet."""

from __future__ import annotations

import ast

import pytest


@pytest.fixture
def parse_source():
    """Factory to parse Python source into an AST module."""

    def _parse(source: str) -> ast.Module:
        return ast.parse(source)

    return _parse
