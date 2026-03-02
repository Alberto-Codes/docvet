# Story 28.2: CLI Wiring and Pipeline Integration

Status: review
Branch: `feat/presence-28-2-cli-wiring-and-pipeline-integration`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/243

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer using the CLI**,
I want to run `docvet presence` as a standalone subcommand and have presence checks included in `docvet check`,
So that I can enforce docstring presence through the same CLI workflow I use for all other checks.

## Acceptance Criteria

1. **Given** a user runs `docvet presence` **When** the command completes **Then** presence check runs on discovered files and outputs findings in the configured format (terminal/markdown/json) **And** exit code follows `fail_on` config (non-zero only if `"presence"` is in `fail_on` and findings exist -- consistent with all other standalone subcommands)

2. **Given** a user runs `docvet check` (or `docvet check --all`) **When** the check pipeline executes **Then** presence runs **first** in the pipeline (before enrichment, freshness, coverage, griffe) **And** findings from all checks are combined in the output

3. **Given** a symbol has no docstring **When** both presence and enrichment checks run via `docvet check` **Then** only a `missing-docstring` finding is produced (presence) **And** enrichment does NOT produce additional findings for that symbol (regression guard -- enrichment already skips undocumented symbols, no enrichment code change needed)

4. **Given** `[tool.docvet.presence]` has `min-coverage = 95.0` in pyproject.toml **When** aggregate coverage across all processed files is below 95% **Then** the exit code is non-zero **And** default output includes coverage in summary: "Vetted N files [...] -- X findings, 87.0% coverage. (0.3s)" **And** verbose output includes full detail: "Docstring coverage: 87/100 symbols (87.0%) -- below 95.0% threshold"

5. **Given** `[tool.docvet.presence]` has `min-coverage = 95.0` **When** aggregate coverage is at or above 95% **Then** the exit code is zero (assuming no other findings) **And** default output includes "96.0% coverage" in the summary line **And** verbose output includes "Docstring coverage: 96/100 symbols (96.0%) -- passes 95.0% threshold"

6. **Given** a user runs `docvet check --quiet` **When** presence findings or coverage threshold violations exist **Then** no coverage information is printed (quiet = exit code only, consistent with all other checks)

7. **Given** a user runs `docvet check --format json` **When** presence findings exist **Then** the JSON output includes presence findings with `rule`, `category`, `file`, `line`, `symbol`, `message` fields **And** a top-level `presence_coverage` object with `documented`, `total`, `percentage`, `threshold`, `passed` fields

8. **Given** `[tool.docvet.presence]` has `enabled = false` **When** `docvet check` runs **Then** presence check is skipped entirely

## Tasks / Subtasks

- [x] Task 1: Implement `_run_presence()` in cli.py (AC: 1, 2)
  - [x] 1.1: Add import of `check_presence` from `docvet.checks.presence`
  - [x] 1.2: Add import of `PresenceStats` from `docvet.checks.presence`
  - [x] 1.3: Implement `_run_presence(files, config, *, show_progress=False)` returning `tuple[list[Finding], PresenceStats]`
  - [x] 1.4: Iterate files with `typer.progressbar(label="presence")`, read source, parse AST
  - [x] 1.5: Call `check_presence(source, str(file_path), config.presence)` per file, aggregate findings and sum stats
  - [x] 1.6: Catch `SyntaxError` per file, print warning, continue (same as `_run_enrichment`)
  - [x] 1.7: Return `(all_findings, PresenceStats(documented=total_documented, total=total_total))`

- [x] Task 2: Add `presence()` subcommand (AC: 1, 4, 5, 6)
  - [x] 2.1: Define `@app.command() def presence(...)` following enrichment subcommand pattern
  - [x] 2.2: Standard discovery/verbosity setup (merge file args, resolve discovery mode, etc.)
  - [x] 2.3: Call `_run_presence(discovered, config, show_progress=sys.stderr.isatty())`
  - [x] 2.4: Print coverage summary on stderr (default/verbose), suppress on quiet
  - [x] 2.5: Call `_output_and_exit` with `{"presence": findings}` and presence_stats

