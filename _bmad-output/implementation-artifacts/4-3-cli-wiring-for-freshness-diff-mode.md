# Story 4.3: CLI Wiring for Freshness Diff Mode

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to run `docvet freshness` from the command line and see stale docstring findings in the standard output format,
so that I can integrate freshness checking into my development workflow and CI pipelines.

## Acceptance Criteria

1. **Given** a codebase with files containing symbols with stale docstrings, **When** `docvet freshness` is run, **Then** findings are printed to terminal in `file:line: rule message` format (one per line)
2. **Given** a codebase with no stale docstrings, **When** `docvet freshness` is run, **Then** it produces no output and exits with code 0
3. **Given** the existing `_run_freshness` stub in `cli.py`, **When** the freshness check is wired for diff mode, **Then** it reads each discovered file, runs `git diff` (or `git diff --cached` for `--staged`), calls `ast.parse()`, and passes `file_path`, `diff_output`, and `tree` to `check_freshness_diff`
4. **Given** a file that fails `ast.parse()` with `SyntaxError`, **When** `docvet freshness` processes it, **Then** the file is skipped with a warning (not passed to `check_freshness_diff`)
5. **Given** `docvet check` is run (all checks), **When** freshness is in the enabled checks, **Then** freshness diff findings are included alongside findings from other checks
6. **Given** `docvet freshness` is run with no `--mode` flag, **When** the command executes, **Then** it defaults to diff mode (FR68)
7. **Given** `docvet freshness --all` is run, **When** the run completes, **Then** all Python files in the project are analyzed using `git diff HEAD` (not just staged/unstaged)

## Tasks / Subtasks

- [x] Task 1: Add imports and `_get_git_diff` helper to `cli.py` (AC: 3, 7)
  - [x] 1.1: Add `import subprocess` to stdlib imports section
  - [x] 1.2: Add `from docvet.checks.freshness import check_freshness_diff` to local imports
  - [x] 1.3: Implement `_get_git_diff(file_path, project_root, discovery_mode)` helper that returns raw diff output string
  - [x] 1.4: Map discovery mode to git diff args: DIFF/FILES → `git diff -- <file>`, STAGED → `git diff --cached -- <file>`, ALL → `git diff HEAD -- <file>`
  - [x] 1.5: Return empty string on git failure (returncode != 0) — consistent with freshness defensive design
- [x] Task 2: Replace `_run_freshness` stub body (AC: 1, 2, 3, 4, 6)
  - [x] 2.1: Add `discovery_mode: DiscoveryMode = DiscoveryMode.DIFF` parameter to `_run_freshness`
  - [x] 2.2: If `freshness_mode is not FreshnessMode.DIFF`, print "freshness drift: not yet implemented" and return (drift stays stubbed until Epic 5)
  - [x] 2.3: Iterate files, read source with `file_path.read_text(encoding="utf-8")`
  - [x] 2.4: Wrap `ast.parse()` in `try/except SyntaxError` — skip file with `typer.echo(f"warning: {file_path}: failed to parse, skipping", err=True)`
  - [x] 2.5: Call `_get_git_diff(file_path, config.project_root, discovery_mode)` to get per-file diff output
  - [x] 2.6: Call `check_freshness_diff(str(file_path), diff_output, tree)` and print each finding as `f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"`
  - [x] 2.7: Update `_run_freshness` docstring to reflect actual behavior
- [x] Task 3: Update subcommand callers to pass `discovery_mode` (AC: 3, 5, 7)
  - [x] 3.1: Update `check` subcommand: `_run_freshness(discovered, config, discovery_mode=discovery_mode)`
  - [x] 3.2: Update `freshness` subcommand: `_run_freshness(discovered, config, freshness_mode=mode, discovery_mode=discovery_mode)`
