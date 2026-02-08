---
title: 'Wire Discovery into CLI Check Pipeline'
slug: 'wire-discovery-cli'
created: '2026-02-08'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - 'Python 3.12+'
  - 'typer (CLI framework — ctx.obj for state passing)'
  - 'docvet.config.load_config (config loading)'
  - 'docvet.discovery.discover_files (file discovery)'
files_to_modify:
  - 'src/docvet/cli.py (modify — add config loading, wire discovery into subcommands, update _run_* stubs)'
  - 'tests/unit/test_cli.py (modify — update tests for new signatures and wiring behavior)'
code_patterns:
  - 'ctx.obj["docvet_config"] stores DocvetConfig — loaded once in @app.callback after invoked_subcommand guard'
  - '_run_* stubs accept (files: list[Path], config: DocvetConfig) — ready for real check modules'
  - '_discover_and_handle() helper pulls config from ctx.obj, handles path conversion, discovery, empty list, verbose'
  - 'Empty file list: typer.echo("No Python files to check.", err=True) + raise typer.Exit(0)'
  - 'Verbose file count: typer.echo(f"Found {n} file(s) to check", err=True)'
  - 'from __future__ import annotations in every file'
test_patterns:
  - 'CliRunner for CLI tests — assert on exit_code and output'
  - 'mocker.patch("docvet.cli.load_config") and mocker.patch("docvet.cli.discover_files") — patch where USED'
  - 'Help tests untouched — config loads after invoked_subcommand guard'
  - 'test_<what>_when_<condition>_<expected> naming'
  - 'No docstrings on test functions'
---

# Tech-Spec: Wire Discovery into CLI Check Pipeline

**Created:** 2026-02-08

## Overview

### Problem Statement

The CLI subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) resolve a `DiscoveryMode` enum but pass it to stub functions that ignore it. Config is never loaded from `pyproject.toml`. No files are ever discovered. The pipeline between CLI → config → discovery → checks is broken — each piece exists in isolation but nothing is wired together.

### Solution

Load `DocvetConfig` once in the `@app.callback` via `load_config()`, store it in `ctx.obj["docvet_config"]`. Each subcommand calls a shared `_discover_and_handle()` helper that invokes `discover_files()`, handles empty file lists gracefully (message + exit 0), and shows verbose file counts on stderr. The resulting `list[Path]` plus `config` are passed to the `_run_*` stubs. This follows the universal pattern from ruff, black, flake8, and pylint: discover files once centrally, pass the list to all checks.

### Scope

**In Scope:**
- Load `DocvetConfig` once in `@app.callback`, store in `ctx.obj["docvet_config"]`
- New `_discover_and_handle()` helper for shared discovery logic
- Each subcommand calls `_discover_and_handle()` after resolving discovery mode
- Update `_run_*` stub signatures from `(mode: DiscoveryMode)` to `(files: list[Path], config: DocvetConfig)`
- Empty file list → `"No Python files to check."` to stderr, exit 0
- `--verbose` → `"Found {n} file(s) to check"` to stderr
- `--config` pointing to nonexistent file → `typer.BadParameter`
- Unit tests for new wiring behavior
- Update existing CLI tests for changed behavior

**Out of Scope:**
- Actual check module implementations (enrichment, freshness, coverage, griffe)
- `src/docvet/checks/` directory or module creation
- Reporting/output formatting beyond stub messages
- Exit code logic based on check results
- Progress bars or timing output

## Context for Development

### Codebase Patterns

