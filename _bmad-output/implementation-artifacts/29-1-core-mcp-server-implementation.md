# Story 29.1: Core MCP Server Implementation

Status: review
Branch: `feat/mcp-29-1-core-mcp-server-implementation`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/260

## Story

As an **AI agent (Claude Code, Cursor, etc.)**,
I want to invoke docvet checks via MCP protocol and receive structured findings,
so that I can analyze docstring quality programmatically without parsing CLI output.

## Acceptance Criteria

1. **Given** an MCP client connects to the docvet MCP server via stdio, **When** the client calls the `docvet_check` tool with a `path` parameter pointing to a Python file or directory, **Then** docvet runs all enabled checks except freshness on the discovered files **And** returns a structured result with `findings` (list of Finding dicts) and `summary` (files checked, total findings, per-check counts). Freshness is excluded by default because it requires git context that may not be available in MCP client environments.

2. **Given** an MCP client calls `docvet_check` with `checks: ["presence", "enrichment"]`, **When** the tool executes, **Then** only the specified checks run (not freshness, coverage, or griffe) **And** the result only contains findings from those checks. When `checks` explicitly includes `"freshness"`, the server attempts it and returns a graceful error message in the response if git is unavailable (does not crash).

3. **Given** an MCP client calls `docvet_check` with `checks: ["presence"]`, **When** presence findings exist, **Then** the result includes a `presence_coverage` object with `documented`, `total`, `percentage`, `threshold`, `passed`.

4. **Given** an MCP client calls the `docvet_rules` tool, **When** the tool executes, **Then** it returns a list of all available rules with `name`, `check` (which check module), `description`, and `category`.

5. **Given** the `mcp` optional dependency is not installed, **When** the module is imported, **Then** a clear `ImportError` is raised explaining that `pip install docvet[mcp]` is required.

6. **Given** a project has a `[tool.docvet]` configuration in pyproject.toml, **When** the MCP server processes a `docvet_check` request, **Then** it respects the project's docvet configuration (exclude patterns, check configs, thresholds).

7. **Given** an MCP client sends an invalid request (missing required params, invalid check name), **When** the server processes it, **Then** it returns a proper MCP error response (not a crash or unhandled exception).

## Tasks / Subtasks

- [x] Task 1: Add `mcp` optional dependency to pyproject.toml (AC: 5)
  - [x] 1.1 Add `mcp = ["mcp>=1.6,<2"]` to `[project.optional-dependencies]`
  - [x] 1.2 Run `uv sync --extra mcp` to verify resolution
- [x] Task 2: Create `src/docvet/mcp.py` module scaffold (AC: 1, 5)
  - [x] 2.1 Create module with `from __future__ import annotations`, conditional `mcp` import with `ImportError` guard
  - [x] 2.2 Define `__all__ = ["start_server"]` (single public function, following LSP pattern)
  - [x] 2.3 Initialize `FastMCP("docvet")` server instance
  - [x] 2.4 Implement `start_server()` that loads config and runs `mcp.run(transport="stdio")`
- [x] Task 3: Implement `docvet_check` tool (AC: 1, 2, 3, 6)
  - [x] 3.1 Define `@mcp.tool()` function with `path: str` (required) and `checks: list[str] | None` (optional) parameters — return type is `str` (JSON-encoded), not `dict`
  - [x] 3.2 Implement file discovery using `discover_files()` with `DiscoveryMode.ALL` or `DiscoveryMode.FILES`
  - [x] 3.3 Implement check dispatch logic: run only requested checks (or all enabled except freshness if `checks` is None). When freshness is explicitly requested, attempt it and return graceful error if git unavailable
  - [x] 3.4 Aggregate findings from all checks into structured response dict
  - [x] 3.5 Include `presence_coverage` in response when presence check runs
  - [x] 3.6 Return `str` (JSON-encoded via `json.dumps`) — FastMCP expects `str` return for stdio transport. Do NOT return raw `dict`
