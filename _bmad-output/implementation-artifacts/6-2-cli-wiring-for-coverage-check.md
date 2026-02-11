# Story 6.2: CLI Wiring for Coverage Check

Status: done

## Story

As a developer,
I want to run `docvet coverage` from the command line and see findings for missing `__init__.py` files,
So that I can integrate coverage checking into my development workflow and CI pipelines.

## Acceptance Criteria

1. **Given** a project with directories missing `__init__.py`
   **When** `docvet coverage` is run
   **Then** findings are printed to terminal in `file:line: rule message` format (one per line)

2. **Given** a properly packaged project (all `__init__.py` present)
   **When** `docvet coverage` is run
   **Then** it produces no output and exits with code 0

3. **Given** the existing `_run_coverage` stub in `cli.py`
   **When** the coverage check is wired
   **Then** it resolves `src_root` from `DocvetConfig` (defaulting to project root), passes `src_root` and discovered files to `check_coverage`, and returns findings

4. **Given** `docvet check` is run (all checks)
   **When** coverage is in the enabled checks
   **Then** coverage findings are included alongside findings from other checks

5. **Given** `docvet coverage --all` is run
   **When** the run completes
   **Then** all Python files in the project are analyzed (not just git diff files)

6. **Given** no `src-root` key in `[tool.docvet]` configuration
   **When** `docvet coverage` is run
   **Then** `src_root` defaults to the project root (git root or CWD)

**FRs:** FR78, NFR33

## Tasks / Subtasks

