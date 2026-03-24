# Story 32.3: Fix CLI Wiring — Subcommand, Dry-Run, and Discovery

Status: review
Branch: `feat/fix-32-3-cli-wiring-dry-run-discovery`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want the fix command integrated into the CLI with dry-run and file discovery support,
so that I can preview changes before applying them and use fix with the same workflows as check.

## Acceptance Criteria

1. **Given** the user runs `docvet fix --dry-run`, **when** files have missing sections, **then** a unified diff is printed to stdout showing what would change, without modifying any files.

2. **Given** the user runs `docvet fix` (no flags), **when** files in the git diff have missing sections, **then** those files are modified in-place with scaffolded sections.

3. **Given** the user runs `docvet fix --staged`, **when** staged files have missing sections, **then** only staged files are modified.

4. **Given** the user runs `docvet fix --all`, **when** the codebase has files with missing sections, **then** all matching files are modified.

5. **Given** the user runs `docvet fix path/to/file.py`, **when** the specified file has missing sections, **then** only that file is modified.

6. **Given** the user runs `docvet fix` on a file with no missing sections, **when** fix completes, **then** no files are modified and a message indicates "No fixes needed".

7. **Given** fix modifies files, **when** the user subsequently runs `docvet check` on those files, **then** the original missing-section findings are gone, replaced by `scaffold` category findings for each scaffolded section. The scaffold findings have actionable messages guiding the user to fill in real content.

## Tasks / Subtasks

- [x] Task 1: Add `_run_fix()` runner in `src/docvet/cli/_runners.py` (AC: 2, 6, 7)
  - [x] 1.1 Implement `_run_fix(files, config, *, dry_run, show_progress) -> tuple[list[Finding], int, int, list[tuple]]` returning `(scaffold_findings, files_modified_count, sections_scaffolded_count, diffs)`
  - [x] 1.2 For each file: read source, parse AST, run `check_enrichment()`, filter to `RULE_TO_SECTION` rules, call `scaffold_missing_sections()`, compare before/after
  - [x] 1.3 If not dry_run and source changed: write modified source back to file
  - [x] 1.4 Re-parse modified source, run `check_enrichment()` to collect scaffold-incomplete findings
  - [x] 1.5 Handle SyntaxError gracefully (skip with warning, same as other runners)
  - [x] 1.6 Unit tests: file modified when source changes, file untouched when no changes, SyntaxError skipping, scaffold findings collected after fix, empty discovery (zero files), no-docstring files (zero modifications), mixed results (some files modified, some not)

- [x] Task 2: Add `docvet fix` subcommand in `src/docvet/cli/__init__.py` (AC: 1, 2, 3, 4, 5, 6)
  - [x] 2.1 Add `@app.command() fix()` following enrichment subcommand pattern: `files_pos`, `verbose`, `quiet`, `staged`, `all_files`, `files` options
  - [x] 2.2 Add `--dry-run` flag (`typer.Option(False, help="Show changes without writing files")`)
  - [x] 2.3 Wire discovery pipeline: `_merge_file_args()` → `_resolve_discovery_mode()` → `_discover_and_handle()`
  - [x] 2.4 Call `_run_fix()` with discovered files and config
  - [x] 2.5 Output: custom summary line to stderr (not `format_summary()`)
  - [x] 2.6 Output scaffold findings via `_output_and_exit()` pipeline (respects `--format`, `--output`, exit code)
  - [x] 2.7 Unit tests: help output, discovery flag acceptance, dry-run flag, output pipeline

- [x] Task 3: Implement dry-run unified diff output (AC: 1)
  - [x] 3.1 When `dry_run=True` in `_run_fix()`: collect `(file_path, original, modified)` tuples instead of writing
  - [x] 3.2 Generate unified diffs using `difflib.unified_diff()` with `fromfile=f"a/{path}"`, `tofile=f"b/{path}"` format
  - [x] 3.3 Print diffs to stdout (one per modified file)
  - [x] 3.4 Print summary: `"Would fix N of M files (K sections scaffolded)"` to stderr
  - [x] 3.5 Exit code 0 (dry-run is informational; `raise typer.Exit(0)`)
  - [x] 3.6 `--format` flag is ignored in dry-run mode — unified diff is always the output format
  - [x] 3.7 Unit tests: diff output format, no file writes during dry-run, summary message, exit code

