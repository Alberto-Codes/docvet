"""Inline suppression comment parser and finding filter.

Parses ``# docvet: ignore[rule]`` and ``# docvet: ignore-file[rule]``
comments from Python source files using the ``tokenize`` module, then
filters findings into active and suppressed partitions. Bracket content
is captured broadly and validated in :func:`_parse_rules` so that
non-standard input (uppercase, underscores) produces warnings rather
than silently falling back to blanket suppression. Operates as a
post-filter on the findings list — no ``_check_*`` functions are modified.

Attributes:
    KNOWN_RULES: Set of all valid docvet rule IDs for validation.

Examples:
    Parse and filter in one pass:

    ```python
    from docvet.cli._suppression import filter_findings, parse_suppression_directives

    smap = parse_suppression_directives(source, "app.py")
    active, suppressed = filter_findings(findings, "app.py", smap)
    ```

See Also:
    [`docvet.cli._output`][]: Output pipeline that invokes the filter.
    [`docvet.checks`][]: Check modules that produce findings.
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from dataclasses import dataclass, field

from docvet.checks import Finding
from docvet.mcp._catalog import _RULE_TO_CHECK

# Complete set of known rule IDs for validation.
KNOWN_RULES: frozenset[str] = frozenset(_RULE_TO_CHECK)

# Regex for the directive payload after ``# docvet:``.
# Matches: ignore, ignore[rule], ignore[rule1,rule2], ignore-file, ignore-file[rule], etc.
# The bracket character class is deliberately broad (``[^\]]+``) so that
# non-standard input (uppercase, underscores) is captured and forwarded
# to ``_parse_rules`` for validation, rather than silently falling back
# to blanket suppression.
_DIRECTIVE_RE = re.compile(
    r"#\s*docvet\s*:\s*"
    r"(?P<kind>ignore-file|ignore)"
    r"(?:\[\s*(?P<rules>[^\]]+)\s*\])?"
)


@dataclass
class SuppressionMap:
    """Parsed suppression directives for a single file.

    Attributes:
        line_directives (dict[int, set[str] | None]): Line-level suppressions.
            Key is the 1-based line number; value is a set of rule IDs or
            ``None`` for blanket suppression.
        file_rules (set[str]): File-level rule suppressions.
        file_blanket (bool): Whether the entire file is blanket-suppressed.

    Examples:
        Create a map with a single line-level suppression:

        ```python
        smap = SuppressionMap(line_directives={1: {"missing-raises"}})
        ```
    """

    line_directives: dict[int, set[str] | None] = field(default_factory=dict)
    file_rules: set[str] = field(default_factory=set)
    file_blanket: bool = False


def parse_suppression_directives(
    source: str,
    file_path: str,
) -> SuppressionMap:
    """Parse suppression comments from Python source code.

    Uses the ``tokenize`` module to extract only real ``COMMENT`` tokens,
    avoiding false positives from ``#`` inside string literals. Validates
    rule IDs against the known rule set and emits warnings to stderr for
    unknown or invalid rules. Such rule IDs are recorded for forward-
    compatibility but only suppress findings when they match exactly.

    Args:
        source: Python source code string.
        file_path: File path for warning messages.

    Returns:
        A :class:`SuppressionMap` containing all parsed directives.

    Examples:
        Parse a file with a single suppression:

        ```python
        smap = parse_suppression_directives(source, "app.py")
        assert 1 in smap.line_directives
        ```
    """
    result = SuppressionMap()

    if not source:
        return result

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type != tokenize.COMMENT:
                continue
            match = _DIRECTIVE_RE.match(tok.string)
            if not match:
                continue

            kind = match.group("kind")
            raw_rules = match.group("rules")
            line_no = tok.start[0]

            rules = _parse_rules(raw_rules, file_path, line_no)

            if kind == "ignore-file":
                if rules is None:
                    result.file_blanket = True
                else:
                    result.file_rules.update(rules)
            else:
                result.line_directives[line_no] = rules

    except tokenize.TokenError:
        pass

    return result


def _parse_rules(
    raw: str | None,
    file_path: str,
    line_no: int,
) -> set[str] | None:
    """Parse and validate rule IDs from bracket content.

    Args:
        raw: Comma-separated rule string from the bracket group, or
            ``None`` for blanket suppression.
        file_path: File path for warning messages.
        line_no: Line number for warning messages.

    Returns:
        A set of rule IDs, or ``None`` for blanket suppression.
    """
    if raw is None:
        return None

    rules: set[str] = set()
    for part in raw.split(","):
        rule = part.strip()
        if not rule:
            continue
        if rule not in KNOWN_RULES:
            sys.stderr.write(
                f"warning: {file_path}:{line_no}: "
                f"unknown rule {rule!r} in suppression comment\n"
            )
        rules.add(rule)

    return rules if rules else None


def filter_findings(
    findings: list[Finding],
    file_path: str,
    suppression: SuppressionMap,
) -> tuple[list[Finding], list[Finding]]:
    """Partition findings into active and suppressed lists.

    Applies file-level blanket, file-level rule, and line-level
    suppressions in that order. Findings are not modified — the
    original objects are placed into either the active or suppressed
    list.

    Args:
        findings: Findings for a single file.
        file_path: The file path (unused in matching, for API symmetry).
        suppression: Parsed suppression map for the file.

    Returns:
        A tuple of ``(active, suppressed)`` finding lists.

    Examples:
        Filter with a blanket file suppression:

        ```python
        smap = SuppressionMap(file_blanket=True)
        active, suppressed = filter_findings(findings, "app.py", smap)
        assert len(active) == 0
        ```
    """
    if not findings:
        return [], []

    active: list[Finding] = []
    suppressed: list[Finding] = []

    for finding in findings:
        if _is_suppressed(finding, suppression):
            suppressed.append(finding)
        else:
            active.append(finding)

    return active, suppressed


def _is_suppressed(finding: Finding, suppression: SuppressionMap) -> bool:
    """Check if a single finding is suppressed.

    Args:
        finding: The finding to check.
        suppression: Parsed suppression map for the file.

    Returns:
        ``True`` if the finding should be suppressed.
    """
    # File-level blanket
    if suppression.file_blanket:
        return True

    # File-level rule
    if finding.rule in suppression.file_rules:
        return True

    # Line-level
    line_rules = suppression.line_directives.get(finding.line)
    if line_rules is None and finding.line in suppression.line_directives:
        # None entry = blanket suppression for that line
        return True
    if line_rules is not None and finding.rule in line_rules:
        return True

    return False
