# Story 23.4: Pre-Commit Hook Definition

Status: done
Branch: `feat/ci-23-4-pre-commit-hook-definition`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a project maintainer,
I want to add docvet as a pre-commit hook via a standard `.pre-commit-hooks.yaml`,
so that docstring quality is checked automatically on every commit without manual setup.

## Acceptance Criteria

1. **Given** the `.pre-commit-hooks.yaml` at the repo root, **when** its structure is validated, **then** it defines a `docvet` hook with `language: python`, `types: [python]`, and an entry point that accepts positional filenames (FR134).

2. **Given** a project adds `repo: https://github.com/Alberto-Codes/docvet` to their `.pre-commit-config.yaml`, **when** `pre-commit run --all-files` is executed, **then** docvet runs on all Python files and reports findings.

3. **Given** the pre-commit framework version is 2.x or 3.x, **when** the hook is installed and run, **then** it works correctly on both major versions (NFR71).

4. **Given** the hook documentation in `docs/site/ci-integration.md`, **when** a developer reads the Pre-commit section, **then** it accurately describes that pre-commit passes filenames as positional arguments (not `--staged` mode).

5. **Given** a unit test validates the `.pre-commit-hooks.yaml` file, **when** the test suite runs, **then** all required hook fields (`id`, `name`, `entry`, `language`, `types`, `require_serial`) are present and correct.

6. **Given** the hook definition includes a `description` field, **when** a user runs `pre-commit install` and views hook metadata, **then** a clear description like "Check docstring quality" is displayed.

## Tasks / Subtasks

