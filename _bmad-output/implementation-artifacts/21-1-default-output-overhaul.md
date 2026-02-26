# Story 21.1: Default Output Overhaul

Status: review
Branch: `feat/cli-21-1-default-output-overhaul`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer running docvet for the first time**,
I want to see a clear summary of what was checked and whether my docs are clean,
So that I immediately understand the result without needing verbose mode or guessing from exit codes.

## Acceptance Criteria

1. **Given** `docvet check --all` runs on a codebase with zero findings **When** the command completes **Then** stderr contains a summary line matching the format: `Vetted {N} files [{checks}] — no findings. ({elapsed}s)` **And** the check list includes only checks that actually ran (e.g., `griffe` omitted if not installed)

2. **Given** `docvet check --all` runs on a codebase with findings **When** the command completes **Then** stdout contains the finding lines (unchanged format) **And** stderr contains a summary line: `Vetted {N} files [{checks}] — {count} findings ({required} required, {recommended} recommended). ({elapsed}s)`

3. **Given** `docvet check --all` runs with `--format markdown` or `--output report.md` **When** the command completes **Then** the summary line still appears on stderr (not in the markdown output or file)

4. **Given** zero files are discovered (empty repo or all excluded) **When** the command completes **Then** the summary line reads: `Vetted 0 files [{checks}] — no findings. ({elapsed}s)`

5. **Given** griffe is not installed **When** `docvet check --all` runs **Then** the check list in the summary omits `griffe` (e.g., `[enrichment, freshness, coverage]`)

6. **Given** the existing `Completed in Xs` output on stderr (`cli.py:615`) **When** the summary line is implemented **Then** the `Completed in Xs` line is **replaced** by the summary line (not duplicated) **And** the timing information is embedded in the summary line's `({elapsed}s)` suffix

7. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all tests pass (existing output assertions updated as needed in this story for the `check` command only)

## Tasks / Subtasks

- [x] Task 1: Add `format_summary` function to `reporting.py` (AC: 1, 2, 4)
  - [x] 1.1: Create `format_summary(file_count: int, checks: Sequence[str], findings: list[Finding], elapsed: float) -> str` function
  - [x] 1.2: Zero-findings branch returns `Vetted {N} files [{checks}] — no findings. ({elapsed}s)\n`
  - [x] 1.3: Findings branch returns `Vetted {N} files [{checks}] — {count} findings ({required} required, {recommended} recommended). ({elapsed}s)\n`
  - [x] 1.4: Use em dash (—) not hyphen; period before parenthesized elapsed time
  - [x] 1.5: Unit tests for `format_summary`: zero findings, mixed findings, zero files, single check, all checks
- [x] Task 2: Replace `Completed in Xs` with summary line in `check` command (AC: 1, 2, 6)
  - [x] 2.1: In `cli.py` `check()` function, replace `sys.stderr.write(f"Completed in {total_elapsed:.1f}s\n")` with `sys.stderr.write(format_summary(file_count, checks, all_findings_flat, total_elapsed))`
  - [x] 2.2: Flatten all findings before the summary call: `all_findings = enrichment_findings + freshness_findings + coverage_findings + griffe_findings`
  - [x] 2.3: Remove the `if verbose and not all_findings: sys.stdout.write("No findings.\n")` block in `_output_and_exit` — summary line covers this
- [x] Task 3: Conditional griffe in check list (AC: 5)
  - [x] 3.1: Build `checks` list dynamically — only include `"griffe"` if griffe is installed and the check actually ran
  - [x] 3.2: Unit test: verify `griffe` omitted from check list when not installed
- [x] Task 4: Ensure summary on stderr regardless of output format (AC: 3)
  - [x] 4.1: Verify summary line is written to `sys.stderr` independent of `--format` and `--output` flags
  - [x] 4.2: Integration test: `--format markdown` still has summary on stderr
  - [x] 4.3: Integration test: `--output report.md` still has summary on stderr
- [x] Task 5: Update existing tests for new output format (AC: 7)
  - [x] 5.1: Find all tests asserting on `Completed in` or `No findings.` output
  - [x] 5.2: Update assertions to match new `Vetted N files [...]` format
  - [x] 5.3: Run full test suite, fix any regressions

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `TestFormatSummary::test_zero_findings`, `TestCheckSummaryLine::test_summary_present_without_verbose` | Pass |
| AC2 | `TestFormatSummary::test_mixed_findings`, `TestCheckSummaryLine::test_summary_present_with_verbose` | Pass |
| AC3 | `TestSummaryAlwaysOnStderr::test_summary_present_with_format_markdown`, `TestSummaryAlwaysOnStderr::test_summary_present_with_output_flag` | Pass |
| AC4 | `TestFormatSummary::test_zero_files` | Pass |
| AC5 | `TestSummaryConditionalGriffe::test_summary_omits_griffe_when_not_installed`, `TestSummaryConditionalGriffe::test_summary_includes_griffe_when_installed` | Pass |
| AC6 | `TestTimingFormat::test_total_format_is_vetted_summary_line` | Pass |
| AC7 | Full test suite: 840 tests pass, zero regressions | Pass |

## Dev Notes

