# Story 21.4: Subcommand Output Parity

Status: done
Branch: `feat/cli-21-4-subcommand-output-parity`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer running a single docvet check**,
I want the individual subcommands (`enrichment`, `freshness`, `coverage`, `griffe`) to show the same summary format as `check`,
So that the output experience is consistent regardless of which command I use.

## Acceptance Criteria

1. **Given** `docvet enrichment --all` runs with zero findings **When** the command completes **Then** stderr shows: `Vetted {N} files [enrichment] — no findings. ({elapsed}s)`

2. **Given** `docvet freshness --all` runs with findings **When** the command completes **Then** stderr shows: `Vetted {N} files [freshness] — {count} findings (...). ({elapsed}s)` **And** findings appear on stdout

3. **Given** `docvet coverage --all` runs **When** the command completes **Then** stderr shows the summary line with `[coverage]` in the check list

4. **Given** `docvet griffe --all` runs with griffe installed **When** the command completes **Then** stderr shows the summary line with `[griffe]` in the check list

5. **Given** any individual subcommand with `--verbose` flag (in either position) **When** the command completes **Then** verbose-tier output appears (file count from `_discover_and_handle`) followed by the summary line

6. **Given** any individual subcommand with `-q` flag **When** the command completes **Then** quiet-tier behavior applies (no summary, findings-only on stdout)

7. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all tests pass

## Tasks / Subtasks

- [x] Task 1: Add verbose/quiet dual-registration to `enrichment` subcommand (AC: 1, 5, 6, 7)
  - [x] 1.1: Add `verbose` and `quiet` parameters to `enrichment()` signature (same `typer.Option` pattern as `check`)
  - [x] 1.2: Add dual-resolution lines after `_resolve_discovery_mode`: `verbose = verbose or ctx.obj.get("verbose", False)` / `quiet = quiet or ctx.obj.get("quiet", False)` / update `ctx.obj`
  - [x] 1.3: Replace `sys.stderr.write(f"Completed in {elapsed:.1f}s\n")` with `if not quiet: sys.stderr.write(format_summary(len(discovered), ["enrichment"], findings, elapsed))`
  - [x] 1.4: Update docstring to document `verbose` and `quiet` params

- [x] Task 2: Add verbose/quiet dual-registration to `freshness` subcommand (AC: 2, 5, 6, 7)
  - [x] 2.1: Add `verbose` and `quiet` parameters to `freshness()` signature
  - [x] 2.2: Add dual-resolution + ctx.obj update
  - [x] 2.3: Replace `sys.stderr.write(f"Completed in {elapsed:.1f}s\n")` with gated `format_summary` call using `["freshness"]`
  - [x] 2.4: Update docstring

- [x] Task 3: Add verbose/quiet dual-registration to `coverage` subcommand (AC: 3, 5, 6, 7)
  - [x] 3.1: Add `verbose` and `quiet` parameters to `coverage()` signature
  - [x] 3.2: Add dual-resolution + ctx.obj update
  - [x] 3.3: Replace `sys.stderr.write(f"Completed in {elapsed:.1f}s\n")` with gated `format_summary` call using `["coverage"]`
  - [x] 3.4: Update docstring

- [x] Task 4: Add verbose/quiet dual-registration to `griffe` subcommand (AC: 4, 5, 6, 7)
  - [x] 4.1: Add `verbose` and `quiet` parameters to `griffe()` signature
  - [x] 4.2: Add dual-resolution + ctx.obj update
  - [x] 4.3: Replace `sys.stderr.write(f"Completed in {elapsed:.1f}s\n")` with gated `format_summary` call using `["griffe"]`
  - [x] 4.4: Pass resolved `quiet` to `_run_griffe`: change `verbose=ctx.obj.get("verbose", False)` to `verbose=verbose, quiet=quiet`
  - [x] 4.5: Update docstring

- [x] Task 5: Unit tests for summary line on each subcommand (AC: 1, 2, 3, 4)
  - [x] 5.1: Test `enrichment --all` produces `Vetted N files [enrichment]` summary on stderr
  - [x] 5.2: Test `freshness --all` produces `Vetted N files [freshness]` summary on stderr
  - [x] 5.3: Test `coverage --all` produces `Vetted N files [coverage]` summary on stderr
  - [x] 5.4: Test `griffe --all` produces `Vetted N files [griffe]` summary on stderr
  - [x] 5.5: Test `freshness --all` with findings shows findings on stdout AND summary on stderr

- [x] Task 6: Unit tests for verbose/quiet on subcommands (AC: 5, 6)
  - [x] 6.1: Test `docvet enrichment --all --verbose` shows file count + summary (verbose tier)
  - [x] 6.2: Test `docvet --verbose enrichment --all` (app-level) shows verbose tier
  - [x] 6.3: Test `docvet enrichment --all -q` suppresses summary on stderr, findings still on stdout
  - [x] 6.4: Test `docvet enrichment --all -q --verbose` — quiet wins
  - [x] 6.5: Test at least one other subcommand (e.g., `coverage`) with `-q` to verify pattern consistency

