# Story 31.2: Summary Flag for Quality Percentages

Status: review
Branch: `feat/cli-31-2-summary-flag`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want a `--summary` flag that prints per-check quality percentages,
so that I can quickly assess my project's overall documentation health without reading individual findings.

## Acceptance Criteria

1. **Given** a codebase with mixed findings across checks, **when** the user runs `docvet check --all --summary`, **then** output includes per-check quality percentages for each check that ran (enrichment, freshness, coverage, griffe) with finding counts, printed to stderr after findings.

2. **Given** the `--summary` flag is used with `--format json`, **when** the check completes, **then** a `quality` object is included in the JSON output alongside the existing `summary` object, containing per-check percentage breakdowns with numeric fields.

3. **Given** the `--summary` flag is used with a subcommand (e.g., `docvet enrichment --summary`), **when** the check completes, **then** only the relevant check's percentage is shown (checks that did not run are omitted).

4. **Given** a codebase with zero findings, **when** `--summary` is used, **then** all percentages show 100%.

5. **Given** the percentage calculation for enrichment or freshness, **when** computed, **then** the formula is `round((symbols_checked - unique_symbols_with_findings) / symbols_checked * 100)` where `unique_symbols_with_findings` is the count of distinct `(file, symbol)` pairs in the check's findings. If `symbols_checked` is 0, percentage is 100.

6. **Given** the percentage calculation for coverage or griffe, **when** computed, **then** the formula is file-based: `round((items_checked - items_with_findings) / items_checked * 100)` where coverage counts unique package directories and griffe counts files. If `items_checked` is 0, percentage is 100.

7. **Given** enrichment or freshness summary, **when** the symbol count is computed, **then** it is derived from `get_documented_symbols()` calls already in the check pipeline (no separate AST pass).

8. **Given** `--summary` and `--quiet` are both set, **when** the check completes, **then** no summary is printed to stderr (`--quiet` takes precedence). The machine-readable path is `--format json --summary`.

## Tasks / Subtasks

- [x] Task 1: Thread check-level counts through the pipeline (AC: 5, 6, 7)
  - [x] 1.1: Modify `_run_enrichment()` to return `(list[Finding], int)` where int is total documented symbols analyzed across all files (sum of `len(get_documented_symbols(tree))` per file)
  - [x] 1.2: Modify `_run_freshness()` to return `(list[Finding], int)` with same symbol count pattern
  - [x] 1.3: Modify `_run_coverage()` to return `(list[Finding], int)` where int is total unique package directories scanned (`len({f.parent for f in files})`)
  - [x] 1.4: Modify `_run_griffe()` to return `(list[Finding], int)` where int is total files checked by griffe (`len(files)`)
  - [x] 1.5: Update `check` subcommand to capture counts from each `_run_*` call into `check_counts: dict[str, int]`
- [x] Task 2: Add `--summary` global option (AC: 1, 3)
  - [x] 2.1: Add `--summary` boolean flag to `@app.callback()` with help text `"Print quality percentages after findings."`
  - [x] 2.2: Store in `ctx.obj["summary"]`
  - [x] 2.3: Wire `--summary` through to individual subcommands (enrichment, freshness, coverage, griffe) and `check`
- [x] Task 3: Create summary data structure and computation (AC: 1, 4, 5, 6)
  - [x] 3.1: Create a `CheckQuality` dataclass with fields: `items_checked: int`, `items_with_findings: int`, `percentage: int`, `unit: str` (either `"symbols"`, `"packages"`, or `"files"`)
  - [x] 3.2: Implement `compute_quality()` function in reporting.py that builds `dict[str, CheckQuality]` from `findings_by_check`, and per-check item counts
  - [x] 3.3: Enrichment/freshness: `unique_symbols_with_findings = len({(f.file, f.symbol) for f in findings})`. Handle `items_checked == 0` → percentage = 100
  - [x] 3.4: Coverage: `items_with_findings = len({f.file for f in findings})` (unique directories). Griffe: `items_with_findings = len({f.file for f in findings})` (unique files)
  - [x] 3.5: Only include checks that actually ran (non-empty key in `findings_by_check` or explicitly listed in `checks`)
