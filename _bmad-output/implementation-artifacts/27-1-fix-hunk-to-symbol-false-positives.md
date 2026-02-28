# Story 27.1: Fix Hunk-to-Symbol False Positives

Status: done
Branch: `feat/freshness-27-1-fix-hunk-to-symbol-false-positives`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/218

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer running `docvet freshness`**,
I want unchanged symbols adjacent to modified code to not be flagged as stale,
so that I can trust freshness results without manually dismissing false positives.

## Acceptance Criteria

1. **Given** a file where a new function is added immediately above an existing function **When** `docvet freshness` runs on the diff **Then** the existing function below the insertion point produces zero freshness findings (its code and docstring are unchanged)
2. **Given** a file where an import is added to the import block **When** the import block change creates a diff hunk whose context overlaps with an adjacent class definition **Then** the adjacent class produces zero freshness findings
3. **Given** a file where a new constant is added above an existing function **When** the diff context lines extend into the function's definition region **Then** the existing function produces zero freshness findings
4. **Given** a symbol whose signature genuinely changed (parameter added/removed/renamed) **When** `docvet freshness` runs **Then** the symbol is still correctly flagged as `stale-signature` (HIGH severity) — only false positives are eliminated, not true positives
5. **Given** the hunk-to-symbol mapping implementation **When** inspecting changed lines within a hunk **Then** only `+`/`-` lines (additions/deletions) are mapped to symbols — context lines (` ` prefix) are excluded from symbol matching
6. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all tests pass **And** existing freshness unit and integration tests continue to verify true positive detection
7. **Given** `docvet check --all` runs on docvet's own codebase **When** the command completes **Then** zero false positive freshness findings are produced

## Tasks / Subtasks

- [x] Task 1: Refactor `_parse_diff_hunks()` to exclude context lines (AC: 5)
  - [x] 1.1: Modify `_parse_diff_hunks()` in `src/docvet/checks/freshness.py` (lines 90-123) to parse actual diff body lines instead of expanding hunk header ranges. Track line numbers incrementally: `+` lines get their new-file line number added to the set; ` ` (context) lines increment the counter but are NOT added; `-` lines are skipped (old file only). See "Implementation Approach" in Dev Notes.
  - [x] 1.2: Update the function's docstring to document the context-line exclusion behavior
  - [x] 1.3: Verify the return type is still `set[int]` — no interface change for downstream consumers (`check_freshness_diff()`)
- [x] Task 2: Add unit tests for context-line exclusion (AC: 1, 2, 3, 5)
  - [x] 2.1: Add test case: new function added above existing function — context lines overlap adjacent symbol → zero findings for adjacent symbol
  - [x] 2.2: Add test case: import added — context lines overlap adjacent class → zero findings for class
  - [x] 2.3: Add test case: constant added — context lines extend into function definition → zero findings for function
  - [x] 2.4: Add test case: diff with mixed `+`/`-`/` ` lines — only `+`/`-` lines produce changed line numbers
  - [x] 2.5: Add test case: diff with ONLY context lines in a hunk region for a symbol → symbol NOT flagged
- [x] Task 3: Add regression tests for true positive preservation (AC: 4, 6)
  - [x] 3.1: Add test case: genuine signature change with context lines present → still correctly flagged as `stale-signature`
  - [x] 3.2: Add test case: genuine body change with adjacent unchanged symbols → changed symbol flagged, unchanged symbols not flagged
  - [x] 3.3: Verify all existing `TestParseDiffHunks`, `TestClassifyChangedLines`, and `TestCheckFreshnessDiff` tests still pass
  - [x] 3.4: Add integration test: create two adjacent functions in a temp git repo, modify one function, run `check_freshness_diff()`, assert zero findings on the unchanged adjacent function (end-to-end validation of ACs 1-3)
