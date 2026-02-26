# Story 20.2: Per-check Timing and Total Execution Time

Status: review
Branch: `feat/cli-20-2-per-check-timing`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer running docvet**,
I want to see how long each check takes and the total execution time,
so that I can identify slow checks and understand overall performance.

## Acceptance Criteria

1. **Given** docvet `check` is running with `--verbose` flag
   **When** each check completes
   **Then** a timing line is printed to stderr showing the check name, file count, and elapsed time (e.g., `enrichment: 42 files in 0.3s`)

2. **Given** docvet `check` is running without `--verbose` flag
   **When** each check completes
   **Then** no per-check timing lines are printed

3. **Given** docvet completes all checks (or a single subcommand completes)
   **When** the summary output is displayed
   **Then** the total execution time is shown on stderr (e.g., `Completed in 1.2s`) regardless of verbose mode

4. **Given** the timing implementation
   **When** reviewing the dependency tree
   **Then** no new runtime dependencies are introduced — only stdlib or typer utilities are used

**Note:** Per-check timing lines (AC #1) apply only to the combined `check` command where multiple checks run. Individual subcommands (`docvet enrichment`, `docvet freshness`, etc.) show only total execution time (AC #3) — per-check timing would be redundant when there is exactly one check.

## Tasks / Subtasks

- [x] Task 1: Add per-check timing to `check()` command (AC: #1, #2, #4)
  - [x] 1.1: Import `time` module (stdlib, already available)
  - [x] 1.2: Wrap each `_run_*` call with `time.perf_counter()` before/after
  - [x] 1.3: After each check, write timing line to stderr if `verbose` is true
- [x] Task 2: Add total execution time to `check()` command (AC: #3, #4)
  - [x] 2.1: Record `total_start = time.perf_counter()` after discovery completes
  - [x] 2.2: Compute total elapsed before calling `_output_and_exit`
  - [x] 2.3: Write `Completed in {elapsed:.1f}s\n` to stderr unconditionally
- [x] Task 3: Add total timing to individual subcommands (AC: #3)
  - [x] 3.1: Add total timing (always) to `enrichment()` subcommand
  - [x] 3.2: Add total timing (always) to `freshness()` subcommand
  - [x] 3.3: Add total timing (always) to `coverage()` subcommand
  - [x] 3.4: Add total timing (always) to `griffe()` subcommand
- [x] Task 4: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 4.1: Test that `check()` writes per-check timing to stderr when verbose
  - [x] 4.2: Test that `check()` does NOT write per-check timing when not verbose
  - [x] 4.3: Test that `check()` writes total time to stderr unconditionally
  - [x] 4.4: Test that individual subcommands write only total time (no per-check line)
  - [x] 4.5: Test timing format matches expected pattern (`enrichment: N files in X.Xs`)
  - [x] 4.6: Test that griffe timing line is suppressed when griffe is not installed (verbose `check`)
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `TestCheckVerbosePerCheckTiming::test_per_check_timing_lines_present_when_verbose`, `test_per_check_timing_format_matches_pattern` | Pass |
| #2 | `TestCheckNonVerboseNoPerCheckTiming::test_no_per_check_timing_without_verbose` | Pass |
| #3 | `TestCheckTotalTime::test_total_time_present_without_verbose`, `test_total_time_present_with_verbose`, `TestIndividualSubcommandTiming::test_*_subcommand_shows_total_only` (4 tests) | Pass |
| #4 | Only `import time` (stdlib) added — verified by inspection, no new entries in pyproject.toml deps | Pass |

## Dev Notes

### Implementation Approach

Add `time.perf_counter()` instrumentation around each `_run_*` call in the `check()` command and individual subcommands. Output to stderr (not stdout) to avoid polluting structured findings output.

**Per-check timing** (verbose only): After each `_run_*` completes, write to stderr:
```
enrichment: 42 files in 0.3s
freshness: 42 files in 0.5s
coverage: 42 files in 0.1s
griffe: 42 files in 0.2s
```

**Total execution time** (always): Before `_output_and_exit`, write to stderr:
```
Completed in 1.2s
```

### Key Design Decisions

1. **All timing output goes to stderr** — stdout is reserved for structured findings output (terminal or markdown). Timing is operational info like progress bars and verbose headers.

2. **No changes to `_output_and_exit`** — timing output happens BEFORE calling `_output_and_exit` because that function calls `raise typer.Exit()` which prevents any subsequent writes. Keep the output pipeline unchanged.

3. **No changes to `_run_*` functions** — timing wraps the calls, not the function bodies. The `_run_*` functions stay focused on their check logic. This is consistent with how Story 20.1 added `show_progress` as a parameter rather than having functions time themselves.

4. **`time.perf_counter()`** — not `time.time()`. `perf_counter` is monotonic and high-resolution, designed for measuring elapsed time. Stdlib, no new deps.

5. **Individual subcommands show only total time** — for `docvet enrichment`, only `Completed in 0.3s` is shown (always, regardless of verbose). Per-check timing is redundant when there is exactly one check. The combined `check` command shows the per-check breakdown because it runs 4 checks.

6. **Griffe skip guard** — when griffe is not installed, `_run_griffe` already prints `griffe: skipped (griffe not installed)` in verbose mode. Adding a timing line would produce contradictory output (`griffe: skipped` followed by `griffe: 42 files in 0.0s`). Guard the griffe timing line with `importlib.util.find_spec("griffe") is not None` to suppress it when griffe is not installed.

7. **Assign elapsed to variable before f-string** — do not compute `time.perf_counter() - start` inline inside f-string expressions. Assign `elapsed = time.perf_counter() - start` first, then use `{elapsed:.1f}s` in the f-string. Clearer, avoids side-effects in format expressions.

### Transformation for `check()` Command

```python
import time

@app.command()
def check(ctx, staged, all_files, files):
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]
    verbose = ctx.obj.get("verbose", False)
    show_progress = sys.stderr.isatty()
    file_count = len(discovered)

    total_start = time.perf_counter()

    start = time.perf_counter()
    enrichment_findings = _run_enrichment(discovered, config, show_progress=show_progress)
    elapsed = time.perf_counter() - start
    if verbose:
        sys.stderr.write(f"enrichment: {file_count} files in {elapsed:.1f}s\n")

    start = time.perf_counter()
    freshness_findings = _run_freshness(discovered, config, discovery_mode=discovery_mode, show_progress=show_progress)
    elapsed = time.perf_counter() - start
    if verbose:
        sys.stderr.write(f"freshness: {file_count} files in {elapsed:.1f}s\n")

    start = time.perf_counter()
    coverage_findings = _run_coverage(discovered, config)
    elapsed = time.perf_counter() - start
    if verbose:
        sys.stderr.write(f"coverage: {file_count} files in {elapsed:.1f}s\n")

    # Guard: only show griffe timing when griffe is actually installed.
    # _run_griffe already prints "griffe: skipped ..." in verbose mode when missing.
    griffe_installed = importlib.util.find_spec("griffe") is not None
    start = time.perf_counter()
    griffe_findings = _run_griffe(discovered, config, verbose=verbose)
    elapsed = time.perf_counter() - start
    if verbose and griffe_installed:
        sys.stderr.write(f"griffe: {file_count} files in {elapsed:.1f}s\n")

    total_elapsed = time.perf_counter() - total_start
    sys.stderr.write(f"Completed in {total_elapsed:.1f}s\n")

    findings_by_check = { ... }
    _output_and_exit(ctx, findings_by_check, config, file_count, ["enrichment", "freshness", "coverage", "griffe"])
```

### Transformation for Individual Subcommands

Individual subcommands show only total execution time (no per-check breakdown — redundant with one check).

Example for `enrichment()`:
```python
@app.command()
def enrichment(ctx, staged, all_files, files):
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_enrichment(discovered, config, show_progress=sys.stderr.isatty())
    elapsed = time.perf_counter() - start
    sys.stderr.write(f"Completed in {elapsed:.1f}s\n")

    _output_and_exit(ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"])
```

Apply the same pattern to `freshness()`, `coverage()`, and `griffe()` subcommands. The `verbose` local variable is not needed in individual subcommands since per-check timing is not shown.

### Cognitive Complexity Consideration

The `check()` command currently has straightforward linear flow. Adding timing introduces 3 `if verbose:` blocks (enrichment, freshness, coverage) plus 1 `if verbose and griffe_installed:` block. Each is a simple conditional write — no nesting. This adds ~4 CC points but the function remains well under the SonarQube threshold of 15.

Individual subcommands are even simpler — 1 timing measurement + 1 unconditional write (no `if verbose:` since per-check timing is not shown).

### Testing Strategy

Tests should verify:

1. **Per-check timing present in verbose `check`** — capture stderr output from `check()` with verbose=True, assert timing lines match `r"enrichment: \d+ files in \d+\.\d+s"` pattern for enrichment, freshness, coverage, and (when installed) griffe.

2. **Per-check timing absent without verbose** — capture stderr from `check()` without verbose, assert no per-check timing lines present (only `Completed in` line).

3. **Total time always present** — capture stderr from `check()` without verbose, assert `Completed in` line present.

4. **Format correctness** — timing lines match expected format: `{check_name}: {N} files in {X.X}s`.

5. **Individual subcommand: total only** — capture stderr from `enrichment()` with verbose=True, assert `Completed in` line present but NO per-check timing line.

6. **Griffe skip guard** — capture stderr from verbose `check()` with griffe not installed, assert only 3 per-check timing lines (no griffe line), and verify the existing `griffe: skipped` message is present.

Use `typer.testing.CliRunner` for integration-style tests or mock `sys.stderr.write` / `time.perf_counter` for unit tests. The Story 20.1 tests in `tests/unit/test_cli_progress.py` and `tests/unit/test_cli.py` establish the testing patterns for CLI behavior.

**Recommended test file**: `tests/unit/test_cli_timing.py` (new file, parallel to `test_cli_progress.py`).

**Mocking approach**: Mock `time.perf_counter` to return controlled values (e.g., 100.0, 100.5 for 0.5s elapsed). Mock `sys.stderr.write` to capture timing output. Mock the `_run_*` functions to avoid actual check execution (return empty findings). Mock `importlib.util.find_spec` to simulate griffe installed/not-installed scenarios.

### What NOT to Change

- Do NOT modify `_output_and_exit` — timing goes before the call, not inside
- Do NOT modify `_run_*` function bodies — timing wraps the calls
- Do NOT add a `--timing` flag — timing is controlled by `--verbose` (per-check) and always-on (total)
- Do NOT add timing to `_discover_and_handle` — discovery time is not part of check timing
- Do NOT change the progress bar behavior from Story 20.1
- Do NOT modify `reporting.py` — timing is CLI-level, not report-level

### Previous Story Intelligence (Story 20.1)

From Story 20.1 implementation:
- `show_progress` was added as keyword-only parameter with default `False` — follow the same backward-compatible pattern for any new parameters
- `sys.stderr.isatty()` is computed once per subcommand and passed through — timing can use the same `verbose` variable already available in subcommands
- Tests in `test_cli_progress.py` mock `typer.progressbar` — timing tests should mock `time.perf_counter` and `sys.stderr.write` similarly
- The `check()` command already extracts `verbose` from `ctx.obj` — reuse this variable for timing conditionals
- Story 20.1 created a new test file (`test_cli_progress.py`) rather than adding to `test_cli.py` — follow the same pattern with `test_cli_timing.py`
- Code review found gaps: missing TTY path tests, missing empty-files boundary tests — proactively add timing tests for edge cases (0 files, griffe skipped)

### Existing `verbose` Variable Availability

The `check()` command does NOT currently extract `verbose` as a local variable — it accesses `ctx.obj.get("verbose", False)` inline when passing to `_run_griffe`. For timing, extract it once:
```python
verbose = ctx.obj.get("verbose", False)
```

Individual subcommands also do not currently have a `verbose` local variable. Add it where needed.

### Edge Cases to Test

- **Griffe not installed** (verbose `check`): No timing line for griffe — only 3 per-check lines (enrichment, freshness, coverage) plus the existing `griffe: skipped (griffe not installed)` message from `_run_griffe`. Total time line still shown. Test that only 3 timing lines appear, not 4.
- **Griffe installed** (verbose `check`): All 4 per-check timing lines appear.
- **Zero files discovered**: Won't reach timing code — `_discover_and_handle` raises `typer.Exit(0)` on empty discovery.
- **Very fast execution**: `0.0s` is valid output (happens when checking 1-2 files).
- **Non-TTY stderr**: Progress bar hidden but timing still writes to stderr. This is correct — timing is text, not progress bar.
- **Individual subcommand**: Only `Completed in X.Xs` shown, no per-check line even in verbose mode.

### Project Structure Notes

- All source changes in `src/docvet/cli.py` — timing instrumentation in `check()`, `enrichment()`, `freshness()`, `coverage()`, `griffe()` subcommands
- New test file `tests/unit/test_cli_timing.py`
- New import: `import time` at top of `cli.py` (stdlib, already imported elsewhere in Python projects)
- No changes to any other source files

### References

- [Source: src/docvet/cli.py#check] — Main check command (line 556)
- [Source: src/docvet/cli.py#enrichment] — Enrichment subcommand (line 601)
- [Source: src/docvet/cli.py#freshness] — Freshness subcommand (line 627)
- [Source: src/docvet/cli.py#coverage] — Coverage subcommand (line 663)
- [Source: src/docvet/cli.py#griffe] — Griffe subcommand (line 685)
- [Source: src/docvet/cli.py#_output_and_exit] — Output pipeline (line 195) — do NOT modify
- [Source: tests/unit/test_cli_progress.py] — Story 20.1 test patterns for CLI behavior mocking
- [Source: tests/unit/test_cli.py] — Existing CLI tests with mock patterns
- [Source: epics-next.md#Story 4.2] — Epic specification
- [Source: GitHub Issue #24] — Feature request with acceptance criteria

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 826 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging needed.

### Completion Notes List

- Added `import time` to cli.py (stdlib, zero new deps)
- Wrapped each `_run_*` call in `check()` with `time.perf_counter()` for per-check timing (verbose only)
- Added griffe skip guard: `importlib.util.find_spec("griffe")` check suppresses griffe timing when not installed
- Added total execution time (`Completed in X.Xs`) to `check()` (unconditional) and all 4 individual subcommands
- Extracted `verbose` as local variable in `check()` for cleaner timing conditionals
- Updated docstrings for `check()`, `enrichment()`, `freshness()`, `coverage()`, `griffe()`, and module docstring to mention timing
- Created `tests/unit/test_cli_timing.py` with 14 tests covering all ACs
- Updated 7 existing tests in `test_cli.py` that expected empty output (now include timing line)

### Change Log

- 2026-02-26: Implemented per-check timing (verbose), total execution time (always), and griffe skip guard

### File List

- `src/docvet/cli.py` — modified (timing instrumentation + docstring updates)
- `tests/unit/test_cli_timing.py` — new (14 timing tests)
- `tests/unit/test_cli.py` — modified (7 tests updated for timing line in output)

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
