"""Typer CLI application for docvet.

Defines the ``typer.Typer`` app with subcommands for each check layer
(``enrichment``, ``freshness``, ``coverage``, ``griffe``) and the
combined ``check`` entry point. All subcommands share three-tier
verbosity control (quiet/default/verbose) via dual-registered
``--verbose`` and ``-q``/``--quiet`` flags and emit a unified
``Vetted N files [check] — ...`` summary line on stderr.

Examples:
    Run all checks on changed files::

        $ docvet check

    Run the enrichment check on the entire codebase::

        $ docvet enrichment --all

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

from docvet.checks import Finding
from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
from docvet.checks.griffe_compat import check_griffe_compat
from docvet.config import DocvetConfig, load_config
from docvet.discovery import DiscoveryMode, discover_files
from docvet.reporting import (
    determine_exit_code,
    format_markdown,
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
    """

    TERMINAL = "terminal"
    MARKDOWN = "markdown"


class FreshnessMode(enum.StrEnum):
    """Freshness check strategy.

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
    list[str] | None, typer.Option("--files", help="Run on specific files.")
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


def _resolve_discovery_mode(
    staged: bool,
    all_files: bool,
    files: list[str] | None,
) -> DiscoveryMode:
    """Validate mutual exclusivity and return the selected discovery mode.

    Args:
        staged: Whether ``--staged`` was passed.
        all_files: Whether ``--all`` was passed.
        files: Explicit file list from ``--files``, or *None*.

    Returns:
        The resolved :class:`DiscoveryMode`.

    Raises:
        typer.BadParameter: If more than one discovery flag is set.
    """
    flags_set = sum((staged, all_files, files is not None))
    if flags_set > 1:
        raise typer.BadParameter(
            "Options --staged, --all, and --files are mutually exclusive."
        )
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
        files: Raw file paths from ``--files``, or *None*.

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


def _output_and_exit(
    ctx: typer.Context,
    findings_by_check: dict[str, list[Finding]],
    config: DocvetConfig,
    file_count: int,
    checks: list[str],
) -> None:
    """Format findings, optionally write to file, and exit with proper code.

    Implements the unified output pipeline: resolves no_color, optionally
    prints verbose header to stderr (only for multi-check runs), selects
    format, writes file or prints findings to stdout, and raises
    ``typer.Exit`` with the appropriate exit code.

    Args:
        ctx: Typer context carrying global options in ``ctx.obj``.
        findings_by_check: Findings grouped by check name.
        config: Loaded docvet configuration.
        file_count: Number of files that were checked.
        checks: List of check names that were run.

    Raises:
        typer.Exit: With code 0 when no fail-on findings, code 1 otherwise.
    """
    output_path = ctx.obj.get("output")
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)
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

    # 4. Resolve format and produce formatted string
    if fmt_opt is not None:
        resolved_fmt = fmt_opt
    elif output_path is not None:
        resolved_fmt = "markdown"
    else:
        resolved_fmt = "terminal"

    # 5-6. Output findings
    if output_path and all_findings:
        write_report(all_findings, Path(output_path), fmt=resolved_fmt)
    elif all_findings:
        if resolved_fmt == "markdown":
            sys.stdout.write(format_markdown(all_findings))
        else:
            sys.stdout.write(format_terminal(all_findings, no_color=no_color))

    # 7. Exit
    raise typer.Exit(determine_exit_code(findings_by_check, config))


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


def _run_enrichment(
    files: list[Path],
    config: DocvetConfig,
    *,
    show_progress: bool = False,
) -> list[Finding]:
    """Run the enrichment check on discovered files.

    Reads each file, parses its AST, and runs all enabled enrichment
    rules. Files that fail to parse are skipped with a warning.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        show_progress: Display a progress bar on stderr.

    Returns:
        All enrichment findings across all files.
    """
    all_findings: list[Finding] = []
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
            findings = check_enrichment(source, tree, config.enrichment, str(file_path))
            all_findings.extend(findings)
    return all_findings


def _run_freshness(
    files: list[Path],
    config: DocvetConfig,
    freshness_mode: FreshnessMode = FreshnessMode.DIFF,
    discovery_mode: DiscoveryMode = DiscoveryMode.DIFF,
    *,
    show_progress: bool = False,
) -> list[Finding]:
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
        All freshness findings across all files.
    """
    if freshness_mode is not FreshnessMode.DIFF:
        all_findings: list[Finding] = []
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
                blame_output = _get_git_blame(file_path, config.project_root)
                findings = check_freshness_drift(
                    str(file_path), blame_output, tree, config.freshness
                )
                all_findings.extend(findings)
        return all_findings

    all_findings: list[Finding] = []
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
            diff_output = _get_git_diff(file_path, config.project_root, discovery_mode)
            findings = check_freshness_diff(str(file_path), diff_output, tree)
            all_findings.extend(findings)
    return all_findings


