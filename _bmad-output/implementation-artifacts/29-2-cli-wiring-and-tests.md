# Story 29.2: CLI Wiring and Tests

Status: done
Branch: `feat/mcp-29-2-cli-wiring-and-tests`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/266

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer setting up docvet's MCP server**,
I want a `docvet mcp` subcommand that starts the MCP server,
so that I can configure MCP clients to connect to docvet easily.

## Acceptance Criteria

1. **Given** a user runs `docvet mcp`, **When** the `mcp` optional dependency is installed, **Then** the MCP server starts on stdio and listens for requests.

2. **Given** a user runs `docvet mcp` without the `mcp` package installed, **When** the command starts, **Then** a clear error message is shown: "MCP server requires the mcp extra: pip install docvet[mcp]" **And** the exit code is 1.

3. **Given** an MCP client connects and calls `docvet_check` on a directory, **When** the check completes, **Then** the response contains findings with the same `rule`, `symbol`, and `message` values as the corresponding `docvet check --format json` output **And** the `summary.total` and `summary.by_check` values match.

4. **Given** an MCP client connects and calls `docvet_rules`, **When** the request completes, **Then** the response lists all 20 rules (including `missing-docstring` from Epic 28).

5. **Given** the MCP server is running, **When** the client disconnects, **Then** the server shuts down cleanly without errors.

## Tasks / Subtasks

- [x] Task 1: Add `mcp` CLI subcommand to `cli.py` (AC: 1, 2)
  - [x] 1.1 Add `@app.command()` function `mcp()` following the exact `lsp()` pattern at `cli.py:1246`
  - [x] 1.2 Lazy import: `from docvet.mcp import start_server` inside try block
  - [x] 1.3 Catch `ModuleNotFoundError`, print error to stderr via `typer.echo(..., err=True)`, raise `typer.Exit(code=1)`
  - [x] 1.4 Call `start_server()` on success
- [x] Task 2: Write CLI unit tests (AC: 1, 2)
  - [x] 2.1 Test `docvet mcp --help` shows expected description — add to existing help test pattern in `test_cli.py` alongside enrichment, freshness, etc.
  - [x] 2.2 Test missing dependency: use `unittest.mock.patch.dict(sys.modules, {'docvet.mcp': None})` to force `ModuleNotFoundError` from the lazy import, verify stderr message and exit code 1 (ref: `test_mcp.py:TestImportErrorGuard` subprocess pattern)
  - [x] 2.3 Test successful invocation: mock `start_server` via `unittest.mock.patch("docvet.mcp.start_server")`, verify it is called once via `CliRunner.invoke(app, ["mcp"])`
  - [x] 2.4 Structural test: assert `"mcp"` appears in registered typer app commands (no mock needed, catches deletion/typo)
- [x] Task 3: Write MCP integration tests (AC: 3, 4, 5)
  - [x] 3.1 Create `tests/integration/test_mcp.py` with `pytestmark = [pytest.mark.integration, pytest.mark.slow]`
  - [x] 3.2 Test `docvet_check` end-to-end: spawn MCP server via `mcp` client SDK (`stdio_client` + `ClientSession`), call `docvet_check` tool on a temp directory with a known undocumented file, verify response contains `findings` and `summary` keys. Use `asyncio.wait_for(..., timeout=30.0)` inside the async helper.
  - [x] 3.3 Test `docvet_rules` end-to-end: call `docvet_rules` tool, verify all 20 rules returned with `name`, `check`, `description`, `category` fields
  - [x] 3.4 Test response parity: compare MCP `docvet_check` result against `docvet check --all --format json` on the same input. Compare findings by `(rule, symbol, message)` tuples — ignore `file` (path format differs: MCP absolute vs CLI relative). Compare `summary.total` and `summary.by_check`. Exclude freshness from CLI comparison (`--fail-on` without freshness).
  - [x] 3.5 Test clean shutdown: close client session, verify server process terminates without error
  - [x] 3.6 Test `docvet_check` on a well-documented file: verify zero findings
  - [x] 3.7 Test `docvet_check` with explicit `checks: ["presence"]` parameter: verify only presence findings returned and `presence_coverage` object present
- [x] Task 4: Run quality gates (AC: all)
  - [x] 4.1 Run `uv run ruff check .` and `uv run ruff format --check .`
  - [x] 4.2 Run `uv run pytest` — all tests pass, no regressions
  - [x] 4.3 Run `uv run docvet check --all` — zero findings
  - [x] 4.4 Run `uv run interrogate -v` — coverage >= 95%

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | 2.3 — start_server called on successful import; 2.4 — structural command registration | PASS |
| 2 | 2.2 — missing dep error message + exit code 1 | PASS |
| 3 | 3.2, 3.4 — e2e docvet_check + parity with CLI JSON; 3.7 — explicit checks param | PASS |
| 4 | 3.3 — e2e docvet_rules returns all 20 rules | PASS |
| 5 | 3.5 — clean shutdown on client disconnect | PASS |

