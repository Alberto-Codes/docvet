# Story 12.1: Enrichment Module Cognitive Complexity Refactoring

Status: done
Branch: `feat/enrichment-12-1-cc-refactoring`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a docvet contributor,
I want the enrichment module's complex functions refactored to cognitive complexity ≤ 15,
so that the codebase exemplifies the maintainability standards SonarQube enforces.

## Acceptance Criteria

1. **Given** `_check_missing_raises` (line 150, CC 20) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all enrichment tests pass without modification
2. **Given** `_check_missing_warns` (line 366, CC 17) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all enrichment tests pass without modification
3. **Given** `_is_dataclass` (line 506, CC 17) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all enrichment tests pass without modification
4. **Given** `_has_self_assignments` (line 652, CC 21) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all enrichment tests pass without modification
5. **Given** `check_enrichment` (line 1163, CC 53) **When** analyzed by SonarQube **Then** CC ≤ 15 **And** all enrichment tests pass without modification
6. **Given** all 5 refactored functions **When** `uv run pytest` is executed **Then** all tests pass with zero failures **And** no functional behavior has changed (identical outputs for identical inputs)

## Tasks / Subtasks

- [x] Task 1: Refactor `check_enrichment` — table-driven dispatch (AC: 5)
  - [x] 1.1 Define `_RULE_DISPATCH` tuple of `(config_attr, check_fn)` pairs
  - [x] 1.2 Replace 10 if/walrus blocks with a loop over `_RULE_DISPATCH`
  - [x] 1.3 Add a test validating every `attr` in `_RULE_DISPATCH` exists on `EnrichmentConfig`
  - [x] 1.4 Verify CC ≤ 15 via `analyze_code_snippet`
  - [x] 1.5 Run `uv run pytest tests/unit/checks/test_enrichment.py` — all enrichment tests pass
- [x] Task 2: Refactor `_check_missing_raises` (AC: 1)
  - [x] 2.1 Extract `_extract_exception_name(node: ast.Raise) -> str | None` helper
  - [x] 2.2 Simplify main function to use helper
  - [x] 2.3 Verify CC ≤ 15 via `analyze_code_snippet`
- [x] Task 3: Refactor `_has_self_assignments` (AC: 4)
  - [x] 3.1 Extract `_find_init_method(node: ast.ClassDef) -> ast.FunctionDef | None` helper
  - [x] 3.2 Extract `_has_self_attribute_target(node: ast.AST) -> bool` helper
  - [x] 3.3 Simplify main function to use helpers
  - [x] 3.4 Verify CC ≤ 15 via `analyze_code_snippet`
- [x] Task 4: Refactor `_check_missing_warns` (AC: 2)
  - [x] 4.1 Extract `_is_warn_call(node: ast.Call) -> bool` helper
  - [x] 4.2 Simplify main function to use helper
  - [x] 4.3 Verify CC ≤ 15 via `analyze_code_snippet`
- [x] Task 5: Refactor `_is_dataclass` (AC: 3)
  - [x] 5.1 Extract `_decorator_matches(dec: ast.expr, name: str) -> bool` helper
  - [x] 5.2 Simplify `_is_dataclass` to use helper
  - [x] 5.3 Verify CC ≤ 15 via `analyze_code_snippet`
- [x] Task 6: Full regression suite (AC: 6)
  - [x] 6.1 Run `uv run pytest` — all tests pass (730 passed, 1 skipped)
  - [x] 6.2 Run `uv run ruff check .` — zero violations
  - [x] 6.3 Run `uv run ruff format --check .` — zero format issues
  - [x] 6.4 Run `uv run ty check` — zero type errors

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | All existing `test_check_missing_raises_*` tests (208 enrichment tests pass unmodified); SonarQube `analyze_code_snippet` returns 0 CC issues | PASS |
| 2 | All existing `test_check_missing_warns_*` tests (208 enrichment tests pass unmodified); SonarQube `analyze_code_snippet` returns 0 CC issues | PASS |
| 3 | All existing `test_is_dataclass_*` tests (208 enrichment tests pass unmodified); SonarQube `analyze_code_snippet` returns 0 CC issues | PASS |
| 4 | All existing `test_has_self_assignments_*` tests (208 enrichment tests pass unmodified); SonarQube `analyze_code_snippet` returns 0 CC issues | PASS |
| 5 | All existing `test_check_enrichment_*` tests + `test_rule_dispatch_attrs_exist_on_enrichment_config`; SonarQube `analyze_code_snippet` returns 0 CC issues | PASS |
| 6 | Full suite: 730 passed, 1 skipped; ruff check 0 violations; ruff format 0 issues; ty check 0 errors | PASS |

