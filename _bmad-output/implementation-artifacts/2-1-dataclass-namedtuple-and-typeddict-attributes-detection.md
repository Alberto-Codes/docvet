# Story 2.1: Dataclass, NamedTuple, and TypedDict Attributes Detection

Status: done

## Story

As a developer,
I want to detect dataclasses, NamedTuples, and TypedDicts that lack an `Attributes:` section,
so that users of my data structures can see all fields documented in one place.

## Acceptance Criteria

1. **Given** a class decorated with `@dataclass` and a docstring with no `Attributes:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`, and a message naming the class (AC: #1)

2. **Given** a class decorated with `@dataclasses.dataclass` (qualified form), **when** `check_enrichment` is called, **then** it detects the dataclass and applies the same rule (AC: #2)

3. **Given** a class decorated with `@dataclass(frozen=True)` (decorator with arguments), **when** `check_enrichment` is called, **then** it detects the dataclass via `ast.Call` node inspection (AC: #3)

4. **Given** a class inheriting from `NamedTuple` (e.g., `class Foo(NamedTuple):`), **when** `check_enrichment` is called and the docstring has no `Attributes:` section, **then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"` (AC: #4)

5. **Given** a class inheriting from `typing.NamedTuple` (qualified base class), **when** `check_enrichment` is called, **then** it detects the NamedTuple via `ast.Attribute` base class inspection (AC: #5)

6. **Given** a class inheriting from `TypedDict`, **when** `check_enrichment` is called and the docstring has no `Attributes:` section, **then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"` (AC: #6)

7. **Given** a dataclass with a docstring containing an `Attributes:` section, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-attributes` on that class (AC: #7)

8. **Given** `config.require_attributes = False`, **when** `check_enrichment` is called on any class-like construct missing `Attributes:`, **then** it returns zero findings for `missing-attributes` (AC: #8)

9. **Given** a dataclass with no docstring at all, **when** `check_enrichment` is called, **then** it returns zero findings (undocumented symbols skipped) (AC: #9)

10. **Given** the `_is_dataclass`, `_is_namedtuple`, and `_is_typeddict` helper functions, **when** tested directly with AST nodes, **then** each correctly identifies its construct type and returns `False` for non-matching nodes (AC: #10)

## Tasks / Subtasks

- [x] Task 1: Implement `_is_dataclass` helper function (AC: #1, #2, #3, #10)
  - [x] 1.1: Write `_is_dataclass(node: ast.ClassDef) -> bool`
  - [x] 1.2: Check `node.decorator_list` for `ast.Name(id="dataclass")` — simple `@dataclass`
  - [x] 1.3: Check for `ast.Attribute(attr="dataclass")` — qualified `@dataclasses.dataclass`
  - [x] 1.4: Check for `ast.Call` where `func` matches patterns above — `@dataclass(frozen=True)`
  - [x] 1.5: Return `False` for non-matching nodes

- [x] Task 2: Implement `_is_namedtuple` helper function (AC: #4, #5, #10)
  - [x] 2.1: Write `_is_namedtuple(node: ast.ClassDef) -> bool`
  - [x] 2.2: Check `node.bases` for `ast.Name(id="NamedTuple")`
  - [x] 2.3: Check for `ast.Attribute(attr="NamedTuple")` — `typing.NamedTuple`
  - [x] 2.4: Return `False` for non-matching nodes

- [x] Task 3: Implement `_is_typeddict` helper function (AC: #6, #10)
  - [x] 3.1: Write `_is_typeddict(node: ast.ClassDef) -> bool`
  - [x] 3.2: Check `node.bases` for `ast.Name(id="TypedDict")`
  - [x] 3.3: Check for `ast.Attribute(attr="TypedDict")` — `typing.TypedDict`
  - [x] 3.4: Return `False` for non-matching nodes

- [x] Task 4: Implement `_check_missing_attributes` rule function (AC: #1-#9)
  - [x] 4.1: Write function with uniform signature `_check_missing_attributes(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 4.2: Guard: return `None` if `symbol.kind != "class"` (only class symbols for this story)
  - [x] 4.3: Early return `None` if `"Attributes" in sections`
  - [x] 4.4: Retrieve class node via `node_index.get(symbol.line)` — return `None` if missing
  - [x] 4.5: Guard: return `None` if not `isinstance(node, ast.ClassDef)` (type narrowing for `ty`)
  - [x] 4.6: Branch 1: `if _is_dataclass(node):` return Finding
  - [x] 4.7: Branch 2: `if _is_namedtuple(node):` return Finding
  - [x] 4.8: Branch 3: `if _is_typeddict(node):` return Finding
  - [x] 4.9: Return `None` if no branch matches (plain class and module branches are Story 2.2)
  - [x] 4.10: Add docstring documenting all 3 branches and first-match-wins semantics

- [x] Task 5: Wire `_check_missing_attributes` into `check_enrichment` orchestrator (AC: #8)
  - [x] 5.1: Add `config.require_attributes` gate before dispatch (taxonomy-table order: after `missing-other-parameters`)
  - [x] 5.2: Use walrus operator pattern consistent with existing dispatch
  - [x] 5.3: Update the `# Future rules dispatched here` comment to reflect remaining rules

- [x] Task 6: Update `complete_module.py` fixture with a dataclass that has `Attributes:` section
  - [x] 6.1: Add a `@dataclass` class with fields and a complete `Attributes:` section
  - [x] 6.2: Verify fixture produces zero findings for `missing-attributes`

- [x] Task 7: Write unit tests for helper functions (AC: #10)
  - [x] 7.1: `test_is_dataclass_when_simple_decorator_returns_true`
  - [x] 7.2: `test_is_dataclass_when_qualified_decorator_returns_true`
  - [x] 7.3: `test_is_dataclass_when_call_decorator_returns_true` (`@dataclass(frozen=True)`)
  - [x] 7.4: `test_is_dataclass_when_qualified_call_decorator_returns_true` (`@dataclasses.dataclass(frozen=True)`)
  - [x] 7.5: `test_is_dataclass_when_no_decorator_returns_false`
  - [x] 7.6: `test_is_dataclass_when_other_decorator_returns_false`
  - [x] 7.7: `test_is_namedtuple_when_simple_base_returns_true`
  - [x] 7.8: `test_is_namedtuple_when_qualified_base_returns_true`
  - [x] 7.9: `test_is_namedtuple_when_no_base_returns_false`
  - [x] 7.10: `test_is_namedtuple_when_other_base_returns_false`
  - [x] 7.11: `test_is_typeddict_when_simple_base_returns_true`
  - [x] 7.12: `test_is_typeddict_when_qualified_base_returns_true`
  - [x] 7.13: `test_is_typeddict_when_no_base_returns_false`

- [x] Task 8: Write unit tests for `_check_missing_attributes` (AC: #1-#9)
  - [x] 8.1: `test_missing_attributes_when_dataclass_without_section_returns_finding` — AC #1
  - [x] 8.2: `test_missing_attributes_when_qualified_dataclass_returns_finding` — AC #2
  - [x] 8.3: `test_missing_attributes_when_dataclass_call_returns_finding` — AC #3
  - [x] 8.4: `test_missing_attributes_when_namedtuple_without_section_returns_finding` — AC #4
  - [x] 8.5: `test_missing_attributes_when_qualified_namedtuple_returns_finding` — AC #5
  - [x] 8.6: `test_missing_attributes_when_typeddict_without_section_returns_finding` — AC #6
  - [x] 8.7: `test_missing_attributes_when_attributes_section_present_returns_none` — AC #7
  - [x] 8.8: `test_missing_attributes_when_node_index_missing_returns_none` (module symbol)
  - [x] 8.9: `test_missing_attributes_when_function_symbol_returns_none` (kind guard)
  - [x] 8.10: `test_missing_attributes_when_plain_class_returns_none` (no branch match — deferred to 2.2)

- [x] Task 9: Write orchestrator integration tests (AC: #8, #9)
  - [x] 9.1: `test_check_enrichment_when_attributes_disabled_returns_no_finding` — AC #8
  - [x] 9.2: `test_check_enrichment_when_dataclass_no_docstring_returns_no_finding` — AC #9
  - [x] 9.3: `test_check_enrichment_when_complete_module_still_returns_empty` (regression)
  - [x] 9.4: Update `test_check_enrichment_when_all_rules_disabled_returns_empty` to disable 6 rules

- [x] Task 10: Run quality gates and verify all pass
  - [x] 10.1: `uv run ruff check .` — All checks pass
  - [x] 10.2: `uv run ruff format --check .` — All files formatted
  - [x] 10.3: `uv run ty check` — All type checks pass
  - [x] 10.4: `uv run pytest tests/unit/checks/ -v` — All enrichment tests pass
  - [x] 10.5: `uv run pytest` — Full suite passes (0 regressions)

## Dev Notes

### Scope

This story implements the **first 3 branches** of the highest-complexity rule (`missing-attributes`) and wires it into the orchestrator. This is the first rule that inspects **class symbols** (all 5 prior rules inspect function/method symbols only).

New functions in `checks/enrichment.py`:
1. **`_is_dataclass(node: ast.ClassDef) -> bool`** — Detects `@dataclass` decorator in all forms
2. **`_is_namedtuple(node: ast.ClassDef) -> bool`** — Detects `NamedTuple` base class
3. **`_is_typeddict(node: ast.ClassDef) -> bool`** — Detects `TypedDict` base class
4. **`_check_missing_attributes(symbol, sections, node_index, config, file_path) -> Finding | None`** — Dispatches to helpers, first-match-wins

**What this story does NOT implement (deferred to Story 2.2):**
- Branch 4: Plain class with `__init__` self-assignments (`_has_self_assignments`)
- Branch 5: `__init__.py` module-level attributes (`_is_init_module`)

The `_check_missing_attributes` function in this story returns `None` for plain classes and modules — those branches are added in Story 2.2.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | MODIFIED — Add 3 helper functions, `_check_missing_attributes()`, wire into orchestrator |
| `tests/unit/checks/test_enrichment.py` | MODIFIED — Add tests for helpers, rule, and orchestrator |
| `tests/fixtures/complete_module.py` | MODIFIED — Add dataclass with complete `Attributes:` section |

### Architecture Constraints

**Uniform `_check_*` Signature (Decision 1):**
```python
def _check_missing_attributes(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
```
- Config gating lives in the orchestrator, NOT inside `_check_*`
- Returns `Finding | None` (not a list)

**First-Match-Wins Dispatch Order (Architecture Constraint):**
Branches within `_check_missing_attributes` are evaluated in this order — first match wins, no fallthrough:
1. Dataclass (decorator inspection) — **this story**
2. NamedTuple (base class inspection) — **this story**
3. TypedDict (base class inspection) — **this story**
4. Plain class with `__init__` self-assignments — **Story 2.2**
5. `__init__.py` module-level exports — **Story 2.2**

For this story, after branches 1-3 fail, return `None`. Story 2.2 adds branches 4-5 before the final `None`.

**Taxonomy-Table Order:**
`_check_missing_attributes` is defined AND dispatched after `_check_missing_other_parameters`:
```
_check_missing_raises          (exists — line 108)
_check_missing_yields          (exists — line 184)
_check_missing_receives        (exists — line 247)
_check_missing_warns           (exists — line 324)
_check_missing_other_parameters (exists — line 402)
_check_missing_attributes       ← NEW (insert before orchestrator)
```

**Helper Function Placement:**
Helper functions (`_is_dataclass`, `_is_namedtuple`, `_is_typeddict`) go in the "Rule-specific helper functions" section, BEFORE `_check_missing_attributes` and AFTER `_check_missing_other_parameters`.

### AST Detection: Dataclass

Inspect `node.decorator_list` for dataclass decorators:

**Pattern 1 — Simple `@dataclass`:**
```python
isinstance(dec, ast.Name) and dec.id == "dataclass"
```

**Pattern 2 — Qualified `@dataclasses.dataclass`:**
```python
isinstance(dec, ast.Attribute) and dec.attr == "dataclass"
```

**Pattern 3 — Call `@dataclass(frozen=True)` or `@dataclasses.dataclass(frozen=True)`:**
```python
isinstance(dec, ast.Call) and (
    (isinstance(dec.func, ast.Name) and dec.func.id == "dataclass")
    or (isinstance(dec.func, ast.Attribute) and dec.func.attr == "dataclass")
)
```

**Scope note:** Decorator alias detection (e.g., `from dataclasses import dataclass as dc`) is explicitly out of MVP scope.

### AST Detection: NamedTuple

Inspect `node.bases` for NamedTuple base class:

**Pattern 1 — Simple `class Foo(NamedTuple)`:**
```python
isinstance(base, ast.Name) and base.id == "NamedTuple"
```

**Pattern 2 — Qualified `class Foo(typing.NamedTuple)`:**
```python
isinstance(base, ast.Attribute) and base.attr == "NamedTuple"
```

### AST Detection: TypedDict

Inspect `node.bases` for TypedDict base class (same patterns as NamedTuple):

**Pattern 1 — Simple `class Foo(TypedDict)`:**
```python
isinstance(base, ast.Name) and base.id == "TypedDict"
```

**Pattern 2 — Qualified `class Foo(typing.TypedDict)`:**
```python
isinstance(base, ast.Attribute) and base.attr == "TypedDict"
```

### Finding Message Format

Per architecture Decision 4 (missing-section rules):
```
{ConstructType} '{symbol.name}' has no Attributes: section
```

Examples:
- `Dataclass 'ValidationResult' has no Attributes: section`
- `NamedTuple 'Point' has no Attributes: section`
- `TypedDict 'Options' has no Attributes: section`

The construct type prefix distinguishes which branch matched, aiding developer comprehension.

### `_check_missing_attributes` Internal Structure

```python
def _check_missing_attributes(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    # Only class symbols (for this story — module branch added in 2.2)
    if symbol.kind != "class":
        return None

    if "Attributes" in sections:
        return None

    node = node_index.get(symbol.line)
    if node is None or not isinstance(node, ast.ClassDef):
        return None

    # Branch 1: Dataclass
    if _is_dataclass(node):
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=symbol.name,
            rule="missing-attributes",
            message=f"Dataclass '{symbol.name}' has no Attributes: section",
            category="required",
        )

    # Branch 2: NamedTuple
    if _is_namedtuple(node):
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=symbol.name,
            rule="missing-attributes",
            message=f"NamedTuple '{symbol.name}' has no Attributes: section",
            category="required",
        )

    # Branch 3: TypedDict
    if _is_typeddict(node):
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=symbol.name,
            rule="missing-attributes",
            message=f"TypedDict '{symbol.name}' has no Attributes: section",
            category="required",
        )

    # Branches 4-5 (plain class, __init__.py module) added in Story 2.2
    return None
```

### What NOT to Do

- Do NOT put config gating inside `_check_missing_attributes` — the orchestrator handles it
- Do NOT walk the raw `tree` — use `node_index.get(symbol.line)` to get the class node
- Do NOT detect decorator aliases (`from dataclasses import dataclass as dc`) — out of MVP scope
- Do NOT implement branch 4 (plain class self-assignments) or branch 5 (`__init__.py` module) — those are Story 2.2
- Do NOT catch exceptions in `_check_*` or helper functions — correctness through design (Decision 5)
- Do NOT use dynamic strings for `rule` or `category` — use literals `"missing-attributes"` and `"required"`
- Do NOT return a list from `_check_*` — return `Finding | None`
- Do NOT check for module symbols in this story — `symbol.kind != "class"` guard rejects them; Story 2.2 changes this to allow module symbols
- Do NOT add `typing_extensions` variants — MVP covers `typing.NamedTuple` and `typing.TypedDict` only

### Testing Strategy

**Dual testing strategy (architecture spec):** `missing-attributes` is the highest-complexity rule and requires direct helper testing + direct `_check_*` testing + orchestrator integration testing.

**Direct helper tests (`_is_dataclass`, `_is_namedtuple`, `_is_typeddict`):**
- Each helper gets positive and negative test cases
- Use inline AST parsing: `ast.parse("@dataclass\nclass Foo: ...").body[0]` to get `ClassDef` nodes
- Test all decorator/base class forms (simple, qualified, call)

**Direct `_check_missing_attributes` tests:**
- Test each branch independently (dataclass, NamedTuple, TypedDict)
- Test section-present guard (returns None)
- Test kind guard (function/module symbols return None)
- Test node-index-missing guard (returns None)
- Test plain class returns None (branch 4 not implemented)

**Orchestrator integration tests:**
- Config gating (`require_attributes = False`)
- No-docstring skip
- Complete module regression
- Update "all rules disabled" test

**Test helper adaptation:**
The existing `_make_symbol_and_index` returns the first non-module symbol. For class tests, you'll need the class symbol specifically. Two approaches:
1. Write source with only one class (the helper returns it as the first non-module symbol)
2. Create a `_make_class_symbol_and_index` helper that filters for `kind == "class"`

Recommend approach 1 (simpler, matches existing pattern) — write source with a single class definition.

### Previous Story Intelligence

**From Story 1.4 (Missing Raises — First Pattern Implementation):**
- First `_check_*` implementation had the highest review churn — expect same for `missing-attributes` as first class-inspecting rule
- `ast.walk()` false positive was caught in code review — scope-aware walk is NOT needed here (decorator/base class inspection doesn't walk into bodies)
- `_make_symbol_and_index` helper returns first non-module symbol — works for single-class test sources
- Extra review attention agreed on by team for first implementation of new patterns

**From Story 1.6 (Missing Other Parameters):**
- `isinstance(node, ast.ClassDef)` guard needed for `ty check` type narrowing (same issue will occur here since `_NodeT` is a union)
- Comment explaining type-narrowing guard: `# ClassDef check narrows the union type for ty`
- "All rules disabled" test needs updating every time a new rule is added — must disable all 6 rules now

**From Epic 1 Retrospective:**
- Architecture doc now documents scope-aware walk (updated as action item)
- Dev agents should proactively test scope boundaries and symbol type guards
- First rule implementation of any new pattern gets extra review scrutiny

**Cross-story pattern — the 5 guards every `_check_*` has:**
1. `symbol.kind` guard — filter by symbol type
2. Section-present guard — `"SectionName" in sections`
3. Node index guard — `node_index.get(symbol.line)` returning `None`
4. Type narrowing guard — `isinstance(node, ast.ClassDef)` (for ty)
5. Detection logic — the actual rule check

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
def _check_missing_raises(...): ...           # existing
def _check_missing_yields(...): ...           # existing
def _check_missing_receives(...): ...         # existing
def _check_missing_warns(...): ...            # existing
def _check_missing_other_parameters(...): ... # existing

# Rule-specific helpers for missing-attributes (NEW)
def _is_dataclass(...): ...                   # NEW
def _is_namedtuple(...): ...                  # NEW
def _is_typeddict(...): ...                   # NEW

# missing-attributes rule (NEW)
def _check_missing_attributes(...): ...       # NEW

# Public orchestrator (always last)
def check_enrichment(...): ...                # MODIFIED — add dispatch
```

**Orchestrator after this story:**
```python
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
    if config.require_attributes:
        if f := _check_missing_attributes(symbol, sections, node_index, config, file_path):
            findings.append(f)
    # Future rules dispatched here in taxonomy-table order
```

### Library/Framework Requirements

**No new dependencies** — stdlib only:
- `ast` — Already imported
- No new imports needed beyond existing `Symbol`, `get_documented_symbols`, `Finding`, `EnrichmentConfig`

### Project Structure Notes

- 3 helper functions + 1 rule function go in `src/docvet/checks/enrichment.py`
- Helpers placed after `_check_missing_other_parameters`, before `_check_missing_attributes`
- New tests go in `tests/unit/checks/test_enrichment.py` in new comment-separated sections
- `tests/fixtures/complete_module.py` needs a dataclass with `Attributes:` section for zero-findings regression
- No new test files needed

### FRs Covered

- FR7: Detect missing Attributes on dataclasses, NamedTuples, TypedDicts
- FR33: Analyze class symbols to determine construct type
- NFR5: Zero false positives on well-documented code
- NFR10: Rule independently testable

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#missing-attributes Dispatch Order] — 5-branch priority order, first-match-wins
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1] — Private function per rule with uniform signature
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — Line-based node index
- [Source: _bmad-output/planning-artifacts/architecture.md#AST Inspection Patterns] — Decorator inspection, base class inspection patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — Helper function naming (`_is_*` for type checks)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1] — BDD acceptance criteria
- [Source: src/docvet/checks/enrichment.py:402-456] — Existing `_check_missing_other_parameters` (insertion point: new helpers + rule after this)
- [Source: src/docvet/checks/enrichment.py:464-522] — Existing `check_enrichment` orchestrator
- [Source: src/docvet/checks/enrichment.py:77] — `_NodeT` type alias
- [Source: src/docvet/config.py:38] — `require_attributes: bool = True` (already exists)
- [Source: src/docvet/ast_utils.py:16-48] — Symbol dataclass (kind: Literal["function", "class", "method", "module"])
- [Source: src/docvet/checks/__init__.py:19-66] — Finding dataclass
- [Source: tests/unit/checks/test_enrichment.py:243-254] — `_make_symbol_and_index` test helper
- [Source: tests/fixtures/complete_module.py] — Fixture with complete docstrings (needs dataclass addition)
- [Source: _bmad-output/implementation-artifacts/1-4-missing-raises-detection-and-orchestrator.md] — First pattern implementation learnings
- [Source: _bmad-output/implementation-artifacts/1-6-missing-warns-and-other-parameters-detection.md] — ty type-narrowing guard pattern
- [Source: _bmad-output/implementation-artifacts/epic-1-retro-2026-02-08.md] — Team agreements on first-pattern review

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debugging required — all tests passed on first implementation.

### Completion Notes List

- Implemented `_is_dataclass()`, `_is_namedtuple()`, `_is_typeddict()` helper functions in enrichment.py
- Implemented `_check_missing_attributes()` rule function with 3 branches (dataclass, NamedTuple, TypedDict) and first-match-wins semantics
- Wired `_check_missing_attributes` into `check_enrichment` orchestrator with `config.require_attributes` gate
- Added `@dataclass` class `ValidationResult` with complete `Attributes:` section to `complete_module.py` fixture
- Wrote 13 helper function tests (6 dataclass, 4 namedtuple, 3 typeddict)
- Wrote 10 `_check_missing_attributes` rule tests covering all 3 branches, section-present guard, kind guard, node-index guard, and plain class fallthrough
- Wrote 3 orchestrator integration tests (config disable, no-docstring skip, complete module regression)
- Updated existing `test_check_enrichment_when_active_rules_disabled_returns_empty` to disable 6 rules (added `require_attributes=False` + dataclass source)
- All quality gates pass: ruff check, ruff format, ty check, 310 tests (0 regressions)

### Change Log

- 2026-02-08: Implemented Story 2.1 — dataclass/NamedTuple/TypedDict attributes detection (3 helpers + 1 rule + orchestrator wiring + 26 new tests)

### File List

- `src/docvet/checks/enrichment.py` — MODIFIED (added `_is_dataclass`, `_is_namedtuple`, `_is_typeddict`, `_check_missing_attributes`, orchestrator dispatch)
- `tests/unit/checks/test_enrichment.py` — MODIFIED (added 26 new tests: 13 helper, 10 rule, 3 orchestrator; updated 1 existing orchestrator test)
- `tests/fixtures/complete_module.py` — MODIFIED (added `ValidationResult` dataclass with `Attributes:` section)
