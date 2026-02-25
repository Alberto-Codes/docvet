"""Check modules for docstring quality validation.

This package contains all check modules that analyze docstrings for quality
issues. Each check module returns a list of Finding objects representing
detected issues.

The Finding dataclass is the shared API contract between all check modules
(enrichment, freshness, griffe, coverage) and the CLI layer.

Attributes:
    Finding: Immutable dataclass representing a docstring quality finding.

Examples:
    Import and inspect a finding:

    ```python
    from docvet.checks import Finding

    f = Finding("app.py", 10, "foo", "missing-raises", "msg", "required")
    assert f.rule == "missing-raises"
    ```

See Also:
    [`docvet.checks.enrichment`][]: Missing docstring section detection.
    [`docvet.checks.freshness`][]: Stale docstring detection via git.
    [`docvet.checks.coverage`][]: Missing ``__init__.py`` detection.
    [`docvet.checks.griffe_compat`][]: Griffe rendering compatibility.
"""

from __future__ import annotations

from docvet.checks._finding import Finding
from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
from docvet.checks.griffe_compat import check_griffe_compat

__all__ = [
    "Finding",
    "check_coverage",
    "check_enrichment",
    "check_freshness_diff",
    "check_freshness_drift",
    "check_griffe_compat",
]