- [x] Task 4: Terminal summary output (AC: 1, 3, 4, 8)
  - [x] 4.1: Create `format_quality_summary()` in reporting.py that produces a compact terminal-friendly summary block
  - [x] 4.2: Output format per check: `"  enrichment   95%  (8 findings)"` — only checks that ran, one line each
  - [x] 4.3: Emit summary to stderr (after findings on stdout), consistent with existing `format_summary()` pattern
  - [x] 4.4: Respect `--no-color` and `--quiet` (`--quiet` suppresses summary entirely — AC 8)
- [x] Task 5: JSON quality output (AC: 2)
  - [x] 5.1: Extend `format_json()` to accept optional `quality: dict[str, CheckQuality]` parameter
  - [x] 5.2: JSON structure: `"quality": {"enrichment": {"items_checked": N, "items_with_findings": M, "percentage": P, "unit": "symbols"}, ...}`
  - [x] 5.3: Only include `quality` key when `--summary` flag is active (backward-compatible — existing `summary` object unchanged)
- [x] Task 6: Wire into `_output_and_exit` (AC: 1, 2, 3, 8)
  - [x] 6.1: Add `summary: bool = False` and `check_counts: dict[str, int] | None = None` parameters to `_output_and_exit()`
  - [x] 6.2: When `summary=True` and not `quiet`: compute quality, emit terminal summary to stderr
  - [x] 6.3: When `summary=True` and `format=json`: compute quality, include in JSON output (regardless of quiet)
  - [x] 6.4: Subcommands pass their single-check count; `check` passes all counts
- [x] Task 7: Tests (AC: 1-8)
  - [x] 7.1: Unit tests for `compute_quality()` — zero findings, mixed findings, single check, all checks, zero items edge case
  - [x] 7.2: Unit tests for `format_quality_summary()` — terminal output format assertions, verify only ran checks appear
  - [x] 7.3: Unit tests for JSON output with `--summary` — verify `quality` key structure, verify existing `summary` key unchanged
  - [x] 7.4: CLI integration: `--summary` flag is accepted, context wiring works
  - [x] 7.5: Subcommand tests: `docvet enrichment --summary` shows only enrichment percentage
  - [x] 7.6: Negative test: `--summary` with `--quiet` — no summary on stderr (AC 8)
  - [x] 7.7: JSON backward compat: `--format json` without `--summary` — no `quality` key present
  - [x] 7.8: Edge case: coverage with zero directories → 100%

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `TestComputeQuality::test_mixed_findings_across_checks`, `TestFormatQualitySummary::test_single_check`, `TestSummaryFlag::test_check_counts_passed_to_output_and_exit` | Pass |
| AC2 | `TestFormatJsonQuality::test_quality_key_present_when_provided`, `TestFormatJsonQuality::test_quality_multiple_checks`, `TestSummaryFlag::test_json_output_includes_quality_key` | Pass |
| AC3 | `TestSummaryFlag::test_subcommand_passes_single_check_count`, `TestFormatQualitySummary::test_only_ran_checks_appear` | Pass |
| AC4 | `TestComputeQuality::test_zero_findings_all_checks_100_percent`, `TestFormatQualitySummary::test_100_percent` | Pass |
| AC5 | `TestComputeQuality::test_symbol_based_deduplication`, `TestComputeQuality::test_zero_items_checked_returns_100` | Pass |
| AC6 | `TestComputeQuality::test_unit_types_match_check_names`, `TestComputeQuality::test_coverage_file_based_deduplication` | Pass |
| AC7 | `TestSummaryFlag::test_check_counts_passed_to_output_and_exit` (verifies counts threaded from `_run_*` via `get_documented_symbols`) | Pass |
| AC8 | `TestSummaryFlag::test_quiet_suppresses_summary`, `TestFormatJsonQuality::test_quality_key_absent_when_none` | Pass |

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch

### Architecture & Integration Context

**Unified output pipeline (`_output_and_exit` in cli.py:348-419):**
The function already receives `findings_by_check: dict[str, list[Finding]]`, `file_count: int`, `checks: list[str]`, and `presence_stats: PresenceStats | None`. The summary computation fits naturally as an additional step between finding flattening (step 2) and format dispatch (step 5). Adding `summary: bool` and `symbol_counts: dict[str, int]` parameters keeps the pipeline signature clean.