- [x] Task 4: Update existing CLI tests that reference the stub (AC: 2, 5, 6)
  - [x] 4.1: Update `test_freshness_when_invoked_exits_successfully` — remove assertion for "freshness: not yet implemented", verify exit code 0 with mocks
  - [x] 4.2: Update `test_check_when_invoked_runs_all_checks_in_order` — mock `_run_freshness` with side_effect printing "freshness: ok" (same pattern as enrichment)
  - [x] 4.3: Update `test_check_when_invoked_passes_config_to_run_stubs` — update assertion to include `discovery_mode` kwarg
  - [x] 4.4: Verify all existing CLI tests still pass after changes
- [x] Task 5: Write new unit tests for `_run_freshness` behavior (AC: 1, 2, 3, 4, 7)
  - [x] 5.1: `test_run_freshness_when_file_has_findings_prints_formatted_output` — mock subprocess + check_freshness_diff returning findings, assert stdout contains `file:line: rule message`
  - [x] 5.2: `test_run_freshness_when_no_findings_produces_no_output` — mock check_freshness_diff returning `[]`, assert no stdout
  - [x] 5.3: `test_run_freshness_when_syntax_error_skips_file_with_warning` — mock ast.parse raising SyntaxError, assert stderr warning, assert check_freshness_diff NOT called
  - [x] 5.4: `test_run_freshness_when_multiple_files_processes_all` — verify check_freshness_diff called once per file
  - [x] 5.5: `test_run_freshness_passes_file_path_diff_output_and_tree` — verify correct args to check_freshness_diff
  - [x] 5.6: `test_run_freshness_with_drift_mode_prints_not_implemented` — verify drift mode still stubbed
  - [x] 5.7: `test_get_git_diff_when_diff_mode_runs_git_diff` — verify correct git args for DIFF mode
  - [x] 5.8: `test_get_git_diff_when_staged_mode_runs_git_diff_cached` — verify `--cached` flag for STAGED
  - [x] 5.9: `test_get_git_diff_when_all_mode_runs_git_diff_head` — verify `HEAD` arg for ALL mode
  - [x] 5.10: `test_get_git_diff_when_git_fails_returns_empty_string` — verify empty string on nonzero returncode
  - [x] 5.11: `test_freshness_subcommand_passes_discovery_mode_to_run_freshness` — verify discovery_mode kwarg
  - [x] 5.12: `test_check_subcommand_passes_discovery_mode_to_run_freshness` — verify discovery_mode kwarg
- [x] Task 6: Run quality gates (AC: all)
  - [x] 6.1: `uv run ruff check .` — All checks pass
  - [x] 6.2: `uv run ruff format --check .` — All files formatted
  - [x] 6.3: `uv run ty check` — All type checks pass
  - [x] 6.4: `uv run pytest tests/unit/test_cli.py -v` — All CLI tests pass
  - [x] 6.5: `uv run pytest` — Full suite passes, 0 regressions

## Dev Notes

### Scope

This story replaces the `_run_freshness` stub in `cli.py` (lines 175-187) with a real implementation for diff mode. It connects the pure-function `check_freshness_diff` (built in Stories 4.1-4.2) to the CLI layer. Drift mode remains stubbed for Epic 5.

This is an **integration story** — same pattern as Story 1.7 (enrichment CLI wiring). The key difference from enrichment wiring is that freshness requires per-file git subprocess calls to obtain diff output.

### Files to Modify

| File | Change |
|------|--------|
| `src/docvet/cli.py` | **MODIFY** — Add `subprocess` + `check_freshness_diff` imports, add `_get_git_diff` helper, replace `_run_freshness` stub body, update `check` and `freshness` subcommands to pass `discovery_mode` |
| `tests/unit/test_cli.py` | **MODIFY** — Update stub-dependent tests, add ~12 new `_run_freshness` behavior tests and `_get_git_diff` tests |

No new files. No changes to `freshness.py`, `config.py`, `discovery.py`, or any other source module.

### Implementation: `_get_git_diff` Helper