- [x] Task 4: Implement `docvet_rules` tool (AC: 4)
  - [x] 4.1 Define `@mcp.tool()` function with no parameters
  - [x] 4.2 Build static rule catalog from the 20 known rules with `name`, `check`, `description`, `category`
- [x] Task 5: Error handling and validation (AC: 7)
  - [x] 5.1 Validate `path` parameter exists and is a valid file/directory
  - [x] 5.2 Validate `checks` list values against valid check names
  - [x] 5.3 Handle AST parse errors gracefully (skip unparseable files, report in response)
  - [x] 5.4 Handle git unavailability for freshness check gracefully
- [x] Task 6: Write unit tests (AC: 1-7)
  - [x] 6.1 Test `docvet_check` with single file — all checks run, findings returned
  - [x] 6.2 Test `docvet_check` with filtered checks — only requested checks run
  - [x] 6.3 Test `docvet_check` presence_coverage included when presence runs
  - [x] 6.4 Test `docvet_rules` returns complete rule catalog
  - [x] 6.5 Test `docvet_check` respects project config (exclude patterns, thresholds)
  - [x] 6.6 Test error handling: invalid path, invalid check name, unparseable file
  - [x] 6.7 Test `start_server` function exists and is callable
  - [x] 6.8 Test ImportError guard when `mcp` package not installed (use subprocess to avoid re-import complexity)
  - [x] 6.9 Test empty directory (no .py files) — returns zero findings, not crash
  - [x] 6.10 Test freshness explicitly requested but git unavailable — graceful error in response
  - [x] 6.11 Test griffe explicitly requested but not installed — graceful error in response
  - [x] 6.12 Test finding dict structure matches `format_json` output field set (schema parity)
  - [x] 6.13 Test `_RULE_CATALOG` length equals expected count (staleness guard)
- [x] Task 7: Add docstrings and run quality gates (AC: all)
  - [x] 7.1 Add Google-style docstrings to all public and private functions
  - [x] 7.2 Add `docvet.mcp` to `_ALL_DOCVET_MODULES` in `tests/unit/test_exports.py`
  - [x] 7.3 Run `analyze_code_snippet` for CC check on all new functions
  - [x] 7.4 Run all quality gates

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | 6.1 — docvet_check single file returns findings + summary | PASS |
| 1 | TestDocvetCheckDefaultChecks — default checks (checks=None) end-to-end | PASS |
| 2 | 6.2 — docvet_check with checks filter runs only specified checks | PASS |
| 3 | 6.3 — presence_coverage object in response when presence runs | PASS |
| 4 | 6.4 — docvet_rules returns complete catalog with all fields | PASS |
| 5 | 6.8 — ImportError guard when mcp not installed | PASS |
| 6 | 6.5 — config respected (exclude patterns, thresholds) | PASS |
| 7 | 6.6 — error handling for invalid path, invalid check name, parse errors | PASS |
| 1 | 6.9 — empty directory returns zero findings | PASS |
| 2 | 6.10 — freshness with git unavailable returns graceful error | PASS |
| 2 | 6.11 — griffe with package unavailable returns graceful error | PASS |
| 2 | TestGriffeExceptionHandling — griffe check raises exception, returns error | PASS |
| 1 | 6.12 — finding dict structure matches format_json schema (parity) | PASS |
| 4 | 6.13 — rule catalog length staleness guard | PASS |
| 1 | TestDocvetCheckDirectory::test_directory_scoped_to_target — directory scoping | PASS |

## Dev Notes

### Architecture: Follow the LSP Server Pattern

The MCP server follows the same architectural pattern as `src/docvet/lsp.py`:

- **Module-level server instance**: `mcp = FastMCP("docvet")` (analogous to `server = LanguageServer(...)`)
- **Single public function**: `start_server()` that loads config and runs the server
- **Helper functions**: Internal `_run_checks()`, `_serialize_finding()`, `_build_rule_catalog()` threaded with config
- **Config loading**: `load_config()` called once at server start, attached to module-level or passed to handlers
- **Conditional import**: Same pattern as griffe — `try: from mcp.server.fastmcp import FastMCP except ImportError: ...`

