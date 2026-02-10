# Story 4.1: Diff Hunk Parser and Shared Infrastructure

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a parser that extracts changed line numbers from git diff output and a shared finding builder,
so that diff mode has reliable input processing and freshness findings are constructed consistently.

## Acceptance Criteria

1. **Given** a git diff output string containing `@@ -10,5 +12,8 @@` hunk headers, **When** `_parse_diff_hunks(diff_output)` is called, **Then** it returns a `set[int]` containing the expanded line numbers from the `+start,count` ranges (e.g., `{12, 13, 14, 15, 16, 17, 18, 19}`)
2. **Given** a git diff output with `--- /dev/null` (new file), **When** `_parse_diff_hunks(diff_output)` is called, **Then** it returns an empty set (FR55 — no prior docstring to become stale)
3. **Given** a git diff output containing `Binary files ... differ`, **When** `_parse_diff_hunks(diff_output)` is called, **Then** it returns an empty set (FR58 — skip binary files)
4. **Given** a hunk header with no count (`@@ -1 +1 @@`, missing `,count`), **When** `_parse_diff_hunks(diff_output)` is called, **Then** it treats the missing count as 1 and includes that single line number
5. **Given** an empty string as `diff_output`, **When** `_parse_diff_hunks(diff_output)` is called, **Then** it returns an empty set (no crash, no exception)
6. **Given** a git diff output with rename headers (`rename from ...` / `rename to ...`) or mode change lines, **When** `_parse_diff_hunks(diff_output)` is called, **Then** those lines are silently skipped and only hunk headers are processed
7. **Given** the `_build_finding` shared helper, **When** called with `file_path`, `symbol`, `rule`, `message`, `category`, **Then** it returns a `Finding` with `file=file_path`, `line=symbol.line`, `symbol=symbol.name`, and the provided `rule`, `message`, `category`
8. **Given** the `_HUNK_PATTERN` module-level constant, **When** inspected, **Then** it is a compiled regex matching `^@@ .+\+(\d+)(?:,(\d+))? @@`

## Tasks / Subtasks

- [x] Task 1: Create `src/docvet/checks/freshness.py` with module skeleton (AC: 8)
  - [x] 1.1: Create file with `from __future__ import annotations`, stdlib imports (`ast`, `re`), local imports (`Symbol`, `map_lines_to_symbols` from `ast_utils`, `Finding` from `checks`, `FreshnessConfig` from `config`)
  - [x] 1.2: Add `_HUNK_PATTERN = re.compile(r"^@@ .+\+(\d+)(?:,(\d+))? @@")` module-level constant
  - [x] 1.3: Add rule identifier string literals as comments for reference: `"stale-signature"`, `"stale-body"`, `"stale-import"`
- [x] Task 2: Implement `_parse_diff_hunks` (AC: 1, 2, 3, 4, 5, 6)
  - [x] 2.1: Signature: `def _parse_diff_hunks(diff_output: str) -> set[int]:`
  - [x] 2.2: Early return empty set on empty input
  - [x] 2.3: Iterate `diff_output.splitlines()` — single pass, line-by-line
  - [x] 2.4: Detect `--- /dev/null` → set `is_new_file` flag, return empty set at end
  - [x] 2.5: Detect `Binary files` prefix → return empty set immediately
  - [x] 2.6: Match hunk headers with `_HUNK_PATTERN.match(line)` → extract start/count, expand `range(start, start + count)`, add to result set
  - [x] 2.7: Default count to 1 when regex group(2) is None (missing `,count`)
  - [x] 2.8: Silently skip all unrecognized lines (rename headers, mode changes, context lines, etc.)
- [x] Task 3: Implement `_build_finding` shared helper (AC: 7)
  - [x] 3.1: Signature: `def _build_finding(file_path: str, symbol: Symbol, rule: str, message: str, category: Literal["required", "recommended"]) -> Finding:`
  - [x] 3.2: Returns `Finding(file=file_path, line=symbol.line, symbol=symbol.name, rule=rule, message=message, category=category)`
