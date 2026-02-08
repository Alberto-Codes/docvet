---
title: 'Scaffold typer CLI with check subcommand'
slug: '4-cli-scaffold'
created: '2026-02-07'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python 3.12+', 'typer>=0.9', 'hatchling', 'pytest', 'ruff', 'ty']
files_to_modify: ['src/docvet/cli.py', 'src/docvet/__init__.py', 'pyproject.toml', 'tests/unit/test_cli.py']
files_to_delete: ['tests/unit/test_init.py']
code_patterns: ['from __future__ import annotations', 'google-style docstrings', 'Annotated type aliases for shared typer options', 'DiscoveryMode enum (plain enum.Enum with auto())', 'OutputFormat/FreshnessMode as enum.StrEnum', 'mutually exclusive flag validation callback', 'explicit help= on Typer() and all commands', 'stub output format: name: not yet implemented', 'ctx.obj dict for global options', 'invoke_without_command=True']
test_patterns: ['typer.testing.CliRunner(mix_stderr=False)', 'unit tests for argument parsing', 'exit code assertions', 'mutual exclusivity error message assertions on stderr', 'deterministic orchestration order tests (index-based)', 'observable global option tests', 'help string content tests']
---

# Tech-Spec: Scaffold typer CLI with check subcommand

**Created:** 2026-02-07

## Overview

### Problem Statement

docvet has no usable CLI entry point — just a placeholder `main()` that prints a greeting. The tool needs a typer-based CLI skeleton that users and future checks can plug into.

### Solution

Create `cli.py` with a typer app exposing `check` (orchestrator), `enrichment`, `freshness`, `coverage`, and `griffe` as subcommands. Wire the entry point directly to `cli:app`. Implement shared discovery flags (`--staged`, `--all`, `--files`) using `Annotated` type aliases (typer best practice). Stub individual checks to print "not yet implemented". `check` calls each stub sequentially.

### Scope

**In Scope:**

- `src/docvet/cli.py` with typer app and all subcommands
- Entry point changed to `docvet = "docvet.cli:app"` in pyproject.toml
- Shared discovery options via `Annotated` type aliases
- Global options (`--verbose`, `--format`, `--output`)
- `check` orchestrates stubs sequentially
- Unit tests for CLI argument parsing in `tests/unit/test_cli.py`
- Update `__init__.py` and `test_init.py`
- `from __future__ import annotations` everywhere

**Out of Scope:**

- Actual check implementations (enrichment, freshness, coverage, griffe logic)
- `discovery.py`, `config.py`, `reporting.py`
- Integration tests
- `checks/` module directory (no real check modules yet)

## Context for Development

### Codebase Patterns

- All files use `from __future__ import annotations`
- Google-style docstrings throughout
- 88-char soft limit (formatter), 100-char hard limit (linter)
- f-strings for formatting, %-formatting for logging
- Type hints on all function signatures, modern syntax (`list[str]` not `List[str]`)
- Import order: `__future__` → stdlib → third-party → local
- `typer` is the only runtime dependency
- Test naming: `test_<what>_<condition>_<expected_result>`
- One assert per test recommended
- Tests mirror source structure: `src/docvet/cli.py` → `tests/unit/test_cli.py`
- Root `tests/conftest.py` has `parse_source` fixture (factory pattern)

### Files to Reference

| File | Purpose | Action |
| ---- | ------- | ------ |
| `src/docvet/__init__.py` | Placeholder `main()` printing greeting | MODIFY: remove `main()`, keep docstring |
| `pyproject.toml:20` | Entry point `docvet = "docvet:main"` | MODIFY: change to `docvet.cli:app` |
| `tests/unit/test_init.py` | 3 placeholder tests for `main()` | DELETE: no testable surface in simplified module |
| `docs/product-vision.md` | Authoritative CLI interface spec | REFERENCE: exact flags and subcommands |
| `.github/instructions/python.instructions.md` | Python style rules | REFERENCE: coding conventions |
| `.github/instructions/pytest.instructions.md` | Test conventions | REFERENCE: test naming and structure |
| `src/docvet/cli.py` | Does not exist yet | CREATE: typer app with subcommands |
| `tests/unit/test_cli.py` | Does not exist yet | CREATE: CLI unit tests |

### Technical Decisions

