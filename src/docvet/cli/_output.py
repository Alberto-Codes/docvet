"""CLI output pipeline — format dispatch, coverage lines, and exit logic.

Handles the unified output pipeline for all CLI commands: resolves
output format, dispatches to formatters, writes quality summaries,
and exits with appropriate codes.

See Also:
    [`docvet.cli`][]: CLI application and subcommands.
    [`docvet.reporting`][]: Report formatters consumed by the pipeline.

Examples:
    The output pipeline is invoked by each CLI subcommand:

    ```python
    _output_and_exit(ctx, findings_by_check, config, file_count, checks)
    ```
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import typer

import docvet.cli as _cli_pkg
from docvet.checks import Finding
from docvet.checks.presence import PresenceStats
from docvet.config import DocvetConfig
from docvet.reporting import CheckQuality


def _emit_findings(
    resolved_fmt: str,
    all_findings: list[Finding],
    output_path: str | None,
    no_color: bool,
    file_count: int,
    *,
    presence_stats: PresenceStats | None = None,
    min_coverage: float = 0.0,
    quality: dict[str, CheckQuality] | None = None,
) -> None:
    """Write findings to stdout or a file in the resolved format.

    Dispatches to the appropriate formatter based on ``resolved_fmt``.
    JSON format always emits output (even with zero findings). For
    non-JSON formats, output is skipped when there are no findings
    (no file is written and nothing is printed to stdout).

    Args:
        resolved_fmt: One of ``"terminal"``, ``"markdown"``, or ``"json"``.
        all_findings: Flattened list of findings across all checks.
        output_path: File path to write to, or ``None`` for stdout.
        no_color: Whether to suppress ANSI color in terminal output.
        file_count: Number of files checked (used by JSON format).
        presence_stats: Aggregate presence coverage stats for JSON output.
        min_coverage: Coverage threshold from config for JSON output.
        quality: Per-check quality data for JSON output, or *None*.
    """
    if resolved_fmt == "json":
        json_output = _cli_pkg.format_json(
            all_findings,
            file_count,
            presence_stats=presence_stats,
            min_coverage=min_coverage,
            quality=quality,
        )
        if output_path:
            Path(output_path).write_text(json_output)
        else:
            sys.stdout.write(json_output)
    elif output_path and all_findings:
        _cli_pkg.write_report(all_findings, Path(output_path), fmt=resolved_fmt)
    elif all_findings:
        if resolved_fmt == "markdown":
            sys.stdout.write(_cli_pkg.format_markdown(all_findings))
        else:
            sys.stdout.write(_cli_pkg.format_terminal(all_findings, no_color=no_color))


def _format_coverage_line(stats: PresenceStats, threshold: float) -> str:
    """Format the verbose coverage status line for stderr.

    Uses :attr:`PresenceStats.percentage` for the coverage calculation.

    Args:
        stats: Aggregate presence coverage stats.
        threshold: Minimum coverage threshold (0.0 means no threshold).

    Returns:
        Formatted coverage line ending with a newline.
    """
    pct = stats.percentage
    if threshold > 0.0:
        status = "passes" if pct >= threshold else "below"
        return (
            f"Docstring coverage: {stats.documented}/{stats.total}"
            f" symbols ({pct:.1f}%) \u2014 {status} {threshold:.1f}% threshold\n"
        )
    return (
        f"Docstring coverage: {stats.documented}/{stats.total} symbols ({pct:.1f}%)\n"
    )


def _resolve_format(fmt_opt: str | None, output_path: str | None) -> str:
    """Resolve the output format from CLI options.

    Uses a three-tier precedence chain: explicit ``--format`` first,
    then ``--output`` implies markdown, then terminal as default.

    Args:
        fmt_opt: Explicit format option value, or *None*.
        output_path: Output file path, or *None*.

    Returns:
        Resolved format string: ``"terminal"``, ``"markdown"``, or ``"json"``.
    """
    if fmt_opt is not None:
        return fmt_opt
    if output_path is not None:
        return "markdown"
    return "terminal"


def _output_and_exit(
    ctx: typer.Context,
    findings_by_check: dict[str, list[Finding]],
    config: DocvetConfig,
    file_count: int,
    checks: list[str],
    *,
    presence_stats: PresenceStats | None = None,
    check_counts: dict[str, int] | None = None,
) -> None:
    """Resolve output options, emit findings, and exit with proper code.

    Implements the unified output pipeline: resolves ``no_color`` from
    environment and TTY state, optionally prints a verbose header to
    stderr for multi-check runs, resolves the output format via a
    three-tier precedence chain (explicit ``--format``, then
    ``--output`` implies markdown, then terminal default), delegates
    to :func:`_emit_findings` for format dispatch, and raises
    ``typer.Exit`` with the appropriate exit code.

    Args:
        ctx: Typer context carrying global options in ``ctx.obj``.
        findings_by_check: Findings grouped by check name.
        config: Loaded docvet configuration.
        file_count: Number of files that were checked.
        checks: List of check names that were run.
        presence_stats: Aggregate presence coverage stats, or *None*
            when the presence check did not run.
        check_counts: Per-check item counts for quality computation,
            or *None* when ``--summary`` is not active.

    Raises:
        typer.Exit: With code 0 when no fail-on findings, code 1 otherwise.
    """
    output_path = ctx.obj.get("output")
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)
    summary = ctx.obj.get("summary", False)
    fmt_opt = ctx.obj.get("format")

    # 1. Resolve no_color
    no_color = (
        os.environ.get("NO_COLOR", "") != ""
        or not sys.stdout.isatty()
        or output_path is not None
    )

    # 2. Flatten findings
    all_findings: list[Finding] = []
    for findings in findings_by_check.values():
        all_findings.extend(findings)

    # 3. Verbose header to stderr (only for multi-check runs)
    if verbose and not quiet and len(checks) > 1:
        sys.stderr.write(_cli_pkg.format_verbose_header(file_count, checks))

    # 4. Verbose coverage line
    if verbose and not quiet and presence_stats is not None:
        sys.stderr.write(
            _format_coverage_line(presence_stats, config.presence.min_coverage)
        )

    # 5. Compute quality if --summary and counts available
    quality = None
    if summary and check_counts is not None:
        quality = _cli_pkg.compute_quality(findings_by_check, check_counts)

    # 6. Resolve format, emit findings, exit
    resolved_fmt = _resolve_format(fmt_opt, output_path)
    _emit_findings(
        resolved_fmt,
        all_findings,
        output_path,
        no_color,
        file_count,
        presence_stats=presence_stats,
        min_coverage=config.presence.min_coverage,
        quality=quality if resolved_fmt == "json" else None,
    )

    # 7. Quality summary to stderr (after findings, before exit)
    if summary and not quiet and quality is not None:
        sys.stderr.write(_cli_pkg.format_quality_summary(quality))

    raise typer.Exit(
        _cli_pkg.determine_exit_code(
            findings_by_check, config, presence_stats=presence_stats
        )
    )
