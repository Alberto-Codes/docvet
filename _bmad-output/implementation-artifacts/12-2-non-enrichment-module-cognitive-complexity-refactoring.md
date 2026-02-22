# Story 12.2: Non-Enrichment Module Cognitive Complexity Refactoring

Status: review
Branch: `feat/refactor-12-2-non-enrichment-cc`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a docvet contributor,
I want the remaining complex functions across config, discovery, freshness, griffe, and coverage modules refactored to cognitive complexity ≤ 15,
so that every source module passes SonarQube's maintainability threshold.

## Acceptance Criteria

1. **Given** `load_config` in `config.py` (CC 29) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing config tests pass without modification
2. **Given** `_walk_all` in `discovery.py` (CC 23) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing discovery tests pass without modification
3. **Given** `discover_files` in `discovery.py` (CC 20) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing discovery tests pass without modification
4. **Given** `_parse_blame_timestamps` in `freshness.py` (CC 19) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing freshness tests pass without modification
5. **Given** `check_freshness_drift` in `freshness.py` (CC 18) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing freshness tests pass without modification
6. **Given** `check_griffe_compat` in `griffe_compat.py` (CC 17) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing griffe tests pass without modification
7. **Given** `check_coverage` in `coverage.py` (CC 16) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all existing coverage tests pass without modification
8. **Given** all 7 refactored functions across 5 modules **When** `uv run pytest` is executed **Then** all tests pass with zero failures **And** no functional behavior has changed

## Tasks / Subtasks

- [x] Task 1: Refactor `load_config` in `config.py` — CC 29 → ≤ 15 (AC: 1)
  - [x] 1.1 Extract `_find_pyproject_path(path: Path | None) -> Path | None` — isolate pyproject.toml discovery logic
  - [x] 1.2 Extract `_read_docvet_toml(pyproject_path: Path) -> dict[str, object]` — isolate TOML parsing and section extraction (3-level nesting)
  - [x] 1.3 ~~Extract `_extract_config_field`~~ — reverted during review; inline `isinstance` checks preserve type safety without `type: ignore` comments
  - [x] 1.4 Simplify `load_config` to: find path → read TOML → parse section → construct dataclass
  - [x] 1.5 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings
  - [x] 1.6 Run `uv run pytest tests/unit/test_config.py` — all 64 config tests pass
- [x] Task 2: Refactor `_walk_all` in `discovery.py` — CC 23 → ≤ 15 (AC: 2)
  - [x] 2.1 Extract `_collect_python_files(path_iter: Iterable[Path], config: DocvetConfig) -> list[Path]` — unify the duplicated git-branch and rglob-branch file filtering logic
  - [x] 2.2 Simplify `_walk_all` to: try git → fallback rglob → both feed into `_collect_python_files`
  - [x] 2.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero issues on full module
- [x] Task 3: Refactor `discover_files` in `discovery.py` — CC 20 → ≤ 15 (AC: 3)
  - [x] 3.1 Extract `_discover_explicit_files(files: Sequence[Path]) -> list[Path]` — isolate FILES mode processing
  - [x] 3.2 Simplify mode dispatch in `discover_files` (early return for ALL, helper call for FILES, shared git path for DIFF/STAGED)
  - [x] 3.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero issues on full module
  - [x] 3.4 Run `uv run pytest tests/unit/test_discovery.py` — all 27 discovery tests pass
- [x] Task 4: Refactor `_parse_blame_timestamps` in `freshness.py` — CC 19 → ≤ 15 (AC: 4)
  - [x] 4.1 Extract `_classify_blame_line(line: str) -> tuple[str, int | None]` — line-classifying helper reducing sequential if-blocks in loop
  - [x] 4.2 Simplify main loop to use helper with kind/value dispatch
  - [x] 4.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings
- [x] Task 5: Refactor `check_freshness_drift` in `freshness.py` — CC 18 → ≤ 15 (AC: 5)
  - [x] 5.1 Extract `_build_drift_finding(sym, code_ts, doc_ts, file_path) -> Finding` — isolate drift finding construction
  - [x] 5.2 Extract `_build_age_finding(sym, doc_ts, effective_now, file_path) -> Finding` — isolate age finding construction
  - [x] 5.3 Extract `_group_timestamps_by_symbol(timestamps, line_map)` — isolate timestamp grouping loop
  - [x] 5.4 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings (first pass was CC 16, extracted grouping helper to fix)
  - [x] 5.5 Run `uv run pytest tests/unit/checks/test_freshness.py` — all 92 freshness tests pass