## Dev Notes

### Architecture: Follow the LSP CLI Pattern Exactly

The `mcp` subcommand follows the identical pattern as `lsp` at `cli.py:1246-1265`:

```python
@app.command()
def mcp() -> None:
    """Start the MCP server for agentic integration.

    Launches a Model Context Protocol server on stdio that exposes
    docstring quality checks as MCP tools for AI agents.
    Requires the ``[mcp]`` extra (``pip install docvet[mcp]``).

    Raises:
        typer.Exit: If required MCP dependencies are not installed.
    """
    try:
        from docvet.mcp import start_server
    except ModuleNotFoundError:
        typer.echo(
            "MCP server requires the mcp extra: pip install docvet[mcp]",
            err=True,
        )
        raise typer.Exit(code=1)
    start_server()
```

Key constraints:
- Catch `ModuleNotFoundError` (not `ImportError`) — matches `lsp()` pattern
- Error message goes to stderr via `typer.echo(..., err=True)`
- No arguments — server reads config per-request from working directory
- `start_server()` blocks until client disconnects (same as LSP)
- **Lazy import is mandatory**: The `mcp()` function name shadows the `mcp` package. The import MUST stay inside the function body to avoid namespace collision. Never add `import mcp` or `from mcp import ...` at `cli.py` module level.

### Integration Test Approach: MCP Client SDK

The `mcp` package is already a dev dependency (added in 29.1). Use its client SDK for integration tests:

```python
import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

def test_docvet_check_e2e(tmp_path):
    """End-to-end: spawn MCP server, call docvet_check, verify response."""
    # Create test file with undocumented symbol
    (tmp_path / "bad.py").write_text("def foo():\n    pass\n")

    async def _run():
        server_params = StdioServerParameters(
            command="docvet", args=["mcp"]
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "docvet_check",
                    arguments={"path": str(tmp_path)},
                )
                return result

    result = asyncio.run(_run())
    content = json.loads(result.content[0].text)
    assert "findings" in content
    assert "summary" in content
```

**Verified imports** (confirmed against `mcp>=1.6,<2`):
```python
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
```

`StdioServerParameters` fields: `command`, `args`, `env`, `cwd`, `encoding`, `encoding_error_handler`.
`ClientSession.call_tool(name, arguments, ...)`. `ClientSession.list_tools()`.

**Important considerations:**
- `asyncio.run()` inside sync test functions works — confirmed via probe (no `pytest-asyncio` needed). `anyio` is already a transitive dep of `mcp`.
- Every `_run()` coroutine must use `asyncio.wait_for(..., timeout=30.0)` to prevent stuck MCP servers from hanging CI.
- `stdio_client` spawns the subprocess and handles JSON-RPC framing — do NOT manually craft JSON-RPC messages
- Each test should use its own `tmp_path` with a `pyproject.toml` to ensure config isolation
- Tests need a `pyproject.toml` in `tmp_path` (even empty `[tool.docvet]`) to avoid config walkup finding the project root's config
- Mark all integration tests with both `@pytest.mark.integration` and `@pytest.mark.slow` via module-level `pytestmark`

### Response Parity Verification

AC 3 requires verifying MCP results match CLI JSON output. **Normalization strategy** (party-mode consensus):

1. Create a temp directory with known files (some documented, some not)
2. Run `docvet check --all --format json` via subprocess on that directory (exclude freshness from `--fail-on` to match MCP defaults)
3. Run MCP `docvet_check` on the same directory
4. **Compare by `(rule, symbol, message)` tuples** — ignore `file` field (MCP returns absolute paths, CLI returns relative)
5. **Compare `summary.total` and `summary.by_check` keys** — these must match exactly
6. Do NOT compare `line` numbers (should match but path format differences could introduce edge cases)
7. Note: MCP excludes freshness by default, so CLI comparison must exclude freshness too

### Previous Story Intelligence (29.1)

From story 29.1 code review and implementation:

- **Module structure**: `src/docvet/mcp.py` uses `mcp_server = FastMCP("docvet")` module-level instance, `__all__ = ["start_server"]`
- **`start_server()` blocks**: Calls `mcp_server.run(transport="stdio")` which blocks until disconnect
- **Directory scoping fix**: `is_relative_to(target)` filter was added in code review to ensure only files within the target directory are checked — integration tests should verify this
- **Absolute paths in findings**: MCP returns absolute paths in findings (intentional for agent use) — parity test must account for this
- **`_RULE_TO_CHECK` dict**: O(1) lookup added during review — rule catalog has 20 entries
- **No freshness by default**: `_DEFAULT_MCP_CHECKS = _VALID_CHECK_NAMES - {"freshness"}` — parity test should reflect this
- **Zero-debug implementation**: 29.1 was straightforward, expect 29.2 to be similar

### Git Intelligence

Recent commits:
- `36b3dde feat(mcp): add core MCP server with docvet_check and docvet_rules tools (#261)` — story 29.1
- `aca1eb0 chore(docvet): enforce presence check with 100% threshold (#258)` — Epic 28 cleanup

