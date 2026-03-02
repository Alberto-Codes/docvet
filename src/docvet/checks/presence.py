"""Presence check for missing docstrings.

Detects public symbols (modules, classes, functions, methods) that lack
a docstring, and reports per-file coverage statistics via
:class:`PresenceStats`. Uses stdlib ``ast`` only — no runtime
dependencies beyond what docvet already requires. Complements ruff
D100–D107 by adding coverage metrics and pipeline integration.

Examples:
    Run the presence check on a source string:

    ```python
    from docvet.checks.presence import check_presence
    from docvet.config import PresenceConfig

    findings, stats = check_presence(source, "app.py", PresenceConfig())
    ```

See Also:
    [`docvet.checks`][]: Package-level re-exports.
    [`docvet.config`][]: ``PresenceConfig`` for check configuration.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from docvet.ast_utils import Symbol, get_documented_symbols
from docvet.checks._finding import Finding
from docvet.config import PresenceConfig

__all__ = ["PresenceStats", "check_presence"]


@dataclass(frozen=True)
class PresenceStats:
    """Per-file docstring coverage statistics.

    Attributes:
        documented (int): Number of symbols that have a docstring.
        total (int): Total number of symbols checked (after filtering).

    Examples:
        ```python
        stats = PresenceStats(documented=3, total=5)
        assert stats.documented + 2 == stats.total
        ```
    """

    documented: int
    total: int

    @property
    def percentage(self) -> float:
        """Coverage as a percentage (0.0–100.0).

        Returns 100.0 when no symbols were checked (vacuous truth).
        """
        return (self.documented / self.total * 100.0) if self.total > 0 else 100.0


def _should_skip(symbol: Symbol, config: PresenceConfig) -> bool:
    """Determine whether a symbol should be excluded from presence checking.

    Args:
        symbol: The extracted AST symbol to evaluate.
        config: Presence configuration with ignore flags.

    Returns:
        ``True`` if the symbol should be skipped, ``False`` otherwise.
    """
    name = symbol.name

    # Module symbols are never filtered by name-based rules.
    if symbol.kind == "module":
        return False

    # __init__ has its own flag, checked before the general magic rule.
    if name == "__init__":
        return config.ignore_init

    # Magic methods: __repr__, __str__, etc.
    if name.startswith("__") and name.endswith("__"):
        return config.ignore_magic

    # Private symbols: single underscore prefix (but not dunder).
    if name.startswith("_"):
        return config.ignore_private

    return False


def check_presence(
    source: str,
    file_path: str,
    config: PresenceConfig,
) -> tuple[list[Finding], PresenceStats]:
    """Detect public symbols that lack a docstring.

    Parses *source* into an AST, extracts all documentable symbols via
    :func:`~docvet.ast_utils.get_documented_symbols`, applies the
    filtering rules from *config*, and returns one
    :class:`~docvet.checks._finding.Finding` per undocumented symbol
    together with per-file coverage statistics.

    Args:
        source: Raw Python source text.
        file_path: Relative file path used in Finding construction.
        config: Presence configuration controlling ignore flags.

    Returns:
        A tuple of ``(findings, stats)`` where *findings* is a list of
        :class:`~docvet.checks._finding.Finding` instances for
        undocumented symbols and *stats* is a :class:`PresenceStats`
        with coverage counts.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], PresenceStats(documented=0, total=0)

    # Empty files have no symbols worth checking.
    if not tree.body:
        return [], PresenceStats(documented=0, total=0)

    symbols = get_documented_symbols(tree)

    findings: list[Finding] = []
    documented = 0
    total = 0

    for symbol in symbols:
        if _should_skip(symbol, config):
            continue

        total += 1

        if symbol.docstring is not None:
            documented += 1
            continue

        # Build message: module is special, others get "Public" prefix.
        if symbol.kind == "module":
            message = "Module has no docstring"
        else:
            message = f"Public {symbol.kind} has no docstring"

        findings.append(
            Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-docstring",
                message=message,
                category="required",
            )
        )

    return findings, PresenceStats(documented=documented, total=total)
