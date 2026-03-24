---
title: 'Pre-release catalog and docs completeness fix'
slug: 'pre-release-catalog-docs-fix'
created: '2026-03-22'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+', 'MCP server (mcp lib)', 'mkdocs-material']
files_to_modify:
  - src/docvet/mcp.py
  - tests/unit/test_mcp.py
  - tests/integration/test_mcp.py
  - docs/site/checks/enrichment.md
  - README.md
code_patterns:
  - '_RULE_CATALOG entry dicts with keys: name, check, description, category, guidance, fix_example'
  - 'enrichment is in _FORMAT_FIXABLE_CHECKS — all enrichment entries MUST have non-null fix_example'
  - 'fix_example is a short code snippet string showing the corrected docstring pattern'
test_patterns:
  - 'TestRuleCatalogStaleness: count (L509), required keys (L511), name set (L523)'
  - 'TestRuleCatalogGuidance: fix_example non-null for enrichment (L756), guidance non-empty (L750)'
  - 'test_fix_example_structural_validity: validates fix_example is parseable (L784)'
---

# Tech-Spec: Pre-release catalog and docs completeness fix

**Created:** 2026-03-22

## Overview

### Problem Statement

Two Epic 35 enrichment rules (`missing-return-type` and `undocumented-init-params`) are missing from the MCP `_RULE_CATALOG` in `mcp.py`. The `docvet_check()` tool finds issues for these rules correctly (via `check_enrichment()` dispatch), but `docvet_rules()` cannot describe them — creating a usability gap for MCP/agent consumers. Additionally, the enrichment docs page is missing the `undocumented-init-params` rule row and the `require-init-params` config key row.

### Solution

Add the 2 missing catalog entries to `_RULE_CATALOG`, update all count references (docstring, tests), and add the missing row + config key to `docs/site/checks/enrichment.md`.

### Scope

**In Scope:**
- Add `missing-return-type` and `undocumented-init-params` entries to `_RULE_CATALOG`
- Update `mcp.py` module docstring rule count (29 → 31)
- Update `test_mcp.py` count assertion (29 → 31), comment (18 → 20), and expected rule name set
- Update `tests/integration/test_mcp.py` count assertion (29 → 31) and docstring
- Add `undocumented-init-params` row to enrichment.md rules table
- Add `require-init-params` row to enrichment.md config table
- Do NOT change enrichment.md header rule count — it says "20 rules" and the table will have 20 rows after adding 1 (self-corrects)
- Update README.md rule count (20 → 31)

**Out of Scope:**
- No new rules, no logic changes, no config changes
- No changes to enrichment.py, config.py, or CLI
- Round-trip test cases for `_isolated_config`/`_ENRICHMENT_ROUND_TRIP_CASES` — pre-existing gap across all 9 Epic 35 rules, not specific to this fix

## Context for Development

### Codebase Patterns

- `_RULE_CATALOG` is a `list[RuleCatalogEntry]` with entries having keys: `name`, `check`, `description`, `category`, `guidance`, `fix_example`
- Enrichment is in `_FORMAT_FIXABLE_CHECKS` — ALL enrichment entries MUST have a non-null `fix_example` string (enforced by `test_format_fixable_rules_have_fix_example` at L756). Only freshness/coverage rules use `fix_example: None`
- The catalog is the source of truth for `docvet_rules()` MCP tool output
- The enrichment.md rules table uses markdown table format with links to individual rule pages
- The enrichment.md config table documents all `[tool.docvet.enrichment]` keys

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/mcp.py` L469-486 | Last catalog entry (`trivial-docstring`) — pattern to follow |
| `src/docvet/mcp.py` L6 | Module docstring with rule count |
| `tests/unit/test_mcp.py` L507-561 | `TestRuleCatalogStaleness` — count, keys, names tests |
| `tests/integration/test_mcp.py` L231-245 | Integration test for `docvet_rules` — count and docstring |
| `README.md` L27 | Rule count in competitive positioning paragraph |
| `docs/site/checks/enrichment.md` L3 | Header with rule count (DO NOT CHANGE — self-corrects) |
| `docs/site/checks/enrichment.md` L11-31 | Rules table |
| `docs/site/checks/enrichment.md` L56-73 | Config table |
| `docs/site/rules/missing-return-type.md` | Existing rule page (description source) |
| `docs/site/rules/undocumented-init-params.md` | Existing rule page (description source) |

### Technical Decisions

- `missing-return-type`: category `recommended`, check `enrichment`, needs `fix_example` string showing a typed Returns entry (e.g., `"Returns:\n    int: The computed value."`)
- `undocumented-init-params`: category `required`, check `enrichment`, needs `fix_example` string showing an Args section in a class docstring (e.g., `"class Server:\n    \"\"\"A network server.\n\n    Args:\n        host: The hostname.\n    \"\"\""`)
- **CORRECTION from Step 1**: enrichment entries are NOT action rules — they are format-fixable and MUST have non-null `fix_example`. The `test_format_fixable_rules_have_fix_example` test (L756) enforces this
- Rule row placement in docs: `undocumented-init-params` goes after `missing-attributes` (line 22) — groups class-related required rules together thematically
- Config row placement: `require-init-params` goes after `require-return-type` (line 72) — groups opt-in boolean toggles together at the end of the config table

## Implementation Plan

### Tasks

- [x] Task 1: Update MCP module docstring rule count
  - File: `src/docvet/mcp.py`
  - Action: Line 6, change `"29 rules across 5 checks"` → `"31 rules across 5 checks"`

- [x] Task 2: Add `missing-return-type` catalog entry
  - File: `src/docvet/mcp.py`
  - Action: Insert new dict after `trivial-docstring` entry (after L485 closing `},`), before `]`
  - Content:
    - `name`: `"missing-return-type"`
    - `check`: `"enrichment"`
    - `description`: `"Returns section has no type and function has no return annotation."`
    - `category`: `"recommended"`
    - `guidance`: `"Add a type to the Returns entry (e.g., 'int: The count.') or add a -> return annotation to the function signature."`
    - `fix_example`: `"Returns:\n    int: The computed value."` (must pass 4-space indent structural test)

- [x] Task 3: Add `undocumented-init-params` catalog entry
  - File: `src/docvet/mcp.py`
  - Action: Insert new dict after `missing-return-type` entry, before `]`
  - Content:
    - `name`: `"undocumented-init-params"`
    - `check`: `"enrichment"`
    - `description`: `"Class __init__ takes parameters but neither class nor __init__ docstring has an Args section."`
    - `category`: `"required"`
    - `guidance`: `"Add an Args: section to either the class docstring or the __init__ docstring listing all constructor parameters with descriptions."`
    - `fix_example`: `"Args:\n    host (str): The server hostname.\n    port (int): The server port number."` (must pass 4-space indent structural test)

- [x] Task 4: Update test catalog count
  - File: `tests/unit/test_mcp.py`
  - Action: Line 509, change `== 29` → `== 31`

- [x] Task 5: Update test enrichment comment count
  - File: `tests/unit/test_mcp.py`
  - Action: Line 528, change `# enrichment (18)` → `# enrichment (20)`

