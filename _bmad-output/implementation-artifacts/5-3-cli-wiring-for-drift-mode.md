# Story 5.3: CLI Wiring for Drift Mode

Status: done

## Story

As a developer,
I want to run `docvet freshness --mode drift` from the command line and see drift/age findings,
so that I can perform periodic docstring health audits on my codebase.

## Acceptance Criteria

1. **AC1 — Blame execution:** `docvet freshness --mode drift` runs `git blame --line-porcelain` for each discovered file and passes the output to `check_freshness_drift`.
2. **AC2 — Finding output format:** Findings are printed in `file:line: rule message` format (one per line), matching the existing enrichment and diff mode output format.
3. **AC3 — Clean exit on no findings:** When no drift or age threshold violations exist, the command produces no output and exits with code 0.
4. **AC4 — Config passthrough:** Config reads `drift-threshold` and `age-threshold` from `[tool.docvet.freshness]` in `pyproject.toml` and passes `FreshnessConfig` to `check_freshness_drift`.
5. **AC5 — Default thresholds:** When no `[tool.docvet.freshness]` section exists, defaults apply (drift: 30 days, age: 90 days — FR65).
6. **AC6 — No git history:** Files with no git history (untracked, no blame data) are skipped — empty blame output produces an empty findings list.
7. **AC7 — Default mode unchanged:** `docvet freshness` with no `--mode` flag still defaults to diff mode (FR68).
8. **AC8 — Check command unchanged:** `docvet check` runs freshness in diff mode by default alongside other checks.

**FRs:** FR67 (drift wiring), FR68 (`--mode drift`), NFR21, NFR29

## Tasks / Subtasks

- [x] Task 1: Add `_get_git_blame` helper to `cli.py` (AC: 1)
  - [x] 1.1 Add private function `_get_git_blame(file_path: Path, project_root: Path) -> str`
  - [x] 1.2 Runs `git blame --line-porcelain -- <file_path>` with `cwd=project_root`
  - [x] 1.3 Returns empty string on non-zero exit (same pattern as `_get_git_diff`)
- [x] Task 2: Wire drift mode in `_run_freshness` (AC: 1, 2, 3, 4, 6)
  - [x] 2.1 Import `check_freshness_drift` from `docvet.checks.freshness`
  - [x] 2.2 Replace `"freshness drift: not yet implemented"` stub with actual logic
  - [x] 2.3 For each file: read source, parse AST, get blame, call `check_freshness_drift(str(file_path), blame_output, tree, config.freshness)`
  - [x] 2.4 Print each finding in `file:line: rule message` format
  - [x] 2.5 Handle `SyntaxError` with warning and skip (existing pattern)
- [x] Task 3: Add unit tests for `_get_git_blame` (AC: 1, 6)
  - [x] 3.1 Test blame runs `git blame --line-porcelain -- <path>` with correct cwd
  - [x] 3.2 Test blame returns stdout on success
  - [x] 3.3 Test blame returns empty string on non-zero exit
- [x] Task 4: Add unit tests for drift mode wiring (AC: 1, 2, 3, 4, 5, 6)
  - [x] 4.1 Test drift mode calls `check_freshness_drift` per file with blame output
  - [x] 4.2 Test drift mode prints findings in correct format
  - [x] 4.3 Test drift mode with no findings produces no output
  - [x] 4.4 Test drift mode passes `config.freshness` to `check_freshness_drift`
  - [x] 4.5 Test drift mode handles syntax errors with warning
  - [x] 4.6 Test drift mode processes multiple files
- [x] Task 5: Verify existing behavior preserved (AC: 7, 8)
  - [x] 5.1 Verify `freshness` with no `--mode` still defaults to diff
  - [x] 5.2 Verify `check` command still runs freshness in diff mode
  - [x] 5.3 Remove/update the "not yet implemented" test
- [x] Task 6: Run full test suite and quality gates

## Dev Notes

### Implementation Pattern — Follow `_get_git_diff` and diff-mode wiring exactly

The existing `_get_git_diff` helper and diff-mode branch in `_run_freshness` establish the exact pattern. Drift mode follows the same shape — only the git command and check function differ.

**`_get_git_blame` helper** (new, modeled on `_get_git_diff` at `cli.py:147-182`):

```python
def _get_git_blame(file_path: Path, project_root: Path) -> str:
    result = subprocess.run(
        ["git", "blame", "--line-porcelain", "--", str(file_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
    )
    if result.returncode != 0:
        return ""
    return result.stdout
```

Note: Unlike `_get_git_diff`, blame does NOT vary by discovery mode — blame always inspects the full committed history. No `discovery_mode` parameter needed.

**`_run_freshness` drift branch** (replace the stub at `cli.py:234-236`):

```python
if freshness_mode is not FreshnessMode.DIFF:
    # Drift mode: git blame per file → check_freshness_drift
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
            continue
        blame_output = _get_git_blame(file_path, config.project_root)
        findings = check_freshness_drift(
            str(file_path), blame_output, tree, config.freshness
        )
        for finding in findings:
            typer.echo(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
            )
    return
```

**Import addition** at `cli.py:14`:

```python
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
```

### Key Architecture Constraints

- `check_freshness_drift` signature: `(file_path: str, blame_output: str, tree: ast.Module, config: FreshnessConfig, *, now: int | None = None) -> list[Finding]` — already implemented in Story 5.2
- `FreshnessConfig` has `drift_threshold: int = 30` and `age_threshold: int = 90` — already in `config.py`
- The `check` command does NOT pass `freshness_mode` — it uses the default (`FreshnessMode.DIFF`), which is correct per AC8
- `_run_freshness` already receives `freshness_mode` and `discovery_mode` params — no signature change needed
- `FreshnessMode.DRIFT` enum value already exists in `cli.py:34`
- `--mode` flag on the `freshness` subcommand already exists at `cli.py:378-380`