- [x] Task 3: Integrate into `check()` command (AC: 2, 3, 8)
  - [x] 3.1: Add presence check block FIRST in the pipeline (before enrichment), gated on `config.presence.enabled`
  - [x] 3.2: Add timing block with verbose logging: `f"presence: {file_count} files in {elapsed:.1f}s\n"`
  - [x] 3.3: Add "presence" to `checks` list when enabled
  - [x] 3.4: Add presence findings to `findings_by_check` dict
  - [x] 3.5: Pass aggregate stats through to `_output_and_exit` and `format_summary`

- [x] Task 4: Update `format_summary` in reporting.py (AC: 4, 5)
  - [x] 4.1: Add optional `coverage_pct: float | None = None` parameter
  - [x] 4.2: Append `, X.X% coverage` to the detail string when `coverage_pct is not None`

- [x] Task 5: Update `format_json` in reporting.py (AC: 7)
  - [x] 5.1: Add optional `presence_stats: PresenceStats | None = None` and `min_coverage: float = 0.0` parameters
  - [x] 5.2: When `presence_stats is not None`, add `presence_coverage` object to JSON with: `documented`, `total`, `percentage`, `threshold`, `passed`

- [x] Task 6: Update `determine_exit_code` in reporting.py (AC: 4, 5)
  - [x] 6.1: Add optional `presence_stats: PresenceStats | None = None` keyword parameter (no separate `presence_config` — use `config.presence.min_coverage` from the existing `DocvetConfig` param)
  - [x] 6.2: After existing `fail_on` loop, check if `config.presence.min_coverage > 0.0` and coverage is below threshold; return 1 if below

- [x] Task 7: Update `_output_and_exit` in cli.py (AC: 4, 5, 6, 7)
  - [x] 7.1: Add optional `presence_stats: PresenceStats | None = None` keyword parameter
  - [x] 7.2: Pass stats through to `_emit_findings` (for JSON) and `determine_exit_code`
  - [x] 7.3: Print verbose coverage line on stderr when verbose and not quiet and stats provided

- [x] Task 8: Update `_emit_findings` in cli.py (AC: 7)
  - [x] 8.1: Add optional `presence_stats` and `min_coverage` parameters
  - [x] 8.2: Pass through to `format_json` when format is "json"

- [x] Task 9: Update config defaults (AC: 8)
  - [x] 9.1: Add `"presence"` to `DocvetConfig.warn_on` default list
  - [x] 9.2: Add `_run_presence` to module-level autouse fixture mock in `test_cli.py`

- [x] Task 10: Write comprehensive unit tests (AC: all)
  - [x] 10.1: `_run_presence` — returns findings and aggregated stats across files
  - [x] 10.2: `_run_presence` — catches SyntaxError and continues
  - [x] 10.3: `_run_presence` — empty file list returns empty findings and zero stats
  - [x] 10.4: `presence()` subcommand — outputs findings and summary line
  - [x] 10.5: `presence()` subcommand — exit code 0 when no findings
  - [x] 10.6: `presence()` subcommand — verbose shows timing
  - [x] 10.7: `presence()` subcommand — quiet suppresses summary
  - [x] 10.8: `check()` — presence runs when enabled, adds to checks list
  - [x] 10.9: `check()` — presence disabled skips the check
  - [x] 10.10: `check()` — summary includes coverage percentage
  - [x] 10.11: Coverage threshold — exit code 1 when below min_coverage
  - [x] 10.12: Coverage threshold — exit code 0 when at or above min_coverage
  - [x] 10.13: Coverage threshold — no enforcement when min_coverage = 0.0
  - [x] 10.14: JSON — includes presence_coverage object with all 5 fields
  - [x] 10.15: JSON — presence_coverage.passed reflects threshold comparison
  - [x] 10.16: JSON — omits presence_coverage when no presence stats
  - [x] 10.17: Summary line — includes "X.X% coverage" when presence runs
  - [x] 10.18: Summary line — no coverage when presence not in checks
  - [x] 10.19: Verbose — shows "Docstring coverage: N/M symbols" line
  - [x] 10.20: No double-counting regression guard — call BOTH `check_presence` and `check_enrichment` on same source with undocumented symbols, verify enrichment returns zero findings for those symbols (unit test in `test_enrichment.py` or `test_presence.py`, NOT a CLI mock test)
  - [x] 10.21: `determine_exit_code` — returns 1 when coverage below threshold
  - [x] 10.22: `determine_exit_code` — returns 0 when coverage meets threshold
  - [x] 10.23: Config default — "presence" in default warn_on
  - [x] 10.24: `_run_presence` mock added to autouse fixture (no existing test regression)
  - [x] 10.25: Coverage threshold boundary — exact 100.0% coverage with `min_coverage=100.0` passes (edge: `>=` not `>`)
  - [x] 10.26: Coverage threshold boundary — float precision edge case (`min_coverage=95.0`, actual 94.99999 vs 95.00001)
  - [x] 10.27: JSON — `presence_coverage` present even when zero findings and 100% coverage (stats exist = key exists)
  - [x] 10.28: `_run_presence` — all files have SyntaxError returns `PresenceStats(0, 0)` and coverage = 100.0%

