"""Markdown and terminal report generation for docstring findings."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from itertools import groupby
from pathlib import Path

import typer

from docvet.checks import Finding
from docvet.config import DocvetConfig

_COLORS: dict[str, str] = {
    "required": typer.colors.RED,
    "recommended": typer.colors.YELLOW,
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
    """Format findings as a GFM markdown table.

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
    findings: list[Finding], output: Path, *, fmt: str = "markdown"
) -> None:
    """Write formatted findings to a file.

    Args:
        findings: List of findings to write.
        output: Path to write the report to.
        fmt: Output format, either "markdown" or "terminal".

    Raises:
        FileNotFoundError: If the parent directory does not exist.
    """
    if fmt == "markdown":
        content = format_markdown(findings)
    else:
        content = format_terminal(findings, no_color=True)
    output.write_text(content)


def determine_exit_code(
    findings_by_check: dict[str, list[Finding]], config: DocvetConfig
) -> int:
    """Determine the CLI exit code based on findings and fail_on config.

    Args:
        findings_by_check: Findings grouped by check name.
        config: The docvet configuration with fail_on list.

    Returns:
        1 if any fail_on check has findings, 0 otherwise.
    """
    for check in config.fail_on:
        if findings_by_check.get(check, []):
            return 1
    return 0
