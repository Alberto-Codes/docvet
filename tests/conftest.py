"""Shared test fixtures for docvet."""

from __future__ import annotations

import ast
import os
from typing import Literal

import pytest

from docvet.checks import Finding

_Category = Literal["required", "recommended", "scaffold"]


@pytest.fixture(autouse=True)
def isolated_git_env(monkeypatch):
    """Strip inherited ``GIT_*`` variables from the test environment.

    Tests build throwaway repositories and shell out to ``git`` with a
    ``cwd``. Git overrides that ``cwd`` when ``GIT_DIR`` or
    ``GIT_INDEX_FILE`` is set, so a suite launched from a git hook —
    which is how the ``pre-push`` hook runs it — would drive those
    commands against the repository being pushed instead of the temp
    repository, failing the tests and rewriting the real index.
    """
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name, raising=False)


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
