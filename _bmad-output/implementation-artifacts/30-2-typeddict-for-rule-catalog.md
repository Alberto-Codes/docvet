# Story 30.2: TypedDict for _RULE_CATALOG

Status: review
Branch: `feat/mcp-30-2-typeddict-for-rule-catalog`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/290

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer working on the MCP module**,
I want `_RULE_CATALOG` to use a TypedDict with per-field types,
so that the type checker correctly narrows field types and `str()` wrappers in `_RULE_TO_CHECK` become unnecessary.

## Acceptance Criteria

1. **Given** the `_RULE_CATALOG` definition in `src/docvet/mcp.py`, **when** it is refactored to use a `RuleCatalogEntry` TypedDict, **then** the TypedDict has fields: `name: str`, `check: str`, `description: str`, `category: str`, `guidance: str`, `fix_example: str | None`.

2. **Given** the `_RULE_TO_CHECK` derivation that uses `str()` wrappers, **when** the TypedDict provides correct per-field type narrowing, **then** the `str()` wrappers are removed as unnecessary.

3. **Given** the existing test suite, **when** all tests run after the refactor, **then** all tests pass unchanged (no behavior change per NFR7).

4. **Given** the refactored code, **when** `uv run ty check` is run, **then** no new type errors are introduced.

## Tasks / Subtasks

- [x] Task 1: Add `RuleCatalogEntry` TypedDict (AC: 1)
  - [x] 1.1 Define `class RuleCatalogEntry(TypedDict)` with the six fields
  - [x] 1.2 Import `TypedDict` from `typing`
- [x] Task 2: Re-type `_RULE_CATALOG` (AC: 1)
  - [x] 2.1 Change type annotation from `list[dict[str, str | None]]` to `list[RuleCatalogEntry]`
- [x] Task 3: Remove `str()` wrappers from `_RULE_TO_CHECK` (AC: 2)
  - [x] 3.1 Change `str(r["name"]): str(r["check"])` to `r["name"]: r["check"]`
- [x] Task 4: Run quality gates (AC: 3, 4)
  - [x] 4.1 `uv run ty check` passes
  - [x] 4.2 `uv run pytest` passes (all 1201 tests)
  - [x] 4.3 `uv run ruff check .` passes
  - [x] 4.4 `uv run docvet check --all` passes

## AC-to-Test Mapping

<!-- Behavior-neutral refactor — existing tests are the quality gate. No new tests needed. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Code inspection: `RuleCatalogEntry` TypedDict exists with 6 fields | Pass |
| 2 | Code inspection: no `str()` wrappers in `_RULE_TO_CHECK` derivation | Pass |
| 3 | `uv run pytest` — all 1201 existing tests pass unchanged | Pass |
| 4 | `uv run ty check` — zero new type errors | Pass |

## Dev Notes

### Target Code (single file: `src/docvet/mcp.py`)

**Current code** (lines 91-333):
```python
_RULE_CATALOG: list[dict[str, str | None]] = [
    {
        "name": "missing-docstring",
        "check": "presence",
        ...
    },
    ...
]

_RULE_TO_CHECK: dict[str, str] = {
    str(r["name"]): str(r["check"]) for r in _RULE_CATALOG
}
```

**Target code**:
```python
from typing import TypedDict

class RuleCatalogEntry(TypedDict):
    """A single entry in the docvet rule catalog."""

    name: str
    check: str
    description: str
    category: str
    guidance: str
    fix_example: str | None

_RULE_CATALOG: list[RuleCatalogEntry] = [
    ...  # entries unchanged
]

_RULE_TO_CHECK: dict[str, str] = {
    r["name"]: r["check"] for r in _RULE_CATALOG
}
```

### Key Constraints

- **Behavior-neutral**: Zero runtime behavior change. The dict entries remain identical; only the static type narrows.
- **Single file**: All changes in `src/docvet/mcp.py`. No other files affected.
- **~5 lines changed**: Add TypedDict class (~7 lines), change type annotation on `_RULE_CATALOG` (1 line), remove `str()` wrappers (1 line), add import (1 line).
- **No new tests**: Existing test suite (971+ tests) validates behavior preservation.
- **TypedDict placement**: Define `RuleCatalogEntry` between the `_DEFAULT_MCP_CHECKS` block and the `_RULE_CATALOG` definition (around line 88-91). Keep it in the "Rule catalog" section.
- **Import placement**: `from typing import TypedDict` goes in the stdlib import block (after `from pathlib import Path`).
- **Docstring**: Add a one-line docstring to the TypedDict class per project conventions.

### Why `str()` Wrappers Exist

With `dict[str, str | None]`, subscript access `r["name"]` returns `str | None`. Since `_RULE_TO_CHECK` is typed as `dict[str, str]`, the type checker requires narrowing — hence the `str()` calls. With `RuleCatalogEntry`, `r["name"]` returns `str` directly, making the wrappers unnecessary.

### Anti-Patterns to Avoid

- Do NOT change any dict literal values in `_RULE_CATALOG` — only the type annotation changes
- Do NOT add `RuleCatalogEntry` to `__all__` — it is internal (`_RULE_CATALOG` is also internal)
- Do NOT use `typing_extensions.TypedDict` — stdlib `typing.TypedDict` is fine for Python 3.12+
- Do NOT change `_RULE_CATALOG` from a list to any other data structure
- Do NOT add `RuleCatalogEntry` to `docvet_rules()` return value — the JSON serialization (`json.dumps`) works with TypedDict instances since they are plain dicts at runtime

### Project Structure Notes

- Single module change: `src/docvet/mcp.py`
- No test file changes
- No config changes
- Aligned with project conventions: `from __future__ import annotations`, Google-style docstring

### References

- [Source: _bmad-output/planning-artifacts/epics-distribution-adoption.md, Story 30.2]
- [Source: src/docvet/mcp.py lines 91-333]
- [FR12: _RULE_CATALOG TypedDict refactor]
- [NFR7: No runtime behavior change]

### Test Maturity Piggyback

- **P3**: Add `[tool.coverage]` thresholds to `pyproject.toml` — codify the current ad-hoc coverage practice with a `fail_under` threshold
- Sourced from test-review.md — address alongside this story's work

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A (internal type annotation refactor only)

## Quality Gates

<!-- All gates mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all 1201 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no debugging needed.

### Completion Notes List

- Added `RuleCatalogEntry` TypedDict with 6 typed fields and Google-style docstring with typed Attributes section
- Changed `_RULE_CATALOG` type annotation from `list[dict[str, str | None]]` to `list[RuleCatalogEntry]`
- Removed `str()` wrappers from `_RULE_TO_CHECK` comprehension — no longer needed with per-field type narrowing
- Added `from typing import TypedDict` import
- Updated module docstring to reference `RuleCatalogEntry` (resolved `stale-body` finding)
- All 1201 tests pass unchanged, all quality gates green

### Change Log

- 2026-03-05: Refactored `_RULE_CATALOG` to use `RuleCatalogEntry` TypedDict, removed unnecessary `str()` wrappers from `_RULE_TO_CHECK`

### File List

- `src/docvet/mcp.py` (modified)

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
