"""MCP server for programmatic docstring quality analysis.

Provides a Model Context Protocol server that exposes docvet checks as
MCP tools. AI agents (Claude Code, Cursor, etc.) connect via stdio and
invoke ``docvet_check`` to run checks on Python files or ``docvet_rules``
to retrieve the full rule catalog.

Follows the same architectural pattern as :mod:`docvet.lsp`: a
module-level server instance, a single public ``start_server()``
function, and internal helpers for check dispatch and serialization.
Freshness checks are excluded by default because they require git
context that may not be available in MCP client environments.

Attributes:
    mcp_server: The FastMCP server instance.

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

# Default checks for MCP (freshness excluded — requires git context)
_DEFAULT_MCP_CHECKS: frozenset[str] = _VALID_CHECK_NAMES - {"freshness"}

# ---------------------------------------------------------------------------
# Rule catalog
# ---------------------------------------------------------------------------

_RULE_CATALOG: list[dict[str, str]] = [
    {
        "name": "missing-docstring",
        "check": "presence",
        "description": "Public symbol lacks a docstring.",
        "category": "required",
    },
    {
        "name": "missing-raises",
        "check": "enrichment",
        "description": "Function raises an exception not documented in Raises section.",
        "category": "required",
    },
    {
        "name": "missing-yields",
        "check": "enrichment",
        "description": "Generator function lacks a Yields section.",
        "category": "required",
    },
    {
        "name": "missing-receives",
        "check": "enrichment",
        "description": "Generator function using send() lacks a Receives section.",
        "category": "required",
    },
    {
        "name": "missing-warns",
        "check": "enrichment",
        "description": "Function issues warnings not documented in Warns section.",
        "category": "required",
    },
    {
        "name": "missing-other-parameters",
        "check": "enrichment",
        "description": "Function has *args or **kwargs not documented in Other Parameters.",
        "category": "required",
    },
    {
        "name": "missing-attributes",
        "check": "enrichment",
        "description": "Class or module has undocumented public attributes.",
        "category": "required",
    },
    {
        "name": "missing-typed-attributes",
        "check": "enrichment",
        "description": "Attributes section uses untyped style instead of typed.",
        "category": "recommended",
    },
    {
        "name": "missing-examples",
        "check": "enrichment",
        "description": "Public symbol lacks an Examples section.",
        "category": "recommended",
    },
    {
        "name": "missing-cross-references",
        "check": "enrichment",
        "description": "Docstring references other symbols without cross-reference links.",
        "category": "recommended",
    },
    {
        "name": "prefer-fenced-code-blocks",
        "check": "enrichment",
        "description": "Docstring uses indented code blocks instead of fenced.",
        "category": "recommended",
    },
    {
        "name": "stale-docstring-high",
        "check": "freshness",
        "description": "Function signature changed without docstring update.",
        "category": "required",
    },
    {
        "name": "stale-docstring-medium",
        "check": "freshness",
        "description": "Function body changed without docstring update.",
        "category": "required",
    },
    {
        "name": "stale-docstring-low",
        "check": "freshness",
        "description": "Minor code change near symbol without docstring update.",
        "category": "recommended",
    },
    {
        "name": "docstring-drift",
        "check": "freshness",
        "description": "Docstring has not been updated since significant code changes.",
        "category": "required",
    },
    {
        "name": "docstring-age",
        "check": "freshness",
        "description": "Docstring has not been updated for an extended period.",
        "category": "recommended",
    },
    {
        "name": "missing-init-py",
        "check": "coverage",
        "description": "Directory with Python files lacks __init__.py for mkdocs discovery.",
        "category": "required",
    },
    {
        "name": "griffe-unknown-param",
        "check": "griffe",
        "description": "Griffe reports a parameter not matching the function signature.",
        "category": "required",
    },
    {
        "name": "griffe-missing-type",
        "check": "griffe",
        "description": "Griffe reports a missing type annotation in docstring.",
        "category": "recommended",
    },
    {
        "name": "griffe-format-warning",
        "check": "griffe",
        "description": "Griffe reports a formatting issue in the docstring.",
        "category": "recommended",
    },
]


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

    Verifies git is available, retrieves the current diff, and runs
    freshness checks on each file. Returns findings and an optional
    error message when git is unavailable.

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

    result = subprocess.run(
        ["git", "diff", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(config.project_root),
    )
    diff_output = result.stdout
    findings: list[Finding] = []
    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        findings.extend(check_freshness_diff(str(file_path), diff_output, tree))
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

    Counts total findings, groups by category and by check module, and
    records the number of files checked.

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
        by_category[f.category] = by_category.get(f.category, 0) + 1
        # Map rule to check module
        for rule_entry in _RULE_CATALOG:
            if rule_entry["name"] == f.rule:
                check_name = rule_entry["check"]
                by_check[check_name] = by_check.get(check_name, 0) + 1
                break

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
    context). Returns a JSON object with findings, summary statistics,
    and optional presence coverage data.

    Args:
        path: Path to a Python file or directory to check.
        checks: Optional list of check names to run. Valid names are
            ``presence``, ``enrichment``, ``freshness``, ``coverage``,
            ``griffe``. Defaults to all except freshness.

    Returns:
        JSON string with ``findings``, ``summary``, and optionally
        ``presence_coverage`` keys.
    """
    target = Path(path).resolve()

    # Validate path
    if not target.exists():
        return json.dumps({"error": f"Path does not exist: {path}"})

    # Find pyproject.toml by walking up from target
    config = _load_config_for_path(target)

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
        discovered = discover_files(config, DiscoveryMode.ALL)
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
    """List all available docvet rules.

    Returns the complete rule catalog with rule name, associated check
    module, human-readable description, and category (required or
    recommended).

    Returns:
        JSON string with a ``rules`` array containing objects with
        ``name``, ``check``, ``description``, and ``category`` keys.
    """
    return json.dumps({"rules": _RULE_CATALOG})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_server() -> None:
    """Start the MCP server on stdio.

    Loads docvet configuration and starts the FastMCP server in stdio
    mode. This function blocks until the client disconnects.

    Examples:
        Typically invoked by the ``docvet mcp`` CLI command:

        ```python
        from docvet.mcp import start_server

        start_server()
        ```
    """
    mcp_server.run(transport="stdio")
