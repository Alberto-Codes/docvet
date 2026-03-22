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
from typing import TypedDict

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

# ---------------------------------------------------------------------------
# Rule catalog
# ---------------------------------------------------------------------------


class RuleCatalogEntry(TypedDict):
    """A single entry in the docvet rule catalog.

    Attributes:
        name (str): The rule identifier (e.g. ``missing-raises``).
        check (str): The check module that owns this rule.
        description (str): Human-readable description of what the rule detects.
        category (str): Severity category (``required`` or ``recommended``).
        guidance (str): Prescriptive fix guidance for the rule.
        fix_example (str | None): Optional code example showing the fix.
    """

    name: str
    check: str
    description: str
    category: str
    guidance: str
    fix_example: str | None


_RULE_CATALOG: list[RuleCatalogEntry] = [
    {
        "name": "missing-docstring",
        "check": "presence",
        "description": "Public symbol lacks a docstring.",
        "category": "required",
        "guidance": (
            "Add a Google-style docstring with a one-line summary ending in a"
            " period, followed by a detailed description."
        ),
        "fix_example": '"""One-line summary.\n\nDetailed description.\n"""',
    },
    {
        "name": "overload-has-docstring",
        "check": "presence",
        "description": (
            "@overload-decorated function has a docstring — document the"
            " implementation instead."
        ),
        "category": "required",
        "guidance": (
            "Remove the docstring from the @overload-decorated function and"
            " document the implementation function instead."
        ),
        "fix_example": (
            "@overload\ndef connect(address: str) -> TCPConnection: ...\n\n"
            "def connect(address):\n"
            '    """Connect to a server.\n\n'
            "    Args:\n"
            '        address: Hostname string or (host, port) tuple.\n    """'
        ),
    },
    {
        "name": "missing-raises",
        "check": "enrichment",
        "description": "Function raises an exception not documented in Raises section.",
        "category": "required",
        "guidance": (
            "Add a Raises: section listing each exception type and the"
            " condition that triggers it."
        ),
        "fix_example": "Raises:\n    ValueError: If the input is negative.",
    },
    {
        "name": "missing-returns",
        "check": "enrichment",
        "description": "Function returns a value but has no Returns section.",
        "category": "required",
        "guidance": (
            "Add a Returns: section describing the type and meaning of the"
            " return value."
        ),
        "fix_example": "Returns:\n    The parsed configuration as a dictionary.",
    },
    {
        "name": "missing-yields",
        "check": "enrichment",
        "description": "Generator function lacks a Yields section.",
        "category": "required",
        "guidance": (
            "Add a Yields: section describing what values the generator produces."
        ),
        "fix_example": (
            "Yields:\n    Row data as a dictionary with column names as keys."
        ),
    },
    {
        "name": "missing-receives",
        "check": "enrichment",
        "description": "Generator function using send() lacks a Receives section.",
        "category": "required",
        "guidance": (
            "Add a Receives: section documenting values accepted via .send()."
        ),
        "fix_example": ("Receives:\n    Numeric value to add to the running total."),
    },
    {
        "name": "missing-warns",
        "check": "enrichment",
        "description": "Function issues warnings not documented in Warns section.",
        "category": "required",
        "guidance": (
            "Add a Warns: section listing each warning category and the condition."
        ),
        "fix_example": ("Warns:\n    UserWarning: If timeout is less than 5 seconds."),
    },
    {
        "name": "missing-deprecation",
        "check": "enrichment",
        "description": (
            "Function uses deprecation patterns (warnings.warn with"
            " DeprecationWarning or @deprecated decorator) but has no"
            " deprecation notice in docstring."
        ),
        "category": "required",
        "guidance": (
            "Add the word 'deprecated' somewhere in the docstring"
            " (case-insensitive). Common formats: Google-style"
            " 'Deprecated:' section, Sphinx '.. deprecated::' directive,"
            " or inline mention."
        ),
        "fix_example": (
            "Deprecated:\n    Use :func:`new_func` instead. Will be removed in v3.0."
        ),
    },
    {
        "name": "missing-other-parameters",
        "check": "enrichment",
        "description": "Function has *args or **kwargs not documented in Other Parameters.",
        "category": "required",
        "guidance": (
            "Add an Other Parameters: section documenting *args and/or **kwargs."
        ),
        "fix_example": (
            "Other Parameters:\n    **kwargs: Arbitrary keyword arguments"
            " passed to the\n        underlying handler."
        ),
    },
    {
        "name": "missing-attributes",
        "check": "enrichment",
        "description": "Class or module has undocumented public attributes.",
        "category": "required",
        "guidance": (
            "Add an Attributes: section listing all public instance attributes"
            " with types and descriptions."
        ),
        "fix_example": (
            "Attributes:\n    name (str): The user's display name.\n"
            "    email (str): The user's email address."
        ),
    },
    {
        "name": "missing-typed-attributes",
        "check": "enrichment",
        "description": "Attributes section uses untyped style instead of typed.",
        "category": "recommended",
        "guidance": "Use typed attribute format: name (type): description.",
        "fix_example": (
            "Attributes:\n    host (str): The server hostname.\n"
            "    port (int): The server port number."
        ),
    },
    {
        "name": "missing-examples",
        "check": "enrichment",
        "description": "Public symbol lacks an Examples section.",
        "category": "recommended",
        "guidance": (
            "Add an Examples: section with a brief description followed by a"
            " fenced code block using ```python."
        ),
        "fix_example": (
            "Examples:\n    Create a widget with default settings:\n\n"
            "    ```python\n    widget = Widget()\n"
            "    assert widget.is_active\n    ```"
        ),
    },
    {
        "name": "missing-cross-references",
        "check": "enrichment",
        "description": (
            "Module missing See Also section, or existing See Also entries"
            " lack cross-reference link syntax."
        ),
        "category": "recommended",
        "guidance": (
            "Add a See Also: section using mkdocstrings cross-reference"
            " syntax: [`fully.qualified.Name`][]. Each entry uses"
            " bracket-backtick-bracket format for linkable references."
        ),
        "fix_example": (
            "See Also:\n    [`mypackage.Config`][]: Application"
            " configuration.\n    [`mypackage.utils`][]: Utility functions."
        ),
    },
    {
        "name": "prefer-fenced-code-blocks",
        "check": "enrichment",
        "description": "Docstring uses indented code blocks instead of fenced.",
        "category": "recommended",
        "guidance": (
            "Replace >>> doctest or :: reST indented code blocks with fenced"
            " ```python blocks."
        ),
        "fix_example": (
            "Examples:\n    Run the check:\n\n    ```python\n"
            "    result = check(data)\n    ```"
        ),
    },
    {
        "name": "stale-signature",
        "check": "freshness",
        "description": "Function signature changed without docstring update.",
        "category": "required",
        "guidance": (
            "Update the docstring Args, Returns, and Raises sections to match"
            " the changed function signature."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-body",
        "check": "freshness",
        "description": "Function body changed without docstring update.",
        "category": "recommended",
        "guidance": (
            "Review and update the docstring description and sections to"
            " reflect the changed function behavior."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-import",
        "check": "freshness",
        "description": "Import changed near symbol without docstring update.",
        "category": "recommended",
        "guidance": (
            "Review the docstring for references to changed imports and update"
            " accordingly."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-drift",
        "check": "freshness",
        "description": "Docstring has not been updated since significant code changes.",
        "category": "recommended",
        "guidance": (
            "Review and refresh the docstring to reflect cumulative code"
            " changes since the last docstring edit."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-age",
        "check": "freshness",
        "description": "Docstring has not been updated for an extended period.",
        "category": "recommended",
        "guidance": (
            "Review and confirm the docstring still accurately describes the"
            " symbol's current behavior."
        ),
        "fix_example": None,
    },
    {
        "name": "missing-init",
        "check": "coverage",
        "description": "Directory with Python files lacks __init__.py for mkdocs discovery.",
        "category": "required",
        "guidance": (
            "Create an __init__.py file with a module docstring in the directory."
        ),
        "fix_example": None,
    },
    {
        "name": "missing-param-in-docstring",
        "check": "enrichment",
        "description": "Function signature parameter not documented in Args section.",
        "category": "required",
        "guidance": (
            "Add the missing parameter to the Args: section with a type"
            " annotation and description."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "extra-param-in-docstring",
        "check": "enrichment",
        "description": "Args section documents a parameter not in the function signature.",
        "category": "required",
        "guidance": (
            "Remove the stale parameter entry from the Args: section, or"
            " rename it to match the current signature."
        ),
        "fix_example": (
            "Args:\n    name (str): The user's display name.\n"
            "    # Remove entries for parameters no longer in the signature."
        ),
    },
    {
        "name": "griffe-unknown-param",
        "check": "griffe",
        "description": "Griffe reports a parameter not matching the function signature.",
        "category": "required",
        "guidance": (
            "Remove or rename the documented parameter in the Args: section to"
            " match the actual function signature."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "griffe-missing-type",
        "check": "griffe",
        "description": "Griffe reports a missing type annotation in docstring.",
        "category": "recommended",
        "guidance": (
            "Add parenthesized type annotations to parameter entries:"
            " name (type): description."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "griffe-format-warning",
        "check": "griffe",
        "description": "Griffe reports a formatting issue in the docstring.",
        "category": "recommended",
        "guidance": (
            "Fix docstring formatting: ensure proper indentation (4 spaces),"
            " correct section headers, and valid Google-style syntax."
        ),
        "fix_example": "Args:\n    data (dict): The input data to process.",
    },
    {
        "name": "extra-raises-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring documents exceptions not raised in the function body."
        ),
        "category": "recommended",
        "guidance": (
            "This rule is opt-in (check-extra-raises = true) because"
            " documenting propagated exceptions from callees is common"
            " and correct. If the exception is genuinely stale, remove"
            " it from the Raises: section."
        ),
        "fix_example": "Raises:\n    ValueError: If the input is invalid.",
    },
    {
        "name": "extra-yields-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring has a Yields: section but the function does not yield."
        ),
        "category": "recommended",
        "guidance": (
            "Remove the Yields: section or convert the function to a"
            " generator. If refactored from a generator, replace Yields:"
            " with Returns:."
        ),
        "fix_example": "Returns:\n    A list of processed items.",
    },
    {
        "name": "extra-returns-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring has a Returns: section but the function does not return a value."
        ),
        "category": "recommended",
        "guidance": (
            "Remove the Returns: section if the function has no meaningful"
            " return value, or add the missing return statement."
        ),
        "fix_example": ('def save(data: dict) -> None:\n    """Save data to disk."""'),
    },
    {
        "name": "trivial-docstring",
        "check": "enrichment",
        "description": (
            "Docstring summary line restates the symbol name without"
            " adding information."
        ),
        "category": "recommended",
        "guidance": (
            "Replace the summary line with a description that adds"
            " information beyond what the name already communicates,"
            " such as behavior, constraints, or return value."
        ),
        "fix_example": (
            'def get_user():\n    """Fetch the active user from the'
            ' session cache by their ID."""'
        ),
    },
    {
        "name": "missing-return-type",
        "check": "enrichment",
        "description": (
            "Returns section has no type and function has no return annotation."
        ),
        "category": "recommended",
        "guidance": (
            "Add a type to the Returns entry (e.g., 'int: The count.')"
            " or add a -> return annotation to the function signature."
        ),
        "fix_example": "Returns:\n    int: The computed value.",
    },
    {
        "name": "undocumented-init-params",
        "check": "enrichment",
        "description": (
            "Class __init__ takes parameters but neither class nor"
            " __init__ docstring has an Args section."
        ),
        "category": "required",
        "guidance": (
            "Add an Args: section to either the class docstring or"
            " the __init__ docstring listing all constructor parameters"
            " with descriptions."
        ),
        "fix_example": (
            "Args:\n    host (str): The server hostname.\n"
            "    port (int): The server port number."
        ),
    },
]

_RULE_TO_CHECK: dict[str, str] = {r["name"]: r["check"] for r in _RULE_CATALOG}


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
