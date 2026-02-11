"""Typer CLI application for docvet."""

from __future__ import annotations

import ast
import enum
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
from docvet.config import DocvetConfig, load_config
from docvet.discovery import DiscoveryMode, discover_files

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OutputFormat(enum.StrEnum):
    """Output format for reports."""

    TERMINAL = "terminal"
    MARKDOWN = "markdown"


class FreshnessMode(enum.StrEnum):
    """Freshness check strategy."""

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


def _print_global_context(ctx: typer.Context) -> None:
    """Print acknowledged global options when set.

    Args:
        ctx: Typer context carrying global options in ``ctx.obj``.
    """
    if ctx.obj.get("verbose"):
        typer.echo("verbose: enabled", err=True)
    fmt = ctx.obj.get("format")
    if fmt is not None:
        typer.echo(f"format: {fmt}", err=True)
    output = ctx.obj.get("output")
    if output is not None:
        typer.echo(f"output: {output}", err=True)


def _discover_and_handle(
    ctx: typer.Context,
    mode: DiscoveryMode,
    files: list[str] | None,
) -> list[Path]:
    """Discover files and handle empty results.

    Pulls config from ``ctx.obj["docvet_config"]``, converts the raw
    ``--files`` strings to :class:`~pathlib.Path` objects, calls
    :func:`discover_files`, and handles the empty-list case with a
    user-friendly message.

    Args:
        ctx: Typer context carrying ``docvet_config`` and ``verbose``.
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

    if ctx.obj.get("verbose"):
        typer.echo(f"Found {len(discovered)} file(s) to check", err=True)

    return discovered


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


def _run_enrichment(files: list[Path], config: DocvetConfig) -> None:
    """Run the enrichment check on discovered files.

    Reads each file, parses its AST, and runs all enabled enrichment
    rules. Findings are printed to stdout in ``file:line: rule message``
    format. Files that fail to parse are skipped with a warning.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
    """
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
            continue
        findings = check_enrichment(source, tree, config.enrichment, str(file_path))
        for finding in findings:
            typer.echo(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
            )


def _run_freshness(
    files: list[Path],
    config: DocvetConfig,
    freshness_mode: FreshnessMode = FreshnessMode.DIFF,
    discovery_mode: DiscoveryMode = DiscoveryMode.DIFF,
) -> None:
    """Run the freshness check on discovered files.

    For diff mode, reads each file, parses the AST, obtains its git
    diff, and calls ``check_freshness_diff``. For drift mode, reads
    each file, parses the AST, runs ``git blame --line-porcelain``,
    and calls ``check_freshness_drift``. Findings are printed to
    stdout in ``file:line: rule message`` format.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        freshness_mode: The freshness check strategy (diff or drift).
        discovery_mode: Controls which git diff variant to run.
    """
    if freshness_mode is not FreshnessMode.DIFF:
        for file_path in files:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            blame_output = _get_git_blame(file_path, config.project_root)
            findings = check_freshness_drift(
                str(file_path), blame_output, tree, config.freshness
            )
            for finding in findings:
                typer.echo(
                    f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
                )
        return

    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
            continue
        diff_output = _get_git_diff(file_path, config.project_root, discovery_mode)
        findings = check_freshness_diff(str(file_path), diff_output, tree)
        for finding in findings:
            typer.echo(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
            )


def _run_coverage(files: list[Path], config: DocvetConfig) -> None:
    """Run the coverage check on discovered files.

    Resolves the source root from configuration and checks all discovered
    files for missing ``__init__.py`` in parent directories.  Findings are
    printed to stdout in ``file:line: rule message`` format.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
    """
    src_root = config.project_root / config.src_root
    findings = check_coverage(src_root, files)
    for finding in findings:
        typer.echo(f"{finding.file}:{finding.line}: {finding.rule} {finding.message}")


def _run_griffe(files: list[Path], config: DocvetConfig) -> None:
    """Stub for griffe compatibility check.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
    """
    typer.echo("griffe: not yet implemented")


# ---------------------------------------------------------------------------
# App callback (global options)
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    fmt: Annotated[
        OutputFormat | None,
        typer.Option("--format", help="Output format."),
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Write report to file.")
    ] = None,
    config: ConfigOption = None,
) -> None:
    """Global options for docvet.

    Args:
        ctx: Typer invocation context.
        verbose: Enable verbose output.
        fmt: Output format (terminal or markdown).
        output: Optional file path for report output.
        config: Explicit path to a ``pyproject.toml``.
    """
    ctx.ensure_object(dict)
    if ctx.resilient_parsing:
        return

    ctx.obj["verbose"] = verbose
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
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Run all enabled checks.

    Args:
        ctx: Typer invocation context.
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    _print_global_context(ctx)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    _run_enrichment(discovered, config)
    _run_freshness(discovered, config, discovery_mode=discovery_mode)
    _run_coverage(discovered, config)
    _run_griffe(discovered, config)


@app.command()
def enrichment(
    ctx: typer.Context,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check for missing docstring sections.

    Args:
        ctx: Typer invocation context.
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    _print_global_context(ctx)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    _run_enrichment(discovered, config)


@app.command()
def freshness(
    ctx: typer.Context,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
    mode: Annotated[
        FreshnessMode, typer.Option("--mode", help="Freshness check strategy.")
    ] = FreshnessMode.DIFF,
) -> None:
    """Detect stale docstrings.

    Args:
        ctx: Typer invocation context.
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
        mode: Freshness strategy (diff or drift).
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    _print_global_context(ctx)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    _run_freshness(
        discovered, config, freshness_mode=mode, discovery_mode=discovery_mode
    )


@app.command()
def coverage(
    ctx: typer.Context,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Find files invisible to mkdocs.

    Args:
        ctx: Typer invocation context.
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    _print_global_context(ctx)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    _run_coverage(discovered, config)


@app.command()
def griffe(
    ctx: typer.Context,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check mkdocs rendering compatibility.

    Args:
        ctx: Typer invocation context.
        staged: Run on staged files.
        all_files: Run on entire codebase.
        files: Run on specific files.
    """
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    _print_global_context(ctx)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    _run_griffe(discovered, config)