- [x] Task 11: Run quality gates
  - [x] 11.1: `uv run ruff check .` -- zero lint violations
  - [x] 11.2: `uv run ruff format --check .` -- zero format issues
  - [x] 11.3: `uv run ty check` -- zero type errors
  - [x] 11.4: `uv run pytest` -- all tests pass, no regressions (1087 total)
  - [x] 11.5: `uv run docvet check --all` -- zero docvet findings
  - [x] 11.6: Run `analyze_code_snippet` on modified modules (background)

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| AC1: `docvet presence` subcommand outputs findings, respects format/exit code | `TestPresenceSubcommand::test_outputs_findings_and_summary` (10.4), `test_exit_code_0_when_no_findings` (10.5), `test_verbose_shows_timing` (10.6), `test_quiet_suppresses_summary` (10.7) | Pass |
| AC2: `docvet check` runs presence first in pipeline | `TestPresenceInCheck::test_presence_runs_when_enabled` (10.8), `test_summary_includes_coverage_percentage` (10.10) | Pass |
| AC3: No double-counting (presence + enrichment) | `TestNoDoubleCounting::test_enrichment_skips_undocumented_symbols` (10.20) in `test_presence.py` | Pass |
| AC4: Coverage threshold enforcement — below threshold | `TestCoverageThreshold::test_exit_code_1_when_below_min_coverage` (10.11), `TestPresenceVerbose::test_verbose_shows_below_threshold` (10.19), `TestDetermineExitCodeWithPresence::test_returns_1_when_coverage_below_threshold` (10.21), `TestFormatSummaryWithCoverage::test_coverage_pct_appended_when_provided` (10.17) | Pass |
| AC5: Coverage threshold enforcement — at or above threshold | `TestCoverageThreshold::test_exit_code_0_when_at_or_above_min_coverage` (10.12), `test_no_enforcement_when_min_coverage_zero` (10.13), `test_exact_100_percent_passes_with_threshold_100` (10.25), `TestPresenceVerbose::test_verbose_shows_passes_threshold` (10.19), `TestDetermineExitCodeWithPresence::test_returns_0_when_coverage_meets_threshold` (10.22) | Pass |
| AC6: `--quiet` suppresses coverage output | `TestPresenceSubcommand::test_quiet_suppresses_summary` (10.7), `TestPresenceVerbose::test_verbose_no_threshold_shows_percentage_only` (10.19) | Pass |
| AC7: JSON output includes `presence_coverage` object | `TestFormatJsonWithPresence::test_includes_presence_coverage_object` (10.14), `test_presence_coverage_passed_true_when_above` (10.15), `test_omits_presence_coverage_when_no_stats` (10.16), `test_presence_coverage_present_with_zero_findings_and_full_coverage` (10.27) | Pass |
| AC8: `enabled = false` skips presence entirely | `TestPresenceInCheck::test_presence_disabled_skips_the_check` (10.9), `test_summary_no_coverage_when_presence_disabled` (10.18) | Pass |

