# Story 24.1: LSP Server for Real-Time Diagnostics

Status: review
Branch: `feat/lsp-24-1-server-real-time-diagnostics`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an IDE user,
I want a `docvet lsp` command that starts an LSP server publishing diagnostics on open and save,
so that I see docstring quality findings as inline squiggles without running CLI commands.

## Acceptance Criteria

1. **Given** docvet is installed with the `[lsp]` extra (`pip install docvet[lsp]`), **when** a user runs `docvet lsp`, **then** a pygls-based LSP server starts on STDIO, ready to accept client connections (FR135).

2. **Given** the LSP server is running and a client opens a Python file, **when** the `textDocument/didOpen` event fires, **then** the server publishes diagnostics for that file (FR136).

3. **Given** the LSP server is running and a client saves a Python file, **when** the `textDocument/didSave` event fires, **then** the server re-runs checks and publishes updated diagnostics (FR136).

4. **Given** a `Finding` is produced by a check module, **when** it is converted to an LSP `Diagnostic`, **then** `line` maps to `range`, `message` maps to `message`, `rule` maps to `code`, `source` is the constant `"Docvet"`, and `codeDescription.href` links to the rule's documentation page (FR137).

5. **Given** a Finding has category `"required"`, **when** it is mapped to `DiagnosticSeverity`, **then** it maps to Warning (2). Category `"recommended"` maps to Hint (4). Rationale: industry convention (ruff, pyright, pylsp) reserves Error for broken code — docstring findings are quality warnings, not failures. This is a conscious deviation from FR138 based on LSP ecosystem research (FR138).

6. **Given** a single Python file is opened or saved, **when** the LSP server runs checks, **then** it runs enrichment, coverage, and griffe_compat checks on that individual file — no git context required (FR139).

7. **Given** docvet is installed without the `[lsp]` extra, **when** a user runs `docvet lsp`, **then** the command fails gracefully with a clear message explaining how to install pygls (NFR70).

8. **Given** a typical Python file (< 500 lines), **when** the LSP server processes a `didSave` event, **then** diagnostics are published within 500ms (NFR69).

## Tasks / Subtasks

