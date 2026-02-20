# Story 8.3: CLI Wiring — Unified Output and Exit Code Pipeline

Status: done

## Story

As a developer,
I want `docvet check` and each standalone subcommand to produce unified, formatted output with proper exit codes,
so that I can use docvet in CI pipelines with configurable fail/warn thresholds and export reports.

## Acceptance Criteria

1. **Given** `docvet check` run on a project with findings **When** the command completes **Then** findings from all enabled checks are aggregated into `dict[str, list[Finding]]` and passed to `_output_and_exit` **And** formatted output is printed to stdout with a summary line

2. **Given** `docvet enrichment` (standalone subcommand) run on a project with findings **When** the command completes **Then** findings are passed as `{"enrichment": findings}` to `_output_and_exit` **And** the same formatting/exit code pipeline is used as `docvet check`

3. **Given** `docvet freshness`, `docvet coverage`, `docvet griffe` standalone subcommands **When** each command completes **Then** each produces a single-key `dict[str, list[Finding]]` and calls `_output_and_exit`

4. **Given** `--format markdown` flag **When** any docvet command is run **Then** `format_markdown` is used instead of `format_terminal` for stdout output

5. **Given** `--format terminal` flag (or no `--format` flag) **When** any docvet command is run **Then** `format_terminal` is used for stdout output (terminal is the default)

6. **Given** `--output report.md` flag with findings **When** any docvet command is run **Then** formatted output is written to `report.md` instead of stdout **And** when `--format` is not explicitly set, the file format defaults to markdown

7. **Given** `--format markdown --output report.md` (both flags explicitly set) **When** any docvet command is run with findings **Then** the user's explicit `--format markdown` is respected and markdown output is written to the file

8. **Given** `--output report.md` flag with zero findings **When** any docvet command is run **Then** `write_report` is not called (no file is created) **And** if verbose, `"No findings.\n"` is printed to stdout

9. **Given** `--verbose` flag with findings **When** any docvet command is run **Then** `format_verbose_header` output is printed to stderr (not stdout) **And** findings are printed to stdout

10. **Given** `--verbose` flag with zero findings **When** any docvet command is run **Then** `format_verbose_header` output is printed to stderr **And** `"No findings.\n"` is printed to stdout

11. **Given** `config.fail_on = ["enrichment"]` and enrichment has findings **When** `docvet check` completes **Then** the exit code is 1

12. **Given** `config.fail_on = ["enrichment"]` and enrichment has zero findings **When** `docvet check` completes **Then** the exit code is 0 (even if other checks have findings)

13. **Given** `config.fail_on = []` (default config -- all checks advisory) **When** `docvet check` completes with findings **Then** the exit code is 0

14. **Given** `NO_COLOR` environment variable is set (any non-empty value) **When** terminal format output is produced **Then** ANSI codes are suppressed (`no_color=True` passed to `format_terminal`)

15. **Given** stdout is not a TTY (e.g., piped to a file) **When** terminal format output is produced **Then** ANSI codes are suppressed

16. **Given** `--output` flag is set **When** terminal format is used for file output **Then** ANSI codes are suppressed (forced `no_color=True`)

17. **Given** `docvet enrichment` with `config.fail_on = ["freshness"]` **When** the command completes **Then** exit code is 0 (enrichment is not in fail_on; the single-key dict only contains "enrichment")

## Tasks / Subtasks

- [x] Task 1: Add `_output_and_exit` helper function to `cli.py` (AC: 1-17)
  - [x] 1.1 Add imports from `docvet.reporting` (5 functions)
  - [x] 1.2 Add `import os` and `import sys` for `NO_COLOR` env var and `isatty()` checks
  - [x] 1.3 Implement `_output_and_exit(ctx, findings_by_check, config, file_count, checks)` with 8-step internal flow
- [x] Task 2: Refactor `check()` subcommand to use `_output_and_exit` (AC: 1, 4-16)
  - [x] 2.1 Remove `_print_global_context(ctx)` call (superseded by `_output_and_exit` verbose handling)
  - [x] 2.2 Aggregate findings into `dict[str, list[Finding]]` with keys `"enrichment"`, `"freshness"`, `"coverage"`, `"griffe"`
  - [x] 2.3 Replace temporary echo loop with `_output_and_exit` call