**Existing JSON summary object (reporting.py `format_json()`):**
Already produces `{"summary": {"total": N, "by_category": {...}, "files_checked": N}}`. The `--summary` flag should ADD a top-level `"quality"` key alongside `"summary"`, NOT inside it. Structure when `--summary` is active:
```json
{
  "findings": [...],
  "summary": {"total": N, "by_category": {...}, "files_checked": N},
  "quality": {
    "enrichment": {"items_checked": 200, "items_with_findings": 8, "percentage": 96, "unit": "symbols"},
    "freshness": {"items_checked": 200, "items_with_findings": 0, "percentage": 100, "unit": "symbols"},
    "coverage": {"items_checked": 12, "items_with_findings": 1, "percentage": 92, "unit": "packages"},
    "griffe": {"items_checked": 15, "items_with_findings": 0, "percentage": 100, "unit": "files"}
  }
}
```
Without `--summary`, no `quality` key appears (backward-compatible).

**Symbol counting strategy:**
`get_documented_symbols()` is already called per-file inside `_run_enrichment()` and `_run_freshness()` (they call `ast.parse()` + `get_documented_symbols(tree)`). Counting symbols is a `len()` call on the already-returned list — zero additional AST passes per AC 6.

Coverage and griffe checks work at directory/file level, not symbol level. Coverage percentage is directory-based: `(directories_scanned - directories_with_findings) / directories_scanned * 100`. Griffe percentage is file-based: `(files_checked - files_with_findings) / files_checked * 100`. Coverage directories = `{f.parent for f in files}` (unique parent dirs of discovered files). Griffe files = `len(files)` passed to `check_griffe_compat()`.

**Unique symbols with findings:**
Findings have `file` and `symbol` fields. To count unique symbols with findings per check: `len({(f.file, f.symbol) for f in findings})`. This avoids double-counting when a symbol has multiple findings (e.g., missing-raises AND missing-yields).

**Output placement:**
Summary goes to stderr (like `format_summary()` and `format_verbose_header()` already do). Findings go to stdout. This separation is critical for piping: `docvet check --all --format json > findings.json` must not mix summary text into the JSON.

**`OutputFormat` enum (cli.py:79-105):**
Three values: `TERMINAL`, `MARKDOWN`, `JSON`. No new format needed — `--summary` is orthogonal to `--format`. It adds supplementary output regardless of format (terminal summary to stderr, JSON quality object to stdout JSON).

**`--quiet` interaction (party-mode consensus):**
`--quiet` suppresses all stderr output including summary. When `--quiet` and `--summary` are both set, terminal summary is suppressed (AC 8). However, `--format json --summary --quiet` still includes the `quality` object in JSON stdout — JSON output is not affected by `--quiet`. This gives CI/machine consumers a clean path: pipe JSON stdout, ignore stderr entirely.

**`Finding` dataclass (`checks/_finding.py`):**
Fields: `file`, `line`, `symbol`, `rule`, `message`, `category`. The `file` + `symbol` pair uniquely identifies a symbol for counting purposes.

**`_run_*` return type change:**
Currently all `_run_*` functions return `list[Finding]`. Changing to `tuple[list[Finding], int]` is a signature change. Only `_run_presence()` already returns a tuple (`tuple[list[Finding], PresenceStats]`). The pattern is established.

### Percentage Computation Details (NFR2)

**Enrichment and freshness (symbol-based):**
```
pct = round((symbols_checked - unique_symbols_with_findings) / symbols_checked * 100)
unique_symbols_with_findings = len({(f.file, f.symbol) for f in findings})
```

**Coverage (directory-based):**
```
directories_scanned = len({f.parent for f in files})
dirs_with_findings = len({f.file for f in coverage_findings})
pct = round((directories_scanned - dirs_with_findings) / directories_scanned * 100)
```

**Griffe (file-based):**
```
files_checked = len(files)
files_with_findings = len({f.file for f in griffe_findings})
pct = round((files_checked - files_with_findings) / files_checked * 100)
```

- Edge case: denominator == 0 → percentage = 100 (nothing to check = nothing wrong)
- No overall/composite score — per-check percentages only (party-mode consensus: 10/10 unanimous, supported by industry research — no major linter produces a composite quality score)

