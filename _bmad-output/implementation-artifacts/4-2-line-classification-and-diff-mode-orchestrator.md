# Story 4.2: Line Classification and Diff Mode Orchestrator

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to classify changed lines per symbol by range (signature, body, docstring) and produce findings at the appropriate severity level,
so that stale docstrings are detected with correct severity and docstring updates suppress findings.

## Acceptance Criteria

1. **Given** a symbol with changed lines in its `signature_range` and no changed lines in its `docstring_range`, **When** `_classify_changed_lines(changed_lines, symbol)` is called, **Then** it returns `"signature"` (FR47 — HIGH severity)
2. **Given** a symbol with changed lines in its `body_range` but not in `signature_range`, and no changed lines in its `docstring_range`, **When** `_classify_changed_lines(changed_lines, symbol)` is called, **Then** it returns `"body"` (FR48 — MEDIUM severity)
3. **Given** a symbol with changed lines only outside its `signature_range`, `docstring_range`, and `body_range`, **When** `_classify_changed_lines(changed_lines, symbol)` is called, **Then** it returns `"import"` (FR49 — LOW severity)
4. **Given** a symbol with changed lines in both `signature_range` and `docstring_range`, **When** `_classify_changed_lines(changed_lines, symbol)` is called, **Then** it returns `None` (docstring updated, finding suppressed — FR46, FR62)
5. **Given** a symbol with changed lines in both `body_range` and `docstring_range`, **When** `_classify_changed_lines(changed_lines, symbol)` is called, **Then** it returns `None` (docstring updated alongside body change)
6. **Given** a class or module symbol with `signature_range is None`, **When** `_classify_changed_lines(changed_lines, symbol)` is called with body changes, **Then** it returns `"body"` (MEDIUM), never `"signature"` (NFR23)
7. **Given** a file with a function whose signature changed and docstring was not updated, **When** `check_freshness_diff(file_path, diff_output, tree)` is called, **Then** it returns a `Finding` with `rule="stale-signature"`, `category="required"`
8. **Given** a file with a method whose body changed and docstring was not updated, **When** `check_freshness_diff(file_path, diff_output, tree)` is called, **Then** it returns a `Finding` with `rule="stale-body"`, `category="recommended"`
9. **Given** a file where only import lines near a symbol changed, **When** `check_freshness_diff(file_path, diff_output, tree)` is called, **Then** it returns a `Finding` with `rule="stale-import"`, `category="recommended"`
10. **Given** a file where a symbol has both signature and body changes (no docstring change), **When** `check_freshness_diff` is called, **Then** it produces exactly one finding at the highest severity (`stale-signature`, not both — FR61)
11. **Given** a symbol with no docstring (`docstring_range is None`), **When** `check_freshness_diff` is called, **Then** it returns zero findings for that symbol (FR54)
12. **Given** a function that was deleted (lines in diff's `-` side but not in current AST), **When** `check_freshness_diff` is called, **Then** it produces zero findings for that deleted function (FR56)
13. **Given** a function relocated within a file, **When** `check_freshness_diff` is called, **Then** it treats the new location as a body change if the docstring wasn't updated (FR57)
14. **Given** a file where all changed symbols have correspondingly updated docstrings, **When** `check_freshness_diff` is called, **Then** it returns an empty list (FR62)
15. **Given** an empty `diff_output` string, **When** `check_freshness_diff` is called, **Then** it returns an empty list immediately (FR66)
16. **Given** identical `diff_output` and identical `tree`, **When** `check_freshness_diff` is called multiple times, **Then** it produces identical output every time (NFR24)

## Tasks / Subtasks

- [ ] Task 1: Add `ast` import to `freshness.py` (AC: all orchestrator tasks)
  - [ ] 1.1: Add `import ast` to stdlib imports section — was removed in Story 4.1 since not needed until now
  - [ ] 1.2: Remove `noqa: F401` from `map_lines_to_symbols` import (now used)
  - [ ] 1.3: Keep `FreshnessConfig` `noqa: F401` (still not used until Epic 5)
- [ ] Task 2: Implement `_classify_changed_lines` (AC: 1-6)
  - [ ] 2.1: Signature: `def _classify_changed_lines(changed_lines: set[int], symbol: Symbol) -> str | None:`
  - [ ] 2.2: Compute set intersection of `changed_lines` with `symbol.docstring_range` — if any overlap, return `None` (docstring updated, suppress finding)
  - [ ] 2.3: Compute set intersection with `symbol.signature_range` — if `signature_range is not None` and any overlap, return `"signature"`
  - [ ] 2.4: Compute set intersection with `symbol.body_range` — if any overlap, return `"body"`
  - [ ] 2.5: Otherwise return `"import"` (changed lines within symbol's total range but outside all named ranges)
  - [ ] 2.6: Handle `signature_range is None` (classes/modules) — skip signature check entirely, body changes produce `"body"` not `"signature"`
- [ ] Task 3: Implement `check_freshness_diff` orchestrator (AC: 7-16)
  - [ ] 3.1: Signature: `def check_freshness_diff(file_path: str, diff_output: str, tree: ast.Module) -> list[Finding]:`
  - [ ] 3.2: Early return `[]` if `diff_output` is empty or `_parse_diff_hunks` returns empty set
  - [ ] 3.3: Call `map_lines_to_symbols(tree)` to get `line_map: dict[int, Symbol]`
  - [ ] 3.4: Invert line_map: for each line in `changed_lines`, look up `line_map.get(line)`, accumulate into `symbol_changes: dict[Symbol, set[int]]` (using `defaultdict(set)`)
  - [ ] 3.5: Iterate `symbol_changes` — skip symbols with `symbol.docstring_range is None` (FR54)
  - [ ] 3.6: Call `_classify_changed_lines(its_changed_lines, symbol)` — if returns `None`, skip (docstring updated)
  - [ ] 3.7: Map classification to rule/category: `"signature"` → `("stale-signature", "required")`, `"body"` → `("stale-body", "recommended")`, `"import"` → `("stale-import", "recommended")`
  - [ ] 3.8: Build message using `symbol.kind.capitalize()`: `"{Kind} '{name}' {change_type} changed but docstring not updated"`
  - [ ] 3.9: Call `_build_finding(file_path, symbol, rule, message, category)` and append to findings
  - [ ] 3.10: Return `findings` list
- [ ] Task 4: Add unit tests for `_classify_changed_lines` (AC: 1-6)
  - [ ] 4.1: Test signature change detected (AC 1)
  - [ ] 4.2: Test body change detected (AC 2)
  - [ ] 4.3: Test import/formatting change detected (AC 3)
  - [ ] 4.4: Test docstring + signature change suppresses finding (AC 4)
  - [ ] 4.5: Test docstring + body change suppresses finding (AC 5)
  - [ ] 4.6: Test class symbol (signature_range=None) body change returns `"body"` not `"signature"` (AC 6)
  - [ ] 4.7: Test module symbol (signature_range=None) body change returns `"body"` (AC 6)
  - [ ] 4.8: Test docstring-only change returns `None`
  - [ ] 4.9: Test signature + body change (no docstring) returns `"signature"` (highest severity wins)
- [ ] Task 5: Add unit tests for `check_freshness_diff` (AC: 7-16)
  - [ ] 5.1: Test stale-signature finding produced (AC 7)
  - [ ] 5.2: Test stale-body finding produced (AC 8)
  - [ ] 5.3: Test stale-import finding produced (AC 9)
  - [ ] 5.4: Test highest severity wins — signature + body → one `stale-signature` finding (AC 10)
  - [ ] 5.5: Test no-docstring symbol skipped (AC 11)
  - [ ] 5.6: Test deleted function produces zero findings (AC 12)
  - [ ] 5.7: Test docstring updated alongside code change → zero findings (AC 14)
  - [ ] 5.8: Test empty diff_output returns empty list (AC 15)
  - [ ] 5.9: Test deterministic output (AC 16)
  - [ ] 5.10: Test finding message format: `"{Kind} '{name}' {change_type} changed but docstring not updated"`
  - [ ] 5.11: Test finding uses `symbol.line` for `Finding.line` (not a changed line number)
  - [ ] 5.12: Run full test suite — zero regressions on existing tests (435 total)

## Dev Notes

### This is Story 4.2 — Core of Epic 4 (Freshness Diff Mode)

This story extends `src/docvet/checks/freshness.py` (created in Story 4.1) and `tests/unit/checks/test_freshness.py`. No new files created. No existing source files other than `freshness.py` are modified.

### Current State of `freshness.py` (After Story 4.1)

```
freshness.py (97 lines):
1-11:  Module docstring, imports (re, Literal, Symbol, map_lines_to_symbols, Finding, FreshnessConfig)
12-22: _HUNK_PATTERN constant, rule ID comments
23-55: _build_finding shared helper
56-96: _parse_diff_hunks diff parser
```

**Imports to update:**
- ADD `import ast` (needed for `check_freshness_diff` signature type annotation and `map_lines_to_symbols`)
- REMOVE `noqa: F401` from `map_lines_to_symbols` (now used in orchestrator)
- KEEP `noqa: F401` on `FreshnessConfig` (not used until Epic 5)

### `_classify_changed_lines` Implementation (Architecture Decision 4)

**Signature:**
```python
def _classify_changed_lines(
    changed_lines: set[int],
    symbol: Symbol,
) -> str | None:
```

**Priority-ordered early returns:**
```python
def _classify_changed_lines(changed_lines: set[int], symbol: Symbol) -> str | None:
    # 1. Docstring updated → suppress finding
    if symbol.docstring_range is not None:
        doc_lines = set(range(symbol.docstring_range[0], symbol.docstring_range[1] + 1))
        if changed_lines & doc_lines:
            return None

    # 2. Signature changed → HIGH
    if symbol.signature_range is not None:
        sig_lines = set(range(symbol.signature_range[0], symbol.signature_range[1] + 1))
        if changed_lines & sig_lines:
            return "signature"

    # 3. Body changed → MEDIUM
    body_lines = set(range(symbol.body_range[0], symbol.body_range[1] + 1))
    if changed_lines & body_lines:
        return "body"

    # 4. Else → LOW (import/formatting)
    return "import"
```

**Critical design points:**
- Docstring check FIRST — if developer updated the docstring, suppress the finding entirely regardless of what else changed
- `signature_range is None` for classes and modules — step 2 is skipped, body changes correctly produce `"body"` not `"signature"` (NFR23)
- Ranges are **inclusive** on both ends — use `range(start, end + 1)` to create the set (matches `Symbol` range convention from `ast_utils.py`)
- Use `&` (set intersection) for readability
- `"import"` is the fallback — changed lines within the symbol's total range but outside signature, docstring, and body ranges (e.g., decorator lines, blank lines between signature and body)

### `check_freshness_diff` Orchestrator Implementation

**Signature:**
```python
def check_freshness_diff(
    file_path: str,
    diff_output: str,
    tree: ast.Module,
) -> list[Finding]:
```

**Implementation pattern:**
```python
def check_freshness_diff(file_path: str, diff_output: str, tree: ast.Module) -> list[Finding]:
    changed_lines = _parse_diff_hunks(diff_output)
    if not changed_lines:
        return []

    line_map = map_lines_to_symbols(tree)
    # Invert: group changed lines by symbol
    symbol_changes: dict[Symbol, set[int]] = {}
    for line_num in changed_lines:
        sym = line_map.get(line_num)
        if sym is not None:
            if sym not in symbol_changes:
                symbol_changes[sym] = set()
            symbol_changes[sym].add(line_num)

    findings: list[Finding] = []
    for symbol, its_changed_lines in symbol_changes.items():
        if symbol.docstring_range is None:
            continue  # FR54: skip undocumented symbols

        classification = _classify_changed_lines(its_changed_lines, symbol)
        if classification is None:
            continue  # Docstring was updated

        rule, category = _CLASSIFICATION_MAP[classification]
        kind = symbol.kind.capitalize()
        message = f"{kind} '{symbol.name}' {classification} changed but docstring not updated"
        findings.append(_build_finding(file_path, symbol, rule, message, category))

    return findings
```

**Add a classification-to-rule mapping constant:**
```python
_CLASSIFICATION_MAP: dict[str, tuple[str, Literal["required", "recommended"]]] = {
    "signature": ("stale-signature", "required"),
    "body": ("stale-body", "recommended"),
    "import": ("stale-import", "recommended"),
}
```

### File Placement Within `freshness.py`

Follow the architecture's mode-oriented file organization:
```
1. Module docstring                            (existing)
2. from __future__ import annotations          (existing)
3. Stdlib imports (ast, re)                    (add ast)
4. Local imports                               (existing, remove noqa from map_lines_to_symbols)
5. Module-level constants (_HUNK_PATTERN)      (existing)
   ADD: _CLASSIFICATION_MAP                    ← NEW
6. Shared helpers (_build_finding)             (existing)
7. Diff mode helpers (_parse_diff_hunks)       (existing)
   ADD: _classify_changed_lines                ← NEW (after _parse_diff_hunks, before orchestrator)
8. check_freshness_diff public function        ← NEW (last in diff block)
```

### Range Intersection Pattern — CRITICAL

`Symbol` ranges are `tuple[int, int]` representing `(start_line, end_line)` **inclusive on both ends**. To convert to a set for intersection:

```python
set(range(start, end + 1))  # +1 because range() is exclusive on end
```

**Verify from `ast_utils.py`:**
- `signature_range` = `(node.lineno, max(node.lineno, node.body[0].lineno - 1))` — inclusive both ends
- `body_range` = `(doc_end + 1, end_lineno)` — inclusive both ends
- `docstring_range` = `(first.lineno, first.end_lineno)` — inclusive both ends

### Edge Cases to Handle

**Deleted functions (FR56):** Functions that appear in the diff's `-` side but not in the current AST are handled naturally — `map_lines_to_symbols` only returns symbols that exist in the current AST, so deleted function lines get `line_map.get(line) → None` and are skipped.

**Relocated functions (FR57):** Treated as delete-plus-add. The new location's lines appear in `changed_lines`, are mapped to the symbol at the new location, and classified as body changes if the docstring wasn't updated.

**Symbols with no docstring (FR54):** Skipped by the `symbol.docstring_range is None` check in the orchestrator. This is the check that matters — `_classify_changed_lines` won't even be called.

**Module symbol changes:** The module symbol spans the entire file. Lines that belong to specific functions/classes are mapped to those inner symbols (innermost wins in `map_lines_to_symbols`). Only truly module-level lines (imports, top-level assignments outside any function/class) map to the module symbol.

**`body_range` where `start >= end`:** Indicates an effectively empty body (e.g., a function that's just a docstring). `range(start, end + 1)` may produce a single-line range or empty range — both handled correctly by set intersection.

### `Symbol` is Frozen — Use as Dict Key

`Symbol` is a frozen dataclass (`frozen=True`), so it is hashable and can be used as a dict key in `symbol_changes: dict[Symbol, set[int]]`. Do NOT use `symbol.name` or `symbol.line` as the key — multiple symbols could share names (methods in different classes), and we need the exact symbol object for classification.

### Message Format (Architecture Decision 5)

**Diff mode pattern:** `{Kind} '{name}' {classification} changed but docstring not updated`

Use `symbol.kind.capitalize()` for the kind label:
- `"Function 'send_request' signature changed but docstring not updated"`
- `"Method 'process' body changed but docstring not updated"`
- `"Function 'parse' import changed but docstring not updated"`
- `"Class 'Config' body changed but docstring not updated"`
- `"Module '<module>' import changed but docstring not updated"`

### Testing Approach

**Unit tests only for Story 4.2** — no integration tests needed. Integration tests (temp git repos) come in Story 4.3 (CLI wiring).

**Test file:** `tests/unit/checks/test_freshness.py` (extend existing file)

**New imports needed in test file:**
```python
from docvet.checks.freshness import _classify_changed_lines, check_freshness_diff
```

**Testing `_classify_changed_lines`:** Use `_make_symbol` helper (already exists in test file). Create symbols with known ranges, pass specific `changed_lines` sets, assert return value.

**Testing `check_freshness_diff`:** Need real source strings + `ast.parse()` to get a valid AST tree. Use the `parse_source` pattern from conftest.py or inline `ast.parse()` calls. Combine with realistic diff output strings that target specific line ranges in the source.

**Test naming convention:** `test_{rule_id}_when_{condition}_returns_{expected}`

**Key test patterns for `check_freshness_diff`:**
```python
import ast

source = '''\
def greet(name):
    """Say hello."""
    return f"Hello, {name}"
'''
tree = ast.parse(source)

# Diff that changes line 3 (body) but not line 2 (docstring)
diff = "... @@ -3,1 +3,1 @@ ...\n-    return ...\n+    return ..."
findings = check_freshness_diff("test.py", diff, tree)
# Assert stale-body finding
```

**IMPORTANT:** When creating test source strings, count lines carefully. Line 1 is the first line. Multiline strings with `'''` start the content on line 1 if the content follows immediately, or line 2 if there's a newline after the opening `'''`.

### Previous Story Learnings (Story 4.1)

- Ruff flagged unused imports — `map_lines_to_symbols` was marked `noqa: F401` because it wasn't used yet. In 4.2, remove that noqa since it's now used.
- `ast` import was removed from the 4.1 skeleton since it wasn't needed. Add it back now.
- 20 existing freshness tests + 415 total project tests. New tests in 4.2 should not regress any of these.
- The `_make_symbol` helper in the test file creates symbols with realistic ranges — extend it or use it as-is for classification tests.
- Code review found: empty `TYPE_CHECKING` block was speculative dead code — don't add speculative imports.

### What NOT to Implement in Story 4.2

- CLI wiring (`_run_freshness` replacement) — Story 4.3
- Any drift mode code (`_parse_blame_timestamps`, `_compute_drift`, `_compute_age`, `check_freshness_drift`) — Epic 5
- Integration tests with git repos — Story 4.3
- Changes to `ast_utils.py`, `config.py`, or `cli.py` — none needed

### Project Structure Notes

| File | Action |
|------|--------|
| `src/docvet/checks/freshness.py` | **MODIFY** — add `_CLASSIFICATION_MAP`, `_classify_changed_lines`, `check_freshness_diff`, update imports |
| `tests/unit/checks/test_freshness.py` | **MODIFY** — add ~20 tests for classification and orchestrator |

No new files. No changes to any other source files.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 4.2 acceptance criteria, Epic 4 FR coverage (FR44-FR49, FR54, FR56, FR57, FR59-FR62, FR66)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Decision 4 (line classification), Decision 5 (message format), Decision 6 (error handling), data flow diagram, freshness naming/structure patterns]
- [Source: `src/docvet/checks/freshness.py` — Current module state (97 lines): `_HUNK_PATTERN`, `_build_finding`, `_parse_diff_hunks`]
- [Source: `src/docvet/ast_utils.py` — `Symbol` dataclass fields (signature_range, body_range, docstring_range), `map_lines_to_symbols` function, range conventions (inclusive both ends)]
- [Source: `src/docvet/checks/__init__.py` — Finding dataclass (6 frozen fields with `__post_init__` validation)]
- [Source: `tests/unit/checks/test_freshness.py` — Existing 20 tests, `_make_symbol` helper, test structure]
- [Source: `_bmad-output/implementation-artifacts/4-1-diff-hunk-parser-and-shared-infrastructure.md` — Story 4.1 completion notes and learnings]
- [Source: `_bmad-output/implementation-artifacts/epic-3-retro-2026-02-09.md` — Enrichment module learnings, text parsing edge cases as category]
- [Source: `_bmad-output/project-context.md` — 73 implementation rules including testing, naming, import patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
