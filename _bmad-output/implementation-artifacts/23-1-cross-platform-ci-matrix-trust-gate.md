# Story 23.1: Cross-Platform CI Matrix (Trust Gate)

Status: review
Branch: `feat/ci-23-1-cross-platform-ci-matrix`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want all tests to pass on Ubuntu, macOS, and Windows CI runners,
so that contributors on any platform can trust docvet works correctly.

## Acceptance Criteria

1. **Given** the current GitHub Actions CI workflow runs on `ubuntu-latest` only, **when** `macos-latest` and `windows-latest` are added to the CI matrix, **then** the full test suite runs on all three platforms on every push and PR.

2. **Given** tests contain path assertions with forward slashes, **when** tests run on Windows, **then** path separators are handled correctly so all assertions pass (NFR74).

3. **Given** freshness diff parsing operates on git diff output, **when** the repository uses CRLF line endings (Windows default), **then** diff parsing produces identical results to LF — no false positives from line ending differences (NFR75).

4. **Given** the CI matrix is green on all three platforms, **when** a contributor checks CI status, **then** all tests pass on Ubuntu, macOS, and Windows (NFR73).

5. **Given** docvet runs on Windows, **when** findings are reported, **then** file paths in output use forward slashes (e.g., `src/app.py:10:`) for consistent cross-platform output.

## Tasks / Subtasks

