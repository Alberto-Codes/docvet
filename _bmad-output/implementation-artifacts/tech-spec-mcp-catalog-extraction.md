---
title: 'Extract MCP rule catalog to _catalog.py'
slug: 'mcp-catalog-extraction'
created: '2026-03-23'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+']
files_to_modify:
  - src/docvet/mcp.py (rename to mcp/__init__.py)
  - src/docvet/mcp/_catalog.py (new)
code_patterns:
  - 'mcp.py is a flat module at 938 lines — converting to mcp/ package'
  - '_RULE_CATALOG is pure data (list of TypedDict), _RULE_TO_CHECK is derived dict'
  - 'Same package conversion pattern proven in enrichment PR #377'
test_patterns:
  - 'Tests import from docvet.mcp — path unchanged after package conversion'
  - 'MCP catalog tests in tests/unit/test_mcp.py import _RULE_CATALOG directly'
---

# Tech-Spec: Extract MCP rule catalog to _catalog.py

**Created:** 2026-03-23

## Overview

### Problem Statement

`src/docvet/mcp.py` is 938 lines — 1.9x the project's 500-line module size gate. The rule catalog (`RuleCatalogEntry` TypedDict, `_RULE_CATALOG` list of 31 entries, `_RULE_TO_CHECK` derived dict, and `_DEFAULT_MCP_CHECKS` constant) accounts for 427 lines (45% of the file) and is pure data with no logic dependencies on the server code.

### Solution

Convert `mcp.py` into an `mcp/` package. Extract the catalog data into `mcp/_catalog.py`. The `__init__.py` re-exports `start_server` so the entry point `from docvet.mcp import start_server` works unchanged.

### Scope

**In Scope:**
- Rename `mcp.py` → `mcp/__init__.py`
- Create `mcp/_catalog.py` with `RuleCatalogEntry`, `_RULE_CATALOG`, `_RULE_TO_CHECK`, `_DEFAULT_MCP_CHECKS` (~427 lines)
- Re-export catalog symbols from `__init__.py` for test imports
- Verify all tests pass with zero import changes
- `Closes #375`

**Out of Scope:**
- Server logic changes
- Check runner extraction
- Behavioral changes

## Context for Development

### Codebase Patterns

- Same package conversion pattern proven in enrichment PR #377 — `git mv` module to `__init__.py`, extract concern, re-export
- `_RULE_CATALOG` is a `list[RuleCatalogEntry]` — pure data, no function calls, no imports from server code
- `_RULE_TO_CHECK` is derived: `{r["name"]: r["check"] for r in _RULE_CATALOG}` — moves with catalog
- `_DEFAULT_MCP_CHECKS` is a frozenset constant — no deps on server code
- `docvet mcp` CLI command calls `start_server()` from `docvet.mcp` — must work unchanged
- `pyproject.toml` entry point: `docvet = "docvet:main"` — unaffected (CLI imports mcp internally)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/mcp.py` L86-96 | `_DEFAULT_MCP_CHECKS` constant |
| `src/docvet/mcp.py` L97-116 | `RuleCatalogEntry` TypedDict |
| `src/docvet/mcp.py` L117-522 | `_RULE_CATALOG` list (31 entries) |
| `src/docvet/mcp.py` L523 | `_RULE_TO_CHECK` derived dict |
| `tests/unit/test_mcp.py` | Imports `_RULE_CATALOG` directly for staleness tests |

### Technical Decisions

- Catalog has ZERO deps on server code — cleanest possible seam (pure data)
- `_catalog.py` imports only `from __future__ import annotations` and `from typing import TypedDict` — no circular import risk
- `__init__.py` does `from ._catalog import` at top of file — catalog is needed before server setup
- **CORRECTION:** `_DEFAULT_MCP_CHECKS` stays in `__init__.py` — it depends on `_VALID_CHECK_NAMES` (from config) and `_GRIFFE_AVAILABLE` (runtime try/except). Not pure data. Only `RuleCatalogEntry`, `_RULE_CATALOG`, `_RULE_TO_CHECK` move
- Extraction is L97-523 (427 lines). Result: `__init__.py` ~511 lines, `_catalog.py` ~430 lines (with header)

## Implementation Plan

### Tasks

- [ ] Task 1: Create `mcp/` package directory
  - Action: `mkdir src/docvet/mcp/`

- [ ] Task 2: Rename `mcp.py` → `mcp/__init__.py`
  - Action: `git mv src/docvet/mcp.py src/docvet/mcp/__init__.py`
  - Notes: Verify with `uv run pytest tests/unit/test_mcp.py -q` after rename

- [ ] Task 3: Create `mcp/_catalog.py`
  - File: `src/docvet/mcp/_catalog.py`
  - Action: Create new file with:
    - `from __future__ import annotations` header
    - Module docstring
    - `from typing import TypedDict`
    - CUT from `__init__.py` L97-523:
      - `RuleCatalogEntry` TypedDict (L97-114)
      - `_RULE_CATALOG` list (L117-521)
      - `_RULE_TO_CHECK` dict (L523)

- [ ] Task 4: Add import from `_catalog` in `__init__.py`
  - File: `src/docvet/mcp/__init__.py`
  - Action: Replace the deleted catalog section with:
    ```python
    from ._catalog import RuleCatalogEntry, _RULE_CATALOG, _RULE_TO_CHECK
    ```
  - Notes: 3 symbols. All used by server code (`docvet_rules()`, `_build_summary()`, etc.)

- [ ] Task 5: Run full test suite + dogfood
  - Action: `uv run pytest -q` and `uv run docvet check --all`

### Acceptance Criteria

- [ ] AC 1: Given `from docvet.mcp import start_server`, when executed, then it resolves correctly
- [ ] AC 2: Given `from docvet.mcp import _RULE_CATALOG`, when executed, then it resolves via re-export
- [ ] AC 3: Given `uv run pytest -q`, when all tests execute, then all pass with zero test file modifications
- [ ] AC 4: Given `wc -l` on both files, then `_catalog.py` ~430 lines and `__init__.py` ~530 lines
- [ ] AC 5: Given `docvet check --all`, then zero findings

## Additional Context

### Dependencies

None — pure refactoring.

### Testing Strategy

- After Task 2: `uv run pytest tests/unit/test_mcp.py -q`
- After Task 4: `uv run pytest -q` full suite
- Dogfood: `uv run docvet check --all`

### Notes

- Commit type: `refactor(mcp)` — no behavioral changes
- Closes #375
- `__init__.py` at ~530 lines is just over 500 but only has 2 concerns (server + check runners) — acceptable for now