## Dev Notes

### Refactoring Strategy Per Function

**`check_enrichment` (CC 53 → ≤ 15) — HIGHEST PRIORITY, do first:**

The orchestrator has 10 sequential `if config.X: if f := _check_Y(...): findings.append(f)` blocks. Each block adds +5 CC (if + walrus). The fix is table-driven dispatch:

```python
_RULE_DISPATCH: tuple[tuple[str, Callable], ...] = (
    ("require_raises", _check_missing_raises),
    ("require_yields", _check_missing_yields),
    ("require_receives", _check_missing_receives),
    ("require_warns", _check_missing_warns),
    ("require_other_parameters", _check_missing_other_parameters),
    ("require_attributes", _check_missing_attributes),
    ("require_typed_attributes", _check_missing_typed_attributes),
    ("require_examples", _check_missing_examples),
    ("require_cross_references", _check_missing_cross_references),
    ("prefer_fenced_code_blocks", _check_prefer_fenced_code_blocks),
)
```

Then the loop body becomes:
```python
for attr, check_fn in _RULE_DISPATCH:
    if getattr(config, attr):
        if f := check_fn(symbol, sections, node_index, config, file_path):
            findings.append(f)
```

This collapses CC from ~53 to ~5 (loop + getattr + walrus + two ifs).

**Safety net:** `getattr(config, attr)` is stringly-typed — a typo in `_RULE_DISPATCH` fails silently. Add one test that asserts every `attr` in `_RULE_DISPATCH` is a valid attribute on `EnrichmentConfig`. This is the only new test in this story.

**`_has_self_assignments` (CC 21 → ≤ 15):**

Two sources of complexity: (1) finding `__init__` in class body, (2) two assignment patterns (`ast.Assign` with multiple targets + `ast.AnnAssign`). Extract:
- `_find_init_method`: linear scan of `node.body` for `__init__`
- `_has_self_attribute_target`: check if an AST node is a `self.*` assignment target

**`_check_missing_raises` (CC 20 → ≤ 15):**

The nested isinstance chains for extracting exception names from `ast.Raise.exc` add CC. Extract a `_extract_exception_name(exc: ast.expr) -> str | None` helper that handles Name, Call(Name), Call(Attribute), and Attribute patterns.

**`_check_missing_warns` (CC 17 → ≤ 15):**

The two warn-call detection patterns (`warnings.warn(...)` and bare `warn(...)`) with nested isinstance checks add CC. Extract `_is_warn_call(node: ast.Call) -> bool`.

**`_is_dataclass` (CC 17 → ≤ 15):**

Three decorator patterns (Name, Attribute, Call wrapping Name or Attribute) can be unified. Extract `_decorator_matches(dec: ast.expr, name: str) -> bool` that handles all three forms. This helper is reusable for `_is_namedtuple` and similar checks, but only refactor what's needed — don't gold-plate.

### Critical Constraints

- **Pure refactoring** — zero behavioral changes. Identical inputs must produce identical outputs.
- **No existing test modifications** — all 208 enrichment tests must pass as-is. If a test fails, the refactoring is wrong. One new test is permitted: `_RULE_DISPATCH` attribute validation.
- **Helper functions stay private** — prefix with `_`, no additions to `__all__`.
- **All helpers need docstrings** — follow Google-style, match existing patterns in the file.
- **`from __future__ import annotations`** — already present at file top.
- **Verify CC with SonarQube** — use `mcp__sonarqube__analyze_code_snippet` with `projectKey: "docvet"` after each function refactor for immediate feedback. The SonarQube dashboard scan on `develop` lags behind local changes.