- Every file starts with `from __future__ import annotations`
- Google-style docstrings with full Args/Returns/Raises sections
- `ctx.obj` is a `dict` — `ctx.ensure_object(dict)` in `@app.callback`
- `ctx.obj["docvet_config"]` holds loaded `DocvetConfig`. Old `ctx.obj["config"]` (raw path string) dropped — dead code, nobody reads it downstream
- Config loading goes AFTER `invoked_subcommand is None` guard — protects all `--help` tests from needing valid pyproject.toml
- `_print_global_context()` migrated to stderr — update `typer.echo()` → `typer.echo(..., err=True)` for consistency with new discovery messages
- New discovery output uses `typer.echo(..., err=True)` (stderr) following industry convention (ruff, ty, mypy, black)
- `--files` is `list[str] | None` — converted inside `_discover_and_handle()` helper via `[Path(f) for f in files] if files else ()`. The `if files` truthiness check handles both `None` (flag not used) and `[]` (edge case) as "no explicit files"
- `FileNotFoundError` from `load_config()` when `--config` points to nonexistent file — caught in callback, raised as `typer.BadParameter`
- `load_config(path)` accepts `Path | None` and returns `DocvetConfig`
- `discover_files(config, mode, *, files=())` accepts `files: Sequence[Path]` (keyword-only), returns `list[Path]`. Passing a `list[Path]` from `_discover_and_handle()` satisfies the `Sequence` type

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/cli.py` | Main file to modify — callback, helpers, stubs, subcommands |
| `src/docvet/config.py` | `load_config()` function, `DocvetConfig` dataclass |
| `src/docvet/discovery.py` | `discover_files()`, `DiscoveryMode` enum |
| `tests/unit/test_cli.py` | Existing CLI tests — 37 tests, ~15 need mocking updates |
| `_bmad-output/project-context.md` | Project conventions for AI agents |

### Technical Decisions

1. **Config stored as `ctx.obj["docvet_config"]`** — new key. Drop `ctx.obj["config"]` (raw path string) entirely — verified via `grep` that it is only written at `cli.py:183` and never read by any production code or test. `_print_global_context()` only reads `verbose`, `format`, `output`.
2. **Config loading AFTER `invoked_subcommand` guard** — critical ordering. The callback already does `if ctx.invoked_subcommand is None: typer.echo(ctx.get_help()); return`. Config loading must go AFTER this guard. Otherwise `--help` invocations need a valid `pyproject.toml` in CWD, breaking 10+ help tests. Flow: store global options → check `invoked_subcommand` → if None, show help and return → load config → store in `ctx.obj["docvet_config"]`.
3. **`load_config()` called in `@app.callback`** — `config` param is already `Path | None` from typer. Pass directly. Wrap in `try/except FileNotFoundError` → `typer.BadParameter(f"Config file not found: {config}")`. Note: `load_config` may also call `sys.exit(1)` on invalid config (bad keys, bad types) — this propagates as `SystemExit` which typer handles gracefully (shows error, exits). No additional handling needed for `SystemExit`. `PermissionError` is not caught — let it propagate with its natural traceback (rare edge case, not worth special-casing).
4. **`_run_*` stubs take `(files: list[Path], config: DocvetConfig)`** — future-proofs for real check modules. Stubs still print `"<name>: not yet implemented"` and ignore both args.
5. **`_run_freshness` keeps `freshness_mode` param with default** — signature: `_run_freshness(files: list[Path], config: DocvetConfig, freshness_mode: FreshnessMode = FreshnessMode.DIFF)`. Default preserved so `check()` can call `_run_freshness(discovered, config)` without specifying the mode.
6. **New `_discover_and_handle()` helper** — signature: `_discover_and_handle(ctx: typer.Context, mode: DiscoveryMode, files: list[str] | None) -> list[Path]`. Pulls config from `ctx.obj["docvet_config"]` internally. Handles path conversion (`[Path(f) for f in files] if files else ()`), `discover_files()` call, empty list (message + exit 0), verbose file count. Single responsibility for the "discover" phase. Subcommand bodies become: resolve mode → `_discover_and_handle()` → pass result to `_run_*`.
7. **Empty list message**: `"No Python files to check."` via `typer.echo(..., err=True)` then `raise typer.Exit(0)`. Follows black convention.
8. **Verbose message**: `"Found {n} file(s) to check"` via `typer.echo(..., err=True)`. Follows ruff/black pattern.
9. **`_print_global_context()` migrated to stderr** — update all `typer.echo()` calls in this function to `typer.echo(..., err=True)` for consistency with the new discovery messages. All verbose/diagnostic output should go to stderr (industry convention). This prevents mixing verbose messages across stdout and stderr when `--verbose` is used.
10. **New imports in `cli.py`** — `from docvet.config import DocvetConfig, load_config`. Add `discover_files` to the existing `from docvet.discovery import DiscoveryMode` line (currently only `DiscoveryMode` is imported).
11. **Help tests untouched** — config loads after the `invoked_subcommand` guard, so `--help` never triggers `load_config()`.
12. **Subcommand tests need mocking** — tests that invoke subcommands trigger `load_config()` and `discover_files()`. Must mock `docvet.cli.load_config` and `docvet.cli.discover_files`.
13. **`test_check_when_invoked_with_config_nonexistent_path_exits_successfully`** — currently expects exit 0. After wiring, `load_config()` raises `FileNotFoundError` caught as `typer.BadParameter`. Test must change to expect non-zero exit and error message.

## Implementation Plan

### Tasks

- [x] Task 1: Update `src/docvet/cli.py` — add imports and config loading in callback
  - File: `src/docvet/cli.py`
  - Action:
    - Add import: `from docvet.config import DocvetConfig, load_config`
    - Update existing import: `from docvet.discovery import DiscoveryMode` → `from docvet.discovery import DiscoveryMode, discover_files` (only `DiscoveryMode` is currently imported)
    - In `main()` callback: remove `ctx.obj["config"] = str(config) if config is not None else None`
    - After the `if ctx.invoked_subcommand is None:` block (which shows help and returns), add config loading:
      ```python
      try:
          ctx.obj["docvet_config"] = load_config(config)
      except FileNotFoundError:
          raise typer.BadParameter(
              f"Config file not found: {config}"
          ) from None
      ```
    - Keep `ctx.obj["verbose"]`, `ctx.obj["format"]`, `ctx.obj["output"]` unchanged — they're set before the guard
  - Notes: The `config` param is `Path | None` from typer, which matches `load_config()` signature exactly. The `from None` suppresses the exception chain for cleaner user output.

- [x] Task 2: Update `src/docvet/cli.py` — add `_discover_and_handle()` helper
  - File: `src/docvet/cli.py`
  - Action: Add new helper function in the Helpers section (after `_print_global_context()`):
    ```python
    def _discover_and_handle(
        ctx: typer.Context,
        mode: DiscoveryMode,
        files: list[str] | None,
    ) -> list[Path]:
        """Discover files and handle empty results.

        Pulls config from ``ctx.obj["docvet_config"]``, converts the raw
        ``--files`` strings to :class:`~pathlib.Path` objects, calls
        :func:`discover_files`, and handles the empty-list case with a
        user-friendly message.

        Args:
            ctx: Typer context carrying ``docvet_config`` and ``verbose``.
            mode: The resolved discovery mode.
            files: Raw file paths from ``--files``, or *None*.

        Returns:
            Discovered Python file paths.

        Raises:
            typer.Exit: If no Python files are found (exit code 0).
        """
        config: DocvetConfig = ctx.obj["docvet_config"]
        explicit = [Path(f) for f in files] if files else ()
        discovered = discover_files(config, mode, files=explicit)

        if not discovered:
            typer.echo("No Python files to check.", err=True)
            raise typer.Exit(0)

        if ctx.obj.get("verbose"):
            typer.echo(f"Found {len(discovered)} file(s) to check", err=True)

        return discovered
    ```
  - Notes: Uses `ctx.obj.get("verbose")` (safe dict access) consistent with `_print_global_context()` pattern. `err=True` sends both messages to stderr. The return type is `list[Path]` but the function guarantees a non-empty list — empty case raises `typer.Exit(0)` before returning. This is documented in the `Raises` section of the docstring.

- [x] Task 3: Update `src/docvet/cli.py` — update `_run_*` stub signatures
  - File: `src/docvet/cli.py`
  - Action: Change all four stub functions:
    - `_run_enrichment(mode: DiscoveryMode)` → `_run_enrichment(files: list[Path], config: DocvetConfig)`
    - `_run_freshness(mode: DiscoveryMode, freshness_mode: FreshnessMode = FreshnessMode.DIFF)` → `_run_freshness(files: list[Path], config: DocvetConfig, freshness_mode: FreshnessMode = FreshnessMode.DIFF)` — preserve default so `check()` can omit it
    - `_run_coverage(mode: DiscoveryMode)` → `_run_coverage(files: list[Path], config: DocvetConfig)`
    - `_run_griffe(mode: DiscoveryMode)` → `_run_griffe(files: list[Path], config: DocvetConfig)`
    - Update docstrings for each: change `mode` arg description to `files` and `config` descriptions
    - Function bodies unchanged — still print `"<name>: not yet implemented"`
  - Notes: The `config` param is typed `DocvetConfig` — import already added in Task 1. The stubs ignore both params today but will use them when real checks land.

- [x] Task 4: Update `src/docvet/cli.py` — wire subcommands to use `_discover_and_handle()` and updated stubs
  - File: `src/docvet/cli.py`
  - Action: Update all five subcommand functions:
    - **`check()`**: Replace `_run_enrichment(discovery_mode)` etc. with:
      ```python
      discovery_mode = _resolve_discovery_mode(staged, all_files, files)
      _print_global_context(ctx)
      discovered = _discover_and_handle(ctx, discovery_mode, files)
      config = ctx.obj["docvet_config"]
      _run_enrichment(discovered, config)
      _run_freshness(discovered, config)
      _run_coverage(discovered, config)
      _run_griffe(discovered, config)
      ```
    - **`enrichment()`**: Same pattern — resolve mode, print context, discover, run one check
    - **`freshness()`**: Same pattern but pass `freshness_mode=mode` to `_run_freshness()`
    - **`coverage()`**: Same pattern
    - **`griffe()`**: Same pattern
  - Also update `_print_global_context()`: change all three `typer.echo()` calls to `typer.echo(..., err=True)` so all verbose/diagnostic output goes to stderr consistently.
  - Notes: `_print_global_context(ctx)` stays before `_discover_and_handle()` — verbose/format/output echo happens first, then discovery. `config` is pulled from `ctx.obj` for the `_run_*` calls. Existing tests asserting `"verbose: enabled"` in `result.output` still pass because CliRunner merges stdout/stderr.

- [x] Task 5: Update `tests/unit/test_cli.py` — add fixtures for mocking config and discovery
  - File: `tests/unit/test_cli.py`
  - Action:
    - Add imports: `from pathlib import Path`, `import pytest`
    - Add module-level marker: `pytestmark = pytest.mark.unit` (matches `test_discovery.py` and `test_ast_utils.py` convention — currently missing from `test_cli.py`)
    - Add an `autouse` fixture that mocks both `load_config` and `discover_files` for all tests that invoke subcommands. Two approaches:
      - **Option A (recommended)**: Module-level `autouse` fixture via `@pytest.fixture(autouse=True)` that patches `docvet.cli.load_config` to return a default `DocvetConfig()` and `docvet.cli.discover_files` to return `[Path("/fake/file.py")]`. This ensures ALL existing subcommand tests pass without individual modifications.
      - The fixture should use `mocker` from `pytest-mock`: `mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())` and `mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])`.
    - Add `from docvet.config import DocvetConfig` import for the fixture
  - Notes: `autouse=True` means help tests also get the mock, but since config loading happens after the `invoked_subcommand` guard, `load_config` is never called for help tests — the mock is harmless. Discovery tests that need empty results will override the fixture locally.

- [x] Task 6: Update `tests/unit/test_cli.py` — fix broken existing tests
  - File: `tests/unit/test_cli.py`
  - Action:
    - **`test_check_when_invoked_with_config_nonexistent_path_exits_successfully`** (line 249): Change from:
      ```python
      result = runner.invoke(app, ["--config", "/nonexistent/pyproject.toml", "check"])
      assert result.exit_code == 0
      ```
      To:
      ```python
      result = runner.invoke(app, ["--config", "/nonexistent/pyproject.toml", "check"])
      assert result.exit_code != 0
      assert "Config file not found" in result.output
      ```
      Also override the `autouse` mock for this specific test: use `mocker.patch("docvet.cli.load_config", side_effect=FileNotFoundError("/nonexistent/pyproject.toml"))`.
    - **`test_check_when_invoked_with_config_flag_exits_successfully`** (line 242): Override the autouse mock to call real `load_config`: `mocker.patch("docvet.cli.load_config", wraps=load_config)`. This ensures the test validates that a real config file path is accepted end-to-end, not just that the mock works. Add `from docvet.config import load_config` to the import if not already present.
    - **`test_check_when_invoked_with_no_flags_uses_diff_mode`** (line 259): Currently asserts "staged", "all", "files" not in output. After wiring, stub output still just says "enrichment: not yet implemented" etc. This test should still pass with the autouse mock.
  - Notes: The autouse fixture handles most existing tests transparently. Only the nonexistent config test needs explicit changes.

- [x] Task 7: Add new tests for wiring behavior in `tests/unit/test_cli.py`
  - File: `tests/unit/test_cli.py`
  - Action: Add new test section `# Wiring: config loading & discovery` with these tests:
    - **`test_check_when_discovery_returns_empty_exits_zero_with_message(mocker)`**: Override `discover_files` mock to return `[]`. Assert `result.exit_code == 0` and `"No Python files to check."` in `result.output`.
    - **`test_enrichment_when_discovery_returns_empty_exits_zero_with_message(mocker)`**: Same for enrichment subcommand.
    - **`test_check_when_verbose_and_files_found_shows_file_count(mocker)`**: Override `discover_files` to return 3 paths. Invoke with `["--verbose", "check"]`. Assert `"Found 3 file(s) to check"` in `result.output`.
    - **`test_check_when_not_verbose_does_not_show_file_count(mocker)`**: Default mock (files returned). Invoke without `--verbose`. Assert `"Found"` NOT in `result.output`.
    - **`test_check_when_config_file_not_found_exits_with_error(mocker)`**: Override `load_config` to raise `FileNotFoundError`. Assert `result.exit_code != 0` and `"Config file not found"` in `result.output`.
    - **`test_check_when_invoked_calls_discover_files_with_diff_mode(mocker)`**: Assert `discover_files` was called with `(ANY, DiscoveryMode.DIFF, files=())` — verifying the default mode wiring.
    - **`test_check_when_invoked_with_staged_calls_discover_with_staged_mode(mocker)`**: Invoke with `["check", "--staged"]`. Assert `discover_files` called with `DiscoveryMode.STAGED`.
    - **`test_check_when_invoked_with_all_calls_discover_with_all_mode(mocker)`**: Invoke with `["check", "--all"]`. Assert `discover_files` called with `DiscoveryMode.ALL`.
    - **`test_check_when_invoked_with_files_calls_discover_with_files_mode(mocker)`**: Invoke with `["check", "--files", "foo.py"]`. Assert `discover_files` called with `DiscoveryMode.FILES` and `files=[Path("foo.py")]`.
    - **`test_check_when_invoked_passes_config_to_run_stubs(mocker)`**: Mock `_run_enrichment` (and others). Assert they were called with `(discovered_files, config)`.
    - **`test_check_when_discovery_returns_empty_does_not_call_stubs(mocker)`**: Override `discover_files` to return `[]`. Mock all four `_run_*` functions. Assert none were called. (AC 9)
    - **`test_check_when_invoked_with_multiple_files_converts_all_paths(mocker)`**: Invoke with `["check", "--files", "foo.py", "--files", "bar.py"]`. Assert `discover_files` called with `DiscoveryMode.FILES` and `files=[Path("foo.py"), Path("bar.py")]`. (AC 7 multi-file)
    - **`test_freshness_when_invoked_with_drift_passes_freshness_mode(mocker)`**: Invoke with `["freshness", "--mode", "drift"]`. Mock `_run_freshness`. Assert called with `freshness_mode=FreshnessMode.DRIFT`. (AC 13)
    - **`test_coverage_when_invoked_calls_discover_and_run_stub(mocker)`**: Invoke `["coverage"]`. Assert `discover_files` called with `DiscoveryMode.DIFF`. Mock `_run_coverage`, assert called with `(files, config)`. (AC 4/12 for non-check subcommand)
    - **`test_griffe_when_invoked_calls_discover_and_run_stub(mocker)`**: Invoke `["griffe"]`. Assert `discover_files` called with `DiscoveryMode.DIFF`. Mock `_run_griffe`, assert called with `(files, config)`. (AC 4/12 for non-check subcommand)
    - **`test_enrichment_when_invoked_with_staged_calls_discover_with_staged_mode(mocker)`**: Invoke `["enrichment", "--staged"]`. Assert `discover_files` called with `DiscoveryMode.STAGED`. (AC 5 for non-check subcommand)
    - **`test_freshness_when_verbose_and_files_found_shows_file_count(mocker)`**: Invoke `["--verbose", "freshness"]`. Assert `"Found"` in `result.output`. (AC 10 for non-check subcommand)
    - **`test_check_when_invoked_calls_load_config_once(mocker)`**: Invoke `["check"]`. Assert `load_config` mock was called exactly once (`load_config.call_count == 1`). (AC 1 explicit verification)
  - Notes: Tests that override the autouse fixture use `mocker.patch(...)` directly in the test body — pytest-mock's `mocker.patch` in the test function takes precedence over the autouse fixture's patch. All new tests use the `mocker` fixture parameter. Total: ~18 new tests.

