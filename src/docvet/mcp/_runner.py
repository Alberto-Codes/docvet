"""Check-running helpers behind the docvet MCP tools.

Holds the MCP-independent parts of the ``docvet_check`` tool: finding
serialization, per-file presence and enrichment dispatch, the freshness
diff run, summary aggregation by check module, and config discovery.
None of these touch the MCP SDK, which keeps the server module in
:mod:`docvet.mcp` focused on tool registration. Freshness git commands
run with :func:`docvet.discovery.git_env` so an inherited ``GIT_DIR``
cannot redirect them away from the project root.

The griffe dispatch stays in :mod:`docvet.mcp` because callers patch
``docvet.mcp._GRIFFE_AVAILABLE`` and ``docvet.mcp.check_griffe_compat``.

Examples:
    Serialize a finding for an MCP response:

    ```python
    from docvet.checks import Finding
    from docvet.mcp._runner import _serialize_finding

    f = Finding("a.py", 10, "foo", "missing-raises", "msg", "required")
    assert _serialize_finding(f)["rule"] == "missing-raises"
    ```

See Also:
    [`docvet.mcp`][]: MCP server and tool handlers.
    [`docvet.rules`][]: Rule catalog used for summary aggregation.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from pathlib import Path

from docvet.checks import (
    Finding,
    PresenceStats,
    check_enrichment,
    check_presence,
)
from docvet.checks.freshness import check_freshness_diff
from docvet.config import DocvetConfig, load_config
from docvet.discovery import git_env
from docvet.rules import _RULE_TO_CHECK

__all__: list[str] = []

# Same logger name as before the split so log filtering keeps working.
logger = logging.getLogger("docvet.mcp")


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
    hunk contamination. Both git invocations use
    :func:`docvet.discovery.git_env`, so they resolve the repository
    from ``config.project_root`` rather than from an inherited
    ``GIT_DIR``. Returns findings and an optional error message when
    git is unavailable.

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
            env=git_env(),
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
            env=git_env(),
        )
        findings.extend(check_freshness_diff(str(file_path), result.stdout, tree))
    return findings, None


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
