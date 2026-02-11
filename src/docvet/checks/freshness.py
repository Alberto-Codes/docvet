"""Freshness check for stale docstrings via git diff and git blame."""

from __future__ import annotations

import ast
import re
from typing import Literal

from docvet.ast_utils import Symbol, map_lines_to_symbols
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

_CLASSIFICATION_MAP: dict[str, tuple[str, Literal["required", "recommended"]]] = {
    "signature": ("stale-signature", "required"),
    "body": ("stale-body", "recommended"),
    "import": ("stale-import", "recommended"),
}


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


def _classify_changed_lines(
    changed_lines: set[int],
    symbol: Symbol,
) -> str | None:
    """Classify changed lines relative to a symbol's ranges.

    Determines the highest-severity change type by checking whether
    changed lines overlap the symbol's docstring, signature, or body
    ranges. Docstring overlap suppresses findings entirely.

    Args:
        changed_lines: Set of 1-based line numbers that changed.
        symbol: The symbol to classify changes against.

    Returns:
        ``"signature"`` for HIGH severity, ``"body"`` for MEDIUM,
        ``"import"`` for LOW, or ``None`` if the docstring was updated
        (finding suppressed).
    """
    # 1. Docstring updated → suppress finding
    if symbol.docstring_range is not None:
        doc_lines = set(range(symbol.docstring_range[0], symbol.docstring_range[1] + 1))
        if changed_lines & doc_lines:
            return None

    # 2. Signature changed → HIGH
    if symbol.signature_range is not None:
        sig_lines = set(range(symbol.signature_range[0], symbol.signature_range[1] + 1))
        if changed_lines & sig_lines:
            return "signature"

    # 3. Body changed → MEDIUM
    body_lines = set(range(symbol.body_range[0], symbol.body_range[1] + 1))
    if changed_lines & body_lines:
        return "body"

    # 4. Else → LOW (import/formatting)
    return "import"


def check_freshness_diff(
    file_path: str,
    diff_output: str,
    tree: ast.Module,
) -> list[Finding]:
    """Check a file for stale docstrings using git diff output.

    Maps changed lines from the diff to AST symbols, classifies the
    change type, and produces findings for symbols whose docstrings
    were not updated alongside code changes.

    Args:
        file_path: Source file path for finding attribution.
        diff_output: Raw unified diff output from ``git diff``.
        tree: Parsed AST module from ``ast.parse()``.

    Returns:
        A list of findings for symbols with stale docstrings.
        Returns an empty list when the diff is empty or all changed
        symbols have updated docstrings.
    """
    changed_lines = _parse_diff_hunks(diff_output)
    if not changed_lines:
        return []

    line_map = map_lines_to_symbols(tree)

    # Invert: group changed lines by symbol
    symbol_changes: dict[Symbol, set[int]] = {}
    for line_num in changed_lines:
        sym = line_map.get(line_num)
        if sym is not None:
            if sym not in symbol_changes:
                symbol_changes[sym] = set()
            symbol_changes[sym].add(line_num)

    findings: list[Finding] = []
    for symbol, its_changed_lines in symbol_changes.items():
        if symbol.docstring_range is None:
            continue  # FR54: skip undocumented symbols

        classification = _classify_changed_lines(its_changed_lines, symbol)
        if classification is None:
            continue  # Docstring was updated

        rule, category = _CLASSIFICATION_MAP[classification]
        kind = symbol.kind.capitalize()
        message = (
            f"{kind} '{symbol.name}' {classification} changed but docstring not updated"
        )
        findings.append(_build_finding(file_path, symbol, rule, message, category))

    return findings
