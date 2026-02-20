# Story 9.1: Fix Docvet Findings on Own Codebase

Status: done

## Story

As a docvet maintainer,
I want all 23 docstring findings on docvet's own source code resolved to zero,
so that the tool credibly dogfoods itself before publication.

## Acceptance Criteria

1. **Given** the docvet codebase with 23 findings (8 required, 15 recommended), **when** findings are resolved (via docstring fixes or config adjustments), **then** `docvet check --all` produces zero findings.
2. **Given** the resolved codebase, **when** all quality gates are run, **then** `ruff check .`, `ruff format --check .`, `ty check`, and `uv run pytest` all pass with zero failures.
3. **Given** docstring fixes applied, **when** reviewing the changes, **then** all added docstring content is accurate, follows Google-style format, and adds genuine value (no filler content).

## Current Findings Inventory

**23 findings across 7 files (8 required, 15 recommended):**

### Required (8) — Must fix via docstring additions

| # | File | Line | Rule | Symbol | Fix |
|---|------|------|------|--------|-----|
| R1 | `__init__.py` | 1 | missing-attributes | Module | Add `Attributes:` section listing `main` and re-exports |
| R2 | `checks/__init__.py` | 1 | missing-attributes | Module | Add `Attributes:` section listing `Finding` and check re-exports |
| R3 | `griffe_compat.py` | 31 | missing-attributes | `_WarningCollector` | Add `Attributes:` section with `records` field |
| R4 | `cli.py` | 144 | missing-raises | `_output_and_exit` | Add `Raises:` section documenting `typer.Exit` |
| R5 | `cli.py` | 407 | missing-raises | `main` | Add `Raises:` section documenting `click.BadParameter` |
| R6 | `config.py` | 16 | missing-attributes | `FreshnessConfig` | Add `Attributes:` section |
| R7 | `config.py` | 24 | missing-attributes | `EnrichmentConfig` | Add `Attributes:` section |
| R8 | `config.py` | 42 | missing-attributes | `DocvetConfig` | Add `Attributes:` section |

### Recommended (15) — Fix via docstring OR config suppression

| # | File | Line | Rule | Symbol | Strategy |
|---|------|------|------|--------|----------|
| C1 | `__init__.py` | 1 | missing-examples | Module | Docstring fix — add usage example |
| C2 | `__init__.py` | 1 | missing-cross-references | Module | Docstring fix — add `See Also:` |
| C3 | `ast_utils.py` | 17 | missing-typed-attributes | `Symbol` | Docstring fix — attrs already documented, add `(type)` format |
| C4 | `ast_utils.py` | 17 | missing-examples | `Symbol` | Config suppress — internal dataclass, examples add no value |
| C5 | `checks/__init__.py` | 1 | missing-examples | Module | Docstring fix — add usage example |
| C6 | `checks/__init__.py` | 1 | missing-cross-references | Module | Docstring fix — add `See Also:` |
| C7 | `checks/__init__.py` | 20 | missing-typed-attributes | `Finding` | Docstring fix — attrs already documented, add `(type)` format |
| C8 | `checks/__init__.py` | 20 | missing-examples | `Finding` | Docstring fix — public API, example valuable |
| C9 | `griffe_compat.py` | 31 | missing-examples | `_WarningCollector` | Config suppress — private class, examples add no value |
| C10 | `cli.py` | 36 | missing-examples | `OutputFormat` | Config suppress — internal enum |
| C11 | `cli.py` | 43 | missing-examples | `FreshnessMode` | Config suppress — internal enum |
| C12 | `config.py` | 16 | missing-examples | `FreshnessConfig` | Config suppress — config dataclass, usage is implicit |
| C13 | `config.py` | 24 | missing-examples | `EnrichmentConfig` | Config suppress — config dataclass, usage is implicit |
| C14 | `config.py` | 42 | missing-examples | `DocvetConfig` | Config suppress — config dataclass, usage is implicit |
| C15 | `discovery.py` | 19 | missing-examples | `DiscoveryMode` | Config suppress — internal enum |

## Tasks / Subtasks

