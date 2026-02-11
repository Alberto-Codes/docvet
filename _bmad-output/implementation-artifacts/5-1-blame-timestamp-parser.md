# Story 5.1: Blame Timestamp Parser

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a parser that extracts per-line modification timestamps from `git blame --line-porcelain` output,
so that drift mode can determine when each line of code was last modified.

## Acceptance Criteria

1. **Given** a `git blame --line-porcelain` output string with multiple blame entries, **When** `_parse_blame_timestamps(blame_output)` is called, **Then** it returns a `dict[int, int]` mapping 1-based line numbers to Unix timestamps extracted from `author-time` fields
2. **Given** a blame entry with a 40-character SHA line containing the final line number as the 3rd field, **When** `_parse_blame_timestamps` parses it, **Then** it extracts the line number via `line.split()` (positional, no regex)
3. **Given** a blame entry with an `author-time 1707500000` header line, **When** `_parse_blame_timestamps` parses it, **Then** it extracts `1707500000` as the Unix timestamp for the current blame block
4. **Given** a blame entry with header fields like `author`, `author-mail`, `committer`, `summary`, etc., **When** `_parse_blame_timestamps` parses it, **Then** those lines are silently skipped (only SHA and `author-time` are consumed)
5. **Given** an empty string as `blame_output`, **When** `_parse_blame_timestamps(blame_output)` is called, **Then** it returns an empty dict (no crash, no exception — NFR25)
6. **Given** a blame output from an initial commit (boundary commit), **When** `_parse_blame_timestamps` parses it, **Then** it parses normally — `author-time` is still present on boundary commits
7. **Given** a blame output with uncommitted changes (zero SHA `0000000...`), **When** `_parse_blame_timestamps` parses it, **Then** it parses normally — `author-time` reflects working copy time
8. **Given** lines that don't match any expected format (corrupted or truncated blame data), **When** `_parse_blame_timestamps` encounters them, **Then** they are silently skipped (NFR25 — never raises exceptions)

## Tasks / Subtasks

- [x] Task 1: Add `_parse_blame_timestamps` to `src/docvet/checks/freshness.py` (AC: 1-8)
  - [x] 1.1: Add a "Drift mode helpers" section header after the `check_freshness_diff` function (line ~199), following the module organization pattern
  - [x] 1.2: Implement `_parse_blame_timestamps(blame_output: str) -> dict[int, int]:` with Google-style docstring
  - [x] 1.3: Early return empty dict on empty input (`if not blame_output: return {}`)
  - [x] 1.4: Implement state machine: track `current_line` (from SHA line) and `current_timestamp` (from `author-time` line)
  - [x] 1.5: SHA line detection: check `len(parts) >= 3` and `len(parts[0]) == 40` after `line.split()`, extract `int(parts[2])` as final line number
  - [x] 1.6: `author-time` detection: `line.startswith("author-time ")`, extract `int(line.split()[1])` as Unix timestamp
  - [x] 1.7: Tab-prefixed content line detection: `line.startswith("\t")`, emit `{current_line: current_timestamp}` to result dict, reset state
  - [x] 1.8: Silently skip all other lines (other blame headers, empty lines, corrupted data)
  - [x] 1.9: Handle edge cases: boundary commits, zero SHA (uncommitted), truncated blocks (missing author-time or content line)
- [x] Task 2: Create unit tests for `_parse_blame_timestamps` in `tests/unit/checks/test_freshness.py` (AC: 1-8)
  - [x] 2.1: Add `_parse_blame_timestamps` to imports from `docvet.checks.freshness`
  - [x] 2.2: Add realistic `_BLAME_SINGLE_ENTRY` constant — one complete blame block for a single line
  - [x] 2.3: Add `_BLAME_MULTI_ENTRY` constant — multiple blame blocks covering 3+ lines with different timestamps
  - [x] 2.4: Test basic single entry → returns `{line_num: timestamp}` (AC 1, 2, 3)
  - [x] 2.5: Test multiple entries → returns complete `dict[int, int]` mapping (AC 1)
  - [x] 2.6: Test empty string → returns empty dict (AC 5)
  - [x] 2.7: Test header fields silently skipped (AC 4) — verify only line numbers and timestamps extracted, not author names etc.
  - [x] 2.8: Test boundary commit (SHA starts with `^` or has boundary marker) → parses normally (AC 6)
  - [x] 2.9: Test uncommitted changes (zero SHA `0000000...`) → parses normally (AC 7)
  - [x] 2.10: Test corrupted/truncated blame data → silently skipped, no exception (AC 8)
  - [x] 2.11: Test blame block missing `author-time` → that block skipped, no crash
  - [x] 2.12: Test blame block missing tab-prefixed content line (truncated at end) → partial data handled gracefully
  - [x] 2.13: Test whitespace-only input → returns empty dict
  - [x] 2.14: Test SHA line with only 2 fields (malformed) → silently skipped
