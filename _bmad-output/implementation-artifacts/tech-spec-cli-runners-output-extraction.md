---
title: 'Extract CLI check runners and output pipeline'
slug: 'cli-runners-output-extraction'
created: '2026-03-23'
status: 'done'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+', 'typer']
files_to_modify:
  - src/docvet/cli.py (rename to cli/__init__.py, remove ~435 lines)
  - src/docvet/cli/_runners.py (new, ~302 lines — git helpers + check runners)
  - src/docvet/cli/_output.py (new, ~179 lines — output pipeline + _emit_findings)
code_patterns:
  - 'cli.py → cli/__init__.py package conversion (same as enrichment.py → enrichment/__init__.py)'
  - 'Entry point pyproject.toml:71 is docvet.cli:app — works unchanged for packages'
  - 'Deferred import for _runners and _output after imports/enum definitions'
  - 'Re-import ALL extracted symbols into __init__.py — tests mock via docvet.cli._run_* paths'
  - '_output.py needs enums/types from parent — relative import (DiscoveryMode, FreshnessMode, OutputFormat, CheckName, etc.)'
  - '_runners.py needs check function imports + _get_git_diff/_get_git_blame from parent'
test_patterns:
  - 'Tests mock via docvet.cli._run_enrichment, docvet.cli._output_and_exit etc — re-imports required'
  - 'Tests also mock docvet.cli._get_git_diff and docvet.cli._get_git_blame — these move to _runners.py with re-import'
  - '100+ mock.patch calls across test_cli.py, test_cli_timing.py, test_cli_progress.py'
---

# Tech-Spec: Extract CLI check runners and output pipeline

**Created:** 2026-03-23

## Overview

### Problem Statement

`src/docvet/cli.py` is 1,456 lines — 2.9x the project's 500-line module size gate. The check runners (`_run_*` functions) and output pipeline (`_output_and_exit`, `_format_coverage_line`) are self-contained blocks totaling ~435 lines that can be extracted cleanly.

### Solution

Convert `cli.py` to a `cli/` package. Extract the 5 `_run_*` functions + `_write_timing` to `cli/_runners.py` (~238 lines) and the output helpers to `cli/_output.py` (~197 lines). The `__init__.py` retains enums, discovery helpers, app callback, and typer subcommands (~1,021 lines). Entry point `docvet = "docvet.cli:app"` works unchanged.

### Scope

**In Scope:**
- Convert `cli.py` → `cli/__init__.py`
- Extract output pipeline (L272-L451) to `_output.py` (~179 lines, includes `_emit_findings`)
- Extract git helpers + check runners (L454-L755) to `_runners.py` (~302 lines)
- Verify entry point, all tests pass, dogfood passes

**Out of Scope:**
- Subcommand extraction (follow-up PR for full gate compliance)
- Getting `__init__.py` under 500 lines (follow-up)
- Behavioral changes

## Context for Development

### Codebase Patterns

