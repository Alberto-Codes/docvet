# Story 21.2: Config Warning Cleanup

Status: done
Branch: `feat/config-21-2-config-warning-cleanup`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer who set `fail-on` in their config**,
I want docvet to silently resolve the overlap with default `warn-on` values,
So that I don't see confusing warnings about a conflict I didn't create.

## Acceptance Criteria

1. **Given** `pyproject.toml` with `fail-on = ["enrichment", "freshness", "coverage", "griffe"]` and no `warn-on` key **When** docvet loads the configuration **Then** the overlap between `fail-on` and default `warn-on` is resolved silently — zero warnings on stderr **And** the resolved `warn-on` list is empty (all four checks promoted to fail-on)

2. **Given** `pyproject.toml` with `fail-on = ["enrichment"]` and no `warn-on` key **When** docvet loads the configuration **Then** zero warnings on stderr **And** the resolved `warn-on` list is `["freshness", "griffe", "coverage"]` (defaults minus overlap)

3. **Given** `pyproject.toml` with both `fail-on = ["enrichment"]` and `warn-on = ["enrichment", "freshness"]` (explicit overlap) **When** docvet loads the configuration **Then** a warning is emitted: `docvet: 'enrichment' appears in both fail-on and warn-on; using fail-on` **And** only the overlapping check produces a warning (one warning, not four)

