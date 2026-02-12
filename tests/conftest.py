"""Shared test fixtures for docvet."""

from __future__ import annotations

import ast
from typing import Literal

import pytest

from docvet.checks import Finding

_Category = Literal["required", "recommended"]


@pytest.fixture
def parse_source():
    """Factory to parse Python source into an AST module."""

    def _parse(source: str) -> ast.Module:
        return ast.parse(source)

    return _parse


@pytest.fixture
def make_finding():
    """Factory to create Finding instances with sensible defaults."""

    def _make(
        *,
        file: str = "test.py",
        line: int = 1,
        symbol: str = "func",
        rule: str = "test-rule",
        message: str = "test message",
        category: _Category = "required",
    ) -> Finding:
        return Finding(
            file=file,
            line=line,
            symbol=symbol,
            rule=rule,
            message=message,
            category=category,
        )

    return _make
