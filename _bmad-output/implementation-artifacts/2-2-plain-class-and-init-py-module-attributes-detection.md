# Story 2.2: Plain Class and `__init__.py` Module Attributes Detection

Status: ready-for-dev

## Story

As a developer,
I want to detect plain classes with `__init__` self-assignments and `__init__.py` modules that lack `Attributes:` sections,
So that all class fields and module exports are documented for consumers.

## Acceptance Criteria

1. **Given** a plain class with an `__init__` method containing `self.x = value` assignments and a docstring with no `Attributes:` section, **when** `check_enrichment` is called, **then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`, and a message naming the class (AC: #1)

2. **Given** a plain class with `__init__` containing annotated assignments (`self.x: int = 0`), **when** `check_enrichment` is called and the docstring has no `Attributes:` section, **then** it detects the self-assignments via `ast.AnnAssign` and returns a finding (AC: #2)

3. **Given** a plain class with `__init__` but no `self.*` assignments, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-attributes` on that class (no fields to document) (AC: #3)

4. **Given** an `__init__.py` module with a module-level docstring but no `Attributes:` section, **when** `check_enrichment` is called with `file_path` ending in `__init__.py`, **then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`, applied to the module-level symbol (AC: #4)

5. **Given** an `__init__.py` module with an `Attributes:` section in its module docstring, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-attributes` (AC: #5)

6. **Given** a regular Python file (not `__init__.py`) with a module-level docstring, **when** `check_enrichment` is called, **then** it does not apply `__init__.py`-specific rules (AC: #6)

7. **Given** a class that is both a `@dataclass` and has `__init__` self-assignments, **when** `check_enrichment` is called, **then** it produces at most one `missing-attributes` finding (dataclass branch wins per first-match-wins dispatch order) (AC: #7)

8. **Given** the full `_check_missing_attributes` dispatch, **when** evaluated on any symbol, **then** branches are checked in order: dataclass, NamedTuple, TypedDict, plain class, `__init__.py` module — first match wins, no fallthrough (AC: #8)

9. **Given** the `_has_self_assignments` and `_is_init_module` helper functions, **when** tested directly, **then** each correctly identifies its pattern and returns `False` for non-matching inputs (AC: #9)

10. **Given** `config.require_attributes = False`, **when** `check_enrichment` is called on any symbol missing `Attributes:`, **then** it returns zero findings for `missing-attributes` (AC: #10 — existing behavior, regression guard)

11. **Given** a class whose `__init__` has self-assignments only inside a nested function, **when** `check_enrichment` is called, **then** it returns zero findings for `missing-attributes` (nested scope boundary — scope-aware walk required) (AC: #11)

## Tasks / Subtasks

- [ ] Task 1: Implement `_has_self_assignments` helper function (AC: #1, #2, #3, #9, #11)
  - [ ] 1.1: Write `_has_self_assignments(node: ast.ClassDef) -> bool`
  - [ ] 1.2: Find `__init__` method in `node.body` via direct `.body` iteration (not `ast.walk`)
  - [ ] 1.3: Walk `__init__` body with scope-aware iterative walk (stop at nested scopes)
  - [ ] 1.4: Detect `ast.Assign` where target is `ast.Attribute` with `value` being `ast.Name(id="self")`
  - [ ] 1.5: Detect `ast.AnnAssign` where `target` is `ast.Attribute` with `value` being `ast.Name(id="self")`
  - [ ] 1.6: Return `True` on first match, `False` if no `__init__` or no self-assignments found

- [ ] Task 2: Implement `_is_init_module` helper function (AC: #4, #6, #9)
  - [ ] 2.1: Write `_is_init_module(file_path: str) -> bool`
  - [ ] 2.2: Check `file_path.endswith("__init__.py")` — OS-agnostic path check
  - [ ] 2.3: Return `True` for `__init__.py` paths, `False` otherwise

- [ ] Task 3: Modify `_check_missing_attributes` to add branches 4-5 (AC: #1-#8)
  - [ ] 3.1: Change the kind guard from `symbol.kind != "class"` to `symbol.kind not in ("class", "module")`
  - [ ] 3.2: Move the `node_index.get()` / `isinstance(node, ast.ClassDef)` block into a class-only branch
  - [ ] 3.3: Add Branch 4 after TypedDict: `if _has_self_assignments(node):` return Finding with message "Class '{symbol.name}' has no Attributes: section"
  - [ ] 3.4: Add Branch 5 for module symbols: `if symbol.kind == "module" and _is_init_module(file_path):` return Finding with message "Module '{symbol.name}' has no Attributes: section"
  - [ ] 3.5: Update docstring to document all 5 branches
  - [ ] 3.6: Ensure first-match-wins dispatch order is preserved (dataclass > NamedTuple > TypedDict > plain class > init module)

- [ ] Task 4: Update `complete_module.py` fixture (regression guard)
  - [ ] 4.1: Verify the existing fixture still produces zero findings (it already has a dataclass with `Attributes:`)
  - [ ] 4.2: Add a plain class with `__init__` self-assignments and a complete `Attributes:` section

- [ ] Task 5: Write unit tests for `_has_self_assignments` helper (AC: #9, #11)
  - [ ] 5.1: `test_has_self_assignments_when_init_with_simple_assign_returns_true`
  - [ ] 5.2: `test_has_self_assignments_when_init_with_annotated_assign_returns_true`
  - [ ] 5.3: `test_has_self_assignments_when_no_init_returns_false`
  - [ ] 5.4: `test_has_self_assignments_when_init_without_self_assigns_returns_false`
  - [ ] 5.5: `test_has_self_assignments_when_nested_function_self_assigns_returns_false` (scope boundary)
  - [ ] 5.6: `test_has_self_assignments_when_init_assigns_local_var_returns_false` (not self.x)
  - [ ] 5.7: `test_has_self_assignments_when_init_assigns_cls_attribute_returns_false` (cls.x, not self.x)

- [ ] Task 6: Write unit tests for `_is_init_module` helper (AC: #9)
  - [ ] 6.1: `test_is_init_module_when_init_py_returns_true`
  - [ ] 6.2: `test_is_init_module_when_nested_init_py_returns_true` (e.g., "src/pkg/__init__.py")
  - [ ] 6.3: `test_is_init_module_when_regular_py_returns_false`
  - [ ] 6.4: `test_is_init_module_when_similar_name_returns_false` (e.g., "not__init__.py")

- [ ] Task 7: Write unit tests for `_check_missing_attributes` branches 4-5 (AC: #1-#8)
  - [ ] 7.1: `test_missing_attributes_when_plain_class_with_self_assigns_returns_finding` — AC #1
  - [ ] 7.2: `test_missing_attributes_when_plain_class_with_annotated_self_assigns_returns_finding` — AC #2
  - [ ] 7.3: `test_missing_attributes_when_plain_class_no_self_assigns_returns_none` — AC #3
  - [ ] 7.4: `test_missing_attributes_when_init_module_without_section_returns_finding` — AC #4
  - [ ] 7.5: `test_missing_attributes_when_init_module_with_section_returns_none` — AC #5
  - [ ] 7.6: `test_missing_attributes_when_regular_module_returns_none` — AC #6
  - [ ] 7.7: `test_missing_attributes_when_dataclass_wins_over_plain_class_returns_dataclass_finding` — AC #7
  - [ ] 7.8: `test_missing_attributes_when_nested_self_assigns_in_init_returns_none` — AC #11 (scope boundary)
  - [ ] 7.9: `test_missing_attributes_when_module_symbol_kind_accepted` — verify `kind == "module"` no longer rejected

- [ ] Task 8: Write orchestrator integration tests (AC: #10)
  - [ ] 8.1: `test_check_enrichment_when_plain_class_detected_returns_finding`
  - [ ] 8.2: `test_check_enrichment_when_init_module_detected_returns_finding`
  - [ ] 8.3: `test_check_enrichment_when_complete_module_with_plain_class_returns_empty` (regression)
  - [ ] 8.4: Update `test_check_enrichment_when_active_rules_disabled_returns_empty` — add plain class + `__init__.py` source if needed

- [ ] Task 9: Run quality gates and verify all pass
  - [ ] 9.1: `uv run ruff check .` — All checks pass
  - [ ] 9.2: `uv run ruff format --check .` — All files formatted
  - [ ] 9.3: `uv run ty check` — All type checks pass
  - [ ] 9.4: `uv run pytest tests/unit/checks/ -v` — All enrichment tests pass
  - [ ] 9.5: `uv run pytest` — Full suite passes (0 regressions)

## Dev Notes

### Scope

This story completes the `missing-attributes` rule by adding the final 2 branches of the 5-branch dispatch. After this story, all class-like constructs and `__init__.py` modules are covered.

New functions in `checks/enrichment.py`:
1. **`_has_self_assignments(node: ast.ClassDef) -> bool`** — Finds `__init__` method and checks for `self.x = ...` patterns
2. **`_is_init_module(file_path: str) -> bool`** — Checks if file is `__init__.py`

Modified functions:
3. **`_check_missing_attributes`** — Kind guard changes from `!= "class"` to `not in ("class", "module")`, adds Branch 4 (plain class) and Branch 5 (init module)

### Critical Implementation Detail: Kind Guard Change

The current `_check_missing_attributes` has:
```python
if symbol.kind != "class":
    return None
```

This MUST change to:
```python
if symbol.kind not in ("class", "module"):
    return None
```

The class-specific logic (node_index lookup, isinstance guard, branches 1-4) should be gated on `symbol.kind == "class"`. The module branch (branch 5) should be gated on `symbol.kind == "module"`.

**Proposed internal structure:**
```python
def _check_missing_attributes(symbol, sections, node_index, config, file_path):
    if symbol.kind not in ("class", "module"):
        return None

    if "Attributes" in sections:
        return None

    # Class branches (1-4)
    if symbol.kind == "class":
        node = node_index.get(symbol.line)
        if node is None or not isinstance(node, ast.ClassDef):
            return None

        # Branch 1: Dataclass
        if _is_dataclass(node):
            return Finding(...)
        # Branch 2: NamedTuple
        if _is_namedtuple(node):
            return Finding(...)
        # Branch 3: TypedDict
        if _is_typeddict(node):
            return Finding(...)
        # Branch 4: Plain class with __init__ self-assignments
        if _has_self_assignments(node):
            return Finding(...)

        return None

    # Module branch (5)
    if _is_init_module(file_path):
        return Finding(...)

    return None
```

### AST Detection: Plain Class Self-Assignments

**Finding `__init__`:**
```python
# Direct .body iteration (NOT ast.walk — we want only immediate methods)
for item in node.body:
    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
        init_node = item
        break
```

**Scope-aware walk of `__init__` body:**
```python
stack = list(ast.iter_child_nodes(init_node))
while stack:
    child = stack.pop()
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        continue  # Don't descend into nested scopes
    # Check for self.x = value (ast.Assign)
    if isinstance(child, ast.Assign):
        for target in child.targets:
            if (isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"):
                return True
    # Check for self.x: int = value (ast.AnnAssign)
    if (isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Attribute)
        and isinstance(child.target.value, ast.Name)
        and child.target.value.id == "self"):
        return True
    stack.extend(ast.iter_child_nodes(child))
```

**Why scope-aware walk matters here:** A nested function inside `__init__` could contain `self.x = ...` referring to closure variables. Without scope boundary stops, `_has_self_assignments` would falsely detect those as class attributes.

### AST Detection: `__init__.py` Module

This is the simplest detection — pure string check:
```python
def _is_init_module(file_path: str) -> bool:
    return file_path.endswith("__init__.py")
```

No AST needed. The `file_path` is passed through from the CLI and already uses the OS-appropriate path separator. Using `endswith` handles both absolute and relative paths, and works cross-platform since `__init__.py` is always the filename regardless of directory separators.

### Finding Message Format

Per architecture Decision 4 (consistent with Story 2.1):
- Branch 4 (plain class): `Class '{symbol.name}' has no Attributes: section`
- Branch 5 (init module): `Module '{symbol.name}' has no Attributes: section`

The construct type prefix distinguishes which branch matched.

Note: For module symbols, `symbol.name` is `"<module>"` (set by `get_documented_symbols`).

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | MODIFIED — Add `_has_self_assignments()`, `_is_init_module()`, modify `_check_missing_attributes()` |
| `tests/unit/checks/test_enrichment.py` | MODIFIED — Add tests for helpers, branches 4-5, orchestrator integration |
| `tests/fixtures/complete_module.py` | MODIFIED — Add plain class with `Attributes:` section for zero-findings regression |

### What NOT to Do

- Do NOT put config gating inside `_check_missing_attributes` — the orchestrator handles it
- Do NOT use `ast.walk()` to find `__init__` — use direct `.body` iteration on the ClassDef
- Do NOT use `ast.walk()` inside `__init__` body — use scope-aware iterative walk
- Do NOT catch exceptions in helpers or `_check_*` — correctness through design (Decision 5)
- Do NOT return a list from `_check_*` — return `Finding | None`
- Do NOT use dynamic strings for `rule` or `category` — use literals `"missing-attributes"` and `"required"`
- Do NOT break existing branches 1-3 (dataclass, NamedTuple, TypedDict) — the kind guard change is the only modification to existing logic
- Do NOT use `os.path` or `pathlib` for the `__init__.py` check — `str.endswith()` is sufficient and has no import overhead
- Do NOT check for `typing_extensions` variants — MVP scope
- Do NOT walk nested scopes in `_has_self_assignments` — nested function `self.x = ...` is NOT a class attribute

### Testing Strategy

**Dual testing strategy (architecture spec):** `missing-attributes` branches 4-5 follow the same pattern as branches 1-3.

**Direct helper tests (`_has_self_assignments`, `_is_init_module`):**
- Each helper gets positive and negative test cases
- Use inline AST parsing for `_has_self_assignments`: `ast.parse("class Foo:\n def __init__(self):\n  self.x = 1").body[0]`
- Use plain string inputs for `_is_init_module`
- Test scope boundary: nested function inside `__init__` with self-assignments must NOT trigger

**Direct `_check_missing_attributes` tests:**
- Test branches 4-5 independently (plain class with self-assigns, init module)
- Test section-present guard still works for both branches
- Test first-match-wins: dataclass decorator + self-assignments → dataclass branch wins
- Test module symbol handling (kind == "module" now accepted)
- Test regular (non-init) module returns None

**Orchestrator integration tests:**
- Config gating regression (require_attributes = False)
- Complete module regression with plain class
- Init module detection through check_enrichment

**Test helper for module symbols:**
The existing `_make_symbol_and_index` returns the first non-module symbol. For init module tests, you need the MODULE symbol specifically:
```python
# Get module symbol for __init__.py tests
from docvet.ast_utils import get_documented_symbols
tree = ast.parse(source)
symbols = get_documented_symbols(tree)
module_symbol = [s for s in symbols if s.kind == "module"][0]
```

### Previous Story Intelligence

**From Story 2.1 (Dataclass/NamedTuple/TypedDict):**
- `_make_symbol_and_index` returns first non-module symbol — works for single-class sources
- `isinstance(node, ast.ClassDef)` guard needed for ty type-narrowing
- "All rules disabled" test updated to disable 6 rules in Story 2.1 — may need update if test source changes
- Direct helper testing pattern established: `ast.parse("...").body[0]`
- Finding message format: `{ConstructType} '{symbol.name}' has no Attributes: section`

**From Epic 1 Retrospective:**
- Scope-aware walk is CRITICAL — `_has_self_assignments` MUST use iterative walk with scope boundary stops in `__init__` body
- Dev agents consistently under-test edge cases on first pass — proactively add scope boundary tests
- `ast.walk()` false positive was caught in code review for Story 1.4 — same risk exists here for nested functions inside `__init__`

**Cross-story guard pattern — the 5 guards every `_check_*` has:**
1. `symbol.kind` guard — NOW allows both "class" and "module"
2. Section-present guard — `"Attributes" in sections` (shared early return)
3. Node index guard — only for class branch (module branch doesn't use node_index)
4. Type narrowing guard — `isinstance(node, ast.ClassDef)` (for ty, class branch only)
5. Detection logic — branch 4 or 5

### File Structure Requirements

**`enrichment.py` after this story:**
```python
# Rule-specific helpers for missing-attributes (after existing helpers)
def _is_dataclass(...): ...         # existing (Story 2.1)
def _is_namedtuple(...): ...        # existing (Story 2.1)
def _is_typeddict(...): ...         # existing (Story 2.1)
def _has_self_assignments(...): ... # NEW
def _is_init_module(...): ...       # NEW

# missing-attributes rule (MODIFIED)
def _check_missing_attributes(...): ... # MODIFIED — adds branches 4-5
```

### Architecture Compliance

- Uniform `_check_*` signature: `(symbol, sections, node_index, config, file_path) -> Finding | None` — maintained
- Config gating in orchestrator: no changes to orchestrator dispatch needed (already wired in Story 2.1)
- Taxonomy-table order: `_check_missing_attributes` position unchanged
- Helper naming: `_has_self_assignments` (boolean check), `_is_init_module` (type/state check) — both follow `_has_*`/`_is_*` convention
- Finding construction: literal strings for `rule` ("missing-attributes") and `category` ("required")
- Scope-aware walk for body-level inspection in `_has_self_assignments`

### Library/Framework Requirements

**No new dependencies** — stdlib only:
- `ast` — Already imported
- No new imports needed

### FRs Covered

- FR6: Detect missing Attributes on plain classes with `__init__` self-assignments
- FR8: Detect missing Attributes on `__init__.py` modules
- FR18: One finding per symbol per rule (first-match-wins deduplication)
- FR33: Analyze class symbols to determine construct type (plain class branch)
- FR34: Analyze module symbols for `__init__.py`
- NFR5: Zero false positives on well-documented code
- NFR10: Rule independently testable

### Project Structure Notes

- 2 helper functions + modified rule function go in `src/docvet/checks/enrichment.py`
- Helpers placed after `_is_typeddict`, before `_check_missing_attributes` (same helper section)
- New tests go in `tests/unit/checks/test_enrichment.py` in new comment-separated sections
- `tests/fixtures/complete_module.py` gets a plain class with `Attributes:` section for zero-findings regression
- No new test files needed

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#missing-attributes Dispatch Order] — 5-branch priority order, first-match-wins
- [Source: _bmad-output/planning-artifacts/architecture.md#AST Inspection Patterns] — `self.*` assignment detection, direct `.body` iteration
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1] — Uniform `_check_*` signature
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] — No try/except, correctness through design
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2] — BDD acceptance criteria
- [Source: src/docvet/checks/enrichment.py:554-631] — Current `_check_missing_attributes` (to be modified)
- [Source: src/docvet/checks/enrichment.py:464-551] — Existing `_is_dataclass`, `_is_namedtuple`, `_is_typeddict` helpers (insertion point: new helpers after these)
- [Source: src/docvet/checks/enrichment.py:639-702] — `check_enrichment` orchestrator (no changes needed — already dispatches to `_check_missing_attributes`)
- [Source: src/docvet/checks/enrichment.py:77] — `_NodeT` type alias
- [Source: src/docvet/config.py:38] — `require_attributes: bool = True` (already exists)
- [Source: src/docvet/ast_utils.py:16-48] — Symbol dataclass (kind: Literal["function", "class", "method", "module"])
- [Source: src/docvet/ast_utils.py:224-256] — `get_documented_symbols` (module symbol has `name="<module>"`, `kind="module"`)
- [Source: tests/unit/checks/test_enrichment.py:247-258] — `_make_symbol_and_index` test helper
- [Source: tests/unit/checks/test_enrichment.py:1516-1698] — Existing `_check_missing_attributes` tests (branches 1-3)
- [Source: tests/fixtures/complete_module.py] — Fixture with complete docstrings (needs plain class addition)
- [Source: _bmad-output/implementation-artifacts/2-1-dataclass-namedtuple-and-typeddict-attributes-detection.md] — Previous story learnings

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
