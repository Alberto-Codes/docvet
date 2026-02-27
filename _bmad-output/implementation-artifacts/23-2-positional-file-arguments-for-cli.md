# Story 23.2: Positional File Arguments for CLI

Status: done
Branch: `feat/cli-23-2-positional-file-arguments`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer or pre-commit hook,
I want to pass file paths as positional arguments (`docvet check src/foo.py src/bar.py`),
so that docvet matches ruff/ty ergonomics and works with pre-commit's filename convention.

## Acceptance Criteria

1. **Given** a user runs `docvet check src/foo.py src/bar.py`, **when** positional arguments are provided without the `--files` flag, **then** docvet discovers and checks exactly those files, producing identical output to `--files src/foo.py --files src/bar.py` (NFR72).

2. **Given** a user runs `docvet enrichment src/foo.py`, **when** any subcommand receives positional file arguments, **then** all subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) accept positional args.

3. **Given** a user runs `docvet check --files src/foo.py`, **when** the existing `--files` flag is used, **then** the flag continues to work identically (backward compatible).

4. **Given** both positional args and `--files` are provided, **when** the CLI parses arguments, **then** docvet produces a clear error (no silent data loss). **Design choice:** error-only, no merge — matches ruff precedent and prevents ambiguous behavior. The epic AC allowed "error or merge"; error-only was chosen deliberately.

5. **Given** the `.pre-commit-hooks.yaml` is updated, **when** a user reads the hook definition, **then** `pass_filenames` is not set to `false` and the entry command does not include `--staged`. (Runtime pre-commit framework integration testing deferred to Story 23.4.)

## Tasks / Subtasks