```python
def _get_git_diff(
    file_path: Path,
    project_root: Path,
    discovery_mode: DiscoveryMode,
) -> str:
    """Get git diff output for a single file.

    Runs the appropriate ``git diff`` variant based on the discovery
    mode and returns the raw unified diff output.

    Args:
        file_path: Absolute path to the file.
        project_root: Project root for git working directory.
        discovery_mode: Controls which git diff variant to run.

    Returns:
        Raw unified diff output string. Returns an empty string if
        git is unavailable or the command fails.
    """
    if discovery_mode is DiscoveryMode.STAGED:
        args = ["git", "diff", "--cached", "--", str(file_path)]
    elif discovery_mode is DiscoveryMode.ALL:
        args = ["git", "diff", "HEAD", "--", str(file_path)]
    else:
        args = ["git", "diff", "--", str(file_path)]

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        cwd=project_root,
    )
    if result.returncode != 0:
        return ""
    return result.stdout
```

**Mode-to-git-args mapping:**
- `DIFF` / `FILES`: `git diff -- <file>` — unstaged changes (default)
- `STAGED`: `git diff --cached -- <file>` — staged changes
- `ALL`: `git diff HEAD -- <file>` — all uncommitted changes vs HEAD

### Implementation: `_run_freshness` After This Story

```python
def _run_freshness(
    files: list[Path],
    config: DocvetConfig,
    freshness_mode: FreshnessMode = FreshnessMode.DIFF,
    discovery_mode: DiscoveryMode = DiscoveryMode.DIFF,
) -> None:
    """Run the freshness check on discovered files.

    For diff mode, reads each file, obtains its git diff, parses the
    AST, and calls ``check_freshness_diff``. Findings are printed to
    stdout in ``file:line: rule message`` format. Drift mode is not
    yet implemented.

    Args:
        files: Discovered Python file paths.
        config: Loaded docvet configuration.
        freshness_mode: The freshness check strategy (diff or drift).
        discovery_mode: Controls which git diff variant to run.
    """
    if freshness_mode is not FreshnessMode.DIFF:
        typer.echo("freshness drift: not yet implemented")
        return

    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            typer.echo(
                f"warning: {file_path}: failed to parse, skipping", err=True
            )
            continue
        diff_output = _get_git_diff(file_path, config.project_root, discovery_mode)
        findings = check_freshness_diff(str(file_path), diff_output, tree)
        for finding in findings:
            typer.echo(
                f"{finding.file}:{finding.line}: {finding.rule} {finding.message}"
            )
```

### Subcommand Updates

**`check` subcommand** — pass `discovery_mode` to `_run_freshness`:
```python
_run_freshness(discovered, config, discovery_mode=discovery_mode)
```

**`freshness` subcommand** — pass both `freshness_mode` and `discovery_mode`:
```python
_run_freshness(discovered, config, freshness_mode=mode, discovery_mode=discovery_mode)
```

### Existing Test Impacts

**Tests requiring updates:**

1. **`test_freshness_when_invoked_exits_successfully` (line 126-129):**
   Currently asserts `"freshness: not yet implemented" in result.output`. After wiring, the stub message is gone. Fix: the autouse fixture already mocks `_run_enrichment`. We need to also mock `_run_freshness` in the autouse fixture (or add subprocess/file mocks). Simplest: add `mocker.patch("docvet.cli._run_freshness")` to the autouse fixture (same pattern as enrichment).

2. **`test_check_when_invoked_runs_all_checks_in_order` (line 109-118):**
   Currently checks `output.index("freshness:")`. After wiring, freshness won't print "freshness:" unless there are findings. Fix: mock `_run_freshness` with `side_effect` printing "freshness: ok" (same as enrichment pattern).

3. **`test_check_when_invoked_passes_config_to_run_stubs` (line 385-398):**
   Currently asserts `mock_freshness.assert_called_once_with(fake_files, fake_config)`. Signature now has `discovery_mode` kwarg. Fix: update assertion to `mock_freshness.assert_called_once_with(fake_files, fake_config, discovery_mode=DiscoveryMode.DIFF)`.

4. **`test_freshness_when_invoked_with_drift_passes_freshness_mode` (line 424-428):**
   Currently asserts `mock_freshness.assert_called_once_with(ANY, ANY, freshness_mode=FreshnessMode.DRIFT)`. Signature now also has `discovery_mode`. Fix: update to include `discovery_mode=DiscoveryMode.DIFF`.