- [x] Task 6: Refactor `check_griffe_compat` in `griffe_compat.py` — CC 17 → ≤ 15 (AC: 6)
  - [x] 6.1 Extract `_load_and_check_packages(src_root, file_set, handler) -> list[Finding]` — isolate package loading loop with try-except
  - [x] 6.2 Simplify main function to: setup → load packages via helper → cleanup
  - [x] 6.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings
  - [x] 6.4 Run `uv run pytest tests/unit/checks/test_griffe_compat.py` — all 40 griffe tests pass
- [x] Task 7: Refactor `check_coverage` in `coverage.py` — CC 16 → ≤ 15 (AC: 7)
  - [x] 7.1 Extract `_find_missing_init_dirs(file: Path, src_root: Path, init_cache: dict) -> set[Path]` — isolate the nested while-loop parent directory walking
  - [x] 7.2 Simplify main function to use helper
  - [x] 7.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings
  - [x] 7.4 Run `uv run pytest tests/unit/checks/test_coverage.py` — all 21 coverage tests pass
- [x] Task 8: Full regression suite (AC: 8)
  - [x] 8.1 Run `uv run pytest` — 731 passed, 1 skipped (griffe optional dep)
  - [x] 8.2 Run `uv run ruff check .` — zero violations
  - [x] 8.3 Run `uv run ruff format --check .` — zero format issues
  - [x] 8.4 Run `uv run ty check` — zero type errors (2 pre-existing griffe warnings)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `tests/unit/test_config.py` (64 tests) + SonarQube `analyze_code_snippet` zero S3776 | PASS |
| 2 | `tests/unit/test_discovery.py` (27 tests) + SonarQube zero S3776 on full module | PASS |
| 3 | `tests/unit/test_discovery.py` (27 tests) + SonarQube zero S3776 on full module | PASS |
| 4 | `tests/unit/checks/test_freshness.py` (92 tests) + SonarQube zero S3776 | PASS |
| 5 | `tests/unit/checks/test_freshness.py` (92 tests) + SonarQube zero S3776 | PASS |
| 6 | `tests/unit/checks/test_griffe_compat.py` (40 tests) + SonarQube zero S3776 | PASS |
| 7 | `tests/unit/checks/test_coverage.py` (21 tests) + SonarQube zero S3776 | PASS |
| 8 | `uv run pytest` — 731 passed, 1 skipped; `uv run ruff check .` — 0 violations; `uv run ruff format --check .` — 0 issues; `uv run ty check` — 0 errors (2 pre-existing griffe warnings) | PASS |

## Dev Notes

### Refactoring Strategy — Lessons from Story 12.1

Story 12.1 established the proven refactoring playbook for this codebase. Apply identical approach:

1. **Extract small private helpers** — move nested logic into `_helper_name()` functions placed immediately above the function they serve
2. **Verify with SonarQube** — use `mcp__sonarqube__analyze_code_snippet` with `projectKey: "docvet"` after each function refactor
3. **Zero test modifications** — if any existing test fails, the refactoring is wrong. Fix the refactoring, not the test
4. **Helpers stay private** — `_leading_underscore` prefix, no additions to `__all__`
5. **All helpers need Google-style docstrings** — match existing patterns in each file

### Per-Function Refactoring Detail

**`load_config` (CC 29 → ≤ 15) — HIGHEST PRIORITY, do first:**

The function does 3 things in one body: (1) find pyproject.toml, (2) parse TOML and extract `[tool.docvet]`, (3) validate types and construct `DocvetConfig`. The 3-level nesting in TOML section extraction (lines 456-476) and 5 repeated `if isinstance` type validation blocks (lines 478-516) are the main CC drivers.

**Strategy:** Extract into 2-3 helpers:
- `_find_pyproject_path()` — path discovery (already uses early returns, may not need extraction)
- `_parse_docvet_section()` — TOML parsing, section extraction, error handling. Returns the raw dict or `None`
- `_extract_config_field()` or a table-driven approach — replace 5 repeated type-check blocks with a single validation loop

**Critical:** The `fail_on`/`warn_on` overlap validation (lines 499-506) must stay in the consolidation path. Don't lose this check when extracting.

**`_walk_all` (CC 23 → ≤ 15):**

Two nearly identical code paths: git-based file listing (lines 140-158) and rglob fallback (lines 161-172). Both iterate paths, check symlinks, resolve, check exclusion, append. The duplication IS the complexity.

