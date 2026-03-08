# Story 34.2: `missing-returns` Enrichment Rule

Status: review
Branch: `feat/enrichment-34-2-missing-returns-rule`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag functions that return values but have no Returns section,
so that callers know what the function returns by reading its docstring.

## Acceptance Criteria

1. **Given** a function with `return <expr>` statements and a docstring with no `Returns:` section, **When** enrichment runs, **Then** a finding is emitted: `missing-returns` with message identifying the function name.

2. **Given** a function with only bare `return` or `return None` statements, **When** enrichment runs, **Then** no `missing-returns` finding is produced (control flow returns are not meaningful).

3. **Given** a function with a mix of `return value` and bare `return` statements, **When** enrichment runs, **Then** a `missing-returns` finding IS produced (at least one meaningful return exists).

4. **Given** a `@property` method, `__init__`, or any dunder method (`__repr__`, `__len__`, `__bool__`, etc.), **When** enrichment runs, **Then** no `missing-returns` finding is produced (skip set applies).

5. **Given** a function with `return <expr>` inside a nested function or class, **When** enrichment runs on the outer function, **Then** no `missing-returns` finding is produced for the outer function (scope-aware AST walk stops at nested `def`/`class`).

6. **Given** a function with a `Returns:` section already present, **When** enrichment runs, **Then** no `missing-returns` finding is produced.

7. **Given** `require-returns = false` in `[tool.docvet.enrichment]`, **When** enrichment runs, **Then** the `missing-returns` rule is skipped entirely.

8. **Given** `require-returns = true` (the default), **When** the rule is dispatched, **Then** `_check_missing_returns` follows the uniform signature `(symbol, sections, node_index, config, file_path) -> Finding | None` and is wired into `_RULE_DISPATCH` with zero dispatch changes.

9. **Given** a function with no docstring, **When** enrichment runs, **Then** no `missing-returns` finding is produced (enrichment only runs on functions that have docstrings).

10. **Given** the `missing-returns` rule is implemented and tested, **When** the story is marked done, **Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern (macros scaffold in `docs/main.py`).

11. **Given** an abstract method (decorated with `@abstractmethod`) with `return <expr>` in its body, **When** enrichment runs, **Then** no `missing-returns` finding is produced (abstract methods define interface contracts, not implementations).

12. **Given** a stub function whose body consists only of `pass`, `...` (Ellipsis), or `raise NotImplementedError`, **When** enrichment runs, **Then** no `missing-returns` finding is produced (stub functions and protocol methods have no meaningful implementation to document).

## Tasks / Subtasks

- [x] Task 1: Add `require_returns` config field (AC: 7, 8)
  - [x] 1.1 Add `require_returns: bool = True` field to `EnrichmentConfig` in `config.py` (after `require_raises`)
  - [x] 1.2 Add `"require-returns"` to `_VALID_ENRICHMENT_KEYS` frozenset in `config.py`
  - [x] 1.3 Validation already handled by the existing `else: _validate_type(value, bool, ...)` branch in `_parse_enrichment()` — no new parsing code needed
  - [x] 1.4 Update `format_config_toml()` and `format_config_json()` to include `require-returns` in enrichment section output
  - [x] 1.5 Write unit tests: default value is `True`, explicit `false` disables, format output includes field