### Party-Mode Consensus Decisions (2026-03-07)

Unanimous (10/10) decisions from full-team research and debate session:

1. **No overall score** — per-check percentages only. Composite scores mix incompatible units (symbols vs directories vs files) and produce misleading numbers. Pylint's score is the most complained-about feature in its tracker. No major linter (ruff, flake8, eslint) provides a composite score.
2. **`--quiet` suppresses `--summary` on stderr** — clean orthogonal semantics. Machine path: `--format json --summary` (quality object in JSON regardless of quiet).
3. **AC precision tightened** — AC 5 specifies unique `(file, symbol)` deduplication + zero-denominator edge case. AC 6 split into symbol-based (enrichment/freshness) and file/directory-based (coverage/griffe).
4. **Coverage = directory-based, griffe = file-based** — only checks that ran appear in summary output. Terminal format: `check_name  pct%  (N findings)`.

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- No new modules — changes to existing `cli.py` and `reporting.py`
- No new dependencies
- Test files: `tests/unit/test_reporting.py` (summary computation + formatting), `tests/unit/test_cli.py` (flag wiring + integration)

**Files to modify:**
- `src/docvet/cli.py` — add `--summary` flag, thread symbol counts, pass to `_output_and_exit`
- `src/docvet/reporting.py` — add `compute_summary()`, `format_summary_table()`, extend `format_json()`
- `tests/unit/test_reporting.py` — unit tests for summary computation and formatting
- `tests/unit/test_cli.py` — CLI flag acceptance and wiring tests

**Files NOT to modify:**
- `src/docvet/checks/*.py` — check functions stay pure, no `--summary` awareness
- `src/docvet/ast_utils.py` — no changes needed, `get_documented_symbols()` already returns what we need
- `src/docvet/config.py` — no new config keys
- `action.yml` — GitHub Action already consumes JSON `summary` object; `quality` is additive

### References

