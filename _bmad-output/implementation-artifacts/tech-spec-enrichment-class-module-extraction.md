---
title: 'Extract class/module checks to _class_module.py'
slug: 'enrichment-class-module-extraction'
created: '2026-03-23'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+']
files_to_modify:
  - src/docvet/checks/enrichment/__init__.py (remove ~824 lines, add deferred import)
  - src/docvet/checks/enrichment/_class_module.py (new, ~850 lines with docstring/imports)
code_patterns:
  - 'Deferred import at bottom of __init__.py — same pattern as _forward.py (L269)'
  - '_RULE_DISPATCH references check functions by name — imports must land before dispatch table'
  - 'Check functions depend on _extract_section_content from __init__.py — relative import from parent'
  - 'Zero external API changes — all consumers import from docvet.checks.enrichment'
  - 'Import style: absolute for external (docvet.ast_utils, docvet.checks._finding, docvet.config), relative for parent private (from . import _extract_section_content)'
  - 'Single file extraction (~850 lines) — exceeds 500-line gate but follows _forward.py precedent (662 lines). Defer further split unless it grows.'
test_patterns:
  - 'Tests import from docvet.checks.enrichment — unchanged after extraction'
  - 'conftest.py resets _active_style — unaffected by this change'
---

# Tech-Spec: Extract class/module checks to _class_module.py

**Created:** 2026-03-23

## Overview

### Problem Statement

`src/docvet/checks/enrichment/__init__.py` is 2,259 lines — 4.5x the project's 500-line module size gate. The class/module check block (L310-L1133) is the largest self-contained concern at ~824 lines, covering attribute checks, example checks, cross-reference checks, and fenced code block checks plus their 11 supporting helpers.

### Solution

Extract L310-L1133 into `enrichment/_class_module.py`. Import back into `__init__.py` with a deferred import block (same proven pattern as `_forward.py` at L269). Zero external API changes — all consumers continue importing from `docvet.checks.enrichment`.

### Scope

**In Scope:**
- Extract 6 check functions + 11 helpers + 5 constants (L310-L1132) to `_class_module.py`
- Add deferred import in `__init__.py` to re-import extracted symbols
- Verify all tests pass with zero import changes

**Out of Scope:**
- Extracting other concerns (params, deprecation, reverse, late rules — future PRs)
- Test file splits
- Eliminating `_active_style` global
- Any behavioral changes

## Context for Development

### Codebase Patterns

