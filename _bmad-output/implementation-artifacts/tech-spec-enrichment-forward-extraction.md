---
title: 'Extract forward checks into enrichment sub-package'
slug: 'enrichment-forward-extraction'
created: '2026-03-22'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+']
files_to_modify:
  - src/docvet/checks/enrichment.py (rename to enrichment/__init__.py)
  - src/docvet/checks/enrichment/_forward.py (new, ~658 lines)
code_patterns:
  - 'enrichment.py is a flat module at 2,870 lines — converting to enrichment/ package'
  - '_RULE_DISPATCH references check functions by name — imports must be updated after extraction'
  - 'Python treats package __init__.py same as module for imports — zero external caller changes'
  - 'Forward checks (L261-918) have ZERO deps on section parsers (L66-260) — cleanest seam'
  - '_should_skip_reverse_check (L540) stays in __init__.py — only used by reverse checks'
  - '_NodeT and _build_node_index move to _forward.py — also re-exported from __init__.py for other modules'
  - 'Top-down import pattern: __init__.py defines shared symbols first, imports from _forward at bottom'
test_patterns:
  - 'Tests import from docvet.checks.enrichment — path unchanged after package conversion'
  - 'Tests that import _check_missing_raises etc directly still work via __init__.py re-export'
  - '1,615+ tests must pass with no import changes'
  - 'conftest.py in tests/unit/checks/ resets _active_style — unaffected by this change'
---

# Tech-Spec: Extract forward checks into enrichment sub-package

**Created:** 2026-03-22

## Overview

### Problem Statement

`src/docvet/checks/enrichment.py` is 2,870 lines — 5.7x the project's 500-line module size gate. The forward missing-* checks (raises, returns, yields, receives, warns, other-parameters) plus their shared helpers span L261-918 (~658 lines, 23% of the file) and have zero dependencies on section parsers — the cleanest extraction seam.

### Solution

Convert `enrichment.py` into an `enrichment/` package. Extract the 6 forward check functions and their helpers into `enrichment/_forward.py`. The `__init__.py` re-exports `check_enrichment` so all external imports (`from docvet.checks.enrichment import check_enrichment`) work unchanged.

### Scope

**In Scope:**
- Rename `enrichment.py` → `enrichment/__init__.py`
- Create `enrichment/_forward.py` with 6 forward check functions + 9 helpers (L261-918, ~658 lines)
- Update `_RULE_DISPATCH` entries to reference imported functions from `_forward`
- Verify all tests pass with zero import changes