- [x] Task 2: Implement `_check_missing_returns` function and helpers (AC: 1, 2, 3, 4, 5, 6, 8, 9, 11, 12)
  - [x] 2.1 Create `_check_missing_returns()` in `enrichment.py` following uniform `_CheckFn` signature
  - [x] 2.2 Guard: return `None` if `symbol.kind not in ("function", "method")` (AC: 9 — classes/modules skip)
  - [x] 2.3 Guard: return `None` if `"Returns" in sections` (AC: 6)
  - [x] 2.4 Guard: return `None` if symbol is a `@property`/`@cached_property`, `__init__`, or dunder method (AC: 4). Use `_is_property()` helper. Detect dunders via `symbol.name.startswith("__") and symbol.name.endswith("__")`.
  - [x] 2.5 Guard: return `None` if `@abstractmethod` decorated (AC: 11). Use `_has_decorator()` helper.
  - [x] 2.6 Guard: return `None` if stub function — body is only `pass`, `...`, or `raise NotImplementedError` (AC: 12). Use `_is_stub_function()` helper.
  - [x] 2.7 Guard: return `None` if `@overload` decorated (defensive skip — Story 34.4 owns overload detection, but this rule should not false-positive on overloads). Use `_has_decorator()` helper.
  - [x] 2.8 Get `node` from `node_index.get(symbol.line)`; return `None` if not found
  - [x] 2.9 Walk the AST subtree scope-aware (stop at nested `FunctionDef`, `AsyncFunctionDef`, `ClassDef`) looking for `ast.Return` nodes
  - [x] 2.10 For each `ast.Return`, check if `node.value` is not `None` AND is not `ast.Constant(value=None)` — these are meaningful returns (AC: 1, 2, 3). Use `_is_meaningful_return()` helper.
  - [x] 2.11 If at least one meaningful return found, emit `Finding(rule="missing-returns", category="required", ...)`
  - [x] 2.12 If no meaningful returns, return `None` (AC: 2)
  - [x] 2.13 Create `_is_property(node) -> bool` helper: check `decorator_list` for `property` and `cached_property` (both `ast.Name` and `ast.Attribute` forms)
  - [x] 2.14 Create `_has_decorator(node, name: str) -> bool` helper: reusable decorator detection for `abstractmethod`, `overload`, etc. Checks both `ast.Name(id=name)` and `ast.Attribute(attr=name)` forms.
  - [x] 2.15 Create `_is_stub_function(node) -> bool` helper: returns `True` if function body is a single statement that is `pass`, `Expr(Constant(Ellipsis))`, or `Raise(exc=Call(func=Name(id="NotImplementedError")))`.
  - [x] 2.16 Create `_is_meaningful_return(node: ast.Return) -> bool` helper: returns `False` for bare `return` and `return None`, `True` otherwise.

- [x] Task 3: Wire into `_RULE_DISPATCH` (AC: 8)
  - [x] 3.1 Add `("require_returns", _check_missing_returns)` to `_RULE_DISPATCH` tuple (after `require_raises`)
  - [x] 3.2 Verify zero dispatch machinery changes needed — orchestrator handles new entry automatically

- [x] Task 4: Write comprehensive tests (AC: 1-12)
  - [x] 4.1 Create `tests/unit/checks/test_missing_returns.py` (dedicated file per test-review recommendation 2)
  - [x] 4.2 Use `_make_symbol_and_index()` helper pattern from `test_prefer_fenced_code_blocks.py`
  - [x] 4.3 Test: function with `return value` and no Returns section — finding emitted (AC: 1)
  - [x] 4.4 Test: function with bare `return` only — no finding (AC: 2)
  - [x] 4.5 Test: function with `return None` only — no finding (AC: 2)
  - [x] 4.6 Test: function with mix of `return value` and bare `return` — finding emitted (AC: 3)
  - [x] 4.7 Test: `@property` method — no finding (AC: 4)
  - [x] 4.8 Test: `__init__` method — no finding (AC: 4)
  - [x] 4.9 Test: dunder method (`__repr__`, `__len__`, `__bool__`) — no finding (AC: 4)
  - [x] 4.10 Test: `return value` inside nested function — no finding for outer (AC: 5)
  - [x] 4.11 Test: `return value` inside nested class — no finding for outer (AC: 5)
  - [x] 4.12 Test: function with `Returns:` section present — no finding (AC: 6)
  - [x] 4.13 Test: `require-returns = false` config — rule skipped (AC: 7)
  - [x] 4.14 Test: function with no docstring — no finding (AC: 9, handled by orchestrator)
  - [x] 4.15 Test: class symbol — no finding (not a function/method)
  - [x] 4.16 Test: async function with `return value` and no Returns section — finding emitted
  - [x] 4.17 Negative assertion: function with Returns section AND return value — zero findings
  - [x] 4.18 Add `pytestmark = pytest.mark.unit` at module level
  - [x] 4.19 Test: `@abstractmethod` with `return value` — no finding (AC: 11)
  - [x] 4.20 Test: stub function with `pass` body and return annotation — no finding (AC: 12)
  - [x] 4.21 Test: stub function with `...` (Ellipsis) body and return annotation — no finding (AC: 12)
  - [x] 4.22 Test: stub function with `raise NotImplementedError` body — no finding (AC: 12)
  - [x] 4.23 Test: `@overload` function with return value — no finding (defensive skip)
  - [x] 4.24 Test: `@cached_property` method — no finding (AC: 4)