- **Primary files to modify**: `src/docvet/reporting.py` (new function), `src/docvet/cli.py` (replace output)
- **Stream separation is critical**: Findings → stdout, summary → stderr. This is an architectural invariant (see architecture.md). The `--format markdown` and `--output` flags affect stdout only; the summary line must always go to stderr.
- **Em dash character**: Use `—` (U+2014), not `--` or `-`. This is a brand-level formatting choice from the epics research.
- **"Vetted" brand verb**: The word "Vetted" is chosen deliberately — it's the verb form of the product name, no other Python tool uses it, and it communicates examination/approval. Do not change to "Checked" or "Scanned".
- **`format_summary` vs `format_verbose_header`**: These are separate functions. `format_verbose_header` stays for verbose mode (Story 21.3 scope). `format_summary` is the new unconditional summary line. Do not merge them.
- **Finding count breakdown**: The summary distinguishes "required" vs "recommended" findings. This maps to `Finding.category` which is `Literal["required", "recommended"]`. Reuse the existing `Counter(f.category for f in findings)` pattern already in `reporting.py:86` and `reporting.py:120` — `Counter` is already imported from `collections`.
- **Elapsed time format**: Use `:.1f` (one decimal place) to match existing `Completed in Xs` format.
- **`griffe_installed` already exists**: `cli.py:607` has `griffe_installed = importlib.util.find_spec("griffe") is not None`. Use this variable to conditionally append `"griffe"` to the `checks` list — do not re-detect.

### Code Locations (current line numbers, may shift)

| What | File | Line(s) | Action |
|------|------|---------|--------|
| `Completed in Xs` | `cli.py` | ~615 | Replace with `format_summary(...)` |
| `No findings.` (verbose-only) | `cli.py` | ~259 | Remove — summary line covers this |
| Verbose header | `cli.py` | ~237-238 | Leave unchanged (Story 21.3 scope) |
| `format_verbose_header` | `reporting.py` | 129-139 | Leave unchanged, use as pattern for `format_summary` |
| `checks` list built | `cli.py` | ~628 | Already has check list — ensure griffe conditional |
| `file_count` | `cli.py` | ~581 | Already available as `len(files)` |
| Findings collected | `cli.py` | ~586-609 | Already collected per-check; flatten for summary |
| `findings_by_check` dict | `cli.py` | ~617-622 | Built after timing — summary should print before this or alongside |

### Data Flow for Summary Line

```
check() function:
  1. files = discover_files(...)         → file_count = len(files)
  2. checks = []                         → populated as checks run
  3. enrichment_findings = _run_enrichment(...)
  4. freshness_findings = _run_freshness(...)
  5. coverage_findings = _run_coverage(...)
  6. griffe_findings = _run_griffe(...)   → only if griffe installed
  7. total_elapsed = time.perf_counter() - start
  8. all_findings = enr + fresh + cov + griffe  ← NEW: flatten here
  9. sys.stderr.write(format_summary(file_count, checks, all_findings, total_elapsed))  ← REPLACE "Completed in"
  10. _output_and_exit(ctx, findings_by_check, config, file_count, checks)
```

### Project Structure Notes

- `format_summary` goes in `reporting.py` alongside `format_verbose_header`, `format_terminal`, `format_markdown` — consistent module placement
- No new files needed — this is additive to existing modules
- Import in `cli.py`: `from docvet.reporting import format_summary` (add to existing import line)

### References

- [Source: _bmad-output/planning-artifacts/epics-cli-ux.md — Story 21.1 section]
- [Source: _bmad-output/planning-artifacts/epics-cli-ux.md — Requirements Inventory, FR-UX1 through FR-UX4]
- [Source: _bmad-output/planning-artifacts/architecture.md — Reporting module location, stderr conventions]
- [Source: src/docvet/cli.py — check() function, _output_and_exit() function]
- [Source: src/docvet/reporting.py — format_verbose_header, format_terminal]

### Documentation Impact

- Pages: `docs/site/cli-reference.md`, `docs/site/getting-started.md`
- Nature of update: Example output will change from `Completed in Xs` to `Vetted N files [...] — ...` format. Deferred to Story 21.5 (dedicated docs story).

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 840 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0% (≥ 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debug issues.

### Completion Notes List

- Added `format_summary()` to `reporting.py` with zero-findings and findings branches, em dash separator, and `:.1f` elapsed formatting
- Replaced `Completed in Xs` line in `check()` with `format_summary()` call on stderr
- Built `checks` list dynamically — griffe only included when installed
- Flattened all findings before summary call for accurate total count
- Removed `if verbose and not all_findings: sys.stdout.write("No findings.\n")` — summary line on stderr replaces this
- Added 9 unit tests for `format_summary` (zero/mixed findings, zero files, single/all checks, em dash, trailing newline, elapsed format)
- Added 2 tests for conditional griffe in summary (installed vs not installed)
- Added 2 tests for summary on stderr regardless of `--format`/`--output`
- Updated `TOTAL_LINE_RE` → `SUMMARY_LINE_RE` regex in timing tests, added `SUBCOMMAND_TOTAL_RE` for individual subcommands
- Updated `_non_timing_lines` helper to filter both old and new format
- Updated 3 test assertions: removed `No findings.` stdout checks, updated diff mode negative assertion
- Updated docstrings for `_output_and_exit`, `check()`, `format_markdown`, and both module docstrings to resolve freshness findings

### Change Log

- 2026-02-26: Implemented default output overhaul — `check` command now prints `Vetted N files [checks] — summary. (Xs)` to stderr unconditionally, replacing `Completed in Xs`. 13 new tests added, 840 total tests pass.

### File List

- `src/docvet/reporting.py` — Added `format_summary()`, updated module docstring and `format_markdown` docstring
- `src/docvet/cli.py` — Replaced `Completed in` with `format_summary()` call, dynamic `checks` list, removed `No findings.` block, updated module and function docstrings
- `tests/unit/test_reporting.py` — Added `TestFormatSummary` class with 9 tests
- `tests/unit/test_cli_timing.py` — Updated regex patterns, added `TestSummaryConditionalGriffe` and `TestSummaryAlwaysOnStderr` classes
- `tests/unit/test_cli.py` — Updated `_non_timing_lines` helper, removed `No findings.` assertions, updated diff mode test

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