### Testing Strategy

Test file: `tests/unit/test_cli.py`

**Tests to ADD:**

1. `test_get_git_blame_runs_correct_command` — verify subprocess args `["git", "blame", "--line-porcelain", "--", "<path>"]`
2. `test_get_git_blame_returns_stdout_on_success` — returncode 0 returns stdout
3. `test_get_git_blame_returns_empty_on_failure` — returncode != 0 returns ""
4. `test_run_freshness_drift_calls_check_freshness_drift_per_file` — mock check, verify called
5. `test_run_freshness_drift_prints_findings_in_correct_format` — verify `file:line: rule message`
6. `test_run_freshness_drift_no_findings_produces_no_output` — empty list, clean output
7. `test_run_freshness_drift_passes_config_freshness_to_check` — verify `config.freshness` arg
8. `test_run_freshness_drift_handles_syntax_error_with_warning` — skip + warning pattern
9. `test_run_freshness_drift_processes_multiple_files` — call_count == N

**Tests to UPDATE:**

- `test_run_freshness_with_drift_mode_prints_not_implemented` (line 641) — **DELETE** this test entirely; replace with the actual drift behavior tests above

**Existing tests that already pass and must NOT break:**

- `test_freshness_when_invoked_with_mode_drift_exits_successfully` (line 136) — will continue to pass (exit code 0)
- `test_freshness_when_invoked_with_drift_passes_freshness_mode` (line 430) — verifies `FreshnessMode.DRIFT` passed through, unaffected
- All diff-mode freshness tests — unchanged behavior

### Project Structure Notes

- Only `src/docvet/cli.py` is modified (add import, add helper, update stub)
- Only `tests/unit/test_cli.py` is modified (add/update tests)
- No new files created
- No config changes
- No freshness.py changes (5.2 already complete)

### References

- [Source: src/docvet/cli.py] — `_get_git_diff` pattern (lines 147-182), `_run_freshness` stub (lines 215-250), `FreshnessMode` enum (line 30-34)
- [Source: src/docvet/checks/freshness.py] — `check_freshness_drift` API (lines 317-412)
- [Source: src/docvet/config.py] — `FreshnessConfig` with `drift_threshold`/`age_threshold` (lines 16-20)
- [Source: tests/unit/test_cli.py] — existing freshness tests (lines 564-743), `_get_git_diff` tests (lines 653-728)
- [Source: _bmad-output/planning-artifacts/epics.md] — Story 5.3 AC (lines 1013-1053)
- [Source: _bmad-output/planning-artifacts/architecture.md] — Freshness Decision 3 (blame parsing), Decision 5 (message format)
- [Source: _bmad-output/implementation-artifacts/5-2-drift-and-age-detection-orchestrator.md] — `check_freshness_drift` implementation details
- [Source: _bmad-output/implementation-artifacts/5-1-blame-timestamp-parser.md] — `_parse_blame_timestamps` implementation details

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Added `_get_git_blame` helper mirroring `_get_git_diff` pattern (no `discovery_mode` — blame always reads full history)
- Replaced "not yet implemented" stub in `_run_freshness` with full drift-mode branch: read → parse → blame → check → print
- Added import of `check_freshness_drift` alongside existing `check_freshness_diff`
- Updated `_run_freshness` docstring to reflect drift mode is implemented
- Added 3 unit tests for `_get_git_blame` (command args, stdout return, failure return)
- Added 6 unit tests for drift mode wiring (per-file call, output format, no-output, config passthrough, syntax error, multi-file)
- Deleted `test_run_freshness_with_drift_mode_prints_not_implemented` (replaced by actual behavior tests)
- All 8 existing drift-related tests continue to pass unchanged
- 528 total tests pass, 0 failures, ruff lint + format clean

### File List

- `src/docvet/cli.py` — added `_get_git_blame` helper, `check_freshness_drift` import, drift branch in `_run_freshness`
- `tests/unit/test_cli.py` — added 9 tests (`_get_git_blame` + drift wiring), deleted 1 "not implemented" test

## Senior Developer Review (AI)

**Reviewer:** Alberto-Codes on 2026-02-11
**Outcome:** Approved with fixes applied

### Review Summary

All 8 ACs verified as implemented. All 6 tasks (19 subtasks) confirmed done. Git vs story File List: 0 discrepancies. 528 tests pass, ruff clean.

### Findings (5 total: 0 High, 2 Medium, 3 Low)

**Fixed (2 Medium):**
- **M1:** `_get_git_blame` wiring test used `assert_called_once()` without verifying arguments — strengthened to `assert_called_once_with(file_path, ANY)` and added negative assertion that `check_freshness_diff` is NOT called during drift mode (also fixes L1)
- **M2:** Multi-file drift test used empty blame for all files — updated to use `side_effect` returning unique blame data per file and verify per-file data isolation

**Acknowledged (3 Low — not fixed, accepted):**
- **L1:** No negative assertion for `check_freshness_diff` during drift mode — fixed as part of M1
- **L2:** Negated conditional `is not FreshnessMode.DIFF` instead of positive `is FreshnessMode.DRIFT` — matches story design spec, equivalent with 2-value enum
- **L3:** Read/parse/SyntaxError pattern duplicated across runners — pre-existing pattern, beyond story scope

### Change Log

- 2026-02-11: Code review — 2 MEDIUM fixes applied to `tests/unit/test_cli.py`, story approved and marked done