- [x] Task 5: Rule reference page and registration (AC: 10)
  - [x] 5.1 Add entry to `docs/rules.yml` with id `missing-returns`, check `enrichment`, category `required`, since `1.13.0`
  - [x] 5.2 Verify `docs/main.py` auto-discovers the new rule (macros scaffold handles rendering)
  - [x] 5.3 Run `mkdocs build --strict` to verify docs build passes

- [x] Task 6: Dogfooding and integration verification
  - [x] 6.1 Run `docvet check --all` on own codebase — either zero new findings or fix any legitimate missing-returns findings in docvet's own code
  - [x] 6.2 All quality gates pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_function_with_return_value_and_no_returns_section_emits_finding` | PASS |
| 2 | `test_function_with_bare_return_only_no_finding`, `test_function_with_return_none_only_no_finding` | PASS |
| 3 | `test_function_with_mixed_returns_emits_finding` | PASS |
| 4 | `test_property_method_no_finding`, `test_init_method_no_finding`, `test_dunder_repr_no_finding`, `test_dunder_len_no_finding`, `test_dunder_bool_no_finding`, `test_cached_property_no_finding` | PASS |
| 5 | `test_return_in_nested_function_no_finding_for_outer`, `test_return_in_nested_class_no_finding_for_outer` | PASS |
| 6 | `test_function_with_returns_section_present_no_finding` | PASS |
| 7 | `test_require_returns_false_config_skips_rule`, `test_enrichment_defaults_require_returns_is_true`, `test_load_config_nested_enrichment_require_returns_false` | PASS |
| 8 | `test_function_with_return_value_and_no_returns_section_emits_finding` (verifies uniform signature + dispatch) | PASS |
| 9 | `test_function_without_docstring_no_finding` | PASS |
| 10 | `test_rule_count` (updated to 21), `mkdocs build --strict` passes | PASS |
| 11 | `test_abstractmethod_with_return_no_finding` | PASS |
| 12 | `test_stub_function_with_pass_no_finding`, `test_stub_function_with_ellipsis_no_finding`, `test_stub_function_with_raise_not_implemented_no_finding` | PASS |

## Dev Notes

### Architecture — Config Layer Changes

**File: `src/docvet/config.py`**

- `EnrichmentConfig` (line ~88-144): Add `require_returns: bool = True` after `require_raises`. This is a simple bool toggle — the existing `_parse_enrichment()` validation already handles bool fields via the `else: _validate_type(value, bool, ...)` branch (line 522-523).
- `_VALID_ENRICHMENT_KEYS` (line 270-283): Add `"require-returns"` to the frozenset. This is the only validation registration needed.
- `format_config_toml()` and `format_config_json()`: Include `require-returns` in the enrichment section render.
- **No new parsing logic needed** — the generic bool handler covers it automatically.

### Architecture — Enrichment Layer Changes

**File: `src/docvet/checks/enrichment.py`**

- **New function**: `_check_missing_returns()` — follows identical pattern to `_check_missing_yields()` (lines 347-407). The only difference is the AST node type being searched (`ast.Return` vs `ast.Yield`/`ast.YieldFrom`) and the additional check for meaningful return values (skip bare `return` and `return None`).

- **AST detection logic**: Walk the function body scope-aware (stop at nested `def`/`class`). For each `ast.Return` node:
  - `node.value is None` → bare `return` (control flow) → skip
  - `isinstance(node.value, ast.Constant) and node.value.value is None` → `return None` → skip
  - Anything else → meaningful return → flag

- **Skip set**: `missing-returns` has a broader skip set than other enrichment rules to prevent false positives (informed by pydoclint DOC201 and ruff DOC201 edge cases). The full skip set:
  - **Dunder methods**: `symbol.name.startswith("__") and symbol.name.endswith("__")` — covers `__init__`, `__repr__`, `__len__`, `__bool__`, `__new__`, `__str__`, etc.
  - **`@property` / `@cached_property`**: Use `_is_property()` helper — checks `decorator_list` for both `property` and `cached_property` (both `ast.Name` and `ast.Attribute` forms). `functools.cached_property` has identical semantics to `@property` for documentation purposes.
  - **`@abstractmethod`**: Use `_has_decorator(node, "abstractmethod")` — abstract methods define interface contracts, not implementations. Return type annotations serve as the contract; a `Returns:` section is noise.
  - **Stub functions**: Use `_is_stub_function()` — body is a single `pass`, `...` (Ellipsis), or `raise NotImplementedError`. Common in protocols, type stubs, and placeholder implementations.
  - **`@overload`**: Use `_has_decorator(node, "overload")` — defensive skip. Story 34.4 owns overload detection, but `missing-returns` should not independently false-positive on overloads.

- **`_RULE_DISPATCH` table** (line 1481-1492): Add `("require_returns", _check_missing_returns)` — position after `require_raises` for logical grouping.

- **Sphinx behavior**: `missing-returns` works identically in both Google and Sphinx styles. Both styles detect `Returns` as a section name via `_parse_sections()`. Do NOT add `require_returns` to `_SPHINX_AUTO_DISABLE_RULES`.

### Architecture — Orchestrator (Zero Changes)

The dispatch loop in `check_enrichment()` (lines 1537-1546) already handles:
- Config gating via `getattr(config, attr)` — checks `config.require_returns`
- Sphinx auto-disable (not applicable to this rule)
- Finding collection

No orchestrator changes needed.

### Key Implementation Pattern (from `_check_missing_yields`)

```python
def _check_missing_returns(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    if symbol.kind not in ("function", "method"):
        return None
    node = node_index.get(symbol.line)
    if node is None:
        return None
    if "Returns" in sections:
        return None
    # Skip dunder methods (covers __init__, __repr__, __len__, __new__, etc.)
    if symbol.name.startswith("__") and symbol.name.endswith("__"):
        return None
    # Skip @property and @cached_property methods
    if _is_property(node):
        return None
    # Skip @abstractmethod (interface contracts, not implementations)
    if _has_decorator(node, "abstractmethod"):
        return None
    # Skip stub functions (pass, ..., raise NotImplementedError)
    if _is_stub_function(node):
        return None
    # Skip @overload (defensive — 34.4 owns overload detection)
    if _has_decorator(node, "overload"):
        return None
    # Scope-aware walk for meaningful return statements
    has_meaningful_return = False
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Return) and _is_meaningful_return(child):
            has_meaningful_return = True
            break
        stack.extend(ast.iter_child_nodes(child))
    if not has_meaningful_return:
        return None
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-returns",
        message=f"Function '{symbol.name}' returns a value but has no Returns: section",
        category="required",
    )
