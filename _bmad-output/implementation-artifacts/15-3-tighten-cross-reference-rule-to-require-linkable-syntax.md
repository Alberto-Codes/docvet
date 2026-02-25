# Story 15.3: Tighten Cross-Reference Rule to Require Linkable Syntax

Status: review
Branch: `feat/enrichment-15-3-tighten-cross-reference-rule`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer using docvet to enforce docstring quality**,
I want **the `missing-cross-references` rule to flag See Also entries that use plain backtick syntax (which doesn't produce clickable links in mkdocstrings)**,
So that **my documentation cross-references actually navigate when rendered, not just look like code**.

## Acceptance Criteria

1. **Given** the `_check_missing_cross_references` function in `enrichment.py` currently accepts `_XREF_BACKTICK` (`` r"`[^`]+`" ``) as valid cross-reference syntax **When** the `_XREF_BACKTICK` pattern is removed from the pass condition (line 1178) **Then** See Also sections containing only plain backtick references (e.g., `` `docvet.checks` ``) produce a `missing-cross-references` finding **And** See Also sections containing bracket references (`[docvet.checks][]`) or Sphinx roles (`:func:`docvet.checks``) continue to pass

2. **Given** the rule logic is updated **When** a See Also section contains `` [`docvet.checks`][] `` (backtick content inside bracket reference) **Then** the rule passes — the `_XREF_MD_LINK` pattern matches the bracket syntax regardless of backtick content inside

3. **Given** the rule documentation at `docs/site/rules/missing-cross-references.md` **When** the "Fix" example is updated **Then** it shows bracket cross-reference syntax (`` [`myapp.utils.parsing`][] ``) instead of plain backtick syntax **And** the "What it detects" section explains that plain backtick syntax doesn't produce clickable links in mkdocstrings

4. **Given** the existing test `test_cross_refs_when_see_also_with_backtick_xrefs_returns_none` **When** the test is updated to reflect the tightened rule **Then** the test is renamed to `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding` (name must match new behavior) **And** it asserts that backtick-only See Also entries now produce a finding (not `None`) **And** a new test verifies that bracket syntax See Also entries return `None` (pass)

5. **Given** all rule changes are applied **When** `docvet check --all` is executed against the docvet codebase **Then** zero findings are produced (own codebase was already fixed in Story 15.2)

6. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all tests pass with zero failures

## Tasks / Subtasks

- [x] Task 1: Remove `_XREF_BACKTICK` from pass condition in `enrichment.py` (AC: 1, 2)
  - [x] Remove `_XREF_BACKTICK.search(line) or` from the `or` chain at line 1178
  - [x] Remove the `_XREF_BACKTICK` constant at line 66 (dead code after removal from pass condition)
  - [x] Update the comment at line 65 to reflect only two remaining patterns
- [x] Task 2: Update existing tests that use backtick-only See Also entries (AC: 4)
  - [x] Rename `test_cross_refs_when_see_also_with_backtick_xrefs_returns_none` (line 3421) → `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding` and change assertion to expect a Finding
  - [x] Update `test_cross_refs_when_non_init_module_with_see_also_returns_none` (line 3298) — uses backtick syntax, now must expect a finding; rename to `test_cross_refs_when_non_init_module_with_backtick_see_also_returns_finding`
  - [x] Update `test_cross_refs_when_init_module_has_see_also_with_xrefs_returns_none` (line 3515) — uses backtick syntax, now must expect a finding; rename to `test_cross_refs_when_init_module_has_backtick_see_also_returns_finding`
- [x] Task 3: Add new tests for bracket syntax passing (AC: 2, 4)
  - [x] Add `test_cross_refs_when_non_init_module_with_bracket_see_also_returns_none` — module-level with `[`docvet.checks`][]` syntax
  - [x] Add `test_cross_refs_when_init_module_has_bracket_see_also_returns_none` — `__init__.py` with bracket syntax
  - [x] Add `test_cross_refs_when_see_also_with_code_bracket_xrefs_returns_none` — class-level with `` [`some.module`][] `` syntax (code-formatted brackets, AC2 specifically)
- [x] Task 4: Update rule documentation page (AC: 3)
  - [x] Update "What it detects" paragraph to explain backtick syntax doesn't produce clickable links
  - [x] Update "Fix" example to use bracket cross-reference syntax `` [`myapp.utils.parsing`][] ``
- [x] Task 5: Convert `tests/fixtures/complete_module.py` See Also entries to bracket syntax (AC: 5)
  - [x] Module-level: `` `tests.fixtures` `` → `` [`tests.fixtures`][] ``
  - [x] `generate_numbers` function: `` `generate_numbers` `` → `` [`generate_numbers`][] ``
  - [x] `process` function: `` `Connection` `` → `` [`Connection`][] ``
  - [x] `Connection` class: `` `ValidationResult` `` → `` [`ValidationResult`][] ``
  - [x] `ValidationResult` class: `` `process` `` → `` [`process`][] ``
  - [x] Also converted `tests/fixtures/missing_raises.py` and `tests/fixtures/missing_yields.py` (same backtick pattern)
- [x] Task 6: Run all quality gates (AC: 5, 6)
  - [x] `uv run ruff check .` — zero violations
  - [x] `uv run ruff format --check .` — zero format issues
  - [x] `uv run ty check` — zero type errors
  - [x] `uv run pytest` — 746 passed, zero failures
  - [x] `uv run docvet check --all` — zero enrichment/coverage/griffe findings (1 freshness stale-body from uncommitted changes — expected)
  - [x] `uv run interrogate -v` — 100%

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding`, `test_cross_refs_when_see_also_with_markdown_link_returns_none`, `test_cross_refs_when_see_also_with_sphinx_role_returns_none` | PASS |
| AC2 | `test_cross_refs_when_see_also_with_code_bracket_xrefs_returns_none` | PASS |
| AC3 | Manual inspection: "What it detects" updated, "Fix" example uses bracket syntax | PASS |
| AC4 | `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding` (renamed), `test_cross_refs_when_see_also_with_code_bracket_xrefs_returns_none` (new) | PASS |
| AC5 | `uv run docvet enrichment --all` — zero findings; all fixtures converted | PASS |
| AC6 | `uv run pytest` — 746 passed, zero failures | PASS |

## Dev Notes

### Code Change: enrichment.py

**Line 66** — Remove the `_XREF_BACKTICK` constant:
```python
# Before:
_XREF_BACKTICK = re.compile(r"`[^`]+`")
_XREF_MD_LINK = re.compile(r"\[[^\]]+\]\[")
_XREF_SPHINX = re.compile(r":\w+:`[^`]+`")

# After:
_XREF_MD_LINK = re.compile(r"\[[^\]]+\]\[")
_XREF_SPHINX = re.compile(r":\w+:`[^`]+`")
```

**Lines 1177-1181** — Remove `_XREF_BACKTICK` from the pass condition:
```python
# Before:
if (
    _XREF_BACKTICK.search(line)
    or _XREF_MD_LINK.search(line)
    or _XREF_SPHINX.search(line)
):
    return None

# After:
if _XREF_MD_LINK.search(line) or _XREF_SPHINX.search(line):
    return None
```

### Test Updates

**3 tests change behavior** (backtick-only See Also now returns a finding):

| Test (current name) | Line | Old Assertion | New Assertion |
|---------------------|------|---------------|---------------|
| `test_cross_refs_when_see_also_with_backtick_xrefs_returns_none` | 3421 | `assert result is None` | `assert result is not None` + verify Finding fields |
| `test_cross_refs_when_non_init_module_with_see_also_returns_none` | 3298 | `assert result is None` | `assert result is not None` + verify Finding fields |
| `test_cross_refs_when_init_module_has_see_also_with_xrefs_returns_none` | 3515 | `assert result is None` | `assert result is not None` + verify Finding fields |

**3 new tests** for bracket syntax:
- Non-init module with bracket See Also → `None`
- Init module with bracket See Also → `None`
- Class with code-formatted bracket syntax (`` [`some.module`][] ``) → `None`

**Existing passing tests** (should remain unchanged):
- `test_cross_refs_when_see_also_with_markdown_link_returns_none` (line 3442) — `[module][some.module]` uses `_XREF_MD_LINK`, unaffected
- `test_cross_refs_when_see_also_with_sphinx_role_returns_none` (line 3463) — `:mod:` uses `_XREF_SPHINX`, unaffected
- `test_cross_refs_when_markdown_shorthand_link_returns_none` (line 3611) — `[identifier][]` uses `_XREF_MD_LINK`, unaffected

### Fixture: complete_module.py

The `tests/fixtures/complete_module.py` file has 5 See Also sections using plain backtick syntax. These MUST be converted to bracket syntax before Story 15.3's rule change, or `docvet check --all` will find them (they're Python files that docvet scans).

### Rule Docs Update

`docs/site/rules/missing-cross-references.md`:
- "What it detects" needs clarification that backtick-only syntax no longer passes
- "Fix" example: change `` `myapp.utils.parsing` `` → `` [`myapp.utils.parsing`][] ``

### Why This Change Matters

Plain backtick syntax (`` `module.name` ``) renders as `<code>module.name</code>` — styled text but NOT a hyperlink. Bracket syntax (`` [`module.name`][] ``) renders as a clickable link resolved by the autorefs plugin. The original rule accepted backticks as a pragmatic starting point, but now that Story 15.2 established the bracket convention on our own codebase, we can tighten the rule to enforce syntax that actually produces links.

### Pattern Compatibility

The `_XREF_MD_LINK` pattern (`r"\[[^\]]+\]\["`) matches all of these bracket formats:
- `[identifier][]` — plain shorthand
- `[`identifier`][]` — code-formatted (wraps backtick content in brackets)
- `[text][identifier]` — explicit reference

The `_XREF_SPHINX` pattern (`r":\w+:`[^`]+`"`) matches:
- `:func:`module.name`` — Sphinx roles

Both patterns are tested by existing tests that should NOT change.

### Project Structure Notes

- All source changes in `src/docvet/checks/enrichment.py` (lines 66, 1177-1181)
- Test changes in `tests/unit/checks/test_enrichment.py` (3 renames + 3 new)
- Fixture changes in `tests/fixtures/complete_module.py` (5 See Also entries)
- Docs changes in `docs/site/rules/missing-cross-references.md`

### References

- [Source: _bmad-output/planning-artifacts/epics-docs-quality.md — Story 15.3, FR-Q12/Q13/Q14]
- [Source: src/docvet/checks/enrichment.py:66-68 — cross-reference detection patterns]
- [Source: src/docvet/checks/enrichment.py:1177-1181 — pass condition to modify]
- [Source: tests/unit/checks/test_enrichment.py:3298,3421,3515 — tests to update]
- [Source: tests/fixtures/complete_module.py:8-9,36-37,58-59,79-80,108-109 — fixture See Also entries]
- [Source: docs/site/rules/missing-cross-references.md — rule documentation page]
- [Source: _bmad-output/implementation-artifacts/15-2-fix-own-cross-reference-syntax.md — previous story intelligence]

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 746 passed, zero failures
- [x] `uv run docvet check --all` — zero enrichment/coverage/griffe findings
- [x] `uv run interrogate -v` — 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero errors encountered.

### Completion Notes List

- Removed `_XREF_BACKTICK` constant and its usage from enrichment.py pass condition
- Updated `_check_missing_cross_references` docstring to reflect tightened rule
- Renamed 3 tests from `returns_none` to `returns_finding` with updated assertions verifying all Finding fields
- Added 3 new bracket-syntax tests (code-bracket, module-level bracket, init-module bracket)
- Updated rule docs: "What it detects" explains why backtick doesn't link; "Fix" example uses bracket syntax
- Converted 7 fixture See Also entries across 3 fixture files (complete_module.py, missing_raises.py, missing_yields.py)
- All 746 tests pass, zero enrichment/coverage/griffe findings

### Change Log

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | Removed `_XREF_BACKTICK` constant (line 66), removed from pass condition (line 1178), updated docstring |
| `tests/unit/checks/test_enrichment.py` | Renamed 3 tests, updated assertions to expect findings, added 3 new bracket-syntax tests |
| `docs/site/rules/missing-cross-references.md` | Updated "What it detects" and "Fix" example to bracket syntax |
| `tests/fixtures/complete_module.py` | Converted 5 See Also entries from backtick to bracket syntax |
| `tests/fixtures/missing_raises.py` | Converted 1 See Also entry from backtick to bracket syntax |
| `tests/fixtures/missing_yields.py` | Converted 1 See Also entry from backtick to bracket syntax |

### File List

- `src/docvet/checks/enrichment.py`
- `tests/unit/checks/test_enrichment.py`
- `docs/site/rules/missing-cross-references.md`
- `tests/fixtures/complete_module.py`
- `tests/fixtures/missing_raises.py`
- `tests/fixtures/missing_yields.py`

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
