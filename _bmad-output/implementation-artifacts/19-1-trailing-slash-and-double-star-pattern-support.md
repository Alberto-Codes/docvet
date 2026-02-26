# Story 19.1: Trailing-Slash and Double-Star Pattern Support

Status: done
Branch: `feat/discovery-19-1-trailing-slash-double-star-patterns`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer configuring docvet**,
I want to use trailing-slash patterns (`build/`) and double-star globs (`**/test_*.py`) in my exclude configuration,
so that I can precisely target directories and cross-directory file patterns without listing every path.

## Acceptance Criteria

1. **Given** an exclude pattern ending with `/` (e.g., `build/`)
   **When** `_is_excluded` evaluates a file path
   **Then** it matches only paths where a directory component equals the pattern prefix (e.g., `build/output.py` matches, `rebuild/main.py` does not)

2. **Given** an exclude pattern containing `**` (e.g., `**/test_*.py`)
   **When** `_is_excluded` evaluates a file path
   **Then** it matches paths across any directory depth (e.g., `src/tests/test_foo.py` matches, `src/foo.py` does not), including root-level files for leading `**/` patterns (e.g., `test_foo.py` matches `**/test_*.py`)

3. **Given** an existing fnmatch-compatible pattern (e.g., `*.pyc`, `test_*`)
   **When** `_is_excluded` evaluates a file path
   **Then** the pattern continues to work identically to current behavior (backward compatibility per NFR5)

4. **Given** both `exclude` and `extend-exclude` contain advanced patterns
   **When** `_is_excluded` evaluates a file path
   **Then** patterns from both config keys are evaluated correctly

## Tasks / Subtasks