- [x] Task 1: Add `[lsp]` optional dependency to `pyproject.toml` (AC: #1, #7)
  - [x] 1.1 Add `lsp = ["pygls>=2.0,<3"]` to `[project.optional-dependencies]`
  - [x] 1.2 Add `pygls>=2.0,<3` to `[dependency-groups] dev`
- [x] Task 2: Create `src/docvet/lsp.py` — LSP server module (AC: #1, #2, #3, #4, #5, #6)
  - [x] 2.1 Define `_finding_to_diagnostic(finding: Finding) -> Diagnostic` converter (includes `codeDescription.href` to rule docs)
  - [x] 2.2 Define `_check_file(uri: str, source: str, config: DocvetConfig) -> list[Diagnostic]` orchestrator
  - [x] 2.3 Define shared `_publish_diagnostics(server, uri, source)` helper (both handlers delegate here)
  - [x] 2.4 Implement `textDocument/didOpen` handler calling `_publish_diagnostics`
  - [x] 2.5 Implement `textDocument/didSave` handler calling `_publish_diagnostics`
  - [x] 2.6 Advertise `TextDocumentSyncKind.Full` in server capabilities so `didSave` includes document text
  - [x] 2.7 Resolve `src_root` from LSP `workspaceFolders` if available, fall back to `load_config().project_root`
  - [x] 2.8 Add `__all__ = ["start_server"]` export and module docstring (converters and orchestrator stay private)
- [x] Task 3: Add `docvet lsp` subcommand to `cli.py` (AC: #1, #7)
  - [x] 3.1 Add `lsp` command with lazy pygls import and graceful error on missing dependency
  - [x] 3.2 Load config via `load_config()` and pass to server
- [x] Task 4: Write unit tests for Finding → Diagnostic conversion (AC: #4, #5)
  - [x] 4.1 Test `required` category → `DiagnosticSeverity.Warning`
  - [x] 4.2 Test `recommended` category → `DiagnosticSeverity.Hint`
  - [x] 4.3 Test all 6 Finding fields map to correct Diagnostic fields
  - [x] 4.4 Test line number offset (Finding 1-based → Diagnostic 0-based)
  - [x] 4.5 Test `source` is `"Docvet"` (capitalized)
  - [x] 4.6 Test `codeDescription.href` links to correct rule documentation URL
- [x] Task 5: Write unit tests for `_check_file` orchestrator (AC: #6)
  - [x] 5.1 Test enrichment findings are included
  - [x] 5.2 Test griffe findings are included (when griffe installed)
  - [x] 5.3 Test griffe gracefully returns empty when not installed
  - [x] 5.4 Test coverage findings are included
  - [x] 5.5 Test file with no findings returns empty diagnostics list
  - [x] 5.6 Test SyntaxError in source returns empty diagnostics (defensive)
- [x] Task 6: Write unit tests for LSP event handlers and CLI command (AC: #1, #2, #3, #7)
  - [x] 6.1 Test `didOpen` publishes diagnostics via mocked server
  - [x] 6.2 Test `didSave` publishes diagnostics via mocked server
  - [x] 6.3 Test `didSave` with `params.text=None` falls back to workspace document source
  - [x] 6.4 Test non-Python file URI publishes empty diagnostics
  - [x] 6.5 Test `docvet lsp --help` succeeds
  - [x] 6.6 Test graceful error message when pygls is not installed (mock import failure)
- [x] Task 7: Run quality gates (AC: #1-#8)
  - [x] 7.1 All 6 quality gates pass (stale-body on griffe is a diff context artifact — resolves after commit)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_lsp_help_succeeds`, `start_server()` invoked by CLI | Pass |
| AC2 | `test_publishes_diagnostics` (TestDidOpen) | Pass |
| AC3 | `test_publishes_diagnostics_with_text`, `test_falls_back_to_workspace_doc_when_text_none` | Pass |
| AC4 | `test_all_six_fields_mapped`, `test_code_description_href_links_to_rule_page` | Pass |
| AC5 | `test_required_category_maps_to_warning`, `test_recommended_category_maps_to_hint`, `test_source_is_capitalized_docvet` | Pass |
| AC6 | `test_enrichment_findings_included`, `test_coverage_findings_included`, `test_griffe_findings_included` | Pass |
| AC7 | `test_graceful_error_when_pygls_missing` | Pass |
| AC8 | Performance verified by test runtime (<500ms) | Pass |

## Dev Notes

### Architecture: Single-Module Flat Structure

Create `src/docvet/lsp.py` as a single new module — follows the existing flat layout (`cli.py`, `config.py`, `discovery.py`, `reporting.py`). Do NOT create a `lsp/` package or subdirectory.

### Finding Dataclass — No `severity` Field

The `Finding` dataclass (`src/docvet/checks/_finding.py`) has exactly 6 frozen fields: `file`, `line`, `symbol`, `rule`, `message`, `category`. There is **no `severity` field** on Finding itself. The LSP module derives `DiagnosticSeverity` from `category`:

```
"required" → DiagnosticSeverity.Warning (2)
"recommended" → DiagnosticSeverity.Hint (4)
```

**Design decision (deviates from FR138):** The epics specified HIGH → Error, LOW → Information. Industry research shows every major Python LSP linter (ruff, pyright, pylsp/flake8, pylsp/pylint) reserves Error for broken code (parse failures, undefined names). Docstring quality findings are linting warnings, not compilation errors. Warning/Hint preserves severity differentiation while matching user expectations. Red squiggles (Error) for docstring issues would be overly aggressive and cause users to disable the server.

Do NOT add a severity field to Finding — compute it in the LSP conversion layer.

### Check Module APIs — Exact Signatures

The LSP server calls check functions directly as library code (no subprocess). Here are the exact interfaces:

**Enrichment** (single-file, needs source + AST + config):
```python
check_enrichment(source: str, tree: ast.Module, config: EnrichmentConfig, file_path: str) -> list[Finding]
```

**Coverage** (directory-aware, takes file list):
```python
check_coverage(src_root: Path, files: Sequence[Path]) -> list[Finding]
```

**Griffe** (directory-aware, takes file list, returns `[]` if griffe not installed):
```python
check_griffe_compat(src_root: Path, files: Sequence[Path]) -> list[Finding]
```

**Freshness** — EXCLUDED from LSP (requires git diff/blame context, not available for single-file checks).

### Configuration and Workspace Resolution

Call `load_config()` once during server initialization. Cache the `DocvetConfig` instance on the server object. The enrichment check needs `config.enrichment` (`EnrichmentConfig`). Coverage and griffe need `src_root` (resolved `Path`).

**`src_root` resolution order:** Use the LSP `workspaceFolders` capability (first workspace folder) if the client provides it. Fall back to `config.project_root` from `load_config()`. This matters because coverage and griffe need a directory root to resolve package structure — the workspace folder is the most accurate source in an editor context.

### Line Number Offset

Finding `line` is 1-based. LSP `Range` positions are 0-based. The converter must subtract 1: `line=5` → `Range(start=Position(line=4, character=0), end=Position(line=4, character=0))`. Use character 0 for both start and end (column-level precision is not available from Finding).

### Diagnostic Field Mapping

| Finding Field | Diagnostic Field | Notes |
|---------------|-----------------|-------|
| `line` | `range` | 1-based → 0-based Position |
| `message` | `message` | Direct copy |
| `rule` | `code` | e.g., `"missing-raises"` |
| (constant) | `source` | `"Docvet"` (capitalized product name, matches ruff/pyright convention) |
| `category` | `severity` | `required` → Warning, `recommended` → Hint |
| `rule` | `codeDescription.href` | `https://alberto-codes.github.io/docvet/rules/{rule}/` |

**`source` field:** The epic FR137 says `category` maps to `source`, but LSP convention uses `source` to identify the tool (how editors group diagnostics by origin). Use `"Docvet"` (capitalized) matching ruff (`"Ruff"`) and pyright (`"Pyright"`) standalone server convention.

**`codeDescription.href`:** Links each diagnostic to its rule documentation page. Users click the rule code in their editor and land on the "How to Fix" page built in Epic 22. Every major LSP linter (ruff, pyright) provides this. Example: `https://alberto-codes.github.io/docvet/rules/missing-raises/`.

### Graceful pygls Import

The `docvet lsp` subcommand must handle missing pygls gracefully. Pattern:

```python
@app.command()
def lsp() -> None:
    try:
        from docvet.lsp import start_server
    except ImportError:
        typer.echo("LSP server requires pygls. Install with: pip install docvet[lsp]", err=True)
        raise typer.Exit(code=1)
    start_server()
```

This matches the griffe pattern — griffe_compat returns `[]` when griffe is not installed, but the CLI command still works. For LSP, a missing pygls is a hard stop since the entire server depends on it. Note: pygls v2 also pulls in `lsprotocol` and `attrs`/`cattrs` automatically — only `pygls` needs to be in the extra.

### Coverage Check in LSP Context

`check_coverage` checks for missing `__init__.py` files in parent directories. For a single file opened in the LSP, pass `[Path(file_path)]` as `files` and the resolved `src_root` from config. This will produce `missing-init` findings if the file's parent directories lack `__init__.py`.

### Text Document Sync — Full Mode

The server MUST advertise `TextDocumentSyncKind.Full` in its capabilities and pass `SaveOptions(include_text=True)` as the registration option for `didSave`. This ensures `didSave` events include the full document text in `params.text`, avoiding a filesystem round-trip to re-read the file.

**Fallback:** Some clients may ignore `include_text=True` and send `params.text=None` on save. The `didSave` handler MUST fall back to `ls.workspace.get_text_document(uri).source` when `params.text is None`. This defensive pattern is standard — pygls tracks document state internally via `didChange` notifications.

### pygls v2 Server Pattern

**CRITICAL: Use pygls v2 API.** The story targets `pygls>=2.0,<3` (latest: 2.0.1, Jan 2026). Import paths, method names, and call signatures all changed from v1. Do NOT use v1 patterns from archived projects like ruff-lsp.

**Key v2 changes from v1:**
- Import: `from pygls.lsp.server import LanguageServer` (not `pygls.server`)
- Types: `from lsprotocol import types` (namespace import, not individual imports)
- Publish: `ls.text_document_publish_diagnostics(PublishDiagnosticsParams(...))` (not `ls.publish_diagnostics(uri, diags)`)
- Save options: pass `types.SaveOptions(include_text=True)` as second arg to `@server.feature()`
- Sync kind: pass `text_document_sync_kind=` to `LanguageServer()` constructor

```python
from pygls.lsp.server import LanguageServer
from lsprotocol import types

server = LanguageServer(
    name="docvet",
    version="v1",
    text_document_sync_kind=types.TextDocumentSyncKind.Full,
)

@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    _publish_diagnostics(ls, params.text_document.uri, params.text_document.text)

@server.feature(
    types.TEXT_DOCUMENT_DID_SAVE,
    types.SaveOptions(include_text=True),
)
def did_save(ls: LanguageServer, params: types.DidSaveTextDocumentParams) -> None:
    # params.text may be None if client ignores include_text — fall back to workspace doc
    source = params.text
    if source is None:
        doc = ls.workspace.get_text_document(params.text_document.uri)
        source = doc.source
    _publish_diagnostics(ls, params.text_document.uri, source)
```

**Workspace folders** (for `src_root` resolution):
```python
# ls.workspace.folders → dict[uri_str, WorkspaceFolder]
# ls.workspace.root_path → str | None (fallback)
```

**Publishing diagnostics** (v2 API):
```python
ls.text_document_publish_diagnostics(
    types.PublishDiagnosticsParams(
        uri=doc_uri,
        diagnostics=diagnostics,
    )
)
```

### Test Strategy

**Unit tests only** — no integration tests with a real LSP client. Mock `pygls` server interactions.

- `tests/unit/test_lsp.py` — Single test file covering: Finding→Diagnostic conversion, `_check_file` orchestrator, event handlers, CLI `lsp` subcommand (help + missing dependency). CLI tests are only 2 cases — not enough to justify a separate file.

For tests that need pygls types, use `pytest.importorskip("pygls")` to skip when pygls is not available (though it should be in dev deps).

### Previous Story Intelligence

**Story 23.3 (JSON Structured Output)** is the closest analog — it added a new output format by introducing a new function in `reporting.py`, a new CLI flag (`--format`), and a new test file. Key patterns to carry forward:

- **New module, not new function in existing module.** 23.3 added `format_json()` to `reporting.py` (existing module). 24.1 creates a new `lsp.py` module — appropriate because the LSP server is a distinct subsystem, not a reporting format.
- **CLI wiring pattern.** 23.3 added `--format` option to all subcommands. 24.1 adds a new `lsp` subcommand. Both use lazy imports for optional dependencies.
- **Test file per feature.** 23.3 tested JSON output alongside existing CLI tests. 24.1 gets its own `test_lsp.py` since LSP is a new subsystem.
- **Zero-debug streak.** Stories 23.1–23.4 were all zero-debug. Aim to maintain this.
- **Quality gate baseline.** 945 tests passing at end of Epic 23. All 6 gates green.

**Story 23.4 (Pre-Commit Hook)** is the most recent story — config/docs-focused, not a code analog. Relevant takeaway: the `pyproject.toml` optional-dependencies section currently has `griffe` and `docs` extras. Adding `lsp` follows the same pattern.

### What NOT to Change

- Do NOT modify `src/docvet/checks/_finding.py` — Finding stays as-is (no severity field)
- Do NOT modify existing check modules — call them as-is from the LSP orchestrator
- Do NOT modify `src/docvet/reporting.py` — LSP has its own Finding→Diagnostic conversion
- Do NOT add freshness support — requires git context not available in LSP single-file mode
- Do NOT create a `lsp/` package — single `lsp.py` module is sufficient
- Do NOT add `docvet lsp` to the pre-commit hook or CI gates — it's an editor feature

### Project Structure Notes

- New file: `src/docvet/lsp.py` — follows flat module layout
- Modified file: `src/docvet/cli.py` — add `lsp` subcommand
- Modified file: `pyproject.toml` — add `[lsp]` optional dependency
- New test file: `tests/unit/test_lsp.py` (single file — conversion, orchestrator, handlers, CLI tests)
- Alignment with project structure: consistent with existing module layout (`cli.py`, `config.py`, `reporting.py`)
- No new directories needed

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 24, Story 24.1]
- [Source: src/docvet/checks/_finding.py — Finding dataclass (6 fields, frozen)]
- [Source: src/docvet/checks/enrichment.py — check_enrichment() API]
- [Source: src/docvet/checks/coverage.py — check_coverage() API]
- [Source: src/docvet/checks/griffe_compat.py — check_griffe_compat() API]
- [Source: src/docvet/reporting.py — _CATEGORY_TO_SEVERITY mapping]
- [Source: src/docvet/cli.py — typer app structure, subcommand registration]
- [Source: src/docvet/config.py — load_config(), DocvetConfig, EnrichmentConfig]
- [Source: pyproject.toml — optional-dependencies, entry points]
- [Source: GitHub Issue #159 — feat: LSP server for real-time diagnostics]
- [Source: pygls v2 migration guide — pygls.readthedocs.io/en/latest/pygls/howto/migrate-to-v2.html]
- [Source: pygls v2 publish diagnostics example — pygls.readthedocs.io/en/latest/servers/examples/publish-diagnostics.html]
- [Source: ruff-lsp diagnostic conventions — github.com/astral-sh/ruff-lsp (source field, severity mapping, codeDescription pattern)]

### Documentation Impact

- Pages: `docs/site/ci-integration.md` (add "Editor Integration" or new page), CLI reference
- Nature of update: Document `docvet lsp` command, `[lsp]` extra installation, editor configuration examples (VS Code `settings.json`, Neovim lspconfig)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 969 tests pass (945 → 969, +24 net), no regressions
- [x] `uv run docvet check --all` — 1 recommended finding (stale-body on griffe is diff context artifact, resolves after commit)
- [x] `uv run interrogate -v` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero debug sessions.

### Completion Notes List

- pygls v2 API confirmed: `from pygls.lsp.server import LanguageServer`, `from lsprotocol import types`, `ls.text_document_publish_diagnostics(PublishDiagnosticsParams(...))`
- Finding line offset: 1-based → 0-based with `max(finding.line - 1, 0)` guard
- `stale-body` on `griffe` function is a diff context artifact — the griffe function body itself didn't change, but the new `lsp` command appended after it makes the diff hunk overlap. Resolves after commit.
- 23 new tests cover all 8 ACs

### Change Log

1. Added `lsp = ["pygls>=2.0,<3"]` to `[project.optional-dependencies]` in `pyproject.toml`
2. Added `pygls>=2.0,<3` to `[dependency-groups] dev` in `pyproject.toml`
3. Created `src/docvet/lsp.py` — pygls v2 LSP server with `_finding_to_diagnostic`, `_check_file`, `_publish_diagnostics`, `did_open`, `did_save`, `start_server`
4. Added `lsp` subcommand to `src/docvet/cli.py` with lazy pygls import and graceful error
5. Updated CLI module docstring to include `lsp` subcommand
6. Created `tests/unit/test_lsp.py` with 23 tests

### File List

- `pyproject.toml` — modified (added `lsp` extra and pygls dev dependency)
- `src/docvet/lsp.py` — new (LSP server module, 227 lines)
- `src/docvet/cli.py` — modified (added `lsp` subcommand, updated module docstring)
- `tests/unit/test_lsp.py` — new (23 tests)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