def _run_coverage(files: list[Path], config: DocvetConfig) -> list[Finding]:
    """Run the coverage check on discovered files.

    Resolves the source root from configuration and checks all discovered
    files for missing ``__init__.py`` in parent directories.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.

    Returns:
        All coverage findings.
    """
    src_root = config.project_root / config.src_root
    return check_coverage(src_root, files)


def _run_griffe(
    files: list[Path],
    config: DocvetConfig,
    *,
    verbose: bool = False,
    quiet: bool = False,
) -> list[Finding]:
    """Run the griffe compatibility check on discovered files.

    Checks if griffe is installed, resolves the source root from
    configuration, and runs ``check_griffe_compat``.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        verbose: Whether verbose mode is enabled.
        quiet: Whether quiet mode is enabled.

    Returns:
        All griffe compatibility findings.
    """
    if importlib.util.find_spec("griffe") is None:
        if "griffe" in config.fail_on:
            typer.echo("warning: griffe check skipped (griffe not installed)", err=True)
        elif verbose and not quiet:
            typer.echo("griffe: skipped (griffe not installed)", err=True)
        return []
    src_root = config.project_root / config.src_root
    if not src_root.is_dir():
        return []
    return check_griffe_compat(src_root, files)


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

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output.
        quiet: Suppress non-finding output on stderr.
        fmt: Output format (terminal or markdown).
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
    ctx.obj["format"] = fmt.value if fmt is not None else None
    ctx.obj["output"] = str(output) if output is not None else None

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

    Displays a progress bar on stderr when connected to a TTY.
    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    per-check timing and file discovery count.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
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

    start = time.perf_counter()
    enrichment_findings = _run_enrichment(
        discovered, config, show_progress=show_progress
    )
    elapsed = time.perf_counter() - start
    if verbose and not quiet:
        sys.stderr.write(f"enrichment: {file_count} files in {elapsed:.1f}s\n")

    start = time.perf_counter()
    freshness_findings = _run_freshness(
        discovered, config, discovery_mode=discovery_mode, show_progress=show_progress
    )
    elapsed = time.perf_counter() - start
    if verbose and not quiet:
        sys.stderr.write(f"freshness: {file_count} files in {elapsed:.1f}s\n")

    start = time.perf_counter()
    coverage_findings = _run_coverage(discovered, config)
    elapsed = time.perf_counter() - start
    if verbose and not quiet:
        sys.stderr.write(f"coverage: {file_count} files in {elapsed:.1f}s\n")

    griffe_installed = importlib.util.find_spec("griffe") is not None
    start = time.perf_counter()
    griffe_findings = _run_griffe(discovered, config, verbose=verbose, quiet=quiet)
    elapsed = time.perf_counter() - start
    if verbose and not quiet and griffe_installed:
        sys.stderr.write(f"griffe: {file_count} files in {elapsed:.1f}s\n")

    total_elapsed = time.perf_counter() - total_start

    checks = ["enrichment", "freshness", "coverage"]
    if griffe_installed:
        checks.append("griffe")

    all_findings_flat = (
        enrichment_findings + freshness_findings + coverage_findings + griffe_findings
    )
    if not quiet:
        sys.stderr.write(
            format_summary(file_count, checks, all_findings_flat, total_elapsed)
        )

    findings_by_check = {
        "enrichment": enrichment_findings,
        "freshness": freshness_findings,
        "coverage": coverage_findings,
        "griffe": griffe_findings,
    }
    _output_and_exit(
        ctx,
        findings_by_check,
        config,
        file_count,
        checks,
    )


@app.command()
def enrichment(
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
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check for missing docstring sections.

    Displays a progress bar on stderr when connected to a TTY.
    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_enrichment(discovered, config, show_progress=sys.stderr.isatty())
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["enrichment"], findings, elapsed)
        )

    _output_and_exit(
        ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"]
    )


@app.command()
def freshness(
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
    file discovery count.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
        mode: Freshness strategy (diff or drift).
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_freshness(
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
        ctx, {"freshness": findings}, config, len(discovered), ["freshness"]
    )


@app.command()
def coverage(
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
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Find files invisible to mkdocs.

    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_coverage(discovered, config)
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["coverage"], findings, elapsed)
        )

    _output_and_exit(ctx, {"coverage": findings}, config, len(discovered), ["coverage"])


@app.command()
def griffe(
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
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check mkdocs rendering compatibility.

    Uses three-tier verbosity: ``--quiet`` suppresses all non-finding
    stderr output, default shows the summary line, ``--verbose`` adds
    file discovery count.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output (subcommand-level).
        quiet: Suppress non-finding output on stderr (subcommand-level).
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_griffe(discovered, config, verbose=verbose, quiet=quiet)
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(format_summary(len(discovered), ["griffe"], findings, elapsed))

    _output_and_exit(ctx, {"griffe": findings}, config, len(discovered), ["griffe"])
