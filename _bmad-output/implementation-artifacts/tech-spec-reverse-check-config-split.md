---
title: 'Independent config toggles for reverse enrichment checks'
slug: 'reverse-check-config-split'
created: '2026-03-22'
status: 'done'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+']
files_to_modify:
  - src/docvet/config.py
  - src/docvet/checks/enrichment.py
  - tests/unit/checks/test_reverse_enrichment.py
  - tests/unit/test_config.py
  - docs/site/checks/enrichment.md
  - docs/site/rules/extra-raises-in-docstring.md
  - docs/site/rules/extra-yields-in-docstring.md
  - docs/site/rules/extra-returns-in-docstring.md
  - src/docvet/mcp.py
  - tests/unit/test_mcp.py
code_patterns:
  - 'EnrichmentConfig frozen dataclass with bool fields, field order matters for docstring'
  - '_RULE_DISPATCH tuple of (config_attr, check_fn) — L2787-2789 are the 3 reverse entries to reassign'
  - 'Config TOML keys hyphenated, Python attrs underscored — _kebab_to_snake() maps them'
  - '_VALID_ENRICHMENT_KEYS frozenset at L311 validates allowed keys'
  - '_parse_enrichment() at L554 auto-tracks user_set_keys for sphinx auto-disable'
  - '_SPHINX_AUTO_DISABLE_RULES at L2762 — must add check_extra_yields to mirror require_yields auto-disable in sphinx mode'
  - 'No extra-* findings on own codebase — default change wont break dogfood'
test_patterns:
  - 'Reverse enrichment tests call _check_extra_*() directly with EnrichmentConfig() — add config gating tests'
  - 'Config parsing tests in tests/unit/test_config.py — validate new keys parse correctly'
  - 'MCP catalog tests at tests/unit/test_mcp.py L507-561 — count stays 31 (no new rules, just config change)'
---

# Tech-Spec: Independent config toggles for reverse enrichment checks

**Created:** 2026-03-22

## Overview

### Problem Statement

The three reverse enrichment checks (`extra-raises-in-docstring`, `extra-yields-in-docstring`, `extra-returns-in-docstring`) share config keys with their forward counterparts (`require-raises`, `require-yields`, `require-returns`). Users cannot disable `extra-raises-in-docstring` (which has a high false-positive rate on propagated exceptions) without also disabling `missing-raises`. This punishes correct API documentation — documenting exceptions that propagate from callees is good practice but triggers false positives because the check only does intraprocedural analysis.

Real-world data: 75% false positive rate on `extra-raises-in-docstring` in a production codebase (3/4 findings were propagated exceptions). See issue #359.

### Solution