- [x] Task 4: Create `tests/unit/checks/test_freshness.py` with tests (AC: all)
  - [x] 4.1: Test `_parse_diff_hunks` — basic hunk expansion (AC 1)
  - [x] 4.2: Test `_parse_diff_hunks` — multiple hunks in single diff
  - [x] 4.3: Test `_parse_diff_hunks` — new file detection returns empty set (AC 2)
  - [x] 4.4: Test `_parse_diff_hunks` — binary file detection returns empty set (AC 3)
  - [x] 4.5: Test `_parse_diff_hunks` — missing count defaults to 1 (AC 4)
  - [x] 4.6: Test `_parse_diff_hunks` — empty string returns empty set (AC 5)
  - [x] 4.7: Test `_parse_diff_hunks` — rename/mode-change lines silently skipped (AC 6)
  - [x] 4.8: Test `_parse_diff_hunks` — count of 0 (deletion hunk with `+start,0`) returns no lines for that hunk
  - [x] 4.9: Test `_build_finding` — constructs Finding with correct field mapping (AC 7)
  - [x] 4.10: Test `_HUNK_PATTERN` — regex matches expected format (AC 8)
  - [x] 4.11: Run full test suite — zero regressions on enrichment tests (415 existing)

## Dev Notes

### This is Story 4.1 — First Story in Epic 4 (Freshness Diff Mode)

This story creates a **new file** (`src/docvet/checks/freshness.py`) and a **new test file** (`tests/unit/checks/test_freshness.py`). No existing files are modified. This establishes the freshness module that Stories 4.2 and 4.3 will extend.

### Module File Organization (Architecture Decision 1)

The freshness module uses mode-oriented flat structure within a single file. Story 4.1 creates the file skeleton and diff-mode infrastructure. The final file layout (after all 6 stories) will be:

```
freshness.py:
1. Module docstring
2. from __future__ import annotations
3. Stdlib imports (ast, re, time)
4. Local imports (ast_utils, Finding, FreshnessConfig)
5. Module-level constants (_HUNK_PATTERN, rule strings)
6. Shared helper functions (_build_finding)          ← Story 4.1
7. Diff mode helpers (_parse_diff_hunks)             ← Story 4.1
8. [_classify_changed_lines]                         ← Story 4.2
9. [check_freshness_diff public function]            ← Story 4.2
10. [Drift mode helpers]                             ← Story 5.1
11. [check_freshness_drift public function]          ← Story 5.2
```

**Story 4.1 delivers items 1-7.** Do NOT add a public orchestrator function yet — that comes in Story 4.2.

### `_parse_diff_hunks` Implementation (Architecture Decision 2)

**Signature:**
```python
def _parse_diff_hunks(diff_output: str) -> set[int]:
```

**Single-pass line iteration design:**

```python
def _parse_diff_hunks(diff_output: str) -> set[int]:
    if not diff_output:
        return set()

    changed: set[int] = set()
    is_new_file = False

    for line in diff_output.splitlines():
        if line.startswith("--- /dev/null"):
            is_new_file = True
            continue
        if line.startswith("Binary files"):
            return set()
        match = _HUNK_PATTERN.match(line)
        if match:
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            changed.update(range(start, start + count))

    if is_new_file:
        return set()
    return changed
```

**Key design points:**
- Returns `set[int]` for O(1) membership testing in downstream `_classify_changed_lines` (Story 4.2)
- Uses `.splitlines()` NOT `.split("\n")` — handles Windows `\r\n`
- `is_new_file` flag checked AFTER iteration (not early return) because `--- /dev/null` may appear before hunk headers
- `Binary files` triggers immediate `return set()` — no further processing needed
- All unrecognized lines silently skipped — no warnings, no exceptions (NFR25)
- Safe direction: false negatives (missed findings) over false positives

### `_HUNK_PATTERN` Regex (Architecture Decision 2)

```python
_HUNK_PATTERN = re.compile(r"^@@ .+\+(\d+)(?:,(\d+))? @@")
```