### File Scope

| File | Action |
|------|--------|
| `src/docvet/checks/enrichment.py` | Refactor 5 functions, add ~4-5 small helper functions |

**No other files should be modified.** Tests, config, CLI — all untouched.

### Existing Module Structure

`enrichment.py` (1245 lines) layout:
- Lines 1-53: Module docstring, imports, section header constants
- Lines 55-142: Shared helpers (`_parse_sections`, `_extract_section_content`, `_build_node_index`)
- Lines 144-1155: 10 `_check_*` rule functions + class-type helpers (`_is_dataclass`, `_is_protocol`, `_is_enum`, etc.)
- Lines 1157-1245: Public orchestrator `check_enrichment`

New helpers should be placed immediately above the function they serve (same pattern as existing helpers like `_XREF_*` patterns above `_check_missing_cross_references`).

### Test Suite Context

- **208 unit tests** in `tests/unit/checks/test_enrichment.py`
- Tests import private functions directly (e.g., `_check_missing_raises`, `_is_dataclass`, `_has_self_assignments`)
- Tests call individual rule functions with constructed `Symbol` objects and `EnrichmentConfig` instances
- The `check_enrichment` orchestrator is tested end-to-end with source strings and full config
- No integration tests for enrichment — all unit-level

### Project Structure Notes

- Single file: `src/docvet/checks/enrichment.py` — all changes contained here
- No new files needed — helpers are private to the module
- No dependency changes — pure stdlib AST refactoring

### References

- [Source: _bmad-output/planning-artifacts/epics-housekeeping.md#Story 12.1]
- [Source: src/docvet/checks/enrichment.py — lines 150, 366, 506, 652, 1163]
- [Source: .claude/rules/sonarqube.md — CC threshold 15, S3776 dominant finding]
- [Source: SonarQube MCP — 5 confirmed S3776 issues in enrichment.py]
- [Source: tests/unit/checks/test_enrichment.py — 208 tests]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Refactored 5 functions in `enrichment.py` to reduce cognitive complexity below SonarQube threshold (15)
- `check_enrichment`: CC 53 → ~5 via table-driven `_RULE_DISPATCH` replacing 10 if/walrus blocks
- `_check_missing_raises`: CC 20 → ~10 via `_extract_exception_name` helper
- `_has_self_assignments`: CC 21 → ~7 via `_find_init_method` and `_has_self_attribute_target` helpers
- `_check_missing_warns`: CC 17 → ~9 via `_is_warn_call` helper
- `_is_dataclass`: CC 17 → ~1 via `_decorator_matches` helper (now a one-liner with `any()`)
- Added 1 new safety-net test: `test_rule_dispatch_attrs_exist_on_enrichment_config`
- All 208 existing enrichment tests pass unmodified — zero behavioral changes
- Full suite: 730 passed, 1 skipped; ruff 0 violations; ruff format 0 issues; ty 0 errors
- Code review: narrowed `_has_self_attribute_target` type hint from `ast.AST` to `ast.Assign | ast.AnnAssign`; added bidirectional dispatch test `test_all_config_toggle_fields_are_in_rule_dispatch`
- Post-review suite: 731 passed, 1 skipped

### Change Log

- 2026-02-22: Refactored 5 high-CC functions in enrichment.py with 6 new private helpers; added dispatch table safety-net test
- 2026-02-22: Code review fixes — narrowed type hint, added bidirectional dispatch safety-net test

### File List

- `src/docvet/checks/enrichment.py` — Refactored 5 functions, added 6 helpers (`_extract_exception_name`, `_find_init_method`, `_has_self_attribute_target`, `_is_warn_call`, `_decorator_matches`, `_RULE_DISPATCH`), added `Callable` import; narrowed `_has_self_attribute_target` type hint
- `tests/unit/checks/test_enrichment.py` — Added `_RULE_DISPATCH` import, `test_rule_dispatch_attrs_exist_on_enrichment_config`, and `test_all_config_toggle_fields_are_in_rule_dispatch` tests