- `cli.py` is a flat module at 1,456 lines under `src/docvet/`
- Entry point: `pyproject.toml:71` → `docvet = "docvet.cli:app"` — resolves to `app` in `cli/__init__.py` after package conversion
- Runners block (L518-L755): `_write_timing`, `_run_enrichment`, `_run_presence`, `_run_freshness`, `_run_coverage`, `_run_griffe` — each takes files + config, returns findings tuple
- Output block (L272-L451): `_emit_findings`, `_format_coverage_line`, `_resolve_format`, `_output_and_exit` — output pipeline (~179 lines). `_emit_findings` (L272-L319) moves with `_output_and_exit` which is its only caller.
- Git helpers (L454-L515): `_get_git_diff`, `_get_git_blame` — move with runners (called by `_run_freshness`)
- Runners depend on check function imports (`check_enrichment`, `check_freshness_diff`, etc.), `get_documented_symbols`, `typer`, and `DiscoveryMode`/`FreshnessMode` enums from parent
- `_get_git_diff` and `_get_git_blame` belong with runners (called by `_run_freshness`) — move together
- Output pipeline depends on `Finding`, `PresenceStats`, `DocvetConfig`, `typer`, and reporting functions

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/cli.py` | Source — rename to `cli/__init__.py`, remove extracted blocks |
| `src/docvet/cli/_runners.py` | New — check runners + git helpers |
| `src/docvet/cli/_output.py` | New — output pipeline |
| `tests/unit/test_cli.py` | Primary test file — mocks `docvet.cli._run_*` and `docvet.cli._output_and_exit` |
| `tests/unit/test_cli_timing.py` | Timing tests — mocks `docvet.cli._run_*` |
| `tests/unit/test_cli_progress.py` | Progress bar tests — mocks `docvet.cli._get_git_diff` and `docvet.cli._get_git_blame` |

### Technical Decisions

- **Re-import list for `__init__.py`**: ALL extracted symbols must be re-imported because 100+ `mocker.patch("docvet.cli.<name>")` calls in tests depend on the name being in the `docvet.cli` namespace. Symbols: `_write_timing`, `_run_enrichment`, `_run_presence`, `_run_freshness`, `_run_coverage`, `_run_griffe`, `_format_coverage_line`, `_resolve_format`, `_output_and_exit`, `_get_git_diff`, `_get_git_blame`.
- **`_get_git_diff` and `_get_git_blame` move to `_runners.py`** (not `_output.py`): They're called by `_run_freshness`, not the output pipeline. They're git helpers for the runners.
- **Import style**: `_runners.py` and `_output.py` use absolute imports for external packages. They import types/enums from parent via relative import (`from . import DiscoveryMode, FreshnessMode`).
- **No `pyproject.toml` change needed**: `docvet.cli:app` resolves to package `__init__.py` just like `docvet.checks.enrichment` did.

## Implementation Plan

### Tasks

- [ ] Task 1: Convert `cli.py` to `cli/` package
  - File: `src/docvet/cli.py` → `src/docvet/cli/__init__.py`
  - Action: `git mv src/docvet/cli.py src/docvet/cli/__init__.py` (create `cli/` directory first with `mkdir`)
  - Notes: Must use git mv to preserve history. Verify the file is identical after move.

- [ ] Task 2: Create `_output.py` with output pipeline
  - File: `src/docvet/cli/_output.py` (new)
  - Action: Create file with module docstring, imports, then move L272-L451 from `__init__.py` verbatim: `_emit_findings`, `_format_coverage_line`, `_resolve_format`, `_output_and_exit`.
  - Notes: Imports needed — `from __future__ import annotations`, `os`, `sys`, `Path`, `typer`, `from docvet.checks import Finding`, `from docvet.checks.presence import PresenceStats`, `from docvet.config import DocvetConfig`, `from docvet.reporting import (CheckQuality, compute_quality, determine_exit_code, format_json, format_markdown, format_quality_summary, format_terminal, format_verbose_header, write_report)`. `_emit_findings` is internal to `_output.py` — not re-imported (no tests mock it).

- [ ] Task 3: Create `_runners.py` with git helpers and check runners
  - File: `src/docvet/cli/_runners.py` (new)
  - Action: Create file with module docstring, imports, then move L454-L755 from `__init__.py` verbatim: `_get_git_diff`, `_get_git_blame`, `_write_timing`, `_run_enrichment`, `_run_presence`, `_run_freshness`, `_run_coverage`, `_run_griffe`.
  - Notes: Imports needed — `from __future__ import annotations`, `ast`, `importlib.util`, `subprocess`, `sys`, `time`, `Path`, `typer`, check function imports (`check_enrichment`, `check_freshness_diff`, etc.), `get_documented_symbols`, `PresenceStats`, `DocvetConfig`. Relative imports from parent for `DiscoveryMode`, `FreshnessMode` enums.

- [ ] Task 4: Remove extracted blocks from `__init__.py` and add deferred imports
  - File: `src/docvet/cli/__init__.py`
  - Action: Delete L321-L755 (output block + git helpers + runners). Add deferred import blocks after the enums/discovery section:
    ```python
    from ._output import (  # noqa: E402
        _format_coverage_line,
        _output_and_exit,
        _resolve_format,
    )

    from ._runners import (  # noqa: E402
        _get_git_blame,
        _get_git_diff,
        _run_coverage,
        _run_enrichment,
        _run_freshness,
        _run_griffe,
        _run_presence,
        _write_timing,
    )
    ```
  - Notes: 11 symbols total. All must appear before the subcommand functions that call them. Place imports after discovery helpers, before the app callback section.

- [ ] Task 5: Update module docstring
  - File: `src/docvet/cli/__init__.py`
  - Action: Update docstring to reflect package structure — mention `_output` and `_runners` submodules.

- [ ] Task 6: Verify tests, lint, dogfood
  - Action: Run `uv run pytest` (1,660+ tests), `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `docvet check --all`. Verify zero test file changes.

- [ ] Task 7: Verify line counts and entry point
  - Action: Run `wc -l` on all cli files. Verify `__init__.py` is ~1,023 lines. Run `docvet --version` and `docvet check --help` to confirm entry point works.

### Acceptance Criteria

- [ ] AC 1: Given the extraction is complete, when `uv run pytest` is run, then all existing tests pass with zero modifications to test files.
- [ ] AC 2: Given the package conversion is done, when `docvet check --all` is run, then the CLI works identically (dogfood passes).
- [ ] AC 3: Given `_runners.py` and `_output.py` exist, when `mocker.patch("docvet.cli._run_enrichment")` is called in a test, then the mock takes effect (re-imports make names available in `docvet.cli` namespace).
- [ ] AC 4: Given the extraction is complete, when `ruff check .` and `ty check` are run, then no new lint or type errors are introduced.
- [ ] AC 5: Given the extraction is complete, when `wc -l` is run on `__init__.py`, then it is under 1,100 lines (target ~1,023).
- [ ] AC 6: Given the package conversion is done, when `docvet --version` is run, then the version prints correctly (entry point `docvet.cli:app` resolves).
- [ ] AC 7: Given the extraction is complete, when all enrichment/freshness/coverage/griffe/presence checks are invoked via CLI subcommands, then they produce identical findings as before extraction.

## Additional Context

### Dependencies

- Closes #373

### Testing Strategy

- **Zero test changes**: All 100+ `mocker.patch("docvet.cli._run_*")` calls work via re-imports in `__init__.py`
- **Test files**: `test_cli.py` (~3,000 lines), `test_cli_timing.py`, `test_cli_progress.py` — all must pass unchanged
- **Entry point**: `docvet check --all` dogfood must pass
- **CI gates**: ruff, ruff format, ty, pytest, docvet check --all

### Notes

- Result: `cli/__init__.py` ~1,021 lines (still over 500 — subcommand extraction is a planned follow-up)
- This is the first CLI package extraction — new territory compared to enrichment/config/mcp extractions
- Entry point is `docvet.cli:app` (not `docvet:main`) — verified in pyproject.toml:71
- `_get_git_diff` and `_get_git_blame` (L454-L515) move with runners since they're called by `_run_freshness`
- Total extraction: output block (L272-L451, ~179 lines) + git helpers + runners (L454-L755, ~302 lines) = ~481 lines
- Result: `cli/__init__.py` = 1,456 - 481 = ~975 lines
