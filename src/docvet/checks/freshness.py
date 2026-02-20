"""Freshness check for stale docstrings via git diff and git blame."""

from __future__ import annotations

import ast
import re
import time
from datetime import datetime, timezone
from typing import Literal

from docvet.ast_utils import Symbol, map_lines_to_symbols
from docvet.checks import Finding
from docvet.config import FreshnessConfig

__all__ = ["check_freshness_diff", "check_freshness_drift"]

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
        ds, de = symbol.docstring_range
        if any(ds <= line <= de for line in changed_lines):
            return None

    # 2. Signature changed → HIGH
    if symbol.signature_range is not None:
        ss, se = symbol.signature_range
        if any(ss <= line <= se for line in changed_lines):
            return "signature"

    # 3. Body changed → MEDIUM
    bs, be = symbol.body_range
    if any(bs <= line <= be for line in changed_lines):
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

    findings.sort(key=lambda f: f.line)
    return findings


# ---------------------------------------------------------------------------
# Drift mode helpers
# ---------------------------------------------------------------------------


def _parse_blame_timestamps(blame_output: str) -> dict[int, int]:
    """Extract per-line modification timestamps from git blame porcelain output.

    Parses ``git blame --line-porcelain`` output and builds a mapping from
    1-based line numbers to Unix timestamps extracted from ``author-time``
    fields.  Uses a simple state machine: each blame block starts with a
    SHA line (setting the current line number), accumulates an
    ``author-time`` value, and emits the mapping entry when a tab-prefixed
    content line is encountered.

    Args:
        blame_output: Raw output from ``git blame --line-porcelain``.

    Returns:
        A dict mapping 1-based line numbers to Unix timestamps.  Returns
        an empty dict for empty or whitespace-only input, and silently
        skips malformed or truncated blame blocks.
    """
    if not blame_output:
        return {}

    timestamps: dict[int, int] = {}
    current_line: int | None = None
    current_timestamp: int | None = None

    for line in blame_output.splitlines():
        # SHA line: 40-hex-chars orig_line final_line [count]
        parts = line.split()
        if len(parts) >= 3 and len(parts[0]) == 40:
            try:
                current_line = int(parts[2])
            except ValueError:
                current_line = None
            current_timestamp = None
            continue

        # author-time line
        if line.startswith("author-time "):
            try:
                current_timestamp = int(line.split()[1])
            except (ValueError, IndexError):
                pass
            continue

        # Tab-prefixed content line — end of blame block
        if line.startswith("\t"):
            if current_line is not None and current_timestamp is not None:
                timestamps[current_line] = current_timestamp
            current_line = None
            current_timestamp = None
            continue

        # All other lines (author, committer, summary, filename, etc.) — skip

    return timestamps


def _compute_drift(
    code_timestamps: list[int],
    doc_timestamps: list[int],
    threshold: int,
) -> bool:
    """Determine whether code has drifted ahead of its docstring.

    Compares the most recent code modification timestamp against the most
    recent docstring modification timestamp.  Drift exceeds the threshold
    when the difference is strictly greater than ``threshold * 86400``
    seconds.

    Args:
        code_timestamps: Unix timestamps for code lines of a symbol.
        doc_timestamps: Unix timestamps for docstring lines of a symbol.
        threshold: Maximum allowed drift in days.

    Returns:
        ``True`` if code is more than *threshold* days newer than the
        docstring, ``False`` otherwise or when either list is empty.
    """
    if not code_timestamps or not doc_timestamps:
        return False
    return max(code_timestamps) - max(doc_timestamps) > threshold * 86400


def _compute_age(
    doc_timestamps: list[int],
    now: int,
    threshold: int,
) -> bool:
    """Determine whether a docstring has aged past a threshold.

    Compares the current time against the most recent docstring
    modification timestamp.  Age exceeds the threshold when the
    difference is strictly greater than ``threshold * 86400`` seconds.

    Args:
        doc_timestamps: Unix timestamps for docstring lines of a symbol.
        now: Current time as a Unix timestamp.
        threshold: Maximum allowed age in days.

    Returns:
        ``True`` if the docstring is more than *threshold* days old,
        ``False`` otherwise or when the list is empty.
    """
    if not doc_timestamps:
        return False
    return now - max(doc_timestamps) > threshold * 86400


def check_freshness_drift(
    file_path: str,
    blame_output: str,
    tree: ast.Module,
    config: FreshnessConfig,
    *,
    now: int | None = None,
) -> list[Finding]:
    """Check a file for stale docstrings using git blame timestamps.

    Parses blame output to extract per-line timestamps, groups them by
    AST symbol, and checks each symbol for drift (code newer than
    docstring) and age (docstring untouched too long).

    Args:
        file_path: Source file path for finding attribution.
        blame_output: Raw output from ``git blame --line-porcelain``.
        tree: Parsed AST module from ``ast.parse()``.
        config: Freshness configuration with threshold values.
        now: Current time as a Unix timestamp.  Defaults to
            ``int(time.time())`` when not provided.

    Returns:
        A list of findings for symbols with stale docstrings, sorted
        by line number.  Returns an empty list when blame output is
        empty or no symbols exceed thresholds.
    """
    if not blame_output:
        return []

    timestamps = _parse_blame_timestamps(blame_output)
    if not timestamps:
        return []

    line_map = map_lines_to_symbols(tree)

    # Group timestamps by symbol into code vs docstring buckets.
    symbol_code_ts: dict[Symbol, list[int]] = {}
    symbol_doc_ts: dict[Symbol, list[int]] = {}

    for line_num, ts in timestamps.items():
        sym = line_map.get(line_num)
        if sym is None:
            continue
        if sym.docstring_range is None:
            continue

        ds, de = sym.docstring_range
        if ds <= line_num <= de:
            symbol_doc_ts.setdefault(sym, []).append(ts)
        else:
            symbol_code_ts.setdefault(sym, []).append(ts)

    effective_now = now if now is not None else int(time.time())

    findings: list[Finding] = []
    all_symbols = set(symbol_code_ts) | set(symbol_doc_ts)

    for sym in all_symbols:
        code_ts = symbol_code_ts.get(sym, [])
        doc_ts = symbol_doc_ts.get(sym, [])
        kind = sym.kind.capitalize()
        doc_max = max(doc_ts) if doc_ts else 0

        if _compute_drift(code_ts, doc_ts, config.drift_threshold):
            code_max = max(code_ts)
            code_date = (
                datetime.fromtimestamp(code_max, tz=timezone.utc).date().isoformat()
            )
            doc_date = (
                datetime.fromtimestamp(doc_max, tz=timezone.utc).date().isoformat()
            )
            days = (code_max - doc_max) // 86400
            message = (
                f"{kind} '{sym.name}' code modified {code_date}, "
                f"docstring last modified {doc_date} ({days} days drift)"
            )
            findings.append(
                _build_finding(file_path, sym, "stale-drift", message, "recommended")
            )

        if _compute_age(doc_ts, effective_now, config.age_threshold):
            doc_date = (
                datetime.fromtimestamp(doc_max, tz=timezone.utc).date().isoformat()
            )
            days = (effective_now - doc_max) // 86400
            message = (
                f"{kind} '{sym.name}' docstring untouched "
                f"since {doc_date} ({days} days)"
            )
            findings.append(
                _build_finding(file_path, sym, "stale-age", message, "recommended")
            )

    findings.sort(key=lambda f: f.line)
    return findings
