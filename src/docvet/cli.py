"""Typer CLI application for docvet.

Defines the ``typer.Typer`` app with subcommands for each check layer
(``presence``, ``enrichment``, ``freshness``, ``coverage``, ``griffe``,
``lsp``, ``mcp``), the combined ``check`` entry point, and the
``config`` introspection command. All check subcommands
accept positional file arguments (``docvet check src/foo.py``) and the
``--files`` option, share three-tier verbosity control
(quiet/default/verbose) via dual-registered ``--verbose`` and
``-q``/``--quiet`` flags, emit a unified
``Vetted N files [check] — ...`` summary line on stderr, and support
``--format json`` for structured machine-readable output. The
``--summary`` flag adds per-check quality percentages to stderr
(terminal) or a ``quality`` object to JSON output. Output formatting is
delegated to :func:`_emit_findings`, which dispatches to the appropriate
formatter in :mod:`docvet.reporting`.

Examples:
    Run all checks on changed files:

    ```bash
    $ docvet check
    ```

    Check specific files:

    ```bash
    $ docvet check src/foo.py src/bar.py
    ```

    Run the enrichment check on the entire codebase:

    ```bash
    $ docvet enrichment --all
    ```

See Also:
    [`docvet.checks`][]: Public API re-exports for check functions.
    [`docvet.config`][]: Configuration dataclasses loaded by the CLI.
    [`docvet.discovery`][]: File discovery invoked by each subcommand.
"""

from __future__ import annotations

import ast
import enum
import importlib.metadata
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated

import typer

from docvet.ast_utils import get_documented_symbols
from docvet.checks import Finding
from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
from docvet.checks.griffe_compat import check_griffe_compat
from docvet.checks.presence import PresenceStats, check_presence
from docvet.config import (
    DocvetConfig,
    format_config_json,
    format_config_toml,
    get_user_keys,
    load_config,
)
from docvet.discovery import DiscoveryMode, discover_files
from docvet.reporting import (
    CheckQuality,
    compute_quality,
    determine_exit_code,
    format_json,
    format_markdown,
    format_quality_summary,
    format_summary,
    format_terminal,
    format_verbose_header,
    write_report,
)

__all__: list[str] = []

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OutputFormat(enum.StrEnum):
    """Output format for reports.

    Examples:
        Select terminal output for CI pipelines:

        ```python
        fmt = OutputFormat.TERMINAL  # "terminal"
        ```

        Select markdown output for saved reports:

        ```python
        fmt = OutputFormat.MARKDOWN  # "markdown"
        ```

        Select JSON output for programmatic consumption:

        ```python
        fmt = OutputFormat.JSON  # "json"
        ```
    """

    TERMINAL = "terminal"
    MARKDOWN = "markdown"
    JSON = "json"


class FreshnessMode(enum.StrEnum):
    """Freshness check strategy for the ``--mode`` option.

    Examples:
        Use diff mode for fast CI checks against recent changes:

        ```python
        mode = FreshnessMode.DIFF  # "diff"
        ```

        Use drift mode for periodic sweeps via git blame timestamps:

        ```python
        mode = FreshnessMode.DRIFT  # "drift"
        ```
    """

    DIFF = "diff"
    DRIFT = "drift"


# ---------------------------------------------------------------------------
# Shared option type aliases
# ---------------------------------------------------------------------------

StagedOption = Annotated[bool, typer.Option("--staged", help="Run on staged files.")]
AllOption = Annotated[bool, typer.Option("--all", help="Run on entire codebase.")]
FilesOption = Annotated[
    list[str] | None,
    typer.Option(
        "--files", help="Run on specific files (alternative to positional args)."
    ),
]
FilesArgument = Annotated[
    list[str] | None,
    typer.Argument(help="Files to check (positional)."),
]
ConfigOption = Annotated[
    Path | None, typer.Option("--config", help="Path to pyproject.toml.")
]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = typer.Typer(help="Comprehensive docstring quality vetting.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _merge_file_args(
    positional: list[str] | None,
    option: list[str] | None,
) -> list[str] | None:
    """Merge positional file arguments with the ``--files`` option.

    Returns the resolved file list: positional args, ``--files`` option,
    or *None* if neither was provided.

    Args:
        positional: File paths from positional arguments.
        option: File paths from the ``--files`` option.

    Returns:
        The merged file list, or *None* if no files were specified.

    Raises:
        typer.BadParameter: If both positional args and ``--files`` are
            provided.
    """
    if positional and option:
        raise typer.BadParameter("Cannot use both positional files and --files.")
    if positional:
        return positional
    return option