- **Entry point**: Change from `docvet:main` to `docvet.cli:app` (typer direct wiring, eliminates indirection)
- **Shared options**: Use `Annotated` type aliases for `--staged`, `--all`, `--files` flags shared across subcommands
- **Mutual exclusivity**: `--staged`, `--all`, `--files` are mutually exclusive; enforced via typer validation callback. Default (none specified) = unstaged git diff mode
- **DiscoveryMode enum**: `DIFF`, `STAGED`, `ALL`, `FILES` — plain `enum.Enum` with `auto()` values (no string values, since it's internal-only and never exposed to CLI). No typer imports, trivially movable to `discovery.py` later
- **OutputFormat enum**: `TERMINAL = "terminal"`, `MARKDOWN = "markdown"` — `enum.StrEnum` (Python 3.11+ stdlib), used as type annotation for `--format`, gives proper error messages for invalid values
- **Global options storage**: Use `ctx.obj` dict on `typer.Context` to store global options. The app callback sets `ctx.ensure_object(dict)` and stores `verbose`, `format`, `output` in `ctx.obj`. Subcommands that need global state accept `ctx: typer.Context` and read from `ctx.obj`. This avoids module-level mutable state and is test-safe (no state leaks between `CliRunner` invocations)
- **Global options**: `--verbose`, `--format`, `--output` via typer app callback. `--format` typed as `OutputFormat` enum. `--output` as optional `Path`
- **App callback**: Uses `invoke_without_command=True` so `docvet` with no args shows help text (typer default without this flag shows a "Missing command" error). Callback checks `ctx.invoked_subcommand is None` and prints help via `ctx.get_help()`
- **Help strings**: Explicit `help=` on `Typer()` constructor ("Comprehensive docstring quality vetting.") and every `@app.command()` (short, imperative descriptions matching vision doc)
- **Freshness-specific flag**: `--mode diff|drift` only on the `freshness` subcommand (not shared)
- **Check orchestration**: `check` subcommand calls each individual check stub in deterministic order (enrichment → freshness → coverage → griffe)
- **Simplified `__init__.py`**: Remove `main()` entirely — module becomes docstring-only. Entry point wires directly to `cli:app`
- **No ports/adapters formalism**: The natural `cli.py` → `checks/*.py` separation provides adequate boundaries
- **Typer app structure**: Single `typer.Typer()` app with top-level commands (not nested sub-apps), since all subcommands are peers
- **Global option ordering**: Typer constraint — callback options (`--verbose`, `--format`, `--output`) must precede the subcommand on the CLI: `docvet --verbose check`, NOT `docvet check --verbose`. This differs from the vision doc's syntax which shows options after the subcommand. Tests reflect the correct ordering
- **`--files` repeated flag syntax**: Typer with `list[str]` requires `--files foo.py --files bar.py` (repeated flag per value), NOT `--files foo.py bar.py` (space-separated). This differs from the vision doc which shows the space-separated form. Tests use the repeated flag form

## Implementation Plan

### Tasks

- [x] Task 1: Create `src/docvet/cli.py` with enums and typer app
  - File: `src/docvet/cli.py` (CREATE)
  - Action:
    - Add `from __future__ import annotations` and required imports (`enum`, `pathlib.Path`, `typing.Annotated`, `typing.Optional`, `typer`)
    - Define `DiscoveryMode(enum.Enum)`: `DIFF = auto()`, `STAGED = auto()`, `ALL = auto()`, `FILES = auto()` — plain enum with auto values (no string values needed since it's internal-only, never exposed to CLI). No typer imports in enum
    - Define `OutputFormat(enum.StrEnum)`: `TERMINAL = "terminal"`, `MARKDOWN = "markdown"` — use `StrEnum` (Python 3.11+ stdlib, cleaner than `(str, enum.Enum)`)
    - Define `FreshnessMode(enum.StrEnum)`: `DIFF = "diff"`, `DRIFT = "drift"` — same `StrEnum` pattern
    - Create `app = typer.Typer(help="Comprehensive docstring quality vetting.")`
    - Define `Annotated` type aliases for shared discovery options:
      - `StagedOption = Annotated[bool, typer.Option("--staged", help="Run on staged files.")]`
      - `AllOption = Annotated[bool, typer.Option("--all", help="Run on entire codebase.")]`
      - `FilesOption = Annotated[Optional[list[str]], typer.Option("--files", help="Run on specific files.")]` — use `list[str]` (reliable across typer versions; `list[Path]` is aspirational but known to break)
    - Define app callback with `invoke_without_command=True` for global options (`--verbose`, `--format`, `--output`). Callback does `ctx.ensure_object(dict)` and stores options in `ctx.obj["verbose"]`, `ctx.obj["format"]`, `ctx.obj["output"]`. When `ctx.invoked_subcommand is None`, prints help via `click.echo(ctx.get_help())`
    - Define `_resolve_discovery_mode()` helper that validates mutual exclusivity of `--staged`/`--all`/`--files` and returns a `DiscoveryMode`. Raises `typer.BadParameter` on conflict
  - Notes: `OutputFormat` and `FreshnessMode` use `enum.StrEnum` (Python 3.11+ stdlib) so typer renders choices correctly. `DiscoveryMode` is plain `enum.Enum` (internal only, not a CLI type).

- [x] Task 2: Add stub subcommands to `cli.py`
  - File: `src/docvet/cli.py` (APPEND)
  - Action:
    - `@app.command(help="Run all enabled checks.")` for `check` — accepts `ctx: typer.Context` + shared discovery options, calls `_resolve_discovery_mode()`, then calls each stub function in order: `_run_enrichment`, `_run_freshness`, `_run_coverage`, `_run_griffe`. Each prints `"<name>: not yet implemented"` (lowercase, colon-separated). If `ctx.obj["verbose"]` is True, also prints `"verbose: enabled"` before checks. If `ctx.obj["format"]` is set, prints `"format: <value>"`. If `ctx.obj["output"]` is set, prints `"output: <path>"`
    - `@app.command(help="Check for missing docstring sections.")` for `enrichment` — accepts `ctx: typer.Context` + shared discovery options, prints global context from `ctx.obj` (verbose/format/output if set), then prints `"enrichment: not yet implemented"`
    - `@app.command(help="Detect stale docstrings.")` for `freshness` — accepts `ctx: typer.Context` + shared discovery options + `--mode` typed as `FreshnessMode` defaulting to `DIFF`, prints global context, then `"freshness: not yet implemented"`
    - `@app.command(help="Find files invisible to mkdocs.")` for `coverage` — accepts `ctx: typer.Context` + shared discovery options, prints global context, then `"coverage: not yet implemented"`
    - `@app.command(help="Check mkdocs rendering compatibility.")` for `griffe` — accepts `ctx: typer.Context` + shared discovery options, prints global context, then `"griffe: not yet implemented"`
    - Define private stub functions with signature `_run_<name>(mode: DiscoveryMode) -> None`. Each prints `"<name>: not yet implemented"`. The `check` command passes the resolved `DiscoveryMode` to each. These signatures form the internal API boundary that future `checks/*.py` modules will replace
  - Notes: Each subcommand must accept `ctx: typer.Context` + the three shared discovery options and call `_resolve_discovery_mode()`. Stub output format is `"<name>: not yet implemented"` (lowercase, colon-separated) — locked for test assertions.

- [x] Task 3: Simplify `src/docvet/__init__.py`
  - File: `src/docvet/__init__.py` (MODIFY)
  - Action:
    - KEEP: module docstring `"""Docstring quality vetting for Python projects."""`
    - KEEP: `from __future__ import annotations` (required in all project files)
    - REMOVE: `main()` function and its docstring entirely
  - Notes: Final file is exactly 4 lines: docstring (triple-quote open, text, triple-quote close) + future import. No `__version__` needed at this stage.

- [x] Task 4: Update entry point in `pyproject.toml`
  - File: `pyproject.toml` (MODIFY, line 20)
  - Action: Change `docvet = "docvet:main"` to `docvet = "docvet.cli:app"`
  - Notes: Typer's `app()` callable works as a direct console_scripts entry point.

- [x] Task 5: Delete `tests/unit/test_init.py`
  - File: `tests/unit/test_init.py` (DELETE)
  - Action: Remove the file entirely. The 3 placeholder tests (`test_package_when_imported_has_main_attribute`, `test_main_when_accessed_is_callable`, `test_main_when_called_outputs_greeting`) are no longer valid.
  - Notes: No replacement needed — `__init__.py` has no testable surface.

- [x] Task 6: Create `tests/unit/test_cli.py` with CLI tests
  - File: `tests/unit/test_cli.py` (CREATE)
  - Action:
    - Add `from __future__ import annotations` and imports (`typer.testing.CliRunner`, `docvet.cli.app`)
    - Create module-level `runner = CliRunner(mix_stderr=False)` — committed config: separate stdout/stderr so mutual exclusivity error assertions target `result.stderr` not `result.output`
    - Tests (one assert per test, `test_<what>_<condition>_<expected>` naming):
      **Help & discovery:**
      - `test_app_when_invoked_with_no_args_shows_help` — exit code 0, output contains "docstring quality vetting" (requires `invoke_without_command=True`)
      - `test_app_when_invoked_with_help_shows_all_subcommands` — output contains "check", "enrichment", "freshness", "coverage", "griffe"
      - `test_check_help_when_invoked_shows_discovery_flags` — `--staged`, `--all`, `--files` in output
      - `test_check_help_when_invoked_shows_correct_description` — output contains "Run all enabled checks"
      - `test_enrichment_help_when_invoked_shows_correct_description` — output contains "missing docstring sections"
      - `test_freshness_help_when_invoked_shows_mode_flag` — `--mode` in output
      - `test_freshness_help_when_invoked_shows_correct_description` — output contains "stale docstrings"
      - `test_coverage_help_when_invoked_shows_correct_description` — output contains "invisible to mkdocs"
      - `test_griffe_help_when_invoked_shows_correct_description` — output contains "rendering compatibility"
      **Subcommand exit codes & output:**
      - `test_check_when_invoked_with_no_flags_exits_successfully` — exit code 0
      - `test_check_when_invoked_runs_all_checks_in_order` — output index: `"enrichment:"` < `"freshness:"` < `"coverage:"` < `"griffe:"`
      - `test_enrichment_when_invoked_exits_successfully` — exit code 0, output contains `"enrichment: not yet implemented"`
      - `test_freshness_when_invoked_exits_successfully` — exit code 0, output contains `"freshness: not yet implemented"`
      - `test_freshness_when_invoked_with_mode_drift_exits_successfully` — exit code 0
      - `test_coverage_when_invoked_exits_successfully` — exit code 0, output contains `"coverage: not yet implemented"`
      - `test_griffe_when_invoked_exits_successfully` — exit code 0, output contains `"griffe: not yet implemented"`
      **Discovery flag parsing:**
      - `test_check_when_invoked_with_staged_exits_successfully` — exit code 0
      - `test_check_when_invoked_with_all_exits_successfully` — exit code 0
      - `test_check_when_invoked_with_single_file_exits_successfully` — invoke with `["check", "--files", "foo.py"]`, exit code 0
      - `test_check_when_invoked_with_multiple_files_exits_successfully` — invoke with `["check", "--files", "foo.py", "--files", "bar.py"]`, exit code 0 (F5: multi-file)
      **Mutual exclusivity:**
      - `test_check_when_invoked_with_staged_and_all_fails_with_error` — exit code != 0, `result.stderr` contains "mutually exclusive" (F8: assert error content)
      - `test_check_when_invoked_with_staged_and_files_fails_with_error` — exit code != 0, `result.stderr` contains "mutually exclusive"
      - `test_check_when_invoked_with_all_and_files_fails_with_error` — exit code != 0, `result.stderr` contains "mutually exclusive"
      - `test_check_when_invoked_with_all_three_flags_fails_with_error` — invoke with `["check", "--staged", "--all", "--files", "f.py"]`, exit code != 0, `result.stderr` contains "mutually exclusive" (F9: three-way)
      **Global options:**
      - `test_check_when_invoked_with_verbose_prints_verbose_enabled` — output contains `"verbose: enabled"` (F3: observable behavior)
      - `test_check_when_invoked_with_format_markdown_prints_format` — invoke with `["--format", "markdown", "check"]`, output contains `"format: markdown"` (F2: observable)
      - `test_check_when_invoked_with_output_flag_prints_output_path` — invoke with `["--output", "report.md", "check"]`, output contains `"output: report.md"` (F2: observable)
      - `test_app_when_invoked_with_format_invalid_fails` — exit code != 0
      - `test_app_when_invoked_with_format_uppercase_fails` — invoke with `["--format", "TERMINAL", "check"]`, exit code != 0 (F15: case sensitivity)
      **Default discovery mode:**
      - `test_check_when_invoked_with_no_flags_uses_diff_mode` — output does NOT contain "staged" or "all" or "files"; confirm default diff mode is selected (F7: negative assertion — placeholder until real discovery lands and can produce positive evidence of DIFF mode)
  - Notes: All tests use `CliRunner(mix_stderr=False)`. Mutual exclusivity tests assert on `result.stderr` content. Global option tests use `["--verbose", "check"]` form (global options before subcommand). All tests are unit tests — no filesystem or git.

- [x] Task 7: Run linting, type checking, and tests
  - Action: Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `uv run pytest` to verify all quality gates pass
  - Notes: Fix any issues found. All existing tests must still pass.

### Acceptance Criteria

- [ ] AC 1: Given docvet is installed, when `docvet` is invoked with no arguments, then help text is displayed containing "docstring quality vetting" and all five subcommand names (requires `invoke_without_command=True`)
- [ ] AC 2: Given docvet is installed, when `docvet check` is invoked with no flags, then it exits with code 0 and prints output for all four checks (enrichment, freshness, coverage, griffe) in that deterministic order
- [ ] AC 3: Given docvet is installed, when `docvet check --staged` is invoked, then it exits with code 0 (staged discovery mode selected)
- [ ] AC 4: Given docvet is installed, when `docvet check --all` is invoked, then it exits with code 0 (all-files discovery mode selected)
- [ ] AC 5: Given docvet is installed, when `docvet check --files foo.py` is invoked, then it exits with code 0 (explicit files discovery mode selected)
- [ ] AC 6: Given docvet is installed, when `docvet check --files foo.py --files bar.py` is invoked, then it exits with code 0 (multiple files accepted)
- [ ] AC 7: Given docvet is installed, when `docvet check --staged --all` is invoked, then it exits with code != 0 and stderr contains "mutually exclusive"
- [ ] AC 8: Given docvet is installed, when `docvet check --staged --all --files f.py` is invoked, then it exits with code != 0 and stderr contains "mutually exclusive" (three-way)
- [ ] AC 9: Given docvet is installed, when `docvet enrichment` is invoked, then it exits with code 0 and prints "enrichment: not yet implemented"
- [ ] AC 10: Given docvet is installed, when `docvet freshness --mode drift` is invoked, then it exits with code 0 and the `--mode` flag is parsed as `drift`
- [ ] AC 11: Given docvet is installed, when `docvet coverage` is invoked, then it exits with code 0 and prints "coverage: not yet implemented"
- [ ] AC 12: Given docvet is installed, when `docvet griffe` is invoked, then it exits with code 0 and prints "griffe: not yet implemented"
- [ ] AC 13: Given docvet is installed, when `docvet --format markdown check` is invoked, then it exits with code 0 and output contains "format: markdown" (format acknowledged)
- [ ] AC 14: Given docvet is installed, when `docvet --verbose check` is invoked, then it exits with code 0 and output contains "verbose: enabled" (verbose acknowledged)
- [ ] AC 15: Given docvet is installed, when `docvet --output report.md check` is invoked, then it exits with code 0 and output contains "output: report.md" (output path acknowledged)
- [ ] AC 16: Given docvet is installed, when `docvet --format invalid check` is invoked, then it exits with code != 0 (invalid format rejected by StrEnum)
- [ ] AC 17: Given docvet is installed, when `docvet --format TERMINAL check` is invoked, then it exits with code != 0 (case-sensitive enum rejection)
- [ ] AC 18: Given docvet is installed, when `docvet check` is invoked with no flags, then the default discovery mode is DIFF (no "staged"/"all"/"files" in output context)
- [ ] AC 19: Given the codebase, when `uv run ruff check .` is run, then no lint errors are reported
- [ ] AC 20: Given the codebase, when `uv run pytest` is run, then all tests pass

## Additional Context

### Dependencies

- `typer>=0.9` (already in pyproject.toml, no changes needed)
- `typer.testing` (included with typer, no extra install)
- No new runtime or dev dependencies required

### Testing Strategy

- **Unit tests only** via `typer.testing.CliRunner` — no filesystem, no git, no subprocess
- **30 test cases** covering: help text + descriptions, exit codes, flag parsing, multi-file, mutual exclusivity (pairwise + three-way, with error message assertions), orchestration order, global options (verbose/format/output with observable stub output), default mode, case sensitivity
- **Test file**: `tests/unit/test_cli.py`
- **Deleted**: `tests/unit/test_init.py` (no testable surface)
- **Run**: `uv run pytest tests/unit/test_cli.py -v`

### Notes

- Closes GitHub issue #4
- Branch: `feat/4-cli-scaffold`
- **`--files` type**: Uses `Optional[list[str]]` (reliable). `list[Path]` is aspirational but known to break across typer versions — not worth the risk for a scaffold.
- **Future**: When real checks land, `DiscoveryMode` will move to `discovery.py`. The enum is designed to be portable (no typer imports).
- **Future**: `_run_*` private functions in `cli.py` will be replaced by imports from `checks/*.py` modules.
