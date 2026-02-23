---
title: 'Extend module-level enrichment rules to standalone modules'
slug: 'extend-module-enrichment-rules'
created: '2026-02-23'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: [python, ast, dataclasses]
files_to_modify: [src/docvet/checks/enrichment.py, tests/unit/checks/test_enrichment.py, src/docvet/cli.py, src/docvet/config.py, src/docvet/discovery.py, src/docvet/ast_utils.py, src/docvet/reporting.py, src/docvet/checks/freshness.py, src/docvet/checks/coverage.py, src/docvet/checks/griffe_compat.py]
code_patterns: [_check_missing_examples, _check_missing_cross_references, _is_init_module, _RULE_DISPATCH, EnrichmentConfig]
test_patterns: [test_missing_examples_when_non_init_module, test_cross_refs_when_non_init_module, module_source_factory_inline, get_documented_symbols]
---

# Tech-Spec: Extend module-level enrichment rules to standalone modules

**Created:** 2026-02-23

## Overview

### Problem Statement

The `missing-examples` and `missing-cross-references` enrichment rules currently only apply to `__init__.py` module docstrings. Standalone modules (`cli.py`, `discovery.py`, `ast_utils.py`, `reporting.py`, plus check submodules and `config.py`) are silently skipped. With auto-generated API reference pages (Epic 13), every public module now renders as a standalone documentation page. Sparse one-liner docstrings create a visible UX gap — the page looks broken or incomplete to readers.

### Solution

Remove `_is_init_module` guards from both `_check_missing_examples` and `_check_missing_cross_references` (Option C from party mode discussion). Both rules will fire on all module-level docstrings. Users who don't want it on internal modules can add config suppression. Enrich all 9 standalone module docstrings to pass the extended rules. Aligns with project convention: "every symbol deserves its natural language representation."

### Scope

**In Scope:**
- Remove `_is_init_module` guard from `_check_missing_examples` (enrichment.py:1045)
- Remove `_is_init_module` guard from `_check_missing_cross_references` (enrichment.py:1140)
- Update Finding message in `_check_missing_cross_references` to drop `__init__.py` wording
- Update/add ~8 tests for the changed behavior
- Enrich module docstrings for 9 standalone modules with Examples + See Also sections
- Add comment to `_is_init_module` noting its remaining consumer (`_check_missing_attributes`)

**Out of Scope:**
- `_check_missing_attributes` — stays `__init__.py`-only by design (Attributes: is a package concern)
- No config changes or new config options
- No AST `__all__` detection in enrichment module
- No changes to `_is_init_module` helper function itself

## Context for Development

### Codebase Patterns

- `_check_*` uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
- Config gating in orchestrator via `_RULE_DISPATCH` table, NOT in `_check_*` functions (except `_check_missing_examples` which reads `config.require_examples` internally)
- `_is_init_module(file_path)` helper at line 796 checks path equality/suffix
- Module symbols have `symbol.kind == "module"` and `name == "<module>"`, `line == 1`
- Finding messages use `f"Module '{symbol.name}' ..."` pattern

#### `_check_missing_examples` module gating (CRITICAL)

The module branch (line 1044) returns a Finding **directly** — it does NOT check list membership. It only checks if `config.require_examples` is truthy (non-empty list). Default is `["class", "protocol", "dataclass", "enum"]` — always truthy. So after guard removal, ALL modules without Examples get flagged with default config. The list membership check at line 1083 only applies to the class branch.

Flow after guard removal:
1. `"Examples" in sections` → No → continue
2. `not config.require_examples` → False (default list is truthy) → continue
3. `symbol.kind == "module"` → True → enter module branch
4. ~~`_is_init_module` guard~~ → REMOVED
5. Return Finding

#### `_check_missing_cross_references` two-branch design

- **Branch A** (line 1140): Module missing `See Also:` entirely → Finding. Guard: `_is_init_module` (REMOVING)
- **Branch B** (line 1155+): Any symbol with `See Also:` but lacking xref syntax → Finding. Already universal (NO CHANGE)
- After removing guard from Branch A, standalone modules missing `See Also:` entirely get flagged
- Standalone modules WITH `See Also:` but bad syntax already caught by Branch B