def _resolve_discovery_mode(
    staged: bool,
    all_files: bool,
    files: list[str] | None,
) -> DiscoveryMode:
    """Validate mutual exclusivity and return the selected discovery mode.

    Args:
        staged: Whether ``--staged`` was passed.
        all_files: Whether ``--all`` was passed.
        files: Explicit file list from ``--files`` or positional args,
            or *None*.

    Returns:
        The resolved :class:`DiscoveryMode`.

    Raises:
        typer.BadParameter: If more than one discovery flag is set.
    """
    flags_set = sum((staged, all_files, files is not None))
    if flags_set > 1:
        raise typer.BadParameter("Use only one of: --staged, --all, or file arguments.")
    if staged:
        return DiscoveryMode.STAGED
    if all_files:
        return DiscoveryMode.ALL
    if files is not None:
        return DiscoveryMode.FILES
    return DiscoveryMode.DIFF


def _discover_and_handle(
    ctx: typer.Context,
    mode: DiscoveryMode,
    files: list[str] | None,
) -> list[Path]:
    """Discover files and handle empty results.

    Pulls config from ``ctx.obj["docvet_config"]``, converts the raw
    ``--files`` strings to :class:`~pathlib.Path` objects, calls
    :func:`discover_files`, and handles the empty-list case with a
    user-friendly message. Prints file count to stderr when verbose
    is enabled and quiet is not.

    Args:
        ctx: Typer context carrying ``docvet_config``, ``verbose``,
            and ``quiet``.
        mode: The resolved discovery mode.
        files: Raw file paths from positional args or ``--files``,
            or *None*.

    Returns:
        Discovered Python file paths.

    Raises:
        typer.Exit: If no Python files are found (exit code 0).
    """
    config: DocvetConfig = ctx.obj["docvet_config"]
    explicit = [Path(f) for f in files] if files else ()
    discovered = discover_files(config, mode, files=explicit)

    if not discovered:
        typer.echo("No Python files to check.", err=True)
        raise typer.Exit(0)

    if ctx.obj.get("verbose") and not ctx.obj.get("quiet"):
        typer.echo(f"Found {len(discovered)} file(s) to check", err=True)

    return discovered


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
        json_output = format_json(
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
        write_report(all_findings, Path(output_path), fmt=resolved_fmt)
    elif all_findings:
        if resolved_fmt == "markdown":
            sys.stdout.write(format_markdown(all_findings))
        else:
            sys.stdout.write(format_terminal(all_findings, no_color=no_color))


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
        sys.stderr.write(format_verbose_header(file_count, checks))

    # 4. Verbose coverage line
    if verbose and not quiet and presence_stats is not None:
        sys.stderr.write(
            _format_coverage_line(presence_stats, config.presence.min_coverage)
        )

    # 5. Compute quality if --summary and counts available
    quality = None
    if summary and check_counts is not None:
        quality = compute_quality(findings_by_check, check_counts)

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
        sys.stderr.write(format_quality_summary(quality))

    raise typer.Exit(
        determine_exit_code(findings_by_check, config, presence_stats=presence_stats)
    )


def _get_git_diff(
    file_path: Path,
    project_root: Path,
    discovery_mode: DiscoveryMode,
) -> str:
    """Get git diff output for a single file.

    Runs the appropriate ``git diff`` variant based on the discovery
    mode and returns the raw unified diff output.

    Args:
        file_path: Absolute path to the file.
        project_root: Project root for git working directory.
        discovery_mode: Controls which git diff variant to run.

    Returns:
        Raw unified diff output string. Returns an empty string if
        the git command exits with a non-zero status.
    """
    if discovery_mode is DiscoveryMode.STAGED:
        args = ["git", "diff", "--cached", "--", str(file_path)]
    elif discovery_mode is DiscoveryMode.ALL:
        args = ["git", "diff", "HEAD", "--", str(file_path)]
    else:
        args = ["git", "diff", "--", str(file_path)]

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def _get_git_blame(file_path: Path, project_root: Path) -> str:
    """Get git blame porcelain output for a single file.

    Runs ``git blame --line-porcelain`` and returns the raw output
    for drift/age analysis.

    Args:
        file_path: Absolute path to the file.
        project_root: Project root for git working directory.

    Returns:
        Raw porcelain blame output string. Returns an empty string
        if the git command exits with a non-zero status.
    """
    result = subprocess.run(
        ["git", "blame", "--line-porcelain", "--", str(file_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


# ---------------------------------------------------------------------------
# Private check runners
# ---------------------------------------------------------------------------


def _write_timing(
    name: str,
    file_count: int,
    elapsed: float,
    *,
    verbose: bool,
    quiet: bool,
    enabled: bool = True,
) -> None:
    """Write a per-check timing line to stderr when verbose.

    Args:
        name: Check name (e.g. ``"enrichment"``).
        file_count: Number of files that were checked.
        elapsed: Elapsed time in seconds.
        verbose: Whether verbose mode is active.
        quiet: Whether quiet mode is active.
        enabled: Extra gate — set to *False* to suppress output
            (used for griffe when not installed).
    """
    if enabled and verbose and not quiet:
        sys.stderr.write(f"{name}: {file_count} files in {elapsed:.1f}s\n")


def _run_enrichment(
    files: list[Path],
    config: DocvetConfig,
    *,
    show_progress: bool = False,
) -> tuple[list[Finding], int]:
    """Run the enrichment check on discovered files.

    Reads each file, parses its AST, and runs all enabled enrichment
    rules. Passes ``config.docstring_style`` to the enrichment checker
    for style-aware section detection and rule gating. Files that fail
    to parse are skipped with a warning.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        show_progress: Display a progress bar on stderr.

    Returns:
        A tuple of ``(findings, symbol_count)`` where *symbol_count*
        is the total documented symbols analyzed across all files.
    """
    all_findings: list[Finding] = []
    symbol_count = 0
    with typer.progressbar(
        files, label="enrichment", file=sys.stderr, hidden=not show_progress
    ) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            symbol_count += len(get_documented_symbols(tree))
            findings = check_enrichment(
                source,
                tree,
                config.enrichment,
                str(file_path),
                style=config.docstring_style,
            )
            all_findings.extend(findings)
    return all_findings, symbol_count


def _run_presence(
    files: list[Path],
    config: DocvetConfig,
    *,
    show_progress: bool = False,
) -> tuple[list[Finding], PresenceStats]:
    """Run the presence check on discovered files.

    Reads each file, parses its AST, and checks for missing docstrings.
    Files that fail to parse are skipped with a warning. Aggregates
    per-file coverage statistics into a single :class:`PresenceStats`.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        show_progress: Display a progress bar on stderr.

    Returns:
        A tuple of ``(findings, stats)`` where *findings* is a list of
        presence findings and *stats* is the aggregate coverage across
        all files.
    """
    all_findings: list[Finding] = []
    total_documented = 0
    total_total = 0
    with typer.progressbar(
        files, label="presence", file=sys.stderr, hidden=not show_progress
    ) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            findings, stats = check_presence(source, str(file_path), config.presence)
            all_findings.extend(findings)
            total_documented += stats.documented
            total_total += stats.total
    return all_findings, PresenceStats(documented=total_documented, total=total_total)


def _run_freshness(
    files: list[Path],
    config: DocvetConfig,
    freshness_mode: FreshnessMode = FreshnessMode.DIFF,
    discovery_mode: DiscoveryMode = DiscoveryMode.DIFF,
    *,
    show_progress: bool = False,
) -> tuple[list[Finding], int]:
    """Run the freshness check on discovered files.

    For diff mode, reads each file, parses the AST, obtains its git
    diff, and calls ``check_freshness_diff``. For drift mode, reads
    each file, parses the AST, runs ``git blame --line-porcelain``,
    and calls ``check_freshness_drift``.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        freshness_mode: The freshness check strategy (diff or drift).
        discovery_mode: Controls which git diff variant to run.
        show_progress: Display a progress bar on stderr.

    Returns:
        A tuple of ``(findings, symbol_count)`` where *symbol_count*
        is the total documented symbols analyzed across all files.
    """
    if freshness_mode is not FreshnessMode.DIFF:
        all_findings: list[Finding] = []
        symbol_count = 0
        with typer.progressbar(
            files, label="freshness", file=sys.stderr, hidden=not show_progress
        ) as progress:
            for file_path in progress:
                source = file_path.read_text(encoding="utf-8")
                try:
                    tree = ast.parse(source, filename=str(file_path))
                except SyntaxError:
                    typer.echo(
                        f"warning: {file_path}: failed to parse, skipping", err=True
                    )
                    continue
                symbol_count += len(get_documented_symbols(tree))
                blame_output = _get_git_blame(file_path, config.project_root)
                findings = check_freshness_drift(
                    str(file_path), blame_output, tree, config.freshness
                )
                all_findings.extend(findings)
        return all_findings, symbol_count

    all_findings: list[Finding] = []
    symbol_count = 0
    with typer.progressbar(
        files, label="freshness", file=sys.stderr, hidden=not show_progress
    ) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            symbol_count += len(get_documented_symbols(tree))
            diff_output = _get_git_diff(file_path, config.project_root, discovery_mode)
            findings = check_freshness_diff(str(file_path), diff_output, tree)
            all_findings.extend(findings)
    return all_findings, symbol_count


def _run_coverage(files: list[Path], config: DocvetConfig) -> tuple[list[Finding], int]:
    """Run the coverage check on discovered files.

    Resolves the source root from configuration and checks all discovered
    files for missing ``__init__.py`` in parent directories.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.

    Returns:
        A tuple of ``(findings, package_count)`` where *package_count*
        is the number of unique package directories scanned.
    """
    src_root = config.project_root / config.src_root
    package_count = len({f.parent for f in files})
    return check_coverage(src_root, files), package_count


def _run_griffe(
    files: list[Path],
    config: DocvetConfig,
    *,
    verbose: bool = False,
    quiet: bool = False,
) -> tuple[list[Finding], int]:
    """Run the griffe compatibility check on discovered files.

    Checks if griffe is installed, resolves the source root from
    configuration, and runs ``check_griffe_compat``.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        verbose: Whether verbose mode is enabled.
        quiet: Whether quiet mode is enabled.

    Returns:
        A tuple of ``(findings, file_count)`` where *file_count*
        is the number of files checked by griffe.
    """
    if importlib.util.find_spec("griffe") is None:
        if "griffe" in config.fail_on:
            typer.echo("warning: griffe check skipped (griffe not installed)", err=True)
        elif verbose and not quiet:
            typer.echo("griffe: skipped (griffe not installed)", err=True)
        return [], 0
    src_root = config.project_root / config.src_root
    if not src_root.is_dir():
        return [], 0
    return check_griffe_compat(src_root, files), len(files)


# ---------------------------------------------------------------------------
# App callback (global options)
# ---------------------------------------------------------------------------


def _version_callback(value: bool | None) -> None:
    """Print version and exit.

    Args:
        value: Whether ``--version`` was passed.

    Raises:
        typer.Exit: After printing the version string.
    """
    if value:
        version = importlib.metadata.version("docvet")
        typer.echo(f"docvet {version}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    summary: Annotated[
        bool,
        typer.Option("--summary", help="Print quality percentages after findings."),
    ] = False,
    fmt: Annotated[
        OutputFormat | None,
        typer.Option("--format", help="Output format."),
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write report to file.")
    ] = None,
    config: ConfigOption = None,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version.",
        ),
    ] = None,
) -> None:
    """Global options for docvet.

    Stores all global options in ``ctx.obj`` so subcommands can access
    them. The ``config`` path is stored as ``config_path`` for use by
    subcommands that need the raw pyproject.toml location.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output.
        quiet: Suppress non-finding output on stderr.
        summary: Print quality percentages after findings.
        fmt: Output format (terminal, markdown, or json).
        output: Optional file path for report output.
        config: Explicit path to a ``pyproject.toml``.
        version: Show version and exit.

    Raises:
        typer.BadParameter: If the specified config file does not exist.
    """
    ctx.ensure_object(dict)
    if ctx.resilient_parsing:
        return

    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["summary"] = summary
    ctx.obj["format"] = fmt.value if fmt is not None else None
    ctx.obj["output"] = str(output) if output is not None else None
    ctx.obj["config_path"] = config

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        return

    try:
        ctx.obj["docvet_config"] = load_config(config)
    except FileNotFoundError:
        raise typer.BadParameter(f"Config file not found: {config}") from None


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


@app.command()
def check(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Run all enabled checks.

    Runs presence (if enabled), enrichment, freshness, coverage, and
    griffe (if installed and compatible) checks in sequence. Each check
    runner returns a ``(findings, item_count)`` tuple; item counts are
    collected into ``check_counts`` for per-check quality percentage
    computation when ``--summary`` is active. Griffe is auto-skipped
    when ``docstring-style`` is ``"sphinx"`` (incompatible parser). Griffe
    is only included in ``check_counts`` when the ``griffe`` package is
    importable and the style is compatible. Coverage percentage is derived
    from :attr:`PresenceStats.percentage`. Displays a progress bar on
    stderr when connected to a TTY. Uses three-tier verbosity:
    ``--quiet`` suppresses all non-finding stderr output, default shows
    the summary line with coverage percentage, ``--verbose`` adds
    per-check timing, file discovery count, and detailed coverage status.

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    show_progress = sys.stderr.isatty()
    file_count = len(discovered)

    total_start = time.perf_counter()

    # Presence (runs first — skip if disabled)
    presence_findings: list[Finding] = []
    agg_stats: PresenceStats | None = None
    if config.presence.enabled:
        start = time.perf_counter()
        presence_findings, agg_stats = _run_presence(
            discovered, config, show_progress=show_progress
        )
        elapsed = time.perf_counter() - start
        _write_timing("presence", file_count, elapsed, verbose=verbose, quiet=quiet)

    start = time.perf_counter()
    enrichment_findings, enrichment_count = _run_enrichment(
        discovered, config, show_progress=show_progress
    )
    elapsed = time.perf_counter() - start
    _write_timing("enrichment", file_count, elapsed, verbose=verbose, quiet=quiet)

    start = time.perf_counter()
    freshness_findings, freshness_count = _run_freshness(
        discovered, config, discovery_mode=discovery_mode, show_progress=show_progress
    )
    elapsed = time.perf_counter() - start
    _write_timing("freshness", file_count, elapsed, verbose=verbose, quiet=quiet)

    start = time.perf_counter()
    coverage_findings, coverage_count = _run_coverage(discovered, config)
    elapsed = time.perf_counter() - start
    _write_timing("coverage", file_count, elapsed, verbose=verbose, quiet=quiet)

    griffe_installed = importlib.util.find_spec("griffe") is not None
    griffe_skipped_style = config.docstring_style == "sphinx"
    if griffe_skipped_style:
        griffe_findings: list[Finding] = []
        griffe_count = 0
        if verbose:
            sys.stderr.write(
                "  griffe: skipped (incompatible with sphinx docstring style)\n"
            )
    else:
        start = time.perf_counter()
        griffe_findings, griffe_count = _run_griffe(
            discovered, config, verbose=verbose, quiet=quiet
        )
        elapsed = time.perf_counter() - start
        _write_timing(
            "griffe",
            file_count,
            elapsed,
            verbose=verbose,
            quiet=quiet,
            enabled=griffe_installed,
        )

    total_elapsed = time.perf_counter() - total_start

    checks: list[str] = []
    if config.presence.enabled:
        checks.append("presence")
    checks.extend(["enrichment", "freshness", "coverage"])
    if griffe_installed and not griffe_skipped_style:
        checks.append("griffe")

    coverage_pct: float | None = None
    if agg_stats is not None:
        coverage_pct = agg_stats.percentage

    all_findings_flat = (
        presence_findings
        + enrichment_findings
        + freshness_findings
        + coverage_findings
        + griffe_findings
    )
    if not quiet:
        sys.stderr.write(
            format_summary(
                file_count,
                checks,
                all_findings_flat,
                total_elapsed,
                coverage_pct=coverage_pct,
            )
        )

    findings_by_check = {
        "presence": presence_findings,
        "enrichment": enrichment_findings,
        "freshness": freshness_findings,
        "coverage": coverage_findings,
        "griffe": griffe_findings,
    }
    check_counts: dict[str, int] = {
        "enrichment": enrichment_count,
        "freshness": freshness_count,
        "coverage": coverage_count,
    }
    if griffe_installed:
        check_counts["griffe"] = griffe_count
    _output_and_exit(
        ctx,
        findings_by_check,
        config,
        file_count,
        checks,
        presence_stats=agg_stats,
        check_counts=check_counts,
    )


@app.command()
def presence(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check for missing docstrings.

    Coverage percentage is derived from :attr:`PresenceStats.percentage`.
    Displays a progress bar on stderr when connected to a TTY.
    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count.

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings, agg_stats = _run_presence(
        discovered, config, show_progress=sys.stderr.isatty()
    )
    elapsed = time.perf_counter() - start
    coverage_pct = agg_stats.percentage
    if not quiet:
        sys.stderr.write(
            format_summary(
                len(discovered),
                ["presence"],
                findings,
                elapsed,
                coverage_pct=coverage_pct,
            )
        )

    _output_and_exit(
        ctx,
        {"presence": findings},
        config,
        len(discovered),
        ["presence"],
        presence_stats=agg_stats,
    )


@app.command()
def enrichment(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check for missing docstring sections.

    Displays a progress bar on stderr when connected to a TTY.
    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count. Passes symbol count to ``_output_and_exit``
    for ``--summary`` quality percentage computation.

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings, symbol_count = _run_enrichment(
        discovered, config, show_progress=sys.stderr.isatty()
    )
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["enrichment"], findings, elapsed)
        )

    _output_and_exit(
        ctx,
        {"enrichment": findings},
        config,
        len(discovered),
        ["enrichment"],
        check_counts={"enrichment": symbol_count},
    )


@app.command()
def freshness(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
    mode: Annotated[
        FreshnessMode, typer.Option("--mode", help="Freshness check strategy.")
    ] = FreshnessMode.DIFF,
) -> None:
    """Detect stale docstrings.

    Displays a progress bar on stderr when connected to a TTY.
    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count. Passes symbol count to ``_output_and_exit``
    for ``--summary`` quality percentage computation.

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.
        mode: Freshness strategy (diff or drift).
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings, symbol_count = _run_freshness(
        discovered,
        config,
        freshness_mode=mode,
        discovery_mode=discovery_mode,
        show_progress=sys.stderr.isatty(),
    )
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["freshness"], findings, elapsed)
        )

    _output_and_exit(
        ctx,
        {"freshness": findings},
        config,
        len(discovered),
        ["freshness"],
        check_counts={"freshness": symbol_count},
    )


@app.command()
def coverage(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Find files invisible to mkdocs.

    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count. Passes package directory count to
    ``_output_and_exit`` for ``--summary`` quality percentage computation.

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings, package_count = _run_coverage(discovered, config)
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["coverage"], findings, elapsed)
        )

    _output_and_exit(
        ctx,
        {"coverage": findings},
        config,
        len(discovered),
        ["coverage"],
        check_counts={"coverage": package_count},
    )


@app.command()
def griffe(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check mkdocs rendering compatibility via griffe.

    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count. Passes file count to ``_output_and_exit``
    for ``--summary`` quality percentage computation. Auto-skips with
    exit code 0 when ``docstring-style`` is ``"sphinx"`` (griffe's
    Google parser is incompatible with RST docstrings).

    Args:
        ctx: Typer invocation context.
        files_pos: Positional file paths to check.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files via ``--files``.

    Raises:
        typer.Exit: When ``docstring-style`` is ``"sphinx"`` (exit 0).
    """
    files = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    if config.docstring_style == "sphinx":
        typer.echo(
            "Griffe check skipped: incompatible with sphinx docstring style",
            err=True,
        )
        raise typer.Exit(0)

    start = time.perf_counter()
    findings, griffe_file_count = _run_griffe(
        discovered, config, verbose=verbose, quiet=quiet
    )
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(format_summary(len(discovered), ["griffe"], findings, elapsed))

    _output_and_exit(
        ctx,
        {"griffe": findings},
        config,
        len(discovered),
        ["griffe"],
        check_counts={"griffe": griffe_file_count},
    )


@app.command()
def lsp() -> None:
    """Start the LSP server for real-time diagnostics.

    Launches a Language Server Protocol server on stdio that publishes
    docstring quality diagnostics on file open and save events.
    Requires the ``[lsp]`` extra (``pip install docvet[lsp]``).

    Raises:
        typer.Exit: If required LSP dependencies are not installed.
    """
    try:
        from docvet.lsp import start_server
    except ModuleNotFoundError:
        typer.echo(
            "LSP server requires pygls. Install with: pip install docvet[lsp]",
            err=True,
        )
        raise typer.Exit(code=1)
    start_server()


@app.command()
def mcp() -> None:
    """Start the MCP server for agentic integration.

    Launches a Model Context Protocol server on stdio that exposes
    docstring quality checks as MCP tools for AI agents.
    Requires the ``[mcp]`` extra (``pip install docvet[mcp]``).
    Catches both ``ModuleNotFoundError`` and ``ImportError`` to
    handle re-raised import failures gracefully.

    Raises:
        typer.Exit: If required MCP dependencies are not installed.
    """
    try:
        from docvet.mcp import start_server as mcp_start_server
    except ImportError:
        typer.echo(
            "MCP server requires the mcp extra: pip install docvet[mcp]",
            err=True,
        )
        raise typer.Exit(code=1)
    mcp_start_server()


@app.command()
def config(
    ctx: typer.Context,
    show_defaults: Annotated[
        bool,
        typer.Option(
            "--show-defaults",
            help="Show effective config (accepted for backward compat).",
        ),
    ] = False,
) -> None:
    """Show effective configuration with source annotations.

    Prints the merged config (user values + defaults) in TOML or JSON
    format. Each value is annotated with ``# (user)`` or
    ``# (default)`` to show its source. Respects the global
    ``--config`` flag via ``ctx.obj["config_path"]``.

    Args:
        ctx: Typer invocation context.
        show_defaults: No-op flag accepted for backward compatibility.
    """
    user_keys, pyproject_path = get_user_keys(ctx.obj.get("config_path"))
    if pyproject_path is None:
        typer.echo(
            "docvet: no pyproject.toml found — showing built-in defaults",
            err=True,
        )
    docvet_config: DocvetConfig = ctx.obj["docvet_config"]
    fmt = ctx.obj.get("format")
    if fmt == "json":
        typer.echo(format_config_json(docvet_config, user_keys))
    else:
        typer.echo(format_config_toml(docvet_config, user_keys))
