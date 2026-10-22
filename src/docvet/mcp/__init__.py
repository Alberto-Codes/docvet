"""MCP server for programmatic docstring quality analysis.

Provides a Model Context Protocol server that exposes docvet checks as
MCP tools. AI agents (Claude Code, Cursor, etc.) connect via stdio and
invoke ``docvet_check`` to run checks on Python files or ``docvet_rules``
to retrieve the full rule catalog (32 rules across 5 checks) with
per-rule fix guidance. Catalog entries include opt-in annotations
(e.g. ``extra-raises-in-docstring`` notes its ``check-extra-raises``
toggle).

Follows the same architectural pattern as :mod:`docvet.lsp`: a
module-level server instance, a single public ``start_server()``
function, and internal helpers for check dispatch and serialization.
The MCP-independent helpers live in :mod:`docvet.mcp._runner` and the
rule catalog in :mod:`docvet.rules`; both are re-exported here.
Freshness checks are excluded by default because they require git
context; griffe is excluded when not installed. Per-file git diffs
prevent cross-file hunk contamination in freshness mode; those git
commands run with :func:`docvet.discovery.git_env` so an inherited
``GIT_DIR`` cannot redirect them away from the project root, and
``SystemExit`` from invalid configuration is caught and returned as
a structured error rather than crashing the server. Source loading shares
Python encoding detection and reports incomplete input analysis through
additive run metadata, preserving legacy error fields and selection counts.

Attributes:
    mcp_server: The FastMCP server instance.
    _RULE_TO_CHECK: Dict mapping rule names to their check module,
        re-exported from :mod:`docvet.rules`.

Examples:
    Start the server on stdio (typically invoked by ``docvet mcp``):

    ```python
    from docvet.mcp import start_server

    start_server()
    ```

    Install with the ``[mcp]`` extra:

    ```bash
    $ pip install docvet[mcp]
    ```

See Also:
    [`docvet.lsp`][]: LSP server for real-time editor diagnostics.
    [`docvet.checks`][]: Check modules that produce Finding objects.
    [`docvet.config`][]: Configuration loaded on server startup.
    [`docvet.rules`][]: Rule catalog served by ``docvet_rules``.
"""

from __future__ import annotations

import json
import logging
import subprocess  # noqa: F401 - kept reachable as docvet.mcp.subprocess
from dataclasses import asdict
from pathlib import Path

from docvet.checks import Finding, PresenceStats, check_coverage
from docvet.config import _VALID_CHECK_NAMES, DocvetConfig
from docvet.discovery import DiscoveryMode, discover_files
from docvet.reporting import UnavailableCheck, determine_run_outcome
from docvet.rules import _RULE_CATALOG
from docvet.rules import _RULE_TO_CHECK as _RULE_TO_CHECK
from docvet.rules import RuleCatalogEntry as RuleCatalogEntry
from docvet.source import InputError, SourceCache

