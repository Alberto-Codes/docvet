---
title: 'Extract config formatting helpers to _formatting.py'
slug: 'config-formatting-extraction'
created: '2026-03-23'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+']
files_to_modify:
  - src/docvet/config.py (rename to config/__init__.py)
  - src/docvet/config/_formatting.py (new, ~268 lines)
code_patterns:
  - 'Proven package conversion pattern from enrichment #377 and mcp #378'
  - 'Formatting functions are pure — only read config, no mutation'
  - 'format_config_toml and format_config_json are public API used by cli.py config command'
test_patterns:
  - 'Tests import from docvet.config — path unchanged'
  - 'Config formatting tests in tests/unit/test_config.py'
---

# Tech-Spec: Extract config formatting helpers to _formatting.py

**Created:** 2026-03-23

## Overview

### Problem Statement

`src/docvet/config.py` is 1,182 lines — 2.4x the 500-line module size gate. The formatting concern (L837-1104, 268 lines) is pure functions that render config as TOML or JSON — no mutation, no parsing, no validation.

### Solution

Convert `config.py` → `config/` package. Extract 7 formatting functions into `config/_formatting.py`. Re-export `format_config_toml` and `format_config_json` from `__init__.py`.

### Scope

**In Scope:**
- Rename `config.py` → `config/__init__.py`
- Create `config/_formatting.py` with L837-1104 (268 lines): `_fmt_toml_value`, `_get_annotation`, `_get_section_user_keys`, `_format_toml_section`, `_convert_keys_to_kebab`, `format_config_toml`, `format_config_json`
- Re-export public symbols
- Closes #374

**Out of Scope:**
- Validation/parsing changes
- Dataclass changes
- Behavioral changes

## Context for Development

### Codebase Patterns

- Same pattern as enrichment #377 and mcp #378
- `format_config_toml` imports `DocvetConfig` — needs to import from parent package
- `_format_toml_section` takes a dataclass instance + field list — generic, no deps on specific config types
- `_convert_keys_to_kebab` is recursive dict walker — pure function
- `cli.py` calls `format_config_toml` and `format_config_json` via `from docvet.config import format_config_toml`

### Technical Decisions

- `_formatting.py` imports `DocvetConfig` from parent package: `from . import DocvetConfig`. No circular import — `DocvetConfig` is defined before `_formatting` is imported
- `get_user_keys` (L808-835) is a borderline case — it's used by `format_config_toml` but also by CLI. Keep in `__init__.py` and pass as parameter (already the pattern)
- Top-down import: `__init__.py` defines dataclasses + parsing first, then `from ._formatting import format_config_toml, format_config_json` at bottom

## Implementation Plan

### Tasks

- [ ] Task 1: Create `config/` package directory + rename
  - Action: `mkdir src/docvet/config && git mv src/docvet/config.py src/docvet/config/__init__.py`
  - Notes: Verify with `uv run pytest tests/unit/test_config.py -q`

- [ ] Task 2: Create `config/_formatting.py`
  - File: `src/docvet/config/_formatting.py`
  - Action: Create with header + CUT L837-1104 from `__init__.py`:
    - `_fmt_toml_value` (L837)
    - `_get_annotation` (L861)
    - `_get_section_user_keys` (L882)
    - `_format_toml_section` (L901)
    - `_convert_keys_to_kebab` (L929)
    - `format_config_toml` (L953)
    - `format_config_json` (L1058)
  - Imports needed: `from __future__ import annotations`, `import dataclasses`, `import json`, `from . import DocvetConfig`

- [ ] Task 3: Add import from `_formatting` in `__init__.py`
  - Action: Replace deleted section with:
    ```python
    from ._formatting import format_config_toml, format_config_json
    ```
  - Notes: Only 2 public symbols need re-export. Internal helpers stay private to `_formatting.py`

- [ ] Task 4: Run full test suite + dogfood
  - Action: `uv run pytest -q` and `uv run docvet check --all`

### Acceptance Criteria

- [ ] AC 1: `from docvet.config import format_config_toml, format_config_json` resolves correctly
- [ ] AC 2: `from docvet.config import load_config, DocvetConfig` resolves correctly
- [ ] AC 3: `uv run pytest -q` — all tests pass, zero test file modifications
- [ ] AC 4: `docvet config` command works unchanged
- [ ] AC 5: `__init__.py` ~914 lines, `_formatting.py` ~280 lines (with header)

## Additional Context

### Notes

- Commit type: `refactor(config)`
- Closes #374
- `__init__.py` at ~914 is still over 500 but only has 2 concerns left (dataclasses + parsing). A follow-up could extract validation helpers (~200 lines) but it's not tracked in the current issue set