Add 3 new independent config keys (`check-extra-raises`, `check-extra-yields`, `check-extra-returns`) that decouple reverse checks from forward checks. Default `check-extra-raises` to `false` (opt-in) since propagated exceptions cause high false positives. Default the other two to `true` since they have near-zero false-positive surfaces (a function either yields/returns or it doesn't — no transitive propagation).

### Scope

**In Scope:**
- 3 new `EnrichmentConfig` fields: `check_extra_raises` (default `False`), `check_extra_yields` (default `True`), `check_extra_returns` (default `True`)
- Dispatch table split: 3 reverse check entries get their own config keys
- Config docs update (enrichment.md config table + note about defaults)
- Rule page update for `extra-raises-in-docstring` (note opt-in default)
- MCP catalog update (description notes opt-in for extra-raises)
- Tests for independent forward/reverse gating
- `Closes #359`

**Out of Scope:**
- Inline suppression comments (Epic 32, Story 32-4)
- Cross-function analysis for raises propagation
- Changes to forward check behavior
- Changes to check logic — only config gating changes

## Context for Development

### Codebase Patterns

- `EnrichmentConfig` is a frozen dataclass in `config.py` with boolean fields for each rule toggle
- `_RULE_DISPATCH` in `enrichment.py` is a tuple of `(config_attr_name, check_function)` pairs — the orchestrator iterates it and calls `getattr(config, attr)` to gate each check
- Config keys use hyphens in TOML (`check-extra-raises`), underscores in Python (`check_extra_raises`) — `_kebab_to_snake()` handles the mapping
- The `_VALID_ENRICHMENT_KEYS` frozenset in `config.py` validates config keys — new keys must be added here

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/config.py` L95-182 | `EnrichmentConfig` dataclass — add 3 new bool fields after L181 |
| `src/docvet/config.py` L311-330 | `_VALID_ENRICHMENT_KEYS` — add 3 new hyphenated keys |
| `src/docvet/config.py` L554-581 | `_parse_enrichment()` — no changes needed, auto-handles new keys via `_kebab_to_snake` |
| `src/docvet/checks/enrichment.py` L2762-2770 | `_SPHINX_AUTO_DISABLE_RULES` — add `check_extra_yields` (mirrors `require_yields` auto-disable) |
| `src/docvet/checks/enrichment.py` L2787-2789 | `_RULE_DISPATCH` — reassign 3 entries to new config attrs |
| `tests/unit/checks/test_reverse_enrichment.py` | Reverse check tests — add config gating tests for each reverse check |
| `tests/unit/test_config.py` | Config parsing tests — validate new keys parse correctly |
| `docs/site/checks/enrichment.md` L56-74 | Config table — add 3 new rows |
| `docs/site/rules/extra-raises-in-docstring.md` L44-51 | Configuration section — rewrite for `check-extra-raises` (opt-in) |
| `docs/site/rules/extra-yields-in-docstring.md` | Configuration section — add `check-extra-yields` reference |
| `docs/site/rules/extra-returns-in-docstring.md` | Configuration section — add `check-extra-returns` reference |
| `src/docvet/config.py` L996-1011 | `format_config_toml` enrichment field list — hardcoded, must add 3 new entries |
| `src/docvet/mcp.py` L429-439 | `extra-raises-in-docstring` catalog entry — update guidance to note opt-in |

### Technical Decisions

- `check-extra-raises` defaults to `false` — high FP rate on propagated exceptions; aligns with "never punish extra documentation" philosophy
- `check-extra-yields` and `check-extra-returns` default to `true` — near-zero FP; a function either yields/returns or it doesn't, no transitive propagation
- The `require-raises` key continues to gate only `missing-raises` (forward check) — no behavioral change for the forward direction
- Naming convention: `check-extra-*` prefix distinguishes reverse toggles from `require-*` forward toggles
- This is a behavioral change: `extra-raises-in-docstring` was previously on by default, now off. Conventional commit `feat` type triggers changelog entry via release-please
- Sphinx auto-disable: `_SPHINX_AUTO_DISABLE_RULES` contains `require_yields` (auto-disables forward yields in sphinx mode). To preserve behavior, `check_extra_yields` must also be added to this set — otherwise the reverse check would fire in sphinx mode while the forward check is auto-disabled. `require_raises` and `require_returns` are NOT in the set, so `check_extra_raises` and `check_extra_returns` don't need adding
- `_parse_enrichment()` handles new keys automatically — `_kebab_to_snake` maps them, `_validate_type` validates as bool, `user_set_keys` tracks them. No parser changes needed
- MCP catalog count stays at 31 — no new rules, just config knobs. `_RULE_CATALOG` entries unchanged except guidance text
- Dogfood: own codebase has zero `extra-*` findings, so the default change is safe
- `format_config_toml` uses a hardcoded field list (L996-1011), NOT dataclass introspection — new keys must be added. `format_config_json` uses `dataclasses.asdict()` — auto-includes new fields, no changes needed
- Pre-existing gap: 3 earlier fields (`check_trivial_docstrings`, `require_return_type`, `require_init_params`) are also missing from `format_config_toml` — out of scope for this spec

## Implementation Plan

### Tasks

- [ ] Task 1: Add 3 new fields to `EnrichmentConfig`
  - File: `src/docvet/config.py`
  - Action: After `require_init_params` (L181), add:
    - `check_extra_raises: bool = False`
    - `check_extra_yields: bool = True`
    - `check_extra_returns: bool = True`
  - Action: Update class docstring Attributes section with descriptions for all 3 fields
  - Notes: `check_extra_raises` defaults `False` (opt-in); others default `True`

- [ ] Task 2: Add 3 new keys to `_VALID_ENRICHMENT_KEYS`
  - File: `src/docvet/config.py`
  - Action: Add `"check-extra-raises"`, `"check-extra-yields"`, `"check-extra-returns"` to the frozenset at L311-330
  - Notes: Keys are hyphenated (TOML convention)

- [ ] Task 3: Add 3 new entries to `format_config_toml` field list
  - File: `src/docvet/config.py`
  - Action: Add `("check_extra_raises", "check-extra-raises")`, `("check_extra_yields", "check-extra-yields")`, `("check_extra_returns", "check-extra-returns")` to the enrichment field list at L996-1011
  - Notes: Insert after `require_deprecation_notice` or at end before `require_examples` — grouping reverse toggles together

- [ ] Task 4: Reassign 3 dispatch entries in `_RULE_DISPATCH`
  - File: `src/docvet/checks/enrichment.py`
  - Action: Change L2787-2789:
    - `("require_raises", _check_extra_raises_in_docstring)` → `("check_extra_raises", _check_extra_raises_in_docstring)`
    - `("require_yields", _check_extra_yields_in_docstring)` → `("check_extra_yields", _check_extra_yields_in_docstring)`
    - `("require_returns", _check_extra_returns_in_docstring)` → `("check_extra_returns", _check_extra_returns_in_docstring)`

- [ ] Task 5: Add `check_extra_yields` to `_SPHINX_AUTO_DISABLE_RULES`
  - File: `src/docvet/checks/enrichment.py`
  - Action: Add `"check_extra_yields"` to the `_SPHINX_AUTO_DISABLE_RULES` frozenset (L2762-2770)
  - Notes: Mirrors `require_yields` auto-disable. `check_extra_raises` and `check_extra_returns` NOT added — their forward counterparts aren't in the set either

- [ ] Task 6: Rewrite existing config-disable tests + add new gating tests
  - File: `tests/unit/checks/test_reverse_enrichment.py`
  - Action: Rewrite the 3 existing `test_config_disable_no_finding` tests (L311, L526, L665):
    - Change from `require_raises=False` / `require_yields=False` / `require_returns=False` to `check_extra_raises=False` / `check_extra_yields=False` / `check_extra_returns=False`
    - Replace `pass` fixture bodies with real bodies that would trigger the reverse check (e.g., a function with a Raises section but no raise statement and a real body, not a stub)
  - Action: Add 3 NEW test methods verifying forward/reverse independence:
    - `require_raises=True` + `check_extra_raises=False` → `missing-raises` fires, `extra-raises-in-docstring` does not
    - Same pattern for yields and returns
  - Notes: Test at orchestrator level (`check_enrichment()`) not individual `_check_*` functions to verify dispatch gating

- [ ] Task 7: Add config parsing tests for new keys
  - File: `tests/unit/test_config.py`
  - Action: Add tests verifying:
    - New keys parse from TOML correctly (`check-extra-raises = true` → `check_extra_raises=True`)
    - Default values are correct (`check_extra_raises=False`, others `True`)
    - Unknown key validation still works (typos rejected)

- [ ] Task 8: Update enrichment docs config table
  - File: `docs/site/checks/enrichment.md`
  - Action: Add 3 new rows to the config table (L56-74):
    - `| \`check-extra-raises\` | \`bool\` | \`false\` | Flag documented exceptions not raised in function body (opt-in due to propagated exception false positives) |`
    - `| \`check-extra-yields\` | \`bool\` | \`true\` | Flag \`Yields:\` section when function has no \`yield\` statement |`
    - `| \`check-extra-returns\` | \`bool\` | \`true\` | Flag \`Returns:\` section when function has no meaningful return |`
  - Notes: Insert after `require-deprecation-notice` row, grouped together

- [ ] Task 9: Update `extra-raises-in-docstring` rule page
  - File: `docs/site/rules/extra-raises-in-docstring.md`
  - Action: Rewrite Configuration section (L44-51):
    - Note this rule is **opt-in** (disabled by default) due to false positives on propagated exceptions
    - Show `check-extra-raises = true` to enable
    - Note that `require-raises` independently controls the forward check (`missing-raises`)

- [ ] Task 10: Update `extra-yields-in-docstring` rule page
  - File: `docs/site/rules/extra-yields-in-docstring.md`
  - Action: Update Configuration section to reference `check-extra-yields` instead of `require-yields`
  - Notes: Default is `true` — no behavioral change, just correct config reference

- [ ] Task 11: Update `extra-returns-in-docstring` rule page
  - File: `docs/site/rules/extra-returns-in-docstring.md`
  - Action: Update Configuration section to reference `check-extra-returns` instead of `require-returns`
  - Notes: Default is `true` — no behavioral change, just correct config reference

- [ ] Task 12: Update MCP catalog guidance for `extra-raises-in-docstring`
  - File: `src/docvet/mcp.py`
  - Action: Update `guidance` field for `extra-raises-in-docstring` (L435-437) to note:
    - Rule is opt-in (`check-extra-raises = true`)
    - If the exception propagates from a callee, the Raises entry may be correct — enable only for codebases with mostly direct raises

- [ ] Task 13: Run tests and dogfood
  - Action: `uv run pytest` full suite + `uv run docvet check --all`
  - Notes: Verify MCP catalog count stays at 31, all reverse check tests pass with new gating, dogfood clean

### Acceptance Criteria

- [ ] AC 1: Given default config (no `[tool.docvet.enrichment]`), when `check_enrichment()` runs on code with extra documented raises (documented but not raised in body), then `extra-raises-in-docstring` does NOT fire because `check_extra_raises` defaults to `False`
- [ ] AC 2: Given `check-extra-raises = true` in config, when `check_enrichment()` runs on code with extra documented raises, then `extra-raises-in-docstring` fires normally
- [ ] AC 3: Given `require-raises = true` and `check-extra-raises = false` (both defaults), when code raises an undocumented exception, then `missing-raises` fires but `extra-raises-in-docstring` does not — proving forward and reverse are independent
- [ ] AC 4: Given default config, when `check_enrichment()` runs on code with a `Yields:` section but no yield, then `extra-yields-in-docstring` fires (default on)
- [ ] AC 5: Given `check-extra-yields = false` in config, when `check_enrichment()` runs on the same code, then `extra-yields-in-docstring` does NOT fire
- [ ] AC 6: Given default config, when `check_enrichment()` runs on code with a `Returns:` section but no return, then `extra-returns-in-docstring` fires (default on)
- [ ] AC 7: Given `check-extra-returns = false` in config, when `check_enrichment()` runs on the same code, then `extra-returns-in-docstring` does NOT fire
- [ ] AC 8: Given `docvet config` is run, when output is inspected, then `check-extra-raises`, `check-extra-yields`, and `check-extra-returns` appear with correct defaults
- [ ] AC 9: Given `docvet check --all` is run on the docvet codebase, when checks complete, then zero findings (dogfood passes)

## Additional Context

### Dependencies

None — no new packages, no config schema changes beyond new fields.

### Testing Strategy

- Unit tests for config gating: verify each reverse check is independently togglable via `check_enrichment()` orchestrator
- Unit tests for config parsing: verify new TOML keys parse correctly with defaults
- Full test suite: `uv run pytest` to catch regressions
- Dogfood: `uv run docvet check --all` to confirm zero findings
- Manual: `uv run docvet config` to verify new keys appear in output

### Notes

- This is a behavioral change for `extra-raises-in-docstring` — previously on by default, now off. Users who relied on it to catch stale Raises entries should add `check-extra-raises = true` to their config
- Commit type: `feat(enrichment)` — triggers minor version bump via release-please
- Closes #359
- Future: Epic 32 Story 32-4 (inline suppression) will allow per-symbol control for users who want `extra-raises` on globally but need to suppress specific propagation cases