- [x] Task 3: Run quality gates (AC: all)
  - [x] 3.1: `uv run ruff check .` — all checks pass
  - [x] 3.2: `uv run ruff format --check .` — all files formatted
  - [x] 3.3: `uv run ty check` — all type checks pass
  - [x] 3.4: `uv run pytest tests/unit/checks/test_freshness.py -v` — all freshness tests pass
  - [x] 3.5: `uv run pytest` — full suite passes, 0 regressions

## Dev Notes

### This is Story 5.1 — First Story in Epic 5 (Freshness Drift Mode)

This story extends `src/docvet/checks/freshness.py` (199 lines, diff mode complete) and `tests/unit/checks/test_freshness.py`. No new files created. No existing source files other than `freshness.py` are modified. This follows the same pattern as Story 4.1 (first parser story in Epic 4).

### Current State of `freshness.py` (After Epic 4)

```
freshness.py (199 lines):
1-11:   Module docstring, imports (ast, re, Literal, Symbol, map_lines_to_symbols, Finding, FreshnessConfig)
12-28:  Module-level constants (_HUNK_PATTERN, rule IDs, _CLASSIFICATION_MAP)
29-62:  Shared helpers (_build_finding)
63-103: Diff mode helpers (_parse_diff_hunks)
104-143: Diff mode helpers (_classify_changed_lines)
144-199: check_freshness_diff public function
--- Story 5.1 adds here ---
NEW:    Drift mode helpers (_parse_blame_timestamps)
--- Story 5.2 adds here ---
FUTURE: Drift mode helpers (_compute_drift, _compute_age)
FUTURE: check_freshness_drift public function
```

**Imports — NO changes needed.** All required imports already exist. Do NOT add `import time` — that's Story 5.2. Do NOT remove the `FreshnessConfig` `noqa: F401` — that's consumed in Story 5.2.

### `_parse_blame_timestamps` Implementation (Architecture Decision 3)

**Signature:**
```python
def _parse_blame_timestamps(blame_output: str) -> dict[int, int]:
```

**State machine design — line-by-line iteration:**

```python
def _parse_blame_timestamps(blame_output: str) -> dict[int, int]:
    if not blame_output:
        return {}

    timestamps: dict[int, int] = {}
    current_line: int | None = None
    current_timestamp: int | None = None

    for line in blame_output.splitlines():
        # SHA line: 40-hex-chars orig_line final_line [count]
        parts = line.split()
        if len(parts) >= 3 and len(parts[0]) == 40:
            try:
                current_line = int(parts[2])
            except ValueError:
                current_line = None
            current_timestamp = None  # Reset for new block
            continue

        # author-time line
        if line.startswith("author-time "):
            try:
                current_timestamp = int(line.split()[1])
            except (ValueError, IndexError):
                pass
            continue

        # Tab-prefixed content line — end of blame block
        if line.startswith("\t"):
            if current_line is not None and current_timestamp is not None:
                timestamps[current_line] = current_timestamp
            current_line = None
            current_timestamp = None
            continue

        # All other lines (author, committer, summary, filename, etc.) — skip

    return timestamps
```

**Key design points:**
- Returns `dict[int, int]` for direct consumption by `map_lines_to_symbols` in Story 5.2
- Uses `.splitlines()` NOT `.split("\n")` — handles Windows `\r\n`
- SHA detection: `len(parts[0]) == 40` (not regex) — simple and fast
- State variables `current_line` / `current_timestamp` reset on each SHA line and content line
- `try/except ValueError` on int conversions — defensive against malformed data
- Tab-prefixed content line triggers emit — this is the architectural trigger for "block complete"
- If a block is missing `author-time` or the content line, partial state is silently discarded
- All unrecognized lines silently skipped — no warnings, no exceptions (NFR25)