### Testing Strategy

**Unit test approach for `_run_freshness` behavior tests:**
- Use `mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)` to restore the real function while keeping autouse mocks for config/discovery
- Mock `docvet.cli.check_freshness_diff` (patch where used) for controlled return values
- Mock `docvet.cli.subprocess.run` for git diff output control
- Mock `Path.read_text` for controlled source input
- Use `mocker.patch("docvet.cli.ast.parse")` for SyntaxError control

**Unit test approach for `_get_git_diff` tests:**
- Mock `docvet.cli.subprocess.run` and verify called with correct args
- Test each discovery mode variant
- Test git failure (nonzero returncode) returns empty string

**Key mocking patterns (from existing test file):**
- `mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])`
- `mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())`
- Module-level `autouse=True` fixture handles `load_config`, `discover_files`, and `_run_enrichment` mocks
- Behavior tests use `side_effect=_run_freshness` to restore the real function

### Git Subprocess Pattern

Follow the project convention: "Git via subprocess only" (project-context.md). Use `subprocess.run` with:
- `capture_output=True` — capture stdout/stderr
- `text=True` — decode to string
- `check=False` — handle returncode manually
- `cwd=project_root` — run from project root

Do NOT import or reuse `_run_git` from `discovery.py` — it returns `list[str]` (split lines), but freshness needs the raw output string. A purpose-built helper in `cli.py` is cleaner.

### Edge Cases

**Empty diff output:** When `_get_git_diff` returns `""`, `check_freshness_diff` returns `[]` (early return on empty input). No findings printed. This is correct.

**File not in git:** `git diff -- <file>` for an untracked file returns exit code 0 with empty stdout. `check_freshness_diff` returns `[]`. Correct behavior.

**Git not available:** `subprocess.run` raises `FileNotFoundError` if `git` binary not found. This is handled by the defensive empty-string return on nonzero returncode. Actually, `FileNotFoundError` is a Python exception, not a returncode. We should handle this case. Options:
- Wrap the `subprocess.run` call in try/except `FileNotFoundError` or `OSError`
- Or let it propagate (crash) — matches the project's "correctness through design" philosophy where git is expected to be available
- **Decision:** Let it propagate. The project requires git (discovery module assumes git). If git is unavailable, `discover_files` already handles it (prints warning, returns empty). By the time `_get_git_diff` is called, git should be available.

### What NOT to Do

- Do NOT add exit code logic (`fail-on`/`warn-on`) — reporting layer
- Do NOT add summary line output — reporting layer
- Do NOT add `--format` handling — MVP terminal text only
- Do NOT catch exceptions other than `SyntaxError` in the file loop — correctness through design
- Do NOT modify `freshness.py` or any other check module — this story only touches `cli.py` and its tests
- Do NOT implement drift mode — that's Epic 5
- Do NOT reuse `_run_git` from `discovery.py` — it returns split lines, freshness needs raw string
- Do NOT use `print()` — use `typer.echo()` for all output

### Previous Story Learnings (Story 4.2)

- 459 total tests, 44 in freshness specifically. All quality gates passing.
- `check_freshness_diff(file_path, diff_output, tree)` API takes `str` file_path, `str` diff_output, `ast.Module` tree
- Returns `list[Finding]` sorted by `finding.line` — never `None`
- Pure function: no I/O, no subprocess calls, deterministic
- `Finding` fields: `file`, `line`, `symbol`, `rule`, `message`, `category`

### Previous Story Learnings (Story 1.7 — Enrichment CLI Wiring)

- Same integration pattern: replace stub body, add imports, update tests
- Autouse fixture in `test_cli.py` mocks `load_config`, `discover_files`, and `_run_enrichment`
- Behavior tests use `side_effect=_run_<check>` to restore the real function while keeping autouse mocks active
- Mock at `docvet.cli.<function>` (patch where used, not where defined)
- CliRunner stderr: `err=True` warnings may appear in `result.output` depending on CliRunner configuration. Assert `"warning:"` and `"failed to parse"` in combined output.