**Out of Scope:**
- Extracting other concerns (class/module, params, deprecation, reverse, late rules — #368-#372)
- Eliminating `_active_style` global (separate concern)
- Test file splits
- Any behavioral changes

## Context for Development

### Codebase Patterns

- `enrichment.py` is currently a flat module under `src/docvet/checks/`
- `_RULE_DISPATCH` is a tuple of `(config_attr, check_fn)` pairs referencing functions by name
- Forward checks share helpers: `_is_stub_function`, `_is_property`, `_has_decorator`, `_should_skip_returns_check`, `_is_meaningful_return`, `_extract_exception_name`, `_build_node_index`, `_NodeT`, `_is_warn_call`
- `check_enrichment` orchestrator iterates `_RULE_DISPATCH` and calls each function
- External callers: `cli.py` and `checks/__init__.py` import directly from `docvet.checks.enrichment`; `lsp.py` and `mcp.py` import via `docvet.checks`; tests import from `docvet.checks.enrichment`

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/checks/enrichment.py` L261-918 | Forward check functions + helpers to extract (~658 lines) |
| `src/docvet/checks/enrichment.py` L261-262 | `_NodeT` type alias — moves to `_forward.py`, re-exported from `__init__.py` |
| `src/docvet/checks/enrichment.py` L264-284 | `_build_node_index` — moves to `_forward.py`, re-exported from `__init__.py` |
| `src/docvet/checks/enrichment.py` L292-322 | `_extract_exception_name` — moves (used by `_check_missing_raises` + reverse checks import it) |
| `src/docvet/checks/enrichment.py` L540-560 | `_should_skip_reverse_check` — STAYS in `__init__.py` (only used by reverse checks) |
| `src/docvet/checks/enrichment.py` L2774-2795 | `_RULE_DISPATCH` — stays, references imported check functions |
| `src/docvet/checks/__init__.py` | Package init — unchanged |

### Technical Decisions

- Package conversion is invisible to callers — Python resolves `from docvet.checks.enrichment import X` identically for module vs package
- **Extraction boundary L261-918** chosen because forward checks have ZERO deps on section parsers (L66-260). They only need `ast`, `Finding`, `EnrichmentConfig`, `Symbol` — all external imports. Cleanest possible seam
- `_NodeT` and `_build_node_index` move to `_forward.py` but must be re-exported from `__init__.py` because class/module checks (L926+) and the orchestrator also use them
- `_extract_exception_name` moves to `_forward.py` but must be re-exported — reverse checks (`_check_extra_raises_in_docstring`) also call it
- `_should_skip_reverse_check` (L540) stays in `__init__.py` despite being defined in the forward range — it's only called by reverse checks (L2274, L2338, L2393)
- `_is_warn_call` (L772) moves to `_forward.py` but must be re-exported — deprecation check (`_is_deprecation_warn_call` L2089) also calls it
- Import pattern (top-down, no circular imports): `_forward.py` only imports from external modules (`ast`, `docvet.checks._finding`, `docvet.config`, `docvet.ast_utils`). `__init__.py` does `from ._forward import` at the bottom after its own symbols are defined. **No circular imports** — `_forward.py` does NOT import from its parent package

## Implementation Plan

### Tasks

- [ ] Task 1: Create `enrichment/` package directory
  - Action: `mkdir src/docvet/checks/enrichment/`
  - Notes: This is infrastructure for the rename in Task 2

- [ ] Task 2: Rename `enrichment.py` → `enrichment/__init__.py`
  - Action: `git mv src/docvet/checks/enrichment.py src/docvet/checks/enrichment/__init__.py`
  - Notes: Use `git mv` to preserve history. After this step, all imports work unchanged — verify with `uv run pytest tests/unit/checks/test_enrichment.py -q`

- [ ] Task 3: Create `enrichment/_forward.py` with forward check functions
  - File: `src/docvet/checks/enrichment/_forward.py`
  - Action: Create new file with:
    - `from __future__ import annotations` header
    - Module docstring describing the forward checks
    - Imports: `ast`, `from docvet.checks._finding import Finding`, `from docvet.config import EnrichmentConfig`, `from docvet.ast_utils import Symbol`
    - CUT these functions/symbols from `__init__.py` L261-918 (in order):
      - `_NodeT` type alias (L261-262)
      - `_build_node_index` (L264-284)
      - `_extract_exception_name` (L292-322)
      - `_check_missing_raises` (L325-390)
      - `_is_meaningful_return` (L393-410)
      - `_is_property` (L413-434)
      - `_has_decorator` (L437-455)
      - `_is_stub_function` (L458-496)
      - `_should_skip_returns_check` (L499-537)
      - `_check_missing_returns` (L563-629)
      - `_check_missing_yields` (L632-692)
      - `_check_missing_receives` (L695-769)
      - `_is_warn_call` (L772-794)
      - `_check_missing_warns` (L797-861)
      - `_check_missing_other_parameters` (L864-918)
    - Do NOT move `_should_skip_reverse_check` (L540-560) — it stays in `__init__.py`
  - Notes: ~658 lines. All functions are self-contained — no deps on section parsers

- [ ] Task 4: Add import from `_forward` in `__init__.py`
  - File: `src/docvet/checks/enrichment/__init__.py`
  - Action: At the bottom of the file (after all remaining definitions, before `_RULE_DISPATCH`), add:
    ```python
    from ._forward import (
        _NodeT,
        _build_node_index,
        _check_missing_other_parameters,
        _check_missing_raises,
        _check_missing_receives,
        _check_missing_returns,
        _check_missing_warns,
        _check_missing_yields,
        _extract_exception_name,
        _has_decorator,
        _is_meaningful_return,
        _is_property,
        _is_stub_function,
        _is_warn_call,
    )
    ```
  - Notes: 14 symbols — 6 check functions for `_RULE_DISPATCH` + 8 helpers used by remaining code in `__init__.py` and tests. `_has_decorator` (used by `_should_skip_reverse_check` L556, `_has_deprecated_decorator` L2115), `_is_stub_function` (used by `_should_skip_reverse_check` L558, also directly imported by `test_missing_returns.py`), `_is_property` (used by `_check_missing_return_type` L2543, `_check_undocumented_init_params` L2653), `_is_meaningful_return` (used by `_check_extra_returns_in_docstring` L2402)

- [ ] Task 5: Verify `__init__.py` line count
  - Action: Run `wc -l src/docvet/checks/enrichment/__init__.py`
  - Notes: Should be ~2,212 lines (2,870 - 658). Still over 500 but reduced by 23% — subsequent PRs (#368-#372) continue the extraction

- [ ] Task 6: Run full test suite + dogfood
  - Action: `uv run pytest -q` and `uv run docvet check --all`
  - Notes: All 1,615+ tests must pass. Zero import changes in any test file. Dogfood must be clean

### Acceptance Criteria

- [ ] AC 1: Given `src/docvet/checks/enrichment/` exists as a package, when `from docvet.checks.enrichment import check_enrichment` is executed, then it resolves correctly (package behaves like module)
- [ ] AC 2: Given `_forward.py` exists, when inspected, then it contains exactly the 6 forward check functions + 9 helper functions/types listed in Task 3
- [ ] AC 3: Given `__init__.py` imports from `_forward`, when `_RULE_DISPATCH` references `_check_missing_raises` etc., then all 6 forward check function names resolve correctly
- [ ] AC 4: Given `_extract_exception_name`, `_is_warn_call`, `_has_decorator`, `_is_stub_function`, `_is_property`, and `_is_meaningful_return` are in `_forward.py`, when remaining code in `__init__.py` and tests reference them, then they resolve via the re-export in `__init__.py`
- [ ] AC 5: Given `_should_skip_reverse_check` stays in `__init__.py`, when reverse checks (L2274, L2338, L2393) reference it, then it resolves correctly
- [ ] AC 6: Given `uv run pytest -q` is run, when all tests execute, then all 1,615+ pass with zero test file modifications
- [ ] AC 7: Given `uv run docvet check --all` is run, when checks complete, then zero required findings (dogfood passes)
- [ ] AC 8: Given `wc -l` is run on both files, when line counts are checked, then `_forward.py` is ~658 lines and `__init__.py` is ~2,230 lines (2,870 - 658 + ~18 lines for import block)

## Additional Context

### Dependencies

None — pure refactoring, no new packages, no behavioral changes.

### Testing Strategy

- After Task 2 (rename only): run `uv run pytest tests/unit/checks/test_enrichment.py -q` to verify package conversion works
- After Task 4 (extraction complete): run full suite `uv run pytest -q`
- Dogfood: `uv run docvet check --all`
- Verify no test imports changed: `grep -r "from docvet.checks.enrichment import" tests/` should show identical paths

### Notes

- This is the first PR in a 6-PR series (#367-#372) to get `enrichment` under 500 lines
- Commit type: `refactor(enrichment)` — no behavioral changes, no version bump
- `_forward.py` at 658 lines is over 500 but contains a single concern (forward missing-section checks) — acceptable per project rules
- Subsequent PRs will extract class/module checks, param agreement, deprecation, reverse checks, and late rules
- Closes #367