**Strategy:** Extract a shared `_collect_python_files(path_source, root, config)` that both branches call. The git branch pre-processes lines into paths, the rglob branch provides paths directly.

**`discover_files` (CC 20 → ≤ 15):**

Mode dispatch via if-elif chain with inline processing for FILES mode (lines 208-220). The FILES mode loop has nested guards (resolve, suffix check, exclusion check).

**Strategy:** Extract FILES mode to `_discover_explicit_files()`. The remaining modes (ALL → `_walk_all`, DIFF/STAGED → shared git path) become simple dispatch.

**`_parse_blame_timestamps` (CC 19 → ≤ 15):**

Implicit state machine with 3 sequential if-blocks in a loop processing git blame porcelain output. Each block has try-except for integer parsing.

**Strategy:** Extract a line classifier helper or an integer parsing helper to reduce the nesting. Alternatively, restructure the sequential ifs to use `elif` chains or early `continue` patterns.

**`check_freshness_drift` (CC 18 → ≤ 15):**

Symbol iteration loop with two nearly identical conditional blocks: drift finding construction (lines 383-398) and age finding construction (lines 400-411). Both compute dates, build messages, create Finding objects.

**Strategy:** Extract `_build_drift_finding()` and `_build_age_finding()` helpers. Main loop becomes 2 simple conditional calls.

**`check_griffe_compat` (CC 17 → ≤ 15):**

Nested try-except inside a package iteration loop, plus a secondary object-processing loop. The try-finally for handler cleanup adds structural depth.

**Strategy:** Extract the package loading loop (with its try-except) into a `_load_griffe_packages()` helper. Main function becomes: setup → load → process → cleanup.

**`check_coverage` (CC 16 → ≤ 15) — LOWEST CC, simplest fix:**

A while-loop nested inside a for-loop, walking parent directories. CC is barely over threshold.

**Strategy:** Extract `_find_missing_init_dirs()` to isolate the parent-walking while-loop. One small extraction should bring CC under 15.

### Critical Constraints

