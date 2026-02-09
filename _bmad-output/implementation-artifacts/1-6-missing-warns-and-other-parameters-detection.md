# Story 1.6: Missing Warns and Other Parameters Detection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect functions that call `warnings.warn()` without a `Warns:` section and functions with `**kwargs` without an `Other Parameters:` section,
so that my docstrings fully describe warning behavior and extra keyword arguments.

## Acceptance Criteria

1. **Given** a function calling `warnings.warn()` with no `Warns:` section in its docstring, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-warns"`, `category="required"` (AC: #1)

2. **Given** a function calling `warnings.warn()` with a `Warns:` section present, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-warns` (AC: #2)

3. **Given** `config.require_warns = False`, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-warns` (AC: #3)

4. **Given** a function with `**kwargs` parameter and no `Other Parameters:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-other-parameters"`, `category="recommended"` (AC: #4)

5. **Given** a function with `**kwargs` and an `Other Parameters:` section present, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-other-parameters` (AC: #5)

6. **Given** `config.require_other_parameters = False`, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-other-parameters` (AC: #6)

7. **Given** a function that calls `warnings.warn()` via a qualified path (e.g., `warnings.warn(...)`), **when** `check_enrichment` is called, **then** it detects the `warn` call via AST `Call` node inspection (AC: #7)

8. **Given** all 5 function-level rules enabled with a function that triggers none of them, **when** `check_enrichment` is called, **then** it returns zero findings for that function (AC: #8)

## Tasks / Subtasks

- [x] Task 1: Implement `_check_missing_warns` private function (AC: #1, #2, #7)
  - [x] 1.1: Write function with uniform signature `_check_missing_warns(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 1.2: Guard on `symbol.kind in ("function", "method")` — return `None` for class/module symbols
  - [x] 1.3: Retrieve function node via `node_index.get(symbol.line)` — return `None` if missing
  - [x] 1.4: Early return `None` if `"Warns" in sections` (section already documented)
  - [x] 1.5: Scope-aware walk of node body to find `ast.Call` nodes where the callee is `warnings.warn` (handle both `warnings.warn()` and bare `warn()` after `from warnings import warn`)
  - [x] 1.6: If any `warnings.warn()` calls found, construct `Finding` with `rule="missing-warns"`, `category="required"`
  - [x] 1.7: Add docstring following project conventions

- [x] Task 2: Implement `_check_missing_other_parameters` private function (AC: #4, #5)
  - [x] 2.1: Write function with uniform signature `_check_missing_other_parameters(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 2.2: Guard on `symbol.kind in ("function", "method")` — return `None` for class/module symbols
  - [x] 2.3: Retrieve function node via `node_index.get(symbol.line)` — return `None` if missing
  - [x] 2.4: Early return `None` if `"Other Parameters" in sections` (section already documented)
  - [x] 2.5: Check `node.args.kwarg is not None` — this is the `**kwargs` parameter
  - [x] 2.6: If `**kwargs` found, construct `Finding` with `rule="missing-other-parameters"`, `category="recommended"`
  - [x] 2.7: Add docstring following project conventions

- [x] Task 3: Wire both rules into `check_enrichment` orchestrator (AC: #3, #6, #8)
  - [x] 3.1: Add `config.require_warns` gate before `_check_missing_warns` dispatch (taxonomy-table order: after `missing-receives`)
  - [x] 3.2: Add `config.require_other_parameters` gate before `_check_missing_other_parameters` dispatch (taxonomy-table order: after `missing-warns`)
  - [x] 3.3: Use walrus operator pattern `if f := _check_missing_warns(...)` consistent with existing dispatch

- [x] Task 4: Write unit tests (AC: #1-#8)
  - [x] 4.1: `test_missing_warns_when_function_calls_warn_without_section_returns_finding` — AC #1
  - [x] 4.2: `test_missing_warns_when_warns_section_present_returns_none` — AC #2
  - [x] 4.3: `test_missing_warns_when_no_warn_calls_returns_none`
  - [x] 4.4: `test_missing_warns_when_qualified_warnings_warn_returns_finding` — AC #7
  - [x] 4.5: `test_missing_warns_when_bare_warn_import_returns_finding`
  - [x] 4.6: `test_missing_warns_when_node_index_missing_returns_none` (module symbol)
  - [x] 4.7: `test_missing_warns_when_class_symbol_returns_none`
  - [x] 4.8: `test_missing_warns_when_nested_warn_call_returns_none` (scope boundary)
  - [x] 4.9: `test_missing_warns_when_unrelated_function_call_returns_none` (e.g., `logging.warn()` should NOT trigger)
  - [x] 4.10: `test_missing_other_parameters_when_kwargs_without_section_returns_finding` — AC #4
  - [x] 4.11: `test_missing_other_parameters_when_section_present_returns_none` — AC #5
  - [x] 4.12: `test_missing_other_parameters_when_no_kwargs_returns_none`
  - [x] 4.13: `test_missing_other_parameters_when_node_index_missing_returns_none`
  - [x] 4.14: `test_missing_other_parameters_when_class_symbol_returns_none`
  - [x] 4.15: `test_check_enrichment_when_warns_disabled_returns_no_finding` — AC #3
  - [x] 4.16: `test_check_enrichment_when_other_parameters_disabled_returns_no_finding` — AC #6
  - [x] 4.17: `test_check_enrichment_when_all_rules_disabled_returns_empty` (update existing to disable all 5 rules)
  - [x] 4.18: `test_check_enrichment_when_complete_module_still_returns_empty` (regression)

- [x] Task 5: Run quality gates and verify all pass
  - [x] 5.1: `uv run ruff check .` — All checks pass
  - [x] 5.2: `uv run ruff format --check .` — All files formatted
  - [x] 5.3: `uv run ty check` — All type checks pass
  - [x] 5.4: `uv run pytest tests/unit/checks/ -v` — All enrichment tests pass
  - [x] 5.5: `uv run pytest` — Full suite passes, 0 regressions

## Dev Notes

### Scope

This story adds two enrichment rules (`missing-warns`, `missing-other-parameters`) and wires them into the existing `check_enrichment` orchestrator. Follows the exact pattern established in Stories 1.4 and 1.5.

Two new functions in `checks/enrichment.py`:
1. **`_check_missing_warns`** — Detects functions calling `warnings.warn()` but no `Warns:` section
2. **`_check_missing_other_parameters`** — Detects functions with `**kwargs` but no `Other Parameters:` section

Plus orchestrator modifications to dispatch both rules with config gating.

**Key differences from previous rules:**

| Aspect | `missing-warns` | `missing-other-parameters` |
|--------|-----------------|---------------------------|
| Detection | Body walk for `ast.Call` nodes | Signature only: `node.args.kwarg` |
| Category | `"required"` | `"recommended"` |
| Complexity | Medium (call site analysis) | Low (signature inspection) |
| Walk needed | Yes — scope-aware walk | **No** — just check `node.args.kwarg` |

`missing-other-parameters` is the simplest rule so far — it only inspects the function signature, no body walk needed. It checks `node.args.kwarg is not None` to detect the `**kwargs` parameter.

`missing-warns` requires a scope-aware walk to find `warnings.warn()` calls. This is similar to `missing-raises` but detects `ast.Call` nodes instead of `ast.Raise` nodes.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | MODIFIED — Add `_check_missing_warns()`, `_check_missing_other_parameters()`, wire into orchestrator |
| `tests/unit/checks/test_enrichment.py` | MODIFIED — Add tests for both rules and orchestrator integration |

No new files. No fixture files needed (inline test sources are sufficient, matching previous story patterns).

### Architecture Constraints

**Uniform `_check_*` Signature (Decision 1):**
```python
def _check_missing_warns(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
```
- Config gating lives in the orchestrator, NOT inside `_check_*`
- Functions are pure detection logic — zero config awareness
- Returns `Finding | None` (not a list)

**Taxonomy-Table Order:**
Functions must be defined AND dispatched in this order:
1. `_check_missing_raises` (exists — line 108)
2. `_check_missing_yields` (exists — line 184)
3. `_check_missing_receives` (exists — line 247)
4. `_check_missing_warns` — **NEW**
5. `_check_missing_other_parameters` — **NEW**
6. (future: `_check_missing_attributes`, `_check_missing_typed_attributes`, ...)

### AST Detection: `missing-warns`

Detect `ast.Call` nodes where the callee is `warnings.warn`:

**Pattern 1 — Qualified call `warnings.warn(...)`:**
```python
# AST: Call(func=Attribute(value=Name(id='warnings'), attr='warn'))
isinstance(child, ast.Call)
and isinstance(child.func, ast.Attribute)
and isinstance(child.func.value, ast.Name)
and child.func.value.id == "warnings"
and child.func.attr == "warn"
```

**Pattern 2 — Bare call after `from warnings import warn`:**
```python
# AST: Call(func=Name(id='warn'))
isinstance(child, ast.Call)
and isinstance(child.func, ast.Name)
and child.func.id == "warn"
```

**IMPORTANT: Do NOT match `logging.warn()` or other `*.warn()` calls.**
- Pattern 1 explicitly checks `child.func.value.id == "warnings"` — other modules won't match
- Pattern 2 matches bare `warn()` calls — this is correct because a bare `warn()` in scope would come from `from warnings import warn`. Other modules' `warn` would be qualified (e.g., `logging.warn`)

**Scope-aware walk pattern** (same as `_check_missing_raises`):
```python
stack = list(ast.iter_child_nodes(node))
while stack:
    child = stack.pop()
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        continue  # Don't descend into nested scopes
    # ... check for warnings.warn() call ...
    stack.extend(ast.iter_child_nodes(child))
```

**Finding message format:**
```
Function '{symbol.name}' calls warnings.warn() but has no Warns: section
```

### AST Detection: `missing-other-parameters`

Detect `**kwargs` parameter via function signature inspection — **NO body walk needed**.

```python
node = node_index.get(symbol.line)
if node is None:
    return None
# Check for **kwargs parameter
if node.args.kwarg is not None:
    return Finding(...)
```

`node.args.kwarg` is an `ast.arg` node representing the `**kwargs` parameter. It's `None` when the function has no `**kwargs`.

**Finding message format:**
```
Function '{symbol.name}' accepts **kwargs but has no Other Parameters: section
```

**Note:** The `category` for `missing-other-parameters` is `"recommended"` (not `"required"` like all previous rules). This is the first recommended-category rule. Per the epics spec and architecture, `**kwargs` documentation is a best practice, not a mandatory requirement.

### What NOT to Do

- Do NOT put config gating inside `_check_missing_warns` or `_check_missing_other_parameters` — the orchestrator handles it
- Do NOT walk the raw `tree` in `_check_*` — use `node_index.get(symbol.line)` to get the node
- Do NOT use `ast.walk(node)` — use the scope-aware iterative walk pattern from Story 1.4 (for `missing-warns` only)
- Do NOT match `logging.warn()` or any `*.warn()` other than `warnings.warn()` — only the stdlib `warnings` module's `warn()` triggers the rule
- Do NOT catch exceptions in `_check_*` functions — correctness through design (Decision 5)
- Do NOT use dynamic strings for `rule` or `category` — use literals
- Do NOT return a list from `_check_*` — return `Finding | None`
- Do NOT do a body walk for `missing-other-parameters` — it only needs `node.args.kwarg`
- Do NOT forget `missing-other-parameters` uses `category="recommended"` (not `"required"`)

### Testing Strategy

**Test through `check_enrichment` for orchestrator integration:**
- Config gating tests (AC #3, #6)
- All-rules-disabled test (AC #8 — update existing test to disable all 5 active rules)
- Complete module regression (zero findings)

**Direct `_check_missing_warns` tests for detection logic:**
- Function with `warnings.warn()` qualified call (AC #1, #7)
- Function with bare `warn()` after import
- Function with Warns section present (AC #2)
- No warn calls (returns None)
- Module/class symbol rejection
- Nested scope boundary (warn in nested function not attributed to outer)
- Unrelated `*.warn()` call (e.g., `logging.warn()` — should NOT trigger)

**Direct `_check_missing_other_parameters` tests:**
- Function with `**kwargs` and no section (AC #4)
- Function with `**kwargs` and section present (AC #5)
- Function without `**kwargs` (returns None)
- Module/class symbol rejection
- Node index missing (returns None)

**Test naming convention:**
- `test_{rule_id}_when_{condition}_returns_{expected}` for direct rule tests
- `test_check_enrichment_when_{condition}_{expected}` for orchestrator tests

**`_make_symbol_and_index` helper:**
Existing test helper at `tests/unit/checks/test_enrichment.py` — reuse for new rule tests. It:
- Parses source via `ast.parse()`
- Calls `get_documented_symbols(tree)` — takes only `tree` (NOT `source, tree`)
- Builds node index
- Returns first non-module symbol + node_index + tree
- Asserts docstring is not None

### Previous Story Intelligence

**From Story 1.5 (Missing Yields and Receives):**
- Scope-aware walk pattern established and validated by code review
- `_make_symbol_and_index` test helper exists — reuse for new rule tests
- Orchestrator uses walrus operator `if f := _check_*(...)` pattern
- `get_documented_symbols(tree)` takes only `tree` (NOT `source, tree`)
- Code review caught false positives with nested scopes — scope-aware walk prevents this
- `config` param is unused in `_check_*` but required by uniform signature (Decision 1)
- Test that disables "all rules" must be updated to include the 2 new rules (total: 5 active rules)
- 20 tests added in 1.5 — current total: 55 enrichment tests, 257 overall. Expect ~18 more from this story
- Code review found missing scope boundary and symbol guard tests — include these proactively

**From Story 1.4 (Missing Raises and Orchestrator):**
- `_check_missing_raises` collects exception names for evidence — `_check_missing_warns` does NOT need evidence collection (just detect presence of warn calls)
- Scope-aware walk: iterative stack with `ast.iter_child_nodes`, skip nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef`
- `[L3] Unnecessary f prefix on non-interpolated string continuation` — avoid this in new functions

**From Story 1.3 (Section Parser and Node Index):**
- `_parse_sections` returns `set[str]` — check `"Warns" in sections` and `"Other Parameters" in sections`
- `_build_node_index` returns `dict[int, _NodeT]` where `_NodeT = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef`

**From Story 1.2 (Finding Dataclass):**
- `Finding(file=, line=, symbol=, rule=, message=, category=)` — all 6 fields, frozen
- `__post_init__` validates category is `"required"` or `"recommended"`

### File Structure Requirements

**`enrichment.py` after this story:**
```python
"""Enrichment check for docstring completeness. ..."""

from __future__ import annotations

import ast
import re

from docvet.ast_utils import Symbol, get_documented_symbols
from docvet.checks import Finding
from docvet.config import EnrichmentConfig

# Constants (existing)
_SECTION_HEADERS = frozenset({...})
_SECTION_PATTERN = re.compile(...)

# Type alias (existing)
_NodeT = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef

# Shared helpers (existing)
def _parse_sections(...): ...
def _build_node_index(...): ...

# Rule functions (taxonomy-table order)
def _check_missing_raises(...): ...           # existing (line 108)
def _check_missing_yields(...): ...           # existing (line 184)
def _check_missing_receives(...): ...         # existing (line 247)
def _check_missing_warns(...): ...            # NEW — insert after line 321
def _check_missing_other_parameters(...): ... # NEW — insert after _check_missing_warns

# Public orchestrator (always last)
def check_enrichment(...): ...                # MODIFIED — add dispatch for 2 new rules
```

**Orchestrator after this story:**
```python
def check_enrichment(source, tree, config, file_path):
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    findings: list[Finding] = []

    for symbol in symbols:
        if not symbol.docstring:
            continue
        sections = _parse_sections(symbol.docstring)

        if config.require_raises:
            if f := _check_missing_raises(symbol, sections, node_index, config, file_path):
                findings.append(f)
        if config.require_yields:
            if f := _check_missing_yields(symbol, sections, node_index, config, file_path):
                findings.append(f)
        if config.require_receives:
            if f := _check_missing_receives(symbol, sections, node_index, config, file_path):
                findings.append(f)
        if config.require_warns:
            if f := _check_missing_warns(symbol, sections, node_index, config, file_path):
                findings.append(f)
        if config.require_other_parameters:
            if f := _check_missing_other_parameters(symbol, sections, node_index, config, file_path):
                findings.append(f)
        # Future rules dispatched here in taxonomy-table order

    return findings
```

### Library/Framework Requirements

**No new dependencies** — stdlib only:
- `ast` — Already imported
- No new imports needed beyond existing `Symbol`, `get_documented_symbols`, `Finding`, `EnrichmentConfig`

### Project Structure Notes

- Both new `_check_*` functions go in `src/docvet/checks/enrichment.py` after `_check_missing_receives` (line 321) and before the orchestrator section
- New tests go in `tests/unit/checks/test_enrichment.py` in new comment-separated sections
- No new files needed
- No fixture files needed — inline test sources are sufficient
- `complete_module.py` fixture does NOT contain `warnings.warn()` or `**kwargs`, so it naturally produces zero findings for the new rules (no fixture changes needed)
- Config fields `require_warns` and `require_other_parameters` already exist in `EnrichmentConfig` (config.py line 32 and 34) — no config changes needed

### FRs Covered

- FR4: Detect missing Warns section on functions calling `warnings.warn()`
- FR5: Detect missing Other Parameters section on functions with `**kwargs`
- FR32: Analyze functions for warnings calls and kwargs parameters
- NFR5: Zero false positives on well-documented code
- NFR10: Each rule independently testable

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1] — Private function per rule with uniform signature
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — Line-based node index for O(1) lookup
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 4] — Finding message format conventions
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] — No try/except, defensive by design
- [Source: _bmad-output/planning-artifacts/architecture.md#AST Inspection Patterns] — ast.walk for body traversal
- [Source: _bmad-output/planning-artifacts/architecture.md#Rule → Internal Function Mapping] — `missing-warns` uses body walk, `missing-other-parameters` uses signature only
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6] — BDD acceptance criteria
- [Source: src/docvet/checks/enrichment.py:108-181] — Existing `_check_missing_raises` (pattern to follow for `_check_missing_warns`)
- [Source: src/docvet/checks/enrichment.py:247-321] — Existing `_check_missing_receives` (insertion point: new rules go after line 321)
- [Source: src/docvet/checks/enrichment.py:329-377] — Existing `check_enrichment` orchestrator (modify dispatch block at lines 360-375)
- [Source: src/docvet/checks/enrichment.py:53-74] — `_parse_sections` helper
- [Source: src/docvet/checks/enrichment.py:80-100] — `_build_node_index` helper
- [Source: src/docvet/checks/enrichment.py:77] — `_NodeT` type alias
- [Source: src/docvet/config.py:32] — `require_warns: bool = True` (already exists)
- [Source: src/docvet/config.py:34] — `require_other_parameters: bool = True` (already exists)
- [Source: tests/fixtures/complete_module.py] — Fixture with complete docstrings (zero findings — no warns/kwargs patterns present)
- [Source: _bmad-output/implementation-artifacts/1-5-missing-yields-and-receives-detection.md] — Previous story patterns, learnings, and code review insights
- [Source: _bmad-output/project-context.md#AST Utilities Rules] — Symbol dataclass shape and `get_documented_symbols` API

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Type checker initially flagged `node.args.kwarg` on `ClassDef` — added `isinstance(node, ast.ClassDef)` guard to narrow the union type and satisfy `ty check`

### Completion Notes List

- Implemented `_check_missing_warns` with scope-aware walk detecting both `warnings.warn()` (qualified) and bare `warn()` (from import) patterns. Correctly excludes `logging.warn()` and other unrelated `*.warn()` calls
- Implemented `_check_missing_other_parameters` as the simplest rule yet — signature-only inspection via `node.args.kwarg`, no body walk needed. First `category="recommended"` rule in the codebase
- Wired both rules into `check_enrichment` orchestrator with config gating in taxonomy-table order (after `missing-receives`)
- Updated existing "all rules disabled" test to cover all 5 active rules
- Added 16 new tests (9 for warns, 5 for other-parameters, 2 orchestrator config tests), bringing enrichment test count from 55 to 71 and overall from 257 to 273
- All quality gates pass: ruff check, ruff format, ty check, full test suite (273/273)

### Change Log

- 2026-02-08: Implemented missing-warns and missing-other-parameters detection rules with full test coverage (Story 1.6)
- 2026-02-08: Code review fixes — added 3 tests (bare warn() false positive edge case, nested class scope boundary, async kwargs), added type-narrowing comment to ClassDef guard. Test count: 74 enrichment, 276 overall.

### File List

- `src/docvet/checks/enrichment.py` (MODIFIED) — Added `_check_missing_warns()`, `_check_missing_other_parameters()`, wired into orchestrator; added type-narrowing comment
- `tests/unit/checks/test_enrichment.py` (MODIFIED) — Added 19 new tests for both rules and orchestrator integration, updated all-rules-disabled test