- `enrichment/` is already a package with `__init__.py` (2,259 lines) + `_forward.py` (662 lines)
- `_forward.py` established the deferred import pattern: symbols defined in `__init__.py` first, then `from ._forward import ...` at L269 with `# noqa: E402`
- Check functions use the uniform 5-parameter dispatch signature (`symbol`, `sections`, `node_index`, `config`, `file_path`) for `_RULE_DISPATCH` compatibility
- `_extract_section_content` (L223 in `__init__.py`) is a shared helper used by multiple check blocks — stays in `__init__.py`, imported by `_class_module.py`
- `_SEE_ALSO` constant (L70) and `_XREF_MD_LINK`/`_XREF_SPHINX` patterns (L116-117) stay in `__init__.py` — used by `_check_missing_cross_references` in the extraction block. These must be imported from parent.
- `_ENUM_NAMES` constant (L394) moves with `_is_enum` — only used by that function
- `_check_fenced_code_blocks_extra` is NOT in `_RULE_DISPATCH` — it's called directly from the `check_enrichment` orchestrator at L2254. Must be imported for orchestrator access.
- `_NodeT` type alias is re-exported from `_forward.py` — used in check function signatures via `node_index: dict[int, _NodeT]`

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/checks/enrichment/__init__.py` | Source — remove L310-L1133, add deferred import |
| `src/docvet/checks/enrichment/_forward.py` | Reference for proven extraction pattern (imports, docstring) |
| `src/docvet/checks/enrichment/_class_module.py` | New file — receives extracted code |
| `tests/unit/checks/test_enrichment.py` | Primary test file (3,756 lines) — must pass unchanged |
| `tests/unit/checks/test_enrichment_sphinx.py` | Sphinx test file (448 lines) — must pass unchanged |
| `tests/unit/checks/test_prefer_fenced_code_blocks.py` | Imports `_check_prefer_fenced_code_blocks` and `_check_fenced_code_blocks_extra` — must pass unchanged |
| `tests/unit/checks/test_undocumented_init_params.py` | Canary for `_find_init_method` re-import — must pass unchanged |

### Technical Decisions

- **Deferred import placement**: New `from ._class_module import ...` block goes after the existing `_forward` import block (~L285 after extraction shifts lines). Same `# noqa: E402` pattern.
- **Dependencies from parent**: `_class_module.py` needs `_extract_section_content`, `_SEE_ALSO`, `_XREF_MD_LINK`, `_XREF_SPHINX` from `__init__.py` (relative import), plus `Finding`, `Symbol`, `module_display_name`, `EnrichmentConfig`, `_NodeT` (absolute/re-exported imports). No circular dependency since all are defined before the deferred import line.
- **Import style**: Absolute for external packages (`from docvet.ast_utils import Symbol, module_display_name`, `from docvet.checks._finding import Finding`, `from docvet.config import EnrichmentConfig`). Relative for parent private helpers (`from . import _extract_section_content, _SEE_ALSO, _XREF_MD_LINK, _XREF_SPHINX`). `_NodeT` via `from ._forward import _NodeT`. This **extends** the `_forward.py` pattern — `_forward.py` uses only absolute imports because it doesn't need parent-private helpers. `_class_module.py` needs `_extract_section_content` and section constants that have no absolute import path, so relative imports from parent are required.
- **Import ordering constraint**: The relative imports from parent (`_extract_section_content`, `_SEE_ALSO`, `_XREF_MD_LINK`, `_XREF_SPHINX`) work because Python resolves the parent `__init__.py` top-level definitions before the child module's import-time code runs. All four symbols are defined at L70-L223, well before the deferred import at ~L285. **Warning:** moving any of these constants below the deferred import line in a future refactor will break the import chain.
- **`_has_rst_indented_block`**: Helper used only by `_check_prefer_fenced_code_blocks` and `_check_fenced_code_blocks_extra` — moves with them.
- **`_check_fenced_code_blocks_extra`**: Called directly from orchestrator (not via `_RULE_DISPATCH`). Must be re-imported into `__init__.py` for orchestrator access.
- **`_find_init_method` cross-consumed**: Used by `_check_missing_attributes` (moves) AND `_check_undocumented_init_params` at L2106 (stays). Must be re-imported.
- **Re-import list (14 symbols)**: Tests import helpers directly from `docvet.checks.enrichment`. The deferred import block must include: `_check_fenced_code_blocks_extra`, `_check_missing_attributes`, `_check_missing_cross_references`, `_check_missing_examples`, `_check_missing_typed_attributes`, `_check_prefer_fenced_code_blocks`, `_find_init_method`, `_has_self_assignments`, `_is_dataclass`, `_is_enum`, `_is_init_module`, `_is_namedtuple`, `_is_protocol`, `_is_typeddict`.
- **8 internal-only symbols** (no re-export needed): `_decorator_matches`, `_has_self_attribute_target`, `_has_rst_indented_block`, `_TYPED_ATTR_PATTERN`, `_SYMBOL_KIND_DISPLAY`, `_DOCTEST_PATTERN`, `_RST_BLOCK_PATTERN`, `_ENUM_NAMES`.
- **Single file, not two**: The ~850-line result exceeds the 500-line gate, but the two sub-concerns (attribute checks vs content checks) share `_SYMBOL_KIND_DISPLAY` and the class-type helpers. `_forward.py` at 662 lines sets precedent that the gate triggers evaluation, not a hard block. Defer further split unless the file grows.

## Implementation Plan

### Tasks

- [x] Task 1: Create `_class_module.py` with module docstring and imports
  - File: `src/docvet/checks/enrichment/_class_module.py` (new)
  - Action: Create file with `from __future__ import annotations`, stdlib imports (`ast`, `re`, `typing.Literal`), absolute imports (`Symbol`, `module_display_name`, `Finding`, `EnrichmentConfig`), relative imports (`_extract_section_content`, `_SEE_ALSO`, `_XREF_MD_LINK`, `_XREF_SPHINX`), sibling import (`_NodeT` from `._forward`). Add module docstring following `_forward.py` pattern.
  - Notes: `_forward.py` does NOT import `re` — don't blindly copy its import block. `_class_module.py` needs `import re` for `_TYPED_ATTR_PATTERN`, `_DOCTEST_PATTERN`, and `_RST_BLOCK_PATTERN`.

- [x] Task 2: Move extraction block (L310-L1132) into `_class_module.py`
  - File: `src/docvet/checks/enrichment/_class_module.py`
  - Action: Copy L310-L1132 from `__init__.py` verbatim. The cut starts at the `# Rule-specific helpers for missing-attributes` section divider (L310) and ends at the `return None` of `_check_fenced_code_blocks_extra` (L1132). Do NOT include the trailing blank line at L1133 — leave it as a separator before the `# Param agreement helpers` block. This includes:
    - Constants: `_ENUM_NAMES`, `_TYPED_ATTR_PATTERN`, `_SYMBOL_KIND_DISPLAY`, `_DOCTEST_PATTERN`, `_RST_BLOCK_PATTERN`
    - Helpers: `_decorator_matches`, `_is_dataclass`, `_is_protocol`, `_is_enum`, `_is_namedtuple`, `_is_typeddict`, `_find_init_method`, `_has_self_attribute_target`, `_has_self_assignments`, `_is_init_module`, `_has_rst_indented_block`
    - Check functions: `_check_missing_attributes`, `_check_missing_typed_attributes`, `_check_missing_examples`, `_check_missing_cross_references`, `_check_prefer_fenced_code_blocks`, `_check_fenced_code_blocks_extra`
  - Notes: Code moves verbatim — no logic changes, no reformatting.

