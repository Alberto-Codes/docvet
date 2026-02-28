# Story 25.1: Standardize pytestmark Usage

Status: review
Branch: `feat/test-25-1-standardize-pytestmark-usage`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/195

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **docvet contributor**,
I want pytestmark usage to be consistent across all unit test files,
so that test organization follows a clear convention and marker-based filtering works reliably.

## Acceptance Criteria

1. **Given** the 15 unit test files (5 with `pytestmark`, 10 without) and 2 integration test files (1 with, 1 without)
   **When** `pytestmark = pytest.mark.unit` is added to the 10 unit files missing it and `pytestmark = pytest.mark.integration` is added to `tests/integration/test_griffe_compat.py`
   **Then** all 15 unit test files have `pytestmark = pytest.mark.unit` and all 2 integration test files have `pytestmark = pytest.mark.integration`

2. **Given** the markers are added to all test files
   **When** `uv run pytest` is executed
   **Then** all 737+ tests pass with zero regressions

3. **Given** the adopt-markers decision
   **When** documented in `.github/instructions/pytest.instructions.md`
   **Then** the file includes a "Module-Level Markers" section explaining the `pytestmark` convention, rationale, and placement rules

4. **Given** markers are consistently applied
   **When** a contributor checks CLAUDE.md or pytest instructions
   **Then** `pytest -m unit` and `pytest -m integration` usage is documented as local development shortcuts

## Tasks / Subtasks

- [x] Task 1: Add `pytestmark = pytest.mark.unit` to the 10 unit test files missing it (AC: 1, 2)
  - [x] 1.1: `tests/unit/test_config.py`
  - [x] 1.2: `tests/unit/test_exports.py`
  - [x] 1.3: `tests/unit/test_reporting.py`
  - [x] 1.4: `tests/unit/test_pre_commit_hooks.py`
  - [x] 1.5: `tests/unit/test_lsp.py`
  - [x] 1.6: `tests/unit/checks/test_enrichment.py`
  - [x] 1.7: `tests/unit/checks/test_freshness.py`
  - [x] 1.8: `tests/unit/checks/test_coverage.py`
  - [x] 1.9: `tests/unit/checks/test_finding.py`
  - [x] 1.10: `tests/unit/checks/test_griffe_compat.py`
- [x] Task 2: Add `pytestmark = pytest.mark.integration` to `tests/integration/test_griffe_compat.py` (AC: 1, 2)
- [x] Task 3: Run `uv run pytest` — all 737+ tests green (AC: 2)
- [x] Task 4: Document the convention in `.github/instructions/pytest.instructions.md` (AC: 3, 4)
  - [x] 4.1: Add "Module-Level Markers" section with `pytestmark` convention, rationale, and placement rules
  - [x] 4.2: Document `pytest -m unit` and `pytest -m integration` as local development shortcuts
- [x] Task 5: Update CLAUDE.md Commands section to mention marker-based filtering (AC: 4)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `grep -r pytestmark tests/` — all 17 test files have `pytestmark`; `pytest --co -m unit` collects 933, `-m integration` collects 38 | PASS |
| 2 | `uv run pytest` — 971 passed in 7.81s | PASS |
| 3 | `.github/instructions/pytest.instructions.md` updated with "Module-Level Markers (Convention)" section | PASS |
| 4 | CLAUDE.md Commands section updated with `pytest -m unit` and `pytest -m integration`; pytest instructions updated | PASS |

## Dev Notes

- This is a **convention/cleanup story** — no new Python modules, no new test files, no new features
- The deliverable is consistency: all test files have markers
- No runtime code changes — only test file headers and documentation files

### Decision: ADOPT Markers

**Decision:** Add `pytestmark` to all test files. Do NOT remove markers.

**Rationale:**
1. `project-context.md` already documents `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow` as conventions — adopting aligns with documented conventions
2. `pyproject.toml` already registers markers with `--strict-markers` — infrastructure is built, just not fully wired
3. `pytest -m unit` enables fast local feedback loops (skip integration tests that spin up temp git repos)
4. Removing would create dead documentation in `project-context.md` and `pytest.instructions.md`
5. The 5 existing files already set the pattern — extend it, don't delete it

### Current State (Verified 2026-02-28)

**Unit test files WITH `pytestmark = pytest.mark.unit`** (5):
1. `tests/unit/test_ast_utils.py` (line 16)
2. `tests/unit/test_cli.py` (line 27)
3. `tests/unit/test_cli_progress.py` (line 15)
4. `tests/unit/test_cli_timing.py` (line 14)
5. `tests/unit/test_discovery.py` (line 13)

