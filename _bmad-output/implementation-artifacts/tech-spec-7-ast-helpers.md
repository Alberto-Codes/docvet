---
title: 'Shared AST Helpers'
slug: '7-ast-helpers'
created: '2026-02-08'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python-stdlib-ast']
files_to_modify: ['src/docvet/ast_utils.py', 'tests/unit/test_ast_utils.py', 'tests/fixtures/nested_symbols.py']
code_patterns: ['dataclass', 'ast-visitor', 'factory-fixture']
test_patterns: ['source-string-fixtures', 'parametrize', 'one-assert-per-test']
---

# Tech-Spec: Shared AST Helpers

**Created:** 2026-02-08

## Overview

### Problem Statement

Multiple checks (enrichment, freshness) need to parse Python files into AST and extract information about functions, classes, docstrings, and their line ranges. Without shared helpers, each check would duplicate AST walking, docstring extraction, and line-range logic.

### Solution

Create `src/docvet/ast_utils.py` with a frozen `Symbol` dataclass and five core functions (`get_documented_symbols`, `get_docstring_range`, `get_body_range`, `get_signature_range`, `map_lines_to_symbols`) that provide a clean abstraction over `ast` module internals for downstream checks.

### Scope

**In Scope:**
- `src/docvet/ast_utils.py` — `Symbol` dataclass + 5 core functions
- `tests/unit/test_ast_utils.py` — comprehensive unit tests
- Test fixture updates in `tests/fixtures/` if needed for thorough coverage

**Out of Scope:**
- Wiring into CLI stubs or check modules (enrichment/freshness consume this later)
- Any runtime dependencies beyond stdlib `ast`
- Support for non-Google docstring styles

## Context for Development

### Codebase Patterns

