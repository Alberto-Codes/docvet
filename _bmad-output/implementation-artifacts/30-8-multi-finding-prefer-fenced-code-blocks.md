# Story 30.8: Multi-finding prefer-fenced-code-blocks

Status: review
Branch: `feat/enrichment-30-8-multi-finding-fenced-code-blocks`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer fixing docstring issues**,
I want `prefer-fenced-code-blocks` to report all non-fenced patterns in one pass,
so that I can fix both `>>>` doctest and `::` rST blocks in a single run instead of a whack-a-mole cycle.

## Acceptance Criteria

1. **Given** a docstring's `Examples:` section contains both `>>>` (doctest) and `::` (rST) non-fenced patterns, **when** enrichment runs the `prefer-fenced-code-blocks` check, **then** 2 findings are returned — one for each pattern type — with distinct messages identifying the pattern type.

2. **Given** a docstring's `Examples:` section contains only `>>>` (doctest) non-fenced pattern, **when** enrichment runs the check, **then** 1 finding is returned for the `>>>` pattern (unchanged from current behavior).

3. **Given** a docstring's `Examples:` section contains only `::` (rST) non-fenced pattern, **when** enrichment runs the check, **then** 1 finding is returned for the `::` pattern (unchanged from current behavior).

4. **Given** a docstring with no `>>>` or `::` patterns, **when** enrichment runs the check, **then** zero findings are returned (unchanged from current behavior).

5. **Given** a docstring with multiple `>>>` blocks but no `::` patterns, **when** enrichment runs the check, **then** 1 finding is returned (deduplicated per pattern type, not per occurrence — max 2 findings per symbol).

6. **Given** the `_RULE_DISPATCH` table, **when** reviewing the implementation approach, **then** the dispatch contract (`_CheckFn` returning `Finding | None`) is unchanged — accumulation of multiple findings happens in `check_enrichment()` orchestrator, not in the dispatch machinery.

7. **Given** the enrichment check runs on a file with multiple symbols, each with different pattern combinations, **when** results are collected, **then** each symbol's findings are independent — a symbol with both patterns gets 2 findings, a symbol with one pattern gets 1.

8. **Given** the existing enrichment test suite, **when** all tests run after the change, **then** all existing tests pass (no regressions in other rules).

## Tasks / Subtasks

- [x] Task 1: Add `_check_fenced_code_blocks_extra` helper (AC: 1, 6)
  - [x] 1.1 Create helper that checks for the *other* pattern type (rST if dispatch found doctest, doctest if dispatch found rST)
  - [x] 1.2 Helper returns `Finding | None` — same interface as dispatch functions
- [x] Task 2: Modify `check_enrichment()` orchestrator (AC: 1, 5, 6, 7)
  - [x] 2.1 After dispatch loop finds a `prefer_fenced_code_blocks` finding, call the extra helper for the remaining pattern type
  - [x] 2.2 Append second finding if found (max 2 per symbol for this rule)
- [x] Task 3: Update existing test (AC: 1, 8)
  - [x] 3.1 Renamed to `test_fenced_blocks_when_mixed_doctest_and_rst_direct_returns_doctest_finding` — clarifies it tests the direct function (still returns only doctest). New orchestrator-level test covers the 2-finding case.
