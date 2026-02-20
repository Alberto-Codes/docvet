# Story 9.2: Add `__all__` Exports to All Public Modules

Status: done

## Story

As a Python developer importing from docvet,
I want only intentional public symbols exported from each module,
so that the v1 API surface is explicit and stable.

## Acceptance Criteria

1. **Given** 11 modules in `src/docvet/` (8 currently lack `__all__`), **when** `__all__` is defined in every module, **then** each module's `__all__` lists only its intended public symbols per NFR66.
2. **Given** `__all__` defined on all modules, **when** `from docvet.checks import *` is executed, **then** only `Finding` and the five check functions (`check_enrichment`, `check_freshness_diff`, `check_freshness_drift`, `check_coverage`, `check_griffe_compat`) are produced.
3. **Given** `__all__` defined on all modules, **when** `from docvet import *` is executed, **then** only the intended top-level API (`Finding`) is produced.
4. **Given** `__all__` defined on all modules, **when** internal helpers (prefixed with `_`) are checked, **then** none are accessible via `*` import from any module (negative assertion).
5. **Given** modules that already have `__all__` (`__init__.py`, `checks/__init__.py`, `checks/coverage.py`), **when** reviewed, **then** they are unchanged or verified as correct.
6. **Given** all `__all__` additions, **when** `uv run pytest` is run, **then** all existing tests continue to pass.

## Tasks / Subtasks

