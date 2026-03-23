"""MCP server for programmatic docstring quality analysis.

Provides a Model Context Protocol server that exposes docvet checks as
MCP tools. AI agents (Claude Code, Cursor, etc.) connect via stdio and
invoke ``docvet_check`` to run checks on Python files or ``docvet_rules``
to retrieve the full rule catalog (31 rules across 5 checks) with
per-rule fix guidance. Catalog entries include opt-in annotations
(e.g. ``extra-raises-in-docstring`` notes its ``check-extra-raises``
toggle).

Follows the same architectural pattern as :mod:`docvet.lsp`: a
module-level server instance, a single public ``start_server()``
function, and internal helpers for check dispatch and serialization.
Freshness checks are excluded by default because they require git
context; griffe is excluded when not installed. Per-file git diffs
prevent cross-file hunk contamination in freshness mode, and
``SystemExit`` from invalid configuration is caught and returned as
a structured error rather than crashing the server.

Attributes:
    mcp_server: The FastMCP server instance.
    _RULE_TO_CHECK: Dict mapping rule names to their check module for
        O(1) lookup in summary aggregation. Derived from
        :data:`_RULE_CATALOG` entries typed as :class:`RuleCatalogEntry`.

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
"""

from __future__ import annotations

import ast
import json
import logging
import subprocess
from pathlib import Path

from docvet.checks import (
    Finding,
    PresenceStats,
    check_coverage,
    check_enrichment,
    check_presence,
)
from docvet.checks.freshness import check_freshness_diff
from docvet.config import _VALID_CHECK_NAMES, DocvetConfig, load_config
from docvet.discovery import DiscoveryMode, discover_files

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

from ._catalog import _RULE_CATALOG, _RULE_TO_CHECK  # noqa: E402
from ._catalog import RuleCatalogEntry as RuleCatalogEntry  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_finding(finding: Finding) -> dict[str, str | int]:
    """Convert a Finding to a JSON-serializable dict.

    Produces a dict with the six canonical Finding fields, matching the
    field set from :func:`~docvet.reporting.format_json` (excluding the
    derived ``severity`` field).

    Args:
        finding: The docvet finding to serialize.

    Returns:
        A dict with keys ``file``, ``line``, ``symbol``, ``rule``,
        ``message``, and ``category``.

    Examples:
        Serialize a finding for MCP response:

        ```python
        from docvet.checks import Finding

        f = Finding("a.py", 10, "foo", "missing-raises", "msg", "required")
        d = _serialize_finding(f)
        assert d["rule"] == "missing-raises"
        ```
    """
    return {
        "file": finding.file,
        "line": finding.line,
        "symbol": finding.symbol,
        "rule": finding.rule,
        "message": finding.message,
        "category": finding.category,
    }


def _run_per_file_checks(
    files: list[Path],
    config: DocvetConfig,
    checks: frozenset[str],
) -> tuple[list[Finding], PresenceStats | None]:
    """Run per-file checks (presence, enrichment) on all files.

    Parses each file into an AST and dispatches to the requested
    per-file checks. Aggregates presence stats across all files when
    the presence check is enabled.

    Args:
        files: List of absolute paths to Python files.
        config: The loaded docvet configuration.
        checks: Set of check names to run.

    Returns:
        A tuple of ``(findings, presence_stats)`` where
        *presence_stats* is ``None`` when the presence check did not
        run.
    """
    findings: list[Finding] = []
    all_presence_stats: list[PresenceStats] = []

    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Cannot read file: %s", file_path)
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            logger.warning("Cannot parse file: %s", file_path)
            continue

        rel_path = str(file_path)

        if "presence" in checks:
            pf, ps = check_presence(source, rel_path, config.presence)
            findings.extend(pf)
            all_presence_stats.append(ps)

        if "enrichment" in checks:
            findings.extend(check_enrichment(source, tree, config.enrichment, rel_path))

    presence_stats: PresenceStats | None = None
    if "presence" in checks and all_presence_stats:
        total_doc = sum(s.documented for s in all_presence_stats)
        total_all = sum(s.total for s in all_presence_stats)
        presence_stats = PresenceStats(documented=total_doc, total=total_all)

    return findings, presence_stats