- [x] Task 4: Update `_make_diff()` helper for richer test data (AC: 5)
  - [x] 4.1: Extend or create a new helper that generates realistic unified diffs with context lines (` ` prefix), additions (`+`), and deletions (`-`) — the current `_make_diff()` (line ~470 in test file) only includes hunk headers and one `+changed` line
- [x] Task 5: Run quality gates and dogfood (AC: 6, 7)
  - [x] 5.1: Run `uv run pytest` — all tests pass (existing + new)
  - [x] 5.2: Run `docvet check --all` — zero findings on own codebase
  - [x] 5.3: Run all quality gates (ruff, format, ty, interrogate)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_new_function_above_existing_no_false_positive`, integration `test_adjacent_function_not_flagged_when_neighbor_modified` | PASS |
| 2 | `test_import_context_overlaps_adjacent_class_no_false_positive` | PASS |
| 3 | `test_constant_above_function_context_overlap_no_false_positive` | PASS |
| 4 | `test_genuine_signature_change_still_flagged_with_context`, `test_genuine_body_change_adjacent_unchanged_not_flagged` | PASS |
| 5 | `test_context_lines_excluded_from_changed_set`, `test_mixed_addition_deletion_context_lines`, `test_only_context_lines_in_hunk_produces_empty`, `test_no_newline_marker_skipped`, `test_deletions_do_not_shift_line_numbers` | PASS |
| 6 | Full test suite: 983 tests pass, zero regressions | PASS |
| 7 | `docvet check --all`: zero findings on own codebase | PASS |

## Dev Notes

- **This is the first code-changing epic since Epic 24** (LSP server). The freshness module hasn't been modified since Epic 5. Approach with care — the module is stable and well-tested (113 existing tests).
- **Root cause**: `_parse_diff_hunks()` reads hunk headers (`@@ -old,count +new,count @@`) and expands the line range to ALL lines: `range(start, start + count)`. Git's unified diff format includes 3 context lines (` ` prefix) above/below each actual change. When a change occurs near a symbol boundary, these context lines bleed into adjacent unchanged symbols, causing false positives.
- **Scope of change**: ONLY `_parse_diff_hunks()` needs modification. The downstream pipeline (`check_freshness_diff()` → `_classify_changed_lines()`) works correctly once it receives accurate changed-line sets. No changes needed to `ast_utils.py`, `cli.py`, or any other module.

### Implementation Approach

The current `_parse_diff_hunks()` (lines 90-123) only reads hunk headers:

```python
# CURRENT (buggy) — treats all hunk lines as changed
match = _HUNK_PATTERN.match(line)
if match:
    start = int(match.group(1))
    count = int(match.group(2) or "1")
    changed.update(range(start, start + count))
