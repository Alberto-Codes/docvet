# Story 1.7: CLI Wiring for Enrichment Check

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to run `docvet enrichment` from the command line and see findings in `file:line: rule message` format,
so that I can integrate enrichment checking into my development workflow and CI pipelines.

## Acceptance Criteria

1. **Given** a codebase with files containing functions missing `Raises:` sections, **when** `docvet enrichment` is run, **then** findings are printed to stdout in `file:line: rule message` format (one per line) (AC: #1)

2. **Given** a codebase with no enrichment issues, **when** `docvet enrichment` is run, **then** it produces no finding output and exits with code 0 (AC: #2)

3. **Given** the existing `_run_enrichment` stub in `cli.py`, **when** the enrichment check is wired, **then** it reads each discovered file, calls `ast.parse()`, and passes `source`, `tree`, `config.enrichment`, and `str(file_path)` to `check_enrichment` (AC: #3)

4. **Given** a file that fails `ast.parse()` with `SyntaxError`, **when** `docvet enrichment` processes it, **then** the file is skipped with a warning to stderr (not passed to `check_enrichment`) (AC: #4)

5. **Given** `docvet check` is run (all checks), **when** enrichment is among the checks, **then** enrichment findings are included alongside other check outputs (AC: #5)

6. **Given** `docvet enrichment --all` is run on a project, **when** the run completes, **then** all Python files in the project are analyzed (not just git diff files) (AC: #6)

## Tasks / Subtasks

- [ ] Task 1: Replace `_run_enrichment` stub body with real implementation (AC: #1, #2, #3, #4)
  - [ ] 1.1: Add `import ast` to `cli.py` module imports (stdlib section)
  - [ ] 1.2: Add `from docvet.checks.enrichment import check_enrichment` to local imports
  - [ ] 1.3: Replace stub body — iterate files, read source with `file_path.read_text(encoding="utf-8")`, `ast.parse(source)`, call `check_enrichment(source, tree, config.enrichment, str(file_path))`, print each finding
  - [ ] 1.4: Wrap `ast.parse()` in `try/except SyntaxError` — skip file with `typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)`
  - [ ] 1.5: Format findings as `f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"` via `typer.echo()`
  - [ ] 1.6: Update `_run_enrichment` docstring to reflect actual behavior (no longer a stub)

- [ ] Task 2: Update existing CLI tests that reference the stub message (AC: #5)
  - [ ] 2.1: Update `test_enrichment_when_invoked_exits_successfully` — it currently asserts `"enrichment: not yet implemented"` in output. Change to mock `_run_enrichment` or verify exit code 0 without the stub string
  - [ ] 2.2: Update `test_check_when_invoked_runs_all_checks_in_order` — currently checks `output.index("enrichment:")`. After wiring, enrichment produces findings or nothing, not a stub message. Mock `_run_enrichment` in this test to preserve dispatch order assertion
  - [ ] 2.3: Verify all existing CLI tests still pass after changes (no regressions)

- [ ] Task 3: Write new unit tests for `_run_enrichment` behavior (AC: #1, #2, #3, #4)
  - [ ] 3.1: `test_run_enrichment_when_file_has_findings_prints_formatted_output` — mock file read + check_enrichment returning findings, assert stdout contains `file:line: rule message`
  - [ ] 3.2: `test_run_enrichment_when_no_findings_produces_no_output` — mock check_enrichment returning `[]`, assert no stdout
  - [ ] 3.3: `test_run_enrichment_when_syntax_error_skips_file_with_warning` — mock file read returning invalid Python, assert stderr warning, assert check_enrichment NOT called for that file
  - [ ] 3.4: `test_run_enrichment_when_multiple_files_processes_all` — verify all files iterated
  - [ ] 3.5: `test_run_enrichment_passes_config_enrichment_and_str_file_path` — verify correct args to `check_enrichment`

- [ ] Task 4: Run quality gates and verify all pass (AC: all)
  - [ ] 4.1: `uv run ruff check .` — All checks pass
  - [ ] 4.2: `uv run ruff format --check .` — All files formatted
  - [ ] 4.3: `uv run ty check` — All type checks pass
  - [ ] 4.4: `uv run pytest tests/unit/test_cli.py -v` — All CLI tests pass
  - [ ] 4.5: `uv run pytest` — Full suite passes, 0 regressions

## Dev Notes

### Scope

This story replaces the `_run_enrichment` stub in `cli.py` (line 148-155) with a real implementation that:
1. Reads each discovered file
2. Parses the AST (handling SyntaxError gracefully)
3. Calls `check_enrichment` from `docvet.checks.enrichment`
4. Formats and prints findings to stdout

This is an **integration story** — it connects the pure-function enrichment module (built in Stories 1.1-1.6) to the CLI layer. Minimal new logic; mostly wiring.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/cli.py` | MODIFIED — Replace `_run_enrichment` stub body, add imports (`ast`, `check_enrichment`) |
| `tests/unit/test_cli.py` | MODIFIED — Update stub-dependent tests, add new `_run_enrichment` behavior tests |

No new files. No fixture files needed.

### Implementation Pattern

**`_run_enrichment` after this story:**
```python
def _run_enrichment(files: list[Path], config: DocvetConfig) -> None:
    """Run the enrichment check on discovered files.

    Reads each file, parses its AST, and runs all enabled enrichment
    rules. Findings are printed to stdout in ``file:line: rule message``
    format. Files that fail to parse are skipped with a warning.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
    """
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            typer.echo(
                f"warning: {file_path}: failed to parse, skipping", err=True
            )
            continue
        findings = check_enrichment(source, tree, config.enrichment, str(file_path))
        for finding in findings:
            typer.echo(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
            )
```

### Architecture Constraints

**Data flow (Architecture doc, Data Flow section):**
```
CLI (_run_enrichment)
  → reads file → source: str
  → ast.parse(source) → tree: ast.Module
  → except SyntaxError: skip with warning to stderr
  → check_enrichment(source, tree, config.enrichment, str(file_path))
  → format findings as file:line: rule message → stdout
```

**Boundary rules:**
- CLI owns I/O — enrichment is pure, no side effects (FR40)
- CLI owns `ast.parse()` — enrichment assumes valid AST
- `config.enrichment` is `EnrichmentConfig` (frozen dataclass from `config.py`)
- `str(file_path)` passed to `check_enrichment` — the function takes `str`, not `Path`
- SyntaxError warnings go to stderr (`err=True`), findings go to stdout
- No cross-check imports — enrichment module depends only on `checks.Finding` and `ast_utils`

**Output format (PRD, Scripting & CI Support):**
- `file:line: rule message` — one finding per line
- Greppable, parseable, familiar to ruff/ty users
- No summary line in this story (that's reporting layer)
- No exit code logic in this story (that's `fail-on`/`warn-on` from top-level config)

**Import contract (Architecture, Module Dependency Boundary):**
```python
# cli.py imports for enrichment wiring:
import ast  # stdlib — add to existing stdlib import block
from docvet.checks.enrichment import check_enrichment  # local — add to existing local imports
```
- Do NOT import `Finding` — it's accessed via `finding.file`, `finding.line` etc. from the return of `check_enrichment`
- Do NOT import from `docvet.checks` (the `Finding` type) unless needed for type annotation

### Existing CLI Test Impacts

**Tests that need updating:**

1. **`test_enrichment_when_invoked_exits_successfully` (line 115):**
   Currently asserts `"enrichment: not yet implemented" in result.output`. After wiring, the stub message is gone. Options:
   - Mock `check_enrichment` to return `[]` and verify clean exit
   - Or mock `_run_enrichment` itself (but that defeats the purpose)
   - Best approach: mock `Path.read_text` and `ast.parse` OR just mock `check_enrichment` at `docvet.cli.check_enrichment` to return `[]`, verify exit code 0

2. **`test_check_when_invoked_runs_all_checks_in_order` (line 107):**
   Currently checks `output.index("enrichment:")` ordering. After wiring, enrichment doesn't output "enrichment:". Options:
   - Mock all `_run_*` functions to print their names (keeps existing test pattern)
   - This test already passes because the other stubs still print their names. But enrichment won't. Simplest fix: mock `_run_enrichment` in this specific test

3. **`test_check_when_invoked_passes_config_to_run_stubs` (line 380):**
   Already mocks `_run_enrichment` — still works, no change needed

4. **`test_check_when_discovery_returns_empty_does_not_call_stubs` (line 396):**
   Already mocks `_run_enrichment` — still works, no change needed

### Testing Strategy

**Unit test approach for `_run_enrichment`:**
- Mock at the `docvet.cli.check_enrichment` level (patch where used, not where defined)
- Mock `Path.read_text` for controlled source input
- Use `mocker.patch("docvet.cli.ast.parse")` for AST parse control
- Use `capsys` or check `result.output` from `CliRunner` for output assertions

**Key mocking patterns from existing test file:**
- `mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])`
- `mocker.patch("docvet.cli._run_enrichment")`
- `mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())`
- Module-level `autouse=True` fixture handles `load_config` and `discover_files` mocks

**The autouse fixture** (test_cli.py, top of file) mocks `load_config` and `discover_files` globally. Individual tests override when needed. New `_run_enrichment` tests may need to NOT mock `_run_enrichment` itself (let it run) while mocking its dependencies (`check_enrichment`, file I/O).

### What NOT to Do

- Do NOT add exit code logic (`fail-on`/`warn-on`) — that's the reporting layer, not this story
- Do NOT add summary line output (`N findings (X required, Y recommended)`) — reporting layer
- Do NOT change the `_run_enrichment` function signature — it stays `(files: list[Path], config: DocvetConfig) -> None`
- Do NOT add `--format` handling for enrichment output — MVP is terminal text only
- Do NOT catch exceptions other than `SyntaxError` in the file processing loop — correctness through design (Decision 5)
- Do NOT add `Finding` import to `cli.py` unless needed for type annotation — access attributes via dot notation on the returned objects
- Do NOT modify `enrichment.py` or any other check module — this story only touches `cli.py` and its tests
- Do NOT add verbose-conditional output for findings — findings always print. Verbose mode is for discovery count, not findings
- Do NOT use `print()` — use `typer.echo()` for all output (project convention)

### Previous Story Intelligence

**From Story 1.6 (Missing Warns and Other Parameters):**
- 276 total tests across the project, 74 in enrichment specifically
- All quality gates passing: ruff check, ruff format, ty check, pytest
- `check_enrichment(source, tree, config, file_path)` API is stable — takes `str` source, `ast.Module` tree, `EnrichmentConfig` config, `str` file_path
- Returns `list[Finding]` — never `None`
- `Finding` has fields: `file`, `line`, `symbol`, `rule`, `message`, `category`
- `get_documented_symbols(tree)` takes only `tree` (not `source, tree`)

**From Story 1.4 (Missing Raises and Orchestrator):**
- `check_enrichment` orchestrator is the public API — only import this, not individual `_check_*` functions
- Pure function: no I/O, no side effects, deterministic

**Key learning from all stories:** The enrichment module is completely self-contained and tested. This story's job is purely to wire it into the CLI. Keep the boundary clean.

### File Structure Requirements

**`cli.py` import section after this story:**
```python
"""Typer CLI application for docvet."""

from __future__ import annotations

import ast                              # ← NEW
import enum
from pathlib import Path
from typing import Annotated

import typer

from docvet.checks.enrichment import check_enrichment  # ← NEW
from docvet.config import DocvetConfig, load_config
from docvet.discovery import DiscoveryMode, discover_files
```

Note: `import ast` goes in the stdlib section (after `from __future__`, before `from pathlib`). `from docvet.checks.enrichment import check_enrichment` goes in the local imports section (after `import typer`, before or after existing local imports — ruff isort will sort).

### FRs Covered

- FR42: A developer can run the enrichment check standalone via `docvet enrichment` or as part of all checks via `docvet check`
- NFR18: The enrichment check integrates with the existing CLI dispatch pattern (`_run_enrichment` stub) without requiring changes to CLI argument parsing or global option handling

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Data Flow] — CLI → check_enrichment data flow diagram
- [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points] — CLI ↔ enrichment integration contract
- [Source: _bmad-output/planning-artifacts/architecture.md#Module Dependency Boundary] — Import paths
- [Source: _bmad-output/planning-artifacts/prd.md#Scripting & CI Support] — Output format `file:line: rule message`
- [Source: _bmad-output/planning-artifacts/prd.md#Integration Contract] — `check_enrichment` public API signature
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7] — BDD acceptance criteria
- [Source: src/docvet/cli.py:148-155] — Existing `_run_enrichment` stub (replacement target)
- [Source: src/docvet/cli.py:245-267] — `check` command dispatching all runners including `_run_enrichment`
- [Source: src/docvet/cli.py:270-289] — `enrichment` command dispatching `_run_enrichment`
- [Source: src/docvet/checks/enrichment.py:464-522] — `check_enrichment` public orchestrator
- [Source: tests/unit/test_cli.py:107-113] — `test_check_when_invoked_runs_all_checks_in_order` (needs update)
- [Source: tests/unit/test_cli.py:115-118] — `test_enrichment_when_invoked_exits_successfully` (needs update)
- [Source: tests/unit/test_cli.py:380-393] — `test_check_when_invoked_passes_config_to_run_stubs` (unaffected — already mocks `_run_enrichment`)
- [Source: _bmad-output/implementation-artifacts/1-6-missing-warns-and-other-parameters-detection.md] — Previous story patterns and learnings
- [Source: _bmad-output/project-context.md#Framework Rules] — Typer CLI conventions, stub pattern, `_run_*` migration paths

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