**Captured groups:**
- Group 1: `(\d+)` — starting line number in new file version
- Group 2: `(?:,(\d+))?` — optional line count. When `None`, defaults to `"1"` (single-line hunk)

**Edge case:** `@@ -1 +1 @@` (no comma, no count) — group(2) is `None`, default to 1 line.

### `_build_finding` Shared Helper (Architecture Decision 5)

```python
def _build_finding(
    file_path: str,
    symbol: Symbol,
    rule: str,
    message: str,
    category: Literal["required", "recommended"],
) -> Finding:
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule=rule,
        message=message,
        category=category,
    )
```

**Why shared helper (not inline `Finding()`):** Freshness has 5 rules with mechanical `file_path → file`, `symbol.line → line`, `symbol.name → symbol` mapping. A shared helper eliminates duplication. This differs from enrichment which constructs `Finding` inline in each `_check_*` function.

**Message format convention:** Use `symbol.kind.capitalize()` for the kind label in messages:
- `"Function 'name' signature changed but docstring not updated"`
- `"Class 'name' body changed but docstring not updated"`

### Error Handling: Defensive by Design, No Try/Except

Three defensive gates (Architecture Decision 6):

1. **`_parse_diff_hunks`** — returns empty `set[int]` on empty/unparseable input; never raises
2. **Unrecognized lines silently skipped** — produces false negatives (safe direction) over crashes
3. **Public functions (Story 4.2)** — will return `[]` on empty git output before calling parser

**No `try/except` blocks.** If a parser has a logic error, it should crash in tests so it gets fixed.

### Imports Pattern

Follow the established enrichment.py pattern:

```python
from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING, Literal

from docvet.ast_utils import Symbol, map_lines_to_symbols
from docvet.checks import Finding
from docvet.config import FreshnessConfig

if TYPE_CHECKING:
    pass  # Reserve for future type-only imports
```

**Note:** `time` import is NOT needed in Story 4.1 — only needed in Story 5.2 for drift mode. Import `map_lines_to_symbols` now since Story 4.2 will use it in the orchestrator — having the import ready avoids a diff-only change later.

### Testing Approach

**Unit tests only for Story 4.1** — no integration tests needed yet. Integration tests (temp git repos) come in Story 4.3 (CLI wiring).

**Test file:** `tests/unit/checks/test_freshness.py`

**Test structure:**

```python
"""Unit tests for the freshness check module."""

from __future__ import annotations

import re

from docvet.checks.freshness import _build_finding, _HUNK_PATTERN, _parse_diff_hunks
```

**Realistic diff output for tests (NOT fabricated):**

```
diff --git a/module.py b/module.py
index abc1234..def5678 100644
--- a/module.py
+++ b/module.py
@@ -10,3 +10,5 @@ def foo():
     pass
+    return 42
+    # new line
```

**Edge case tests to include:**
- Hunk with `count=0` (pure deletion in new file, e.g., `@@ -5,3 +5,0 @@`) — `range(5, 5)` produces empty range, no lines added
- Multiple hunks in one diff output
- Diff with both rename headers AND hunks (rename lines skipped, hunks processed)
- `--- /dev/null` followed by hunks — returns empty set (new file, FR55)
- `+++ /dev/null` (deleted file) — hunk headers may still appear but no changed lines in new version

### Naming Conventions

- Private functions: `_parse_*` for parsing, `_build_*` for construction
- Anti-patterns: Do NOT use `_process_diff`, `_handle_*`, `_get_severity`
- Constants: `_ALL_CAPS` at module level, private (not exported)
- Rule identifiers: string literals (`"stale-signature"`), NOT enums or variables

### What NOT to Implement in Story 4.1

- `_classify_changed_lines` — Story 4.2
- `check_freshness_diff` public orchestrator — Story 4.2
- CLI wiring (`_run_freshness` replacement) — Story 4.3
- Any drift mode code (`_parse_blame_timestamps`, etc.) — Epic 5
- Integration tests with git repos — Story 4.3

