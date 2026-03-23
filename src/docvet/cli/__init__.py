"""Typer CLI application for docvet.

Defines the ``typer.Typer`` app with subcommands for each check layer
(``presence``, ``enrichment``, ``freshness``, ``coverage``, ``griffe``,
``lsp``, ``mcp``), the combined ``check`` entry point, and the
``config`` introspection command.  Check runners are in ``_runners``
and the output pipeline is in ``_output``.  This module retains enums,
discovery helpers, the app callback, and all typer subcommands.

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

Attributes:
    app: The ``typer.Typer`` application instance.

See Also:
    [`docvet.checks`][]: Public API re-exports for check functions.
    [`docvet.config`][]: Configuration dataclasses loaded by the CLI.
    [`docvet.discovery`][]: File discovery invoked by each subcommand.
"""

from __future__ import annotations

import ast  # noqa: F401 – re-exported for test mocks
import enum
import importlib.metadata
import importlib.util
import os  # noqa: F401 – re-exported for test mocks
import subprocess  # noqa: F401 – re-exported for test mocks
import sys
import time
from pathlib import Path
from typing import Annotated

import typer

from docvet.ast_utils import (
    get_documented_symbols,  # noqa: F401 – re-exported for test mocks
)
from docvet.checks import Finding
from docvet.checks.coverage import (
    check_coverage,  # noqa: F401 – re-exported for test mocks
)
from docvet.checks.enrichment import (
    check_enrichment,  # noqa: F401 – re-exported for test mocks
)
from docvet.checks.freshness import (  # noqa: F401
    check_freshness_diff,
    check_freshness_drift,
)
from docvet.checks.griffe_compat import (
    check_griffe_compat,  # noqa: F401 – re-exported for test mocks
)
from docvet.checks.presence import PresenceStats, check_presence  # noqa: F401
from docvet.config import (
    DocvetConfig,
    format_config_json,
    format_config_toml,
    get_user_keys,
    load_config,
)
from docvet.discovery import DiscoveryMode, discover_files
from docvet.reporting import (
    CheckQuality,  # noqa: F401 – re-exported for test mocks
    compute_quality,  # noqa: F401 – re-exported for test mocks
    determine_exit_code,  # noqa: F401 – re-exported for test mocks
    format_json,  # noqa: F401 – re-exported for test mocks
    format_markdown,  # noqa: F401 – re-exported for test mocks
    format_quality_summary,  # noqa: F401 – re-exported for test mocks
    format_summary,
    format_terminal,  # noqa: F401 – re-exported for test mocks
    format_verbose_header,  # noqa: F401 – re-exported for test mocks
    write_report,  # noqa: F401 – re-exported for test mocks
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


from ._output import (  # noqa: E402
    _format_coverage_line,  # noqa: F401 – re-exported for tests
    _output_and_exit,
    _resolve_format,  # noqa: F401 – re-exported for tests
)
from ._runners import (  # noqa: E402
    _get_git_blame,  # noqa: F401 – re-exported for tests
    _get_git_diff,  # noqa: F401 – re-exported for tests
    _run_coverage,
    _run_enrichment,
    _run_freshness,
    _run_griffe,
    _run_presence,
    _write_timing,
)

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
    importable and the docstring style is compatible. Coverage percentage is derived
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
    if griffe_installed and not griffe_skipped_style:
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