- [x] Task 8: Update impacted documentation
  - Files:
    - `CLAUDE.md`
    - `_bmad-output/project-context.md`
  - Action:
    - **`CLAUDE.md`** — Module Layout section: update `cli.py` comment from `# typer-based CLI entry points` to `# typer CLI: config loading, file discovery, check dispatch`. This reflects that `cli.py` now orchestrates the full pipeline, not just defines entry points.
    - **`_bmad-output/project-context.md`** — Framework Rules (Typer CLI) section:
      - **Line 49 (ctx.obj values)**: Add `ctx.obj["docvet_config"]` is a `DocvetConfig` instance. Remove mention of `ctx.obj["config"]` (dead code, removed).
      - **Line 53 (Stub pattern)**: Update `_run_*` signature description from `(mode: DiscoveryMode)` to `(files: list[Path], config: DocvetConfig)`. Note that `_run_freshness` also accepts `freshness_mode: FreshnessMode = FreshnessMode.DIFF`.
      - **Line 56 (Migration paths)**: Update to reflect stubs already accept `(files, config)` — migration is now replacing stub bodies with real check logic from `checks/<name>.py`.
    - **`_bmad-output/project-context.md`** — Testing Rules section:
      - **Line 66 (CLI tests)**: Add note about autouse fixture pattern: `test_cli.py` uses module-level `autouse=True` fixture mocking `docvet.cli.load_config` and `docvet.cli.discover_files`. Tests needing different behavior override locally.
  - Notes: Keep changes minimal — update only what this PR changed. Do not rewrite unrelated sections.