from ._runner import (
    _build_summary,
    _load_config_for_path,
    _run_freshness,
    _run_per_file_checks,
    _serialize_finding,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    msg = "MCP server requires the mcp extra: pip install docvet[mcp]"
    raise ImportError(msg) from exc

try:
    from docvet.checks.griffe_compat import check_griffe_compat

    _GRIFFE_AVAILABLE = True
except ImportError:
    _GRIFFE_AVAILABLE = False

__all__ = ["start_server"]

logger = logging.getLogger(__name__)

# Default checks for MCP (freshness excluded — requires git context;
# griffe excluded when not installed to avoid spurious error entries)
_DEFAULT_MCP_CHECKS: frozenset[str] = frozenset(
    name
    for name in _VALID_CHECK_NAMES
    if name != "freshness" and (_GRIFFE_AVAILABLE or name != "griffe")
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_griffe(
    src_root: Path,
    files: list[Path],
    source_cache: SourceCache | None = None,
) -> tuple[list[Finding], str | None]:
    """Run the griffe compatibility check.

    Returns findings and an optional error message when griffe is not
    available or the check fails.

    Args:
        src_root: Source root directory for griffe package loading.
        files: List of absolute paths to Python files.
        source_cache: Shared decoded sources for encoding-aware griffe checks.

    Returns:
        A tuple of ``(findings, error)`` where *error* is ``None``
        when the check executed successfully.
    """
    if not _GRIFFE_AVAILABLE:
        return [], "griffe check requires the griffe extra: pip install docvet[griffe]"
    try:
        if source_cache is None:
            return list(check_griffe_compat(src_root, files)), None
        return list(
            check_griffe_compat(src_root, files, source_cache=source_cache)
        ), None
    except (ImportError, OSError, AttributeError) as exc:
        return [], f"griffe check failed: {exc}"


def _run_checks(
    files: list[Path],
    config: DocvetConfig,
    checks: frozenset[str],
    source_cache: SourceCache | None = None,
    unavailable: list[UnavailableCheck] | None = None,
) -> tuple[list[Finding], PresenceStats | None, list[str]]:
    """Run the requested docvet checks on discovered files.

    Dispatches to per-file checks (presence, enrichment) and batch
    checks (coverage, griffe, freshness) based on the *checks* set.
    Returns findings, optional presence stats, and a list of error
    messages for checks that could not run (e.g., griffe not installed,
    git unavailable). Freshness retains the shared prerequisite record's
    reason and remedy while also populating the legacy errors list.

    Args:
        files: List of absolute paths to Python files.
        config: The loaded docvet configuration.
        checks: Set of check names to run.
        source_cache: Shared invocation source cache.
        unavailable: Optional sink for structured check execution failures.

    Returns:
        A tuple of ``(findings, presence_stats, errors)`` where
        *presence_stats* is ``None`` when the presence check did not
        run, and *errors* contains messages for checks that failed
        to execute.
    """
    errors: list[str] = []

    cache = source_cache if source_cache is not None else SourceCache()
    analysis_files = files
    if checks & {"presence", "enrichment", "freshness"} or (
        "griffe" in checks and _GRIFFE_AVAILABLE
    ):
        analysis_files = [path for path in files if cache.get(path) is not None]
    findings, presence_stats = _run_per_file_checks(
        analysis_files, config, checks, cache
    )

    src_root = config.project_root / config.src_root

    if "coverage" in checks:
        findings.extend(check_coverage(src_root, files))

    if "griffe" in checks:
        griffe_findings, griffe_error = _run_griffe(src_root, analysis_files, cache)
        findings.extend(griffe_findings)
        if griffe_error:
            errors.append(griffe_error)
            if unavailable is not None:
                unavailable.append(_griffe_unavailable(griffe_error, config))

    if "freshness" in checks:
        freshness_findings, freshness_error = _run_freshness(
            analysis_files, config, cache
        )
        findings.extend(freshness_findings)
        if freshness_error:
            errors.append(freshness_error.reason)
            if unavailable is not None:
                unavailable.append(freshness_error)

    return findings, presence_stats, errors


def _griffe_unavailable(reason: str, config: DocvetConfig) -> UnavailableCheck:
    """Describe an unavailable griffe check using the configured-gate policy.

    Args:
        reason: Legacy error message explaining the execution failure.
        config: Configuration controlling availability gating.

    Returns:
        Structured availability record with a remedy and gate state.
    """
    configured_gate = "griffe" in config.fail_on
    return UnavailableCheck(
        check="griffe",
        reason=reason,
        remedy="Install docvet[griffe] and verify source loading",
        blocking=configured_gate and config.fail_on_unavailable,
        configured_gate=configured_gate,
    )


def _build_response(
    files: list[Path],
    config: DocvetConfig,
    checks: frozenset[str],
    findings: list[Finding],
    presence_stats: PresenceStats | None,
    cache: SourceCache,
    unavailable: list[UnavailableCheck] | None = None,
) -> dict[str, object]:
    """Build additive run metadata without changing finding serialization.

    Args:
        files: Selected files, preserving legacy selection counts.
        config: Loaded configuration for gates and coverage thresholds.
        checks: Requested checks.
        findings: Findings produced by successfully analyzed inputs.
        presence_stats: Observed presence statistics, when available.
        cache: Shared sources and deduplicated input failures.
        unavailable: Structured check execution failures.

    Returns:
        The complete MCP result with input accounting and run outcome.
    """
    failed = {Path(error.file).absolute() for error in cache.errors}
    attempted = set(files) | set(cache.attempted_paths) | failed
    analyzed = set(cache.successful_paths)
    if "coverage" in checks:
        analyzed.update(files)
    analyzed -= failed
    summary = _build_summary(findings, len(files), checks)
    summary.update(
        files_attempted=len(attempted),
        files_analyzed=len(analyzed),
        files_failed=len(failed),
    )
    grouped = {
        check: [f for f in findings if _RULE_TO_CHECK.get(f.rule) == check]
        for check in checks
    }
    outcome = determine_run_outcome(
        grouped,
        config,
        presence_stats=presence_stats,
        input_errors=cache.errors,
        unavailable=unavailable or (),
    )
    result: dict[str, object] = {
        "findings": [_serialize_finding(f) for f in findings],
        "summary": summary,
        "run": {
            "status": outcome.status,
            "exit_code": outcome.exit_code,
            "exit_reason": outcome.reason,
            "input_errors": [asdict(error) for error in cache.errors],
            "unavailable_checks": [asdict(item) for item in unavailable or ()],
        },
    }
    if presence_stats is not None or ("presence" in checks and cache.errors):
        stats = presence_stats or PresenceStats(documented=0, total=0)
        complete = not cache.errors
        result["presence_coverage"] = {
            "documented": stats.documented,
            "total": stats.total,
            "percentage": round(stats.percentage, 1) if analyzed else None,
            "threshold": config.presence.min_coverage,
            "passed": complete and stats.percentage >= config.presence.min_coverage,
            "complete": complete,
        }
    return result


def _invalid_target(target: Path, message: str, cache: SourceCache) -> str:
    """Serialize invalid targets with the legacy error and structured metadata.

    Args:
        target: Invalid requested path.
        message: Existing human-readable error text.
        cache: Invocation source cache.

    Returns:
        JSON response retaining the legacy error field.
    """
    cache.record_error(InputError(str(target), "input", message))
    result = _build_response([], DocvetConfig(), frozenset(), [], None, cache)
    result["error"] = message
    return json.dumps(result)


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp_server = FastMCP("docvet")


@mcp_server.tool()
def docvet_check(path: str, checks: list[str] | None = None) -> str:
    """Run docvet checks on Python files.

    Analyzes Python source files for docstring quality issues. Runs all
    enabled checks except freshness by default (freshness requires git
    context; griffe also excluded when not installed). When *path* is a
    directory, only files within that directory tree are checked (not the
    entire project). Returns a JSON object with findings, summary
    statistics, and optional presence coverage data. Invalid
    configuration triggers a structured error response instead of
    crashing the server. Input, read, decode, and parse failures report
    an incomplete run with unique attempted, analyzed, and failed file counts.
    Presence coverage explicitly marks incomplete results, with a null
    percentage when no input could be analyzed. Legitimate empty selections
    succeed without requiring optional check dependencies or git context.

    Args:
        path: Path to a Python file or directory to check.
        checks: Optional list of check names to run. Valid names are
            ``presence``, ``enrichment``, ``freshness``, ``coverage``,
            ``griffe``. Defaults to all except freshness.

    Returns:
        JSON string with ``findings``, ``summary``, and optionally
        ``presence_coverage`` keys. Returns an ``error`` key on
        invalid path, unknown check name, or malformed configuration.
        Call docvet_rules() for per-rule fix guidance and format examples.
    """
    cache = SourceCache()
    target = Path(path).absolute()
    try:
        target = target.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        return _invalid_target(target, str(exc), cache)

    # Validate path
    if not target.exists():
        return _invalid_target(target, f"Path does not exist: {path}", cache)

    # Find pyproject.toml by walking up from target
    try:
        config = _load_config_for_path(target)
    except SystemExit:
        return json.dumps({"error": "Invalid docvet configuration in pyproject.toml"})

    # Resolve checks
    if checks is not None:
        invalid = sorted(c for c in checks if c not in _VALID_CHECK_NAMES)
        if invalid:
            valid_csv = ", ".join(sorted(_VALID_CHECK_NAMES))
            return json.dumps(
                {
                    "error": f"Invalid check names: {', '.join(invalid)}. Valid: {valid_csv}"
                }
            )
        requested = frozenset(checks)
    else:
        requested = _DEFAULT_MCP_CHECKS

    # Discover files
    discovery_errors: list[InputError] = []
    if target.is_file() and target.suffix == ".py":
        discovered = discover_files(
            config, DiscoveryMode.FILES, files=[target], errors=discovery_errors
        )
    elif target.is_dir():
        all_files = discover_files(config, DiscoveryMode.ALL, errors=discovery_errors)
        discovered = [f for f in all_files if f.is_relative_to(target)]
    else:
        return _invalid_target(
            target, f"Path is not a Python file or directory: {path}", cache
        )

    for error in discovery_errors:
        cache.record_error(error)
    if not discovered and not cache.errors:
        return json.dumps(_build_response([], config, requested, [], None, cache))
    # Run checks
    unavailable: list[UnavailableCheck] = []
    findings, presence_stats, errors = _run_checks(
        discovered, config, requested, cache, unavailable
    )

    result = _build_response(
        discovered, config, requested, findings, presence_stats, cache, unavailable
    )

    if errors:
        result["errors"] = errors

    return json.dumps(result)


@mcp_server.tool()
def docvet_rules() -> str:
    """List all available docvet rules with fix guidance.

    Returns the complete rule catalog with rule name, associated check
    module, human-readable description, category (required or
    recommended), prescriptive fix guidance, and a format example.

    Returns:
        JSON string with a ``rules`` array containing objects with
        ``name``, ``check``, ``description``, ``category``,
        ``guidance``, and ``fix_example`` keys.
    """
    return json.dumps({"rules": _RULE_CATALOG})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_server() -> None:
    """Start the MCP server on stdio.

    Starts the FastMCP server in stdio mode. Configuration is loaded
    per-request by each tool handler. This function blocks until the
    client disconnects.

    Examples:
        Typically invoked by the ``docvet mcp`` CLI command:

        ```python
        from docvet.mcp import start_server

        start_server()
        ```
    """
    mcp_server.run(transport="stdio")