- [x] Task 1: Expand CI workflow matrix (AC: #1, #4)
  - [x] 1.1 Edit `.github/workflows/ci.yml` — add `os: [ubuntu-latest, macos-latest, windows-latest]` to `test` job matrix
  - [x] 1.2 Update `cache-suffix` key in uv setup to include OS: `${{ matrix.os }}-py${{ matrix.python-version }}`
  - [x] 1.3 Conditional Codecov upload: only on ubuntu + Python 3.12 (not all matrix entries)
  - [x] 1.4 Keep `lint`, `type-check`, `interrogate`, and `docvet` jobs Ubuntu-only (platform-agnostic tools)
- [x] Task 2: Push and identify actual failures (AC: #1)
  - [x] 2.1 Push branch with CI matrix change only
  - [x] 2.2 Collect actual failures from macOS and Windows runners
  - [x] 2.3 Categorize failures: path separator issues vs. line ending issues vs. other
- [x] Task 3: Normalize file paths in `Finding` dataclass (AC: #2, #5)
  - [x] 3.1 Add `self.file = self.file.replace("\\", "/")` to `Finding.__post_init__` in `src/docvet/checks/_finding.py` — one normalization point for all findings across all checks
  - [x] 3.2 Verify `checks/coverage.py` already uses `.as_posix()` (line 91/96) — confirmed no change needed
  - [x] 3.3 Verify `discovery.py` already normalizes with `replace("\\", "/")` and `.as_posix()` — confirmed no change needed
- [x] Task 4: Add `.gitattributes` for line ending normalization (AC: #3)
  - [x] 4.1 Create `.gitattributes` at repo root with `* text=auto eol=lf` to force LF in the repo
  - [x] 4.2 Add `*.py text eol=lf` explicit rule for Python files
- [x] Task 5: Fix integration test git fixture for cross-platform (AC: #3)
  - [x] 5.1 In `tests/integration/conftest.py`, add `git config core.autocrlf false` to the `git_repo` fixture
- [x] Task 6: Fix any remaining test failures identified in Task 2 (AC: #2, #4)
  - [x] 6.1 Fix actual failures from CI — do not pre-fix hypothetical problems
  - [x] 6.2 Run full test suite locally to confirm all pass on Linux before each push
- [x] Task 7: Verify CI passes on all three platforms (AC: #4)
  - [x] 7.1 Push final fixes and verify all 6 matrix entries (3 OS x 2 Python) pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | CI run 22499623587 — all 6 matrix entries pass | PASS |
| #2 | `test_finding_normalizes_backslash_paths_to_forward_slashes`, `test_finding_preserves_forward_slash_paths`, CI Windows tests pass | PASS |
| #3 | `.gitattributes` enforces LF, `core.autocrlf false` in git fixture, CI Windows tests pass | PASS |
| #4 | CI run 22499623587 — ubuntu/macos/windows x 3.12/3.13 all green | PASS |
| #5 | `test_finding_normalizes_backslash_paths_to_forward_slashes` verifies backslash→forward slash normalization in Finding | PASS |

## Dev Notes

### Strategy: Normalize at the Finding Boundary

The recommended approach is to **normalize file paths in `Finding.__post_init__`** — one normalization point for all output across all checks. Add `self.file = self.file.replace("\\", "/")` to the dataclass.

Why this placement:
1. **Single normalization point** — every Finding produced by every check gets normalized, no scattered `replace()` calls in `cli.py` or individual check modules
2. **Consistent user-facing output** — users expect `src/app.py:10:` not `src\app.py:10:` regardless of platform
3. **Future-proof** — any new check module automatically gets correct path output
4. **Follows existing patterns** — `discovery.py` already normalizes with `replace("\\", "/")` and `.as_posix()`

### Workflow: CI-First, Fix What Breaks

Do **not** pre-fix hypothetical problems. The workflow is:
1. Push CI matrix change first (Task 1-2)
2. Observe actual failures on macOS/Windows runners
3. Apply `Finding.__post_init__` normalization (Task 3) — this will fix the majority
4. Fix remaining failures based on CI evidence (Task 6)

This is an **iterative push-fix-push story** — the dev agent cannot test Windows locally (Linux workstation). Expect 2-3 CI round-trips.

### Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Line ending parsing | LOW | Already safe — all parsing uses `.splitlines()`, all `subprocess.run` uses `text=True` |
| `_is_excluded` paths | LOW | Already normalizes backslashes via `replace("\\", "/")` |
| `_collect_python_files` | LOW | Already uses `.as_posix()` for forward slashes |
| `str(file_path)` in Finding.file | HIGH | **Fix:** `Finding.__post_init__` normalizes backslashes — one point, all checks |
| Integration test autocrlf | MEDIUM | **Fix:** Add `core.autocrlf false` to git_repo fixture |
| Test assertion failures | UNKNOWN | **Approach:** CI-first — push matrix, observe actual failures, fix with evidence |

### CRLF / Line Ending Safety (Verified by Architecture — No Dedicated Test Needed)

The codebase was designed cross-platform from the start:
- All git output parsing uses `.splitlines()` (not `.split("\n")`) — handles `\r\n`, `\r`, and `\n`
- All `subprocess.run` calls use `text=True` — enables universal newline mode
- Documented in architecture: "Always use `.splitlines()`, not `.split("\n")` — handles `\r\n` on Windows"
- Documented in Story 5.1 dev notes: "Uses `.splitlines()` NOT `.split("\n")` — handles Windows `\r\n`"

NFR75 (no CRLF false positives) is satisfied by architectural guarantee. No dedicated CRLF integration test needed — if CI surfaces a real CRLF issue, fix it then.

### CI Matrix Design

Only the `test` job gets the OS matrix. The other jobs are platform-agnostic:
- `lint` (ruff) — pure Python analysis, no OS-dependent behavior
- `type-check` (ty) — pure Python analysis
- `interrogate` — pure Python analysis
- `docvet` — runs via GitHub Action, platform-agnostic

The `test` matrix becomes 3 OS x 2 Python = 6 entries. Test suite runs in ~1s, so 3x runner cost is negligible.

### What NOT to Change

- Do not add OS matrix to `lint`, `type-check`, `interrogate`, or `docvet` jobs
- Do not change any `.splitlines()` calls — they already handle CRLF
- Do not change `_is_excluded` normalization — it already handles backslashes
- Do not change `_collect_python_files` — it already uses `.as_posix()`
- Do not add `os.sep` usage — the project standardizes on forward slashes everywhere
- Do not add CRLF-specific integration tests — verified by architecture
- Do not pre-fix hypothetical test failures — push CI first, fix what actually breaks
- Do not add `@pytest.mark.skipif(sys.platform == "win32")` markers — no platform-specific skip markers expected; all tests should pass everywhere

### Key Source Files

| File | Lines | Relevance |
|------|-------|-----------|
| `.github/workflows/ci.yml` | Full | CI matrix expansion (Task 1) |
| `src/docvet/reporting.py` | `Finding` dataclass | Add `__post_init__` path normalization (Task 3) |
| `src/docvet/discovery.py` | 209, 251 | Already normalized — reference pattern for `replace("\\", "/")` |
| `src/docvet/checks/coverage.py` | 91, 96 | Already uses `.as_posix()` — verify only |
| `tests/integration/conftest.py` | git_repo fixture | Add `core.autocrlf false` (Task 5) |
| `.gitattributes` (new) | Full | Line ending normalization (Task 4) |

### Project Structure Notes

- Alignment with unified project structure: all changes stay within existing module boundaries
- No new modules or packages created
- `.gitattributes` is a standard git config file at repo root
- CI workflow changes are additive (matrix expansion, no structural changes)

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 23, Story 23.1]
- [Source: GitHub Issue #101 — chore: add macOS and Windows CI testing]
- [Source: _bmad-output/planning-artifacts/architecture.md — ".splitlines() not .split("\n")" convention]
- [Source: _bmad-output/implementation-artifacts/5-1-blame-timestamp-parser.md — Windows CRLF handling note]
- [Source: src/docvet/discovery.py:209 — existing backslash normalization pattern]

### Documentation Impact

- Pages: README.md
- Nature of update: Add platform badges or combined matrix badge confirming macOS/Windows support

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 891 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- CI Run 1 (22499434647): Windows failed at `uv sync --dev` — PowerShell doesn't support inline env vars (`UV_PYTHON=3.12 cmd`)
- CI Run 2 (22499475965): Windows `uv sync` fixed, 12 test failures on Windows — path separator assertion mismatches
- CI Run 3 (22499623587): All 10 jobs pass (6 test matrix + 4 platform-agnostic)

### Completion Notes List

- Added macOS and Windows to CI test matrix (3 OS x 2 Python = 6 entries)
- Normalized backslash paths in `Finding.__post_init__` using `object.__setattr__` (frozen dataclass)
- Fixed Windows CI by using `env:` directive instead of inline env vars for UV_PYTHON
- Fixed 12 test assertions to handle cross-platform path separators
- Added `.gitattributes` for LF line ending enforcement
- Added `core.autocrlf false` to integration test git fixture
- Documentation Impact (README badges) deferred — no badge changes needed; CI matrix is the trust gate itself

### Change Log

- 2026-02-27: Implemented cross-platform CI matrix with path normalization. 3 CI iterations to resolve Windows-specific failures.

### File List

- `.github/workflows/ci.yml` (modified) — OS matrix + env directive for UV_PYTHON
- `.gitattributes` (new) — LF line ending enforcement
- `src/docvet/checks/_finding.py` (modified) — backslash path normalization in `__post_init__`
- `tests/integration/conftest.py` (modified) — `core.autocrlf false` in git fixture
- `tests/unit/checks/test_finding.py` (modified) — path normalization tests
- `tests/unit/checks/test_coverage.py` (modified) — cross-platform path assertions
- `tests/unit/checks/test_griffe_compat.py` (modified) — cross-platform path assertions
- `tests/unit/test_cli.py` (modified) — cross-platform git command assertions

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
