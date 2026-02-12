# Story 7.2: CLI Wiring for Griffe Compatibility Check

Status: done

## Story

As a developer,
I want to run `docvet griffe` from the command line and see rendering compatibility findings in the standard output format,
So that I can integrate griffe checking into my development workflow and CI pipelines.

## Acceptance Criteria

1. **Given** a codebase with docstrings that produce griffe parser warnings, **When** `docvet griffe` is run, **Then** findings are printed to terminal in `file:line: rule message` format (one per line).

2. **Given** a codebase with well-documented code (no griffe warnings), **When** `docvet griffe` is run, **Then** it produces no output and exits with code 0.

3. **Given** the existing `_run_griffe` stub in `cli.py`, **When** the griffe check is wired, **Then** it resolves `src_root` from `config.project_root / config.src_root` (same pattern as `_run_coverage`) and passes `src_root` and discovered files to `check_griffe_compat`.

4. **Given** griffe is not installed, **When** `docvet griffe` is run, **Then** the CLI detects griffe unavailability via `importlib.util.find_spec("griffe")` and skips the check silently (exit 0, no error).

5. **Given** griffe is not installed and verbose mode is enabled, **When** `docvet griffe` is run, **Then** the CLI emits a note: `griffe: skipped (griffe not installed)` (FR97).

6. **Given** griffe is not installed and griffe is in the `fail-on` list, **When** `docvet check` is run, **Then** the CLI emits a stderr warning that the griffe check was skipped due to missing dependency (FR97).

7. **Given** `docvet check` is run (all checks), **When** griffe is installed and in the enabled checks, **Then** griffe findings are included alongside findings from enrichment, freshness, and coverage.

8. **Given** `docvet griffe --all` is run, **When** the run completes, **Then** all Python files in the project are analyzed (discovery passes full file list to `check_griffe_compat`).

9. **Given** `docvet griffe --staged` is run, **When** the run completes, **Then** only staged files are passed to `check_griffe_compat` (griffe still loads the full package but findings are filtered to staged files).

10. **Given** `src_root` cannot be resolved (e.g., configured path does not exist), **When** `docvet griffe` is run, **Then** the CLI handles the error gracefully (same error handling as `_run_coverage`).

## Tasks / Subtasks

