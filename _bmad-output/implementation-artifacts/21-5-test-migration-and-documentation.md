# Story 21.5: Test Migration & Documentation

Status: done
Branch: `feat/docs-21-5-test-migration-and-documentation`

## Story

As a docvet contributor,
I want all tests updated for the new output format and docs reflecting the three-tier model,
so that the test suite is green, docs are accurate, and future contributors understand the design.

## Acceptance Criteria

1. **Integration test updates (pre-verified)** — Stories 21.1-21.4 already migrated all test assertions. Zero occurrences of `Completed in` or `No findings.` remain in test files. This AC is satisfied — no migration work needed. Remaining work: add missing edge-case tests per AC5.
2. **CLI Reference docs** — Given `docs/site/cli-reference.md`, when updated, then documents three tiers (quiet/default/verbose) with examples, documents `-q`/`--quiet` and `--verbose` dual-registration, and example output uses `Vetted` format.
3. **CI Integration docs** — Given `docs/site/ci-integration.md`, when reviewed, then existing examples are verified accurate (no stale output). Add a `-q` tip for scripted/CI contexts where only exit code matters.
4. **Getting Started docs** — Given `docs/site/index.md`, when updated, then quickstart example matches new default format with Vetted summary line.
5. **Edge case testing** — When following scenarios tested with representative subcommands (enrichment + griffe), then correct output for each: `freshness --quiet` suppresses summary, `griffe --quiet` suppresses summary, subcommand `--format markdown` keeps summary on stderr, subcommand `--output file.md` keeps summary on stderr, `check --staged` with zero files exits cleanly.
6. **Check page docs** — Given `docs/site/checks/{enrichment,freshness,coverage,griffe}.md`, when updated, then Usage sections mention `--verbose` and `--quiet` flags.
7. **Full test pass** — When `uv run pytest` executed, then all tests pass with zero failures, and `docvet check --all` on docvet shows new summary format.
8. **Docs build** — When `mkdocs build --strict` executed, then build succeeds with zero warnings. Requires `uv sync --extra docs` for mkdocs dependencies.

## Tasks / Subtasks

