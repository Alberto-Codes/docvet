"""Typer CLI application for docvet."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Annotated

import typer

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DiscoveryMode(enum.Enum):
    """Internal discovery mode for file selection."""

    DIFF = enum.auto()
    STAGED = enum.auto()
    ALL = enum.auto()
    FILES = enum.auto()


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
        typer.echo("verbose: enabled")
    fmt = ctx.obj.get("format")
    if fmt is not None:
        typer.echo(f"format: {fmt}")
    output = ctx.obj.get("output")
    if output is not None:
        typer.echo(f"output: {output}")


# ---------------------------------------------------------------------------
# Private stub runners
# ---------------------------------------------------------------------------


def _run_enrichment(mode: DiscoveryMode) -> None:
    """Stub for enrichment check.

    Args:
        mode: The resolved discovery mode.
    """
    typer.echo("enrichment: not yet implemented")


def _run_freshness(
    mode: DiscoveryMode,
    freshness_mode: FreshnessMode = FreshnessMode.DIFF,
) -> None:
    """Stub for freshness check.

    Args:
        mode: The resolved discovery mode.
        freshness_mode: The freshness check strategy (diff or drift).
    """
    typer.echo("freshness: not yet implemented")


def _run_coverage(mode: DiscoveryMode) -> None:
    """Stub for coverage check.

    Args:
        mode: The resolved discovery mode.
    """
    typer.echo("coverage: not yet implemented")


def _run_griffe(mode: DiscoveryMode) -> None:
    """Stub for griffe compatibility check.

    Args:
        mode: The resolved discovery mode.
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
    ctx.obj["verbose"] = verbose
    ctx.obj["format"] = fmt.value if fmt is not None else None
    ctx.obj["output"] = str(output) if output is not None else None
    ctx.obj["config"] = str(config) if config is not None else None

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


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
    _run_enrichment(discovery_mode)
    _run_freshness(discovery_mode)
    _run_coverage(discovery_mode)
    _run_griffe(discovery_mode)


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
    _run_enrichment(discovery_mode)


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
    _run_freshness(discovery_mode, freshness_mode=mode)


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
    _run_coverage(discovery_mode)


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
    _run_griffe(discovery_mode)