- [x] Task 7: Update existing subcommand tests and run full suite (AC: 7)
  - [x] 7.1: Update `tests/unit/test_cli_timing.py:26` — change `SUBCOMMAND_TOTAL_RE` regex from `Completed in` pattern to match `Vetted` summary format
  - [x] 7.2: Update `tests/unit/test_cli_timing.py:163-190` — `TestIndividualSubcommandTiming` class (4 tests, one per subcommand) to use the updated regex
  - [x] 7.3: Update `tests/unit/test_cli.py:559` — `test_griffe_when_invoked_calls_discover_and_run_griffe` mock assertion: add `quiet=False` kwarg to `mock_run.assert_called_once_with(..., verbose=False, quiet=False)`
  - [x] 7.4: Run full test suite, fix any regressions

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_enrichment_subcommand_shows_vetted_summary_on_stderr` | Pass |
| 2 | `test_freshness_subcommand_shows_vetted_summary_on_stderr`, `test_freshness_subcommand_with_findings_shows_findings_and_summary` | Pass |
| 3 | `test_coverage_subcommand_shows_vetted_summary_on_stderr` | Pass |
| 4 | `test_griffe_subcommand_shows_vetted_summary_on_stderr` | Pass |
| 5 | `test_enrichment_subcommand_verbose_shows_file_count_and_summary`, `test_enrichment_app_level_verbose_shows_file_count_and_summary`, `test_verbose_single_check_suppresses_header` | Pass |
| 6 | `test_enrichment_subcommand_quiet_suppresses_summary`, `test_enrichment_subcommand_quiet_wins_over_verbose`, `test_coverage_subcommand_quiet_suppresses_summary`, `test_griffe_subcommand_quiet_passes_quiet_to_run_griffe` | Pass |
| 7 | Full suite: 872 tests pass, 0 regressions | Pass |

## Dev Notes

- **Primary file**: `src/docvet/cli.py` — four subcommand functions
- **No new files**: All changes are modifications to existing `cli.py` and test files
- **Pattern is proven**: The exact same dual-registration + format_summary pattern from `check` (Story 21.3) is applied to each subcommand. Copy the pattern, don't reinvent.

### Exact Code Pattern to Apply

Each subcommand gets the identical transformation. Use `enrichment` as the template:

**Before** (current `enrichment`, lines 678-707):
```python
@app.command()
def enrichment(
    ctx: typer.Context,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_enrichment(discovered, config, show_progress=sys.stderr.isatty())
    elapsed = time.perf_counter() - start
    sys.stderr.write(f"Completed in {elapsed:.1f}s\n")

    _output_and_exit(
        ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"]
    )
```

**After** (target pattern):
```python
@app.command()
def enrichment(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress non-finding output (summary, timing, verbose details)."
            " Config warnings are always shown.",
        ),
    ] = False,
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    discovery_mode = _resolve_discovery_mode(staged, all_files, files)
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = quiet or ctx.obj.get("quiet", False)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    discovered = _discover_and_handle(ctx, discovery_mode, files)
    config = ctx.obj["docvet_config"]

    start = time.perf_counter()
    findings = _run_enrichment(discovered, config, show_progress=sys.stderr.isatty())
    elapsed = time.perf_counter() - start
    if not quiet:
        sys.stderr.write(
            format_summary(len(discovered), ["enrichment"], findings, elapsed)
        )

    _output_and_exit(
        ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"]
    )
```

### Subcommand-Specific Notes

| Subcommand | Line Range | Special Handling |
|------------|-----------|------------------|
| `enrichment` | 678-707 | None — straightforward pattern |
| `freshness` | 710-749 | Has extra `mode` parameter — parameter order: `ctx, verbose, quiet, staged, all_files, files, mode` |
| `coverage` | 752-778 | None — straightforward pattern |
| `griffe` | 781-807 | Pass `verbose=verbose, quiet=quiet` to `_run_griffe` (line 803 currently passes `verbose=ctx.obj.get(...)`) |

### Critical: `griffe` subcommand `_run_griffe` call

The `griffe` subcommand currently calls (line 803):
```python
findings = _run_griffe(discovered, config, verbose=ctx.obj.get("verbose", False))
```

After the change, it should use the resolved local variables:
```python
findings = _run_griffe(discovered, config, verbose=verbose, quiet=quiet)
```

`_run_griffe` already accepts `quiet=False` as a keyword parameter (added in Story 21.3). This is the forward-compatibility that 21.3 prepared for.

### `_discover_and_handle` Already Works

`_discover_and_handle` reads verbose/quiet from `ctx.obj` (lines 194-195):
```python
if ctx.obj.get("verbose") and not ctx.obj.get("quiet"):
    typer.echo(f"Found {len(discovered)} file(s) to check", err=True)
