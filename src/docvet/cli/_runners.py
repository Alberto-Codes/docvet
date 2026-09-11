"""CLI check runners, fix runner, and git helpers.

Each ``_run_*`` function reads files, invokes the corresponding check
module, and returns findings.  The ``_run_fix`` runner additionally
writes scaffolded sections back to files (or collects diffs in dry-run
mode).  ``_griffe_unavailability`` is the single source of truth for
whether the griffe check can execute at all, and
``_write_unavailable_notice`` reports a check that could not run.
Git helpers (``_get_git_diff``, ``_get_git_blame``) provide
raw VCS data for the freshness runner, each running git through
:func:`docvet.discovery.git_env` so an inherited ``GIT_DIR`` cannot
redirect it away from the project root.  Progress display is handled
by ``_maybe_progressbar``, which avoids the ``click >= 8.2``
``hidden`` kwarg requirement.

See Also:
    [`docvet.cli`][]: CLI application and subcommands.
    [`docvet.checks`][]: Check modules invoked by runners.

Examples:
    Run the enrichment check on a file list:

    ```python
    findings, count = _run_enrichment(files, config)
    ```
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import typer

import docvet.cli as _cli_pkg
from docvet.checks import Finding
from docvet.checks.presence import PresenceStats
from docvet.config import DocvetConfig
from docvet.reporting import UnavailableCheck

from ..discovery import git_env
from . import DiscoveryMode, FreshnessMode


@contextmanager
def _maybe_progressbar[V](
    items: Sequence[V],
    *,
    label: str,
    show: bool,
) -> Iterator[Iterator[V]]:
    """Wrap items in a typer progress bar, or iterate directly.

    Avoids passing ``hidden`` to ``typer.progressbar`` which relies
    on a ``click >= 8.2`` parameter not available in all environments.

    Args:
        items: Items to iterate over.
        label: Progress bar label.
        show: When ``True``, display a progress bar on stderr.

    Yields:
        An iterator over *items*.
    """
    if show:
        with typer.progressbar(items, label=label, file=sys.stderr) as progress:
            yield progress
    else:
        yield iter(items)


def _get_git_diff(
    file_path: Path,
    project_root: Path,
    discovery_mode: DiscoveryMode,
) -> str:
    """Get git diff output for a single file.

    Runs the appropriate ``git diff`` variant based on the discovery
    mode and returns the raw unified diff output. Git runs with the
    environment from :func:`docvet.discovery.git_env`, so it resolves
    the repository from *project_root* even when the caller inherited
    a ``GIT_DIR`` from a git hook.

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

    result = _cli_pkg.subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
        env=git_env(),
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def _get_git_blame(file_path: Path, project_root: Path) -> str:
    """Get git blame porcelain output for a single file.

    Runs ``git blame --line-porcelain`` and returns the raw output
    for drift/age analysis. Git runs with the environment from
    :func:`docvet.discovery.git_env` so an inherited ``GIT_DIR`` cannot
    point it at a different repository than *project_root*.

    Args:
        file_path: Absolute path to the file.
        project_root: Project root for git working directory.

    Returns:
        Raw porcelain blame output string. Returns an empty string
        if the git command exits with a non-zero status.
    """
    result = _cli_pkg.subprocess.run(
        ["git", "blame", "--line-porcelain", "--", str(file_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
        env=git_env(),
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
) -> None:
    """Write a per-check timing line to stderr when verbose.

    Only called for checks that actually ran; a check that could not
    execute is reported by :func:`_write_unavailable_notice` instead.

    Args:
        name: Check name (e.g. ``"enrichment"``).
        file_count: Number of files that were checked.
        elapsed: Elapsed time in seconds.
        verbose: Whether verbose mode is active.
        quiet: Whether quiet mode is active.
    """
    if verbose and not quiet:
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
    to parse are skipped with a warning. Uses ``_maybe_progressbar``
    for click-compatible progress display.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        show_progress: Display a progress bar on stderr via
            ``_maybe_progressbar``.

    Returns:
        A tuple of ``(findings, symbol_count)`` where *symbol_count*
        is the total documented symbols analyzed across all files.
    """
    all_findings: list[Finding] = []
    symbol_count = 0
    with _maybe_progressbar(files, label="enrichment", show=show_progress) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = _cli_pkg.ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            symbol_count += len(_cli_pkg.get_documented_symbols(tree))
            findings = _cli_pkg.check_enrichment(
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
    Uses ``_maybe_progressbar`` for click-compatible progress display.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        show_progress: Display a progress bar on stderr via
            ``_maybe_progressbar``.

    Returns:
        A tuple of ``(findings, stats)`` where *findings* is a list of
        presence findings and *stats* is the aggregate coverage across
        all files.
    """
    all_findings: list[Finding] = []
    total_documented = 0
    total_total = 0
    with _maybe_progressbar(files, label="presence", show=show_progress) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                _cli_pkg.ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            findings, stats = _cli_pkg.check_presence(
                source, str(file_path), config.presence
            )
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
    and calls ``check_freshness_drift``. Uses ``_maybe_progressbar``
    for click-compatible progress display.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        freshness_mode: The freshness check strategy (diff or drift).
        discovery_mode: Controls which git diff variant to run.
        show_progress: Display a progress bar on stderr via
            ``_maybe_progressbar``.

    Returns:
        A tuple of ``(findings, symbol_count)`` where *symbol_count*
        is the total documented symbols analyzed across all files.
    """
    if freshness_mode is not FreshnessMode.DIFF:
        all_findings: list[Finding] = []
        symbol_count = 0
        with _maybe_progressbar(
            files, label="freshness", show=show_progress
        ) as progress:
            for file_path in progress:
                source = file_path.read_text(encoding="utf-8")
                try:
                    tree = _cli_pkg.ast.parse(source, filename=str(file_path))
                except SyntaxError:
                    typer.echo(
                        f"warning: {file_path}: failed to parse, skipping", err=True
                    )
                    continue
                symbol_count += len(_cli_pkg.get_documented_symbols(tree))
                blame_output = _cli_pkg._get_git_blame(file_path, config.project_root)
                findings = _cli_pkg.check_freshness_drift(
                    str(file_path), blame_output, tree, config.freshness
                )
                all_findings.extend(findings)
        return all_findings, symbol_count

    all_findings: list[Finding] = []
    symbol_count = 0
    with _maybe_progressbar(files, label="freshness", show=show_progress) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = _cli_pkg.ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            symbol_count += len(_cli_pkg.get_documented_symbols(tree))
            diff_output = _cli_pkg._get_git_diff(
                file_path, config.project_root, discovery_mode
            )
            findings = _cli_pkg.check_freshness_diff(str(file_path), diff_output, tree)
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
    return _cli_pkg.check_coverage(src_root, files), package_count


def _griffe_unavailability(config: DocvetConfig) -> UnavailableCheck | None:
    """Report why the griffe check cannot execute, if it cannot.

    Griffe cannot run when the package is not importable, or when
    ``docstring-style`` is ``"sphinx"`` (griffe's Google parser cannot
    read RST field lists). The returned record is *blocking* only when
    ``griffe`` is listed in ``fail-on`` *and* ``fail-on-unavailable``
    is enabled, which makes the run exit non-zero rather than
    reporting success for a gate that never ran. With the opt-in off
    the record still records ``in_fail_on`` so the caller can be
    warned that a configured gate never executed.

    Args:
        config: Loaded docvet configuration.

    Returns:
        An :class:`~docvet.reporting.UnavailableCheck` describing the
        obstacle, or *None* when griffe can run.
    """
    if config.docstring_style == "sphinx":
        reason = "incompatible with sphinx docstring style"
        remedy = 'set docstring-style to "google", or drop griffe from fail-on'
    elif importlib.util.find_spec("griffe") is None:
        reason = "griffe not installed"
        remedy = "pip install 'docvet[griffe]', or drop griffe from fail-on"
    else:
        return None
    in_fail_on = "griffe" in config.fail_on
    return UnavailableCheck(
        check="griffe",
        reason=reason,
        remedy=remedy,
        blocking=in_fail_on and config.fail_on_unavailable,
        in_fail_on=in_fail_on,
    )


def _write_unavailable_notice(
    unavailable: UnavailableCheck,
    *,
    note: bool,
) -> None:
    """Write a stderr notice for a check that could not execute.

    A blocking check reports an error with its remedy, since the run
    exits non-zero because of it. A check that is listed in
    ``fail-on`` but not blocking — ``fail-on-unavailable`` is off —
    reports an unconditional warning naming the check, why it could
    not run, that this check did not fail the run because the setting
    is off, how to make it an error, and that this becomes an error in
    a future major. The notice speaks only for this check: it is
    written mid-run, so another ``fail-on`` check or a coverage
    shortfall can still fail the run. A check that is in neither
    reports a skip line only when *note* is set.

    Args:
        unavailable: The check that could not execute.
        note: Whether to write the skip line for a check that is not
            listed in ``fail-on``.
    """
    if unavailable.blocking:
        sys.stderr.write(
            f"error: {unavailable.check} check is in fail-on but could not run"
            f" ({unavailable.reason})\n"
            f"  remedy: {unavailable.remedy}\n"
        )
    elif unavailable.in_fail_on:
        sys.stderr.write(
            f"warning: {unavailable.check} check is in fail-on but could not run"
            f" ({unavailable.reason}), so that gate never executed\n"
            f"  remedy: {unavailable.remedy}\n"
            "  this did not fail the run because fail-on-unavailable is off;"
            " set fail-on-unavailable = true under [tool.docvet] (or pass"
            " --fail-on-unavailable) to make it an error\n"
            "  a future major release will make this an error by default\n"
        )
    elif note:
        sys.stderr.write(f"{unavailable.check}: skipped ({unavailable.reason})\n")


def _run_griffe(files: list[Path], config: DocvetConfig) -> tuple[list[Finding], int]:
    """Run the griffe compatibility check on discovered files.

    Returns no findings when griffe cannot execute; callers decide
    what that means for the run via :func:`_griffe_unavailability`.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.

    Returns:
        A tuple of ``(findings, file_count)`` where *file_count*
        is the number of files checked by griffe.
    """
    if _griffe_unavailability(config) is not None:
        return [], 0
    src_root = config.project_root / config.src_root
    if not src_root.is_dir():
        return [], 0
    return _cli_pkg.check_griffe_compat(src_root, files), len(files)


# ---------------------------------------------------------------------------
# Fix runner
# ---------------------------------------------------------------------------


def _run_fix(
    files: list[Path],
    config: DocvetConfig,
    *,
    dry_run: bool = False,
    show_progress: bool = False,
) -> tuple[list[Finding], int, int, list[tuple[str, str, str]]]:
    """Run the fix pipeline on discovered files.

    For each file: runs enrichment to find missing sections, scaffolds
    them via ``scaffold_missing_sections``, and either writes the result
    or collects diffs.  In write mode, re-runs enrichment to collect
    scaffold-incomplete findings.  In dry-run mode, collects diffs
    without writing or re-checking. Uses ``_maybe_progressbar`` for
    click-compatible progress display.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        dry_run: When ``True``, collect diffs without writing files
            or re-running enrichment.
        show_progress: Display a progress bar on stderr via
            ``_maybe_progressbar``.

    Returns:
        A tuple of ``(scaffold_findings, files_modified, sections_scaffolded,
        diffs)`` where *diffs* is a list of ``(path, original, modified)``
        tuples (only populated in dry-run mode) and *scaffold_findings*
        is empty in dry-run mode.
    """
    from docvet.checks.fix import RULE_TO_SECTION, scaffold_missing_sections

    all_findings: list[Finding] = []
    files_modified = 0
    sections_scaffolded = 0
    diffs: list[tuple[str, str, str]] = []

    with _maybe_progressbar(files, label="fix", show=show_progress) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = _cli_pkg.ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue

            # Step 1: enrichment to find missing sections.
            findings = _cli_pkg.check_enrichment(
                source,
                tree,
                config.enrichment,
                str(file_path),
                style=config.docstring_style,
            )
            scaffoldable = [f for f in findings if f.rule in RULE_TO_SECTION]
            if not scaffoldable:
                continue

            # Step 2: scaffold missing sections.
            modified = scaffold_missing_sections(source, tree, scaffoldable)
            if modified == source:
                continue

            section_count = len(scaffoldable)
            sections_scaffolded += section_count
            files_modified += 1

            if dry_run:
                diffs.append((str(file_path), source, modified))
                continue

            file_path.write_text(modified, encoding="utf-8")

            # Step 3: re-check for scaffold-incomplete findings.
            try:
                new_tree = _cli_pkg.ast.parse(modified, filename=str(file_path))
            except SyntaxError:
                continue
            new_findings = _cli_pkg.check_enrichment(
                modified,
                new_tree,
                config.enrichment,
                str(file_path),
                style=config.docstring_style,
            )
            all_findings.extend(f for f in new_findings if f.category == "scaffold")

    return all_findings, files_modified, sections_scaffolded, diffs