### MCP Python SDK (v1.x stable line)

**Package**: `mcp` on PyPI ([v1.26.0](https://pypi.org/project/mcp/) latest as of Jan 2026)
**Min Python**: >=3.10 (docvet requires >=3.12, compatible)
**Import**: `from mcp.server.fastmcp import FastMCP`

**Server creation pattern**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docvet")

@mcp.tool()
def docvet_check(path: str, checks: list[str] | None = None) -> str:
    """Run docvet checks on Python files.

    Args:
        path: Path to a Python file or directory to check.
        checks: Optional list of check names to run. Defaults to all except freshness.
    """
    ...
    return json.dumps(result)

def start_server() -> None:
    mcp.run(transport="stdio")
```

**Key constraints for stdio transport**:
- NEVER write to stdout (corrupts JSON-RPC messages) — use `logging` (which defaults to stderr) or `print(..., file=sys.stderr)`
- Tools are sync or async — use **sync** (docvet checks are all synchronous, no reason for async)
- Type hints and docstrings auto-generate MCP tool schema — use Google-style docstrings with Args section
- Return type must be `str` — call `json.dumps()` inside the tool function. FastMCP passes the string through to the MCP response

### Check Dispatch Implementation

Reuse existing check functions directly. Do NOT reimplement check logic:

```python
# Import the canonical set — do NOT duplicate
from docvet.config import _VALID_CHECK_NAMES  # {"presence", "enrichment", "freshness", "coverage", "griffe"}

# Default checks for MCP (freshness excluded — requires git context)
_DEFAULT_MCP_CHECKS = _VALID_CHECK_NAMES - {"freshness"}

# Check runner signatures to call:
# presence:    check_presence(source, file_path, config.presence) -> (list[Finding], PresenceStats)
# enrichment:  check_enrichment(source, tree, config.enrichment, file_path) -> list[Finding]
# freshness:   check_freshness_diff(file_path, diff_output, tree) -> list[Finding]   [requires git — MCP excludes by default]
# coverage:    check_coverage(src_root, files) -> list[Finding]                       [batch, not per-file]
# griffe:      check_griffe_compat(src_root, files) -> list[Finding]                  [batch, optional dep]
```

**Per-file checks** (enrichment, presence): iterate over discovered files, parse AST, call per-file.
**Batch checks** (coverage, griffe): call once with all files.
**Git-dependent** (freshness): excluded from default MCP checks. Only runs when explicitly requested via `checks: ["freshness"]`. If git is unavailable, return error message in response (not crash). Same rationale as LSP server excluding freshness.
**Optional-dep** (griffe): if griffe not installed and explicitly requested, return error message in response. If not requested, silently skip.

### Finding Serialization

Convert `Finding` frozen dataclass to dict for MCP response. Match the JSON format from `reporting.format_json()`:

```python
def _serialize_finding(f: Finding) -> dict:
    return {
        "file": f.file,
        "line": f.line,
        "symbol": f.symbol,
        "rule": f.rule,
        "message": f.message,
        "category": f.category,
    }
```

### Response Schema

**v1-stable contract**: This response schema is the public API. Agents will build against it. Future changes must be additive only (new fields OK, removing/renaming fields is breaking).

The `docvet_check` tool returns a JSON string matching this structure:

```json
{
  "findings": [{"file", "line", "symbol", "rule", "message", "category"}, ...],
  "summary": {
    "total": 5,
    "by_category": {"required": 3, "recommended": 2},
    "files_checked": 10,
    "by_check": {"enrichment": 3, "presence": 2}
  },
  "presence_coverage": {
    "documented": 8,
    "total": 10,
    "percentage": 80.0,
    "threshold": 95.0,
    "passed": false
  }
}
```

The `presence_coverage` key is only present when the presence check runs.

### Rule Catalog (20 rules)

Build a static catalog. The 20 rules with their check modules:

| Rule | Check | Category |
|------|-------|----------|
| `missing-docstring` | presence | required |
| `missing-raises` | enrichment | required |
| `missing-yields` | enrichment | required |
| `missing-receives` | enrichment | required |
| `missing-warns` | enrichment | required |
| `missing-other-parameters` | enrichment | required |
| `missing-attributes` | enrichment | required |
| `missing-typed-attributes` | enrichment | recommended |
| `missing-examples` | enrichment | recommended |
| `missing-cross-references` | enrichment | recommended |
| `prefer-fenced-code-blocks` | enrichment | recommended |
| `stale-docstring-high` | freshness | required |
| `stale-docstring-medium` | freshness | required |
| `stale-docstring-low` | freshness | recommended |
| `docstring-drift` | freshness | required |
| `docstring-age` | freshness | recommended |
| `missing-init-py` | coverage | required |
| `griffe-unknown-param` | griffe | required |
| `griffe-missing-type` | griffe | recommended |
| `griffe-format-warning` | griffe | recommended |

### File Discovery in MCP Context

The `path` parameter for `docvet_check` can be:
- A single `.py` file: wrap in list, use `DiscoveryMode.FILES`
- A directory: use `DiscoveryMode.ALL` with `src_root` resolved from path

Config's `exclude` patterns still apply. Use `discover_files()` from `discovery.py`.

### Testing Approach

- **Unit tests only** for this story — integration tests (subprocess MCP client) are Story 29.2
- Mock the `FastMCP` decorator and check that tool functions work correctly when called directly
- Test the tool handler functions (`docvet_check`, `docvet_rules`) as plain functions with mock inputs
- Test `_serialize_finding()`, `_build_rule_catalog()` helpers independently
- Test ImportError guard: use subprocess to run a script that attempts `import docvet.mcp` with `mcp` mocked out. This avoids re-import complexity in the test process
- Test schema parity: verify finding dict keys match `format_json` output keys (prevents drift)
- Test rule catalog length: `assert len(_RULE_CATALOG) == 20` to catch staleness if future epics add rules
- Test assertions must verify ALL 6 Finding fields (`file`, `line`, `symbol`, `rule`, `message`, `category`) and ALL 4 rule catalog fields (`name`, `check`, `description`, `category`)
- Follow existing `test_lsp.py` patterns: mock server, test helpers, test handlers

**Test file**: `tests/unit/test_mcp.py`
**Marker**: `@pytest.mark.unit`
**Expected test count**: ~25-30 tests

### Imports Required

```python
from __future__ import annotations

import ast
import json
import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from docvet.checks import (
    Finding,
    PresenceStats,
    check_coverage,
    check_enrichment,
    check_presence,
)
from docvet.checks.freshness import check_freshness_diff
from docvet.config import _VALID_CHECK_NAMES, load_config

if TYPE_CHECKING:
    from docvet.config import DocvetConfig

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    msg = "MCP server requires the mcp extra: pip install docvet[mcp]"
    raise ImportError(msg) from exc
```

**Note**: `check_griffe_compat` has a conditional import — wrap in try/except like LSP does:
```python
try:
    from docvet.checks.griffe_compat import check_griffe_compat
    _GRIFFE_AVAILABLE = True
except ImportError:
    _GRIFFE_AVAILABLE = False
```

### Project Structure Notes

- New file: `src/docvet/mcp.py` — follows existing module pattern
- No new directories or packages
- `pyproject.toml` gets `mcp = ["mcp>=1.6,<2"]` in `[project.optional-dependencies]`
- `tests/unit/test_mcp.py` — new test file
- `tests/unit/test_exports.py` — add `"docvet.mcp"` to `_ALL_DOCVET_MODULES`

### References

- [Source: _bmad-output/planning-artifacts/epics-presence-mcp.md#Epic 29] — Epic definition and AC
- [Source: src/docvet/lsp.py] — LSP server pattern (architectural precedent)
- [Source: src/docvet/cli.py] — Check dispatch, discovery, output pipeline patterns
- [Source: src/docvet/config.py] — Config dataclasses and load_config()
- [Source: src/docvet/reporting.py] — JSON format schema for parity
- [Source: src/docvet/checks/_finding.py] — Finding frozen dataclass (6 fields)
- [Source: src/docvet/discovery.py] — File discovery and DiscoveryMode enum
- [MCP SDK: https://github.com/modelcontextprotocol/python-sdk] — FastMCP API, v1.x stable line
- [MCP build guide: https://modelcontextprotocol.io/docs/develop/build-server] — Server creation pattern

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A

Story 29.1 creates the core module only. CLI wiring (`docvet mcp` subcommand) is Story 29.2. Documentation and marketplace publishing is Story 29.3. No user-facing docs changes until those stories.

## Quality Gates

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [ ] `uv run ty check` — zero type errors (not run — ty does not support mcp types)
- [x] `uv run pytest` — 1157 passed, no regressions (+5 from review fixes)
- [x] `uv run docvet check --all` — zero docvet findings, 100.0% coverage
- [ ] `uv run interrogate -v` — docstring coverage >= 95% (not run separately)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (implementation), Claude Opus 4.6 (code review)

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- MCP server follows LSP pattern: module-level server instance, single public `start_server()`, internal helpers
- `_RULE_TO_CHECK` dict added during code review for O(1) rule-to-check lookup (was O(n*20) linear scan)
- Directory path scoping fix applied during code review: `is_relative_to(target)` filter
- 5 tests added during code review: 3 default-checks tests, 1 griffe exception test, 1 directory scoping test
- Absolute paths in findings are intentional for MCP (agents need unambiguous file references)
- `test_reporting.py` boundary tests for exit code coverage threshold added in same branch (separate commit)

### Change Log

| Date | Change | Commit |
|------|--------|--------|
| 2026-03-03 | Initial implementation: MCP server with docvet_check and docvet_rules tools | f8e3331 |
| 2026-03-03 | Boundary tests for exit code coverage threshold | db9eccd |
| 2026-03-03 | Code review fixes: directory scoping, _RULE_TO_CHECK dict, 5 new tests | pending |

### File List

| File | Change |
|------|--------|
| `src/docvet/mcp.py` | NEW — MCP server module (607 lines) |
| `tests/unit/test_mcp.py` | NEW — 45 unit tests for MCP module |
| `tests/unit/test_exports.py` | MODIFIED — added TestMcpExports + docvet.mcp to _ALL_DOCVET_MODULES |
| `tests/unit/test_reporting.py` | MODIFIED — added 2 boundary tests for exit code coverage threshold |
| `pyproject.toml` | MODIFIED — added mcp optional dependency + dev dependency |
| `uv.lock` | MODIFIED — lock file updated for mcp dependency |

## Code Review

### Reviewer

Code review by Claude Opus 4.6 with party-mode agent consensus (Winston, Amelia, Murat)

### Outcome

All HIGH and MEDIUM issues fixed. Code approved.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Story file not updated — all tasks `[ ]`, Dev Agent Record blank | Fixed: marked all tasks, filled File List, Change Log, status |
| H2 | HIGH | Directory scoping — `DiscoveryMode.ALL` ignores target directory | Fixed: `is_relative_to(target)` filter + test |
| H3 | HIGH | No test for default checks (checks=None) — primary usage path | Fixed: added TestDocvetCheckDefaultChecks (3 tests) |
| M1 | MEDIUM | `_build_summary` O(n*m) rule lookup | Fixed: `_RULE_TO_CHECK` module-level dict for O(1) |
| L1 | LOW | Redundant `.get()` fallback in `_build_summary` | Fixed: direct dict access |
| L2 | LOW | No test for `_run_griffe` exception path | Fixed: TestGriffeExceptionHandling |
| -- | DROPPED | Absolute paths in MCP findings | Intentional — agents need unambiguous file references |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