- [x] Task 4: Summary and reporting integration (AC: 6, 7)
  - [x] 4.1 Custom fix summary line: `"Fixed N of M files (K sections scaffolded) — L scaffold findings. (Xs)"` or `"No fixes needed (0 of M files) — 0 findings. (Xs)"`
  - [x] 4.2 Scaffold findings from post-fix enrichment check passed to `_output_and_exit()` for terminal/markdown/JSON output
  - [x] 4.3 Unit tests: summary format for zero/nonzero fixes, scaffold findings in output

- [x] Task 5: Integration testing and dogfooding (AC: 1-7)
  - [x] 5.1 Integration test: create temp git repo with incomplete docstrings, run `docvet fix`, verify files modified
  - [x] 5.2 Integration test: `docvet fix --dry-run` produces diff output, files unchanged
  - [x] 5.3 Integration test: `docvet fix --staged` only modifies staged files
  - [x] 5.4 Integration test: `docvet fix` then `docvet check` shows scaffold findings instead of missing-section findings (roundtrip)
  - [x] 5.5 Run `docvet fix --dry-run --all` on own codebase — zero diffs (verified)
  - [x] 5.6 Verify `docvet fix --help` output shows all flags (verified)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | test_cli_fix::TestFixSubcommand::test_dry_run_produces_diff_output; test_fix_cli::TestFixCliIntegration::test_dry_run_does_not_modify_files | PASS |
| 2 | test_cli_fix::TestRunFix::test_modifies_file_with_missing_sections; test_fix_cli::TestFixCliIntegration::test_fix_modifies_files_in_repo | PASS |
| 3 | test_cli_fix::TestFixSubcommand::test_discovery_flags_accepted[staged]; test_fix_cli::TestFixCliIntegration::test_fix_staged_only_modifies_staged | PASS |
| 4 | test_cli_fix::TestFixSubcommand::test_discovery_flags_accepted[all] | PASS |
| 5 | test_cli_fix::TestFixSubcommand::test_fix_modifies_file_in_place (positional arg) | PASS |
| 6 | test_cli_fix::TestRunFix::test_no_modification_when_complete; test_cli_fix::TestFixSubcommand::test_summary_format_no_fixes | PASS |
| 7 | test_cli_fix::TestRunFix::test_scaffold_findings_collected; test_fix_cli::TestFixCliIntegration::test_fix_then_check_shows_scaffold_findings | PASS |

## Dev Notes

- **Interaction Risk:** The `fix` subcommand adds a new entry to the typer CLI app. It does NOT modify any existing check runner or subcommand. The `_run_fix()` runner is a new function in `_runners.py`. Risk is low — the main interaction surface is `_output_and_exit()` which is already battle-tested across 5 check subcommands.
- **Production function available from 32.2:** `scaffold_missing_sections(source: str, tree: ast.Module, findings: list[Finding]) -> str` — takes enrichment findings and returns modified source. Idempotent, deterministic, handles one-liners, multi-line, quote styles, CRLF. Re-export from `docvet.checks`.
- **Fix pipeline order (critical):** (1) Read source + parse AST → (2) `check_enrichment()` for `missing-*` findings → (3) Filter to `RULE_TO_SECTION` keys only → (4) `scaffold_missing_sections()` → (5) If source changed: write file → (6) Re-parse + `check_enrichment()` for scaffold-incomplete findings → (7) Report.
- **Dry-run uses `difflib.unified_diff()`:** Stdlib, no new dependencies. Format: `--- a/path` / `+++ b/path` with context lines. Print to stdout.
- **Exit code behavior:** Scaffold findings are enrichment findings. If `enrichment` is in `fail_on`, scaffold findings trigger exit code 1 via existing `determine_exit_code()`. Dry-run always exits 0.
- **Discovery reuse:** Use exactly the same `_merge_file_args()` → `_resolve_discovery_mode()` → `_discover_and_handle()` chain as other subcommands. No custom discovery logic.
- **File I/O pattern:** `Path(file_path).read_text(encoding="utf-8")` for read, `Path(file_path).write_text(modified_source, encoding="utf-8")` for write. Newline preservation is handled by `scaffold_missing_sections()` internally.
- **Filtering findings for scaffold input:** Only pass findings with `rule in RULE_TO_SECTION` to `scaffold_missing_sections()`. Other enrichment findings (trivial-docstring, missing-return-type, etc.) are not actionable by the scaffolding engine and should be ignored.
- **Config:** `fix` does not need its own config section. It uses `config.enrichment` for the enrichment check and `config.docstring_style` for style selection. The `scaffold_incomplete` config field controls whether scaffold-incomplete findings are reported in the post-fix check.
- **Dry-run architecture (party-mode consensus):** Dry-run mode bypasses `_output_and_exit()` entirely. Unified diffs print to stdout, summary to stderr, then `raise typer.Exit(0)`. The `--format` flag is ignored in dry-run mode — the diff IS the output, not findings. In non-dry-run mode, use `_output_and_exit()` normally with scaffold findings.
- **Summary line for fix:** Use a custom summary format, NOT `format_summary()`. Fix is an action, not a check — it doesn't "vet" files. Format: `"Fixed N of M files (K sections scaffolded) — L scaffold findings. (Xs)"`. This gives the user context about how many files were affected out of the total discovered.