#### `_RULE_DISPATCH` table (line 1258)

```python
("require_examples", _check_missing_examples),      # list[str] — truthy check
("require_cross_references", _check_missing_cross_references),  # bool — True/False
```

Dispatch uses `if getattr(config, attr):` — for lists, empty = skip, non-empty = run.

### Files to Reference

| File | Purpose | Change Type |
| ---- | ------- | ----------- |
| `src/docvet/checks/enrichment.py` | Guards at lines 1045 and 1140 | Guard removal + message update + comment |
| `tests/unit/checks/test_enrichment.py` | 3 tests to invert, 5 new tests | Test changes |
| `src/docvet/cli.py` | One-liner docstring, `__all__: list[str] = []` | Docstring enrichment (internal tier) |
| `src/docvet/config.py` | One-liner docstring, `__all__ = [4 items]` | Docstring enrichment (public tier) |
| `src/docvet/discovery.py` | One-liner docstring, `__all__: list[str] = []` | Docstring enrichment (internal tier) |
| `src/docvet/ast_utils.py` | One-liner docstring, `__all__: list[str] = []` | Docstring enrichment (internal tier) |
| `src/docvet/reporting.py` | One-liner docstring, `__all__: list[str] = []` | Docstring enrichment (internal tier) |
| `src/docvet/checks/enrichment.py` | 5-line docstring, `__all__ = ["check_enrichment"]` | Docstring enrichment (public tier) |
| `src/docvet/checks/freshness.py` | One-liner docstring, `__all__ = [2 items]` | Docstring enrichment (public tier) |
| `src/docvet/checks/coverage.py` | 5-line docstring, `__all__ = ["check_coverage"]` | Docstring enrichment (public tier) |
| `src/docvet/checks/griffe_compat.py` | 5-line docstring, `__all__ = ["check_griffe_compat"]` | Docstring enrichment (public tier) |

### Technical Decisions

- **Option C chosen**: Extend both rules to all modules, let config suppress. No special-casing by `__all__` status.
- **`_check_missing_attributes` stays `__init__.py`-only**: Module-level `Attributes:` is a package-level concern; standalone modules rarely have meaningful module-level attributes.
- **Message wording**: Drop `__init__.py` from cross-references Finding message to be file-type-neutral. Examples message already neutral (`"Module '<module>' has no Examples: section"`).
- **Blast radius expanded**: Deep investigation revealed 9 modules need enrichment (not 4). All check submodules and `config.py` also lack Examples + See Also.
- **`_is_init_module` comment**: Add clarifying comment noting single remaining consumer to prevent future "dead code" cleanup.
- **Two-tier docstring pattern**: Internal modules (empty `__all__`) show CLI usage in Examples; public-API modules (non-empty `__all__`) show programmatic import + function call in Examples. Both use backtick cross-references in See Also.

### Reference Docstring Patterns

**Internal module tier** (empty `__all__` — cli, discovery, ast_utils, reporting):

```python
"""One-sentence summary (existing).

Expanded description of internal role and architecture placement.

Examples:
    This module is invoked internally by the CLI entry point::

        $ docvet check --all

See Also:
    `docvet.checks`: Public API re-exports for external consumers.
"""
```

**Public-API module tier** (non-empty `__all__` — config, enrichment, freshness, coverage, griffe_compat):

```python
"""One-sentence summary (existing).

Expanded description (existing or new).

Examples:
    Programmatic usage::

        >>> from docvet.checks import check_enrichment
        >>> findings = check_enrichment(source, tree, config, "app.py")

See Also:
    `docvet.checks`: Package-level re-exports.
    `docvet.config`: Configuration dataclasses.
"""
```

## Implementation Plan

### Tasks

