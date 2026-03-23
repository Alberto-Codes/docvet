"""Shared fixtures for enrichment check tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_active_style():
    """Reset module-level _active_style after each test.

    ``check_enrichment()`` sets a module-level ``_active_style`` global
    before dispatching rules.  Without cleanup, sphinx-mode tests leak
    into subsequent Google-mode tests when ``pytest-randomly`` reorders
    across files.
    """
    import docvet.checks.enrichment as enrichment_mod

    yield
    enrichment_mod._active_style = "google"
