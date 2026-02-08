"""Check modules for docstring quality validation.

This package contains all check modules that analyze docstrings for quality
issues. Each check module returns a list of Finding objects representing
detected issues.

The Finding dataclass is the shared API contract between all check modules
(enrichment, freshness, griffe, coverage) and the CLI layer.
"""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal

__all__ = ["Finding"]


@_dataclass(frozen=True)
class Finding:
    """A docstring quality finding.

    Findings are immutable records produced by check modules to report
    missing or incomplete docstring sections. All check modules (enrichment,
    freshness, griffe, coverage) return list[Finding] to the CLI layer.

    The 6-field shape is stable for v1 and will not change within the v1
    lifecycle (no fields added, removed, or renamed).

    Attributes:
        file: Source file path where the finding was detected.
        line: Line number of the symbol definition (def/class keyword line).
        symbol: Name of the symbol with the issue (function/class/module name).
        rule: Kebab-case rule identifier (e.g., "missing-raises").
        message: Human-readable description of the issue.
        category: Severity classification ("required" or "recommended").
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