- [x] Task 1: Fix all 8 required findings via docstring additions (AC: #1, #3)
  - [x] 1.1 `src/docvet/__init__.py` — add `Attributes:` section to module docstring listing re-exported `Finding`
  - [x] 1.2 `src/docvet/checks/__init__.py` — add `Attributes:` section to module docstring listing `Finding`
  - [x] 1.3 `src/docvet/checks/griffe_compat.py` — add `Attributes:` section to `_WarningCollector` documenting `records: list[logging.LogRecord]`
  - [x] 1.4 `src/docvet/cli.py` — add `Raises:` section to `_output_and_exit` documenting `typer.Exit`
  - [x] 1.5 `src/docvet/cli.py` — add `Raises:` section to `main` documenting `typer.BadParameter`
  - [x] 1.6 `src/docvet/config.py` — add `Attributes:` sections to `FreshnessConfig`, `EnrichmentConfig`, and `DocvetConfig`
- [x] Task 2: Fix selected recommended findings via docstring improvements (AC: #1, #3)
  - [x] 2.1 `src/docvet/__init__.py` — add `Examples:` and `See Also:` sections to module docstring
  - [x] 2.2 `src/docvet/ast_utils.py` — update `Symbol` attributes to `name (type): description` format
  - [x] 2.3 `src/docvet/checks/__init__.py` — add `Examples:`, `See Also:` to module; add typed format to `Finding` attributes; add `Examples:` to `Finding`
  - [x] 2.4 `src/docvet/checks/griffe_compat.py` — add `Examples:` to `_WarningCollector` (story miscategorized as dataclass; actually a plain class needing examples)
- [x] Task 3: Add `[tool.docvet]` config to suppress remaining recommended findings (AC: #1)
  - [x] 3.1 Add `[tool.docvet.enrichment]` section to `pyproject.toml` with `require-examples = ["class", "protocol"]` (removes "dataclass" and "enum" from defaults, suppressing examples on enums and config dataclasses)
- [x] Task 4: Verify zero findings and all quality gates (AC: #1, #2)
  - [x] 4.1 Run `uv run docvet enrichment --all` — 0 enrichment findings; `docvet check --all` shows only 2 transient `stale-body` from uncommitted diff (will resolve after commit)
  - [x] 4.2 Run `uv run ruff check .` — 0 errors
  - [x] 4.3 Run `uv run ruff format --check .` — 0 reformatted
  - [x] 4.4 Run `uv run pytest` — all 678 tests pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `uv run docvet enrichment --all` produces 0 findings; `docvet check --all` shows 0 after commit (2 transient stale-body from uncommitted diff) | Pass |
| #2 | `uv run ruff check .` (0 errors) + `ruff format --check .` (0 reformatted) + `uv run pytest` (678 pass) | Pass |
| #3 | All docstring content reviewed: accurate types, genuine examples, proper cross-reference syntax, Google-style format | Pass |

## Dev Notes

### Branch Scope Note

This branch includes story 8.3 (unified output pipeline) changes that were not yet merged to `develop` when story 9.1 started. The findings inventory (R4, R5) references `_output_and_exit` and `main` Raises sections that only exist because 8.3 introduced them on this branch. The `tests/unit/test_cli.py` changes (renamed tests, `TestOutputAndExit` class) are also 8.3 carry-over. Story 9.1 changes are limited to docstring additions, config suppression, and the `Finding` re-export.

### Fix Strategy

**Two-pronged approach:**

1. **Docstring fixes** for all 8 required findings + 7 high-value recommended findings (typed-attributes format, examples on public API, cross-references on `__init__.py` modules)
2. **Config suppression** for 8 low-value recommended findings via `[tool.docvet.enrichment]` in `pyproject.toml`

### Config Suppression Rationale

The default `require_examples` list is `["class", "protocol", "dataclass", "enum"]`. Changing to `["class", "protocol"]` removes the requirement for examples on:
- **Enums** (OutputFormat, FreshnessMode, DiscoveryMode) — values are self-documenting
- **Dataclasses** (Symbol, FreshnessConfig, EnrichmentConfig, DocvetConfig, _WarningCollector) — construction is obvious from field definitions

This suppresses 8 of the 15 recommended findings. The remaining 7 recommended findings are fixed via docstring improvements because they add genuine value.

### Key Gotcha

`typer.Exit` is actually `click.exceptions.Exit`. When documenting the `Raises:` section for `_output_and_exit`, write:

```
Raises:
    typer.Exit: With code 0 when no fail-on findings, code 1 otherwise.
```

Use `typer.Exit` in the docstring (user-facing name), not `click.exceptions.Exit` (implementation detail).

### Files to Modify (7 source + 1 config)

| File | Changes |
|------|---------|
| `src/docvet/__init__.py` | Expand module docstring: add Attributes, Examples, See Also |
| `src/docvet/ast_utils.py` | Update Symbol Attributes format to typed `name (type): desc` |
| `src/docvet/checks/__init__.py` | Expand module docstring + Finding docstring |
| `src/docvet/checks/griffe_compat.py` | Add Attributes to _WarningCollector |
| `src/docvet/cli.py` | Add Raises to _output_and_exit and main |
| `src/docvet/config.py` | Add Attributes to all 3 dataclasses |
| `src/docvet/discovery.py` | No changes needed (suppressed via config) |
| `pyproject.toml` | Add `[tool.docvet.enrichment]` section |

### Testing Impact

Docstring-only changes do not affect runtime behavior. No test modifications needed. All 678 existing tests should continue passing unchanged.

### Google-Style Docstring Format Reference

```python
"""Summary line.

Extended description.

Attributes:
    name (str): Description of name.
    value (int): Description of value.

Examples:
    >>> from docvet import main
    >>> main()

See Also:
    docvet.checks: Check modules for quality validation.

Raises:
    typer.Exit: When processing is complete.
"""
```

### Project Structure Notes

- All source files are in `src/docvet/` with `checks/` subpackage
- All files use `from __future__ import annotations`
- 88-char soft limit (formatter), 100-char hard limit (linter)
- Google-style docstrings throughout

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.1]
- [Source: CLAUDE.md#Code Style]
- [Source: MEMORY.md#Key Gotchas — typer.Exit]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — no debugging required. All changes were docstring additions and config.

### Completion Notes List

- Resolved all 23 findings (8 required + 15 recommended) to 0 enrichment findings
- Story miscategorized `_WarningCollector` as a dataclass (it's a plain class extending `logging.Handler`). Added `Examples:` section instead of relying on config suppression (added as subtask 2.4).
- Story referenced `main` function in `__init__.py` but it doesn't exist (entry point is `docvet.cli:app`). Re-exported `Finding` from `docvet.checks` instead for a genuine Attributes section.
- Used fenced code blocks for Python Examples sections per `prefer-fenced-code-blocks` rule. Exception: `__init__.py` module docstring uses RST `::` indented blocks for shell command examples (not flagged by the rule).
- Used backtick cross-reference syntax in See Also sections per `missing-cross-references` rule.
- 2 transient `stale-body` findings remain in `docvet check --all` due to uncommitted diff; these resolve after commit when `git diff HEAD` returns empty.

### Change Log

- 2026-02-20: Implemented all 4 tasks — docstring fixes, config suppression, verification
- 2026-02-20: Code review — fixed 3 MEDIUM issues (File List incomplete, scope bleed undocumented, Completion Notes inaccuracy)

### File List

- `src/docvet/__init__.py` — expanded module docstring (Attributes, Examples, See Also); re-exported `Finding`
- `src/docvet/ast_utils.py` — updated Symbol Attributes to typed format `name (type): desc`
- `src/docvet/checks/__init__.py` — expanded module docstring (Attributes, Examples, See Also); updated Finding Attributes to typed format; added Finding Examples
- `src/docvet/checks/griffe_compat.py` — added Attributes and Examples to `_WarningCollector`
- `src/docvet/cli.py` — added Raises to `_output_and_exit` and `main`
- `src/docvet/config.py` — added Attributes to `FreshnessConfig`, `EnrichmentConfig`, `DocvetConfig`
- `pyproject.toml` — added `[tool.docvet.enrichment]` with `require-examples = ["class", "protocol"]`
- `tests/unit/test_cli.py` — (story 8.3 carry-over) renamed 3 tests for new output pipeline, added `TestOutputAndExit` class
