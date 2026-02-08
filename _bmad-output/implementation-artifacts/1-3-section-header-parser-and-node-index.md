# Story 1.3: Section Header Parser and Node Index

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want shared infrastructure for parsing docstring sections and indexing AST nodes,
so that all enrichment rules can efficiently determine which sections exist and look up AST nodes.

## Acceptance Criteria

1. **Given** a docstring containing `Raises:`, `Yields:`, and `Args:` section headers, **when** `_parse_sections(docstring)` is called, **then** it returns `{"Raises", "Yields", "Args"}` (AC: #1)

2. **Given** a docstring with varied indentation (e.g., module-level with no indent, method-level with 8-space indent), **when** `_parse_sections(docstring)` is called, **then** it correctly identifies section headers regardless of leading whitespace (AC: #2)

3. **Given** a docstring with no recognized section headers, **when** `_parse_sections(docstring)` is called, **then** it returns an empty set (never raises an exception) (AC: #3)

4. **Given** a malformed docstring with broken indentation or missing colons, **when** `_parse_sections(docstring)` is called, **then** it returns an empty set (graceful degradation, no crash) (AC: #4)

5. **Given** `_SECTION_HEADERS` constant, **when** inspected, **then** it contains all 10 recognized headers: `Args`, `Returns`, `Raises`, `Yields`, `Receives`, `Warns`, `Other Parameters`, `Attributes`, `Examples`, `See Also` (AC: #5)

6. **Given** an `ast.Module` tree with functions, classes, and async functions, **when** `_build_node_index(tree)` is called, **then** it returns a `dict[int, ast.AST]` mapping line numbers to `FunctionDef | AsyncFunctionDef | ClassDef` nodes (AC: #6)

7. **Given** a module-level symbol (line 1) with no corresponding AST node, **when** `node_index.get(symbol.line)` is called, **then** it returns `None` (safe for rules to handle) (AC: #7)

## Tasks / Subtasks

- [x] Task 1: Create `_SECTION_HEADERS` constant and `_SECTION_PATTERN` compiled regex (AC: #5)
  - [x] 1.1: Define `_SECTION_HEADERS` frozenset with all 10 section names
  - [x] 1.2: Create `_SECTION_PATTERN` regex with multiline flag for lenient matching
  - [x] 1.3: Document why Args and Returns are included (parsing context only, not checked for absence)

- [x] Task 2: Implement `_parse_sections` function (AC: #1, #2, #3, #4)
  - [x] 2.1: Write function with signature `_parse_sections(docstring: str) -> set[str]`
  - [x] 2.2: Use `_SECTION_PATTERN.findall()` to extract matching headers
  - [x] 2.3: Return set of matched header names (empty set if no matches)
  - [x] 2.4: Add comprehensive docstring explaining graceful degradation on malformed input

- [x] Task 3: Implement `_build_node_index` function (AC: #6, #7)
  - [x] 3.1: Write function with signature `_build_node_index(tree: ast.Module) -> dict[int, ast.AST]`
  - [x] 3.2: Use `ast.walk(tree)` to collect FunctionDef, AsyncFunctionDef, and ClassDef nodes
  - [x] 3.3: Index nodes by their `lineno` attribute
  - [x] 3.4: Add comprehensive docstring explaining O(1) lookup benefit and None-handling for module symbols

- [x] Task 4: Write comprehensive unit tests (AC: #1-#7)
  - [x] 4.1: `test_parse_sections_when_headers_present_returns_matching_set` — AC #1
  - [x] 4.2: `test_parse_sections_when_varied_indentation_returns_headers` — AC #2
  - [x] 4.3: `test_parse_sections_when_no_headers_returns_empty_set` — AC #3
  - [x] 4.4: `test_parse_sections_when_malformed_missing_colon_returns_empty_set` — AC #4
  - [x] 4.5: `test_section_headers_contains_all_ten_headers` — AC #5
  - [x] 4.6: `test_build_node_index_when_functions_and_classes_maps_lines` — AC #6
  - [x] 4.7: `test_build_node_index_get_returns_none_for_missing_line` — AC #7
  - [x] 4.8: Edge case tests: `test_section_headers_is_frozenset`, `test_parse_sections_when_empty_string_returns_empty_set`, `test_parse_sections_when_all_headers_present_returns_all`, `test_parse_sections_when_header_has_trailing_whitespace_returns_header`, `test_build_node_index_when_async_function_includes_async_node`, `test_build_node_index_when_nested_functions_includes_inner`, `test_build_node_index_when_module_only_returns_empty_dict`

- [x] Task 5: Run quality gates and verify all pass
  - [x] 5.1: `uv run ruff check .` — All checks passed
  - [x] 5.2: `uv run ruff format --check .` — All files formatted
  - [x] 5.3: `uv run ty check` — All type checks passed
  - [x] 5.4: `uv run pytest tests/unit/checks/ -v` — 25 tests pass (14 enrichment + 11 finding)

## Dev Notes

### Scope

This story creates the **shared infrastructure layer** that all 10 enrichment rules depend on. Two private functions in `checks/enrichment.py`:

1. **`_parse_sections(docstring: str) -> set[str]`** — Identifies which Google-style section headers are present in a docstring
2. **`_build_node_index(tree: ast.Module) -> dict[int, ast.AST]`** — Creates a line-number-to-AST-node lookup table

These are **load-bearing** architectural components. Every rule calls `_parse_sections` once per symbol. Medium-tier rules (missing-raises, missing-yields, missing-receives, missing-warns) use `node_index` for O(1) body inspection.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | NEW — Create module with `_SECTION_HEADERS`, `_SECTION_PATTERN`, `_parse_sections()`, `_build_node_index()` |
| `tests/unit/checks/test_enrichment.py` | NEW — Unit tests for section parsing and node indexing |

### Architecture Constraints

**Section Header Parsing:**
- **Lenient regex matching** — `^\s*` allows variable leading whitespace (module-level has 0 indent, method-level has 8+ spaces)
- **Fail-safe design** — `re.findall()` returns empty list if no matches → empty set (never crashes)
- **False negatives preferred** — Better to miss a malformed header than produce a false positive (NFR5)
- **Single compiled regex** — One `_SECTION_PATTERN` at module level, called via `.findall()` per symbol

**10 Recognized Headers:**
1. `Args` (context only — not checked for absence)
2. `Returns` (context only — not checked for absence)
3. `Raises` (checked by `missing-raises` rule)
4. `Yields` (checked by `missing-yields` rule)
5. `Receives` (checked by `missing-receives` rule)
6. `Warns` (checked by `missing-warns` rule)
7. `Other Parameters` (checked by `missing-other-parameters` rule)
8. `Attributes` (checked by `missing-attributes` rule)
9. `Examples` (checked by `missing-examples` rule)
10. `See Also` (checked by `missing-cross-references` rule)

**Why Args and Returns are included:**
- FR15: "The system can recognize `Args:` and `Returns:` section headers for docstring parsing context without checking for their absence"
- Layers 1-2 (presence and style) are ruff D-rules and interrogate's domain
- `_parse_sections` needs complete context — returning `{"Args", "Returns", "Raises"}` is more useful than `{"Raises"}` alone
- Future rules might need to know if Args/Returns exist (e.g., format checking)

**Node Index Design:**
- **One pass over tree** — `ast.walk(tree)` collects all `FunctionDef | AsyncFunctionDef | ClassDef` nodes once
- **Line-based indexing** — `node_index[node.lineno] = node` (line numbers are unique per node)
- **O(1) lookup** — Rules call `node_index.get(symbol.line)` instead of walking the tree again
- **None-safe** — `.get()` returns `None` for module symbols (line 1, no corresponding node)
- **Replaces tree parameter** — Later stories will use `node_index` instead of raw `tree` in `_check_*` signatures

### Implementation Details

**`_SECTION_HEADERS` Constant:**
```python
_SECTION_HEADERS = frozenset({
    "Args", "Returns", "Raises", "Yields", "Receives",
    "Warns", "Other Parameters", "Attributes", "Examples", "See Also",
})
```
- `frozenset` for immutability and O(1) membership testing
- Alphabetical order within semantic groups (args/returns, error handling, attributes, docs)
- All exact string matches (case-sensitive) per Google-style conventions

**`_SECTION_PATTERN` Regex:**
```python
_SECTION_PATTERN = re.compile(
    r"^\s*(Args|Returns|Raises|Yields|Receives|Warns|Other Parameters|Attributes|Examples|See Also):\s*$",
    re.MULTILINE,
)
```
- `^\s*` — Matches start of line with optional leading whitespace (handles varied indentation)
- Capturing group with all 10 header names separated by `|` (alternation)
- `:\s*$` — Requires colon followed by optional trailing whitespace and end of line
- `re.MULTILINE` — Makes `^` and `$` match start/end of each line (not just string start/end)
- **Edge case:** Fenced code blocks with headers inside (e.g., example code) will match → false negatives are safe

**`_parse_sections` Function:**
```python
def _parse_sections(docstring: str) -> set[str]:
    """Extract recognized Google-style section headers from a docstring.

    Identifies which of the 10 recognized section headers (Args, Returns,
    Raises, Yields, Receives, Warns, Other Parameters, Attributes, Examples,
    See Also) are present in the docstring. Handles varied indentation
    gracefully (module-level with no indent, method-level with 8+ spaces).

    Args:
        docstring: The raw docstring text to parse.

    Returns:
        A set of header names found in the docstring. Returns empty set if no
        headers match or if docstring is malformed. Never raises an exception.

    Examples:
        >>> _parse_sections("Summary.\\n\\n    Args:\\n        x: Param.\\n")
        {'Args'}
        >>> _parse_sections("No headers here.")
        set()
    """
    return set(_SECTION_PATTERN.findall(docstring))
```
- **Graceful degradation** — `re.findall()` returns `[]` if no matches → `set()` (empty set)
- **No exception paths** — Regex on string input never crashes
- **Single responsibility** — Only parses headers, doesn't validate content or structure

**`_build_node_index` Function:**
```python
def _build_node_index(tree: ast.Module) -> dict[int, ast.AST]:
    """Build a line-number-to-AST-node lookup table for O(1) access.

    Walks the AST tree once and collects all FunctionDef, AsyncFunctionDef,
    and ClassDef nodes, indexed by their line number. This enables rules to
    retrieve the AST node for a symbol via symbol.line without re-walking the
    tree for each rule.

    Args:
        tree: The parsed AST tree for the source file.

    Returns:
        A dict mapping line numbers to AST nodes. Module-level symbols (line 1)
        have no corresponding node, so node_index.get(1) returns None.

    Examples:
        >>> source = "def foo():\\n    pass\\n"
        >>> tree = ast.parse(source)
        >>> index = _build_node_index(tree)
        >>> isinstance(index[1], ast.FunctionDef)
        True
    """
    index: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            index[node.lineno] = node
    return index
```
- **ast.walk efficiency** — Single pass over entire tree (no repeated traversal)
- **Type filtering** — Only collects node types that enrichment rules inspect
- **Nested functions** — Each gets its own line number, so no collision risk
- **Safe lookup** — Rules use `.get()` which returns `None` for missing keys

### What NOT to Do

**Section Parsing:**
- Do NOT write a custom docstring parser — use regex on raw text
- Do NOT try to validate section content (e.g., checking if Raises lists actual exceptions) — only detect presence
- Do NOT handle non-Google-style docstrings (reStructuredText, NumPy) — out of scope
- Do NOT raise exceptions on malformed input — return empty set instead

**Node Indexing:**
- Do NOT index other node types (ast.Assign, ast.Expr) — only Function/Class definitions
- Do NOT attempt to validate or transform nodes — pure index construction
- Do NOT walk the tree multiple times — single `ast.walk()` pass only
- Do NOT use node names as keys — line numbers are the canonical identifier

### Testing Strategy

**Section Parsing Tests:**
1. **Happy path** — Well-formed docstring with 3-4 headers returns correct set
2. **Varied indentation** — Module-level (0 indent) and method-level (8 spaces) both work
3. **Empty set** — Docstring with no headers returns `set()` (not None, not exception)
4. **Malformed input** — Missing colons, extra spaces, broken indentation → `set()` (graceful)
5. **All 10 headers** — Constant inspection confirms completeness

**Node Index Tests:**
1. **Happy path** — Module with functions and classes builds correct line→node mapping
2. **Async functions** — `async def` nodes included in index
3. **Nested functions** — Inner functions get their own index entries
4. **Module symbol** — Line 1 with no node returns `None` via `.get()`
5. **Empty module** — `ast.Module` with no nodes returns empty dict (not crash)

**Test file organization:**
- Group by function: `# Section parsing tests`, `# Node index tests`
- Use project fixture pattern: `parse_source(source_code)` from `conftest.py`
- Test naming: `test_{function_name}_when_{condition}_returns_{expected}`

### FRs Covered

- FR15: Recognize Args/Returns headers for parsing context (included in `_SECTION_HEADERS`)
- FR31: Recognize 8 Google-style section headers for missing section detection
- FR35: Extract and parse raw docstring text from symbols to identify which sections are present
- FR36: Analyze any symbol with non-empty docstring
- FR38: Handle malformed docstrings gracefully without raising exceptions
- NFR7: Malformed docstrings result in zero findings (via empty set return, not crash)

### Project Structure Notes

**New file:** `src/docvet/checks/enrichment.py`
- Module docstring explaining enrichment check purpose
- `from __future__ import annotations` (first line after docstring)
- Imports: `ast`, `re` (stdlib), `from docvet.checks import Finding` (local)
- Module-level constants: `_SECTION_HEADERS`, `_SECTION_PATTERN`
- Two private functions: `_parse_sections`, `_build_node_index`
- No public functions yet — later stories add `check_enrichment` orchestrator

**New file:** `tests/unit/checks/test_enrichment.py`
- Organized by function under test
- Uses `parse_source` fixture from `tests/conftest.py`
- Follows project naming convention: `test_{what}_{condition}_{expected}`

### Previous Story Intelligence

**From Story 1.1 (Config Toggle):**
- ✅ `EnrichmentConfig` has `require_attributes: bool = True` field
- ✅ `_VALID_ENRICHMENT_KEYS` includes `"require-attributes"`
- ✅ All 10 boolean toggles + 1 list config (`require_examples`) are defined
- ✅ Backward-compatible defaults work (existing configs don't break)

**Key Lesson:** Config additions are straightforward when using frozen dataclasses with defaults. No parser changes needed — existing validation handles new keys automatically after adding to `_VALID_ENRICHMENT_KEYS`.

**From Story 1.2 (Finding Dataclass):**
- ✅ `Finding` frozen dataclass exists in `checks/__init__.py`
- ✅ All 6 fields defined: `file`, `line`, `symbol`, `rule`, `message`, `category`
- ✅ `__post_init__` validation rejects empty strings and line < 1
- ✅ Private imports (`_dataclass`, `_Literal`) prevent import leakage
- ✅ 11 unit tests cover construction, immutability, validation, edge cases

**Key Lessons:**
1. Input validation via `__post_init__` is the right pattern for frozen dataclasses
2. Private imports (`_name`) prevent polluting module's public API
3. Import `Finding` as `from docvet.checks import Finding` (not `from docvet.checks.__init__`)
4. Test frozen behavior explicitly with `FrozenInstanceError` (not generic `AttributeError`)

**File Patterns Established:**
- Every file starts with `from __future__ import annotations`
- Private module-level items use `_prefix` naming
- Comprehensive docstrings with Args/Returns/Examples sections
- Test files mirror source file structure (`checks/enrichment.py` → `checks/test_enrichment.py`)

### Git Intelligence

**Recent Commits Pattern (from Story 1.1 and 1.2):**
- **Commit message format:** `feat(scope): imperative description`
  - Story 1.1: `feat(enrichment): add require_attributes config toggle`
  - Story 1.2: `feat(dataclass): create shared immutable Finding dataclass for consistent check module findings`
- **Scope choices:** `enrichment` for enrichment module changes, `dataclass` for Finding
- **PR numbers:** Sequential (#25, #26) — Story 1.3 likely #27
- **Conventional commit type:** `feat` for new functionality
- **Branch naming:** Not visible in `git log` output, but likely `feat/enrichment-*` pattern

**Code Patterns from PRs:**
- Small, focused PRs (2 files modified in #25, 3 files created in #26)
- Config changes land first (prerequisite PR #25 before #26)
- Comprehensive test coverage (190 tests → 201 tests, +11 in #26)
- Quality gates pass before merge (ruff, ty, pytest all green)
- Module docstrings explain purpose and context
- Private helpers use `_name` prefix consistently

**Suggested Commit Message for Story 1.3:**
```
feat(enrichment): add section header parser and AST node index (#27)

Create shared infrastructure for enrichment rules: _parse_sections()
identifies Google-style section headers in docstrings, and
_build_node_index() creates O(1) line-to-AST-node lookup table.

- Add _SECTION_HEADERS frozenset with 10 recognized headers
- Add _SECTION_PATTERN compiled regex with lenient matching
- Implement _parse_sections() with graceful degradation on malformed input
- Implement _build_node_index() with ast.walk() single-pass collection
- Add 8+ unit tests covering happy path, edge cases, and None-handling

Test: uv run pytest tests/unit/checks/test_enrichment.py -v
```

### Latest Technical Context

**Python 3.12+ stdlib APIs used:**
- `ast.parse(source)` — Parses Python source to AST (no changes from 3.10)
- `ast.walk(tree)` — Depth-first tree traversal generator (stable since 2.6)
- `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef` — Node types to index
- `re.compile(pattern, flags)` — Compiled regex for performance
- `re.findall(string)` — Returns all non-overlapping matches as list
- `frozenset({...})` — Immutable set for constant data

**No breaking changes in Python 3.12/3.13** — All AST APIs used are stable.

**Regex Pattern Explanation:**
- `r"^\s*"` — Start of line, optional leading whitespace (raw string for readability)
- Capturing group `(Header1|Header2|...)` — Alternation matches any header
- `:\s*$` — Colon, optional trailing whitespace, end of line
- `re.MULTILINE` — Treats each line as start/end (not just full string)

**AST Node Attributes Used:**
- `node.lineno` — Line number where node starts (1-indexed)
- `isinstance(node, tuple_of_types)` — Type checking for AST nodes

### Architecture Context

**This story creates the foundation for all 10 enrichment rules:**

```
check_enrichment(source, tree, config, file_path)
  │
  ├─ get_documented_symbols(source, tree) → symbols: list[Symbol]
  ├─ _build_node_index(tree) → node_index: dict[int, ast.AST]  ← THIS STORY
  │
  ▼
  for each symbol:
  │
  ├─ if not symbol.docstring: continue
  ├─ _parse_sections(symbol.docstring) → sections: set[str]  ← THIS STORY
  │
  ├─ _check_missing_raises(symbol, sections, node_index, ...)
  ├─ _check_missing_yields(symbol, sections, node_index, ...)
  └─ ... (8 more rules)
```

**Dependency Chain:**
1. ✅ Story 1.1: `EnrichmentConfig` with all toggles
2. ✅ Story 1.2: `Finding` dataclass
3. **Story 1.3: Section parser + node index** ← YOU ARE HERE
4. Story 1.4: First rule (`missing-raises`) + orchestrator that calls helpers from 1.3
5. Stories 1.5-1.7: Remaining 9 rules (all use helpers from 1.3)

**Why this story is critical:**
- Every `_check_*` function depends on `sections: set[str]` parameter
- 4 medium-tier rules need `node_index: dict[int, ast.AST]` for body inspection
- Centralized parsing prevents inconsistencies between rules (NFR5, NFR6)
- Single-pass indexing satisfies NFR1-4 (performance requirements)

### Library/Framework Requirements

**No new dependencies** — This story uses only Python stdlib:
- `ast` — Already used by `ast_utils.py`
- `re` — Standard library regex module
- `frozenset`, `dict`, `set` — Built-in types

**Versions:**
- Python 3.12+ (project requirement)
- No third-party libraries needed

**Why no libraries:**
- Google-style docstrings are simple text patterns (regex sufficient)
- AST traversal is `ast.walk()` one-liner (no visitor pattern needed)
- NFR16: "No new runtime dependencies (stdlib `ast`, `re`, and existing `ast_utils` only)"

### File Structure Requirements

**`src/docvet/checks/enrichment.py` structure:**
```python
"""Enrichment check for docstring completeness.

Detects missing docstring sections (Raises, Yields, Attributes, etc.) by
combining AST analysis with section header parsing. Implements Layer 3 of
the docstring quality model.
"""

from __future__ import annotations

import ast
import re

from docvet.checks import Finding
from docvet.config import EnrichmentConfig

# Module-level constants
_SECTION_HEADERS = frozenset({...})
_SECTION_PATTERN = re.compile(r"...", re.MULTILINE)


def _parse_sections(docstring: str) -> set[str]:
    """Extract recognized Google-style section headers."""
    ...


def _build_node_index(tree: ast.Module) -> dict[int, ast.AST]:
    """Build line-number-to-AST-node lookup table."""
    ...
```

**`tests/unit/checks/test_enrichment.py` structure:**
```python
"""Tests for enrichment check infrastructure and rules."""

from __future__ import annotations

import ast
import pytest

from docvet.checks.enrichment import (
    _SECTION_HEADERS,
    _build_node_index,
    _parse_sections,
)


# Section parsing tests
def test_parse_sections_returns_matching_headers():
    ...


# Node index tests
def test_build_node_index_maps_line_numbers_to_nodes():
    ...
```

**Note:** Private functions (`_parse_sections`, `_build_node_index`) can be imported in tests because they're in the same package. This is the **only** context where importing private functions is acceptable.

### Testing Standards Summary

**From project-context.md Testing Rules:**
- Test naming: `test_{unit_under_test}_{condition}_{expected_behavior}`
- Self-contained tests (no shared state between tests)
- Use `parse_source` fixture for AST creation (never hand-roll AST nodes)
- Parametrize tests with `@pytest.mark.parametrize` for multiple inputs
- Group related tests with class containers: `class TestParseSections:` (optional)

**Coverage expectations:**
- Project-wide: >=85% (CI gate)
- `enrichment.py` target: >=90% (aspirational, NFR12)
- This story: High coverage easy (2 pure functions, no branches)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 3] — Section header regex strategy (lenient matching, single compiled regex)
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — AST node-to-Symbol mapping (line-based index, O(1) lookup)
- [Source: _bmad-output/planning-artifacts/architecture.md#Shared Infrastructure] — Section header parsing as load-bearing component
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns] — `_build_*` for construction, `_parse_*` for text parsing
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3] — BDD acceptance criteria
- [Source: _bmad-output/project-context.md#Python Language Rules] — Every file starts with `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Testing Rules] — Test naming convention and fixture usage
- [Source: src/docvet/checks/__init__.py:19-66] — Finding dataclass (imported by enrichment.py)
- [Source: src/docvet/config.py:24-39] — EnrichmentConfig structure

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

- Minor ruff I001 import ordering issue in test file — fixed via `ruff check --fix` (removed blank line between stdlib and local imports)

### Completion Notes List

- ✅ Created `src/docvet/checks/enrichment.py` with shared enrichment infrastructure
  - `_SECTION_HEADERS` frozenset with all 10 recognized Google-style headers
  - `_SECTION_PATTERN` compiled regex with `re.MULTILINE` for lenient matching
  - `_parse_sections(docstring) -> set[str]` with graceful degradation on malformed input
  - `_build_node_index(tree) -> dict[int, ast.AST]` with single-pass `ast.walk()` collection
  - Module docstring explains enrichment check purpose and Layer 3 role
  - Comments explain FR15 inclusion of Args/Returns for parsing context
- ✅ Created 14 unit tests in `tests/unit/checks/test_enrichment.py`
  - 2 constant tests: `_SECTION_HEADERS` completeness and frozenset type
  - 6 section parsing tests: happy path, varied indentation, no headers, malformed, empty string, all headers, trailing whitespace
  - 5 node index tests: functions+classes, async functions, nested functions, module-only, None for missing lines
  - All tests use `parse_source` fixture where applicable (project convention)
  - Test naming follows `test_{what}_{condition}_{expected}` convention
- ✅ All 7 acceptance criteria verified with passing tests
  - AC#1: `_parse_sections` returns matching headers ✓
  - AC#2: Varied indentation handled correctly ✓
  - AC#3: Empty set for no headers (no exception) ✓
  - AC#4: Graceful degradation on malformed docstrings ✓
  - AC#5: `_SECTION_HEADERS` contains all 10 headers ✓
  - AC#6: `_build_node_index` maps line numbers to nodes ✓
  - AC#7: `.get()` returns None for module-level symbols ✓
- ✅ All quality gates pass: ruff check, ruff format, ty check, 216 tests (0 regressions)

### Change Log

- 2026-02-08: Implemented Story 1.3 — Created section header parser and AST node index as shared enrichment infrastructure with 14 unit tests

### File List

- `src/docvet/checks/enrichment.py` (NEW) — `_SECTION_HEADERS`, `_SECTION_PATTERN`, `_parse_sections()`, `_build_node_index()`
- `tests/unit/checks/test_enrichment.py` (NEW) — 14 unit tests covering all 7 acceptance criteria
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED) — Story status: ready-for-dev → in-progress → review