- [x] Task 9: Run full quality gates
  - Action: Run all quality checks:
    - `uv run ruff check .`
    - `uv run ruff format .`
    - `uv run ty check`
    - `uv run pytest --cov=docvet --cov-report=term-missing`
  - Notes: Fix any issues found. Ensure all 37+ existing tests pass plus new tests. Coverage should stay >= 85%.

### Acceptance Criteria

**Config loading:**
- [x] AC 1: Given a valid `pyproject.toml` in the project, when any subcommand is invoked, then `load_config()` is called once and the resulting `DocvetConfig` is available in `ctx.obj["docvet_config"]`.
- [x] AC 2: Given `--config /nonexistent/file.toml`, when any subcommand is invoked, then the CLI exits with non-zero code and prints `"Config file not found"`.
- [x] AC 3: Given `docvet --help` or `docvet check --help`, when invoked, then `load_config()` is NOT called (help works without valid config).

**Discovery wiring:**
- [x] AC 4: Given no discovery flags (default DIFF mode), when `check` is invoked, then `discover_files()` is called with `DiscoveryMode.DIFF`.
- [x] AC 5: Given `--staged`, when any subcommand is invoked, then `discover_files()` is called with `DiscoveryMode.STAGED`.
- [x] AC 6: Given `--all`, when any subcommand is invoked, then `discover_files()` is called with `DiscoveryMode.ALL`.
- [x] AC 7: Given `--files foo.py --files bar.py`, when any subcommand is invoked, then `discover_files()` is called with `DiscoveryMode.FILES` and `files=[Path("foo.py"), Path("bar.py")]`.