- [x] Task 3: Refactor `enrichment()` subcommand (AC: 2, 4-17)
  - [x] 3.1 Remove `_print_global_context(ctx)` call
  - [x] 3.2 Replace echo loop with `_output_and_exit(ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"])`
- [x] Task 4: Refactor `freshness()` subcommand (AC: 3, 4-16)
  - [x] 4.1 Remove `_print_global_context(ctx)` call
  - [x] 4.2 Replace echo loop with `_output_and_exit(ctx, {"freshness": findings}, config, len(discovered), ["freshness"])`
- [x] Task 5: Refactor `coverage()` subcommand (AC: 3, 4-16)
  - [x] 5.1 Remove `_print_global_context(ctx)` call
  - [x] 5.2 Replace echo loop with `_output_and_exit(ctx, {"coverage": findings}, config, len(discovered), ["coverage"])`
- [x] Task 6: Refactor `griffe()` subcommand (AC: 3, 4-16)
  - [x] 6.1 Remove `_print_global_context(ctx)` call
  - [x] 6.2 Replace echo loop with `_output_and_exit(ctx, {"griffe": findings}, config, len(discovered), ["griffe"])`
- [x] Task 7: Add `_output_and_exit` unit tests in `tests/unit/test_cli.py` (AC: 1-17)
  - [x] 7.1 Test terminal format is default when `--format` not set
  - [x] 7.2 Test `--format markdown` selects `format_markdown`
  - [x] 7.3 Test `--output` writes file via `write_report` and suppresses stdout
  - [x] 7.4 Test `--output` with `--format` not set defaults to markdown for file
  - [x] 7.5 Test `--output` with explicit `--format terminal` writes terminal format to file
  - [x] 7.6 Test `--output` with zero findings skips `write_report` (no file created)
  - [x] 7.6b Test `--output` + `--verbose` + zero findings: no file created, header to stderr, "No findings.\n" to stdout
  - [x] 7.7 Test `--verbose` with findings prints header to stderr, findings to stdout
  - [x] 7.8 Test `--verbose` with zero findings prints header to stderr, "No findings.\n" to stdout
  - [x] 7.9 Test exit code 1 when fail_on check has findings
  - [x] 7.10 Test exit code 0 when fail_on check has no findings
  - [x] 7.11 Test exit code 0 when fail_on is empty (advisory mode)
  - [x] 7.12 Test `NO_COLOR` env var suppresses ANSI
  - [x] 7.13 Test non-TTY stdout suppresses ANSI
  - [x] 7.14 Test `--output` flag forces `no_color=True`
  - [x] 7.15 Test standalone subcommand exit code when check not in fail_on
- [x] Task 8: Update existing subcommand integration tests (AC: 1-3)
  - [x] 8.1 Verify `check` command produces formatted output (not raw echo)
  - [x] 8.2 Verify `enrichment` subcommand calls `_output_and_exit` with `{"enrichment": findings}`
  - [x] 8.3 Verify `freshness` subcommand calls `_output_and_exit` with `{"freshness": findings}`
  - [x] 8.4 Verify `coverage` subcommand calls `_output_and_exit` with `{"coverage": findings}`
  - [x] 8.5 Verify `griffe` subcommand calls `_output_and_exit` with `{"griffe": findings}`
- [x] Task 9: Remove dead `_print_global_context` helper (AC: 9-10)
  - [x] 9.1 Delete `_print_global_context` function from `cli.py`
  - [x] 9.2 Remove or update any tests that assert `_print_global_context` behavior

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_check_when_invoked_runs_all_checks_in_order` | pass |
| 2 | `test_terminal_format_is_default_when_format_not_set` (via enrichment single-key dict) | pass |
| 3 | `test_standalone_subcommand_exit_code_when_check_not_in_fail_on` (freshness/coverage/griffe use same pattern) | pass |
| 4 | `test_format_markdown_selects_format_markdown` | pass |
| 5 | `test_terminal_format_is_default_when_format_not_set` | pass |
| 6 | `test_output_writes_file_via_write_report`, `test_output_without_format_defaults_to_markdown_for_file` | pass |
| 7 | `test_output_with_explicit_format_terminal_writes_terminal_to_file` | pass |
| 8 | `test_output_with_zero_findings_skips_write_report` | pass |
| 9 | `test_verbose_with_findings_prints_header_to_stderr` | pass |
| 10 | `test_verbose_with_zero_findings_prints_header_stderr_no_findings_stdout` | pass |
| 11 | `test_exit_code_1_when_fail_on_check_has_findings` | pass |
| 12 | `test_exit_code_0_when_fail_on_check_has_no_findings` | pass |
| 13 | `test_exit_code_0_when_fail_on_is_empty` | pass |
| 14 | `test_no_color_env_var_suppresses_ansi` | pass |
| 15 | `test_non_tty_stdout_suppresses_ansi` | pass |
| 16 | `test_output_flag_forces_no_color_true` | pass |
| 17 | `test_standalone_subcommand_exit_code_when_check_not_in_fail_on` | pass |

## Dev Notes

### Architecture: `_output_and_exit` Internal Flow (Decision 5)

The core of this story is a single `_output_and_exit` helper in `cli.py`. Per architecture Decision 5, it follows this 8-step sequence:

```
1. Resolve no_color: NO_COLOR env var OR not sys.stdout.isatty() OR --output flag set
2. Flatten findings_by_check values into all_findings: list[Finding]
3. If verbose: print format_verbose_header(file_count, checks) to stderr
4. Resolve format and produce formatted string:
   - use --format if set, else "terminal" for stdout / "markdown" for --output
   - call format_terminal(all_findings, no_color=no_color) or format_markdown(all_findings)
