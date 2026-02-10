"""Freshness check for stale docstrings via git diff and git blame."""

from __future__ import annotations

import re
from typing import Literal

from docvet.ast_utils import Symbol, map_lines_to_symbols  # noqa: F401
from docvet.checks import Finding
from docvet.config import FreshnessConfig  # noqa: F401

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_HUNK_PATTERN = re.compile(r"^@@ .+\+(\d+)(?:,(\d+))? @@")

# Rule identifier string literals (for reference):
# "stale-signature"  — function signature changed, docstring not updated
# "stale-body"       — function body changed, docstring not updated
# "stale-import"     — import changed, docstring not updated


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _build_finding(
    file_path: str,
    symbol: Symbol,
    rule: str,
    message: str,
    category: Literal["required", "recommended"],
) -> Finding:
    """Construct a Finding from freshness detection results.

    Args:
        file_path: Source file path where the finding was detected.
        symbol: The symbol whose docstring is potentially stale.
        rule: Kebab-case rule identifier.
        message: Human-readable description of the issue.
        category: Severity classification.

    Returns:
        A Finding with fields mapped from the symbol and arguments.
    """
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule=rule,
        message=message,
        category=category,
    )


# ---------------------------------------------------------------------------
# Diff mode helpers
# ---------------------------------------------------------------------------


def _parse_diff_hunks(diff_output: str) -> set[int]:
    """Extract changed line numbers from unified diff output.

    Parses ``@@ ... +start,count @@`` hunk headers and expands them
    into a set of affected line numbers in the new file version.

    Args:
        diff_output: Raw unified diff output from ``git diff``.

    Returns:
        A set of 1-based line numbers changed in the new file version.
        Returns an empty set for new files, binary files, or empty input.
    """
    if not diff_output:
        return set()

    changed: set[int] = set()
    is_new_file = False

    for line in diff_output.splitlines():
        if line.startswith("--- /dev/null"):
            is_new_file = True
            continue
        if line.startswith("Binary files"):
            return set()
        match = _HUNK_PATTERN.match(line)
        if match:
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            changed.update(range(start, start + count))

    if is_new_file:
        return set()
    return changed