**Unit test files WITHOUT `pytestmark`** (10):
1. `tests/unit/test_config.py`
2. `tests/unit/test_exports.py`
3. `tests/unit/test_reporting.py`
4. `tests/unit/test_pre_commit_hooks.py`
5. `tests/unit/test_lsp.py` (added in Epic 24 — not in original issue #181)
6. `tests/unit/checks/test_enrichment.py`
7. `tests/unit/checks/test_freshness.py`
8. `tests/unit/checks/test_coverage.py`
9. `tests/unit/checks/test_finding.py`
10. `tests/unit/checks/test_griffe_compat.py`

**Integration test files WITH `pytestmark = pytest.mark.integration`** (1):
1. `tests/integration/test_discovery.py` (line 13)

**Integration test files WITHOUT `pytestmark`** (1):
1. `tests/integration/test_griffe_compat.py`

### Placement Convention

The `pytestmark` assignment goes after all imports, before any test code — matching the pattern in the 5 existing files. Example placement:

```python
from __future__ import annotations

import ast
# ... other imports ...

import pytest
# ... other test imports ...

pytestmark = pytest.mark.unit


# Test code starts here
class TestSomething:
    ...
```

### Project Structure Notes

- Alignment with unified project structure: test files in `tests/unit/` and `tests/integration/` exactly mirror production structure
- No detected conflicts or variances — all paths and naming follow established conventions
- The `tests/unit/checks/` subdirectory contains 5 of the 10 files missing markers

### References

- [Source: GitHub Issue #181] — original file inventory and decision points
- [Source: _bmad-output/planning-artifacts/epics.md#Story 25.1] — acceptance criteria and implementation notes
- [Source: .github/instructions/pytest.instructions.md#Test Markers] — current marker documentation
- [Source: pyproject.toml lines 145-157] — pytest configuration with markers and strict-markers
- [Source: _bmad-output/project-context.md#Testing Rules] — marker conventions documented for AI agents

### Documentation Impact

- Pages: `.github/instructions/pytest.instructions.md`, `CLAUDE.md` Commands section
- Nature of update: Add "Module-Level Markers" convention section to pytest instructions; add `pytest -m unit` / `pytest -m integration` to CLAUDE.md Commands

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 971 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% (>= 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug sessions required. Convention/cleanup story with zero implementation issues.

### Completion Notes List

- Added `pytestmark = pytest.mark.unit` to 10 unit test files missing it
- Added `pytestmark = pytest.mark.integration` to `tests/integration/test_griffe_compat.py`
- Also added `import pytest` to 4 test files that lacked it: `test_enrichment.py`, `test_freshness.py`, `test_coverage.py`, `test_pre_commit_hooks.py`
- Removed 8 redundant `@pytest.mark.unit` class-level decorators from `test_exports.py` (module-level `pytestmark` makes them redundant)
- Cleaned up `tests/integration/test_griffe_compat.py`: replaced `__import__("pytest").importorskip("griffe")` with standard `pytest.importorskip("griffe")`
- Verified marker filtering: `pytest -m unit` collects 933 tests, `pytest -m integration` collects 38 tests (933 + 38 = 971 total)
- Updated `.github/instructions/pytest.instructions.md` with "Module-Level Markers (Convention)" section
- Updated `CLAUDE.md` Commands section with `pytest -m unit` and `pytest -m integration`
- All 6 quality gates pass: ruff, format, ty, pytest (971 passed), docvet, interrogate (100%)

### Change Log

- 2026-02-28: Standardized pytestmark across all 17 test files (10 unit + 1 integration added, 8 redundant decorators removed)
- 2026-02-28: Code review — added conftest.py exclusion note to pytest.instructions.md (L2 fix)

### File List

- `tests/unit/test_config.py` — added `pytestmark = pytest.mark.unit`
- `tests/unit/test_exports.py` — added module-level `pytestmark`, removed 8 `@pytest.mark.unit` class decorators
- `tests/unit/test_reporting.py` — added `pytestmark = pytest.mark.unit`
- `tests/unit/test_pre_commit_hooks.py` — added `import pytest` + `pytestmark = pytest.mark.unit`
- `tests/unit/test_lsp.py` — added `pytestmark = pytest.mark.unit`
- `tests/unit/checks/test_enrichment.py` — added `import pytest` + `pytestmark = pytest.mark.unit`
- `tests/unit/checks/test_freshness.py` — added `import pytest` + `pytestmark = pytest.mark.unit`
- `tests/unit/checks/test_coverage.py` — added `import pytest` + `pytestmark = pytest.mark.unit`
- `tests/unit/checks/test_finding.py` — added `pytestmark = pytest.mark.unit`
- `tests/unit/checks/test_griffe_compat.py` — added `pytestmark = pytest.mark.unit`
- `tests/integration/test_griffe_compat.py` — added `import pytest` + `pytestmark = pytest.mark.integration`, standardized `importorskip` call
- `.github/instructions/pytest.instructions.md` — added "Module-Level Markers" convention section, updated "Running Tests" commands, added conftest.py exclusion clarification (review fix L2)
- `CLAUDE.md` — added `pytest -m unit` and `pytest -m integration` to Commands section

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow) — 2026-02-28

### Outcome

**APPROVED** with 1 inline fix (L2) applied. 1 follow-up issue (M1) recommended. 2 items logged as separate backlog chores (M2, L1).

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | No automated enforcement of pytestmark convention — new test files without `pytestmark` pass all quality gates silently | Follow-up: create GitHub issue for conftest.py enforcement hook |
| M2 | MEDIUM | CLAUDE.md Architecture test structure lists non-existent files (`test_freshness_diff.py`, `test_freshness_drift.py`, `stale_signature.py`) | Backlog: separate chore to sweep CLAUDE.md test structure section |
| L1 | LOW | `test_exports.py` `_ALL_DOCVET_MODULES` missing `docvet.lsp` (pre-existing, Epic 24 gap) | Backlog: separate story to add LSP module to export tests |
| L2 | LOW | Pytest instructions don't explicitly exclude `conftest.py` from pytestmark requirement | **Fixed inline** — added parenthetical clarification to `pytest.instructions.md` |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