- [x] Task 1: Add positional `Argument` to all 5 subcommands (AC: #1, #2)
  - [x] 1.1 Define a shared `FilesArgument` type alias using `typer.Argument()` for optional positional file list
  - [x] 1.2 Add `files_pos: FilesArgument` parameter to `check`, `enrichment`, `freshness`, `coverage`, `griffe` subcommands
  - [x] 1.3 Update each subcommand body to merge positional args into the `files` flow
- [x] Task 2: Create `_merge_file_args` helper and update error message (AC: #1, #4)
  - [x] 2.1 Create `_merge_file_args(positional, option)` helper that returns the resolved file list or raises `typer.BadParameter` if both are provided
  - [x] 2.2 Call `_merge_file_args` in each subcommand body **before** `_resolve_discovery_mode` — pass the merged result as the existing `files` parameter (no signature change to `_resolve_discovery_mode`)
  - [x] 2.3 Update the mutual exclusivity error message in `_resolve_discovery_mode` to mention positional arguments
- [x] Task 3: Update `_discover_and_handle` to accept positional args (AC: #1)
  - [x] 3.1 Ensure the `files` parameter passed to `_discover_and_handle` works whether sourced from `--files` or positional args — verified no changes needed, existing flow handles both
- [x] Task 4: Fix existing hook to use positional args (AC: #5)
  - [x] 4.1 Remove `pass_filenames: false` (defaults to `true` when omitted)
  - [x] 4.2 Remove `--staged` from entry (pre-commit passes filenames directly)
  - [x] 4.3 Entry becomes `docvet check` (positional filenames appended by pre-commit)
  - [x] Note: Full pre-commit hook formalization (NFR71 framework compat testing, docs) deferred to Story 23.4
- [x] Task 5: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 5.1 Test positional args invoke check on those files
  - [x] 5.2 Test positional args work on all 5 subcommands
  - [x] 5.3 Test `--files` continues to work (backward compatibility)
  - [x] 5.4 Test error when both positional and `--files` are provided
  - [x] 5.5 Test no positional args falls back to default discovery mode (DIFF)
- [x] Task 6: Update documentation (AC: #5)
  - [x] 6.1 Update CLI usage examples in docs if any reference `--files` exclusively
- [x] Task 7: Run quality gates and verify CI (AC: #1-#5)
  - [x] 7.1 All 6 quality gates pass
  - [ ] 7.2 CI passes on all three platforms (Ubuntu, macOS, Windows) — deferred to post-push

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1: Positional args discover and check files | `test_check_when_invoked_with_positional_files_calls_discover_with_files_mode`, `test_check_when_invoked_with_positional_files_exits_successfully` | Pass |
| AC2: All subcommands accept positional args | `test_enrichment_when_invoked_with_positional_files_exits_successfully`, `test_freshness_when_invoked_with_positional_files_exits_successfully`, `test_coverage_when_invoked_with_positional_files_exits_successfully`, `test_griffe_when_invoked_with_positional_files_exits_successfully` | Pass |
| AC3: `--files` backward compatibility | `test_check_when_invoked_with_files_option_exits_successfully` | Pass |
| AC4: Positional + `--files` error | `test_merge_file_args_when_both_provided_raises_bad_parameter`, `test_check_when_invoked_with_positional_and_files_flag_fails_with_error` | Pass |
| AC5: `.pre-commit-hooks.yaml` updated | Static file inspection: no `pass_filenames: false`, no `--staged` in entry | Pass |

## Dev Notes

### Design: Typer Positional Arguments

In typer, positional arguments use `typer.Argument()`. The key design:

```python
# New shared type alias (alongside existing FilesOption)
FilesArgument = Annotated[
    list[str] | None, typer.Argument(default=None, help="Files to check.")
]
```

Each subcommand gains a `files_pos` parameter. The merge logic in each subcommand body:
- If `files_pos` is provided and `files` (from `--files`) is also provided -> error
- If `files_pos` is provided -> use as `files`
- If `files` is provided -> use as `files` (existing behavior)
- If neither -> fall back to discovery mode (DIFF/STAGED/ALL)

### Merge Logic Placement

Create a small helper `_merge_file_args(positional, option)` that returns the resolved file list or raises `typer.BadParameter`. This keeps each subcommand's body clean and avoids duplicating the merge check in 5 places.

### `_resolve_discovery_mode` — No Signature Change

`_resolve_discovery_mode(staged, all_files, files)` already treats `files is not None` as a flag. The `_merge_file_args` helper resolves positional vs `--files` into a single `files` variable **before** calling this function. Only change: update the error message string to mention positional arguments. No new parameters, no signature change.

### `.pre-commit-hooks.yaml` Changes

Current (incompatible with pre-commit convention):
```yaml
- id: docvet
  name: docvet
  entry: docvet check --staged
  language: python
  types: [python]
  pass_filenames: false
  require_serial: true
```

New (standard pre-commit pattern):
```yaml
- id: docvet
  name: docvet
  entry: docvet check
  language: python
  types: [python]
  require_serial: true
```

`pass_filenames` defaults to `true` when omitted. Pre-commit appends filenames as positional args to the entry command. Removing `--staged` because pre-commit passes exactly the staged files — docvet doesn't need its own discovery mode.

### What NOT to Change

- Do not deprecate `--files` — keep it for backward compatibility (scripts may use it)
- Do not change `discover_files()` or `_discover_explicit_files()` in `discovery.py` — they already handle `Sequence[Path]`
- Do not change the `Finding` dataclass or any check module — this is purely CLI surface
- Do not change discovery mode logic beyond accepting merged file args
- Do not add `pass_filenames: true` explicitly to `.pre-commit-hooks.yaml` — `true` is the default; omit it for cleanliness (matches ruff's hook definition pattern)

### Key Source Files

| File | Lines | Relevance |
|------|-------|-----------|
| `src/docvet/cli.py` | 109-113, 130-159, 576-677, 679-731, 734-796, 799-848, 851-898 | `FilesOption` type alias, `_resolve_discovery_mode`, all 5 subcommands |
| `.pre-commit-hooks.yaml` | Full | Hook definition update |
| `tests/unit/test_cli.py` | Full | Existing CLI tests — add positional arg tests |

### Previous Story Intelligence (23.1)

- **CI-first workflow**: Push changes, observe CI on all 3 platforms, fix what breaks. Expect tests to pass immediately since this is a pure CLI surface change.
- **Path normalization is handled**: `Finding.__post_init__` normalizes backslash paths — no cross-platform concerns for this story.
- **Test pattern**: CLI tests use `CliRunner` from `typer.testing` with an autouse fixture that mocks `load_config`, `discover_files`, and all 4 `_run_*` functions. Follow this pattern.
- **Quality gates**: 892+ tests at end of 23.1. All 6 gates pass.

### Git Intelligence

Recent commits on main are Epic 22 (discoverability) — AGENTS.md, CONTRIBUTING.md, README rewrite, rule pages. No CLI changes since Epic 21 (output overhaul). The CLI surface is stable.

### Project Structure Notes

- Alignment with unified project structure: all changes stay within `cli.py` and `.pre-commit-hooks.yaml`
- No new modules or packages created
- Test additions go in existing `tests/unit/test_cli.py`

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 23, Story 23.2]
- [Source: GitHub Issue #152 — feat: add pre-commit hook support]
- [Source: src/docvet/cli.py:109-113 — `FilesOption` type alias]
- [Source: src/docvet/cli.py:130-159 — `_resolve_discovery_mode`]
- [Source: src/docvet/discovery.py:294-317 — `_discover_explicit_files` (no changes needed)]
- [Source: .pre-commit-hooks.yaml — current hook definition]

### Documentation Impact

- Pages: `docs/site/cli-reference.md`, `docs/development-guide.md`
- Nature of update: Added positional argument syntax to CLI examples, updated discovery flags table and pre-commit hook documentation

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 909 tests passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Typer does not allow `default=None` inside `typer.Argument()` when the function signature also sets `= None`. Fixed by removing `default=None` from `typer.Argument()`.
- Long error messages get word-wrapped by typer's rich box formatting (~62 usable chars per line), breaking substring test assertions. Shortened all error messages to fit on one line.
- `docvet check --all` flagged `cli.py:1` with `stale-body` after implementation — updated module docstring to mention positional file arguments.
- Task 3 required no code changes — `_discover_and_handle` and `discover_files()` already handle `Sequence[Path]` from either source.
- Updated all 10 existing mutual-exclusivity test assertions to match the new shorter error message.

### Change Log

- `src/docvet/cli.py`: Added `FilesArgument` type alias, `_merge_file_args` helper, `files_pos` parameter to all 5 subcommands, updated `_resolve_discovery_mode` error message, updated module docstring
- `.pre-commit-hooks.yaml`: Removed `pass_filenames: false` and `--staged` from entry command
- `tests/unit/test_cli.py`: Added 17 new tests (6 `_merge_file_args` unit tests + 11 CLI integration tests), updated 10 existing assertions
- `docs/site/cli-reference.md`: Added positional args row to discovery flags table, updated examples
- `docs/development-guide.md`: Updated CLI example to use positional syntax

### File List

- `src/docvet/cli.py`
- `.pre-commit-hooks.yaml`
- `tests/unit/test_cli.py`
- `docs/site/cli-reference.md`
- `docs/development-guide.md`

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review)

### Outcome

Approved with fixes — 5 findings resolved, 1 won't-fix (by consensus).

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| R1 | MEDIUM | `--files` labeled "legacy alternative" in cli-reference.md contradicts design intent | Fixed: changed to "repeatable alternative" |
| R2 | MEDIUM | Misleading test name `test_merge_file_args_returns_none_for_empty_positional` | Fixed: renamed to `...falls_through_to_option_when_positional_is_empty` |
| R3 | MEDIUM | `FilesOption` help text doesn't mention positional alternative | Fixed: updated help to "Run on specific files (alternative to positional args)." |
| R4 | LOW | CLAUDE.md discovery.py comment doesn't mention positional args | Fixed: added "positional args" to comment |
| R5 | LOW | Documentation Impact section references wrong file | Fixed: corrected to `cli-reference.md` and `development-guide.md` |
| R6 | LOW | Subcommand positional tests lack discovery mode assertion | Won't fix: shared code path covered by unit tests + check integration test |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