- [x] Task 4: Add new tests (AC: 1, 2, 3, 4, 5, 7)
  - [x] 4.1 Test: `test_orchestrator_mixed_doctest_and_rst_returns_two_findings` — both patterns → 2 findings with distinct messages
  - [x] 4.2 Test: `test_orchestrator_multiple_doctest_blocks_no_rst_returns_one_finding` — dedup per pattern type
  - [x] 4.3 Test: (merged with 4.1 — same orchestrator-level test)
  - [x] 4.4 Test: `test_orchestrator_multi_symbol_mixed_patterns_independent` — independent findings per symbol
  - [x] 4.5 Test: `test_orchestrator_single_doctest_pattern_returns_one_finding` + `test_orchestrator_single_rst_pattern_returns_one_finding` + `test_orchestrator_no_patterns_returns_zero_findings` — regression guards for AC 2, 3, 4
  - [x] 4.6 Test: `test_orchestrator_doctest_inside_fenced_and_rst_outside_returns_two_findings` — edge case

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_orchestrator_mixed_doctest_and_rst_returns_two_findings` | Pass |
| 2 | `test_orchestrator_single_doctest_pattern_returns_one_finding` | Pass |
| 3 | `test_orchestrator_single_rst_pattern_returns_one_finding` | Pass |
| 4 | `test_orchestrator_no_patterns_returns_zero_findings` | Pass |
| 5 | `test_orchestrator_multiple_doctest_blocks_no_rst_returns_one_finding` | Pass |
| 6 | `_check_fenced_code_blocks_extra` returns `Finding | None`; `_RULE_DISPATCH` unchanged | Pass |
| 7 | `test_orchestrator_multi_symbol_mixed_patterns_independent` | Pass |
| 8 | All 211 existing test_enrichment.py tests pass, all 16 migrated tests pass | Pass |

## Dev Notes

### Current Implementation (What Changes)

The `_check_prefer_fenced_code_blocks` function (`enrichment.py:1228-1300`) currently uses a **two-pass fast-fail** design:
1. Scan for `>>>` (doctest) — if found, return Finding immediately
2. Scan for `::` (rST) — if found, return Finding
3. Return None

This means if both `>>>` and `::` exist, only the doctest finding is reported. The user fixes doctest, reruns, then sees the rST finding — whack-a-mole.

### Implementation Approach (Orchestrator-Level Accumulation)

**Do NOT change `_check_prefer_fenced_code_blocks` or `_RULE_DISPATCH` contract.** The dispatch function continues returning `Finding | None` (first match). The orchestrator handles the second pass.

**New helper function:** `_check_fenced_code_blocks_extra(symbol, sections, node_index, config, file_path, first_finding) -> Finding | None`

This helper inspects the `first_finding.message` to determine which pattern was already found, then checks for the *other* pattern:
- If first finding mentions `>>>` → check for `::` (rST)
- If first finding mentions `::` → check for `>>>` (doctest)

**Orchestrator change in `check_enrichment()` (lines 1358-1361):**

```python
for attr, check_fn in _RULE_DISPATCH:
    if getattr(config, attr):
        if f := check_fn(symbol, sections, node_index, config, file_path):
            findings.append(f)
            # Multi-finding: check for second pattern type
            if attr == "prefer_fenced_code_blocks":
                if extra := _check_fenced_code_blocks_extra(
                    symbol, sections, node_index, config, file_path, f
                ):
                    findings.append(extra)
```

This is minimal: 3 lines added to the orchestrator, one new helper function. The dispatch contract is untouched.

### Alternative Considered: Split _check_prefer_fenced_code_blocks

Could refactor the function to return both findings internally and change the dispatch contract to `Finding | list[Finding] | None`. Rejected because:
- Changes `_CheckFn` type signature (breaks all 10 dispatch functions)
- Adds union-type complexity to the orchestrator loop
- Only one rule needs multi-finding — not worth generalizing

### Pattern Detection Logic for Extra Helper

Reuse the same detection patterns already defined at module level:
- `_DOCTEST_PATTERN = re.compile(r"^\s*>>>")` (line 1200)
- `_RST_BLOCK_PATTERN = re.compile(r"::\s*$")` (line 1201)
- `_has_rst_indented_block()` helper (line 1204)

The extra helper doesn't need new regex — it reuses existing infrastructure.

### Message Discrimination

The first finding's message contains either `">>>"` or `"::"` — use this to determine which pattern was already reported:

```python
if ">>>" in first_finding.message:
    # First finding was doctest — check for rST
    ...
else:
    # First finding was rST — check for doctest
    ...