**Empty file handling:**
- [x] AC 8: Given `discover_files()` returns an empty list, when any subcommand is invoked, then the CLI prints `"No Python files to check."` to stderr and exits with code 0.
- [x] AC 9: Given `discover_files()` returns an empty list, when `check` is invoked, then no `_run_*` stubs are called.

**Verbose output:**
- [x] AC 10: Given `--verbose` and `discover_files()` returns 5 files, when any subcommand is invoked, then `"Found 5 file(s) to check"` appears in stderr output.
- [x] AC 11: Given no `--verbose` flag, when any subcommand is invoked, then no `"Found"` message appears in output.

**Stub signatures:**
- [x] AC 12: Given discovery returns files, when `check` is invoked, then `_run_enrichment`, `_run_coverage`, `_run_griffe` are each called with `(files, config)`, and `_run_freshness` is called with `(files, config)` using its default `freshness_mode=FreshnessMode.DIFF`.
- [x] AC 13: Given `freshness --mode drift`, when invoked, then `_run_freshness` is called with `freshness_mode=FreshnessMode.DRIFT`.

**Existing behavior preserved:**
- [x] AC 14: Given the updated CLI, when all existing help tests run, then they pass without modification.
- [x] AC 15: Given discovery returns files, when any subcommand is invoked, then stub output still contains `"<name>: not yet implemented"`.