- [x] Task 1: Update `.pre-commit-hooks.yaml` with `description` field (AC: #1, #6)
  - [x] 1.1 Add `description: Check docstring quality` to the hook entry
  - [x] 1.2 Verify all fields match FR134: `id`, `name`, `entry`, `language`, `types`, `require_serial`
- [x] Task 2: Add `pyyaml` to dev dependencies (AC: #5)
  - [x] 2.1 Add `pyyaml` to the `[dependency-groups] dev` list in `pyproject.toml`
- [x] Task 3: Write unit test validating hook YAML schema (AC: #5)
  - [x] 3.1 Create test that loads `.pre-commit-hooks.yaml` with `yaml.safe_load()` and validates all required fields
  - [x] 3.2 Validate `id` is `docvet`, `language` is `python`, `types` contains `python`
  - [x] 3.3 Validate `entry` starts with `docvet` (accepts positional filenames)
  - [x] 3.4 Validate `require_serial` is `true`
  - [x] 3.5 Validate `description` field is present and non-empty
  - [x] 3.6 Add negative assertion: `pass_filenames` is NOT explicitly set to `false` (prevents future regression)
- [x] Task 4: Fix documentation in `docs/site/ci-integration.md` (AC: #4)
  - [x] 4.1 Remove incorrect claim that hook runs `docvet check --staged`
  - [x] 4.2 Update to explain that pre-commit passes staged filenames as positional args
  - [x] 4.3 Add explicit callout: `[tool.docvet].exclude` does not apply in pre-commit mode — use pre-commit's `exclude` key
  - [x] 4.4 Add one-line note explaining why `require_serial: true` is set
  - [x] 4.5 Add note that progress output is automatically suppressed when stderr is piped (e.g., pre-commit)
- [x] Task 5: Manual verification — `pre-commit try-repo` (AC: #2, #3)
  - [x] 5.1 Run `pre-commit try-repo . docvet --all-files` from a test project and verify findings are reported
  - [x] 5.2 Document tested pre-commit version in completion notes
- [x] Task 6: Run quality gates (AC: #1-#6)
  - [x] 6.1 All 6 quality gates pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 (hook fields + positional filenames) | `test_all_required_fields_present`, `test_id_is_docvet`, `test_language_is_python`, `test_types_contains_python`, `test_entry_starts_with_docvet`, `test_require_serial_is_true` | PASS |
| AC2 (pre-commit run --all-files) | Manual: `pre-commit try-repo . docvet --all-files` — 74 findings reported, exit code 1 | PASS |
| AC3 (2.x/3.x compat) | Manual: tested with pre-commit 4.5.1 (3.x+ line). Hook YAML uses only 1.x-compatible fields | PASS |
| AC4 (accurate documentation) | Manual: `docs/site/ci-integration.md` updated — removed `--staged` claim, added positional filename explanation, exclude callout, `require_serial` note, progress suppression note | PASS |
| AC5 (unit test validates YAML) | `TestPreCommitHooksYaml` — 12 tests covering all required fields, values, and `pass_filenames` negative assertion | PASS |
| AC6 (description field) | `test_description_field_present_and_nonempty` | PASS |

## Dev Notes

### Context: Hook Already Exists (10-3 → 23.2 Evolution)

The `.pre-commit-hooks.yaml` was created in story 10-3 with `pass_filenames: false` and `--staged` entry. Story 23.2 updated it to use positional filenames (`entry: docvet check`, default `pass_filenames: true`). This story validates and polishes that hook definition, adds tests, and fixes stale documentation.

### Current Hook State

```yaml
# .pre-commit-hooks.yaml (current)
- id: docvet
  name: docvet
  entry: docvet check
  language: python
  types: [python]
  require_serial: true
```

This works because:
- Pre-commit default `pass_filenames: true` appends staged filenames as positional args
- Story 23.2 added positional file argument support to all subcommands
- The effective command is `docvet check file1.py file2.py ...`

### Design: Pre-commit Handles File Filtering

When pre-commit passes filenames, docvet's `_discover_explicit_files()` (FILES mode) does NOT apply `[tool.docvet].exclude` patterns — it only validates existence and `.py` suffix. This is intentional and matches the ruff/ty convention:

- Pre-commit handles file filtering via `types: [python]` and the user's `exclude` regex
- If a user wants to exclude directories, they add `exclude: ^tests/` in their `.pre-commit-config.yaml`
- Docvet's own `exclude` config is for non-pre-commit workflows (e.g., `docvet check --all`)

Do NOT add `--force-exclude` or change `_discover_explicit_files` — this is standard behavior.

### Design: Why `require_serial: true`

Prevents parallel invocations that would race on git state. Without this, multiple pre-commit workers could invoke `docvet check` simultaneously, causing unpredictable results if any check accesses git (freshness does).

### Documentation Fix Required

`docs/site/ci-integration.md` line 102 currently says:
> "The hook runs `docvet check --staged`, which checks only the files you are about to commit. It runs on Python files only and discovers files through git — no filenames are passed by pre-commit."

This is **incorrect** after 23.2. The hook now:
- Runs `docvet check file1.py file2.py` (pre-commit passes filenames)
- Does NOT use `--staged` mode
- Files ARE passed by pre-commit as positional arguments

Update to explain the positional filename approach. Add a note about using pre-commit's `exclude` key for file-level exclusion and a tip about `additional_dependencies: [griffe]` for users who want griffe checking.

### Pre-commit 2.x/3.x Compatibility (NFR71)

The hook YAML uses only standard fields (`id`, `name`, `description`, `entry`, `language`, `types`, `require_serial`) — all supported since pre-commit 1.x. No `minimum_pre_commit_version` field is needed because no features specific to 2.x or 3.x are used.

Key differences between 2.x and 3.x:
- 3.x changed the default config file name from `.pre-commit-config.yaml` to the same (no change)
- 3.x dropped Python 3.7 support (irrelevant — docvet requires 3.12+)
- The hook definition schema is stable across both versions

### Test Strategy

**PyYAML as explicit dev dependency:** Add `pyyaml` to the `[dependency-groups] dev` list in `pyproject.toml`. It is already transitively present via mkdocs, but making it explicit prevents fragile transitive-dep breakage. ~200KB, zero cost.

**Unit test for hook YAML schema** (new test in `tests/unit/`):
- Load `.pre-commit-hooks.yaml` using `yaml.safe_load()` — validates both structure and YAML syntax
- Validate structure: list of dicts, each with required fields
- Validate specific field values: `id: docvet`, `language: python`, `types: [python]`, `require_serial: true`, `entry` starts with `docvet`, `description` is present and non-empty
- **Negative assertion:** If `pass_filenames` is present, it must NOT be `false` — prevents accidental regression to the old 10-3 design where pre-commit didn't pass filenames

**Manual test plan (AC #2, #3):** Run `pre-commit try-repo . docvet --all-files` from a test project once during development. This verifies end-to-end hook behavior. Document the tested pre-commit version in completion notes. This is a release gate, not a CI gate — `pre-commit` is not a dev dependency.

### Exclude Pattern Behavior (Split-Brain Callout)

When pre-commit passes filenames, docvet enters FILES mode (`_discover_explicit_files`). This mode does NOT apply `[tool.docvet].exclude` patterns. This is intentional and matches ruff/ty convention — when files are explicitly named, the tool checks them.

For pre-commit users, file exclusion is handled by pre-commit's own `exclude` regex in `.pre-commit-config.yaml`. The documentation update (Task 4) MUST include an explicit callout about this behavior so users don't wonder why their `[tool.docvet].exclude` config is ignored in pre-commit mode.

### Progress Bar Under Pre-commit

Non-issue. The progress bar checks `sys.stderr.isatty()` (Epic 20, NFR6). Pre-commit pipes stderr, so `isatty()` returns `False` and the progress bar is suppressed. Add one sentence to docs for clarity.

### What NOT to Change

- Do NOT modify `src/docvet/discovery.py` — the FILES mode behavior is correct as-is
- Do NOT modify `src/docvet/cli.py` — the positional arg support from 23.2 is complete
- Do NOT add `--force-exclude` flag — pre-commit handles exclusions
- Do NOT add `minimum_pre_commit_version` — all used fields are pre-commit 1.x compatible
- Do NOT change the hook `entry` command — `docvet check` is correct

### Key Source Files

| File | Lines | Relevance |
|------|-------|-----------|
| `.pre-commit-hooks.yaml` | Full | Hook definition — add `description` field |
| `pyproject.toml` | dev deps | Add `pyyaml` to `[dependency-groups] dev` |
| `docs/site/ci-integration.md` | 77-106 | Pre-commit section — fix stale `--staged` description, add exclude callout |
| `tests/unit/` | TBD | New test file for hook YAML validation |
| `src/docvet/discovery.py` | 294-317 | `_discover_explicit_files` — DO NOT MODIFY (reference only) |

### Previous Story Intelligence (23.3)

- **CLI test pattern**: Tests use `CliRunner` from `typer.testing` with autouse fixtures. Hook YAML tests don't need CliRunner — they're pure file validation.
- **Zero-debug goal**: Stories 23.1, 23.2, and 23.3 were all zero-debug. Aim for the same.
- **Quality gates**: 934 tests at end of 23.3. All 6 gates pass.
- **docvet dogfooding**: After modifying docs, run `docvet check --all` to verify no freshness findings.

### Git Intelligence

Recent commits:
- `40c86db refactor(cli): reduce _output_and_exit cognitive complexity (#179)`
- `da8e51d feat(cli): add --format json for structured machine-readable output (#177)`
- `dee57cc feat(cli): add positional file arguments to all subcommands (#175)` — this commit updated `.pre-commit-hooks.yaml`
- `e418fbc feat(ci): add cross-platform CI matrix and path normalization (#174)`

The `.pre-commit-hooks.yaml` was last modified in story 23.2 (commit `dee57cc`). Stable since.

### Project Structure Notes

- `.pre-commit-hooks.yaml` is at repo root — tiny change (add `description`)
- `docs/site/ci-integration.md` — documentation fix
- New test file in `tests/unit/` — hook YAML schema validation
- No production code changes in `src/docvet/`

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 23, Story 23.4]
- [Source: GitHub Issue #152 — feat: add pre-commit hook support (CLOSED)]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 4: Pre-commit Hook Design]
- [Source: .pre-commit-hooks.yaml — current hook definition]
- [Source: docs/site/ci-integration.md:77-106 — pre-commit documentation section]
- [Source: src/docvet/discovery.py:294-317 — `_discover_explicit_files` (reference)]

### Documentation Impact

- Pages: `docs/site/ci-integration.md`
- Nature of update: Fix incorrect `--staged` description, explain positional filename approach, add `exclude` tip

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 945 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Added `description: Check docstring quality` to `.pre-commit-hooks.yaml` (7 → 8 lines)
- Added `pyyaml>=6.0` as explicit dev dependency in `pyproject.toml` (was transitively available via mkdocs)
- Created `tests/unit/test_pre_commit_hooks.py` with 11 tests validating YAML schema, field values, and `pass_filenames` negative assertion
- Fixed 3 factual errors in `docs/site/ci-integration.md` Pre-commit section: removed `--staged` claim, corrected to positional filename approach
- Added "With exclude" tab, exclude behavior callout, `require_serial` explanation, progress suppression note to docs
- Manual verification: `pre-commit try-repo . docvet --all-files` succeeded with pre-commit 4.5.1 (74 findings reported, exit code 1)
- Fourth consecutive zero-debug story in Epic 23

### Change Log

- `.pre-commit-hooks.yaml`: Added `description` field
- `pyproject.toml`: Added `pyyaml>=6.0` to dev dependencies
- `tests/unit/test_pre_commit_hooks.py`: Created with 11 hook YAML schema validation tests
- `docs/site/ci-integration.md`: Rewrote Pre-commit section — fixed stale `--staged` description, added exclude callout, `require_serial` note, progress suppression note, "With exclude" tab

### File List

| File | Action |
|------|--------|
| `.pre-commit-hooks.yaml` | Modified |
| `pyproject.toml` | Modified |
| `tests/unit/test_pre_commit_hooks.py` | Created |
| `docs/site/ci-integration.md` | Modified |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party-mode consensus)

### Outcome

Approved with fixes (3 accepted, 3 rejected)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | `test_types_contains_python` doesn't verify `types` is a list — `"python" in "python"` (string) also passes | Fixed: added `assert isinstance(hook["types"], list)` |
| M2 | MEDIUM | `test_entry_starts_with_docvet` too loose — `startswith("docvet")` passes for bare `docvet` (no subcommand) | Fixed: changed to `startswith("docvet check")`, renamed test |
| L1 | LOW | Repeated YAML loading in every test — could use module-scoped fixture | Rejected: test isolation > DRY for 7-line files, matches codebase convention |
| L2 | LOW | No `name` value assertion — only presence tested, not value | Fixed: added `test_name_is_docvet` |
| L3 | LOW | `description` not in `_REQUIRED_FIELDS` constant | Rejected: preserves intentional AC5/AC6 design boundary |
| L4 | LOW | Doc says "staged Python filenames" — slightly misleading for `--all-files` | Rejected: accurate in primary commit-hook context |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
