"""Internal module defining the Finding dataclass.

This module exists to break the circular import between ``checks/__init__.py``
(which re-exports check functions) and the check submodules (which produce
Finding instances).  External consumers should import Finding from
``docvet.checks``, not from this module.

Examples:
    Import ``Finding`` through the public API::

        from docvet.checks import Finding

See Also:
    [`docvet.checks`][]: Public re-export surface for ``Finding``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__: list[str] = []


@dataclass(frozen=True)
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
    category: Literal["required", "recommended"]

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