- [x] Task 1: Remove `_is_init_module` guard from `_check_missing_examples`
  - File: `src/docvet/checks/enrichment.py`
  - Action: Delete lines 1045-1046 (`if not _is_init_module(file_path): return None`). The module branch at line 1044 (`if symbol.kind == "module":`) remains, and the Finding return at lines 1047-1054 becomes the direct path for all modules.
  - Notes: No message change needed — existing message `"Module '{symbol.name}' has no Examples: section"` is already file-type-neutral.

- [x] Task 2: Remove `_is_init_module` guard from `_check_missing_cross_references` and update message
  - File: `src/docvet/checks/enrichment.py`
  - Action: Change line 1140 from `if symbol.kind == "module" and _is_init_module(file_path):` to `if symbol.kind == "module":`. Update the Finding message at lines 1148-1149 from `f"Module '{symbol.name}' is an __init__.py but has no See Also: section"` to `f"Module '{symbol.name}' has no See Also: section"`.
  - Notes: Branch B (line 1155+) is unchanged — it already applies to all symbol kinds.

- [x] Task 3: Update the `_check_missing_cross_references` docstring
  - File: `src/docvet/checks/enrichment.py`
  - Action: Update the function docstring to reflect the changed scope. Branch A description should say "any module" instead of "`__init__.py` module". Remove references to `__init__.py` restriction.

- [x] Task 4: Add comment to `_is_init_module` helper
  - File: `src/docvet/checks/enrichment.py`
  - Action: Add a comment above the `_is_init_module` function (before line 796): `# Used only by _check_missing_attributes (module Attributes: is __init__.py-only by design).`
  - Notes: Prevents future contributors from removing it as dead code.

- [x] Task 5: Invert 3 existing tests
  - File: `tests/unit/checks/test_enrichment.py`
  - Action: Modify these tests to expect a Finding instead of None:
    - `test_missing_examples_when_non_init_module_returns_none` (line ~2842): Change `assert result is None` to assert a Finding with `rule="missing-examples"`, `file="regular.py"`, `category="recommended"`. Update test name to `test_missing_examples_when_non_init_module_returns_finding`.
    - `test_missing_examples_when_non_init_module_no_finding` (line ~3048): Change assertion from empty findings to expect one `missing-examples` finding. Update test name to `test_missing_examples_when_non_init_module_has_finding`.
    - `test_cross_refs_when_non_init_module_no_see_also_returns_none` (line ~3209): Change `assert result is None` to assert a Finding with `rule="missing-cross-references"`, `message="Module '<module>' has no See Also: section"`, `category="recommended"`. Update test name to `test_cross_refs_when_non_init_module_no_see_also_returns_finding`.
  - Notes: Verify all 6 Finding fields (file, line, symbol, rule, message, category) per dev quality checklist.

- [x] Task 6: Add 5 new tests
  - File: `tests/unit/checks/test_enrichment.py`
  - Action: Add these tests using the existing inline module fixture pattern (`ast.parse(source)` → `get_documented_symbols` → filter `kind == "module"`):
    - `test_missing_examples_when_non_init_module_with_examples_returns_none`: Source has `Examples:` section, `file_path="regular.py"`, config default → assert None.
    - `test_cross_refs_when_non_init_module_with_see_also_returns_none`: Source has `See Also:` section with backtick xrefs, `file_path="regular.py"`, config default → assert None.
    - `test_missing_examples_when_require_examples_empty_non_init_module_returns_none`: Source lacks Examples, `file_path="regular.py"`, `config=EnrichmentConfig(require_examples=[])` → assert None (rule entirely skipped by dispatch gate).
    - `test_cross_refs_when_non_init_module_require_cross_refs_false_returns_none`: Source lacks See Also, `file_path="regular.py"`, `config=EnrichmentConfig(require_cross_references=False)` → assert None (config disables rule via dispatch gate).
    - `test_cross_refs_when_non_init_module_see_also_without_xrefs_returns_finding`: Source has `See Also:` section with plain text (no backticks, no markdown links, no sphinx roles), `file_path="regular.py"`, config default → assert Finding from Branch B with `message` containing `"lacks cross-reference syntax"` (verifies two-branch interaction for standalone modules).
  - Notes: `__init__.py` regression is already covered by existing tests `test_missing_examples_when_init_module_without_section_returns_finding` (line ~2778) and `test_cross_refs_when_init_module_missing_see_also_returns_finding` (line ~3181). The two edge-case tests above provide higher-value coverage: config disabling and Branch B interaction.