4. **Given** `pyproject.toml` with neither `fail-on` nor `warn-on` set **When** docvet loads the configuration **Then** zero warnings on stderr (defaults don't conflict with themselves)

5. **Given** the detection mechanism for "user explicitly set" vs "default value" **When** inspecting the implementation **Then** detection is based on key presence in the parsed TOML `[tool.docvet]` section (checking if `"warn-on"` or `"warn_on"` key exists), not on value comparison

6. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all tests pass (config test assertions updated for new warning behavior)

## Tasks / Subtasks

- [x] Task 1: Add explicit-vs-default detection for `warn_on` in `load_config` (AC: 5)
  - [x] 1.1: After `_parse_docvet_section()` returns `parsed`, check if `"warn_on"` key is present in the parsed dict (note: `_parse_docvet_section` converts `warn-on` to `warn_on` via `_kebab_to_snake`)
  - [x] 1.2: Store result as `warn_on_explicit: bool = "warn_on" in parsed`
  - [x] 1.3: Unit test: verify `warn_on_explicit` is `True` when TOML has `warn-on` key
  - [x] 1.4: Unit test: verify `warn_on_explicit` is `False` when TOML has no `warn-on` key
- [x] Task 2: Gate overlap warnings on `warn_on_explicit` (AC: 1, 2, 3, 4)
  - [x] 2.1: Wrap the existing warning loop (`for check in warn_on: if check in fail_on_set:`) in `if warn_on_explicit:`
  - [x] 2.2: When `warn_on_explicit` is `False`, skip the warning loop entirely — overlap is silently resolved
  - [x] 2.3: The overlap resolution logic (subtracting `fail_on_set` from `warn_on` at line ~590) remains unchanged — it always runs regardless of `warn_on_explicit`
- [x] Task 3: Update existing config tests for new warning behavior (AC: 6)
  - [x] 3.1: Update `test_load_config_overlap_default_warn_on_emits_warning` — rename to `test_load_config_overlap_default_warn_on_no_warning` and assert zero stderr output
  - [x] 3.2: Verify `test_load_config_overlap_emits_stderr_warning` passes unchanged — fixture already has explicit `warn-on = ["freshness", "enrichment"]` (line 593), so `warn_on_explicit = True` and warning still fires
  - [x] 3.3: Verify `test_load_config_overlap_multiple_checks_emits_warning_for_each` passes unchanged — fixture already has explicit `warn-on = ["freshness", "coverage", "enrichment"]` (line 624), so `warn_on_explicit = True`
  - [x] 3.4: Verify `test_load_config_no_overlap_emits_no_warning` still passes unchanged
  - [x] 3.5: Verify `test_load_config_overlap_auto_subtracts_from_warn_on` still passes (tests deduplication, not warnings)
- [x] Task 4: Add new tests for explicit-vs-default scenarios (AC: 1, 2, 3, 4)
  - [x] 4.1: Test: `fail-on` set with all four checks, no `warn-on` → zero warnings, empty `warn_on` in result
  - [x] 4.2: Test: `fail-on = ["enrichment"]`, no `warn-on` → zero warnings, `warn_on = ["freshness", "griffe", "coverage"]`
  - [x] 4.3: Test: both `fail-on` and `warn-on` explicitly set with overlap → warning emitted for overlapping checks only
  - [x] 4.4: Test: neither `fail-on` nor `warn-on` set → zero warnings, defaults intact. Check existing tests first — many use empty `[tool.docvet]` sections; avoid creating a duplicate. If an existing test already covers this scenario (zero config, no stderr), add a targeted `assert "appears in both" not in err` to it instead of a new test function
  - [x] 4.5: Test: `warn-on` explicitly set, no `fail-on` → zero warnings. Note: the reason is that default `fail_on` is `[]` (empty list), so `fail_on_set` is empty and the inner `if check in fail_on_set` never fires — the `warn_on_explicit` gate is irrelevant here. The test verifies the edge case but the mechanism is the empty fail-on set, not the explicit gate
- [x] Task 5: Run quality gates (AC: 6)
  - [x] 5.1: `uv run ruff check .` — zero violations
  - [x] 5.2: `uv run ruff format --check .` — zero format issues
  - [x] 5.3: `uv run ty check` — zero type errors
  - [x] 5.4: `uv run pytest` — all tests pass
  - [x] 5.5: `uv run docvet check --all` — zero findings
  - [x] 5.6: `uv run interrogate -v` — ≥ 95% coverage

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_load_config_fail_on_all_four_no_warn_on_zero_warnings` | PASS |
| AC2 | `test_load_config_fail_on_partial_no_warn_on_zero_warnings` | PASS |
| AC3 | `test_load_config_both_explicit_overlap_warns_for_overlapping_only` | PASS |
| AC4 | `test_load_config_neither_exclude_uses_defaults` (augmented with capsys) | PASS |
| AC5 | `test_load_config_overlap_default_warn_on_no_warning` (warn_on_explicit=False), `test_load_config_overlap_emits_stderr_warning` (warn_on_explicit=True) | PASS |
| AC6 | 845 tests pass (`uv run pytest`) | PASS |

## Dev Notes

- **Single file to modify**: `src/docvet/config.py` — the overlap warning logic in `load_config()` (lines 564-569)
- **Single test file to modify**: `tests/unit/test_config.py` — existing overlap tests (lines 541-649)
- **Minimal change surface**: This is a ~3-line change in production code (add `warn_on_explicit` bool, wrap warning loop in `if`), plus test updates
- **The overlap resolution logic is separate from the warning**: Lines ~590 in `load_config()` subtract `fail_on_set` from `warn_on` to build the final config — this must continue to run unconditionally regardless of `warn_on_explicit`. Only the **warning print** is gated.

### How the Current Code Works

The overlap warning is at `config.py:564-569`:

```python
fail_on_set = set(fail_on)
for check in warn_on:
    if check in fail_on_set:
        print(
            f"docvet: '{check}' appears in both fail-on and warn-on; using fail-on",
            file=sys.stderr,
        )
```

The problem: when `warn-on` is not in the TOML, `warn_on` defaults to all four checks. If the user sets `fail-on = ["enrichment", "freshness", "coverage", "griffe"]`, all four overlap with the defaults, producing 4 warnings for a conflict the user didn't create.

### The Fix

```python
warn_on_explicit = "warn_on" in parsed
fail_on_set = set(fail_on)
if warn_on_explicit:
    for check in warn_on:
        if check in fail_on_set:
            print(
                f"docvet: '{check}' appears in both fail-on and warn-on; using fail-on",
                file=sys.stderr,
            )
```

**Why `"warn_on" in parsed`**: The `_parse_docvet_section()` function (line 432) converts all kebab-case keys to snake_case via `_kebab_to_snake()`. So `warn-on` in TOML becomes `warn_on` in the parsed dict. If the key is absent from TOML, it won't be in `parsed` — `parsed.get("warn_on")` returns `None` and the default is used instead (line 557-561). Checking `"warn_on" in parsed` directly tests key presence, not value comparison (FR-UX7).

### Data Flow (annotated)

```
load_config():
  1. parsed = _parse_docvet_section(raw_toml)  # snake_case keys
  2. warn_on_explicit = "warn_on" in parsed     # ← NEW: key presence check
  3. raw_fail = parsed.get("fail_on")           # None if not in config
  4. fail_on = [str(x) for x in raw_fail] if isinstance(raw_fail, list) else defaults.fail_on
  5. raw_warn = parsed.get("warn_on")           # None if not in config
  6. warn_on = [str(x) for x in raw_warn] if isinstance(raw_warn, list) else defaults.warn_on
  7. fail_on_set = set(fail_on)
  8. if warn_on_explicit:                        # ← NEW: gate on explicit
  9.     for check in warn_on:
  10.        if check in fail_on_set: print(warning)
  11. # ... build DocvetConfig ...
  12. warn_on = [c for c in warn_on if c not in fail_on_set]  # Always deduplicates
```

### Existing Test Map (lines to update)

| Test | Lines | Current Behavior | New Behavior |
|------|-------|------------------|--------------|
| `test_load_config_overlap_auto_subtracts_from_warn_on` | 541-548 | Verifies deduplication | **Unchanged** — tests config result, not warnings |
| `test_load_config_overlap_emits_stderr_warning` | 588-602 | Expects warning on overlap | **Unchanged** — fixture already has explicit `warn-on` (line 593) |
| `test_load_config_no_overlap_emits_no_warning` | 605-614 | No overlap → no warning | **Unchanged** |
| `test_load_config_overlap_multiple_checks_emits_warning_for_each` | 617-636 | 2 overlapping → 2 warnings | **Unchanged** — fixture already has explicit `warn-on` (line 624) |
| `test_load_config_overlap_default_warn_on_emits_warning` | 639-649 | Default warn-on + fail-on → warning | **Invert**: rename, assert zero warnings |

### Known Limitation

`warn_on_explicit` checks key presence in the *parsed TOML dict*, not "user explicitly chose a value" in a general sense. Today these are identical — `load_config(path)` has no config-override parameters and the CLI passes no `warn_on` override. But if a future story adds a `--warn-on` CLI flag that injects values into the config without going through TOML, `"warn_on" in parsed` would return `False` and warnings would be suppressed even for an explicit CLI choice. This is acceptable: no `--warn-on` flag exists or is planned (Story 21.3 only adds `--verbose` and `--quiet`), and any future CLI override would require refactoring `load_config` anyway, at which point the developer would see `warn_on_explicit` and handle it.

### Previous Story Intelligence (21-1)

- Story 21-1 added `format_summary()` to `reporting.py` and replaced `Completed in Xs` with the `Vetted` summary line in `cli.py`
- Tests were updated: `TOTAL_LINE_RE` → `SUMMARY_LINE_RE`, `_non_timing_lines` filter updated
- 841 tests currently passing
- Code review found that AC4 (zero-files case) behavior was better than originally specified — verify assumptions against actual code
- Pattern: keep changes minimal, test thoroughly, update existing tests rather than creating parallel ones

### Project Structure Notes

- All changes in `src/docvet/config.py` and `tests/unit/test_config.py` — no new files
- No cross-module impact — the warning is entirely contained in `load_config()`
- The `DocvetConfig` dataclass is frozen and unchanged by this story
- No import changes needed

### References

- [Source: _bmad-output/planning-artifacts/epics-cli-ux.md — Story 21.2 section, FR-UX5 through FR-UX7]
- [Source: src/docvet/config.py — lines 551-570 (overlap warning logic), lines 394-449 (_parse_docvet_section)]
- [Source: tests/unit/test_config.py — lines 541-649 (overlap warning tests)]
- [Source: _bmad-output/implementation-artifacts/21-1-default-output-overhaul.md — previous story learnings]

### Documentation Impact

- Pages: `docs/site/configuration.md`, `docs/site/ci-integration.md`
- Nature of update: Updated overlap warning documentation to reflect silent resolution of default overlaps. Changed admonition type from "warning" to "tip" in both pages.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 845 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging required.

### Completion Notes List

- Added `warn_on_explicit = "warn_on" in parsed` to detect explicit vs default `warn-on` key presence
- Wrapped the overlap warning loop in `if warn_on_explicit:` — only warns when user explicitly set both keys
- Overlap resolution (subtracting `fail_on_set` from `warn_on`) continues to run unconditionally
- Renamed `test_load_config_overlap_default_warn_on_emits_warning` → `test_load_config_overlap_default_warn_on_no_warning` (inverted assertion)
- All 4 existing overlap tests verified passing unchanged (explicit `warn-on` fixtures)
- Added 4 new tests: all-four fail-on, partial fail-on, both explicit with overlap, explicit warn-on only
- Augmented `test_load_config_neither_exclude_uses_defaults` with capsys assertion (subtask 4.4)
- Updated `load_config` docstring to document overlap warning behavior
- 845 tests (841 → 845), all green

### Change Log

- 2026-02-26: Implemented config warning cleanup — overlap warnings gated on explicit `warn-on` key presence
- 2026-02-26: Code review fixes — updated 2 doc pages for documentation drift, added `fail_on` assertion to AC3 test

### File List

- `src/docvet/config.py` — modified (added `warn_on_explicit` detection and warning gate)
- `tests/unit/test_config.py` — modified (renamed 1 test, added 4 new tests, augmented 1 existing test, added `fail_on` assertion to AC3 test)
- `docs/site/configuration.md` — modified (updated overlap warning docs for silent default resolution)
- `docs/site/ci-integration.md` — modified (updated overlap warning admonition for silent default resolution)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — modified (story status)
- `_bmad-output/implementation-artifacts/21-2-config-warning-cleanup.md` — modified (story file)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Changes Requested → Fixed

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Documentation drift — `docs/site/configuration.md:30-33` and `docs/site/ci-integration.md:129-130` describe old warning behavior where default overlaps print stderr warnings | Fixed — updated both pages to describe silent default resolution; changed admonition type from "warning" to "tip" |
| M1 | MEDIUM | Near-duplicate test fixtures between `test_load_config_overlap_auto_subtracts_from_warn_on` (line 541) and `test_load_config_overlap_default_warn_on_no_warning` (line 639) | Dismissed — separate concerns (config result vs warning behavior); single-responsibility testing pattern |
| L1 | LOW | AC3 test `test_load_config_both_explicit_overlap_warns_for_overlapping_only` missing `cfg.fail_on` assertion | Fixed — added `assert cfg.fail_on == ["enrichment"]` |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
