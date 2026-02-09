# Story 1.5: Missing Yields and Receives Detection

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect generator functions missing `Yields:` and `Receives:` sections,
so that consumers of my generators understand what values are yielded and what can be sent in.

## Acceptance Criteria

1. **Given** a generator function with `yield` expressions and a docstring with no `Yields:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-yields"`, `category="required"` (AC: #1)

2. **Given** a generator function with `yield` and a docstring containing a `Yields:` section, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-yields` (AC: #2)

3. **Given** `tests/fixtures/missing_yields.py`, **when** `check_enrichment` is called, **then** it returns exactly the expected `missing-yields` finding for `stream_items` (AC: #3)

4. **Given** a generator function using `value = yield` (send pattern) with no `Receives:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-receives"`, `category="required"` (AC: #4)

5. **Given** a generator with `value = yield` and a `Receives:` section present, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-receives` (AC: #5)

6. **Given** `config.require_yields = False`, **when** `check_enrichment` is called on a generator missing `Yields:`, **then** it returns zero findings for `missing-yields` (AC: #6)

7. **Given** `config.require_receives = False`, **when** `check_enrichment` is called on a generator with send pattern missing `Receives:`, **then** it returns zero findings for `missing-receives` (AC: #7)

8. **Given** an async generator function with `yield`, **when** `check_enrichment` is called, **then** it detects the `yield` via the scope-aware walk on the `AsyncFunctionDef` body and applies the same `missing-yields` rule (AC: #8)

## Tasks / Subtasks

- [ ] Task 1: Implement `_check_missing_yields` private function (AC: #1, #2, #8)
  - [ ] 1.1: Write function with uniform signature `_check_missing_yields(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [ ] 1.2: Guard on `symbol.kind in ("function", "method")` — return `None` for class/module symbols
  - [ ] 1.3: Retrieve function node via `node_index.get(symbol.line)` — return `None` if missing
  - [ ] 1.4: Early return `None` if `"Yields" in sections` (section already documented)
  - [ ] 1.5: Scope-aware walk of node body to find `ast.Yield` or `ast.YieldFrom` nodes (stop at nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef` boundaries)
  - [ ] 1.6: If any yield nodes found, construct `Finding` with `rule="missing-yields"`, `category="required"`
  - [ ] 1.7: Add docstring following project conventions

- [ ] Task 2: Implement `_check_missing_receives` private function (AC: #4, #5)
  - [ ] 2.1: Write function with uniform signature `_check_missing_receives(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [ ] 2.2: Guard on `symbol.kind in ("function", "method")` — return `None` for class/module symbols
  - [ ] 2.3: Retrieve function node via `node_index.get(symbol.line)` — return `None` if missing
  - [ ] 2.4: Early return `None` if `"Receives" in sections` (section already documented)
  - [ ] 2.5: Scope-aware walk of node body to find `ast.Yield` nodes used as assignment targets (`ast.Assign` or `ast.AnnAssign` where `value` is `ast.Yield`)
  - [ ] 2.6: If any send-pattern yields found, construct `Finding` with `rule="missing-receives"`, `category="required"`
  - [ ] 2.7: Add docstring following project conventions

- [ ] Task 3: Wire both rules into `check_enrichment` orchestrator (AC: #6, #7)
  - [ ] 3.1: Add `config.require_yields` gate before `_check_missing_yields` dispatch (taxonomy-table order: after `missing-raises`)
  - [ ] 3.2: Add `config.require_receives` gate before `_check_missing_receives` dispatch (taxonomy-table order: after `missing-yields`)
  - [ ] 3.3: Use walrus operator pattern `if f := _check_missing_yields(...)` consistent with existing `missing-raises` dispatch

- [ ] Task 4: Write unit tests (AC: #1-#8)
  - [ ] 4.1: `test_missing_yields_when_generator_yields_without_section_returns_finding` — AC #1
  - [ ] 4.2: `test_missing_yields_when_yields_section_present_returns_none` — AC #2
  - [ ] 4.3: `test_missing_yields_when_no_yield_statements_returns_none`
  - [ ] 4.4: `test_missing_yields_when_yield_from_without_section_returns_finding`
  - [ ] 4.5: `test_missing_yields_when_node_index_missing_returns_none` (module symbol)
  - [ ] 4.6: `test_missing_yields_when_class_symbol_returns_none`
  - [ ] 4.7: `test_missing_yields_when_nested_generator_yields_returns_none` (scope boundary)
  - [ ] 4.8: `test_missing_yields_when_async_generator_yields_returns_finding` — AC #8
  - [ ] 4.9: `test_missing_receives_when_send_pattern_without_section_returns_finding` — AC #4
  - [ ] 4.10: `test_missing_receives_when_receives_section_present_returns_none` — AC #5
  - [ ] 4.11: `test_missing_receives_when_no_send_pattern_returns_none`
  - [ ] 4.12: `test_missing_receives_when_plain_yield_no_assignment_returns_none`
  - [ ] 4.13: `test_missing_receives_when_annotated_assign_yield_returns_finding`
  - [ ] 4.14: `test_check_enrichment_when_yields_disabled_returns_no_finding` — AC #6
  - [ ] 4.15: `test_check_enrichment_when_receives_disabled_returns_no_finding` — AC #7
  - [ ] 4.16: `test_check_enrichment_when_missing_yields_fixture_returns_finding` — AC #3
  - [ ] 4.17: `test_check_enrichment_when_complete_module_still_returns_empty`

- [ ] Task 5: Run quality gates and verify all pass
  - [ ] 5.1: `uv run ruff check .` — All checks pass
  - [ ] 5.2: `uv run ruff format --check .` — All files formatted
  - [ ] 5.3: `uv run ty check` — All type checks pass
  - [ ] 5.4: `uv run pytest tests/unit/checks/ -v` — All enrichment tests pass
  - [ ] 5.5: `uv run pytest` — Full suite passes (0 regressions)

## Dev Notes

### Scope

This story adds two enrichment rules (`missing-yields`, `missing-receives`) and wires them into the existing `check_enrichment` orchestrator. Follows the exact pattern established in Story 1.4 (`missing-raises`).

Two new functions in `checks/enrichment.py`:
1. **`_check_missing_yields`** — Detects generators with `yield`/`yield from` but no `Yields:` section
2. **`_check_missing_receives`** — Detects generators using `value = yield` send pattern but no `Receives:` section

Plus orchestrator modifications to dispatch both rules with config gating.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | MODIFIED — Add `_check_missing_yields()`, `_check_missing_receives()`, wire into orchestrator |
| `tests/unit/checks/test_enrichment.py` | MODIFIED — Add tests for both rules and orchestrator integration |

### Architecture Constraints

**Uniform `_check_*` Signature (Decision 1):**
```python
def _check_missing_yields(
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
1. `_check_missing_raises` (exists)
2. `_check_missing_yields` — **NEW**
3. `_check_missing_receives` — **NEW**
4. (future: `_check_missing_warns`, `_check_missing_other_parameters`, ...)

**Scope-Aware Walk (from Story 1.4 code review):**
Use the iterative stack-based walk pattern that stops at scope boundaries:
```python
stack = list(ast.iter_child_nodes(node))
while stack:
    child = stack.pop()
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        continue  # Don't descend into nested scopes
    # ... check for ast.Yield / ast.YieldFrom ...
    stack.extend(ast.iter_child_nodes(child))
```
This prevents yields inside nested generators from being attributed to the outer function (NFR5 — zero false positives).

### AST Detection: `missing-yields`

Detect `ast.Yield` and `ast.YieldFrom` nodes in the function body:
- `ast.Yield` — covers `yield expr` and `yield` (bare yield)
- `ast.YieldFrom` — covers `yield from iterable`
- Both sync `FunctionDef` and async `AsyncFunctionDef` generators are handled

**Finding message format:**
```
Function '{symbol.name}' yields but has no Yields: section
```
No evidence collection needed (unlike `missing-raises` which lists exception names). A generator either yields or it doesn't.

**Note:** `ast.YieldFrom` should also trigger `missing-yields` (a `yield from` expression produces values just like `yield`).

### AST Detection: `missing-receives`

Detect `ast.Yield` nodes that appear as assignment targets (the send pattern):

**Pattern 1 — `ast.Assign`:**
```python
value = yield expr
# AST: Assign(targets=[Name(id='value')], value=Yield(value=...))
```
Check: `isinstance(child, ast.Assign) and isinstance(child.value, ast.Yield)`

**Pattern 2 — `ast.AnnAssign`:**
```python
value: int = yield expr
# AST: AnnAssign(target=Name(id='value'), value=Yield(value=...))
```
Check: `isinstance(child, ast.AnnAssign) and child.value is not None and isinstance(child.value, ast.Yield)`

**Pattern 3 — Standalone `ast.Yield` used as expression statement (bare `yield` for receiving):**
NOTE: The `value = yield` pattern is the primary send pattern. A bare `yield` (not assigned) can also receive a sent value, but it discards it. The key signal for `missing-receives` is that the result of `yield` is **captured** in a variable — this indicates the generator protocol's `.send()` is intentionally used. Do NOT flag bare `yield` as a send pattern.

**`ast.YieldFrom` does NOT trigger `missing-receives`** — `yield from` delegates to a sub-generator and does not use the send protocol directly.

**Finding message format:**
```
Function '{symbol.name}' uses yield send pattern but has no Receives: section
```

### What NOT to Do

- Do NOT put config gating inside `_check_missing_yields` or `_check_missing_receives` — the orchestrator handles it
- Do NOT walk the raw `tree` in `_check_*` — use `node_index.get(symbol.line)` to get the node
- Do NOT use `ast.walk(node)` — use the scope-aware iterative walk pattern from Story 1.4
- Do NOT flag bare `yield` (no assignment) as a send pattern for `missing-receives`
- Do NOT flag `ast.YieldFrom` as a send pattern for `missing-receives`
- Do NOT collect evidence strings for yields (unlike `missing-raises` which collects exception names) — the message is simpler
- Do NOT catch exceptions in `_check_*` functions — correctness through design (Decision 5)
- Do NOT use dynamic strings for `rule` or `category` — use literals
- Do NOT return a list from `_check_*` — return `Finding | None`

### Testing Strategy

**Test through `check_enrichment` for orchestrator integration:**
- Config gating tests (AC #6, #7)
- Fixture-based tests (AC #3)
- Complete module regression (zero findings)

**Direct `_check_missing_yields` tests for detection logic:**
- Generator with yield (AC #1)
- Generator with Yields section present (AC #2)
- No yield statements (returns None)
- `yield from` detection
- Module/class symbol rejection
- Nested generator scope boundary
- Async generator (AC #8)

**Direct `_check_missing_receives` tests for send pattern:**
- `value = yield` pattern (AC #4)
- Receives section present (AC #5)
- No send pattern (returns None)
- Plain yield without assignment (returns None)
- Annotated assignment yield
- Node index missing (returns None)

**Fixture usage pattern:**
```python
def test_check_enrichment_when_missing_yields_fixture_returns_finding():
    source = Path("tests/fixtures/missing_yields.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "tests/fixtures/missing_yields.py")
    assert len(findings) == 1
    assert findings[0].rule == "missing-yields"
    assert findings[0].symbol == "stream_items"
```

**Test naming convention:**
- `test_{rule_id}_when_{condition}_returns_{expected}` for direct rule tests
- `test_check_enrichment_when_{condition}_{expected}` for orchestrator tests

### Previous Story Intelligence

**From Story 1.4 (Missing Raises and Orchestrator):**
- Scope-aware walk pattern established: iterative stack with `ast.iter_child_nodes`, skip nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef`
- `_make_symbol_and_index` test helper exists — reuse for new rule tests
- Orchestrator uses walrus operator `if f := _check_*(...)` pattern
- `get_documented_symbols(tree)` takes only `tree` (NOT `source, tree`)
- Code review caught `ast.walk()` false positives with nested scopes — fixed with scope-aware walk. Apply same pattern here.
- `config` param is unused in `_check_*` but required by uniform signature (Decision 1)
- 17 tests added in 1.4 — current total: 34 enrichment tests. Expect ~17 more from this story.

**From Story 1.3 (Section Parser and Node Index):**
- `_parse_sections` returns `set[str]` — check `"Yields" in sections` and `"Receives" in sections`
- `_build_node_index` returns `dict[int, _NodeT]` where `_NodeT = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef`
- Node index covers `AsyncFunctionDef` — async generators get their node via `node_index.get(symbol.line)`

**From Story 1.2 (Finding Dataclass):**
- `Finding(file=, line=, symbol=, rule=, message=, category=)` — all 6 fields, frozen
- `__post_init__` validates category is `"required"` or `"recommended"`

### Git Intelligence

**Recent commits on develop:**
- `244bb9c` feat(enrichment): add missing-raises detection and orchestrator (#28)
- `f4429c8` feat(enrichment): enhance section parsing logic and documentation
- `304bd76` feat(enrichment): add section header parser and AST node index (#27)
- `0dee333` feat(dataclass): create shared immutable Finding dataclass (#26)
- `2937807` feat(enrichment): add require_attributes config toggle (#25)

**Patterns to follow:**
- Branch naming: `feat/enrichment-missing-yields-receives` or similar
- Commit scope: `enrichment`
- File separators: `# ---` comment blocks for logical sections
- Import order: `from __future__` -> stdlib -> local (`from docvet.*`)

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
def _check_missing_raises(...): ...     # existing
def _check_missing_yields(...): ...     # NEW
def _check_missing_receives(...): ...   # NEW

# Public orchestrator (always last)
def check_enrichment(...): ...          # MODIFIED — add dispatch for new rules
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
        # Future rules dispatched here in taxonomy-table order

    return findings
```

### Library/Framework Requirements

**No new dependencies** — stdlib only:
- `ast` — Already imported
- No new imports needed beyond existing `Symbol`, `get_documented_symbols`, `Finding`, `EnrichmentConfig`

### Project Structure Notes

- Both new `_check_*` functions go in `src/docvet/checks/enrichment.py` between `_check_missing_raises` and the orchestrator
- New tests go in `tests/unit/checks/test_enrichment.py` in new comment-separated sections
- No new files needed
- No fixture changes needed — `tests/fixtures/missing_yields.py` already exists and has the right content

### FRs Covered

- FR2: Detect missing Yields section on generator functions
- FR3: Detect missing Receives section on generators using send pattern
- FR32: Analyze functions for yield expressions and send patterns
- NFR5: Zero false positives on well-documented code
- NFR6: Identical output for identical input (deterministic)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1] — Private function per rule with uniform signature
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — Line-based node index for O(1) lookup
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 4] — Finding message format conventions
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] — No try/except, defensive by design
- [Source: _bmad-output/planning-artifacts/architecture.md#AST Inspection Patterns] — ast.walk for body traversal
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5] — BDD acceptance criteria
- [Source: src/docvet/checks/enrichment.py:108-181] — Existing _check_missing_raises (pattern to follow)
- [Source: src/docvet/checks/enrichment.py:189-227] — Existing check_enrichment orchestrator
- [Source: src/docvet/checks/enrichment.py:53-74] — _parse_sections helper
- [Source: src/docvet/checks/enrichment.py:80-100] — _build_node_index helper
- [Source: src/docvet/config.py:31-33] — require_yields and require_receives toggles
- [Source: tests/fixtures/missing_yields.py] — Fixture with yield but no Yields: section
- [Source: tests/fixtures/complete_module.py:31-46] — Generator with Yields: section (zero findings expected)
- [Source: _bmad-output/implementation-artifacts/1-4-missing-raises-detection-and-orchestrator.md] — Previous story patterns and learnings

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