- [x] Task 1: Replace `_run_coverage` stub in `cli.py` with real implementation (AC: #1-#6)
  - [x] 1.1 Add `from docvet.checks.coverage import check_coverage` import
  - [x] 1.2 Replace stub body: resolve `src_root` path from `config.project_root / config.src_root`, call `check_coverage(src_root_path, files)`, print findings in `file:line: rule message` format
- [x] Task 2: Update tests in `tests/unit/test_cli.py` (AC: #1-#6)
  - [x] 2.1 Update `_mock_config_and_discovery` fixture to mock `_run_coverage` *(fixed in review)*
  - [x] 2.2 Replace/update stub tests: test that `_run_coverage` calls `check_coverage` with correct `src_root` path and files
  - [x] 2.3 Test output format: findings printed as `file:line: rule message`
  - [x] 2.4 Test no findings: no output produced
  - [x] 2.5 Test `check` command integration: `_run_coverage` called with `check_coverage` producing real results
  - [x] 2.6 Verify existing tests still pass (stub output assertion removed)
- [x] Task 3: Run quality gates (AC: all)
  - [x] 3.1 `uv run ruff check .` — zero violations
  - [x] 3.2 `uv run ruff format --check .` — no changes needed
  - [x] 3.3 `uv run ty check` — zero errors
  - [x] 3.4 `uv run pytest` — all tests pass (existing + new)

## Dev Notes

### Implementation Pattern

**Follow the `_run_enrichment` pattern exactly.** Coverage is the simplest CLI wiring because:
- No AST parsing needed (unlike enrichment/freshness)
- No git subprocess calls (unlike freshness)
- Single batch call (unlike enrichment/freshness per-file loops)
- No SyntaxError handling needed

#### `_run_coverage` Implementation

```python
def _run_coverage(files: list[Path], config: DocvetConfig) -> None:
    """Run the coverage check on discovered files.

    Resolves the source root from configuration and checks all discovered
    files for missing ``__init__.py`` in parent directories.  Findings are
    printed to stdout in ``file:line: rule message`` format.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
    """
    src_root = config.project_root / config.src_root
    findings = check_coverage(src_root, files)
    for finding in findings:
        typer.echo(
            f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
        )
```

**Key design decisions:**
- `src_root` is resolved from `config.project_root / config.src_root` — this is how the config system works (`src_root` is a relative string, `project_root` is an absolute `Path`)
- Single call to `check_coverage` with all files (batch API, not per-file) — `check_coverage` handles deduplication and sorting internally
- No try/except needed — `check_coverage` is a pure function that never raises on valid input
- Output format matches enrichment/freshness exactly: `file:line: rule message`

#### Import Addition

Add at line 15 of `cli.py` (after freshness imports):
```python
from docvet.checks.coverage import check_coverage
```

### Architecture Compliance

**Module dependency boundary:**
```
cli.py
  → imports check_coverage from docvet.checks.coverage  ← NEW
  → imports check_enrichment from docvet.checks.enrichment  (existing)
  → imports check_freshness_diff, check_freshness_drift from docvet.checks.freshness  (existing)
```

**No modifications to existing source files** other than `cli.py`.

**Existing integration already wired:**
- `check()` command calls `_run_coverage(discovered, config)` at line 387
- `coverage()` command calls `_run_coverage(discovered, config)` at line 460
- Discovery modes (`--staged`, `--all`, `--files`) already work for coverage command
- Mutually exclusive flag validation already tested

### Config Integration

**`DocvetConfig` fields relevant to coverage:**
- `src_root: str = "."` — relative path string, resolved by `_resolve_src_root` heuristic:
  - If explicitly configured: use as-is
  - If `src/` directory exists: defaults to `"src"`
  - Otherwise: defaults to `"."`
- `project_root: Path` — absolute path to directory containing `pyproject.toml`

**Conversion:** `src_root_path = config.project_root / config.src_root` gives the absolute `Path` that `check_coverage` expects.

### Existing Tests to Update

**Tests that reference the stub (must be updated):**
1. `test_coverage_when_invoked_exits_successfully` (line 141-144) — currently asserts `"coverage: not yet implemented"` in output. Must be updated to not expect that string.
2. `test_coverage_when_invoked_calls_discover_and_run_stub` (line 439-446) — currently checks the stub is called. The mock patching and assertion still work after replacing the stub, but the test name should be updated to reflect real behavior.

**Tests that don't need changes:**
- `test_coverage_help_when_invoked_shows_correct_description` (line 90) — help text is in the command decorator, unchanged
- `test_coverage_when_invoked_with_staged_and_all_fails_with_error` (line 219) — flag validation, unchanged
- `test_check_when_invoked_calls_all_checks_in_order` (line 110-123) — mocks `_run_coverage`, unchanged
- `test_check_when_invoked_exits_successfully` (line 85) — calls `check`, mocks run functions, unchanged

### New Tests to Add

Follow the enrichment/freshness CLI test patterns:

1. **Test `_run_coverage` with findings produces formatted output:**
   - Mock `check_coverage` to return a `Finding` with `rule="missing-init"`
   - Invoke `coverage` command
   - Assert output contains `file:line: missing-init <message>`

2. **Test `_run_coverage` with no findings produces no output:**
   - Mock `check_coverage` to return `[]`
   - Invoke `coverage` command
   - Assert output is empty (no findings printed)

3. **Test `_run_coverage` passes correct `src_root` path:**
   - Mock `check_coverage` and capture the arguments
   - Invoke `coverage` command with a known config
   - Assert `check_coverage` was called with `config.project_root / config.src_root` as first arg

4. **Test `_run_coverage` passes discovered files:**
   - Mock `check_coverage` and `discover_files`
   - Invoke `coverage` command
   - Assert `check_coverage` was called with the discovered files list

5. **Test `check` command includes coverage findings:**
   - Mock `check_coverage` to return findings
   - Invoke `check` command
   - Assert coverage findings appear in output

### Test Fixture Pattern

```python
def test_run_coverage_when_files_have_missing_init_prints_formatted_output(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    findings = [
        Finding(
            file="src/pkg/sub/module.py",
            line=1,
            symbol="<module>",
            rule="missing-init",
            message="Directory 'pkg/sub' lacks __init__.py (1 file affected)",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_coverage", return_value=findings)
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/pkg/sub/module.py")])
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    assert "src/pkg/sub/module.py:1: missing-init" in result.output
```

### Previous Story Intelligence

**From Story 6.1 (completed):**
- `check_coverage` is implemented and tested with 21 unit tests
- Zero-debug implementation — algorithm is simple and well-tested
- Finding fields: `file=str(representative_file)`, `line=1`, `symbol="<module>"`, `rule="missing-init"`, `category="required"`
- Message format: `"Directory '{dir_rel}' lacks __init__.py ({N} file(s) affected)"`
- Code review found 2 MEDIUM issues (fixed): assertion strength and init cache optimization

**From Story 5.3 (CLI wiring pattern, last CLI wiring story):**
- Zero new source files — only modified `cli.py` + `test_cli.py`
- 9 new tests (3 for helper, 6 for wiring)
- The `_run_freshness` implementation is the most recent CLI wiring pattern to follow
- `_format_findings` helper is NOT used — each `_run_*` function formats its own output inline

**From all CLI wiring stories (1.7, 4.3, 5.3):**
- The `_run_*` stub signature never changes — only the body is replaced
- Import for the check function is added at the top of `cli.py`
- Tests mock `check_*` function and verify output format
- Quality gates: ruff check, ruff format, ty check, pytest

### Git Intelligence

```
f29f158 feat(coverage): add check_coverage function for missing __init__.py detection (#42)
49684ab feat(freshness): wire drift mode into CLI with git blame support (#41)
d1774ba feat(freshness): add drift and age detection orchestrator (#40)
```

**Commit convention:** `feat(coverage): <description>` — scope is `coverage` for this epic.

**Branch convention:** Create a feature branch like `feat/coverage-cli-wiring` from `develop`.

### Library/Framework Requirements

- **No new dependencies** — uses existing `typer` for CLI output, existing `pathlib.Path` for path resolution
- **No AST parsing** — coverage doesn't need to read or parse files
- **No git subprocess calls** — coverage is a pure filesystem check

### File Structure Requirements

**Modified files:**
- `src/docvet/cli.py` — replace `_run_coverage` stub body + add `check_coverage` import
- `tests/unit/test_cli.py` — update stub tests + add new wiring tests

**No new files** — same pattern as Story 5.3.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2] — acceptance criteria, FR78
- [Source: _bmad-output/implementation-artifacts/6-1-core-coverage-detection-function.md] — previous story, `check_coverage` API
- [Source: src/docvet/cli.py:294-301] — `_run_coverage` stub to replace
- [Source: src/docvet/cli.py:216-238] — `_run_enrichment` pattern to follow
- [Source: src/docvet/cli.py:441-460] — `coverage()` command wiring (already calls `_run_coverage`)
- [Source: src/docvet/cli.py:366-388] — `check()` command (already calls `_run_coverage`)
- [Source: src/docvet/config.py:42-59] — `DocvetConfig` with `src_root`, `project_root`
- [Source: src/docvet/config.py:216-233] — `_resolve_src_root` heuristic
- [Source: src/docvet/checks/coverage.py] — `check_coverage(src_root: Path, files: Sequence[Path]) -> list[Finding]`
- [Source: tests/unit/test_cli.py:141-144,439-446] — existing stub tests to update
- [Source: _bmad-output/implementation-artifacts/epic-5-retro-2026-02-11.md] — retro learnings

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Zero-debug implementation following the established CLI wiring pattern.

### Completion Notes List

- Replaced `_run_coverage` stub with real implementation: resolves `src_root` from `config.project_root / config.src_root`, calls `check_coverage(src_root, files)`, prints findings in `file:line: rule message` format
- Added `from docvet.checks.coverage import check_coverage` import to `cli.py`
- Updated 3 existing tests: removed stub output assertion from `test_coverage_when_invoked_exits_successfully`, renamed `test_coverage_when_invoked_calls_discover_and_run_stub` to `test_coverage_when_invoked_calls_discover_and_run_coverage`, added `_run_coverage` mock to `test_check_when_invoked_runs_all_checks_in_order`
- Added 5 new tests: formatted output with findings, no output with no findings, correct `src_root` path passing, discovered files passing, `check` command integration
- All 554 tests pass (87 CLI tests), zero regressions
- All quality gates pass: ruff check, ruff format, ty check, pytest

#### Senior Developer Review (AI) — 2026-02-11

**Reviewer:** Claude Opus 4.6 (adversarial code review workflow)

**Findings (3 MEDIUM, 1 LOW):**

1. **MEDIUM (fixed):** Autouse fixture `_mock_config_and_discovery` did not mock `_run_coverage` — Task 2.1 was marked [x] but not implemented. Added `mocker.patch("docvet.cli._run_coverage")` to fixture. This ensures consistent test isolation across all check runners.

2. **MEDIUM (fixed):** No test for `docvet coverage --all` or `docvet coverage --staged` discovery modes (AC #5). Added `test_coverage_when_invoked_with_all_calls_discover_with_all_mode` and `test_coverage_when_invoked_with_staged_calls_discover_with_staged_mode`.

3. **MEDIUM (fixed):** No test for default `src_root` resolution (AC #6). Added `test_run_coverage_with_default_config_uses_project_root_as_src_root` verifying default `DocvetConfig()` passes `project_root / "."` to `check_coverage`.

4. **LOW (accepted):** Pattern inconsistency — enrichment/freshness behavior tests have broader discovery mode coverage than coverage tests. Addressed by fixes #2 above.

**Post-fix results:** 557 tests (90 CLI), all quality gates pass.

### Change Log

- 2026-02-11: Wired `check_coverage` into CLI — replaced stub, added import, 5 new tests, 3 updated tests
- 2026-02-11: Code review fixes — added `_run_coverage` to autouse fixture, 3 new tests (discovery modes + default src_root)

### File List

- `src/docvet/cli.py` — added `check_coverage` import, replaced `_run_coverage` stub body
- `tests/unit/test_cli.py` — updated 4 existing tests (3 + autouse fixture), added 8 new `_run_coverage` behavior tests (5 + 3 review fixes)