- [x] Task 1: Update CLI Reference documentation (AC: #2)
  - [x] 1.1 Add `-q`/`--quiet` to Global Options table in `docs/site/cli-reference.md`
  - [x] 1.2 Fix the "Wrong" example that labels `docvet check --verbose --all` as incorrect (it's now valid via dual-registration)
  - [x] 1.3 Add "Output Tiers" section documenting quiet/default/verbose behavior with examples
  - [x] 1.4 Add Vetted summary line example showing actual output format
- [x] Task 2: Update Getting Started documentation (AC: #4)
  - [x] 2.1 Update output example block in `docs/site/index.md` (lines ~113-119) to show Vetted summary on stderr alongside findings on stdout
- [x] Task 3: Update CI Integration documentation (AC: #3)
  - [x] 3.1 Verify `docs/site/ci-integration.md` — existing YAML examples are config-only (no terminal output to update). Already accurate.
  - [x] 3.2 Add `-q` tip for scripted/CI contexts where only exit code matters
- [x] Task 4: Add missing edge-case tests (AC: #1, #5)
  - [x] 4.1 Add `freshness --quiet` suppresses Vetted summary test
  - [x] 4.2 Add `griffe --quiet` suppresses Vetted summary test
  - [x] 4.3 Add subcommand `--format markdown` → summary on stderr tests (enrichment + griffe — two representative subcommands, not all four)
  - [x] 4.4 Add subcommand `--output file.md` → summary on stderr tests (enrichment + griffe)
  - [x] 4.5 Add `check --staged` with zero files → clean exit test
- [x] Task 5: Update check page docs (AC: #6)
  - [x] 5.1 Add `--verbose` and `--quiet` to Usage section in `docs/site/checks/enrichment.md`
  - [x] 5.2 Add `--verbose` and `--quiet` to Usage section in `docs/site/checks/freshness.md`
  - [x] 5.3 Add `--verbose` and `--quiet` to Usage section in `docs/site/checks/coverage.md`
  - [x] 5.4 Add `--verbose` and `--quiet` to Usage section in `docs/site/checks/griffe.md`
- [x] Task 6: Verify all quality gates pass (AC: #7, #8)
  - [x] 6.1 `uv run pytest` — 879 passed
  - [x] 6.2 `uv run ruff check . && uv run ruff format --check .` — all passed
  - [x] 6.3 `uv run ty check` — all passed
  - [x] 6.4 `uv run docvet check --all` — zero findings
  - [x] 6.5 `uv run interrogate -v` — 100.0%
  - [x] 6.6 `uv sync --extra docs && mkdocs build --strict` — built in 1.79s, zero warnings

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Pre-verified: zero `Completed in` or `No findings.` in tests/. Stories 21.1-21.4 migrated all assertions. No work needed. | Done |
| AC2 | Manual: cli-reference.md has Output Tiers section, quiet flag in Global Options, dual-registration examples, Vetted output examples | Done |
| AC3 | Manual: ci-integration.md verified accurate + `-q` tip added | Done |
| AC4 | Manual: index.md output example updated with Vetted summary line | Done |
| AC5 | test_freshness_subcommand_quiet_suppresses_summary, test_griffe_subcommand_quiet_suppresses_summary, test_enrichment_summary_on_stderr_with_format_markdown, test_griffe_summary_on_stderr_with_format_markdown, test_enrichment_summary_on_stderr_with_output_flag, test_griffe_summary_on_stderr_with_output_flag, test_check_staged_zero_files_exits_cleanly | Done |
| AC6 | Manual: `--verbose`/`--quiet` added to Usage sections in all 4 check pages | Done |
| AC7 | 879 tests passed, `docvet check --all` zero findings | Done |
| AC8 | `mkdocs build --strict` built in 1.79s, zero warnings | Done |

## Dev Notes

### Scope Clarification

This story is **primarily documentation + edge-case tests**. No source code changes to `cli.py`, `config.py`, or `reporting.py` are expected. Stories 21.1-21.4 already implemented the full three-tier output model.

### What's Already Done (No Migration Needed)

The previous stories (21.1-21.4) already cleaned up stale test assertions during implementation:
- `_non_timing_lines` helper in `test_cli.py` filters `"Vetted "` lines (old `"Completed in"` branch removed in 21.4)
- `SUMMARY_LINE_RE` regex in `test_cli_timing.py` matches `Vetted N files [...]` format (consolidated from `SUBCOMMAND_TOTAL_RE` in 21.4)
- Zero occurrences of `"Completed in"` or standalone `"No findings."` remain in any test file

### Documentation Gaps to Fix

**`docs/site/cli-reference.md`:**
- Global Options table (lines ~11-18) is missing `-q`/`--quiet` entirely
- Lines ~22-28 label `docvet check --verbose --all` as "Wrong" — this is now valid via dual-registration
- No "Output Tiers" section explaining quiet/default/verbose behavior
- No example of the Vetted summary line format

**`docs/site/index.md` (Getting Started):**
- Output example block (lines ~113-119) only shows finding lines + count — missing the Vetted summary line
- Should clarify stream separation: findings on stdout, summary on stderr

**`docs/site/ci-integration.md`:**
- Already accurate — YAML config examples only, no terminal output to update (verified by research)
- Overlap warning tip at line ~129-131 already reflects Story 21.2's silent resolution
- Only addition needed: `-q` tip for scripted/CI contexts where only exit code matters

**`docs/site/checks/{enrichment,freshness,coverage,griffe}.md`:**
- All four check pages have correct output format (no stale `Completed in`)
- BUT none mention `--verbose` or `--quiet` in their Usage sections
- Add a brief mention of both flags to each page's Usage section

### Edge-Case Test Gaps

Existing coverage is strong (Stories 21.1-21.4 added 31+ new tests). Remaining gaps use **two representative subcommands** (enrichment + griffe) to prove the pattern without boilerplate:

| Missing Test | File | Pattern |
|---|---|---|
| `freshness --quiet` suppresses summary | `test_cli.py` | Same pattern as `test_enrichment_subcommand_quiet` |
| `griffe --quiet` suppresses summary | `test_cli.py` | Same pattern as `test_enrichment_subcommand_quiet` |
| `enrichment --format markdown` → summary on stderr | `test_cli.py` | Extend `TestSummaryAlwaysOnStderr` pattern from `test_cli_timing.py` |
| `griffe --format markdown` → summary on stderr | `test_cli.py` | Same (griffe has different code path via `_run_griffe`) |
| `enrichment --output file.md` → summary on stderr | `test_cli.py` | Same extension |
| `griffe --output file.md` → summary on stderr | `test_cli.py` | Same extension |
| `check --staged` with zero files → clean exit | `test_cli.py` | Similar to existing zero-files test at line ~393 |

**Why enrichment + griffe, not all four?** Enrichment uses the standard `_output_and_exit` path. Griffe has a unique code path through `_run_griffe`. If both pass, freshness and coverage (which share the standard path) are covered by induction. This avoids 4x boilerplate tests that add noise without catching real bugs.

### Testing Patterns to Follow

Use the established patterns from Stories 21.3 and 21.4:

**Quiet suppression test pattern** (from `test_cli.py:2115`):
```python
def test_<subcommand>_subcommand_quiet_suppresses_summary(mock_config, ...):
    """<Subcommand> -q suppresses Vetted summary."""
    result = runner.invoke(app, ["<subcommand>", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output  # stdout
    # stderr check via capsys or mock
```

**Summary-on-stderr test pattern** (from `test_cli_timing.py:310`):
```python
def test_summary_on_stderr_with_format_markdown(mock_config, ...):
    result = runner.invoke(app, ["<subcommand>", "--all", "--format", "markdown"])
    assert "Vetted" not in result.output  # not in stdout
    # Verify stderr has summary line
```

### Stream Separation Architecture (Invariant)

This is a core design decision that must be preserved in all tests and docs:
- **stdout**: Findings only (parseable by scripts/tools)
- **stderr**: Summary line, verbose metadata, config warnings, progress bar

### Key Code References

- `src/docvet/reporting.py:130-179` — `format_summary()` function
- `src/docvet/cli.py` — all five subcommands call `format_summary` gated by `if not quiet`
- `tests/unit/test_cli.py:2027-2118` — Story 21.4 subcommand tests (follow this pattern)
- `tests/unit/test_cli_timing.py:275-320` — Summary-on-stderr tests (follow this pattern)
- `tests/unit/test_cli.py:1844-1870` — Story 21.3 quiet/verbose tests (follow this pattern)

### Three-Tier Output Model (Document This)

| Tier | Trigger | stderr | stdout |
|------|---------|--------|--------|
| Quiet | `-q` / `--quiet` | Nothing | Findings only |
| Default | (no flags) | Summary line | Findings only |
| Verbose | `--verbose` | File count + per-check timing + summary | Findings only |

Summary line format: `Vetted {N} files [{checks}] — {detail}. ({elapsed}s)`

### Project Structure Notes

- All changes are in `docs/site/` (documentation) and `tests/unit/` (edge-case tests)
- No new source files created
- Alignment with existing doc structure in `docs/site/` and test patterns in `tests/unit/`
- No conflicts with project conventions

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 21, Story 21.5]
- [Source: CLAUDE.md — Code Style, Commands sections]
- [Source: docs/site/cli-reference.md — current Global Options table]
- [Source: docs/site/index.md — current quickstart output example]
- [Source: tests/unit/test_cli.py:2027-2118 — Story 21.4 test patterns]
- [Source: tests/unit/test_cli_timing.py:275-320 — summary-on-stderr patterns]

### Build Dependencies

mkdocs and related packages are in `pyproject.toml` under the `docs` optional dependency group. To run `mkdocs build --strict` (AC8), install with: `uv sync --extra docs`.

### Documentation Impact

- Pages: `docs/site/cli-reference.md`, `docs/site/index.md`, `docs/site/ci-integration.md`, `docs/site/checks/enrichment.md`, `docs/site/checks/freshness.md`, `docs/site/checks/coverage.md`, `docs/site/checks/griffe.md`
- Nature of update: Add three-tier output model section to CLI reference, add `--quiet` flag to global options, fix dual-registration examples, update output examples to show Vetted summary format, add `--verbose`/`--quiet` to check page Usage sections, add `-q` CI tip

## Quality Gates

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 879 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All documentation updated for three-tier output model (quiet/default/verbose)
- 7 new edge-case tests added (3 in test_cli.py, 4 in test_cli_timing.py)
- Zero source code changes — docs + tests only, as expected
- Test count: 872 -> 879 (+7 new tests)
- All 8 ACs satisfied, all quality gates green

### Change Log

- 2026-02-26: Implemented all 6 tasks — CLI reference, getting started, CI integration, edge-case tests, check page docs, quality gates

### File List

- docs/site/cli-reference.md — Added `--quiet` to Global Options, fixed dual-registration example, added Output Tiers section with Vetted examples
- docs/site/index.md — Updated output example to show Vetted summary line
- docs/site/ci-integration.md — Added `-q` tip for scripted/CI contexts
- docs/site/checks/enrichment.md — Added `--verbose`/`--quiet` to Usage section
- docs/site/checks/freshness.md — Added `--verbose`/`--quiet` to Usage section
- docs/site/checks/coverage.md — Added `--verbose`/`--quiet` to Usage section
- docs/site/checks/griffe.md — Added `--verbose`/`--quiet` to Usage section
- tests/unit/test_cli.py — Added 3 edge-case tests (freshness quiet, griffe quiet, staged zero-files)
- tests/unit/test_cli_timing.py — Added 4 subcommand stderr tests (enrichment/griffe x format-markdown/output-flag)

## Code Review

### Reviewer

Claude Opus 4.6 (adversarial review) — 2026-02-26

### Outcome

Approved with fixes applied.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | cli-reference.md `--quiet` description claims config messages are suppressed, contradicting CLI `--help` which says "Config warnings are always shown." | Fixed: updated Global Options description to match CLI help text |
| M2 | MEDIUM | `test_griffe_subcommand_quiet_suppresses_summary` mocks `find_spec` but not `_run_griffe`, making test depend on optional griffe install | Fixed: added `mocker.patch("docvet.cli._run_griffe", return_value=[])` |
| L1 | LOW | Output Tiers table says Quiet stderr = *(nothing)* but parse/availability warnings still appear | Fixed: added clarifying sentence below the table |
| L2 | LOW | Check page docs say "suppress the summary line" vs full description elsewhere | Dismissed: intentional information architecture (task-oriented vs reference-oriented docs) |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass (879 tests, ruff, ty, docvet all green)
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