5. If --output and all_findings: call write_report(all_findings, output, fmt=resolved_format)
6. Else if all_findings: print formatted output to stdout
7. If verbose and not all_findings: print "No findings.\n" to stdout
8. raise typer.Exit(determine_exit_code(findings_by_check, config))
```

**Signature:**
```python
def _output_and_exit(
    ctx: typer.Context,
    findings_by_check: dict[str, list[Finding]],
    config: DocvetConfig,
    file_count: int,
    checks: list[str],
) -> None:
```

### `no_color` Resolution Logic

Three conditions trigger `no_color=True`:
1. `NO_COLOR` env var set to any non-empty value (`os.environ.get("NO_COLOR", "") != ""`)
2. `sys.stdout.isatty()` returns `False` (piped output)
3. `--output` flag is set (file output always strips ANSI)

### Format Resolution Logic

- `--output` set, `--format` NOT set: default to `"markdown"`
- `--output` set, `--format` explicitly set: respect user's choice
- `--output` NOT set: use `--format` or default to `"terminal"`

### Removing `_print_global_context`

The existing `_print_global_context` helper (cli.py:98-111) echoes raw option values (`verbose: enabled`, `format: ...`, `output: ...`) to stderr. With `_output_and_exit`, verbose output is handled by `format_verbose_header` (richer, consistent format to stderr), and the format/output acknowledgments become redundant since the pipeline acts on them directly. Remove `_print_global_context` and all 5 call sites in subcommands to avoid duplicate stderr output.

### Files to Modify

| File | Change |
|------|--------|
| `src/docvet/cli.py` | Add `_output_and_exit`, remove `_print_global_context`, refactor 5 subcommands, add `os`/`sys` imports, add reporting imports |
| `tests/unit/test_cli.py` | Add `_output_and_exit` tests (~17 tests), update subcommand tests, remove `_print_global_context` tests |

### Files NOT to Create or Modify

- `src/docvet/reporting.py` -- already complete (Story 8.2)
- `src/docvet/config.py` -- already has overlap warning (Story 8.1)
- `tests/unit/test_reporting.py` -- already complete (Story 8.2)
- `tests/conftest.py` -- `make_finding` fixture already exists (Story 8.1)

### Import Pattern (cli.py)

Add at top of `cli.py` alongside existing imports:
```python
import os
import sys

from docvet.reporting import (
    determine_exit_code,
    format_markdown,
    format_terminal,
    format_verbose_header,
    write_report,
)
```

### Current Bridge Pattern to Replace

All 5 subcommands currently have temporary echo loops from Story 8.1:
```python
# CURRENT (to be replaced):
for f in findings:
    typer.echo(f"{f.file}:{f.line}: {f.rule} {f.message}")