Files from 29.1 that are relevant:
- `src/docvet/mcp.py` — the MCP server module (read, don't modify)
- `tests/unit/test_mcp.py` — existing unit tests (don't duplicate)
- `pyproject.toml` — `mcp` dependency already added

### Project Structure Notes

- CLI wiring: modify `src/docvet/cli.py` — add `mcp()` function after `lsp()` at line ~1266
- CLI unit tests: add to `tests/unit/test_cli.py` — `mcp --help` test alongside existing subcommand help tests; new `TestMcpSubcommand` class for dependency/invocation tests
- Integration tests: create `tests/integration/test_mcp.py` — new file
- No new directories needed, no new packages, no new dependencies

### References

- [Source: src/docvet/cli.py:1246-1265] — `lsp()` subcommand pattern to replicate
- [Source: src/docvet/mcp.py] — MCP server module with `start_server()` and tool implementations
- [Source: tests/unit/test_cli.py:2506-2553] — `TestPresenceSubcommand` pattern for CLI tests
- [Source: tests/unit/test_mcp.py] — Existing unit tests (45 tests, do NOT duplicate)
- [Source: tests/integration/conftest.py] — `git_repo` fixture pattern
- [Source: _bmad-output/implementation-artifacts/29-1-core-mcp-server-implementation.md] — Previous story learnings
- [Source: _bmad-output/planning-artifacts/epics-presence-mcp.md#Story 29.2] — Epic AC definition

### Documentation Impact

- Pages: docs/site/cli-reference.md
- Nature of update: Add `docvet mcp` subcommand entry to CLI reference page. Also backfills missing `docvet lsp` entry (gap from Epic 24) and updates subcommand count from six to eight. Full MCP documentation (ai-integration page, setup guide) is Story 29.3's scope — this story only documents the CLI subcommand existence.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all 1170 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v src/` — 100% docstring coverage on source

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Parity test initially failed: CLI subprocess picked up system-installed docvet v1.0.0 instead of venv v1.7.0. Fixed by using `sys.executable` parent path to locate the venv's `docvet` console script.
- Structural test initially used `app.registered_commands[].name` which returns `None` for typer commands. Fixed by using `typer.main.get_command(app).list_commands()`.
- ty type checker flagged `result.content[0].text` (union type) and `click_app.commands` (Command vs Group). Fixed with `type: ignore` comments.

### Completion Notes List

- Added `mcp()` CLI subcommand at `cli.py:1268-1287` following the `lsp()` pattern exactly
- Used `start_server as mcp_start_server` alias to avoid shadowing the `mcp` function name
- Updated `cli.py` module docstring to include `mcp` in the subcommand list
- Added 4 CLI unit tests: help text, missing dependency, successful invocation, structural registration
- Added existing help test assertion for `mcp` in `test_app_when_invoked_with_help_shows_all_subcommands`
- Created `tests/integration/test_mcp.py` with 6 end-to-end tests using MCP client SDK
- Integration tests use `_docvet_executable()` helper to find the venv's docvet script
- Updated `docs/site/cli-reference.md` with `docvet lsp` and `docvet mcp` entries

### Change Log

- 2026-03-03: Implemented story 29.2 — added `docvet mcp` CLI subcommand, 4 CLI unit tests, 6 MCP integration tests, updated CLI reference docs
- 2026-03-03: Code review — fixed 4 findings (M1: assertion strength, M2: lsp help test gap, M3: Documentation Impact, L1: parity fixture enrichment). Dropped L2 (async boilerplate) by consensus.

### File List

- `src/docvet/cli.py` — added `mcp()` subcommand function, updated module docstring
- `tests/unit/test_cli.py` — added `test_mcp_help_when_invoked_shows_correct_description`, `TestMcpSubcommand` class (3 tests), updated existing help test
- `tests/integration/test_mcp.py` — NEW: 6 end-to-end MCP integration tests
- `docs/site/cli-reference.md` — added `docvet lsp` and `docvet mcp` subcommand entries

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Code review (adversarial) — 2026-03-03

### Outcome

Approved with fixes applied

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | `test_successful_invocation_calls_start_server` uses `assert_called_once()` instead of `assert_called_once_with()` (dev quality checklist violation) | Fixed: `test_cli.py:2831` |
| M2 | MEDIUM | `test_app_when_invoked_with_help_shows_all_subcommands` missing `lsp` assertion (7/8 subcommands) | Fixed: added `assert "lsp" in output` |
| M3 | MEDIUM | Documentation Impact section doesn't mention `docvet lsp` docs backfill or subcommand count change | Fixed: updated Documentation Impact |
| L1 | LOW | Parity test fixture only exercises presence check (single `def foo(): pass`) — no enrichment findings | Fixed: added `bar()` with `raise ValueError` to exercise enrichment |
| L2 | LOW | Integration test async boilerplate duplicated 6 times | Dropped: test isolation > DRY for subprocess-spawning integration tests |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