### `git blame --line-porcelain` Format Reference

A single blame block looks like:
```
abc1234567890123456789012345678901234567890 1 1 3
author Developer Name
author-mail <dev@example.com>
author-time 1707500000
author-tz +0000
committer Developer Name
committer-mail <dev@example.com>
committer-time 1707500000
committer-tz +0000
summary Initial commit
filename module.py
	def greet(name):
```

**Field breakdown for SHA line:** `<40-char-sha> <orig_line> <final_line> [<num_lines>]`
- Field 0 (index 0): 40-character hex SHA
- Field 1 (index 1): original line number in the commit
- Field 2 (index 2): **final line number in current file** — this is what we extract
- Field 3 (index 3, optional): number of lines in this group (only on first entry of a group)

**Boundary commits:** SHA may be prefixed with `^` in some outputs, but `--line-porcelain` always uses 40-char SHA. `author-time` is still present.

**Uncommitted changes:** SHA is `0000000000000000000000000000000000000000` (40 zeros). `author-time` reflects working copy time.

**Content line:** Always starts with `\t` (literal tab character). This is the actual source line.

### Error Handling: Defensive by Design, No Try/Except (Decision 6)

Defensive gates (same philosophy as `_parse_diff_hunks`):

1. Early return empty dict on empty input
2. SHA detection via `len(parts) >= 3 and len(parts[0]) == 40` — rejects short lines and non-SHA lines
3. `try/except ValueError` on `int()` conversions — handles non-numeric fields gracefully
4. Content line emit requires both `current_line` and `current_timestamp` to be non-None — incomplete blocks produce no entry
5. All unrecognized lines silently skipped — safe direction (false negatives over crashes)

**Exception:** Unlike `_parse_diff_hunks` which uses no try/except at all, `_parse_blame_timestamps` uses targeted `try/except ValueError` on `int()` conversions. This is because blame output has more free-form fields where a corrupted line could plausibly look like a SHA line but have non-numeric fields. The try/except is the minimal defensive wrapper.

### Testing Approach

**Unit tests only for Story 5.1** — no integration tests needed. Integration tests (temp git repos with blame history) come in Story 5.3.

**Test file:** `tests/unit/checks/test_freshness.py` (extend existing file)

**New import:**
```python
from docvet.checks.freshness import _parse_blame_timestamps
```

**Realistic blame output for tests:**

Use multiline string constants with proper `git blame --line-porcelain` format. The constants should be defined at module level (following the pattern of `_SIMPLE_SOURCE`, `_TWO_FUNC_SOURCE` etc.).

**Single blame entry constant:**
```python
_BLAME_SINGLE_ENTRY = """\
abc1234567890123456789012345678901234567890 1 1 1
author Test Author
author-mail <test@example.com>
author-time 1707500000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Initial commit
filename test.py
\tdef greet(name):
"""
```

**Multi-entry constant:** Should have 3+ lines with different timestamps to verify complete mapping.

**Edge case tests to include:**
- Empty string → empty dict
- Whitespace-only string → empty dict
- Single blame entry → `{1: 1707500000}`
- Multiple entries with different timestamps → complete mapping
- Boundary commit (normal 40-char SHA with `author-time` present) → parsed normally
- Zero SHA (uncommitted) → parsed normally
- Truncated block (SHA line + author-time but no tab content line) → no entry emitted
- Block missing `author-time` → no entry emitted
- Malformed SHA line (only 2 fields) → silently skipped
- Non-numeric third field in SHA-like line → silently skipped
- Corrupted data interspersed with valid blocks → valid blocks still parsed

**Test class:** `TestParseBlameTimestamps` (following the `TestParseDiffHunks` naming pattern)

### Naming Conventions

- Private function: `_parse_blame_timestamps` (follows `_parse_*` pattern for text parsing)
- Anti-patterns: Do NOT use `_handle_blame`, `_process_blame`, `_get_timestamps`
- Test constant naming: `_BLAME_SINGLE_ENTRY`, `_BLAME_MULTI_ENTRY` (ALL_CAPS, private)