- [x] Task 3: Remove extraction block from `__init__.py`
  - File: `src/docvet/checks/enrichment/__init__.py`
  - Action: Delete L310-L1132 (from the `# Rule-specific helpers for missing-attributes` section divider through the `return None` of `_check_fenced_code_blocks_extra`). Leave the blank line and `# Param agreement helpers` section divider intact.

- [x] Task 4: Add deferred import block in `__init__.py`
  - File: `src/docvet/checks/enrichment/__init__.py`
  - Action: After the existing `from ._forward import ...` block, add:
    ```python
    from ._class_module import (  # noqa: E402
        _check_fenced_code_blocks_extra,
        _check_missing_attributes,
        _check_missing_cross_references,
        _check_missing_examples,
        _check_missing_typed_attributes,
        _check_prefer_fenced_code_blocks,
        _find_init_method,
        _has_self_assignments,
        _is_dataclass,
        _is_enum,
        _is_init_module,
        _is_namedtuple,
        _is_protocol,
        _is_typeddict,
    )
    ```
  - Notes: 14 symbols. Alphabetical order. Must appear before `_RULE_DISPATCH` and `check_enrichment`.

- [x] Task 5: Verify tests and dogfood
  - Action: Run `uv run pytest` (all 1,660+ tests pass), `uv run ruff check .`, `uv run ty check`, `docvet check --all`. Verify zero test changes needed.

- [x] Task 6: Verify line counts
  - Action: Run `wc -l` on both files. Confirm `__init__.py` dropped to ~1,451 and `_class_module.py` is ~850.

### Acceptance Criteria

- [ ] AC 1: Given the extraction is complete, when `uv run pytest` is run, then all existing tests pass with zero modifications to test files.
- [ ] AC 2: Given `_class_module.py` exists, when its imports are inspected, then it uses absolute imports for external packages and relative imports for parent private helpers (extending `_forward.py` pattern with parent-relative imports for `_extract_section_content`, `_SEE_ALSO`, `_XREF_MD_LINK`, `_XREF_SPHINX`).
- [ ] AC 3: Given the deferred import block is in `__init__.py`, when `from docvet.checks.enrichment import _is_dataclass` is executed, then it resolves successfully (tests prove this).
- [ ] AC 4: Given the extraction is complete, when `docvet check --all` is run on the docvet codebase, then zero required findings are reported (dogfood passes).
- [ ] AC 5: Given the extraction is complete, when `wc -l` is run on `__init__.py`, then it is under 1,500 lines (target ~1,451: 2,259 - 823 removed + 16 deferred import block).
- [ ] AC 6: Given the extraction is complete, when `ruff check .` and `ty check` are run, then no new lint or type errors are introduced.
- [ ] AC 7: Given a consumer imports `check_enrichment` from `docvet.checks.enrichment`, when the enrichment check is invoked, then all rules (including missing-attributes, missing-examples, missing-cross-references, prefer-fenced-code-blocks) produce identical findings as before extraction.

## Additional Context

### Dependencies

- Depends on #367 (forward extraction) — already completed
- Closes #368

### Testing Strategy

- **Zero test changes**: All existing tests import from `docvet.checks.enrichment` — the `__init__.py` re-exports make the extraction transparent.
- **Test files**: `test_enrichment.py` (3,756 lines), `test_enrichment_sphinx.py` (448 lines), `test_prefer_fenced_code_blocks.py` (imports `_check_prefer_fenced_code_blocks` and `_check_fenced_code_blocks_extra`) — all must pass unchanged.
- **Canary test**: `test_undocumented_init_params.py` — depends on `_find_init_method` being available in `__init__.py` via re-import. If the re-import fails, this test breaks.
- **Dogfood**: `docvet check --all` runs all 4 checks on the docvet codebase itself.
- **CI gates**: ruff check, ruff format, ty check, pytest, docvet check --all, interrogate.

### Notes

- The issue #368 estimated ~454 lines; actual extraction is ~824 lines because line numbers shifted after #367 and the block is larger than originally scoped.
- Result: `__init__.py` drops from 2,259 → ~1,451 lines (36% reduction, accounting for 16-line deferred import block added).
- `_class_module.py` will be ~850 lines — exceeds 500-line gate but accepted per `_forward.py` precedent (662 lines). Defer further split unless it grows.
- High-risk item: the 14-symbol re-import list. If any symbol is missed, a test will fail with `ImportError` — easy to catch, easy to fix.
- Future consideration: after all enrichment extractions (#368-372), evaluate whether `_extract_section_content`, `_parse_sections`, and section constants should move to a shared `_sections.py` module.