- [x] Task 7: Enrich internal module docstrings (4 modules)
  - Files: `src/docvet/cli.py`, `src/docvet/discovery.py`, `src/docvet/ast_utils.py`, `src/docvet/reporting.py`
  - Action: Replace the one-liner module docstring in each file with an enriched version following the internal-tier pattern. Each must include:
    - One-sentence summary (keep existing)
    - Expanded description (2-3 sentences on internal role)
    - `Examples:` section showing CLI usage (e.g., `$ docvet check --all`)
    - `See Also:` section with backtick cross-references to related modules
  - Content guidance per module:
    - **cli.py**: Examples show `$ docvet check`, `$ docvet enrichment`. See Also → `docvet.checks`, `docvet.config`, `docvet.discovery`.
    - **discovery.py**: Examples show `$ docvet check --staged`, `$ docvet check --all`. See Also → `docvet.cli`, `docvet.checks`.
    - **ast_utils.py**: Examples show programmatic usage `from docvet.ast_utils import get_documented_symbols`. See Also → `docvet.checks.enrichment`, `docvet.checks.freshness`.
    - **reporting.py**: Examples show `$ docvet check` (which triggers reporting). See Also → `docvet.cli`, `docvet.checks`.
  - Notes: Keep docstrings genuine and accurate. These are internal modules — don't oversell.

- [x] Task 8: Enrich public-API module docstrings (5 modules)
  - Files: `src/docvet/config.py`, `src/docvet/checks/enrichment.py`, `src/docvet/checks/freshness.py`, `src/docvet/checks/coverage.py`, `src/docvet/checks/griffe_compat.py`
  - Action: Extend each module docstring with Examples + See Also sections following the public-tier pattern. Keep existing expanded descriptions where present (enrichment, coverage, griffe_compat). Each must include:
    - One-sentence summary (keep existing)
    - Expanded description (keep existing or add 2-3 sentences)
    - `Examples:` section showing programmatic import + function call
    - `See Also:` section with backtick cross-references to related modules
  - Content guidance per module:
    - **config.py**: Examples show `from docvet.config import load_config` and `EnrichmentConfig()`. See Also → `docvet.cli`, `docvet.checks`.
    - **enrichment.py**: Examples show `from docvet.checks import check_enrichment` and calling with source/tree/config. See Also → `docvet.config`, `docvet.ast_utils`, `docvet.checks`.
    - **freshness.py**: Examples show `from docvet.checks import check_freshness_diff` with parameters. See Also → `docvet.config`, `docvet.checks`.
    - **coverage.py**: Examples show `from docvet.checks import check_coverage` with parameters. See Also → `docvet.checks`, `docvet.config`.
    - **griffe_compat.py**: Examples show `from docvet.checks import check_griffe_compat` with parameters. See Also → `docvet.checks`, `docvet.config`.
  - Notes: For check submodules, show imports from `docvet.checks` (the public re-export surface), not direct imports from the submodule.

- [x] Task 9: Run quality gates and validate
  - Action: Run all quality gates in sequence:
    1. `uv run ruff check .` — lint passes
    2. `uv run ruff format --check .` — formatting passes
    3. `uv run ty check` — type checking passes
    4. `uv run pytest` — all tests pass (737 existing + 5 new)
    5. `docvet check --all` — zero findings on own codebase
  - Notes: If `docvet check --all` surfaces additional findings beyond the 9 modules (e.g., `checks/_finding.py`), investigate and fix. The `_finding.py` module is private (`_` prefix) but still has a module docstring that will be checked.

### Acceptance Criteria

- [x] AC 1: Given a standalone module (non-`__init__.py`) without an `Examples:` section, when `_check_missing_examples` is called with default config, then a Finding is returned with `rule="missing-examples"`, `category="recommended"`.

