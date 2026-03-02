"""Markdown, terminal, JSON, and summary report generation for docstring findings.

Renders check findings as terminal output (default), markdown reports, or
structured JSON for programmatic consumption. Produces an unconditional
summary line for stderr (with optional coverage percentage from the
presence check), groups findings by file, calculates summary statistics,
and determines the CLI exit code based on finding severity and coverage
threshold enforcement.

Examples:
    Generate a terminal report via the CLI:

    ```bash
    $ docvet check --all
    ```

    Write a markdown report to a file:

    ```bash
    $ docvet check --all --format markdown --output report.md
    ```

    Produce JSON output for agent or CI consumption:

    ```bash
    $ docvet check --all --format json
    ```

See Also:
    [`docvet.cli`][]: Subcommands that invoke report rendering.
    [`docvet.checks`][]: Check functions that produce findings.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from itertools import groupby
from pathlib import Path

import typer

from docvet.checks import Finding
from docvet.checks.presence import PresenceStats
from docvet.config import DocvetConfig

__all__: list[str] = []

_COLORS: dict[str, str] = {
    "required": typer.colors.RED,
    "recommended": typer.colors.YELLOW,
}

_CATEGORY_TO_SEVERITY: dict[str, str] = {
    "required": "high",
    "recommended": "low",
}


def _colorize(text: str, color: str, *, no_color: bool) -> str:
    """Apply ANSI color to text unless no_color is set.

    Args:
        text: The text to colorize.
        color: The typer color constant.
        no_color: If True, return text unchanged.

    Returns:
        The optionally colorized text.
    """
    if no_color:
        return text
    return typer.style(text, fg=color)


def format_terminal(findings: list[Finding], *, no_color: bool = False) -> str:
    """Format findings for terminal output.

    Args:
        findings: List of findings to format.
        no_color: If True, suppress ANSI color codes.

    Returns:
        Formatted terminal output string, or empty string if no findings.
    """
    if not findings:
        return ""

    sorted_findings = sorted(findings, key=lambda f: (f.file, f.line))
    lines: list[str] = []

    for _file_path, group in groupby(sorted_findings, key=lambda f: f.file):
        if lines:
            lines.append("")
        for finding in group:
            tag = _colorize(
                f"[{finding.category}]",
                _COLORS[finding.category],
                no_color=no_color,
            )
            lines.append(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message} {tag}"
            )

    counts = Counter(f.category for f in findings)
    lines.append("")
    lines.append(
        f"{len(findings)} findings "
        f"({counts['required']} required, {counts['recommended']} recommended)"
    )
    return "\n".join(lines) + "\n"


def format_markdown(findings: list[Finding]) -> str:
    """Format findings as a GFM markdown table with summary footer.

    Produces a pipe-delimited table with File, Line, Rule, Symbol,
    Message, and Category columns, followed by a bold summary count.

    Args:
        findings: List of findings to format.

    Returns:
        Formatted markdown table string, or empty string if no findings.
    """
    if not findings:
        return ""

    sorted_findings = sorted(findings, key=lambda f: (f.file, f.line))
    lines: list[str] = [
        "| File | Line | Rule | Symbol | Message | Category |",
        "|------|------|------|--------|---------|----------|",
    ]

    for finding in sorted_findings:
        escaped_message = finding.message.replace("|", "\\|")
        lines.append(
            f"| {finding.file} | {finding.line} | {finding.rule} "
            f"| {finding.symbol} | {escaped_message} | {finding.category} |"
        )

    counts = Counter(f.category for f in findings)
    lines.append("")
    lines.append(
        f"**{len(findings)} findings** "
        f"({counts['required']} required, {counts['recommended']} recommended)"
    )
    return "\n".join(lines) + "\n"


def format_json(
    findings: list[Finding],
    file_count: int,
    *,
    presence_stats: PresenceStats | None = None,
    min_coverage: float = 0.0,
) -> str:
    """Format findings as a structured JSON object.

    Produces a JSON object with a ``findings`` array and a ``summary``
    object. Each finding includes all six ``Finding`` fields plus a
    derived ``severity`` field (``"high"`` for required, ``"low"`` for
    recommended). When *presence_stats* is provided, a
    ``presence_coverage`` object is added using
    :attr:`PresenceStats.percentage` for documented/total counts,
    percentage, threshold, and pass/fail status. Always returns a valid
    JSON object, even when there are no findings.

    Args:
        findings: List of findings to format.
        file_count: Number of files that were checked.
        presence_stats: Aggregate presence coverage stats, or *None*
            when the presence check did not run.
        min_coverage: Coverage threshold from config (0.0 means no
            threshold enforcement).

    Returns:
        JSON string with ``indent=2`` formatting.

    Examples:
        Format findings for JSON output:

        ```python
        from docvet.checks import Finding

        fs = [Finding("a.py", 1, "f", "missing-raises", "msg", "required")]
        result = format_json(fs, 10)
        # '{"findings": [...], "summary": {"total": 1, ...}}'
        ```
    """
    sorted_findings = sorted(findings, key=lambda f: (f.file, f.line))
    counts = Counter(f.category for f in findings)

    obj: dict[str, object] = {
        "findings": [
            {
                "file": f.file,
                "line": f.line,
                "symbol": f.symbol,
                "rule": f.rule,
                "message": f.message,
                "category": f.category,
                "severity": _CATEGORY_TO_SEVERITY[f.category],
            }
            for f in sorted_findings
        ],
        "summary": {
            "total": len(findings),
            "by_category": {
                "required": counts.get("required", 0),
                "recommended": counts.get("recommended", 0),
            },
            "files_checked": file_count,
        },
    }
    if presence_stats is not None:
        pct = presence_stats.percentage
        obj["presence_coverage"] = {
            "documented": presence_stats.documented,
            "total": presence_stats.total,
            "percentage": round(pct, 1),
            "threshold": min_coverage,
            "passed": pct >= min_coverage,
        }
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def format_summary(
    file_count: int,
    checks: Sequence[str],
    findings: list[Finding],
    elapsed: float,
    *,
    coverage_pct: float | None = None,
) -> str:
    """Format the unconditional summary line for stderr.

    Produces a one-line summary showing file count, checks that ran,
    finding count with category breakdown, optional coverage percentage,
    and elapsed time. Uses the "Vetted" brand verb and an em dash
    separator.

    Args:
        file_count: Number of files that were checked.
        checks: List of check names that were run.
        findings: All findings across all checks.
        elapsed: Total elapsed time in seconds.
        coverage_pct: Docstring coverage percentage from the presence
            check. When not *None*, appended to the detail string.

    Returns:
        Formatted summary string ending with a newline.

    Examples:
        Zero findings:

        ```python
        format_summary(12, ["enrichment", "freshness"], [], 1.5)
        # 'Vetted 12 files [enrichment, freshness] — no findings. (1.5s)'
        ```

        With findings and coverage:

        ```python
        from docvet.checks import Finding

        fs = [Finding("f", 1, "s", "r", "m", "required")]
        format_summary(1, ["enrichment"], fs, 0.3, coverage_pct=87.0)
        # 'Vetted 1 files [enrichment] — 1 findings (...), 87.0% coverage. (0.3s)'
        ```
    """
    check_list = ", ".join(checks)
    if findings:
        counts = Counter(f.category for f in findings)
        detail = (
            f"{len(findings)} findings"
            f" ({counts['required']} required, {counts['recommended']} recommended)"
        )
    else:
        detail = "no findings"
    if coverage_pct is not None:
        detail = f"{detail}, {coverage_pct:.1f}% coverage"
    return (
        f"Vetted {file_count} files [{check_list}] \u2014 {detail}. ({elapsed:.1f}s)\n"
    )


def format_verbose_header(file_count: int, checks: Sequence[str]) -> str:
    """Format the verbose mode header line.

    Args:
        file_count: Number of files being checked.
        checks: List of check names being run.

    Returns:
        Formatted header string.
    """
    return f"Checking {file_count} files [{', '.join(checks)}]\n"


def write_report(
    findings: list[Finding],
    output: Path,
    *,
    fmt: str = "markdown",
    file_count: int = 0,
) -> None:
    """Write formatted findings to a file.

    Args:
        findings: List of findings to write.
        output: Path to write the report to.
        fmt: Output format — ``"markdown"``, ``"terminal"``, or
            ``"json"``.
        file_count: Number of files checked. Only used when
            *fmt* is ``"json"`` (for the summary object).

    Raises:
        FileNotFoundError: If the parent directory does not exist.
        ValueError: If fmt is not a recognized format.
    """
    if fmt == "markdown":
        content = format_markdown(findings)
    elif fmt == "terminal":
        content = format_terminal(findings, no_color=True)
    elif fmt == "json":
        content = format_json(findings, file_count)
    else:
        msg = f"Unknown format: {fmt!r}. Expected 'markdown', 'terminal', or 'json'"
        raise ValueError(msg)
    output.write_text(content)


def determine_exit_code(
    findings_by_check: dict[str, list[Finding]],
    config: DocvetConfig,
    *,
    presence_stats: PresenceStats | None = None,
) -> int:
    """Determine the CLI exit code based on findings and fail_on config.

    Returns 1 if any ``fail_on`` check has findings, or if the
    presence coverage threshold (compared via
    :attr:`PresenceStats.percentage`) is configured and not met.
    Returns 0 otherwise.

    Args:
        findings_by_check: Findings grouped by check name.
        config: The docvet configuration with fail_on list.
        presence_stats: Aggregate presence coverage stats, or *None*
            when the presence check did not run.

    Returns:
        1 if any fail_on check has findings or coverage is below
        threshold, 0 otherwise.
    """
    for check in config.fail_on:
        if findings_by_check.get(check, []):
            return 1
    if presence_stats is not None and config.presence.min_coverage > 0.0:
        if presence_stats.percentage < config.presence.min_coverage:
            return 1
    return 0
