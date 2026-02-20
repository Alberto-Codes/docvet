# Story 9.1: Fix Docvet Findings on Own Codebase

Status: ready-for-dev

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

- [ ] Task 1: Fix all 8 required findings via docstring additions (AC: #1, #3)
  - [ ] 1.1 `src/docvet/__init__.py` — add `Attributes:` section to module docstring listing `main` and any re-exported symbols
  - [ ] 1.2 `src/docvet/checks/__init__.py` — add `Attributes:` section to module docstring listing `Finding` and check function re-exports
  - [ ] 1.3 `src/docvet/checks/griffe_compat.py` — add `Attributes:` section to `_WarningCollector` documenting `records: list[logging.LogRecord]`
  - [ ] 1.4 `src/docvet/cli.py` — add `Raises:` section to `_output_and_exit` documenting `typer.Exit` (note: this is actually `click.exceptions.Exit`)
  - [ ] 1.5 `src/docvet/cli.py` — add `Raises:` section to `main` documenting `click.BadParameter`
  - [ ] 1.6 `src/docvet/config.py` — add `Attributes:` sections to `FreshnessConfig`, `EnrichmentConfig`, and `DocvetConfig`
- [ ] Task 2: Fix selected recommended findings via docstring improvements (AC: #1, #3)
  - [ ] 2.1 `src/docvet/__init__.py` — add `Examples:` and `See Also:` sections to module docstring
  - [ ] 2.2 `src/docvet/ast_utils.py` — update `Symbol` attributes to `name (type): description` format
  - [ ] 2.3 `src/docvet/checks/__init__.py` — add `Examples:`, `See Also:` to module; add typed format to `Finding` attributes; add `Examples:` to `Finding`
- [ ] Task 3: Add `[tool.docvet]` config to suppress remaining recommended findings (AC: #1)
  - [ ] 3.1 Add `[tool.docvet.enrichment]` section to `pyproject.toml` with `require-examples = ["class", "protocol"]` (removes "dataclass" and "enum" from defaults, suppressing examples on enums, config dataclasses, and private classes)
- [ ] Task 4: Verify zero findings and all quality gates (AC: #1, #2)
  - [ ] 4.1 Run `uv run docvet check --all` — expect 0 findings
  - [ ] 4.2 Run `uv run ruff check .` — expect 0 errors
  - [ ] 4.3 Run `uv run ruff format --check .` — expect 0 reformatted
  - [ ] 4.4 Run `uv run pytest` — expect all 678 tests pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `uv run docvet check --all` produces "0 findings" | |
| #2 | `uv run ruff check .` + `ruff format --check .` + `uv run pytest` all green | |
| #3 | Manual review of docstring additions for accuracy and Google-style compliance | |

## Dev Notes

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

### Debug Log References

### Completion Notes List

### File List