```

Replace with:
```python
# NEW:
_output_and_exit(ctx, {"enrichment": findings}, config, len(discovered), ["enrichment"])
```

For `check()`, aggregate all findings:
```python
findings_by_check = {
    "enrichment": enrichment_findings,
    "freshness": freshness_findings,
    "coverage": coverage_findings,
    "griffe": griffe_findings,
}
_output_and_exit(
    ctx,
    findings_by_check,
    config,
    len(discovered),
    ["enrichment", "freshness", "coverage", "griffe"],
)
```

### Testing Strategy for `_output_and_exit`

Per architecture Pattern 7:
- **Mock** `format_terminal`, `format_markdown`, `determine_exit_code` from `reporting`
- **Assert** correct formatter called based on `--format`
- **Assert** verbose header printed to stderr via `capsys.readouterr().err`
- **Assert** `typer.Exit` raised with correct code
- **Do NOT** test formatting logic here -- that's `test_reporting.py`'s job
- Use `monkeypatch` for `NO_COLOR` env var and `sys.stdout.isatty()`
- Use `make_finding` fixture from `tests/conftest.py`

### Anti-Patterns to Avoid

- Never inline post-check logic in individual subcommands -- use `_output_and_exit`
- Never test formatting logic via `_output_and_exit` -- test reporting functions directly
- Never call `_output_and_exit` without a complete `findings_by_check` dict
- Never add `verbose` parameter to `format_terminal` -- verbose concerns handled by `_output_and_exit`
- `format_terminal` and `format_markdown` are pure functions (no I/O, no env inspection)

### Previous Story Intelligence

**From Story 8.1 (CLI refactor):**
- All `_run_*` functions now return `list[Finding]` -- verified working
- Temporary echo loops in subcommands are the bridge pattern to replace
- `make_finding` fixture available in `tests/conftest.py`
- Config overlap warning already in `config.py` with tests
- 634 total tests passing

**From Story 8.2 (Core reporting):**
- `reporting.py` is complete with 5 public functions + 1 private helper
- 34 tests in `test_reporting.py` covering all 22 ACs
- `write_report` raises `FileNotFoundError` on missing parent dir
- `format_terminal` and `format_markdown` return `""` for empty findings
- `determine_exit_code` checks `config.fail_on` against findings_by_check keys
- 668 total tests passing

### Git Intelligence

Recent commit pattern: "core function then CLI wiring" cadence. Each check module gets a core implementation PR followed by a CLI integration PR. This story follows the same pattern -- wiring `reporting.py` (Story 8.2) into `cli.py`.

Last 5 commits show:
- `e5bc0dd` feat(reporting): add core reporting functions module (#47)
- `6fd717a` refactor(cli): return list[Finding] from check runners (#46)
- Consistent patterns: single production file + single test file per PR

### Project Structure Notes

- All changes within `src/docvet/cli.py` and `tests/unit/test_cli.py`
- No new files needed -- extending existing modules
- Import pattern matches established convention (individual function imports)
- `_output_and_exit` placed in helpers section of `cli.py` (after `_discover_and_handle`, before private check runners)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] -- `_output_and_exit` signature and 8-step flow
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern 7] -- Test patterns for `_output_and_exit`
- [Source: _bmad-output/planning-artifacts/architecture.md#FR101a-FR101b] -- NO_COLOR and non-TTY suppression
- [Source: _bmad-output/planning-artifacts/epics.md#Story 8.3] -- 17 acceptance criteria
- [Source: _bmad-output/implementation-artifacts/8-1-cli-refactor-return-findings-from-check-runners.md] -- Bridge pattern context
- [Source: _bmad-output/implementation-artifacts/8-2-core-reporting-functions.md] -- Reporting API surface

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None required — clean implementation with no debugging needed.

### Completion Notes List

- Implemented `_output_and_exit` with 8-step flow matching architecture Decision 5
- `typer.Exit` is actually `click.exceptions.Exit` (inherits from `RuntimeError`, not `SystemExit`); exit code accessed via `.exit_code` attribute
- All 5 subcommands refactored from bridge echo loops to `_output_and_exit` calls
- `_print_global_context` removed (function + 5 call sites + 3 tests updated)
- 16 new `_output_and_exit` unit tests in `TestOutputAndExit` class
- Existing subcommand tests still pass because `format_terminal` output is a superset of old echo format
- 678 total tests passing (was 662 before story, +16 new)

### File List

| File | Change |
|------|--------|
| `src/docvet/cli.py` | Added `os`, `sys` imports; added 5 reporting imports; added `_output_and_exit` (lines 144-206); removed `_print_global_context`; refactored 5 subcommands |
| `tests/unit/test_cli.py` | Added `TestOutputAndExit` class with 16 tests; updated 3 `_print_global_context` tests to test new behavior |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Updated story status |