## Dev Notes

### Architecture Patterns

**Return type divergence:** `_run_presence` returns `tuple[list[Finding], PresenceStats]` unlike other `_run_*` functions which return `list[Finding]`. This is because `check_presence` already returns per-file stats that must be aggregated. The CLI layer sums `documented` and `total` across all files to compute aggregate coverage percentage.

**Stats aggregation in `_run_presence`:**

```python
total_documented = 0
total_total = 0
all_findings: list[Finding] = []

for file_path in files:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    findings, stats = check_presence(source, str(file_path), config.presence)
    all_findings.extend(findings)
    total_documented += stats.documented
    total_total += stats.total

return all_findings, PresenceStats(documented=total_documented, total=total_total)
```

**Coverage percentage computation:** `(stats.documented / stats.total * 100.0) if stats.total > 0 else 100.0`. Zero total symbols = 100% coverage (nothing to check).

**Pipeline order change:** In `check()`, presence runs FIRST:
```
presence → enrichment → freshness → coverage → griffe
```
This is the natural order: detect missing docstrings first, then check quality of existing ones.

**No double-counting verification (AC 3):** Enrichment already skips undocumented symbols via `if not symbol.docstring: continue` at `src/docvet/checks/enrichment.py:1354`. No enrichment code changes needed. Verify with a unit-level regression test that calls both `check_presence` and `check_enrichment` on the same source — `check_enrichment` must produce zero findings for undocumented symbols. Do NOT test this at the CLI mock level (mocking both `_run_*` functions proves nothing about actual behavior).

### CLI Wiring Pattern Reference

**Subcommand template** (copy from `enrichment()` at cli.py ~line 771):

**CRITICAL: `verbose` and `quiet` are NOT module-level type aliases.** Only `StagedOption`, `AllOption`, `FilesOption`, `FilesArgument`, and `ConfigOption` are module-level `Annotated` aliases (lines 131-145). The `verbose` and `quiet` parameters are defined inline with `Annotated[bool, typer.Option(...)]` in each subcommand signature. Copy the exact inline definition from an existing subcommand like `enrichment()`.

```python
@app.command()
def presence(
    ctx: typer.Context,
    files_pos: FilesArgument = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", ...)] = False,  # inline, not a module alias
    quiet: Annotated[bool, typer.Option("--quiet", "-q", ...)] = False,  # inline, not a module alias
    staged: StagedOption = False,
    all_files: AllOption = False,
    files: FilesOption = None,
) -> None:
    """Check for missing docstrings."""
    files_pos_or_opt = _merge_file_args(files_pos, files)
    discovery_mode = _resolve_discovery_mode(staged, all_files, files_pos_or_opt)
    # ... standard verbose/quiet/discovery setup ...
    findings, agg_stats = _run_presence(discovered, config, show_progress=...)
    coverage_pct = (agg_stats.documented / agg_stats.total * 100.0) if agg_stats.total > 0 else 100.0
    if not quiet:
        sys.stderr.write(format_summary(..., coverage_pct=coverage_pct))
    _output_and_exit(ctx, {"presence": findings}, config, ..., presence_stats=agg_stats)
```

**check() integration template** (insert BEFORE enrichment block, ~line 713):
```python
# Presence (runs first — skip if disabled)
presence_findings: list[Finding] = []
agg_stats: PresenceStats | None = None
if config.presence.enabled:
    start = time.perf_counter()
    presence_findings, agg_stats = _run_presence(discovered, config, show_progress=show_progress)
    elapsed = time.perf_counter() - start
    if verbose and not quiet:
        sys.stderr.write(f"presence: {file_count} files in {elapsed:.1f}s\n")
```

### Reporting Changes

**`format_summary` signature change:**
```python
def format_summary(
    file_count: int,
    checks: Sequence[str],
    findings: list[Finding],
    elapsed: float,
    *,
    coverage_pct: float | None = None,
) -> str:
```