- Every file starts with `from __future__ import annotations`
- Modern type hints only (`list[str]`, `X | None`)
- Google-style docstrings on all public functions/classes
- No mutable defaults, no bare exceptions
- `frozen=True` dataclasses for immutable data structures (see `config.py:DocvetConfig`, `FreshnessConfig`, `EnrichmentConfig`)
- AST tests use source string fixtures via `parse_source` factory — never mock AST nodes
- Module structure: section dividers with `# ---...` comment blocks
- Public API separated from private helpers with `_` prefix
- `field(default_factory=...)` for mutable defaults in dataclasses
- Existing `parse_source` fixture in `tests/conftest.py` returns a callable that wraps `ast.parse()`
- Existing fixture files are simple, single-concept Python files (one function each)
- `Literal` type used for constrained string values (use for `Symbol.kind`)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/ast_utils.py` | New module to create |
| `tests/unit/test_ast_utils.py` | New test file to create |
| `tests/conftest.py` | Contains `parse_source` fixture factory |
| `tests/fixtures/missing_raises.py` | Existing fixture — function with raise |
| `tests/fixtures/missing_yields.py` | Existing fixture — generator function |
| `tests/fixtures/complete_module.py` | Existing fixture — well-documented module |
| `tests/fixtures/nested_symbols.py` | New fixture — nesting depth, decorators, multi-line sigs |
| `docs/product-vision.md` | Detection rules for enrichment patterns |
| `src/docvet/config.py` | Reference for `frozen=True` dataclass pattern, section dividers |
| `src/docvet/discovery.py` | Reference for private helper pattern, public API structure |
| `src/docvet/cli.py` | Downstream consumer — `_run_enrichment()` / `_run_freshness()` stubs |
| `pyproject.toml` | Pytest markers, ruff config, interrogate thresholds |

### Technical Decisions

1. **Module body_range**: For modules, `body_range` follows the same rule as all other nodes: excludes the docstring. A module with a docstring on lines 1-3 and code on lines 5-10 gets `body_range=(4, 10)`. A module with no docstring gets `body_range=(1, end_lineno)`. Empty module edge case: `body_range = (1, 1)`.
2. **Nested symbols**: `map_lines_to_symbols` returns the innermost containing symbol (most specific scope wins), matching ruff/pyright behavior.
3. **Decorators excluded from signature, included in definition**: `signature_range` starts at the `def`/`class` keyword line (Python 3.8+ `lineno` points to `def`, not first decorator). However, `map_lines_to_symbols` uses the full definition range (`definition_start` through `end_line`) so decorator changes map to the decorated function. `definition_start` is stored on `Symbol` to avoid a second AST walk.
4. **Flat list, not tree**: `get_documented_symbols` returns a flat list of all symbols. Parent context is tracked via the `parent` field on `Symbol`. No tree structures.
5. **`parent` semantics**: Immediate enclosing **class** name only. Methods get `parent="ClassName"`. Functions nested inside functions get `parent=None`. Nested class methods get `parent="InnerClassName"`.
6. **Multi-line signature handling**: `get_signature_range` uses `(node.lineno, max(node.lineno, node.body[0].lineno - 1))`. For single-line functions where `body[0].lineno == node.lineno`, the `max()` ensures `(lineno, lineno)`. For single-line `def f(): """doc"""`, signature_range is `(lineno, lineno)` — the signature range is line-level granularity and includes the entire `def` line regardless of inline content. This is acceptable since signature changes are detected at line level, not character level.
7. **Lambdas out of scope**: Not documentable symbols. `Symbol.kind` is `Literal["function", "class", "method", "module"]` — no lambda, comprehension, or import nodes.
8. **Primary vs building-block API**: `get_documented_symbols` and `map_lines_to_symbols` are the two main entry points for downstream checks. The three range functions are public building blocks.
9. **`signature_range` is functions-only**: `get_signature_range` only accepts `FunctionDef | AsyncFunctionDef`. For `ClassDef` and module symbols, `get_documented_symbols` sets `signature_range=None`.
10. **`Symbol.line` vs `definition_start`**: `line` is always `node.lineno` (the `def`/`class` keyword line, NOT the first decorator). `definition_start` is `decorator_list[0].lineno` if decorators exist, else `node.lineno`. For undecorated symbols, `line == definition_start`. For decorated symbols, `definition_start < line`. For module symbols, both are `1`.
11. **Module `Symbol` conventions**: `name` is `"<module>"` (constant string). `line = 1`, `definition_start = 1`, `end_line = tree.end_lineno` (or `1` for empty modules). `signature_range = None`, `parent = None`. Trailing blank lines/comments after the last statement may not be covered by `tree.end_lineno` — this is acceptable since those lines contain no documentable code.
12. **`get_body_range` degenerate cases**: When a function/class body contains ONLY a docstring (no other statements), `body_range = (docstring_end_line + 1, node.end_lineno)`. If `docstring_end_line + 1 > node.end_lineno` (single-line case), return `(node.end_lineno, node.end_lineno)`. This range points at the closing line and represents "effectively empty body" — downstream consumers should treat a zero-width or single-line body range as having no meaningful code to check.
13. **Type narrowing for range functions**: `get_docstring_range` and `get_body_range` accept `ast.AST` but only operate on nodes with a `body` attribute (`Module`, `FunctionDef`, `AsyncFunctionDef`, `ClassDef`). If a node lacks `body` or has empty `body`, `get_docstring_range` returns `None`. `get_body_range` returns `(node.end_lineno, node.end_lineno)` for nodes with no body statements (degenerate case). Use `hasattr(node, "body")` guard.
14. **`map_lines_to_symbols` line count**: Derives total line count from the module symbol's `end_line` (which equals `tree.end_lineno`). Iterates lines `1..end_line` inclusive. For empty modules where `end_line=1`, the dict contains a single entry mapping line 1 to the module symbol.
15. **Caller responsibility for valid AST**: All functions in `ast_utils.py` assume they receive well-formed AST from `ast.parse()` on valid Python source. Handling `SyntaxError` is the caller's responsibility. Functions do NOT need to guard against `None` values in `lineno`/`end_lineno` on well-formed nodes.
16. **Stdlib only**: Uses `ast` module exclusively — no runtime dependencies.
17. **Google-style assumed**: Docstring content parsing is out of scope for this module; it extracts raw docstring text and ranges only.

## Implementation Plan

### Tasks

- [x] Task 1: Create the `Symbol` dataclass
  - File: `src/docvet/ast_utils.py`
  - Action: Create new module with `from __future__ import annotations`, module docstring, and `Symbol` frozen dataclass with fields: `name: str`, `kind: Literal["function", "class", "method", "module"]`, `line: int`, `end_line: int`, `definition_start: int`, `docstring: str | None`, `docstring_range: tuple[int, int] | None`, `signature_range: tuple[int, int] | None`, `body_range: tuple[int, int]`, `parent: str | None`
  - Notes: Follow `config.py` pattern — `@dataclass(frozen=True)`. Import `Literal` from `typing`. Use section dividers matching codebase convention. Field semantics: `line` = `node.lineno` (the `def`/`class` keyword, NOT first decorator); `definition_start` = `decorator_list[0].lineno` if decorators exist, else `node.lineno`; `name` = `"<module>"` for module symbols; `signature_range = None` for classes and modules; `parent` = immediate enclosing class name only (not functions). For module symbols: `line=1`, `definition_start=1`, `end_line=tree.end_lineno` (or `1` for empty modules).

- [x] Task 2: Implement `get_docstring_range`
  - File: `src/docvet/ast_utils.py`
  - Action: Add function `get_docstring_range(node: ast.AST) -> tuple[int, int] | None`. Guard with `hasattr(node, "body")` — return `None` if no `body` attribute. Check if `body` is non-empty and `body[0]` is `ast.Expr` wrapping `ast.Constant` with a `str` value. Return `(expr.lineno, expr.end_lineno)` or `None`.
  - Notes: Works for `Module`, `FunctionDef`, `AsyncFunctionDef`, `ClassDef`. Returns `None` for: nodes without `body`, empty bodies, body[0] not a string constant docstring, or any non-documentable node type passed in.

- [x] Task 3: Implement `get_body_range`
  - File: `src/docvet/ast_utils.py`
  - Action: Add function `get_body_range(node: ast.AST) -> tuple[int, int]`. Guard with `hasattr(node, "body")`. Return `(start_line, end_line)` of the body excluding the docstring. If node has a docstring, start at `docstring_end_line + 1`. If no docstring, start at `body[0].lineno`. End at `node.end_lineno`.
  - Notes: For nodes without `body` or with empty `body`, return `(node.end_lineno, node.end_lineno)` (degenerate). For empty modules (`ast.parse("")`), return `(1, 1)`. For functions whose body is **only** a docstring (no other statements after docstring), return `(docstring_end_line + 1, node.end_lineno)` — if that produces `start > end`, clamp to `(node.end_lineno, node.end_lineno)`. Downstream consumers should treat a body_range where `start >= end` as "effectively empty — no meaningful code to check."

- [x] Task 4: Implement `get_signature_range`
  - File: `src/docvet/ast_utils.py`
  - Action: Add function `get_signature_range(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]`. Return `(node.lineno, max(node.lineno, node.body[0].lineno - 1))`. Excludes decorators (uses `node.lineno` which points to `def` keyword in Python 3.8+).
  - Notes: Single-line functions (`def f(): pass`) return `(lineno, lineno)`. Multi-line signatures spanning several lines correctly capture through `body[0].lineno - 1`.

- [x] Task 5: Implement `get_documented_symbols`
  - File: `src/docvet/ast_utils.py`
  - Action: Add function `get_documented_symbols(tree: ast.Module) -> list[Symbol]`. Walk the AST recursively, extracting `Symbol` instances for: the module itself, all `FunctionDef`/`AsyncFunctionDef` nodes, and all `ClassDef` nodes. Track parent class context during recursion. Set `kind="method"` for functions directly inside a class body.
  - Notes: Returns flat list ordered by line number. Module symbol: `name="<module>"`, `line=1`, `definition_start=1`, `end_line=tree.end_lineno or 1`, `signature_range=None`, `parent=None`. Class symbols: `signature_range=None`. Function/method symbols: `signature_range` from `get_signature_range()`. `definition_start` = `decorator_list[0].lineno` if decorators, else `node.lineno`. `parent` is set only when inside a class (not when nested inside a function). Private helper `_walk_node` handles recursion with parent tracking.

- [x] Task 6: Implement `map_lines_to_symbols`
  - File: `src/docvet/ast_utils.py`
  - Action: Add function `map_lines_to_symbols(tree: ast.Module) -> dict[int, Symbol]`. Call `get_documented_symbols` to get all symbols. Derive total line count from the module symbol's `end_line`. For each line `1..end_line` inclusive, find the innermost symbol whose definition range (`definition_start` through `end_line`) contains that line.
  - Notes: Uses `Symbol.definition_start` (already computed during `get_documented_symbols`) — no second AST walk needed. The module symbol spans the entire file and naturally serves as the outermost catch-all. Innermost = smallest `(end_line - definition_start)` range containing the line. Performance: sort symbols by range size, iterate lines once — O(lines * symbols) is acceptable for typical Python files (hundreds of lines, dozens of symbols). For empty modules, returns `{1: module_symbol}`.

- [x] Task 7: Create test fixture file
  - File: `tests/fixtures/nested_symbols.py`
  - Action: Create a Python fixture file covering all symbol extraction scenarios: module docstring, top-level function with docstring, top-level class with class docstring + `__init__` + regular method + `@property` + `@staticmethod` + `@classmethod` + nested class with method, standalone async function, decorated function with multi-line signature, function with no docstring.
  - Notes: Follow existing fixture pattern — `from __future__ import annotations` at top. Keep bodies minimal (`pass` or simple returns). This file serves as a comprehensive integration-style fixture.

- [x] Task 8: Write unit tests
  - File: `tests/unit/test_ast_utils.py`
  - Action: Create test file with 5 test classes (~27 tests total). Use inline source strings via `parse_source` fixture for most tests. For the comprehensive fixture test (AC 13), read `tests/fixtures/nested_symbols.py` with `Path.read_text()` and pass to `parse_source` — this keeps the test consistent with the factory pattern. No docstrings on test functions (suppressed by ruff per-file-ignores).
  - Notes: See Testing Strategy section for full test matrix. Follow `test_<what>_<condition>_<expected>` naming (matches existing test conventions). One assert per test recommended. Use `@pytest.mark.unit` marker. For AC 13, assert on concrete expected values: exact symbol count, specific `name`/`kind`/`parent` values for each symbol — not vague "correct metadata."

- [x] Task 9: Update `project-context.md` with AST utilities rules
  - File: `_bmad-output/project-context.md`
  - Action: Add a new "### AST Utilities Rules (`ast_utils.py`)" subsection under "Critical Implementation Rules". Document the patterns and conventions introduced by this module that future agents (enrichment, freshness) must follow.
  - Notes: Key rules to document:
    - `Symbol` dataclass is `frozen=True` with fields: `name`, `kind`, `line`, `end_line`, `definition_start`, `docstring`, `docstring_range`, `signature_range`, `body_range`, `parent`
    - `line` = `node.lineno` (keyword line, not decorator). `definition_start` = first decorator line or `node.lineno`
    - `signature_range` is `None` for classes and modules — only set for functions/methods
    - Module symbol uses `name="<module>"`, `line=1`, `definition_start=1`
    - `body_range` excludes docstring. `start >= end` means effectively empty body
    - `get_documented_symbols` returns flat list, not tree. `parent` = enclosing class name only
    - `map_lines_to_symbols` returns innermost symbol. Uses `definition_start` through `end_line`
    - Caller handles `SyntaxError` — `ast_utils` assumes valid AST
    - Never mock AST nodes — use source strings with `parse_source` or fixture files with `Path.read_text()` + `parse_source`
    - Update `rule_count` and `date` in frontmatter

- [x] Task 10: Update `product-vision.md` with implementation progress
  - File: `docs/product-vision.md`
  - Action: Add an "## Implementation Progress" section after "Package Architecture" showing current status of each module and check. Annotate what exists, what's in-progress, and what's planned.
  - Notes: Current state to document:
    - `cli.py` — implemented (all subcommands scaffolded as stubs)
    - `config.py` — implemented (`[tool.docvet]` reader with full validation)
    - `discovery.py` — implemented (all 4 modes: diff, staged, all, files)
    - `ast_utils.py` — in-progress (spec ready, implementation next)
    - `reporting.py` — not started
    - `checks/` directory — not started (no directory in `src/docvet/` yet)
    - `checks/enrichment.py` — not started (depends on `ast_utils.py`)
    - `checks/freshness.py` — not started (depends on `ast_utils.py`)
    - `checks/coverage.py` — not started
    - `checks/griffe_compat.py` — not started
    - CI workflow — implemented (lint, format, type-check, test, interrogate)
    - Keep the existing architecture diagram unchanged — it represents the target state

- [x] Task 11: Run quality gates
  - Action: Run `uv run ruff check .`, `uv run ruff format .`, `uv run ty check`, `uv run pytest --cov=docvet --cov-report=term-missing` to verify all gates pass.
  - Notes: Fix any issues before marking complete. Coverage must be >=85%.

### Acceptance Criteria

- [ ] AC 1: Given a Python source string with a function that has a docstring, when `get_documented_symbols` is called, then a `Symbol` with `kind="function"`, correct `name`, non-None `docstring`, and accurate `docstring_range` is returned.
- [ ] AC 2: Given a Python source with a class containing methods, when `get_documented_symbols` is called, then methods have `kind="method"` and `parent` set to the class name.
- [ ] AC 3: Given a Python source with nested classes and functions, when `get_documented_symbols` is called, then all symbols are extracted as a flat list with correct `parent` values (class name for methods, `None` for nested functions).
- [ ] AC 4: Given a function with no docstring, when `get_docstring_range` is called on its AST node, then `None` is returned.
- [ ] AC 5: Given a function with a multi-line docstring, when `get_docstring_range` is called, then the returned tuple accurately spans from the opening `"""` line to the closing `"""` line.
- [ ] AC 6: Given a function with a docstring, when `get_body_range` is called, then the returned range excludes the docstring lines.
- [ ] AC 7: Given a function with a multi-line signature, when `get_signature_range` is called, then the range spans from the `def` line to the line before the body starts, excluding decorators.
- [ ] AC 8: Given a single-line function `def f(): pass`, when `get_signature_range` is called, then `(lineno, lineno)` is returned.
- [ ] AC 9: Given a decorated function, when `get_signature_range` is called, then decorator lines are excluded from the range.
- [ ] AC 10: Given a source with nested functions, when `map_lines_to_symbols` is called with a line inside the inner function, then the inner function's `Symbol` is returned (innermost wins).
- [ ] AC 11: Given a decorated function, when `map_lines_to_symbols` is called with the decorator's line number, then the decorated function's `Symbol` is returned.
- [ ] AC 12: Given an empty Python source, when `get_documented_symbols` is called, then a single module `Symbol` is returned with `name="<module>"`, `kind="module"`, `line=1`, `definition_start=1`, `end_line=1`, `body_range=(1, 1)`, `signature_range=None`, `parent=None`.
- [ ] AC 13: Given the `tests/fixtures/nested_symbols.py` file read and parsed via `parse_source`, when `get_documented_symbols` is called, then the returned list contains the exact expected count of symbols, and each symbol has the correct `name`, `kind`, `parent`, and `line` values verified against concrete assertions (not vague "correct metadata").
- [ ] AC 15: Given a function with only a docstring and no other statements, when `get_body_range` is called, then the range is clamped to `(node.end_lineno, node.end_lineno)` (no inverted range).
- [ ] AC 16: Given `project-context.md`, when an agent reads it before implementing `checks/enrichment.py` or `checks/freshness.py`, then all `ast_utils.py` conventions (`Symbol` fields, `"<module>"` name, `definition_start` vs `line`, body_range clamping, caller SyntaxError responsibility) are documented and discoverable.
- [ ] AC 17: Given `product-vision.md`, when an agent reads it, then the implementation status of every module (`cli.py`, `config.py`, `discovery.py`, `ast_utils.py`, `reporting.py`, `checks/*.py`) is clearly indicated as implemented, in-progress, or not started.
- [ ] AC 18: All quality gates pass — `ruff check`, `ruff format --check`, `ty check`, `pytest` with >=85% coverage.

## Additional Context

### Dependencies

- **Upstream**: None — this is a foundation module
- **Downstream consumers**: `checks/enrichment.py`, `checks/freshness.py`

### Testing Strategy

- Source string fixtures via `parse_source` factory (no AST mocking)
- Parametrize across: nested classes, decorated functions, no docstring, generators, async functions, properties, staticmethods, classmethods, module-level symbols
- One assert per test, descriptive names: `test_<what>_<condition>_<expected>`
- Coverage target: >=85% (CI gate)
- New fixture file: `tests/fixtures/nested_symbols.py` for nesting depth coverage
- ~27 tests across 5 test classes:
  - `TestGetDocumentedSymbols` (~11 tests): simple function, no docstring, class with methods, nested class, nested function, parent field for method, nested function parent is None, nested class method parent is inner class, decorated (including @classmethod), async, module docstring, property, empty module, comprehensive fixture file
  - `TestGetDocstringRange` (~3 tests): single-line, multi-line, no docstring returns None
  - `TestGetBodyRange` (~4 tests): with docstring (body excludes docstring), without docstring, single-line function, function with only docstring (body-range clamped)
  - `TestGetSignatureRange` (~4 tests): single-line, multi-line, excludes decorators, single-line function `def f(): pass`
  - `TestMapLinesToSymbols` (~5 tests): top-level function, method vs class (returns method not class), nested function (returns inner), decorator line maps to function, module-level line

### Notes

- Issue: #7
- Branch convention: `feat/7-ast-helpers`
- **High-risk items**: `get_signature_range` edge cases with single-line functions and inline docstrings. `get_body_range` clamping for docstring-only bodies. Validate thoroughly.
- **Known limitation**: `Symbol.kind` does not distinguish `async def` from `def` — both are `"function"` (or `"method"`). If downstream checks need this distinction, add `is_async: bool` field later.
- **Known limitation**: `tree.end_lineno` may not cover trailing blank lines/comments after the last statement. Lines beyond `end_lineno` won't appear in `map_lines_to_symbols` output. This is acceptable since those lines contain no documentable code.
- **Caller responsibility**: `ast_utils.py` assumes valid AST from `ast.parse()`. Callers handle `SyntaxError` before invoking any function in this module.
- **Future consideration**: `Symbol` may eventually need a `decorators: list[str]` field for enrichment checks that care about `@property`, `@staticmethod`, etc. Out of scope for this spec.

## Review Notes

- Adversarial review completed
- Findings: 16 total, 12 fixed, 4 skipped (acceptable by design or codebase convention)
- Resolution approach: auto-fix
- Key fixes: `map_lines_to_symbols` performance (break on first match), `_HasBody` renamed to `_ScopeNode`, `Union` replaced with `|` syntax, Module `end_lineno` absence documented correctly, test coverage brought to 100% on `ast_utils.py`