```

### Deduplication (AC 5)

Max 2 findings per symbol for this rule: one `>>>`, one `::`. Multiple `>>>` blocks in the same Examples section produce one finding. Multiple `::` blocks produce one finding. This is already the current behavior — the function short-circuits on first match of each type.

### Existing Test That Changes

`test_fenced_blocks_when_mixed_doctest_and_rst_returns_doctest_finding` (line 4011) currently asserts:
- `result is not None`
- `">>>" in result.message`
- `"::" not in result.message`

This test must be updated. It was testing the direct function (which still returns only doctest). Add a **new orchestrator-level test** that asserts 2 findings for the mixed case.

**Important:** Direct-function tests (`_check_prefer_fenced_code_blocks` called directly) MUST stay unchanged — the function still returns only the first match. All new multi-finding tests MUST go through `check_enrichment()` orchestrator, since that's where the second-pass accumulation happens. Do NOT modify existing direct-function tests to expect 2 findings.

### Edge Case: Doctest Inside Fenced Block + rST Outside

The existing test `test_fenced_blocks_when_doctest_inside_fenced_block_returns_finding` (line 3908) shows that `>>>` inside fenced blocks still fires a finding. If a docstring has `>>>` inside a fenced block AND a `::` rST block outside, both findings should fire via the orchestrator. Add a dedicated test for this (Task 4.6).

### Future Note

If a second enrichment rule ever needs multi-finding, refactor `_CheckFn` to return `list[Finding]` at that point (Option 2 from party-mode debate). The current special-case approach is justified because only `prefer-fenced-code-blocks` has two distinct pattern types — no other rule has this characteristic.

### Key Files

- **Modified:** `src/docvet/checks/enrichment.py` — new helper + 3-line orchestrator change
- **Modified:** `tests/unit/checks/test_enrichment.py` — new tests, possibly update existing

### Project Structure Notes

- No new files — all changes in existing enrichment module and test file
- No config changes — `prefer_fenced_code_blocks` boolean stays the same
- No CLI changes — findings flow through existing pipeline

### References

- [Source: _bmad-output/planning-artifacts/epics-distribution-adoption.md, Story 30.8]
- [Source: src/docvet/checks/enrichment.py — `_check_prefer_fenced_code_blocks` lines 1228-1300]
- [Source: src/docvet/checks/enrichment.py — `check_enrichment` orchestrator lines 1326-1363]
- [Source: src/docvet/checks/enrichment.py — `_RULE_DISPATCH` lines 1312-1323, `_CheckFn` lines 1307-1310]
- [Source: tests/unit/checks/test_enrichment.py — existing fenced-code tests lines 3751-4134]
- [FR14: Multi-finding prefer-fenced-code-blocks]
- [NFR9: Dispatch contract unchanged]

### Previous Story Intelligence

Stories 30-5 and 30-6 were docs-only — no code patterns to carry forward. The most recent code story in the enrichment module was Epic 3 (Story 3-2, format and cross-reference rules). The `_check_prefer_fenced_code_blocks` function follows the same pattern established then.

### Test Maturity Piggyback

**Source:** `_bmad-output/test-artifacts/test-review.md` (2026-03-06, score 95/100)

**Selected item (P3, Maintainability — Recommendation 2):** Extract the prefer-fenced-code-blocks tests from `test_enrichment.py` (lines 3751-4134, ~380 lines + new tests from this story) into a dedicated `tests/unit/checks/test_prefer_fenced_code_blocks.py`. This directly addresses the "split test_enrichment.py by rule" recommendation and is naturally scoped — we're already modifying these tests. The new file gets the existing 16 tests plus the ~6 new multi-finding tests. Demonstrates the pattern for future rule-level splits without touching unrelated test code.

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A (internal behavior change — the rule name, config key, and message format stay the same; users just get more findings per run)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1208 tests pass, no regressions
- [x] `uv run docvet check --all` — 2 recommended freshness findings (stale-body from uncommitted changes, will clear on commit)
- [x] `uv run interrogate -v src/` — 100% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Clean implementation.

### Completion Notes List

- Added `_check_fenced_code_blocks_extra` helper in `enrichment.py` — checks for the *other* pattern type after the first is found by the dispatch function
- Modified `check_enrichment()` orchestrator with 4-line addition to call the extra helper when `prefer_fenced_code_blocks` fires
- Extracted all 16 prefer-fenced-code-blocks tests from `test_enrichment.py` into dedicated `test_prefer_fenced_code_blocks.py` (test maturity piggyback)
- Added 7 new orchestrator-level multi-finding tests covering all ACs
- Renamed mixed-case direct-function test to clarify it tests the direct function (which still returns only first match)
- `_RULE_DISPATCH` and `_CheckFn` type signature untouched — dispatch contract preserved

### Change Log

- 2026-03-06: Implemented multi-finding prefer-fenced-code-blocks (all 4 tasks + test extraction piggyback)

### File List

- `src/docvet/checks/enrichment.py` — added `_check_fenced_code_blocks_extra` helper + 4-line orchestrator change
- `tests/unit/checks/test_prefer_fenced_code_blocks.py` — new file: 16 extracted + 7 new tests
- `tests/unit/checks/test_enrichment.py` — removed 16 fenced-code-blocks tests (extracted), removed unused import

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
