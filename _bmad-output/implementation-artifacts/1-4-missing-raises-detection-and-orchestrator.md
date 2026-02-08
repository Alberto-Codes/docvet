# Story 1.4: Missing Raises Detection and Orchestrator

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect functions that raise exceptions without documenting them in a `Raises:` section,
so that I can ensure my docstrings accurately describe error behavior for callers.

## Acceptance Criteria

1. **Given** a function with `raise ValueError` and a docstring with no `Raises:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-raises"`, `category="required"`, and a message naming the function and the exception (AC: #1)

2. **Given** a function with `raise ValueError` and a docstring containing a `Raises:` section, **when** `check_enrichment` is called, **then** it returns zero findings for that function (missing-only, not incomplete) (AC: #2)

3. **Given** a function with no `raise` statements, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-raises` on that function (AC: #3)

4. **Given** a function with `raise` but no docstring at all, **when** `check_enrichment` is called, **then** it returns zero findings (undocumented symbols are skipped) (AC: #4)

5. **Given** `config.require_raises = False`, **when** `check_enrichment` is called on a function with `raise` and no `Raises:` section, **then** it returns zero findings for `missing-raises` (config toggle respected) (AC: #5)

6. **Given** a well-documented file (`tests/fixtures/complete_module.py`), **when** `check_enrichment` is called, **then** it returns an empty list (zero findings) (AC: #6)

7. **Given** `tests/fixtures/missing_raises.py`, **when** `check_enrichment` is called, **then** it returns exactly the expected `missing-raises` finding (AC: #7)

8. **Given** the `check_enrichment` orchestrator, **when** called with `source`, `tree`, `config`, `file_path`, **then** it returns `list[Finding]` with no I/O and no side effects (pure function) (AC: #8)

## Tasks / Subtasks

- [x] Task 1: Implement `_check_missing_raises` private function (AC: #1, #2, #3)
  - [x] 1.1: Write function with uniform signature `_check_missing_raises(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 1.2: Retrieve function node via `node_index.get(symbol.line)` — return `None` if missing (module symbols)
  - [x] 1.3: Walk node body with `ast.walk()` to find `ast.Raise` nodes
  - [x] 1.4: Extract exception class names from `ast.Raise.exc` (handle `ast.Name`, `ast.Call`, `ast.Attribute`)
  - [x] 1.5: Check `"Raises" not in sections` — if section exists, return `None` (AC: #2)
  - [x] 1.6: Construct `Finding` with `rule="missing-raises"`, `category="required"`, evidence listing exception names
  - [x] 1.7: Add docstring following project conventions

- [x] Task 2: Implement `check_enrichment` public orchestrator (AC: #4, #5, #6, #7, #8)
  - [x] 2.1: Write function with signature `check_enrichment(source, tree, config, file_path) -> list[Finding]`
  - [x] 2.2: Call `get_documented_symbols(tree)` to get symbol list (NOTE: only takes `tree`, not `source`)
  - [x] 2.3: Call `_build_node_index(tree)` once at top
  - [x] 2.4: Loop over symbols, skip those with no docstring (FR20)
  - [x] 2.5: Call `_parse_sections(symbol.docstring)` once per symbol
  - [x] 2.6: Config-gate `_check_missing_raises` with `if config.require_raises:` (AC: #5)
  - [x] 2.7: Use walrus operator `if f := _check_missing_raises(...)` for concise finding collection
  - [x] 2.8: Return collected `list[Finding]`
  - [x] 2.9: Add comprehensive docstring with Args/Returns sections

- [x] Task 3: Write unit tests for `_check_missing_raises` (AC: #1, #2, #3)
  - [x] 3.1: `test_missing_raises_when_function_raises_without_section_returns_finding` — AC #1
  - [x] 3.2: `test_missing_raises_when_raises_section_present_returns_none` — AC #2
  - [x] 3.3: `test_missing_raises_when_no_raise_statements_returns_none` — AC #3
  - [x] 3.4: `test_missing_raises_when_raise_without_exception_returns_finding` (bare `raise`)
  - [x] 3.5: `test_missing_raises_when_multiple_exceptions_lists_all_in_message`
  - [x] 3.6: `test_missing_raises_when_node_index_missing_returns_none` (module symbol)

- [x] Task 4: Write unit tests for `check_enrichment` orchestrator (AC: #4, #5, #6, #7, #8)
  - [x] 4.1: `test_check_enrichment_when_no_docstring_skips_symbol` — AC #4
  - [x] 4.2: `test_check_enrichment_when_raises_disabled_returns_no_finding` — AC #5
  - [x] 4.3: `test_check_enrichment_when_complete_module_returns_empty` — AC #6 (use fixture)
  - [x] 4.4: `test_check_enrichment_when_missing_raises_fixture_returns_finding` — AC #7 (use fixture)
  - [x] 4.5: `test_check_enrichment_returns_list_of_findings` — AC #8
  - [x] 4.6: `test_check_enrichment_when_all_rules_disabled_returns_empty`

- [x] Task 5: Run quality gates and verify all pass
  - [x] 5.1: `uv run ruff check .` — All checks pass
  - [x] 5.2: `uv run ruff format --check .` — All files formatted
  - [x] 5.3: `uv run ty check` — All type checks pass
  - [x] 5.4: `uv run pytest tests/unit/checks/ -v` — All enrichment tests pass
  - [x] 5.5: `uv run pytest` — Full suite passes (0 regressions)

## Dev Notes

### Scope

This story implements the **first enrichment rule** (`missing-raises`) and the **public orchestrator** (`check_enrichment`). This is the first story that produces `Finding` objects and establishes the pattern all subsequent rules follow.

Two new functions in `checks/enrichment.py`:
1. **`_check_missing_raises(symbol, sections, node_index, config, file_path) -> Finding | None`** — Detects functions with `raise` statements but no `Raises:` section
2. **`check_enrichment(source, tree, config, file_path) -> list[Finding]`** — Public orchestrator that dispatches to rule functions

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | MODIFIED — Add `_check_missing_raises()`, `check_enrichment()`, new imports |
| `tests/unit/checks/test_enrichment.py` | MODIFIED — Add tests for `_check_missing_raises` and `check_enrichment` |

### Architecture Constraints

**Uniform `_check_*` Signature (Decision 1):**
```python
def _check_missing_raises(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
```
- Config gating lives in the orchestrator, NOT inside `_check_*`
- The function is pure detection logic — zero config awareness
- Returns `Finding | None` (not a list)

**Orchestrator Pattern (Architecture Orchestrator Pattern):**
```python
def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
) -> list[Finding]:
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
        # Future rules dispatched here in taxonomy-table order

    return findings
```

**CRITICAL: `get_documented_symbols` takes only `tree`:**
The actual signature is `get_documented_symbols(tree: ast.Module) -> list[Symbol]`, NOT `get_documented_symbols(source, tree)` as the architecture doc's data flow diagram shows. The `source` parameter in `check_enrichment`'s signature is kept for future use but is not passed to `get_documented_symbols`.

**Finding Message Format (Decision 4):**
```
Function '{symbol.name}' raises {exception_names} but has no Raises: section
```
- `exception_names` = comma-separated list of exception class names found in `raise` statements
- For bare `raise` (re-raise), use the string `"(re-raise)"`
- For `raise SomeException(...)` (ast.Call), extract the function name
- For `raise module.Exception` (ast.Attribute), extract the attribute name

**AST Inspection for `raise` statements:**
- Use `ast.walk(node)` on the function/method node to find all `ast.Raise` nodes in body
- `raise.exc` is the exception expression:
  - `ast.Name` → `raise ValueError` → extract `node.id` ("ValueError")
  - `ast.Call` → `raise ValueError("msg")` → extract `node.func` (could be `ast.Name` or `ast.Attribute`)
  - `ast.Attribute` → `raise errors.CustomError` → extract `node.attr` ("CustomError")
  - `None` → bare `raise` (re-raise with no argument)
- Collect unique exception names into a sorted set for deterministic output (NFR6)

**File Organization Order:**
Functions must appear in this order in `enrichment.py`:
1. Module constants (`_SECTION_HEADERS`, `_SECTION_PATTERN`) — exists
2. `_NodeT` type alias — exists
3. Shared helpers (`_parse_sections`, `_build_node_index`) — exists
4. `_check_missing_raises` — **NEW** (first `_check_*` function)
5. `check_enrichment` — **NEW** (last function in file, always at bottom)

### What NOT to Do

- Do NOT put config gating inside `_check_missing_raises` — the orchestrator handles it
- Do NOT walk the raw `tree` in `_check_*` — use `node_index.get(symbol.line)` to get the node
- Do NOT use `ast.walk(tree)` to find raise statements — walk only the specific node's subtree
- Do NOT return a list from `_check_*` — return `Finding | None` (one finding per symbol per rule, FR18)
- Do NOT pass `source` to `get_documented_symbols()` — it only takes `tree`
- Do NOT catch exceptions in `_check_*` functions — correctness through design (Decision 5)
- Do NOT use dynamic strings for `rule` or `category` — use literals `"missing-raises"` and `"required"`
- Do NOT import or call anything from `docvet.cli` or `docvet.discovery` — enrichment has no I/O
- Do NOT add `try/except` blocks — if something crashes, it should crash in tests

### Testing Strategy

**Test through `check_enrichment` (simple rule, dual testing strategy):**
- Most tests should call `check_enrichment` directly with targeted config
- This tests config gating AND detection logic in one shot
- Create source strings inline in tests using triple-quoted strings

**Direct `_check_missing_raises` tests for edge cases:**
- Module symbol (node_index returns `None`)
- Multiple exceptions in one function
- Bare `raise` (re-raise)

**Use existing fixtures for integration-level tests:**
- `tests/fixtures/missing_raises.py` — should produce exactly 1 `missing-raises` finding
- `tests/fixtures/complete_module.py` — should produce zero findings

**Fixture usage pattern:**
```python
def test_check_enrichment_when_missing_raises_fixture_returns_finding():
    source = Path("tests/fixtures/missing_raises.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()  # defaults: all rules enabled
    findings = check_enrichment(source, tree, config, "tests/fixtures/missing_raises.py")
    assert len(findings) == 1
    assert findings[0].rule == "missing-raises"
    assert findings[0].symbol == "validate_input"
```

**Test naming convention:**
- `test_{rule_id}_when_{condition}_returns_{expected}` for direct rule tests
- `test_check_enrichment_when_{condition}_{expected}` for orchestrator tests

### Previous Story Intelligence

**From Story 1.3 (Section Parser and Node Index):**
- `_parse_sections(docstring: str) -> set[str]` — returns matched header names as a set
- `_build_node_index(tree: ast.Module) -> dict[int, _NodeT]` — maps line numbers to AST nodes
- `_NodeT = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef` — type alias for node types
- `_SECTION_HEADERS` and `_SECTION_PATTERN` — module-level constants
- 17 unit tests pass, 100% coverage on enrichment.py

**Key Lessons from Story 1.3:**
1. `_build_node_index` return type was narrowed from `ast.AST` to `_NodeT` during code review — use the precise type
2. Code block edge case: `_parse_sections` matches headers inside fenced code blocks (documented as safe-direction false negative)
3. Docstring accuracy matters — code review caught misleading docstring claims (be precise about what functions actually do)

**From Story 1.2 (Finding Dataclass):**
- `Finding` is in `checks/__init__.py`, imported as `from docvet.checks import Finding`
- 6 fields: `file`, `line`, `symbol`, `rule`, `message`, `category`
- `__post_init__` validates: non-empty strings, line >= 1, category in `("required", "recommended")`
- Private imports: `_dataclass`, `_Literal` prevent import leakage

**From Story 1.1 (Config Toggle):**
- `EnrichmentConfig` has `require_raises: bool = True` (default enabled)
- All 10 toggles exist — the orchestrator can gate all rules from day 1
- Import as `from docvet.config import EnrichmentConfig`

### Git Intelligence

**Recent Commits on develop:**
- `f4429c8` feat(enrichment): enhance section parsing logic and documentation
- `304bd76` feat(enrichment): add section header parser and AST node index (#27)
- `0dee333` feat(dataclass): create shared immutable Finding dataclass (#26)
- `2937807` feat(enrichment): add require_attributes config toggle (#25)

**Code Patterns Established:**
- Branch naming: `feat/enrichment-*`
- Commit scope: `enrichment` for enrichment module changes
- PR flow: draft PR → code review → squash merge to develop
- File separators: `# ---` comment blocks for logical sections
- Import order: `from __future__` → stdlib → local (`from docvet.*`)
- Test naming: `test_{what}_when_{condition}_{expected}`

### Implementation Details

**Exception Name Extraction:**

```python
def _extract_exception_names(node: ast.AST) -> set[str]:
    """Extract unique exception class names from raise statements in a node."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc is not None:
            exc = child.exc
            # raise ValueError
            if isinstance(exc, ast.Name):
                names.add(exc.id)
            # raise ValueError("msg")
            elif isinstance(exc, ast.Call):
                if isinstance(exc.func, ast.Name):
                    names.add(exc.func.id)
                elif isinstance(exc.func, ast.Attribute):
                    names.add(exc.func.attr)
            # raise errors.CustomError
            elif isinstance(exc, ast.Attribute):
                names.add(exc.attr)
        elif isinstance(child, ast.Raise) and child.exc is None:
            names.add("(re-raise)")
    return names
```

This is a helper that could be inlined or extracted as `_extract_exception_names`. The choice is implementation-level — either approach is acceptable as long as the function stays private and follows naming conventions.

**Orchestrator imports needed (add to existing imports):**
```python
from docvet.ast_utils import Symbol, get_documented_symbols
from docvet.checks import Finding
from docvet.config import EnrichmentConfig
```

### Library/Framework Requirements

**No new dependencies** — stdlib only:
- `ast` — Already imported in `enrichment.py`
- New imports: `Symbol`, `get_documented_symbols` from `docvet.ast_utils`; `Finding` from `docvet.checks`; `EnrichmentConfig` from `docvet.config`

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

# Rule functions (NEW — taxonomy-table order)
def _check_missing_raises(...): ...

# Public orchestrator (NEW — always last)
def check_enrichment(...): ...
```

### Testing Standards Summary

- Test naming: `test_{unit_under_test}_{condition}_{expected_behavior}`
- Use `parse_source` fixture for AST creation where convenient
- Use `Path.read_text()` for fixture file tests
- Self-contained tests (no shared state)
- `EnrichmentConfig()` with defaults for "all rules enabled" scenario
- `EnrichmentConfig(require_raises=False)` for config-disabled tests
- Group tests: `# _check_missing_raises tests`, `# check_enrichment orchestrator tests`

### FRs Covered

- FR1: Detect functions with `raise` statements but no `Raises:` section
- FR18: At most one finding per symbol per rule
- FR19: Zero findings on well-documented code
- FR20: Zero findings for symbols with no docstring
- FR21: Missing-only detection (not incomplete)
- FR24: Rule identifiers usable in config/filtering
- FR25: 14 scenarios → 10 rule ID mapping
- FR32: Analyze functions for raise patterns
- FR37: Distinguish documented vs undocumented symbols
- FR39: Pure function API: source, tree, config, file_path → findings
- FR40: No I/O, no side effects, deterministic
- NFR5: Zero false positives on well-documented code
- NFR6: Identical output for identical input
- NFR8: Never modifies input data
- NFR9: Actionable finding messages

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1] — Private function per rule with uniform signature
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — Line-based node index for O(1) lookup
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 4] — Finding message format conventions
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] — No try/except, defensive by design
- [Source: _bmad-output/planning-artifacts/architecture.md#Orchestrator Pattern] — Config gating and dispatch pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#AST Inspection Patterns] — ast.walk for body traversal, isinstance for type checking
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4] — BDD acceptance criteria
- [Source: src/docvet/checks/enrichment.py:49-96] — Existing _parse_sections and _build_node_index
- [Source: src/docvet/checks/__init__.py:19-66] — Finding dataclass
- [Source: src/docvet/config.py:24-39] — EnrichmentConfig with require_raises toggle
- [Source: src/docvet/ast_utils.py:224-257] — get_documented_symbols(tree) signature (NOT source, tree)
- [Source: src/docvet/ast_utils.py:16-48] — Symbol dataclass fields
- [Source: tests/fixtures/missing_raises.py] — Fixture with raise but no Raises: section
- [Source: tests/fixtures/complete_module.py] — Fixture with complete docstrings

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- ty check caught `str | None` type error on `module_symbol.docstring` — added `assert` guard in test

### Completion Notes List

- Implemented `_check_missing_raises` with uniform `_check_*` signature per Decision 1
- Exception name extraction handles `ast.Name`, `ast.Call` (with `ast.Name`/`ast.Attribute` func), `ast.Attribute`, and bare `raise` (re-raise)
- Exception names collected as sorted set for deterministic output (NFR6)
- Implemented `check_enrichment` orchestrator following the Architecture Orchestrator Pattern
- Config gating in orchestrator, not in rule function (Decision 1)
- `get_documented_symbols(tree)` called correctly with only `tree` parameter
- Walrus operator used for concise finding collection
- 17 new tests (11 for `_check_missing_raises`, 6 for `check_enrichment`) — all pass
- All 8 acceptance criteria satisfied
- 236 total tests pass, 0 regressions

### Change Log

- 2026-02-08: Implemented `_check_missing_raises` rule and `check_enrichment` orchestrator with 12 unit tests
- 2026-02-08: Code review — Fixed `ast.walk()` nested scope false positive (NFR5 violation), added 5 tests for full AST branch coverage and nested scope scenarios, coverage 91% → 100%

### File List

- `src/docvet/checks/enrichment.py` — MODIFIED: Added `_check_missing_raises()`, `check_enrichment()`, new imports (`Symbol`, `get_documented_symbols`, `Finding`, `EnrichmentConfig`). Review fix: scope-aware walk replacing `ast.walk()` to prevent nested function false positives.
- `tests/unit/checks/test_enrichment.py` — MODIFIED: Added 17 tests (11 for `_check_missing_raises`, 6 for `check_enrichment`), new imports. Review additions: 5 tests for uncovered AST branches and nested scope scenarios.

### Senior Developer Review (AI)

**Reviewer:** Alberto-Codes on 2026-02-08

**Outcome:** Approved with fixes applied

**Findings (3 fixed, 2 noted):**

1. **[FIXED][HIGH] `ast.walk()` false positives with nested scopes** — `ast.walk(node)` traversed into nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef` nodes, attributing their raises to the outer function (NFR5 violation). Fixed with scope-aware iterative walk that stops at scope boundaries.
2. **[FIXED][MEDIUM] Missing test coverage for 3 AST branches** — Lines 147, 151-154 (bare `ast.Name`, `ast.Call(func=ast.Attribute)`, bare `ast.Attribute`) were untested. Added 3 targeted tests.
3. **[FIXED][MEDIUM] No test for nested scope behavior** — No test verified raises inside nested functions are excluded. Added 2 tests (pure nested, mixed outer+nested).
4. **[NOTED][LOW] `_make_symbol_and_index` always returns first symbol** — Acceptable for current single-function test sources.
5. **[NOTED][LOW] Unused `config` param in `_check_missing_raises`** — Intentional per architecture Decision 1 (uniform signature).