```

**Helper `_is_meaningful_return(node: ast.Return) -> bool`**:
```python
def _is_meaningful_return(node: ast.Return) -> bool:
    if node.value is None:
        return False  # bare `return`
    if isinstance(node.value, ast.Constant) and node.value.value is None:
        return False  # `return None`
    return True
```

**Helper `_is_property(node) -> bool`**:
```python
def _is_property(node) -> bool:
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Name) and dec.id in ("property", "cached_property"):
            return True
        if isinstance(dec, ast.Attribute) and dec.attr in ("property", "cached_property"):
            return True
    return False
```

**Helper `_has_decorator(node, name: str) -> bool`** (reusable by Stories 34.4, 35.x):
```python
def _has_decorator(node, name: str) -> bool:
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Name) and dec.id == name:
            return True
        if isinstance(dec, ast.Attribute) and dec.attr == name:
            return True
    return False
```

**Helper `_is_stub_function(node) -> bool`**:
```python
def _is_stub_function(node) -> bool:
    if len(node.body) != 1:
        return False
    stmt = node.body[0]
    # pass
    if isinstance(stmt, ast.Pass):
        return True
    # ... (Ellipsis)
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
        return True
    # raise NotImplementedError / raise NotImplementedError(...)
    if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, (ast.Name, ast.Call)):
        exc = stmt.exc.func if isinstance(stmt.exc, ast.Call) else stmt.exc
        return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"
    return False