### Project Structure Notes

| File | Action |
|------|--------|
| `src/docvet/checks/freshness.py` | **CREATE** — new module with constants, `_parse_diff_hunks`, `_build_finding` |
| `tests/unit/checks/test_freshness.py` | **CREATE** — new test file with ~15 unit tests |

No existing files modified. No config changes. No CLI changes.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 4.1 acceptance criteria, Epic 4 FR coverage]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Decision 1 (module org), Decision 2 (diff parsing), Decision 5 (_build_finding), Decision 6 (error handling), naming conventions, data flow]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR43, FR55, FR58, FR59, FR60]
- [Source: `src/docvet/checks/enrichment.py` — Module structure pattern, import style, constant definitions]
- [Source: `src/docvet/checks/__init__.py` — Finding dataclass (6 frozen fields with __post_init__ validation)]
- [Source: `src/docvet/ast_utils.py` — Symbol dataclass fields (signature_range, body_range, docstring_range)]
- [Source: `src/docvet/config.py` — FreshnessConfig (drift_threshold=30, age_threshold=90)]
- [Source: `_bmad-output/implementation-artifacts/epic-3-retro-2026-02-09.md` — Enrichment learnings applicable to freshness]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Ruff flagged `map_lines_to_symbols` and `FreshnessConfig` imports as unused (F401). Added `noqa: F401` comments since these imports are intentionally pre-staged for Story 4.2 per architecture spec.
- Ruff auto-fixed import ordering (I001) and formatting in test file.

### Completion Notes List

- Created `src/docvet/checks/freshness.py` with module skeleton: `_HUNK_PATTERN` regex constant, `_build_finding` shared helper, `_parse_diff_hunks` diff parser
- Implementation follows architecture exactly: single-pass line iteration, `set[int]` return type, defensive empty-set returns for new/binary/empty files
- Created `tests/unit/checks/test_freshness.py` with 19 unit tests covering all 8 ACs plus edge cases (count=0, deleted file, multiple hunks, new file with hunks)
- All 434 tests pass (19 new + 415 existing), zero regressions
- Lint (ruff check), format (ruff format), and type check (ty check) all pass
- `ast` import removed from skeleton since it's not needed until Story 4.2; `map_lines_to_symbols` and `FreshnessConfig` kept with noqa for Story 4.2 readiness

### Change Log

- 2026-02-09: Created freshness module skeleton with diff hunk parser and shared finding builder (Story 4.1)
- 2026-02-09: Code review fixes — removed unused TYPE_CHECKING block, typed _make_symbol kind parameter, added whitespace-only input test

### File List

- `src/docvet/checks/freshness.py` (CREATE) — freshness check module with `_HUNK_PATTERN`, `_build_finding`, `_parse_diff_hunks`
- `tests/unit/checks/test_freshness.py` (CREATE) — 20 unit tests for freshness module

### Senior Developer Review (AI)

**Reviewer:** Alberto-Codes on 2026-02-09
**Outcome:** Approved with fixes applied

**AC Validation:** 8/8 implemented and verified
**Task Audit:** All [x] tasks confirmed as genuinely complete
**Regression Check:** 435 tests pass (20 freshness + 415 existing), lint clean, type check clean

**Issues Found:** 0 High, 3 Medium, 2 Low

**MEDIUM — Fixed:**
- M1: `_make_symbol` test helper `kind` parameter typed as `str` instead of `Literal` — fixed to use `Literal["function", "class", "method", "module"]` for type safety
- M2: No test for whitespace-only input — added `test_whitespace_only_returns_empty_set`
- M3: Empty `TYPE_CHECKING` block with `pass` was speculative dead code — removed along with unused `TYPE_CHECKING` import

**LOW — Noted:**
- L1: `_build_finding` tests don't verify Finding immutability (tested in `checks/__init__` tests, low risk)
- L2: Story subtask list enumerates 11 items but 20 tests exist — minor doc mismatch, all tests are valid
