# Story 19.2: Integration Tests and Documentation

Status: review
Branch: `feat/discovery-19-2-integration-tests-and-docs`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer configuring docvet**,
I want the supported exclude pattern syntax documented with examples,
so that I know which patterns are available and can configure them confidently.

## Acceptance Criteria

1. **Given** a temporary git repo with files in nested directories
   **When** an integration test runs docvet with a trailing-slash exclude pattern (e.g., `build/`)
   **Then** files under that directory are excluded and files elsewhere are checked

2. **Given** a temporary git repo with files matching a `**` glob pattern
   **When** an integration test runs docvet with a double-star exclude pattern (e.g., `**/test_*.py`)
   **Then** matching files across all directory depths are excluded

3. **Given** a temporary git repo with a mix of simple and advanced patterns in config
   **When** an integration test runs docvet
   **Then** all pattern types work together correctly (simple fnmatch, trailing-slash, double-star)

4. **Given** the configuration documentation at `docs/site/configuration.md`
   **When** a developer reads the exclude pattern section
   **Then** it documents the supported pattern subset: simple globs, trailing-slash directory patterns, and `**` cross-directory globs with examples for each (per NFR4)

## Tasks / Subtasks

- [x] Task 1: Add trailing-slash integration tests (AC: #1)
  - [x] 1.1: ALL mode — `build/` excludes `build/output.py` but not `rebuild/main.py` or `app.py`
  - [x] 1.2: ALL mode — path trailing-slash `vendor/legacy/` excludes rooted but not nested occurrences
  - [x] 1.3: DIFF mode — trailing-slash pattern excludes changed files under matched directory
  - [x] 1.4: STAGED mode — trailing-slash pattern excludes staged files under matched directory
- [x] Task 2: Add double-star integration tests (AC: #2)
  - [x] 2.1: ALL mode — `**/test_*.py` excludes test files at all depths including root
  - [x] 2.2: ALL mode — middle `src/**/generated.py` excludes at variable depth
  - [x] 2.3: DIFF mode — double-star pattern excludes changed files matching pattern
  - [x] 2.4: STAGED mode — double-star pattern excludes staged files matching pattern
- [x] Task 3: Add mixed-pattern integration tests (AC: #3)
  - [x] 3.1: ALL mode — combine simple (`scripts`), trailing-slash (`build/`), and double-star (`**/conftest.py`) in one exclude list
  - [x] 3.2: Verify non-excluded files are still discovered alongside excluded ones
- [x] Task 4: Update configuration documentation (AC: #4)
  - [x] 4.1: Replace stale matching-rules sentence in `extend-exclude` paragraph with forward-reference to new section; add "Exclude Pattern Syntax" subsection to `docs/site/configuration.md`
  - [x] 4.2: Document three pattern types with examples: simple globs, trailing-slash, double-star
  - [x] 4.3: Add a pattern reference table with examples and behavior descriptions
  - [x] 4.4: Note limitations (no negation, no combined trailing-slash + double-star)
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_all_mode_trailing_slash_excludes_directory`, `test_all_mode_path_trailing_slash_excludes_rooted_only`, `test_diff_mode_trailing_slash_excludes_changed_files`, `test_staged_mode_trailing_slash_excludes_staged_files` | PASS |
| AC2 | `test_all_mode_double_star_excludes_test_files_at_all_depths`, `test_all_mode_middle_double_star_excludes_at_variable_depth`, `test_diff_mode_double_star_excludes_changed_files`, `test_staged_mode_double_star_excludes_staged_files` | PASS |
| AC3 | `test_all_mode_mixed_patterns_exclude_correctly`, `test_all_mode_mixed_patterns_non_excluded_files_discovered` | PASS |
| AC4 | Manual: "Exclude Pattern Syntax" subsection added to `docs/site/configuration.md` with pattern reference table, TOML examples, and limitations admonition | PASS |

## Dev Notes

### Implementation Context from Story 19.1

Story 19.1 implemented the pattern logic in `src/docvet/discovery.py` with **23 unit tests** covering all four pattern dispatch branches. This story adds **integration tests** (real git repos, real `discover_files()` calls) and **documentation**.

The implementation added three functions:
- `_matches_trailing_slash(normalized, parts, pattern)` — trailing-slash directory matching
- `_matches_double_star(normalized, pattern)` — recursive glob matching with zero-segment fallbacks
- Updated `_is_excluded()` — 4-branch compound `or` dispatch: trailing-slash → double-star → path-level → component-level

### Integration Test Patterns

**Existing infrastructure** (reuse, do NOT recreate):
- `git_repo` fixture in `tests/integration/conftest.py` — creates tmp git repo with user config
- `_git()` helper in `tests/integration/test_discovery.py:20-21` — runs git commands
- `_make_config()` helper in `tests/integration/test_discovery.py:24-33` — creates `DocvetConfig`
- Existing extend-exclude integration tests (lines 265-386) — model for new tests

**Test placement**: Add new tests to `tests/integration/test_discovery.py` in a new section after the extend-exclude tests (after line 386).

**Test structure**: Each test should:
1. Create directory structure and files in `git_repo`
2. Commit all files via `_git(["add", "."], ...)` + `_git(["commit", "-m", "init"], ...)`
3. For DIFF/STAGED tests: modify files and optionally stage them
4. Create config with the pattern under test in `exclude`
5. Call `discover_files(config, mode)` and assert correct inclusion/exclusion

**Section headers for new tests:**
```python
# ---------------------------------------------------------------------------
# Trailing-slash pattern integration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Double-star pattern integration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Mixed pattern integration (simple + trailing-slash + double-star)
# ---------------------------------------------------------------------------
```

### Documentation Update

**File**: `docs/site/configuration.md`

**What to add**: A new subsection "Exclude Pattern Syntax" between the `extend-exclude` section and the "Example" section.

**Stale sentence to update**: The `extend-exclude` paragraph currently ends with *"Patterns follow the same matching rules as `exclude` — patterns without `/` match against individual path components, patterns with `/` match the full relative path."* This sentence is incomplete now that trailing-slash and double-star patterns exist. **Replace it** with a forward-reference: *"See Exclude Pattern Syntax below for the full matching rules."* This prevents developers reading linearly from hitting stale information before reaching the new section.

**Content structure:**
1. Introductory paragraph explaining the four pattern types
2. Pattern reference table with columns: Pattern, Example, Matches, Does Not Match
3. Examples in TOML for each pattern type
4. Limitations note (no negation patterns, no combined trailing-slash + double-star) — use `!!! warning` admonition consistent with existing style

**Pattern types to document:**

| Type | Pattern | Example | Behavior |
|------|---------|---------|----------|
| Simple glob | `tests`, `*.pyc` | Matches any path component |
| Path-level | `scripts/gen_*.py` | Matches full relative path (fnmatch) |
| Trailing-slash | `build/` | Matches directory at any depth; `vendor/legacy/` is root-anchored |
| Double-star | `**/test_*.py` | Matches across any directory depth including root |

**Admonition style**: Use mkdocs-material `!!! tip` or `!!! info` for the pattern reference, consistent with the existing `!!! warning` and `!!! info` in the file.

### What NOT to Change

- Do NOT modify `src/docvet/discovery.py` — pattern logic is complete from story 19.1
- Do NOT modify `tests/unit/test_discovery.py` — unit tests are complete from story 19.1
- Do NOT modify `tests/integration/conftest.py` — fixture is sufficient
- Do NOT add negation pattern support or documentation — deferred per epics doc
- Do NOT modify `_make_config()` helper — it already accepts `exclude` parameter

### Key Technical Details

- Integration tests use `DiscoveryMode.ALL` as the primary mode (most straightforward — commit files, call discover, assert). DIFF and STAGED modes need extra setup (commit → modify → optionally stage).
- The `_make_config()` helper defaults to `exclude=["tests", "scripts"]` — override with explicit `exclude` parameter for pattern-specific tests.
- `git ls-files` is used by `_walk_all()` in ALL mode — files MUST be committed (or at least added/tracked) to appear in results.
- For DIFF mode tests: files must be committed first, then modified in the working tree.
- For STAGED mode tests: files must be committed first, then modified and staged.
- Root-level files (e.g., `test_foo.py` at repo root) require special attention for `**/` patterns — the zero-segment fallback in `_matches_double_star` handles this.

### Previous Story Learnings (19.1)

- `PurePath.full_match()` is Python 3.13+ NOT 3.12 — the implementation uses `fnmatch` with fallbacks instead. Do NOT reference `full_match()` anywhere.
- `fnmatch.fnmatch` treats `**` as `*` — it matches any characters including `/`. The zero-segment fallback is the key innovation.
- The SonarQube CC refactoring extracted helpers to keep `_is_excluded` CC low. The compound `or` expression in `_is_excluded` is intentional — do not restructure.
- Patterns combining trailing-slash with double-star (e.g., `build/**/`) route to trailing-slash branch and silently fail. Document this limitation.

### Git Intelligence

Recent commits show the pattern:
- `3696e6a feat(discovery): add trailing-slash and double-star pattern support (#137)` — story 19.1 merged
- `6711525 test(config): add extend-exclude integration tests and docs (#133)` — story 16.2, similar scope to this story (integration tests + docs for a config feature)

Story 16.2 (`16-2-integration-verification-and-documentation.md`) is the closest precedent — it added integration tests and configuration docs for extend-exclude. The same file locations and patterns apply here.

### Project Structure Notes

- `tests/integration/test_discovery.py` — append new test sections (do not interleave with existing tests)
- `docs/site/configuration.md` — add pattern syntax section (keep existing content intact)
- No new files needed
- No new modules or imports needed in test file (already imports `discover_files`, `DiscoveryMode`, `DocvetConfig`)

### References

- [Source: src/docvet/discovery.py#_is_excluded] — 4-branch pattern dispatch (lines 182-222)
- [Source: src/docvet/discovery.py#_matches_trailing_slash] — trailing-slash matcher (lines 121-146)
- [Source: src/docvet/discovery.py#_matches_double_star] — double-star matcher (lines 149-179)
- [Source: tests/integration/test_discovery.py] — existing integration tests (lines 1-386), model for new tests
- [Source: tests/integration/conftest.py] — `git_repo` fixture
- [Source: docs/site/configuration.md] — current exclude/extend-exclude docs (lines 1-147)
- [Source: epics-next.md#Story 3.2] — original story specification (lines 202-224)
- [Source: 19-1-trailing-slash-and-double-star-pattern-support.md] — previous story with implementation details and dev notes
- [Source: 16-2-integration-verification-and-documentation.md] — precedent story (integration tests + docs for config feature)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 795 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No issues encountered.

### Completion Notes List

- Added 10 integration tests across 3 new sections (trailing-slash, double-star, mixed patterns) to `tests/integration/test_discovery.py`
- Trailing-slash tests cover ALL, DIFF, STAGED modes plus root-anchored path patterns
- Double-star tests cover leading `**/` (root + nested), middle `src/**/` (variable depth), DIFF, and STAGED modes
- Mixed-pattern tests verify all three pattern types work together and non-excluded files remain discoverable
- Replaced stale matching-rules sentence in `extend-exclude` docs with forward-reference to new section
- Added comprehensive "Exclude Pattern Syntax" subsection with 6-row pattern reference table, prose explanations for each type, TOML example admonition, and limitations warning
- All 795 tests pass (10 new + 785 existing), all quality gates green

### Change Log

- 2026-02-26: Added integration tests for trailing-slash, double-star, and mixed exclude patterns; added Exclude Pattern Syntax documentation section

### File List

- `tests/integration/test_discovery.py` — modified (added 10 integration tests in 3 new sections)
- `docs/site/configuration.md` — modified (replaced stale sentence, added Exclude Pattern Syntax subsection)

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