### Project Structure Notes

- `cli.py` import section additions go in correct positions: `subprocess` in stdlib (alphabetical), `check_freshness_diff` in local (ruff isort will sort)
- `_get_git_diff` placed in the "Helpers" section of `cli.py` (after `_discover_and_handle`, before "Private stub runners")
- `_run_freshness` stays in the "Private stub runners" section (name unchanged, body replaced)
- No structural changes to subcommands beyond adding `discovery_mode` kwarg to `_run_freshness` calls

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 4.3`] — BDD acceptance criteria, FRs: FR67, FR68, NFR20, NFR30
- [Source: `_bmad-output/planning-artifacts/architecture.md#Freshness Data Flow`] — CLI → check_freshness_diff data flow
- [Source: `_bmad-output/planning-artifacts/architecture.md#Freshness Integration Points`] — CLI ↔ freshness integration contract
- [Source: `_bmad-output/planning-artifacts/architecture.md#Freshness Architectural Boundaries`] — Config asymmetry (diff has zero config dependency)
- [Source: `src/docvet/cli.py:175-187`] — Existing `_run_freshness` stub (replacement target)
- [Source: `src/docvet/cli.py:262-284`] — `check` subcommand dispatching `_run_freshness`
- [Source: `src/docvet/cli.py:309-332`] — `freshness` subcommand dispatching `_run_freshness`
- [Source: `src/docvet/checks/freshness.py:146-199`] — `check_freshness_diff` public orchestrator
- [Source: `src/docvet/discovery.py:33-62`] — `_run_git` helper (reference, not reused)
- [Source: `tests/unit/test_cli.py:33-38`] — Autouse fixture (needs `_run_freshness` mock added)
- [Source: `tests/unit/test_cli.py:109-118`] — `test_check_when_invoked_runs_all_checks_in_order` (needs update)
- [Source: `tests/unit/test_cli.py:126-129`] — `test_freshness_when_invoked_exits_successfully` (needs update)
- [Source: `tests/unit/test_cli.py:385-398`] — `test_check_when_invoked_passes_config_to_run_stubs` (needs signature update)
- [Source: `tests/unit/test_cli.py:424-428`] — `test_freshness_when_invoked_with_drift_passes_freshness_mode` (needs signature update)
- [Source: `_bmad-output/implementation-artifacts/1-7-cli-wiring-for-enrichment-check.md`] — Enrichment CLI wiring pattern (reference implementation)
- [Source: `_bmad-output/implementation-artifacts/4-2-line-classification-and-diff-mode-orchestrator.md`] — Previous story patterns and learnings
- [Source: `_bmad-output/project-context.md`] — 73 implementation rules including testing, naming, subprocess patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed `Finding` category in test: must be "required" or "recommended", not arbitrary string

### Completion Notes List

- Replaced `_run_freshness` stub with full diff-mode implementation following same pattern as `_run_enrichment`
- Added `_get_git_diff` helper with mode-to-git-args mapping (DIFF/FILES → `git diff`, STAGED → `git diff --cached`, ALL → `git diff HEAD`)
- Added `import subprocess` and `from docvet.checks.freshness import check_freshness_diff` imports
- Updated `check` and `freshness` subcommands to pass `discovery_mode` kwarg
- Updated autouse fixture to mock `_run_freshness` (prevents real subprocess calls in tests)
- Updated 4 existing tests for new signature and behavior
- Added 12 new tests: 6 for `_run_freshness` behavior, 4 for `_get_git_diff` mode variants, 2 for subcommand discovery_mode passing
- All 471 tests pass (73 CLI tests), all quality gates green

### File List

| File | Action |
|------|--------|
| `src/docvet/cli.py` | Modified |
| `tests/unit/test_cli.py` | Modified |

### Change Log

- 2026-02-10: Implemented CLI wiring for freshness diff mode — replaced stub with real implementation, added `_get_git_diff` helper, updated subcommand callers, updated 4 existing tests, added 12 new tests. All 471 tests pass.