- [x] Task 1: Add `__all__` to check submodules (AC: #1, #2, #4)
  - [x] 1.1 `src/docvet/checks/enrichment.py` — add `__all__ = ["check_enrichment"]`
  - [x] 1.2 `src/docvet/checks/freshness.py` — add `__all__ = ["check_freshness_diff", "check_freshness_drift"]`
  - [x] 1.3 `src/docvet/checks/griffe_compat.py` — add `__all__ = ["check_griffe_compat"]`
- [x] Task 2: Re-export check functions from `checks/__init__.py` (AC: #2)
  - [x] 2.1 Import all 5 check functions into `checks/__init__.py` and add to `__all__`
  - [x] 2.2 Verify `from docvet.checks import *` produces exactly `Finding` + 5 check functions
- [x] Task 3: Add `__all__` to config module with supporting public types (AC: #1)
  - [x] 3.1 `src/docvet/config.py` — add `__all__ = ["DocvetConfig", "EnrichmentConfig", "FreshnessConfig", "load_config"]`
- [x] Task 4: Add empty `__all__` to internal modules (AC: #1, #4)
  - [x] 4.1 `src/docvet/ast_utils.py` — add `__all__: list[str] = []`
  - [x] 4.2 `src/docvet/cli.py` — add `__all__: list[str] = []`
  - [x] 4.3 `src/docvet/discovery.py` — add `__all__: list[str] = []`
  - [x] 4.4 `src/docvet/reporting.py` — add `__all__: list[str] = []`
- [x] Task 5: Verify existing `__all__` modules are correct (AC: #5)
  - [x] 5.1 Verify `src/docvet/__init__.py` `__all__ = ["Finding"]` is correct
  - [x] 5.2 Verify `src/docvet/checks/__init__.py` `__all__` after Task 2 additions
  - [x] 5.3 Verify `src/docvet/checks/coverage.py` `__all__ = ["check_coverage"]` is correct
- [x] Task 6: Add tests for `__all__` exports (AC: #2, #3, #4)
  - [x] 6.1 Test `from docvet import *` produces only `Finding`
  - [x] 6.2 Test `from docvet.checks import *` produces `Finding` + 5 check functions
  - [x] 6.3 Test every module's `__all__` matches expectations (parametrized)
  - [x] 6.4 Negative test: verify `_` prefixed names not in any module's `__all__`
- [x] Task 7: Run all quality gates (AC: #6)
  - [x] 7.1 `uv run pytest` — all tests pass (712 passed, 1 skipped)
  - [x] 7.2 `uv run ruff check .` — no lint errors
  - [x] 7.3 `uv run docvet check --all` — freshness findings only (expected for uncommitted changes)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `TestAllModulesHaveAll::test_module_defines_all` (parametrized, 11 modules) | Pass |
| #2 | `TestChecksPackageReExports::test_checks_all_contains_finding_and_all_check_functions`, `test_checks_package_exposes_check_functions_as_attributes` | Pass |
| #3 | `TestTopLevelExports::test_docvet_all_contains_only_finding` | Pass |
| #4 | `TestNoPrivateNamesExported::test_no_underscore_prefixed_names_in_all` (parametrized, 11 modules), `TestInternalModulesExportNothing::test_internal_module_has_empty_all` | Pass |
| #5 | `TestCheckSubmoduleExports::test_coverage_all_contains_check_coverage`, `TestTopLevelExports::test_docvet_all_contains_only_finding` | Pass |
| #6 | Full test suite: 712 passed, 1 skipped | Pass |

## Dev Notes

### Current `__all__` Audit (as of story 9.1 completion)

| Module | Has `__all__` | Current Public Symbols | Action |
|--------|---------------|----------------------|--------|
| `__init__.py` | Yes `["Finding"]` | `Finding` | Verify (Task 5.1) |
| `checks/__init__.py` | Yes `["Finding"]` | `Finding` | Expand with check re-exports (Task 2) |
| `checks/coverage.py` | Yes `["check_coverage"]` | `check_coverage` | Verify (Task 5.3) |
| `checks/enrichment.py` | **No** | `check_enrichment` | Add `["check_enrichment"]` (Task 1.1) |
| `checks/freshness.py` | **No** | `check_freshness_diff`, `check_freshness_drift` | Add both (Task 1.2) |
| `checks/griffe_compat.py` | **No** | `check_griffe_compat` | Add `["check_griffe_compat"]` (Task 1.3) |
| `config.py` | **No** | `FreshnessConfig`, `EnrichmentConfig`, `DocvetConfig`, `load_config` | Add all 4 (Task 3.1) |
| `ast_utils.py` | **No** | `Symbol`, `get_docstring_range`, `get_body_range`, `get_signature_range`, `get_documented_symbols`, `map_lines_to_symbols` | Add `[]` — internal (Task 4.1) |
| `cli.py` | **No** | `OutputFormat`, `FreshnessMode`, `app`, `main`, `check`, etc. | Add `[]` — CLI internals (Task 4.2) |
| `discovery.py` | **No** | `DiscoveryMode`, `discover_files` | Add `[]` — internal (Task 4.3) |
| `reporting.py` | **No** | `format_terminal`, `format_markdown`, `format_verbose_header`, `write_report`, `determine_exit_code` | Add `[]` — internal (Task 4.4) |

### Public vs Internal Classification Rationale

**Public modules** (export intentional API per NFR66 + supporting types):
- `checks/` submodules: export their `check_*` functions — these are the programmatic API
- `config.py`: export `DocvetConfig`, `EnrichmentConfig`, `FreshnessConfig`, `load_config` — needed as parameters to check functions by programmatic users
- `checks/__init__.py`: re-export `Finding` + all 5 check functions — convenience import path

**Internal modules** (`__all__ = []`):
- `ast_utils.py`: `Symbol` and helpers are internal plumbing used by checks; not part of public API
- `cli.py`: Typer app, subcommands, enums are CLI scaffolding; entry point is `docvet.cli:app` console script
- `discovery.py`: File discovery is CLI-layer concern; programmatic users provide files directly to check functions
- `reporting.py`: Output formatting is CLI-layer concern; programmatic users consume `list[Finding]`

### `checks/__init__.py` Re-export Pattern

AC #2 requires `from docvet.checks import *` to produce `Finding` plus all 5 check functions. This requires importing them in `checks/__init__.py`:

```python
from docvet.checks.coverage import check_coverage
from docvet.checks.enrichment import check_enrichment
from docvet.checks.freshness import check_freshness_diff, check_freshness_drift
from docvet.checks.griffe_compat import check_griffe_compat

__all__ = [
    "Finding",
    "check_coverage",
    "check_enrichment",
    "check_freshness_diff",
    "check_freshness_drift",
    "check_griffe_compat",
]
```

**Gotcha**: The `griffe_compat` module has a `try/except ImportError` for griffe at module level. Importing `check_griffe_compat` in `checks/__init__.py` will trigger that import guard. This is safe — `check_griffe_compat` returns `[]` when griffe is not installed. The import itself won't fail.

### `__all__` Placement Convention

Place `__all__` immediately after the module-level imports, before any constants or class definitions. For modules with `from __future__ import annotations`, the order is:

```python
"""Module docstring."""

from __future__ import annotations

import ...

__all__ = [...]

# rest of module
```

For empty `__all__`, use the typed form for clarity: `__all__: list[str] = []`

### Test Strategy

Create a single test file `tests/unit/test_exports.py` with:
1. **Parametrized module `__all__` assertion**: For each module, verify `__all__` exists and matches expected content
2. **Wildcard import simulation**: Use `importlib` to load modules and check `__all__` rather than literal `from X import *` (which is lint-unfriendly in test code)
3. **Negative assertions**: Verify no `_`-prefixed names appear in any module's `__all__`
4. **Exact counts**: Assert `len(__all__)` to catch drift

### Previous Story Intelligence (9.1)

- Story 9.1 added `__all__ = ["Finding"]` to `__init__.py` and `from docvet.checks import Finding` re-export. This is already correct and should not be modified.
- Story 9.1 did NOT add `__all__` to any other module — all 8 remaining modules need it.
- The `[tool.docvet.enrichment]` config from 9.1 (`require-examples = ["class", "protocol"]`) means new test files won't trigger enrichment findings.
- All 678 existing tests pass — this is the baseline to maintain.

### Project Structure Notes

- All source files are in `src/docvet/` with `checks/` subpackage
- All files use `from __future__ import annotations`
- 88-char soft limit (formatter), 100-char hard limit (linter)
- Google-style docstrings throughout
- Test files go in `tests/unit/` — one test file per concern

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.2]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR66 — stable API surface]
- [Source: CLAUDE.md#Architecture — Module Layout]
- [Source: 9-1-fix-docvet-findings-on-own-codebase.md#Completion Notes — __all__ additions]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Circular import resolved: `checks/__init__.py` re-exports placed after `Finding` class definition
- Pre-existing `ty` warnings fixed: removed 4 unused `type: ignore` comments in `griffe_compat.py`
- ruff E402 resolved via per-file-ignore in `pyproject.toml` (required for circular import break)
- Pre-existing test `test_finding_exports_only_finding_class` updated to `test_finding_exports_finding_class` (no longer asserts `__all__ == ["Finding"]` since checks package now re-exports check functions)

### Completion Notes List

- Added `__all__` to all 11 `src/docvet/` modules (8 new, 3 existing verified/expanded)
- Public modules export their intended API: check functions, config types, Finding
- Internal modules (`ast_utils`, `cli`, `discovery`, `reporting`) export nothing (`__all__: list[str] = []`)
- `checks/__init__.py` re-exports all 5 check functions for convenience imports
- 34 new tests in `tests/unit/test_exports.py` covering all ACs
- Removed 4 stale `type: ignore` comments in `griffe_compat.py`
- Added E402 per-file-ignore for `checks/__init__.py` in `pyproject.toml`
- All quality gates pass: 723 tests, ruff clean, ty clean, format clean

### Change Log

- 2026-02-20: Implemented story 9.2 — added `__all__` exports to all 11 public modules
- 2026-02-20: Code review — fixed 4 findings (2 MEDIUM, 2 LOW)

### File List

- `src/docvet/checks/__init__.py` — expanded `__all__`, added check function re-exports
- `src/docvet/checks/enrichment.py` — added `__all__ = ["check_enrichment"]`
- `src/docvet/checks/freshness.py` — added `__all__ = ["check_freshness_diff", "check_freshness_drift"]`
- `src/docvet/checks/griffe_compat.py` — added `__all__ = ["check_griffe_compat"]`, removed stale type: ignore comments
- `src/docvet/config.py` — added `__all__` with 4 public types
- `src/docvet/ast_utils.py` — added `__all__: list[str] = []`
- `src/docvet/cli.py` — added `__all__: list[str] = []`
- `src/docvet/discovery.py` — added `__all__: list[str] = []`
- `src/docvet/reporting.py` — added `__all__: list[str] = []`
- `tests/unit/test_exports.py` — new file, 45 tests for `__all__` exports
- `tests/unit/checks/test_finding.py` — updated assertion for expanded `checks.__all__`
- `pyproject.toml` — added E402 per-file-ignore for `checks/__init__.py`