When `coverage_pct is not None`, append `, {coverage_pct:.1f}% coverage` to the `detail` string:
- Zero findings: `"no findings, 96.0% coverage"`
- With findings: `"2 findings (2 required, 0 recommended), 87.0% coverage"`

**`format_json` signature change:**
```python
def format_json(
    findings: list[Finding],
    file_count: int,
    *,
    presence_stats: PresenceStats | None = None,
    min_coverage: float = 0.0,
) -> str:
```

When `presence_stats is not None`, add top-level key:
```json
{
  "findings": [...],
  "summary": {...},
  "presence_coverage": {
    "documented": 87,
    "total": 100,
    "percentage": 87.0,
    "threshold": 95.0,
    "passed": false
  }
}
```

**`determine_exit_code` signature change** (no separate `presence_config` — `config.presence` is already accessible):
```python
def determine_exit_code(
    findings_by_check: dict[str, list[Finding]],
    config: DocvetConfig,
    *,
    presence_stats: PresenceStats | None = None,
) -> int:
```

After existing `fail_on` loop, add coverage threshold check:
```python
if presence_stats is not None and config.presence.min_coverage > 0.0:
    pct = (presence_stats.documented / presence_stats.total * 100.0) if presence_stats.total > 0 else 100.0
    if pct < config.presence.min_coverage:
        return 1
```

**Verbose coverage line** (printed by `_output_and_exit` on stderr):
```python
if verbose and not quiet and presence_stats is not None:
    pct = ...
    threshold = config.presence.min_coverage
    if threshold > 0.0:
        status = "passes" if pct >= threshold else "below"
        sys.stderr.write(
            f"Docstring coverage: {presence_stats.documented}/{presence_stats.total} "
            f"symbols ({pct:.1f}%) \u2014 {status} {threshold:.1f}% threshold\n"
        )
    else:
        sys.stderr.write(
            f"Docstring coverage: {presence_stats.documented}/{presence_stats.total} "
            f"symbols ({pct:.1f}%)\n"
        )
```

### Config Changes

**`DocvetConfig.warn_on` default** (config.py ~line 209): Add `"presence"` to the default list. Current default: `["freshness", "enrichment", "griffe", "coverage"]`. New: `["presence", "freshness", "enrichment", "griffe", "coverage"]`. This was flagged as L1 in Story 28.1 code review and explicitly deferred to 28.2.

### Testing Strategy

**Test file:** Add tests to existing `tests/unit/test_cli.py` and `tests/unit/test_reporting.py`. No new test files needed.

**Autouse fixture update:** Add `mocker.patch("docvet.cli._run_presence", return_value=([], PresenceStats(documented=0, total=0)))` to the module-level `_mock_config_and_discovery` fixture. This is CRITICAL — without it, existing tests will break because `_run_presence` returns a tuple not a list.

**Test input pattern:** Use `make_finding()` factory with `rule="missing-docstring"`, `category="required"` for presence findings. Use `PresenceStats(documented=X, total=Y)` for stats.

**Key test patterns:**
- Mock `_run_presence` to return specific findings + stats
- Mock `check_presence` for `_run_presence` unit tests
- Use `runner.invoke(app, ["presence", "--all"])` for subcommand tests
- Use `runner.invoke(app, ["check", "--all"])` for integration tests
- Assert exit code, stdout output, stderr output (summary/verbose lines)
- Use `capsys.readouterr()` in `TestOutputAndExit` class tests

**Regression guard (AC 3):** Write a unit-level test (NOT a CLI mock test) that calls both `check_presence` and `check_enrichment` on the same source containing undocumented symbols. Verify `check_enrichment` produces zero findings for those undocumented symbols (it skips `symbol.docstring is None` at `enrichment.py:1354`). A CLI-level test that mocks both `_run_*` functions proves nothing about actual double-counting behavior.

**Output assertion gotcha:** The summary line uses `\u2014` (em-dash) in the actual code, NOT `--` (double hyphen) as written in the AC text. Test assertions must match the actual code output: `"\u2014"` or `chr(8212)`. The AC examples use `--` for readability only.