## Additional Context

### Dependencies

- No new dependencies — uses existing `config.py` and `discovery.py`
- Depends on: #6 (discovery — already merged)

### Testing Strategy

- **Unit tests only** — no integration tests needed. This is a thin wiring layer, not new logic.
- **Mock boundary**: `mocker.patch("docvet.cli.load_config")` and `mocker.patch("docvet.cli.discover_files")` — patch where USED (in `cli.py`), not where DEFINED.
- **Autouse fixture**: Module-level `autouse=True` fixture mocks both `load_config` (returns `DocvetConfig()`) and `discover_files` (returns `[Path("/fake/file.py")]`). Ensures all existing subcommand tests pass without individual edits. Tests needing different behavior override locally.
- **Help tests untouched**: Config loads after `invoked_subcommand` guard — help tests never trigger `load_config()`. Autouse mock is harmless for these.
- **New tests**: ~17 new tests covering config loading, discovery mode wiring (including multi-file), empty list handling (exit + stubs not called), verbose output (check + freshness), error handling, stub call verification, freshness mode pass-through, and representative wiring tests for coverage/griffe/enrichment subcommands.
- **stderr testing**: CliRunner merges stdout/stderr — assert message content in `result.output`. Stream routing (`err=True`) verified by code review.

### Notes

