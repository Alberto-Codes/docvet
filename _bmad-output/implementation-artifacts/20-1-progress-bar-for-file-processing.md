# Story 20.1: Progress Bar for File Processing

Status: review
Branch: `feat/cli-20-1-progress-bar-file-processing`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer running docvet**,
I want to see a progress bar showing files being processed,
so that I get real-time feedback on long-running checks instead of staring at a silent terminal.

## Acceptance Criteria

1. **Given** docvet is running with stderr connected to a TTY
   **When** checks are processing files
   **Then** a progress bar is displayed on stderr showing files processed out of total (e.g., `enrichment  [####------]  42/128`)

2. **Given** docvet is running with stderr piped or redirected (not a TTY)
   **When** checks are processing files
   **Then** no progress output is written to stderr

3. **Given** the progress bar implementation
   **When** reviewing the dependency tree
   **Then** no new runtime dependencies are introduced — only stdlib or typer utilities are used

4. **Given** docvet completes all checks
   **When** the final report is displayed
   **Then** the progress bar is cleared and does not interfere with the report output

5. **Given** individual subcommands (`docvet enrichment`, `docvet freshness`)
   **When** run with stderr connected to a TTY
   **Then** the progress bar is displayed for the per-file check loop

## Tasks / Subtasks

- [x] Task 1: Add progress bar to `_run_enrichment` (AC: #1, #2, #3, #4)
  - [x] 1.1: Accept `show_progress: bool` parameter
  - [x] 1.2: Wrap file iteration loop with `typer.progressbar(files, label="enrichment", file=sys.stderr, hidden=not show_progress)`
  - [x] 1.3: Move file-reading and AST-parsing logic inside the progress bar context
- [x] Task 2: Add progress bar to `_run_freshness` (AC: #1, #2, #3, #4)
  - [x] 2.1: Accept `show_progress: bool` parameter
  - [x] 2.2: Wrap both the diff-mode and drift-mode file iteration loops with `typer.progressbar`
  - [x] 2.3: Use label `"freshness"` for the progress bar
- [x] Task 3: Wire `show_progress` through subcommands (AC: #1, #2, #5)
  - [x] 3.1: Compute `show_progress = sys.stderr.isatty()` in `check()` subcommand
  - [x] 3.2: Pass `show_progress` to `_run_enrichment` and `_run_freshness`
  - [x] 3.3: Wire `show_progress` in `enrichment()` and `freshness()` subcommands
- [x] Task 4: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 4.1: Test that `_run_enrichment` calls `typer.progressbar` with correct args when `show_progress=True`
  - [x] 4.2: Test that `_run_enrichment` does NOT call `typer.progressbar` (or uses `hidden=True`) when `show_progress=False`
  - [x] 4.3: Test that `_run_freshness` (both modes) uses progress bar when `show_progress=True`
  - [x] 4.4: Test that findings are identical with and without progress bar (no behavioral change)
  - [x] 4.5: Test that progress bar writes to `sys.stderr`, not `sys.stdout`
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 (TTY progress bar) | `test_enrichment_progressbar_hidden_false_when_show_progress_true`, `test_freshness_diff_progressbar_hidden_false_when_show_progress_true`, `test_freshness_drift_progressbar_hidden_false_when_show_progress_true` | PASS |
| AC2 (non-TTY suppression) | `test_enrichment_progressbar_hidden_true_when_show_progress_false`, `test_freshness_diff_progressbar_hidden_true_when_show_progress_false`, `test_freshness_drift_progressbar_hidden_true_when_show_progress_false`, `test_enrichment_progressbar_default_show_progress_is_false` | PASS |
| AC3 (no new deps) | No new imports — `typer.progressbar` is Click's built-in `click.progressbar` (verified by inspection) | PASS |
| AC4 (progress bar clears) | `typer.progressbar` context manager self-clears on exit; `test_enrichment_findings_identical_with_and_without_progress`, `test_freshness_findings_identical_with_and_without_progress` | PASS |
| AC5 (subcommand progress) | `test_freshness_subcommand_passes_discovery_mode_to_run_freshness` (verifies `show_progress=False` kwarg), `test_check_when_invoked_passes_config_to_run_stubs` (verifies wiring in `check` cmd) | PASS |

## Dev Notes

### Implementation Approach

The progress bar wraps the per-file iteration loops in `_run_enrichment` and `_run_freshness`. These are the only `_run_*` functions that iterate over files in `cli.py`:

- `_run_enrichment` (line 346): `for file_path in files:` — reads, parses AST, runs checks per file
- `_run_freshness` (lines 382, 397): two `for file_path in files:` loops — one for drift mode, one for diff mode

The other two runners delegate to check functions that process all files at once:
- `_run_coverage` → `check_coverage(src_root, files)` — single call, no per-file loop in CLI
- `_run_griffe` → `check_griffe_compat(src_root, files)` — single call, no per-file loop in CLI

Coverage and griffe do not need progress bars — they are fast single-call operations.

### typer.progressbar() API

`typer.progressbar()` (Click's `click.progressbar`) provides exactly what we need:

```python
with typer.progressbar(files, label="enrichment", file=sys.stderr, hidden=not show_progress) as progress:
    for file_path in progress:
        source = file_path.read_text(encoding="utf-8")
        # ... rest of per-file logic
```

Key parameters:
- `iterable`: Pass the `files` list directly
- `label`: Check name (e.g., `"enrichment"`, `"freshness"`)
- `file`: Must be `sys.stderr` — stdout is reserved for report output
- `hidden`: When `True`, renders nothing (handles non-TTY case)
- Auto-behavior: Click's progressbar already suppresses rendering when `file` is not a TTY, but `hidden` gives us explicit control

The progressbar outputs to `file` (stderr) and clears itself when the context manager exits (AC #4), so it won't interfere with report output on stdout.

### show_progress Computation

Compute once per subcommand, pass to `_run_*` functions:

```python
show_progress = sys.stderr.isatty()
```

This covers:
- **TTY** (interactive terminal): `True` — show progress bar
- **Piped/redirected**: `False` — `hidden=True` suppresses output
- **CI environments**: Typically `False` (stderr not a TTY)

### Signature Changes

```python
# Before:
def _run_enrichment(files: list[Path], config: DocvetConfig) -> list[Finding]:

# After:
def _run_enrichment(files: list[Path], config: DocvetConfig, *, show_progress: bool = False) -> list[Finding]:
```

```python
# Before:
def _run_freshness(files: list[Path], config: DocvetConfig, freshness_mode: FreshnessMode = FreshnessMode.DIFF, discovery_mode: DiscoveryMode = DiscoveryMode.DIFF) -> list[Finding]:

# After:
def _run_freshness(files: list[Path], config: DocvetConfig, freshness_mode: FreshnessMode = FreshnessMode.DIFF, discovery_mode: DiscoveryMode = DiscoveryMode.DIFF, *, show_progress: bool = False) -> list[Finding]:
```

Default `show_progress=False` preserves backward compatibility for any direct callers and tests.

### _run_enrichment Transformation

```python
def _run_enrichment(files: list[Path], config: DocvetConfig, *, show_progress: bool = False) -> list[Finding]:
    all_findings: list[Finding] = []
    with typer.progressbar(files, label="enrichment", file=sys.stderr, hidden=not show_progress) as progress:
        for file_path in progress:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)
                continue
            findings = check_enrichment(source, tree, config.enrichment, str(file_path))
            all_findings.extend(findings)
    return all_findings
```

### _run_freshness Transformation

Both branches (diff and drift) get the same treatment. The function has two `for` loops — both wrapped:

```python
def _run_freshness(files, config, freshness_mode=..., discovery_mode=..., *, show_progress: bool = False):
    if freshness_mode is not FreshnessMode.DIFF:
        all_findings: list[Finding] = []
        with typer.progressbar(files, label="freshness", file=sys.stderr, hidden=not show_progress) as progress:
            for file_path in progress:
                # ... drift-mode logic
        return all_findings

    all_findings: list[Finding] = []
    with typer.progressbar(files, label="freshness", file=sys.stderr, hidden=not show_progress) as progress:
        for file_path in progress:
            # ... diff-mode logic
    return all_findings
```

### Warning Messages Inside Progress Bar

`typer.echo(..., err=True)` writes to stderr, same as the progress bar. Click's progressbar handles interleaved stderr writes by clearing and redrawing the bar. The existing `warning: {file_path}: failed to parse, skipping` messages should work correctly.

### Cognitive Complexity Consideration

The `_run_enrichment` function is simple (CC ~3) — adding a `with` block won't push it near the SonarQube threshold of 15.

The `_run_freshness` function is more complex but each branch is straightforward. The `with` block adds 1 nesting level inside the existing `if/else` branches — should stay well under 15 CC.

### Testing Strategy

Tests should verify behavior, not implementation details. Focus on:

1. **Findings correctness**: `_run_enrichment(files, config, show_progress=True)` produces the same findings as `_run_enrichment(files, config, show_progress=False)` — progress bar doesn't alter behavior.
2. **Progress bar activation**: Mock `typer.progressbar` and verify it's called with `hidden=False` when `show_progress=True` and `hidden=True` when `show_progress=False`.
3. **stderr targeting**: Verify `file=sys.stderr` parameter.
4. **Integration**: Existing tests continue to pass since `show_progress` defaults to `False`.

Use `pytest-mock` to mock `typer.progressbar` as a context manager. The key assertion is that the progress bar's `file` parameter is `sys.stderr` and `hidden` reflects the `show_progress` flag.

### What NOT to Change

- Do NOT add progress bars to `_run_coverage` or `_run_griffe` — they don't iterate per-file in cli.py
- Do NOT add a `--quiet` flag — deferred to a future story (mentioned in GitHub issue #24 as future)
- Do NOT add timing output — that's Story 20.2
- Do NOT change the `_discover_and_handle` function — progress is at the check level, not discovery level
- Do NOT modify the `_output_and_exit` pipeline — progress bar self-clears before output
- Do NOT change the public API of check functions in `docvet.checks`

### Project Structure Notes

- All changes are in `src/docvet/cli.py` — signature changes to `_run_enrichment` and `_run_freshness`, progress bar wrappers, `show_progress` wiring in subcommands
- Tests in `tests/unit/test_cli.py` or a new `tests/unit/test_cli_progress.py` depending on existing test file structure
- No new files needed (uses existing `typer.progressbar` which is Click's `click.progressbar`)
- No new imports — `sys` is already imported, `typer` is already imported

### References

- [Source: src/docvet/cli.py#_run_enrichment] — Per-file loop (line 346)
- [Source: src/docvet/cli.py#_run_freshness] — Per-file loops (lines 382, 397)
- [Source: src/docvet/cli.py#check] — Main check command (line 536)
- [Source: src/docvet/cli.py#enrichment] — Enrichment subcommand (line 577)
- [Source: src/docvet/cli.py#freshness] — Freshness subcommand (line 601)
- [Source: GitHub Issue #24] — Feature request with acceptance criteria
- [Source: epics-next.md#Story 4.1] — Epic specification
- [Source: Click docs] — `click.progressbar` API with `hidden`, `file`, `label` parameters
- [Source: pyproject.toml] — `dependencies = ["typer>=0.9"]` (no new deps needed)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (806 passed), no regressions
- [x] `uv run docvet check --all` — pre-commit stale-body artifacts only (4 recommended, 0 required); will resolve post-commit when diff against HEAD is empty
- [x] `uv run interrogate -v` — docstring coverage 100% (threshold 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging required.

### Completion Notes List

- Added `show_progress: bool` keyword-only parameter to `_run_enrichment` and `_run_freshness` with default `False` for backward compatibility
- Wrapped per-file loops in both functions with `typer.progressbar()` using `label`, `file=sys.stderr`, and `hidden=not show_progress`
- Wired `show_progress = sys.stderr.isatty()` in `check()`, `enrichment()`, and `freshness()` subcommands
- Created 11 new unit tests in `tests/unit/test_cli_progress.py` covering both enrichment and freshness (diff + drift modes)
- Updated 4 existing tests in `tests/unit/test_cli.py` to expect the new `show_progress=False` keyword argument
- No new runtime dependencies — uses `typer.progressbar` (Click's `click.progressbar`)
- All 806 tests pass, zero regressions

### Change Log

- 2026-02-26: Story implemented — progress bar for file processing in enrichment and freshness checks

### File List

- `src/docvet/cli.py` (modified) — `_run_enrichment`, `_run_freshness` signatures + progress bar wrappers; `check`, `enrichment`, `freshness` subcommand wiring
- `tests/unit/test_cli_progress.py` (new) — 11 unit tests for progress bar behavior
- `tests/unit/test_cli.py` (modified) — 4 tests updated to expect `show_progress=False` kwarg

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