- [x] Task 1: Replace `_run_griffe` stub with real implementation (AC: #1, #2, #3, #4, #5, #6, #10)
  - [x] 1.1 Add `import importlib.util` to `cli.py` imports
  - [x] 1.2 Add `from docvet.checks.griffe_compat import check_griffe_compat` to `cli.py` imports
  - [x] 1.3 Add `verbose: bool = False` keyword parameter to `_run_griffe` signature
  - [x] 1.4 Implement griffe availability check via `importlib.util.find_spec("griffe")`
  - [x] 1.5 Implement verbose-mode skip message: `griffe: skipped (griffe not installed)` on stderr
  - [x] 1.6 Implement fail-on stderr warning when griffe is in `config.fail_on` but not installed
  - [x] 1.7 Implement `src_root` resolution: `config.project_root / config.src_root`
  - [x] 1.8 Add `src_root.is_dir()` guard — return silently if path doesn't exist
  - [x] 1.9 Call `check_griffe_compat(src_root, files)` and print findings in `file:line: rule message` format
  - [x] 1.10 Update `_run_griffe` docstring to reflect real implementation

- [x] Task 2: Update callers to pass `verbose` flag (AC: #5, #7)
  - [x] 2.1 Update `check()` subcommand: pass `verbose=ctx.obj.get("verbose", False)` to `_run_griffe`
  - [x] 2.2 Update `griffe()` subcommand: pass `verbose=ctx.obj.get("verbose", False)` to `_run_griffe`

- [x] Task 3: Write unit tests for `_run_griffe` behavior (AC: #1, #2, #3, #4, #5, #6, #10)
  - [x] 3.1 Test: findings printed in `file:line: rule message` format (AC #1)
  - [x] 3.2 Test: no findings produces no output (AC #2)
  - [x] 3.3 Test: passes correct `src_root` from config (AC #3)
  - [x] 3.4 Test: passes discovered files to `check_griffe_compat` (AC #3)
  - [x] 3.5 Test: griffe not installed skips silently (AC #4)
  - [x] 3.6 Test: griffe not installed + verbose emits skip note (AC #5)
  - [x] 3.7 Test: griffe not installed + fail-on emits stderr warning (AC #6)
  - [x] 3.8 Test: `src_root` doesn't exist returns silently (AC #10)
  - [x] 3.9 Test: `_run_griffe` with default config uses `project_root/.` as `src_root` (AC #3)

- [x] Task 4: Update existing CLI tests and add integration tests (AC: #7, #8, #9)
  - [x] 4.1 Update `test_griffe_when_invoked_exits_successfully` — remove "not yet implemented" assertion
  - [x] 4.2 Update `test_check_when_invoked_runs_all_checks_in_order` — verify griffe runs after coverage (already present)
  - [x] 4.3 Test: `docvet check` includes griffe findings in output (AC #7)
  - [x] 4.4 Test: `check` passes verbose flag to `_run_griffe` (AC #7)
  - [x] 4.5 Test: discovery modes work with griffe subcommand (AC #8, #9 — already covered by existing tests)

- [x] Task 5: Fill AC-to-Test Mapping table and verify completeness
  - [x] 5.1 Map every AC to at least one test function name
  - [x] 5.2 Run full test suite (`uv run pytest`) and verify all pass
  - [x] 5.3 Run lint (`uv run ruff check .`) and format check (`uv run ruff format --check .`)

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_run_griffe_when_file_has_findings_prints_formatted_output` | PASS |
| AC2 | `test_run_griffe_when_no_findings_produces_no_output` | PASS |
| AC3 | `test_run_griffe_passes_correct_src_root_path`, `test_run_griffe_with_default_config_uses_project_root_dot`, `test_run_griffe_passes_discovered_files` | PASS |
| AC4 | `test_run_griffe_when_griffe_not_installed_skips_silently` | PASS |
| AC5 | `test_run_griffe_when_griffe_not_installed_and_verbose_emits_note` | PASS |
| AC6 | `test_run_griffe_when_griffe_not_installed_and_fail_on_emits_warning` | PASS |
| AC7 | `test_check_command_includes_griffe_findings`, `test_check_passes_verbose_to_run_griffe`, `test_check_when_invoked_runs_all_checks_in_order` | PASS |
| AC8 | `test_griffe_when_invoked_with_all_calls_discover_with_all_mode` | PASS |
| AC9 | `test_griffe_when_invoked_with_staged_calls_discover_with_staged_mode` | PASS |
| AC10 | `test_run_griffe_when_src_root_not_exists_returns_silently` | PASS |

## Dev Notes

### Architecture Decisions

**`_run_griffe` implementation follows `_run_coverage` pattern:**
```python
def _run_griffe(files: list[Path], config: DocvetConfig, *, verbose: bool = False) -> None:
    if importlib.util.find_spec("griffe") is None:
        if "griffe" in config.fail_on:
            typer.echo("warning: griffe check skipped (griffe not installed)", err=True)
        elif verbose:
            typer.echo("griffe: skipped (griffe not installed)", err=True)
        return
    src_root = config.project_root / config.src_root
    if not src_root.is_dir():
        return
    findings = check_griffe_compat(src_root, files)
    for finding in findings:
        typer.echo(f"{finding.file}:{finding.line}: {finding.rule} {finding.message}")
```

**Key design choices:**
1. **Two-layer griffe availability detection:** The `check_griffe_compat` function already returns `[]` when griffe is not installed (FR90). The CLI adds a second layer at `_run_griffe` using `importlib.util.find_spec("griffe")` for verbose messaging and fail-on warnings (FR97). This avoids importing griffe_compat.py unnecessarily when griffe isn't installed.
2. **`verbose` keyword parameter added to `_run_griffe` only** — other `_run_*` functions don't need it because they have no optional-dependency messaging. The `verbose` flag comes from `ctx.obj["verbose"]` in the caller.
3. **`fail-on` priority over verbose:** When griffe is in `fail_on` AND verbose is enabled, only the fail-on warning is emitted (not both). The `elif` structure ensures one message.
4. **`src_root.is_dir()` guard:** Prevents `FileNotFoundError` from `check_griffe_compat`'s `src_root.iterdir()`. Returns silently — same graceful behavior as coverage when files are outside src_root.
5. **`importlib.util.find_spec` (not try/import):** Avoids side effects of importing griffe. `find_spec` only checks if the package is importable without actually loading it.

### Key Constraints

- **Zero config dependency** — no `GriffeConfig` dataclass. `_run_griffe` reads `config.fail_on` for the warning check but doesn't pass config to `check_griffe_compat`.
- **Import `check_griffe_compat` at module level** — the import itself is safe even when griffe isn't installed (the module uses `try/except ImportError` internally).
- **Autouse fixture mocks `_run_griffe`** — existing CLI tests use `mocker.patch("docvet.cli._run_griffe")` in the autouse fixture. Tests that verify `_run_griffe` behavior must use `side_effect=_run_griffe` to unwrap the mock, then mock `check_griffe_compat` and `importlib.util.find_spec` as needed.
- **`CliRunner` doesn't support `mix_stderr`** — stderr output may appear in `result.output` rather than `result.stderr`. Use combined `result.output + getattr(result, "stderr", "")` for assertions on stderr messages (same pattern used by freshness tests).

### Test Strategy

**Existing tests that need updating:**
- `test_griffe_when_invoked_exits_successfully` (line 157-160) — remove `"griffe: not yet implemented"` assertion. Replace with exit code 0 + empty output (griffe installed but no findings from mocked `check_griffe_compat` returning `[]`).

**New tests (follow patterns from `_run_coverage` tests at lines 916-1001):**

| Test | Mock Setup | Assertion |
|------|-----------|-----------|
| `test_run_griffe_when_file_has_findings_prints_formatted_output` | `check_griffe_compat → [Finding(...)]`, `find_spec → MagicMock()` | Output contains `file:line: rule message` |
| `test_run_griffe_when_no_findings_produces_no_output` | `check_griffe_compat → []`, `find_spec → MagicMock()` | `result.output == ""` |
| `test_run_griffe_passes_correct_src_root_path` | `check_griffe_compat → []`, `find_spec → MagicMock()`, custom config | `check_griffe_compat` called with `Path("/project/src")` |
| `test_run_griffe_with_default_config_uses_project_root_dot` | `check_griffe_compat → []`, `find_spec → MagicMock()` | Called with `Path("/project/.")` |
| `test_run_griffe_passes_discovered_files` | `check_griffe_compat → []`, `find_spec → MagicMock()` | Called with `[Path("/a.py"), ...]` |
| `test_run_griffe_when_griffe_not_installed_skips_silently` | `find_spec → None` | Exit code 0, empty output, `check_griffe_compat` NOT called |
| `test_run_griffe_when_griffe_not_installed_and_verbose_emits_note` | `find_spec → None`, verbose mode | Output contains `griffe: skipped (griffe not installed)` |
| `test_run_griffe_when_griffe_not_installed_and_fail_on_emits_warning` | `find_spec → None`, `fail_on=["griffe"]` | Output contains `warning: griffe check skipped` |
| `test_run_griffe_when_src_root_not_exists_returns_silently` | `find_spec → MagicMock()`, non-existent src_root | Exit code 0, `check_griffe_compat` NOT called |
| `test_check_command_includes_griffe_findings` | `_run_griffe` side_effect with real impl, findings | Output contains griffe findings |
| `test_check_passes_verbose_to_run_griffe` | Mock `_run_griffe` | `_run_griffe.assert_called_once_with(ANY, ANY, verbose=True)` |

**Mock patterns:**
- `mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())` — griffe installed
- `mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)` — griffe not installed
- `mocker.patch("docvet.cli.check_griffe_compat", return_value=[...])` — control findings
- `mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)` — unwrap autouse mock
- `mocker.patch.object(Path, "is_dir", return_value=False)` — non-existent src_root (use carefully)

### Quality Checklist (gated from Epic 6 retro)

- [x] AC-to-test traceability: every AC has >= 1 mapped test
- [x] Assertion strength: verify all 6 Finding fields where applicable
- [x] Edge case coverage: boundary tests, skip conditions
- [x] Task tracking: verify code change exists before marking subtask done

### Project Structure Notes

**Files modified (this story):**
- `src/docvet/cli.py` — replace `_run_griffe` stub, add `importlib.util` import, add `check_griffe_compat` import, update `check()` and `griffe()` callers
- `tests/unit/test_cli.py` — update existing griffe test, add ~11 new tests

**No new files created.** All changes are in existing files.

**Module dependency changes:**
```
cli.py
  → NEW: import importlib.util
  → NEW: from docvet.checks.griffe_compat import check_griffe_compat
  → EXISTING: all other imports unchanged
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#CLI Stub Signature Mismatch] — `_run_griffe` must resolve `src_root` internally
- [Source: _bmad-output/planning-artifacts/architecture.md#Griffe Cross-Cutting Concerns] — Two-layer skip logic for optional dependency
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2] — AC definitions, FR95 + FR97
- [Source: _bmad-output/implementation-artifacts/7-1-core-griffe-compatibility-check-function.md] — Previous story patterns and learnings
- [Source: src/docvet/cli.py:312-319] — Current `_run_griffe` stub to replace
- [Source: src/docvet/cli.py:295-309] — `_run_coverage` pattern to follow
- [Source: src/docvet/checks/griffe_compat.py:136-191] — `check_griffe_compat` API contract
- [Source: tests/unit/test_cli.py:475-482] — Existing griffe CLI test to update
- [Source: tests/unit/test_cli.py:916-1001] — `_run_coverage` test patterns to follow

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed 2 test failures: `test_run_griffe_passes_correct_src_root_path` and `test_run_griffe_with_default_config_uses_project_root_dot` failed because `src_root.is_dir()` returned False for non-existent test paths. Resolved by using `tmp_path` to create real directories (unlike coverage tests which don't have this guard).

### Completion Notes List

- Replaced `_run_griffe` stub with full implementation following `_run_coverage` pattern
- Added two-layer griffe availability detection: `importlib.util.find_spec` at CLI level + `try/except ImportError` in griffe_compat module
- Added `verbose` keyword parameter to `_run_griffe` for optional-dependency skip messaging
- Added `_run_griffe` to autouse fixture in test_cli.py for test isolation consistency
- Updated 4 existing tests (griffe exit, check order, config passing, discover+run)
- Added 11 new tests covering all AC (findings format, no output, src_root, files, not installed, verbose, fail-on, missing dir, check integration, verbose passing)
- All 614 tests pass (up from 557), lint and format clean

### File List

- `src/docvet/cli.py` — replaced `_run_griffe` stub, added `importlib.util` and `check_griffe_compat` imports, updated `check()` and `griffe()` callers
- `tests/unit/test_cli.py` — added `_run_griffe` to imports and autouse fixture, updated 4 existing tests, added 11 new tests

### Change Log

- 2026-02-11: Wired griffe compatibility check into CLI — replaced stub with real implementation, added griffe availability detection and verbose/fail-on messaging, 11 new tests (614 total)
- 2026-02-11: Code review fixes — added 3 missing tests (griffe --all/--staged discovery, fail-on priority over verbose), moved MagicMock to module-level import (617 total)