```

By updating `ctx.obj` before calling `_discover_and_handle`, the file discovery count message is automatically gated correctly. No changes needed to `_discover_and_handle`.

### `_output_and_exit` Already Works

`_output_and_exit` reads verbose/quiet from `ctx.obj` (lines 224-226):
```python
verbose = ctx.obj.get("verbose", False)
quiet = ctx.obj.get("quiet", False)
```

The verbose header gating (line 241-243) already uses `if verbose and not quiet:`. No changes needed to `_output_and_exit`.

### format_summary Signature

```python
format_summary(file_count: int, checks: Sequence[str], findings: list[Finding], elapsed: float) -> str
```

Already imported in `cli.py` (line 49). Each subcommand passes its single check name as a one-element list: `["enrichment"]`, `["freshness"]`, `["coverage"]`, `["griffe"]`.

### Test Patterns from Story 21.3

Reuse the test patterns established in Story 21.3 for `check`. Key patterns:
- `SUMMARY_LINE_RE` regex (if defined) or assert `"Vetted"` in stderr
- `_non_timing_lines` helper (if available) or direct stderr assertions
- Test file: `tests/unit/test_cli.py`

### Known Tests That Will Break

**`tests/unit/test_cli_timing.py`:**
- Line 26: `SUBCOMMAND_TOTAL_RE = re.compile(r"^Completed in \d+\.\d+s$", re.MULTILINE)` — must be updated to match `Vetted` summary format
- Lines 163-190: `TestIndividualSubcommandTiming` class — 4 tests (one per subcommand) use `SUBCOMMAND_TOTAL_RE`. All will fail after `Completed in` is replaced with `format_summary`. Update regex or switch to `"Vetted"` assertion.

**`tests/unit/test_cli.py`:**
- Line 559: `test_griffe_when_invoked_calls_discover_and_run_griffe` — asserts `mock_run.assert_called_once_with([Path("/fake/file.py")], ANY, verbose=False)`. After changes, `_run_griffe` is called with `verbose=False, quiet=False`. Fix: add `quiet=False` kwarg to the assertion.

**`tests/unit/test_cli.py:39`:**
- `_non_timing_lines` helper already filters both `Completed in` and `Vetted ` — no change needed.

### Three-Tier Output Model (reminder)

| Tier | Trigger | stderr Output | stdout Output |
|------|---------|---------------|---------------|
| Quiet | `-q` / `--quiet` | Nothing | Findings only |
| Default | (no flags) | Summary line only | Findings only |
| Verbose | `--verbose` | File count + summary line | Findings only |

Note: Individual subcommands do NOT have per-check timing lines (that's a `check`-only feature where multiple checks run sequentially). Verbose mode on individual subcommands shows the file discovery count from `_discover_and_handle` plus the summary line.

### Previous Story Intelligence

**From 21-3 (Verbose & Quiet Flag Redesign):**
- Dual-registration pattern proven and working on `check` command
- Order-of-operations bug found in review (H1): `_discover_and_handle` was called BEFORE verbose/quiet resolution. Fix: place dual-resolution lines BEFORE `_discover_and_handle` call. Apply this lesson to all four subcommands.
- `_run_griffe` already has `quiet` parameter (forward compatibility from 21.3)
- Config warnings are NOT suppressed by quiet (deliberate decision per 21.3 Dev Notes)
- 860 tests after story 21.3 completion

**From 21-1 (Default Output Overhaul):**
- `format_summary` lives in `reporting.py`, already imported in `cli.py`
- The `check` command's `Completed in Xs` was replaced with `format_summary` — this story does the same for individual subcommands
- Zero-files edge case exits early at `cli.py:188-190` (in `_discover_and_handle`) before reaching any summary code

**From 21-2 (Config Warning Cleanup):**
- Config warnings are in `config.py`, fire during `load_config()` in the app callback — completely independent of subcommand output. No interaction with this story.

### Project Structure Notes

- All changes in `src/docvet/cli.py`, `tests/unit/test_cli.py`, and `tests/unit/test_cli_timing.py`
- No new modules, no cross-module changes
- `reporting.py`, `config.py`, `discovery.py`, `ast_utils.py` — all untouched
- `Annotated` is already imported in `cli.py` (used by `check` command)

### References

- [Source: _bmad-output/planning-artifacts/epics-cli-ux.md — Story 21.4 section, FR-UX15, FR-UX16]
- [Source: _bmad-output/planning-artifacts/epics-cli-ux.md — Requirements Inventory, NFR-UX1 through NFR-UX8]
- [Source: src/docvet/cli.py — enrichment() lines 678-707, freshness() lines 710-749, coverage() lines 752-778, griffe() lines 781-807]
- [Source: src/docvet/cli.py — check() lines 574-675 (reference pattern for dual-registration + format_summary)]
- [Source: src/docvet/cli.py — _output_and_exit() lines 200-263, _discover_and_handle() lines 161-197, _run_griffe() lines 450-480]
- [Source: src/docvet/reporting.py — format_summary() line 130]
- [Source: _bmad-output/implementation-artifacts/21-3-verbose-and-quiet-flag-redesign.md — previous story learnings, H1 order-of-operations bug]

### Documentation Impact

- Pages: `docs/site/cli-reference.md`
- Nature of update: Document that individual subcommands now support `--verbose` and `-q`/`--quiet` flags and show the `Vetted` summary line. Deferred to Story 21.5 (dedicated docs story).

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (872 passed), no regressions
- [x] `uv run docvet check --all` — zero findings (Vetted 12 files — no findings)
- [x] `uv run interrogate -v` — docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no blockers.

### Completion Notes List

- Applied the proven dual-registration pattern from `check` (Story 21.3) to all four individual subcommands
- Each subcommand now accepts `--verbose` and `-q`/`--quiet` at both app-level and subcommand-level
- Replaced `Completed in {elapsed}s` with `format_summary()` gated by `if not quiet`
- Critical: placed verbose/quiet resolution BEFORE `_discover_and_handle` call (lesson from 21.3 H1 bug)
- `griffe` subcommand now passes `verbose=verbose, quiet=quiet` to `_run_griffe` (using forward-compatibility from 21.3)
- Updated `SUBCOMMAND_TOTAL_RE` regex in test_cli_timing.py to match new `Vetted` summary format
- Updated griffe mock assertion to include `quiet=False` kwarg
- Added 13 new tests covering all ACs (summary line per subcommand, verbose/quiet tiers, quiet wins)
- All 870 tests pass, all quality gates green
- Code review: fixed 5 findings (M1-M3, L1-L2), accepted L3 as by-design
- M1: Added `len(checks) > 1` guard in `_output_and_exit` to suppress redundant verbose header for single-check subcommands
- M2: Added stdout finding assertion to AC2 test
- M3: Added `test_griffe_subcommand_quiet_passes_quiet_to_run_griffe` for unique griffe quiet wiring
- L1: Consolidated duplicate `SUBCOMMAND_TOTAL_RE` into `SUMMARY_LINE_RE`
- L2: Removed dead `"Completed in"` filter from `_non_timing_lines`
- Post-review: 872 tests pass, all quality gates green

### Change Log

- 2026-02-26: Implemented subcommand output parity — all subcommands now emit unified `Vetted` summary line with three-tier verbosity control
- 2026-02-26: Code review fixes — verbose header guard for single-check runs, test gaps (AC2 stdout, griffe quiet wiring), test constant cleanup

### File List

- `src/docvet/cli.py` — modified (enrichment, freshness, coverage, griffe subcommands + module docstring + `_output_and_exit` verbose header guard)
- `tests/unit/test_cli.py` — modified (griffe mock assertion fix + 15 new tests + dead filter cleanup + verbose header test updates)
- `tests/unit/test_cli_timing.py` — modified (SUBCOMMAND_TOTAL_RE consolidated into SUMMARY_LINE_RE)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party-mode consensus with Dev, QA, Architect, UX, Analyst agents)

### Outcome

Approved with fixes (all applied)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | Medium | Verbose header "Checking N files" appears after "Vetted N files" for single-check subcommands — violates AC5 two-element verbose contract | Fixed: added `len(checks) > 1` guard in `_output_and_exit` + negative assertion + new `test_verbose_single_check_suppresses_header` test |
| M2 | Medium | AC2 test does not verify findings appear on stdout | Fixed: added `assert "test.py:1:" in result.output` to `test_freshness_subcommand_with_findings_shows_findings_and_summary` |
| M3 | Medium | No CLI test for `griffe -q` passing `quiet=True` to `_run_griffe` (unique wiring) | Fixed: added `test_griffe_subcommand_quiet_passes_quiet_to_run_griffe` |
| L1 | Low | `SUBCOMMAND_TOTAL_RE` identical to `SUMMARY_LINE_RE` — redundant constant | Fixed: removed `SUBCOMMAND_TOTAL_RE`, replaced all usages with `SUMMARY_LINE_RE` |
| L2 | Low | `_non_timing_lines` filters dead `"Completed in"` pattern — no command produces this anymore | Fixed: removed dead filter branch |
| L3 | Low | Four subcommands repeat identical verbose/quiet boilerplate (~40 lines) | Accepted: by design per story instructions, typer decorator pattern doesn't lend to abstraction |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