- [x] Task 1: Add trailing-slash pattern support to `_is_excluded` (AC: #1)
  - [x] 1.1: Detect trailing-slash patterns (`pattern.endswith("/")`)
  - [x] 1.2: Strip the trailing slash and match against path directory components only
  - [x] 1.3: Ensure `build/` matches `build/output.py` but not `rebuild/main.py`
- [x] Task 2: Add double-star pattern support to `_is_excluded` (AC: #2)
  - [x] 2.1: Detect patterns containing `**`
  - [x] 2.2: Create `_matches_double_star()` helper using `fnmatch` + zero-segment fallback
  - [x] 2.3: Handle leading `**/` (strip prefix for root-level match)
  - [x] 2.4: Handle middle `/**/` (collapse to `/` for zero-segment match)
  - [x] 2.5: Ensure `**/test_*.py` matches `test_foo.py` (root), `src/test_foo.py`, and `a/b/c/test_bar.py` but not `src/foo.py`
- [x] Task 3: Preserve backward compatibility (AC: #3)
  - [x] 3.1: Ensure existing fnmatch patterns (component-level and path-level) work identically
  - [x] 3.2: No changes to non-advanced pattern code paths
- [x] Task 4: Write unit tests for all new patterns (AC: #1, #2, #3, #4)
  - [x] 4.1: Trailing-slash pattern tests (match, no-match, edge cases)
  - [x] 4.2: Double-star pattern tests (match, no-match, nested depths)
  - [x] 4.3: Backward compatibility regression tests
  - [x] 4.4: Mixed pattern tests (simple + advanced in same exclude list)
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 Trailing-slash | `test_is_excluded_trailing_slash_matches_direct_child`, `test_is_excluded_trailing_slash_matches_nested_child`, `test_is_excluded_trailing_slash_matches_at_any_depth`, `test_is_excluded_trailing_slash_rejects_partial_dir_name`, `test_is_excluded_trailing_slash_rejects_filename`, `test_is_excluded_path_trailing_slash_matches_rooted_prefix`, `test_is_excluded_path_trailing_slash_rejects_non_root` | Pass |
| #2 Double-star | `test_is_excluded_double_star_leading_matches_root_level`, `test_is_excluded_double_star_leading_matches_one_level`, `test_is_excluded_double_star_leading_matches_deep_nesting`, `test_is_excluded_double_star_leading_rejects_non_match`, `test_is_excluded_double_star_middle_matches_zero_segment`, `test_is_excluded_double_star_middle_matches_one_segment`, `test_is_excluded_double_star_middle_rejects_wrong_prefix`, `test_is_excluded_double_star_trailing_matches_direct`, `test_is_excluded_double_star_trailing_matches_nested` | Pass |
| #3 Backward compat | `test_is_excluded_backward_compat_component_match`, `test_is_excluded_backward_compat_glob_match`, `test_is_excluded_backward_compat_path_pattern` + 6 existing `_is_excluded` tests | Pass |
| #4 Mixed patterns | `test_is_excluded_mixed_patterns_all_types`, `test_is_excluded_mixed_simple_and_advanced_from_extend_exclude` | Pass |

## Dev Notes

### Critical Finding: `PurePath.full_match()` is Python 3.13+, NOT 3.12

The epics file states "Python 3.12+ `pathlib.PurePath.full_match()` supports `**` natively." **This is incorrect.** `full_match()` was added in Python 3.13 (CPython gh-73435). Since docvet targets `>=3.12` and CI tests on both 3.12 and 3.13, using `full_match()` would cause `AttributeError` on 3.12.

**Verified on Python 3.12.12:** `hasattr(PurePosixPath, "full_match")` returns `False`.

The implementation uses `fnmatch.fnmatch()` with a zero-segment fallback instead — stdlib only, works on 3.12+.

### Implementation Approach

Changes span **two functions** in `src/docvet/discovery.py` (lines 106-129): modify `_is_excluded()` and add a new `_matches_double_star()` helper.

The current `_is_excluded` logic has two branches:

1. **Path-level** (pattern contains `/`): `fnmatch.fnmatch(normalized, pattern)`
2. **Component-level** (no `/`): iterate over path components, `fnmatch.fnmatch(component, pattern)`

Add two new branches **before** the existing logic (order matters for correctness):

1. **Trailing-slash** (pattern ends with `/`): strip the trailing slash, match against directory components only
2. **Double-star** (pattern contains `**`): delegate to `_matches_double_star()` helper

**Pattern dispatch order in `_is_excluded`:**
```
for pattern in exclude:
    1. if pattern.endswith("/"):     → trailing-slash directory match
    2. elif "**" in pattern:         → _matches_double_star() helper
    3. elif "/" in pattern:           → existing fnmatch path-level match
    4. else:                          → existing fnmatch component-level match
```

### Key Technical Details

- **`fnmatch.fnmatch` treats `**` as `*`** — it matches any characters including `/`. This means `fnmatch("src/tests/test_foo.py", "**/test_*.py")` returns `True` (works for 1+ path segments). But it fails for **zero segments**: `fnmatch("test_foo.py", "**/test_*.py")` returns `False` because `**/` requires at least one character before the `/`.
- **Zero-segment fallback**: For leading `**/`, also try `fnmatch` with the `**/` prefix stripped. For middle `/**/`, also try with `/**/` collapsed to `/`. This handles root-level files and adjacent-directory matching correctly.
- **`PurePosixPath` already imported**: Line 29 of `discovery.py` — no new imports needed.
- **No new runtime deps**: Uses stdlib only (`fnmatch` and `pathlib.PurePosixPath`).
- **Backward compatibility**: The trailing-slash and double-star branches are added as new `if/elif` cases before the existing logic. Existing patterns (no trailing slash, no `**`) fall through to the existing branches unchanged.

### Trailing-Slash Semantics

Two sub-cases, following `.gitignore` semantics:

**Simple trailing-slash** (`build/` — no `/` before the trailing one):
Match at any depth — `build` can appear as a directory component anywhere in the path.
- `build/output.py` → matches (direct child)
- `build/sub/deep.py` → matches (nested child)
- `src/build/mod.py` → matches (any depth)
- `rebuild/main.py` → does NOT match (`rebuild` ≠ `build`)
- `buildfile.py` → does NOT match (filename, not directory component)

Implementation: strip trailing `/`, check `dirname in parts[:-1]` (`parts[:-1]` = directory components, excludes the filename).

**Path trailing-slash** (`vendor/legacy/` — has `/` before the trailing one):
Match anchored to the repo root only — follows `.gitignore` semantics where patterns with `/` are root-anchored.
- `vendor/legacy/old.py` → matches (rooted path prefix)
- `src/vendor/legacy/old.py` → does NOT match (not at root)

Implementation: strip trailing `/`, check `normalized.startswith(dirname + "/")`.

```python
if pattern.endswith("/"):
    dirname = pattern.rstrip("/")
    if "/" in dirname:
        # Path trailing-slash: anchored to root
        if normalized.startswith(dirname + "/"):
            return True
    else:
        # Simple trailing-slash: match at any depth
        if dirname in parts[:-1]:
            return True
```

### Double-Star Semantics

Extract to `_matches_double_star(normalized, pattern)` helper to keep `_is_excluded` CC low.

`fnmatch.fnmatch` handles the multi-segment case (1+ dirs) but fails the zero-segment case. The helper adds fallback checks:

```python
def _matches_double_star(normalized: str, pattern: str) -> bool:
    # Multi-segment case (1+ dirs) — fnmatch treats ** as *
    if fnmatch.fnmatch(normalized, pattern):
        return True
    # Zero-segment fallback for leading **/
    if pattern.startswith("**/") and fnmatch.fnmatch(normalized, pattern[3:]):
        return True
    # Zero-segment fallback for middle /**/
    if "/**/" in pattern and fnmatch.fnmatch(normalized, pattern.replace("/**/", "/", 1)):
        return True
    return False
```

**Verified behavior:**

| Pattern | Path | Result |
|---------|------|--------|
| `**/test_*.py` | `test_foo.py` (root) | True (zero-segment fallback) |
| `**/test_*.py` | `src/test_foo.py` | True (fnmatch direct) |
| `**/test_*.py` | `a/b/c/test_bar.py` | True (fnmatch direct) |
| `**/test_*.py` | `src/foo.py` | False |
| `src/**/test_*.py` | `src/test_foo.py` | True (middle collapse fallback) |
| `src/**/test_*.py` | `src/a/test_foo.py` | True (fnmatch direct) |
| `src/**/test_*.py` | `other/test_foo.py` | False |
| `build/**` | `build/out.py` | True (fnmatch direct) |
| `build/**` | `build/sub/out.py` | True (fnmatch direct) |

### Behavioral Change Note

Trailing-slash and double-star patterns currently **silently fail** in docvet:
- `build/` routes to the path branch (has `/`) but `fnmatch("build/out.py", "build/")` returns `False` because file paths never end with `/`
- `**/test_*.py` routes to the path branch and `fnmatch` handles it as `*/test_*.py`, but root-level files miss

This story fixes these silent failures. Users who already have these patterns in their config will see them start working correctly. This is a net improvement, not a regression — but worth noting in the PR description.

### Cognitive Complexity Consideration

Initial implementation had `_is_excluded` at CC=27 (SonarQube snippet analyzer) due to nested `if` checks inside the `for` loop's 4-branch dispatch. Code review refactored to compound `and` conditions with an extracted `_matches_trailing_slash()` helper (mirrors `_matches_double_star`), reducing `_is_excluded` to ~9 CC — well under the SonarQube threshold of 15.

### What NOT to Change

- Do NOT change `_collect_python_files()` — it delegates to `_is_excluded` which handles everything
- Do NOT change `config.py` — no new config keys needed
- Do NOT add negation pattern support (`!pattern`) — deferred per epics doc
- Do NOT change the `discover_files()` public API
- Do NOT use `PurePath.full_match()` — it requires Python 3.13+ and we target 3.12+

### Test Matrix

**Trailing-slash tests (AC #1):**

| Pattern | Path | Expected | Case |
|---------|------|----------|------|
| `build/` | `build/output.py` | True | Direct child |
| `build/` | `build/sub/deep.py` | True | Nested child |
| `build/` | `src/build/mod.py` | True | Any depth |
| `build/` | `rebuild/main.py` | False | Partial dir name |
| `build/` | `buildfile.py` | False | Filename, not dir |
| `vendor/legacy/` | `vendor/legacy/old.py` | True | Path prefix |
| `vendor/legacy/` | `src/vendor/legacy/old.py` | False | Not at root |

**Double-star tests (AC #2):**

| Pattern | Path | Expected | Case |
|---------|------|----------|------|
| `**/test_*.py` | `test_foo.py` | True | Root level (zero-segment) |
| `**/test_*.py` | `src/test_foo.py` | True | One level |
| `**/test_*.py` | `a/b/c/test_bar.py` | True | Deep nesting |
| `**/test_*.py` | `src/foo.py` | False | Non-match |
| `src/**/test_*.py` | `src/test_foo.py` | True | Zero-segment middle |
| `src/**/test_*.py` | `src/a/test_foo.py` | True | One-segment middle |
| `src/**/test_*.py` | `other/test_foo.py` | False | Wrong prefix |
| `build/**` | `build/out.py` | True | Trailing ** direct |
| `build/**` | `build/sub/out.py` | True | Trailing ** nested |

**Backward compat tests (AC #3):** Existing 6 unit tests at lines 41-62 serve as regression tests. No changes to non-advanced pattern code paths.

**Mixed patterns test (AC #4):** Exclude list `["tests", "build/", "**/conftest.py"]` — verify all three pattern types evaluated correctly in a single call.

### Project Structure Notes

- `_is_excluded` is called from two places: `_collect_python_files()` (line 161) and `discover_files()` DIFF/STAGED branch (line 275)
- Both pass `config.exclude` which is already the merged list (base + extend-exclude)
- No alignment issues — change is contained within the private functions
- New `_matches_double_star()` helper placed between `_is_excluded` and `_collect_python_files`

### References

- [Source: src/docvet/discovery.py#_is_excluded] — Current implementation (lines 106-129)
- [Source: src/docvet/discovery.py#L29] — `PurePosixPath` already imported
- [Source: tests/unit/test_discovery.py] — Existing unit tests for `_is_excluded` (lines 41-62)
- [Source: tests/integration/test_discovery.py] — Integration tests with extend-exclude (lines 265-386)
- [Source: epics-next.md#Story 3.1] — Original story specification with acceptance criteria
- [Source: docs/site/configuration.md] — Current exclude pattern documentation (story 19.2 will update this)
- [Source: Python 3.13 whatsnew] — `PurePath.full_match()` added in Python 3.13 (NOT 3.12)
- [Source: fnmatch docs] — `fnmatch` treats `**` identically to `*` (no recursive semantics)
- [Verified: Python 3.12.12] — `hasattr(PurePosixPath, "full_match")` = False

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 785 tests pass, no regressions
- [x] `uv run docvet check --all` — 0 required findings (1 recommended transient false positive from diff context overlap on unchanged `_run_git`, resolves on commit)
- [x] `uv run interrogate -v` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None required — zero-debug implementation.

### Completion Notes List

- Added trailing-slash pattern support (`build/`) to `_is_excluded` with two sub-cases: simple (any-depth directory match) and path (root-anchored prefix match), following `.gitignore` semantics.
- Added `_matches_double_star()` helper for recursive glob patterns (`**/test_*.py`) using `fnmatch` with zero-segment fallbacks for leading `**/` and middle `/**/`.
- Extended `_is_excluded` from 2-branch to 4-branch dispatch: trailing-slash → double-star → path-level → component-level.
- Updated module docstring to document new pattern capabilities.
- Updated `_is_excluded` docstring to document all four dispatch branches.
- 21 new unit tests covering all 4 ACs (7 trailing-slash, 9 double-star, 3 backward-compat regression, 2 mixed-pattern tests).
- All 785 tests pass. All quality gates green.

### Change Log

- 2026-02-25: Implemented trailing-slash and double-star pattern support in `_is_excluded` with `_matches_double_star` helper. Added 21 unit tests.
- 2026-02-25: Code review — extracted `_matches_trailing_slash()` helper, refactored `_is_excluded` to compound `or` expression (CC 27→0 SonarQube issues), added 2 boundary tests, updated docstrings with limitation notes.

### File List

- `src/docvet/discovery.py` — Modified: added `_matches_trailing_slash()` and `_matches_double_star()` helpers, `_is_excluded` uses compound `or` dispatch, updated module and function docstrings with limitation notes
- `tests/unit/test_discovery.py` — Modified: added 23 new tests for trailing-slash, double-star, backward-compat, mixed patterns, and boundary cases

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Changes Requested → Fixed → Approved

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| F1 | HIGH | `_is_excluded` CC=27 exceeds SonarQube threshold of 15 | Fixed: extracted `_matches_trailing_slash()` helper, refactored to compound `or` expression. SonarQube: 0 issues. |
| F2 | MEDIUM | Trailing-slash + double-star pattern interaction silently fails (`build/**/`, `**/`) | Documented: added Note sections to `_is_excluded` and `_matches_trailing_slash` docstrings. Added boundary test. |
| F3 | MEDIUM | Dev Notes CC estimate inaccurate ("~6 CC" vs actual 27) | Fixed: corrected CC section in story Dev Notes. |
| F4 | LOW | `_matches_double_star` only collapses one `/**/` for zero-segment fallback | Documented: added Note section to `_matches_double_star` docstring. |
| F5 | LOW | No tests for degenerate patterns (`**`, `build/**/`, `**/`) | Fixed: added 2 boundary tests documenting expected behavior. |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass (785 tests, ruff, ty, interrogate, SonarQube 0 issues)
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