```

**Required change**: After encountering a hunk header, iterate through the subsequent diff body lines and track line numbers:

```
For each line after a hunk header:
  - If line starts with '+' (but NOT '+++'):
      → Add current_line to changed set
      → Increment current_line
  - If line starts with '-' (but NOT '---'):
      → Do NOT add to changed set (old file line, not in new file)
      → Do NOT increment current_line (deletions don't occupy new-file lines)
  - If line starts with ' ' (space — context line):
      → Do NOT add to changed set
      → Increment current_line
  - If line starts with '\' (no newline at end):
      → Skip (metadata, no line number change)
  - If line starts with 'diff' or '---' or '+++':
      → New file header, reset state
  - If line starts with '@@':
      → New hunk header, parse start/count as before
```

The key insight: `current_line` starts at the hunk header's `+start` value. Only `+` lines and ` ` lines advance the new-file line counter, but only `+` lines are added to the changed set.

> **Guardrail:** We track new-file line numbers only because `map_lines_to_symbols()` operates on the current AST (new file), not the old file. Old-file line numbers from `-` lines are meaningless in the new-file coordinate space.

### Key Functions and Line Numbers

| Function | File | Lines | Purpose | Modification Needed? |
|----------|------|-------|---------|---------------------|
| `_HUNK_PATTERN` | freshness.py | 37 | Regex for hunk headers | No — still needed for start/count extraction |
| `_parse_diff_hunks()` | freshness.py | 90-123 | Extract changed lines from diff | **YES — core fix** |
| `_classify_changed_lines()` | freshness.py | 126-163 | Classify change type per symbol | No |
| `check_freshness_diff()` | freshness.py | 166-219 | Main entry point for diff mode | No (interface unchanged) |
| `map_lines_to_symbols()` | ast_utils.py | 323-351 | Line→Symbol mapping | No |
| `_make_diff()` | test_freshness.py | ~470-479 | Test helper for minimal diffs | Extend for context lines |

### Symbol Data Structure (for reference)

```python
@dataclass(frozen=True)
class Symbol:
    name: str
    kind: Literal["function", "class", "method", "module"]
    line: int                                      # def/class keyword line
    end_line: int                                  # last line of body
    definition_start: int                          # first decorator or def/class
    docstring: str | None
    docstring_range: tuple[int, int] | None       # (start_line, end_line)
    signature_range: tuple[int, int] | None       # (start_line, end_line)
    body_range: tuple[int, int]                    # (start_line, end_line) excluding docstring
    parent: str | None
```

### Existing Test Patterns

The test file (`tests/unit/checks/test_freshness.py`) uses these patterns:

- **`_make_diff(start, count)`**: Creates minimal unified diff with hunk header + `+changed` line. Must be extended to support context lines.
- **`_make_function_symbol()`**: Creates test `Symbol` with customizable ranges.
- **Test classes**: `TestHunkPattern`, `TestParseDiffHunks`, `TestClassifyChangedLines`, `TestCheckFreshnessDiff`.
- **Source fixtures**: `_SIMPLE_SOURCE` (1 function), `_TWO_FUNC_SOURCE` (2 functions with import), `_NO_DOC_SOURCE`, `_DECORATED_SOURCE`.
- **Mocking**: `check_freshness_diff()` tests mock `subprocess.run` to inject diff output and provide source code strings parsed via `ast.parse()`.

### SonarQube Consideration

- `_parse_diff_hunks()` current CC is low. The refactored version with line-by-line parsing may increase CC. Target CC ≤ 12 to stay under the SonarQube threshold of 15.
- If the state machine gets complex, consider extracting the line-type dispatch into a helper function.
- Use `analyze_code_snippet` for fast CC feedback during development.

### Anti-Patterns (Do NOT)

- Do NOT modify `_classify_changed_lines()` — it works correctly once given accurate line sets
- Do NOT modify `map_lines_to_symbols()` in ast_utils.py — the mapping is correct; the input is wrong
- Do NOT change the return type of `_parse_diff_hunks()` — downstream consumers expect `set[int]`
- Do NOT break existing true-positive detection — every existing test MUST continue passing
- Do NOT add git as a dependency — git output parsing stays as string processing
- Do NOT use external diff parsing libraries — keep it stdlib-only

### Edge Cases to Test

1. **Diff with only context lines overlapping a symbol**: Symbol should NOT be flagged
2. **Diff with `+` lines at exact symbol boundary**: Symbol SHOULD be flagged
3. **Diff where deletion (`-`) removes a line inside a symbol**: The corresponding new-file lines may shift — verify line mapping still works
4. **Diff with `\ No newline at end of file`**: Should be skipped without affecting line counts
5. **Multi-hunk diff where one hunk has real changes and another only overlaps via context**: Only the actually-changed symbol should be flagged
6. **New file diff (`/dev/null` → file)**: All lines are `+` lines, no context — should work as before
7. **Interleaved `+`/`-`/` ` lines within a single hunk**: Verify `_parse_diff_hunks()` returns exactly the correct new-file line numbers for `+` lines only — deletions must NOT increment the new-file line counter or subsequent line numbers will drift

### Project Structure Notes

- Modified: `src/docvet/checks/freshness.py` (refactor `_parse_diff_hunks()`)
- Modified: `tests/unit/checks/test_freshness.py` (new tests + extend helper)
- Modified: `tests/integration/test_freshness_diff.py` (mandatory — at least one integration test for false-positive absence)
- No new files expected

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 27, Story 27.1]
- [Source: GitHub Issue #176 — Hunk-to-symbol false positives]
- [Source: src/docvet/checks/freshness.py — `_parse_diff_hunks()` lines 90-123]
- [Source: src/docvet/ast_utils.py — `map_lines_to_symbols()` lines 323-351]
- [Source: tests/unit/checks/test_freshness.py — existing test patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md — Freshness check design]

### Documentation Impact

- Pages: docs/site/checks/freshness.md
- Nature of update: No content change expected — the fix is a bug fix to existing behavior, not a new feature. The freshness check page already documents diff mode correctly. However, if the page mentions "changed lines" in a way that implies context lines are included, a precision fix may be needed. Verify during implementation.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (983 passed), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Refactored `_parse_diff_hunks()` from hunk-header-range expansion to line-by-line diff body parsing. Only `+` (addition) lines are now included in the changed-line set; context lines (space prefix) and deletion lines (`-` prefix) are excluded.
- Simplified new-file detection: `--- /dev/null` now triggers immediate `return set()` instead of deferred flag check at end.
- Combined `--- /dev/null` and `Binary files` into a single `startswith` tuple check to reduce CC.
- Updated 5 existing tests that relied on the old hunk-range-expansion behavior to match the corrected behavior.
- Added 11 new unit tests (5 at `_parse_diff_hunks` level, 4 false-positive absence at `check_freshness_diff` level, 2 regression tests for true-positive preservation).
- Added 1 integration test using a real temp git repo to validate end-to-end false-positive absence.
- Created `_make_diff_with_body()` helper for generating realistic diffs with context/addition/deletion lines.
- Docs page `docs/site/checks/freshness.md` verified — no update needed (bug fix, not new feature).
- CC of `_parse_diff_hunks()` reduced by extracting `_diff_line_delta()` helper during code review (CC ~8, well under 15 SonarQube threshold).

### Change Log

- 2026-02-28: Implemented Story 27.1 — fixed `_parse_diff_hunks()` false positives by parsing diff body lines instead of expanding hunk header ranges. Added 12 new tests (5 parse-level + 6 check-level + 1 integration). Updated 5 existing tests. Zero regressions (983 tests pass).
- 2026-02-28: Code review fixes — extracted `_diff_line_delta()` helper to reduce CC (H1), refactored 3 tests to use `_make_diff_with_body()` (M1), fixed 2 stale test comments (L1), corrected completion notes (L2), fixed module docstring example (pre-existing).

### File List

- `src/docvet/checks/freshness.py` — refactored `_parse_diff_hunks()` (core fix)
- `tests/unit/checks/test_freshness.py` — updated 5 existing tests, added 11 new tests, added `_make_diff_with_body()` helper
- `tests/integration/test_freshness_diff.py` — new file: 1 integration test for false-positive absence

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approved — all findings fixed in review.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | `_parse_diff_hunks()` CC=18 exceeded SonarQube threshold 15 | Extracted `_diff_line_delta()` helper, simplified hunk header parsing — CC now 0 issues |
| M1 | LOW (downgraded) | `_make_diff_with_body()` defined but never called | Refactored 3 tests to use helper |
| L1 | LOW | Stale test comments after `_make_diff()` behavior change | Updated 2 comments |
| L2 | LOW | Completion Notes count said "7" but actual count is 11 | Corrected notes |
| — | — | Module docstring example had 4 args instead of 3 (pre-existing) | Fixed example |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass (983 tests, ruff, format, ty, docvet check --all zero findings)
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