- **Pure refactoring** — zero behavioral changes. Identical inputs produce identical outputs
- **No existing test modifications** — all existing tests must pass as-is. If a test fails, the refactoring is wrong
- **No new tests required** — unless a helper warrants a safety-net test (like 12.1's `_RULE_DISPATCH` validation). Evaluate on a case-by-case basis
- **Helper functions stay private** — `_` prefix, no additions to `__all__`
- **All helpers need docstrings** — Google-style, matching existing patterns per module
- **`from __future__ import annotations`** — already present in all files
- **Verify CC with SonarQube** — use `mcp__sonarqube__analyze_code_snippet` with `projectKey: "docvet"` after each function refactor
- **Recommended task order:** `load_config` (highest CC, most complex) → `_walk_all` → `discover_files` (same module, do together) → `_parse_blame_timestamps` → `check_freshness_drift` (same module) → `check_griffe_compat` → `check_coverage` (lowest CC, simplest)

### File Scope

| File | Action |
|------|--------|
| `src/docvet/config.py` | Refactor `load_config`, add 2-3 helpers |
| `src/docvet/discovery.py` | Refactor `_walk_all` + `discover_files`, add 2-3 helpers |
| `src/docvet/checks/freshness.py` | Refactor `_parse_blame_timestamps` + `check_freshness_drift`, add 2-3 helpers |
| `src/docvet/checks/griffe_compat.py` | Refactor `check_griffe_compat`, add 1-2 helpers |
| `src/docvet/checks/coverage.py` | Refactor `check_coverage`, add 1 helper |

**No other files should be modified.** Tests, CLI, enrichment — all untouched.

### Test Suite Context

| Test File | Test Count | Module Coverage |
|-----------|------------|-----------------|
| `tests/unit/test_config.py` | 64 | `config.py` — defaults, path discovery, TOML parsing, validation |
| `tests/unit/test_discovery.py` | 27 | `discovery.py` — all 4 modes, exclusion, edge cases |
| `tests/unit/checks/test_freshness.py` | 92 | `freshness.py` — blame parsing, drift, age, diff mode |
| `tests/unit/checks/test_griffe_compat.py` | 40 | `griffe_compat.py` — warnings, traversal, package loading |
| `tests/unit/checks/test_coverage.py` | 21 | `coverage.py` — init detection, caching, relative paths |
| **Total** | **244** | Robust safety net for refactoring |

### Previous Story Intelligence (12.1)

**What worked:**
- Table-driven dispatch (`_RULE_DISPATCH`) reduced `check_enrichment` from CC 53 to ~5
- Small focused helpers (`_extract_exception_name`, `_is_warn_call`, etc.) each reduced CC by 5-10 points
- One safety-net test (dispatch table validation) was the only new test needed
- All 208 enrichment tests passed without modification — confirming pure behavioral preservation
- Code review caught: narrowed type hint (`ast.AST` → `ast.Assign | ast.AnnAssign`), added bidirectional dispatch test

**What to carry forward:**
- Extract helpers immediately above the function they serve (matches existing module convention)
- Verify CC with `analyze_code_snippet` after EACH function, not just at the end
- If SonarQube reports CC still above 15, extract more aggressively — don't leave partial work
- Run module-specific tests after each function, full suite only at the end

### Git Intelligence

Latest commit: `64f0945 refactor(enrichment): reduce cognitive complexity of 5 functions below SonarQube threshold (#73)` — this is Story 12.1, merged to develop. The codebase is clean and ready for 12.2.

### Project Structure Notes

- All 5 target files follow the same pattern: module docstring → imports → constants → private helpers → public API
- New helpers should be placed immediately above the function they serve
- No new files, no dependency changes, no module reorganization
- `from __future__ import annotations` present in all files

### References

- [Source: _bmad-output/planning-artifacts/epics-housekeeping.md#Story 12.2]
- [Source: src/docvet/config.py — `load_config` line 426]
- [Source: src/docvet/discovery.py — `_walk_all` line 113, `discover_files` line 180]
- [Source: src/docvet/checks/freshness.py — `_parse_blame_timestamps` line 211, `check_freshness_drift` line 319]
- [Source: src/docvet/checks/griffe_compat.py — `check_griffe_compat` line 152]
- [Source: src/docvet/checks/coverage.py — `check_coverage` line 19]
- [Source: .claude/rules/sonarqube.md — CC threshold 15, S3776 dominant finding]
- [Source: _bmad-output/implementation-artifacts/12-1-enrichment-module-cognitive-complexity-refactoring.md — previous story patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- All 7 functions refactored below CC 15 using helper extraction pattern from Story 12.1
- `load_config` (CC 29→≤15): Extracted `_find_pyproject_path`, `_read_docvet_toml` — 2 helpers (review removed `_extract_config_field` to preserve type safety)
- `_walk_all` (CC 23→≤15): Extracted `_collect_python_files` — 1 helper unifying git/rglob branches
- `discover_files` (CC 20→≤15): Extracted `_discover_explicit_files` — 1 helper for FILES mode
- `_parse_blame_timestamps` (CC 19→≤15): Extracted `_classify_blame_line` — 1 helper for line classification
- `check_freshness_drift` (CC 18→≤15): Extracted `_build_drift_finding`, `_build_age_finding`, `_group_timestamps_by_symbol` — 3 helpers (initial pass was CC 16; grouping helper was needed to cross threshold)
- `check_griffe_compat` (CC 17→≤15): Extracted `_load_and_check_packages` — 1 helper for package loading loop
- `check_coverage` (CC 16→≤15): Extracted `_find_missing_init_dirs` — 1 helper for parent directory walking
- Review finding: `_extract_config_field` introduced 6 `type: ignore` comments where original had zero — reverted to inline `isinstance` checks which give proper type narrowing
- Fixed pre-existing ty `possibly-missing-attribute` warnings in griffe_compat.py via type-narrowing guard instead of ignore comments
- Zero test modifications — all 731 tests pass (1 skipped for optional griffe dep)
- All quality gates green: ruff check 0 violations, ruff format 0 issues, ty check 0 errors

### File List

| File | Action |
|------|--------|
| `src/docvet/config.py` | Added `_find_pyproject_path`, `_read_docvet_toml`; simplified `load_config` |
| `src/docvet/discovery.py` | Added `_collect_python_files`, `_discover_explicit_files`; simplified `_walk_all` and `discover_files` |
| `src/docvet/checks/freshness.py` | Added `_classify_blame_line`, `_group_timestamps_by_symbol`, `_build_drift_finding`, `_build_age_finding`; simplified `_parse_blame_timestamps` and `check_freshness_drift` |
| `src/docvet/checks/griffe_compat.py` | Added `_load_and_check_packages`; simplified `check_griffe_compat` |
| `src/docvet/checks/coverage.py` | Added `_find_missing_init_dirs`; simplified `check_coverage` |

### Change Log

| Commit | Description |
|--------|-------------|
| (pending) | refactor: reduce cognitive complexity of 7 functions across 5 non-enrichment modules below SonarQube threshold |