### Project Structure Notes

- New runner: `_run_fix()` in `src/docvet/cli/_runners.py` (~40-60 lines)
- Modified: `src/docvet/cli/__init__.py` — add `@app.command() fix` (~40 lines)
- Modified: `src/docvet/cli/_output.py` — may need minor updates if fix metadata added to JSON
- New tests: `tests/unit/test_cli_fix.py` — unit tests for fix subcommand and runner
- New tests: `tests/integration/test_fix_cli.py` — integration tests with temp git repos
- Alignment: follows exact same pattern as enrichment subcommand (the most similar existing command)

### References

- [Source: _bmad-output/implementation-artifacts/32-2-fix-core-section-scaffolding-engine.md] — Scaffolding engine design, completion notes, code review findings
- [Source: _bmad-output/implementation-artifacts/32-1-spike-decision.md] — Feasibility spike, insertion strategy decision, edge case catalog
- [Source: _bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md#Story 32.3] — Acceptance criteria, epic context
- [Source: src/docvet/cli/__init__.py] — Existing subcommand pattern (enrichment as reference)
- [Source: src/docvet/cli/_runners.py] — Runner pattern (_run_enrichment as reference)
- [Source: src/docvet/cli/_output.py] — _output_and_exit() pipeline
- [Source: src/docvet/checks/fix.py] — scaffold_missing_sections() API, RULE_TO_SECTION mapping
- [Source: src/docvet/discovery.py] — discover_files(), DiscoveryMode enum

### Documentation Impact

- Pages: docs/site/cli-reference.md
- Nature of update: Document new `docvet fix` subcommand with `--dry-run`, `--staged`, `--all`, positional file args. Add usage examples showing fix → check roundtrip workflow.

### Test Maturity Piggyback

- P2 (Medium): Continue parametrize adoption — apply `@pytest.mark.parametrize` for discovery mode variants in fix CLI tests (--all, --staged, default, positional) instead of duplicating test bodies. Sourced from test-review.md v7.0 — address alongside this story's work.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1733 passed, zero regressions
- [x] `uv run docvet check --all` — zero findings, 100% coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- All 1733 tests pass (1714 existing + 19 new)
- All 5 quality gates green
- Dogfooding: `docvet fix --dry-run --all` produces zero diffs on own codebase

### Completion Notes List

- Task 1: Created `_run_fix()` in `_runners.py`. Pipeline: enrichment -> filter RULE_TO_SECTION -> scaffold -> write (or collect diffs) -> re-check for scaffold-incomplete. Returns 4-tuple: (findings, files_modified, sections_scaffolded, diffs).
- Task 2: Added `@app.command() fix()` in `cli/__init__.py` following enrichment pattern. Wires discovery pipeline, passes `--dry-run` to runner.
- Task 3: Dry-run bypasses `_output_and_exit()`, prints unified diffs via `difflib.unified_diff()` to stdout, summary to stderr, exits 0.
- Task 4: Custom summary format: `"Fixed N of M files (K sections scaffolded) -- L scaffold findings. (Xs)"`. Non-dry-run uses `_output_and_exit()` for scaffold findings.
- Task 5: 4 integration tests in temp git repos. Roundtrip verified: fix -> check shows scaffold-incomplete, not missing-raises.
- Docs: Updated cli-reference.md with fix subcommand documentation and workflow example.

### Change Log

- 2026-03-23: Implemented fix CLI subcommand with dry-run, discovery modes, custom summary, integration tests. All quality gates pass.

### File List

- `src/docvet/cli/__init__.py` (modified) -- Added `fix` subcommand, imported `_run_fix`
- `src/docvet/cli/_runners.py` (modified) -- Added `_run_fix()` runner function
- `docs/site/cli-reference.md` (modified) -- Documented `docvet fix` subcommand
- `tests/unit/test_cli_fix.py` (new) -- 15 unit tests for fix runner and CLI subcommand
- `tests/integration/test_fix_cli.py` (new) -- 4 integration tests in temp git repos
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) -- Story status updates

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
