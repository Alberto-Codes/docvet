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
    `docvet.checks.enrichment`: Missing docstring section detection.
    `docvet.checks.freshness`: Stale docstring detection via git.
    `docvet.checks.coverage`: Missing ``__init__.py`` detection.
    `docvet.checks.griffe_compat`: Griffe rendering compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal


@_dataclass(frozen=True)
class Finding:
    """A docstring quality finding.

    Findings are immutable records produced by check modules to report
    missing or incomplete docstring sections. All check modules (enrichment,
    freshness, griffe, coverage) return list[Finding] to the CLI layer.

    The 6-field shape is stable for v1 and will not change within the v1
    lifecycle (no fields added, removed, or renamed).

    Attributes:
        file (str): Source file path where the finding was detected.
        line (int): Line number of the symbol definition (def/class keyword
            line).
        symbol (str): Name of the symbol with the issue
            (function/class/module name).
        rule (str): Kebab-case rule identifier (e.g., ``"missing-raises"``).
        message (str): Human-readable description of the issue.
        category (str): Severity classification (``"required"`` or
            ``"recommended"``).

    Examples:
        Create a finding for a function missing a Raises section:

        ```python
        Finding(
            "cli.py",
            42,
            "main",
            "missing-raises",
            "Function 'main' raises Exit",
            "required",
        )
        ```
    """

    file: str
    line: int
    symbol: str
    rule: str
    message: str
    category: _Literal["required", "recommended"]

    def __post_init__(self) -> None:
        """Validate Finding fields after initialization.

        Raises:
            ValueError: If any field has an invalid value.
        """
        if not self.file:
            raise ValueError("file must be non-empty")
        if self.line < 1:
            raise ValueError(f"line must be >= 1, got {self.line}")
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        if not self.rule:
            raise ValueError("rule must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")
        if self.category not in ("required", "recommended"):
            raise ValueError(
                f'category must be "required" or "recommended", got {self.category!r}'
            )


# Re-export check functions for convenience imports.
# These imports MUST come after the Finding class definition to avoid
# circular imports (each check submodule imports Finding from this package).
from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import (
    check_freshness_diff,
    check_freshness_drift,
)
from docvet.checks.griffe_compat import check_griffe_compat

__all__ = [
    "Finding",
    "check_coverage",
    "check_enrichment",
    "check_freshness_diff",
    "check_freshness_drift",
    "check_griffe_compat",
]