### Previous Story Intelligence (Story 28.1)

**Key learnings from 28.1:**
- Category must be `"required"` (not `"presence"` as epic AC says) — `Finding.__post_init__` validates against `Literal["required", "recommended"]`
- `get_documented_symbols` returns ALL symbols despite its name
- `ast.parse("")` returns Module with empty body — `check_presence` has early return guard
- `_parse_presence` type narrowing: use positive `isinstance` branch for `float()` call (ty limitation)
- `PresenceStats` already exported from `presence.py` and re-exported through `checks/__init__.py`

**Code review findings carried forward from 28.1:**
- L1: `"presence"` not in default `warn_on` — address in Task 9
- M3: Progressive build pattern accepted — docs deferred to 28.3

### Git Intelligence

Recent commits show:
- `a48edd3 feat(presence): add core presence detection and configuration (#240)` — Story 28.1 merged
- `53eafee ci(release): sync uv.lock after release-please version bump (#241)` — latest on main
- `5778ff8 test(exports): add docvet.lsp to module coverage in test_exports.py (#237)` — exports updated
- `83575c5 chore(deps): add dependency health gates and drop interrogate (#235)` — interrogate dropped from CI

**CRITICAL: interrogate dropped** (PR #235). The CI gate `interrogate -v` was removed. However, the quality gates checklist still lists `interrogate -v`. Since docvet's presence check is the replacement for interrogate, this story makes that replacement concrete. The quality gates checklist should continue listing interrogate (`uv run interrogate -v`) since the project still has it as a dev dependency — but verify this during implementation.

### Project Structure Notes

- Modified files: `src/docvet/cli.py`, `src/docvet/reporting.py`, `src/docvet/config.py` (warn_on default)
- Modified test files: `tests/unit/test_cli.py`, `tests/unit/test_reporting.py`
- No new files needed
- No structural conflicts with existing codebase

### References

- [Source: `src/docvet/cli.py:425-570`] -- `_run_enrichment`, `_run_freshness`, `_run_coverage`, `_run_griffe` patterns
- [Source: `src/docvet/cli.py:664-768`] -- `check()` command with per-check timing and pipeline assembly
- [Source: `src/docvet/cli.py:771-826`] -- `enrichment()` subcommand template
- [Source: `src/docvet/cli.py:293-353`] -- `_output_and_exit()` flow
- [Source: `src/docvet/reporting.py:149-201`] -- `format_json()` JSON schema
- [Source: `src/docvet/reporting.py:204-254`] -- `format_summary()` format string
- [Source: `src/docvet/reporting.py:303-318`] -- `determine_exit_code()` exit logic
- [Source: `src/docvet/checks/presence.py:86-152`] -- `check_presence()` signature and return type
- [Source: `src/docvet/checks/presence.py:36-53`] -- `PresenceStats` dataclass
- [Source: `src/docvet/checks/enrichment.py:1354`] -- Enrichment skip: `if not symbol.docstring: continue`
- [Source: `src/docvet/config.py:129-167`] -- `PresenceConfig` fields and defaults
- [Source: `src/docvet/config.py:208-216`] -- `DocvetConfig.warn_on` default list
- [Source: `_bmad-output/planning-artifacts/epics-presence-mcp.md:157-212`] -- Story 28.2 ACs and implementation notes
- [Source: `_bmad-output/implementation-artifacts/28-1-core-presence-detection-and-configuration.md`] -- Previous story learnings

### Documentation Impact

<!-- REQUIRED: Every story must identify affected docs pages or explicitly acknowledge "None". Do NOT leave blank or use vague language like "update docs if needed". -->

- Pages: None -- no user-facing documentation changes in this story
- Nature of update: N/A -- Story 28.2 adds CLI wiring. Documentation (check page, rule page, CLI reference, configuration reference, migration guide) is Story 28.3's scope per the progressive build pattern established in 28.1.

<!-- Decision tree for docs page identification (source of truth: instructions.xml step 5, documentation_impact_assessment):
  CLI changes (flags, subcommands) -> docs/site/cli-reference.md
  Config key changes ([tool.docvet]) -> docs/site/configuration.md
  Check behavior changes -> docs/site/checks/{check_name}.md
  Rule changes -> docs/site/rules/{rule_name}.md
  Public API surface changes -> reference/ (auto-generated from docstrings; update source code)
  User workflow changes (install, pre-commit, CI) -> README.md and/or relevant docs/site/ page
  Internal-only (refactor, test, internal CI config, BMAD) -> "None -- no user-facing changes"
-->

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory -- no exceptions. -->

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors
- [x] `uv run pytest` -- all tests pass (1087 total, zero regressions)
- [x] `uv run docvet check --all` -- zero docvet findings, 100.0% coverage
- [x] `uv run interrogate -v` -- docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- All 11 tasks completed in TDD order (implementation then tests)
- SonarQube analysis found CC=20 in `check()` and CC=17 in `_output_and_exit()` — refactored by extracting `_write_timing`, `_format_coverage_line`, and `_resolve_format` helpers, reducing both to under threshold (verified 0 SonarQube violations)
- `_run_presence` returns `tuple[list[Finding], PresenceStats]` unlike other `_run_*` functions — type divergence documented in Dev Notes
- Updated 6 existing `TestOutputAndExit` tests for new kwargs (`presence_stats=None`, `min_coverage=0.0`)
- Updated `_mock_check_internals` fixture in `test_cli_timing.py` and `_mock_config_and_discovery` autouse fixture in `test_cli.py`
- Updated 5 `test_config.py` assertions for new `warn_on` default
- Fixed 2 freshness stale-body findings in own codebase (`check()` docstring, `reporting.py` module docstring)

### Change Log

| Change | Description |
|--------|-------------|
| Add `_run_presence()` | New runner in `cli.py` — reads files, calls `check_presence`, aggregates `PresenceStats` |
| Add `presence()` subcommand | `@app.command()` following enrichment pattern |
| Integrate into `check()` | Presence runs first, gated on `config.presence.enabled` |
| Update `format_summary` | New `coverage_pct` kwarg appends coverage percentage |
| Update `format_json` | New `presence_stats`/`min_coverage` kwargs add `presence_coverage` object |
| Update `determine_exit_code` | New `presence_stats` kwarg enforces coverage threshold |
| Update `_output_and_exit` | Threads `presence_stats` through pipeline, verbose coverage line |
| Update `_emit_findings` | Threads `presence_stats`/`min_coverage` to `format_json` |
| Update `warn_on` default | Added `"presence"` to `DocvetConfig.warn_on` default list |
| Extract `_write_timing` | Reduces CC in `check()` by centralizing verbose timing writes |
| Extract `_format_coverage_line` | Reduces CC in `_output_and_exit` by isolating coverage formatting |
| Extract `_resolve_format` | Reduces CC in `_output_and_exit` by isolating format resolution |
| 36 new unit tests | Comprehensive coverage of all 8 ACs across CLI, reporting, and presence |

### File List

| File | Action | Description |
|------|--------|-------------|
| `src/docvet/cli.py` | Modified | Added `_run_presence`, `presence` subcommand, `check()` integration, `_write_timing`, `_format_coverage_line`, `_resolve_format` helpers; updated `_output_and_exit`, `_emit_findings` |
| `src/docvet/reporting.py` | Modified | Updated `format_summary`, `format_json`, `determine_exit_code` signatures and module docstring |
| `src/docvet/config.py` | Modified | Added `"presence"` to `warn_on` default |
| `tests/unit/test_cli.py` | Modified | Added 36 tests in 7 new classes; updated autouse fixture and 6 existing assertions |
| `tests/unit/test_reporting.py` | Modified | Added 11 tests in 3 new classes |
| `tests/unit/checks/test_presence.py` | Modified | Added `TestNoDoubleCounting` class (1 test) |
| `tests/unit/test_cli_timing.py` | Modified | Updated fixture, patterns, and assertion counts for presence |
| `tests/unit/test_config.py` | Modified | Updated 5 `warn_on` assertions |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story -- no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