def _run_freshness(
    files: list[Path],
    config: DocvetConfig,
) -> tuple[list[Finding], str | None]:
    """Run the freshness diff check on files with git context.

    Verifies git is available, then retrieves a per-file diff for each
    file and runs freshness checks. Per-file diffs prevent cross-file
    hunk contamination. Returns findings and an optional error message
    when git is unavailable.

    Args:
        files: List of absolute paths to Python files.
        config: The loaded docvet configuration.

    Returns:
        A tuple of ``(findings, error)`` where *error* is ``None``
        when the check executed successfully.
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
            cwd=str(config.project_root),
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [], (
            "freshness check requires git context: "
            "not a git repository or git is not installed"
        )

    findings: list[Finding] = []
    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        # Per-file diff to avoid cross-file hunk contamination
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(config.project_root),
        )
        findings.extend(check_freshness_diff(str(file_path), result.stdout, tree))
    return findings, None


def _run_griffe(
    src_root: Path,
    files: list[Path],
) -> tuple[list[Finding], str | None]:
    """Run the griffe compatibility check.

    Returns findings and an optional error message when griffe is not
    available or the check fails.

    Args:
        src_root: Source root directory for griffe package loading.
        files: List of absolute paths to Python files.

    Returns:
        A tuple of ``(findings, error)`` where *error* is ``None``
        when the check executed successfully.
    """
    if not _GRIFFE_AVAILABLE:
        return [], "griffe check requires the griffe extra: pip install docvet[griffe]"
    try:
        return list(check_griffe_compat(src_root, files)), None
    except (ImportError, OSError, AttributeError) as exc:
        return [], f"griffe check failed: {exc}"


def _run_checks(
    files: list[Path],
    config: DocvetConfig,
    checks: frozenset[str],
) -> tuple[list[Finding], PresenceStats | None, list[str]]:
    """Run the requested docvet checks on discovered files.

    Dispatches to per-file checks (presence, enrichment) and batch
    checks (coverage, griffe, freshness) based on the *checks* set.
    Returns findings, optional presence stats, and a list of error
    messages for checks that could not run (e.g., griffe not installed,
    git unavailable).

    Args:
        files: List of absolute paths to Python files.
        config: The loaded docvet configuration.
        checks: Set of check names to run.

    Returns:
        A tuple of ``(findings, presence_stats, errors)`` where
        *presence_stats* is ``None`` when the presence check did not
        run, and *errors* contains messages for checks that failed
        to execute.
    """
    errors: list[str] = []

    findings, presence_stats = _run_per_file_checks(files, config, checks)

    src_root = config.project_root / config.src_root

    if "coverage" in checks:
        findings.extend(check_coverage(src_root, files))

    if "griffe" in checks:
        griffe_findings, griffe_error = _run_griffe(src_root, files)
        findings.extend(griffe_findings)
        if griffe_error:
            errors.append(griffe_error)

    if "freshness" in checks:
        freshness_findings, freshness_error = _run_freshness(files, config)
        findings.extend(freshness_findings)
        if freshness_error:
            errors.append(freshness_error)

    return findings, presence_stats, errors


def _build_summary(
    findings: list[Finding],
    file_count: int,
    checks: frozenset[str],
) -> dict[str, object]:
    """Build the summary section of the MCP response.

    Counts total findings, groups by category and by check module using
    the :data:`_RULE_TO_CHECK` lookup dict, and records the number of
    files checked.

    Args:
        findings: All findings from the check run.
        file_count: Number of files that were checked.
        checks: Set of check names that were run.

    Returns:
        A dict with ``total``, ``by_category``, ``files_checked``, and
        ``by_check`` keys.
    """
    by_category: dict[str, int] = {"required": 0, "recommended": 0}
    by_check: dict[str, int] = {c: 0 for c in sorted(checks)}

    for f in findings:
        by_category[f.category] += 1
        check_name = _RULE_TO_CHECK.get(f.rule)
        if check_name and check_name in by_check:
            by_check[check_name] += 1

    return {
        "total": len(findings),
        "by_category": by_category,
        "files_checked": file_count,
        "by_check": by_check,
    }


def _load_config_for_path(target: Path) -> DocvetConfig:
    """Find and load docvet config relative to a target path.

    Walks upward from *target* (or its parent if a file) to locate the
    nearest ``pyproject.toml``, then delegates to :func:`load_config`.

    Args:
        target: Resolved path to a file or directory.

    Returns:
        A fully resolved DocvetConfig.
    """
    search = target if target.is_dir() else target.parent
    pyproject: Path | None = None
    d = search
    while True:
        candidate = d / "pyproject.toml"
        if candidate.is_file():
            pyproject = candidate
            break
        parent = d.parent
        if parent == d:
            break
        d = parent
    return load_config(path=pyproject)


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
    crashing the server.

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
    target = Path(path).resolve()

    # Validate path
    if not target.exists():
        return json.dumps({"error": f"Path does not exist: {path}"})

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
    if target.is_file() and target.suffix == ".py":
        discovered = discover_files(config, DiscoveryMode.FILES, files=[target])
    elif target.is_dir():
        all_files = discover_files(config, DiscoveryMode.ALL)
        discovered = [f for f in all_files if f.is_relative_to(target)]
    else:
        return json.dumps({"error": f"Path is not a Python file or directory: {path}"})

    # Run checks
    findings, presence_stats, errors = _run_checks(discovered, config, requested)

    # Build response
    result: dict[str, object] = {
        "findings": [_serialize_finding(f) for f in findings],
        "summary": _build_summary(findings, len(discovered), requested),
    }

    if presence_stats is not None:
        pct = presence_stats.percentage
        result["presence_coverage"] = {
            "documented": presence_stats.documented,
            "total": presence_stats.total,
            "percentage": round(pct, 1),
            "threshold": config.presence.min_coverage,
            "passed": pct >= config.presence.min_coverage,
        }

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