```

**Design decision**: All helpers are module-private standalone functions (not methods on a class). Follows the existing pattern in enrichment.py (e.g., `_has_docstring_body`, `_extract_section_content`). `_has_decorator()` and `_is_stub_function()` are intentionally reusable — Stories 34.4 (`@overload` detection) and Epic 35 stories will need them.

### Test Strategy

**File: `tests/unit/checks/test_missing_returns.py`** (new, dedicated file per test-review recommendation 2)

Follow the pattern from `test_prefer_fenced_code_blocks.py`:
- Module-level `pytestmark = pytest.mark.unit`
- Import `_make_symbol_and_index` helper (or define locally)
- Import `_check_missing_returns` directly from enrichment module
- Test both direct function calls AND orchestrator-level behavior (config gating)
- All 6 Finding fields asserted on positive cases
- `assert len(findings) == 0` on negative cases
- AC-labeled docstrings for traceability

### Test Maturity Piggyback

From test-review.md — Recommendation 2 (P3): Continue splitting `test_enrichment.py` by rule. This story naturally addresses it by creating a dedicated `test_missing_returns.py` file instead of adding to the monolithic test file.

### Project Structure Notes

- All changes align with existing project structure
- New file: `tests/unit/checks/test_missing_returns.py` (follows recommendation to split by rule)
- Modified files: `src/docvet/config.py`, `src/docvet/checks/enrichment.py`, `docs/rules.yml`
- No new modules, packages, or dependencies

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 34.2] — Full AC and FR mapping (FR7-FR8)
- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Requirements Inventory] — NFR3, NFR4
- [Source: src/docvet/checks/enrichment.py:347-407] — `_check_missing_yields` as pattern template
- [Source: src/docvet/checks/enrichment.py:1481-1492] — `_RULE_DISPATCH` table
- [Source: src/docvet/config.py:88-144] — `EnrichmentConfig` dataclass
- [Source: src/docvet/config.py:270-283] — `_VALID_ENRICHMENT_KEYS` frozenset
- [Source: tests/unit/checks/test_prefer_fenced_code_blocks.py] — Test pattern reference (dedicated file, `_make_symbol_and_index` helper)
- [Source: _bmad-output/test-artifacts/test-review.md#Recommendation 2] — Test file splitting recommendation
- [Source: _bmad-output/implementation-artifacts/34-1-sphinx-rst-docstring-style-support.md] — Previous story intelligence
- [Competitive: ruff DOC201] — Excludes abstract methods, stub functions, `__new__`, `@property`. "Returns" in summary debate ongoing. Rule is preview/unstable.
- [Competitive: pydoclint DOC201] — Excludes abstract methods, stub functions, `@property`. Baseline exclusion set we must match.
- [Party-mode consensus 2026-03-07] — Added AC 11 (abstract skip), AC 12 (stub skip), defensive `@overload` skip, `cached_property` in `_is_property()`. Deferred "Returns in summary" heuristic.

### Documentation Impact

- Pages: docs/site/rules/missing-returns.md (auto-generated from rules.yml via macros scaffold)
- Nature of update: New rule reference page registered in `docs/rules.yml` with id, name, check, category, applies_to, summary, since, and fix guidance

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1376 passed, zero failures
- [x] `uv run docvet check --all` — zero required findings (3 recommended stale-body from in-flight changes)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed ty type errors: added `assert symbol.docstring is not None` narrowing before `_parse_sections()` calls in 6 test cases
- Updated `_EXPECTED_RULE_COUNT` from 20 to 21 in `test_docs_infrastructure.py` to account for new rule

### Completion Notes List

- Implemented `missing-returns` enrichment rule with 4 reusable helpers (`_is_meaningful_return`, `_is_property`, `_has_decorator`, `_is_stub_function`)
- Rule follows identical pattern to `_check_missing_yields` with additional guard clauses for broader skip set
- 23 dedicated tests in `test_missing_returns.py` + 3 config tests in `test_config.py` = 26 new tests
- Zero dispatch machinery changes — wired via single `_RULE_DISPATCH` entry
- Rule reference page created with macros scaffold integration
- All quality gates pass: ruff, ty, pytest (1376), docvet dogfooding

### Change Log

- 2026-03-07: Implemented `missing-returns` enrichment rule (Story 34.2)

### File List

- `src/docvet/config.py` — added `require_returns: bool = True` to `EnrichmentConfig`, `"require-returns"` to `_VALID_ENRICHMENT_KEYS`, and entry to `format_config_toml()`
- `src/docvet/checks/enrichment.py` — added `_is_meaningful_return()`, `_is_property()`, `_has_decorator()`, `_is_stub_function()`, `_check_missing_returns()`, and `_RULE_DISPATCH` entry
- `tests/unit/checks/test_missing_returns.py` — new file, 23 tests
- `tests/unit/test_config.py` — 3 new config tests for `require_returns`
- `tests/unit/test_docs_infrastructure.py` — updated `_EXPECTED_RULE_COUNT` from 20 to 21
- `docs/rules.yml` — added `missing-returns` rule entry
- `docs/site/rules/missing-returns.md` — new rule reference page
- `mkdocs.yml` — added `missing-returns` to nav
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status update

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
