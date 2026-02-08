# Story 1.1: Add `require_attributes` Config Toggle

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a `require-attributes` boolean toggle in `[tool.docvet.enrichment]`,
so that teams can enable or disable Attributes checking for classes independently.

## Acceptance Criteria

1. **Given** an `EnrichmentConfig` with no explicit `require-attributes` setting, **when** the config is loaded from `pyproject.toml`, **then** `require_attributes` defaults to `True` (AC: #1)

2. **Given** a `pyproject.toml` with `require-attributes = false` under `[tool.docvet.enrichment]`, **when** the config is loaded, **then** `require_attributes` is `False` (AC: #2)

3. **Given** an existing `pyproject.toml` without a `require-attributes` key, **when** the config is loaded, **then** all existing config fields retain their values and no error is raised (backward-compatible) (AC: #3)

4. **Given** the `_VALID_ENRICHMENT_KEYS` set in `config.py`, **when** inspected, **then** it includes `"require-attributes"` (AC: #4)

5. **Given** the `_parse_enrichment` function, **when** it receives an unknown key (e.g., `require-foo = true`), **then** it rejects the key at config load time with a clear error message (AC: #5)

## Tasks / Subtasks

- [x] Task 1: Add `require_attributes: bool = True` field to `EnrichmentConfig` dataclass (AC: #1, #3)
  - [x] 1.1: Add the field after `prefer_fenced_code_blocks` in `EnrichmentConfig`
- [x] Task 2: Add `"require-attributes"` to `_VALID_ENRICHMENT_KEYS` frozenset (AC: #4, #5)
  - [x] 2.1: Insert the key into the existing frozenset in alphabetical position relative to other `require-*` keys
- [x] Task 3: Write unit tests for the new config toggle (AC: #1, #2, #3, #4, #5)
  - [x] 3.1: `test_enrichment_defaults_require_attributes_is_true` — default value test
  - [x] 3.2: `test_load_config_nested_enrichment_require_attributes_false` — explicit `false` parsed correctly
  - [x] 3.3: `test_load_config_nested_enrichment_without_require_attributes_uses_default` — backward compatibility (omitted key keeps default)
  - [x] 3.4: Verify existing unknown-key test still passes (covers AC #5 via existing `test_load_config_unknown_enrichment_key_exits`)
- [x] Task 4: Run quality gates and verify all pass
  - [x] 4.1: `uv run ruff check .`
  - [x] 4.2: `uv run ruff format --check .`
  - [x] 4.3: `uv run ty check`
  - [x] 4.4: `uv run pytest --cov=docvet --cov-report=term-missing`

## Dev Notes

### Scope

This is **Prerequisite PR 1** of the enrichment module. It is intentionally minimal — a single new field on an existing frozen dataclass plus a key added to an existing validation set. No new files created.

### Files to Modify

| File | Change |
|------|--------|
| `src/docvet/config.py` | Add `require_attributes: bool = True` to `EnrichmentConfig`; add `"require-attributes"` to `_VALID_ENRICHMENT_KEYS` |
| `tests/unit/test_config.py` | Add 3 new tests for the toggle |

### Architecture Constraints

- `EnrichmentConfig` is a `@dataclass(frozen=True)` — new field must have a default value for backward compatibility (NFR19)
- `_VALID_ENRICHMENT_KEYS` is a `frozenset[str]` using kebab-case keys — the new key must be `"require-attributes"` (kebab-case)
- `_parse_enrichment()` already handles boolean validation for all non-`require-examples` keys via the `else` branch — no parser changes needed, the new key is automatically validated as `bool`
- The existing `_validate_keys()` call in `_parse_enrichment()` ensures unknown keys are rejected — AC #5 is covered by the existing validation mechanism once the key is added to the valid set

### Implementation Details

**`EnrichmentConfig` field placement:** Add `require_attributes: bool = True` as the last boolean field before the class closes. Current field order:
1. `require_examples` (list)
2. `require_raises` through `prefer_fenced_code_blocks` (9 booleans)
3. **NEW:** `require_attributes: bool = True`

**Why no `_parse_enrichment` changes:** The function iterates `data.items()` and for any key that isn't `"require-examples"`, it validates the value as `bool` then converts kebab-to-snake. Since `"require-attributes"` is a standard boolean toggle, the existing parsing logic handles it automatically after the key is added to `_VALID_ENRICHMENT_KEYS`.

**Test naming convention:** Follow existing pattern in `test_config.py`:
- `test_enrichment_defaults_require_attributes_is_true` (matches `test_enrichment_defaults_require_raises_is_true` pattern)
- `test_load_config_nested_enrichment_require_attributes_false` (matches `test_load_config_nested_enrichment_flipped_booleans` pattern)

### What NOT to Do

- Do NOT modify `_parse_enrichment()` logic — it already handles boolean keys generically
- Do NOT add a new section parser or validation function
- Do NOT modify `cli.py` or any other file — this is config-only
- Do NOT add `require_attributes` to `DocvetConfig` — it belongs in `EnrichmentConfig`
- Do NOT change the frozen dataclass to mutable

### Testing Strategy

- **Unit tests only** — no integration tests needed for a config field addition
- Use existing `write_pyproject` fixture pattern from `test_config.py`
- Existing tests must continue passing unchanged (backward compatibility proof)
- Existing `test_load_config_unknown_enrichment_key_exits` already covers unknown key rejection (AC #5)
- Existing `test_enrichment_when_mutated_raises_frozen_error` covers frozen enforcement

### FRs Covered

- FR26: Per-rule boolean config toggles (the `require-attributes` toggle)
- FR29: Disable all findings via config (contributes — all toggles must exist)
- FR30: Sensible defaults when no config provided (`require_attributes=True`)
- NFR19: Backward-compatible config addition

### Project Structure Notes

- No new files — modifications to 2 existing files only
- `src/docvet/config.py` is the single source of truth for all configuration
- `tests/unit/test_config.py` mirrors the config module

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Prerequisite PRs] — "Prereq PR 1: Add `require_attributes: bool = True` to `EnrichmentConfig`, update `_VALID_ENRICHMENT_KEYS`, update `_parse_enrichment` validation, update affected tests"
- [Source: _bmad-output/planning-artifacts/architecture.md#Config Schema Update] — "New toggle needed: `require-attributes: bool = True`"
- [Source: _bmad-output/planning-artifacts/prd.md#Config Schema Update] — "Updated EnrichmentConfig (10 booleans + 1 list)"
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1] — BDD acceptance criteria
- [Source: _bmad-output/project-context.md#Python Language Rules] — "Every file starts with `from __future__ import annotations`"
- [Source: _bmad-output/project-context.md#Testing Rules] — Test naming convention and self-contained test requirements
- [Source: src/docvet/config.py:24-38] — Current `EnrichmentConfig` definition
- [Source: src/docvet/config.py:79-91] — Current `_VALID_ENRICHMENT_KEYS` definition
- [Source: src/docvet/config.py:257-277] — Current `_parse_enrichment` function
- [Source: tests/unit/test_config.py] — Existing test patterns to follow

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No issues encountered. All tasks completed in a single pass.

### Completion Notes List

- Added `require_attributes: bool = True` as the last field in `EnrichmentConfig` dataclass (after `prefer_fenced_code_blocks`)
- Added `"require-attributes"` to `_VALID_ENRICHMENT_KEYS` frozenset in alphabetical position among `require-*` keys
- No changes needed to `_parse_enrichment()` — existing generic boolean parsing handles the new key automatically
- Added 3 new unit tests following existing naming conventions
- Verified existing `test_load_config_unknown_enrichment_key_exits` still passes (AC #5 coverage)
- All 190 tests pass, 98% coverage, all quality gates green

### Change Log

- 2026-02-08: Implemented story 1-1 — added `require_attributes` config toggle to `EnrichmentConfig` with 3 new unit tests
- 2026-02-08: Code review — fixed 2 issues: updated `test_load_config_full_config_populates_all_fields` to cover `require-attributes`, sorted `_VALID_ENRICHMENT_KEYS` alphabetically

### File List

- `src/docvet/config.py` (modified) — added `require_attributes: bool = True` field; added `"require-attributes"` valid key; sorted `_VALID_ENRICHMENT_KEYS` alphabetically
- `tests/unit/test_config.py` (modified) — added 3 new tests for default value, explicit false, and backward compatibility; updated full-config test to cover `require-attributes`

## Senior Developer Review (AI)

**Review Date:** 2026-02-08
**Reviewer:** Claude Opus 4.6 (code-review workflow)
**Outcome:** Approve (with fixes applied)

### Findings Summary

| # | Severity | Description | Resolution |
|---|----------|-------------|------------|
| 1 | MEDIUM | `test_load_config_full_config_populates_all_fields` did not exercise `require-attributes` | Fixed — added TOML key and assertion |
| 2 | MEDIUM | Excessive/disordered git commits (5 commits for trivial change) | Deferred — user will squash on merge |
| 3 | LOW | No explicit `require-attributes = true` TOML test | Accepted — default path covers this |
| 4 | LOW | Field placed after `prefer_fenced_code_blocks` breaks `require_*` grouping | Accepted — matches Dev Notes spec |
| 5 | LOW | `_VALID_ENRICHMENT_KEYS` not alphabetically sorted | Fixed — sorted all keys alphabetically |

### AC Verification

All 5 Acceptance Criteria verified as IMPLEMENTED with runtime confirmation and passing tests.