- [Source: _bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md#Story 31.2]
- [Source: _bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md — FR2, FR3, NFR2, NFR10]
- [Source: src/docvet/cli.py — `_output_and_exit` unified pipeline, `_run_*` functions]
- [Source: src/docvet/reporting.py — `format_json()`, `format_summary()`, `determine_exit_code()`]
- [Source: src/docvet/ast_utils.py — `get_documented_symbols()`, `Symbol` dataclass]
- [Source: src/docvet/checks/_finding.py — `Finding` dataclass fields]
- [Source: _bmad-output/implementation-artifacts/31-1-dynamic-badge-endpoint.md — previous story learnings]

### Documentation Impact

<!-- REQUIRED: Every story must identify affected docs pages or explicitly acknowledge "None". Do NOT leave blank or use vague language like "update docs if needed". -->

- Pages: docs/site/cli-reference.md, docs/site/ci-integration.md
- Nature of update: Document `--summary` flag in CLI reference with usage examples and sample output; add note in CI integration page about using `--summary` with `--format json` for machine-readable quality metrics

### Test Maturity Piggyback

- **P3 (Low)**: Add explicit assertions to "does not raise" tests in `tests/unit/test_config.py` (lines 824, 850) — add `# Should not raise` comment to clarify intent
- Sourced from test-review.md -- address alongside this story's work

### Previous Story Intelligence (31.1)

Story 31.1 was CI-configuration-only (action.yml, ci.yml, docs). No Python code changed. Key learnings:
- The GitHub Action already produces JSON with a `summary` object — any `quality` additions must be backward-compatible
- Action outputs (`badge_message`, `badge_color`, `total_findings`) parse from JSON — new `quality` key won't break them
- Forward compatibility noted in 31.1: "Story 31.2 may enhance the badge message to include quality percentage"
- Zero-debug implementation achieved through thorough story context

### Git Intelligence

Recent commits show:
- `4e4a09a` feat(ci): add badge outputs to GitHub Action (Story 31.1)
- `8ec1abd` docs(bmad): add Growth phase PRD, architecture, and epics
- `9fde030` chore(main): release 1.11.0
- The codebase is stable and all quality gates pass

### What NOT to Do

- Do NOT compute an overall/composite quality score — party-mode consensus: per-check percentages only (no weighting, no averaging)
- Do NOT add a new `OutputFormat` enum value — `--summary` is orthogonal to `--format`
- Do NOT modify check functions in `checks/*.py` — counting happens in `_run_*` wrappers in cli.py
- Do NOT add a separate AST pass for symbol counting — reuse existing `get_documented_symbols()` calls
- Do NOT add runtime dependencies
- Do NOT break the existing JSON `summary` schema — add `quality` as a NEW key alongside existing fields
- Do NOT mix summary text into stdout when `--format json` — summary text goes to stderr only
- Do NOT have `--summary` override `--quiet` — quiet wins for stderr (machine path is `--format json --summary`)
- Do NOT show checks that didn't run in the summary — only display percentages for checks that actually executed

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (1245 tests), no regressions
- [x] `uv run docvet check --all` — zero required findings (9 recommended stale-body from uncommitted changes, will resolve after commit)
- [x] `uv run interrogate -v` — docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- All 7 tasks (30 subtasks) completed via TDD red-green-refactor cycle
- Changed `_run_enrichment`, `_run_freshness`, `_run_coverage`, `_run_griffe` return types from `list[Finding]` to `tuple[list[Finding], int]` for threading item counts
- Added `CheckQuality` frozen dataclass, `compute_quality()`, and `format_quality_summary()` to reporting.py
- Extended `format_json()` with optional `quality` parameter serialized via `dataclasses.asdict()`
- Added `--summary` global flag via `@app.callback()`, stored in `ctx.obj["summary"]`
- Updated `_output_and_exit` and `_emit_findings` to support quality computation and emission
- Updated ~30 existing tests for new `_run_*` tuple return types
- Test Maturity Piggyback: added `# Should not raise` comments to test_config.py
- Documentation: updated cli-reference.md (Quality Summary subsection) and ci-integration.md (machine-readable metrics tip)

### Change Log

| Change | Description |
|--------|-------------|
| `_run_*` return types | Changed from `list[Finding]` to `tuple[list[Finding], int]` for all 4 check runners |
| `CheckQuality` dataclass | New frozen dataclass in reporting.py with `items_checked`, `items_with_findings`, `percentage`, `unit` |
| `compute_quality()` | New function computing per-check quality percentages from findings and counts |
| `format_quality_summary()` | New function producing compact terminal summary lines |
| `format_json()` extended | Added optional `quality` parameter for JSON quality object |
| `--summary` CLI flag | New global boolean option in `@app.callback()` |
| `_output_and_exit` extended | Added `check_counts` parameter for quality computation |
| `_emit_findings` extended | Added `quality` parameter for JSON and terminal quality output |
| All 5 subcommands updated | Unpack tuples from `_run_*`, build `check_counts`, pass to pipeline |
| 35 new tests | 20 in test_reporting.py (compute + format + JSON), 15 in test_cli.py (flag wiring + integration) |
| ~30 existing tests fixed | Updated mock return values and assertions for tuple return types |

### File List

| File | Action |
|------|--------|
| `src/docvet/cli.py` | Modified — `--summary` flag, `_run_*` return types, `_output_and_exit`/`_emit_findings` extensions, subcommand wiring |
| `src/docvet/reporting.py` | Modified — `CheckQuality` dataclass, `compute_quality()`, `format_quality_summary()`, `format_json()` extended |
| `tests/unit/test_reporting.py` | Modified — 20 new tests (`TestComputeQuality`, `TestFormatQualitySummary`, `TestFormatJsonQuality`) |
| `tests/unit/test_cli.py` | Modified — 15 new tests (`TestSummaryFlag`), ~30 existing tests updated for tuple returns |
| `tests/unit/test_cli_timing.py` | Modified — mock return values updated for tuple returns |
| `tests/unit/test_cli_progress.py` | Modified — direct call tests updated for tuple returns |
| `tests/unit/test_config.py` | Modified — `# Should not raise` comments (Test Maturity Piggyback) |
| `docs/site/cli-reference.md` | Modified — `--summary` in Global Options table, new Quality Summary subsection |
| `docs/site/ci-integration.md` | Modified — tip about `--summary --format json` for machine-readable metrics |

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