- [x] Task 6: Add new rule names to test expected set
  - File: `tests/unit/test_mcp.py`
  - Action: After line 546 (`"trivial-docstring",`), insert `"missing-return-type",` and `"undocumented-init-params",`

- [x] Task 7: Update integration test rule count and docstring
  - File: `tests/integration/test_mcp.py`
  - Action: Line 231, change docstring `"all 29 rules"` → `"all 31 rules"`
  - Action: Line 245, change `assert len(rules) == 29` → `== 31`

- [x] Task 8: Update README rule count
  - File: `README.md`
  - Action: Line 27, change `"20 rules across 5 checks"` → `"31 rules across 5 checks"`

- [x] Task 9: Add `undocumented-init-params` to docs rules table
  - File: `docs/site/checks/enrichment.md`
  - Action: Insert new row after line 22 (`missing-attributes` row) — groups class-related required rules together
  - Content: `| [\`undocumented-init-params\`](../rules/undocumented-init-params.md) | required | classes | Class \`__init__\` takes parameters but neither class nor \`__init__\` docstring has an \`Args:\` section |`

- [x] Task 10: Add `require-init-params` to docs config table
  - File: `docs/site/checks/enrichment.md`
  - Action: Insert new row after line 72 (`require-return-type` row)
  - Content: `| \`require-init-params\` | \`bool\` | \`false\` | Require \`Args:\` section when \`__init__\` takes parameters (opt-in) |`

### Acceptance Criteria

- [x] AC 1: Given `_RULE_CATALOG` is inspected, when counting entries, then there are exactly 31 entries
- [x] AC 2: Given `_RULE_CATALOG` is inspected, when finding `missing-return-type` and `undocumented-init-params`, then both exist with keys `name`, `check`, `description`, `category`, `guidance`, `fix_example` — and `fix_example` is a non-null string with 4-space indented continuation lines
- [x] AC 3: Given `uv run pytest tests/unit/test_mcp.py tests/integration/test_mcp.py -v` is run, when all catalog tests execute, then all pass (unit: count=31, names match, keys valid, guidance non-empty, fix_example non-null and structurally valid; integration: count=31)
- [x] AC 4: Given the enrichment docs page is inspected, when counting rules table rows, then there are 20 data rows; when counting config table rows, then there are 17 data rows; when reading the header, then it says "20 rules" (unchanged — now matches table)
- [x] AC 5: Given `docvet check --all` is run on the codebase, when checks complete, then zero findings (dogfood passes)
- [x] AC 6: Given the README is inspected, when reading the competitive positioning paragraph (L27), then it says "31 rules across 5 checks"

## Additional Context

### Dependencies

None — no new packages, no config schema changes.

### Testing Strategy

- Run `uv run pytest tests/unit/test_mcp.py tests/integration/test_mcp.py -v` to verify all catalog tests pass (unit + integration)
- Run `uv run pytest` full suite to catch any regressions
- Run `docvet check --all` to confirm dogfood still passes

### Notes

- This is a pre-release fix for v1.14.0 (PR #350 pending)
- After this fix lands on main, release-please will update PR #350 automatically
- The functional check behavior is already correct — only metadata/catalog/docs are affected
- Do NOT manually touch the release PR — release-please updates it automatically on push to main