### What NOT to Implement in Story 5.1

- `_compute_drift` — Story 5.2
- `_compute_age` — Story 5.2
- `check_freshness_drift` public orchestrator — Story 5.2
- CLI wiring changes — Story 5.3
- Integration tests with git repos — Story 5.3
- `import time` — Story 5.2 (not needed for parsing)
- Any drift-specific constants or classification maps — Story 5.2
- Changes to `ast_utils.py`, `config.py`, or `cli.py` — none needed

### Previous Story Learnings (Epic 4)

- **Ruff flagged unused imports in 4.1** — don't add speculative imports. Only import what this story uses.
- **Zero-debugging in 4.2** when following architecture exactly — stick to the spec.
- **Edge case test gaps found in every code review** — be thorough with boundary tests. The code review will look for missing edge cases.
- **Empty TYPE_CHECKING block was flagged as dead code in 4.1** — don't add speculative blocks.
- **Test naming accuracy matters** — name tests after what they actually test, not what you intend them to test.
- **Documentation accuracy** — docstrings must match actual behavior. Don't promise error handling that doesn't exist.
- **`_make_symbol` helper** exists in test file for creating test symbols — not needed for Story 5.1 (blame parser doesn't use Symbol), but available for Story 5.2.

### Project Structure Notes

| File | Action |
|------|--------|
| `src/docvet/checks/freshness.py` | **MODIFY** — add drift mode section header, add `_parse_blame_timestamps` function |
| `tests/unit/checks/test_freshness.py` | **MODIFY** — add blame output constants, add `TestParseBlameTimestamps` test class (~12 tests) |

No new files. No changes to any other source files.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 5.1 acceptance criteria, Epic 5 FR coverage (FR50, NFR25, NFR29)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Decision 3 (blame parsing state machine), Decision 6 (error handling), naming conventions, module organization]
- [Source: `src/docvet/checks/freshness.py` — Current module state (199 lines): diff mode complete, drift mode section placeholder needed]
- [Source: `src/docvet/checks/__init__.py` — Finding dataclass (6 frozen fields with `__post_init__` validation)]
- [Source: `src/docvet/ast_utils.py` — Symbol dataclass fields (signature_range, body_range, docstring_range), `map_lines_to_symbols` function]
- [Source: `src/docvet/config.py` — FreshnessConfig (drift_threshold=30, age_threshold=90)]
- [Source: `_bmad-output/implementation-artifacts/4-1-diff-hunk-parser-and-shared-infrastructure.md` — Parallel story pattern (parser story in previous epic)]
- [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-02-10.md` — Epic 4 retrospective learnings]
- [Source: `_bmad-output/project-context.md` — 73 implementation rules including testing, naming, import patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Initial test run: 6 failures due to test constants using 43-char SHAs instead of 40-char. Fixed by replacing with proper 40-char hex strings.

### Completion Notes List

- Implemented `_parse_blame_timestamps` state machine parser in freshness.py (lines 207–261), following architecture Decision 3 exactly
- Added "Drift mode helpers" section header at line 202, consistent with existing module organization
- No new imports needed — all existing imports sufficient for this parser
- 13 unit tests added in `TestParseBlameTimestamps` class covering all 8 ACs plus edge cases
- Test constants `_BLAME_SINGLE_ENTRY` and `_BLAME_MULTI_ENTRY` use realistic git blame porcelain format
- All quality gates pass: ruff lint, ruff format, ty check, 485/485 tests (13 new, 0 regressions)

### Change Log

- 2026-02-10: Implemented `_parse_blame_timestamps` parser and 13 unit tests (Story 5.1 complete)

### File List

- `src/docvet/checks/freshness.py` — MODIFIED: added drift mode section header and `_parse_blame_timestamps` function (lines 202–261)
- `tests/unit/checks/test_freshness.py` — MODIFIED: added `_parse_blame_timestamps` import, `_BLAME_SINGLE_ENTRY` and `_BLAME_MULTI_ENTRY` constants, `TestParseBlameTimestamps` class with 13 tests