- [x] AC 2: Given a standalone module without a `See Also:` section, when `_check_missing_cross_references` is called with default config, then a Finding is returned with `rule="missing-cross-references"`, `category="recommended"`, and the message does NOT contain `__init__.py`.

- [x] AC 3: Given a standalone module WITH an `Examples:` section, when `_check_missing_examples` is called, then no Finding is returned (None).

- [x] AC 4: Given a standalone module WITH a `See Also:` section containing backtick cross-references, when `_check_missing_cross_references` is called, then no Finding is returned (None).

- [x] AC 5: Given `config.require_examples = []` (empty list), when `_check_missing_examples` is called on any module, then no Finding is returned (rule skipped entirely by dispatch gate).

- [x] AC 6: Given an `__init__.py` module without `Examples:` or `See Also:` sections, when the respective check functions are called, then Findings are still returned (regression: `__init__.py` behavior unchanged).

- [x] AC 7: Given `_check_missing_attributes` is called on a standalone module, then no Finding is returned (guard intentionally NOT extended).

- [x] AC 8: Given the complete docvet codebase with enriched docstrings, when `docvet check --all` is run, then zero findings are reported for `missing-examples` and `missing-cross-references` rules.

- [x] AC 9: Given the complete test suite, when `uv run pytest` is run, then all tests pass including the 3 inverted tests and 5 new tests.

## Additional Context

### Dependencies

None — no new packages, no config schema changes, no CI/CD modifications.

### Testing Strategy

**Unit tests — direct function calls (8 tests):**

| # | Test | Type | Assertion |
|---|------|------|-----------|
| 1 | `test_missing_examples_when_non_init_module_returns_finding` | Inverted | Finding with all 6 fields verified |
| 2 | `test_missing_examples_when_non_init_module_has_finding` | Inverted | Integration: check_enrichment returns finding |
| 3 | `test_cross_refs_when_non_init_module_no_see_also_returns_finding` | Inverted | Finding with updated message (no `__init__.py`) |
| 4 | `test_missing_examples_when_non_init_module_with_examples_returns_none` | New | None (positive path) |
| 5 | `test_cross_refs_when_non_init_module_with_see_also_returns_none` | New | None (positive path) |
| 6 | `test_missing_examples_when_require_examples_empty_non_init_module_returns_none` | New | None (config disables) |
| 7 | `test_cross_refs_when_non_init_module_require_cross_refs_false_returns_none` | New | None (config disables rule) |
| 8 | `test_cross_refs_when_non_init_module_see_also_without_xrefs_returns_finding` | New | Finding from Branch B (two-branch interaction) |

**Integration test:**
- `docvet check --all` passing clean on own codebase validates all 9 enriched docstrings end-to-end.

**Regression safety:**
- All 737 existing tests must continue to pass.
- `__init__.py` test behavior verified via regression tests (tests 7-8) and existing test suite.

### Notes

- **GitHub Issue:** #80
- **Party mode:** Established Option C consensus; party review found 9 gaps (all addressed in Step 2).
- **Scope expansion:** Deep investigation revealed 9 modules need enrichment (not 4 from original issue).
- **`_check_missing_examples` message:** Already file-type-neutral — no change needed.
- **`_check_missing_cross_references` Branch B:** Already universal — no change needed.
- **`checks/_finding.py`:** Private module (starts with `_`). May or may not be checked by `docvet check --all` depending on file discovery. Investigate during Task 9 if findings appear.
- **Task ordering rationale:** Rule changes first (Tasks 1-4), then tests (Tasks 5-6), then docstrings internal-tier first (Task 7), public-tier second (Task 8), validation last (Task 9). Rule changes enable test verification; tests confirm behavior before docstring work; docstrings satisfy the quality gate.
- **Quality gates:** `ruff check .`, `ruff format --check .`, `ty check`, `pytest`, `docvet check --all`.
- **PR note:** This is a behavioral change — `docvet check` will now flag standalone modules missing Examples/See Also that were previously silently skipped. Mention in PR body and changelog. Users can suppress via `require_examples = []` or `require_cross_references = false` in `[tool.docvet.enrichment]`.