- Branch: `feat/16-wire-discovery-cli`
- Closes: #16
- Industry research (ruff, ty, mypy, pyright, black, flake8, pylint, interrogate) unanimously supports: discover files once, pass to all checks; load config once in CLI entry; verbose output to stderr; empty file list = message + exit 0
- **Risk**: Autouse fixture may mask test failures if a future change removes the `invoked_subcommand` guard. Mitigated by AC 3 explicitly testing help-without-config.
- **Autouse fixture override**: `mocker` is function-scoped — each test gets fresh mocks. When a test body calls `mocker.patch("docvet.cli.discover_files", return_value=[])`, it replaces the autouse fixture's patch for that test only. This is standard pytest-mock behavior (patches are applied in order, last wins). Verified by pytest-mock documentation.
- **Future**: When real check modules land, they replace the `_run_*` stub bodies. Signatures (`files, config`) are already correct — no CLI changes needed per-check.
- **Error precedence**: Config errors surface before discovery-mode validation errors. A user with both bad config and conflicting flags sees the config error first. This is acceptable — config loading happens in the callback (before subcommands), while flag validation happens in subcommands. Matches ruff/ty behavior where config errors are fatal early.
- **Future**: `_discover_and_handle()` is the natural place to add progress bars, timing, or `--quiet` suppression later.

## Review Notes

- Adversarial review completed
- Findings: 13 total, 0 fixed, 13 skipped (11 noise, 2 undecided)
- Resolution approach: auto-fix (no real findings to fix)
