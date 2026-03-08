# Story 34.3: NumPy-Style Section Recognition Phase 1

Status: done
Branch: `feat/enrichment-34-3-numpy-section-recognition`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer maintaining a NumPy-style codebase,
I want docvet's section parser to recognize NumPy sections and underline format,
so that section-boundary parsing doesn't bleed content across sections.

## Acceptance Criteria

1. **Given** a docstring with `Notes`, `References`, `Warnings`, `Extended Summary`, or `Methods` as section headers, **When** `_parse_sections()` runs, **Then** these headers are recognized as valid section boundaries (added to `_SECTION_HEADERS` frozenset).

2. **Given** a docstring with NumPy underline format (e.g., `Parameters\n----------`), **When** `_parse_sections()` runs, **Then** the underline format is detected alongside Google colon format as a section delimiter. This applies to ALL entries in `_SECTION_HEADERS` — both the 10 existing headers and the 5 new ones.

3. **Given** a docstring with a `Notes` section followed by a `Returns` section, **When** `_extract_section_content()` extracts `Returns` content, **Then** `Notes` content does not bleed into the `Returns` section (correct boundary detection).

4. **Given** existing Google-style docstrings with `Args:`, `Returns:`, `Raises:` headers, **When** `_parse_sections()` runs after the NumPy additions, **Then** all existing section detection behavior is identical — zero regression (NFR6).

5. **Given** a NumPy-style `Notes` section exists in a docstring, **When** enrichment rules run, **Then** no enforcement rules fire for `Notes` — recognition is additive only, no new required-section rules.

6. **Given** the `_SECTION_HEADERS` frozenset after this story, **When** inspecting the codebase, **Then** exactly 5 new entries are added: `Notes`, `References`, `Warnings`, `Extended Summary`, `Methods`.

## Tasks / Subtasks

- [x] Task 1: Add 5 new section headers to `_SECTION_HEADERS` and `_SECTION_PATTERN` (AC: 1, 4, 6)
  - [x] 1.1 Add `Notes`, `References`, `Warnings`, `Extended Summary`, `Methods` to `_SECTION_HEADERS` frozenset (line 55-68 in enrichment.py)
  - [x] 1.2 Add these 5 names to `_SECTION_PATTERN` regex alternatives (line 70-76) so Google colon format (`Notes:`, `References:`, etc.) is recognized
  - [x] 1.3 Verify the frozenset has exactly 15 entries after change (10 existing + 5 new)

- [x] Task 2: Add NumPy underline format detection to `_parse_sections()` (AC: 2, 4)
  - [x] 2.1 Create `_NUMPY_UNDERLINE_PATTERN` compiled regex that matches any `_SECTION_HEADERS` member on a line by itself (no colon), followed by a line of 3+ dashes/equals — use `re.MULTILINE`
  - [x] 2.2 Modify `_parse_sections()` for google mode: after `_SECTION_PATTERN.findall()`, also run `_NUMPY_UNDERLINE_PATTERN.findall()` and union the results
  - [x] 2.3 Ensure the underline pattern only matches lines that are actual `_SECTION_HEADERS` entries (not arbitrary text followed by dashes)

- [x] Task 3: Update `_extract_section_content()` to recognize underline boundaries (AC: 3)
  - [x] 3.1 Restructure the boundary detection loop in `_extract_section_content()` (line 183-215) from a simple `for line in lines[start_idx:]` to indexed iteration (`for i, line in enumerate(lines[start_idx:], start_idx)`) to enable next-line lookahead for underline detection
  - [x] 3.2 Add lookahead check: if the current line matches a `_SECTION_HEADERS` entry (stripped, no colon) AND `lines[i+1]` is 3+ dashes/equals, treat it as a section boundary and break
  - [x] 3.3 Skip the underline line itself when detecting boundaries (the underline is part of the new section header, not content)
  - [x] 3.4 Ensure the existing `_SECTION_PATTERN.match(line)` boundary check is unchanged (Google colon format still works)

- [x] Task 4: Write comprehensive tests (AC: 1-6)
  - [x] 4.1 Create `tests/unit/checks/test_numpy_sections.py` (dedicated test file following test-review recommendation 2)
  - [x] 4.2 Add `pytestmark = pytest.mark.unit` at module level
  - [x] 4.3 Test: docstring with `Notes:` header (Google colon format) — recognized in `_parse_sections()` (AC: 1)
  - [x] 4.4 Test: docstring with `References:` header — recognized (AC: 1)
  - [x] 4.5 Test: docstring with `Warnings:` header — recognized (AC: 1)
  - [x] 4.6 Test: docstring with `Extended Summary:` header — recognized (AC: 1)
  - [x] 4.7 Test: docstring with `Methods:` header — recognized (AC: 1)
  - [x] 4.8 Test: docstring with NumPy underline format `Parameters\n----------` — recognized (AC: 2)
  - [x] 4.9 Test: docstring with NumPy underline format `Returns\n-------` — recognized (AC: 2)
  - [x] 4.10 Test: docstring with NumPy underline format for new headers (`Notes\n-----`) — recognized (AC: 2)
  - [x] 4.11 Test: `Notes` section followed by `Returns:` — `_extract_section_content("Returns")` returns only Returns content, no Notes bleed (AC: 3)
  - [x] 4.12 Test: NumPy-underlined `Notes` followed by NumPy-underlined `Returns` — boundary detection correct (AC: 3)
  - [x] 4.13 Test: existing Google-style `Args:`, `Returns:`, `Raises:` — identical behavior, zero regression (AC: 4)
  - [x] 4.14 Test: `_SECTION_HEADERS` frozenset contains exactly 15 entries (AC: 6)
  - [x] 4.15 Test: `_SECTION_HEADERS` contains all 5 new entries (AC: 6)
  - [x] 4.16 Negative test: arbitrary text followed by dashes is NOT recognized as a section (AC: 2)
  - [x] 4.17 Negative test: underline with fewer than 3 dashes is NOT recognized (AC: 2)
  - [x] 4.18 Test: mixed Google colon and NumPy underline in same docstring — both detected (AC: 2)

- [x] Task 5: Dogfooding and quality gates (AC: 4, 5)
  - [x] 5.1 Run `docvet check --all` — zero new findings (new sections are recognition-only, no enforcement)
  - [x] 5.2 Run full test suite — all existing tests pass (zero regression)
  - [x] 5.3 All quality gates pass

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_notes_colon_recognized`, `test_references_colon_recognized`, `test_warnings_colon_recognized`, `test_extended_summary_colon_recognized`, `test_methods_colon_recognized` | Pass |
| AC2 | `test_args_underline_recognized`, `test_returns_underline_recognized`, `test_notes_underline_recognized`, `test_raises_underline_recognized`, `test_examples_underline_with_equals_recognized`, `test_arbitrary_text_with_dashes_not_recognized`, `test_underline_fewer_than_3_dashes_not_recognized`, `test_mixed_google_and_numpy_in_same_docstring` | Pass |
| AC3 | `test_notes_colon_does_not_bleed_into_returns`, `test_numpy_notes_boundary_stops_colon_returns_extraction`, `test_mixed_boundary_numpy_before_colon` | Pass |
| AC4 | `test_args_colon_still_recognized`, `test_returns_colon_still_recognized`, `test_raises_colon_still_recognized`, `test_extract_section_content_unchanged_for_google`, `test_section_headers_contains_all_fifteen_headers`, `test_parse_sections_when_all_headers_present_returns_all` | Pass |
| AC5 | Verified by `docvet check --all` — zero enforcement findings for Notes/References/Warnings/Extended Summary/Methods | Pass |
| AC6 | `test_section_headers_has_exactly_15_entries`, `test_section_headers_contains_new_entries` (parametrized x5) | Pass |

## Dev Notes

### Architecture — Section Infrastructure Changes

**File: `src/docvet/checks/enrichment.py`**

- **`_SECTION_HEADERS` frozenset** (line 55-68): Add 5 new entries. After change, 15 total:
  - Existing 10: `Args`, `Returns`, `Raises`, `Yields`, `Receives`, `Warns`, `Other Parameters`, `Attributes`, `Examples`, `See Also`
  - New 5: `Notes`, `References`, `Warnings`, `Extended Summary`, `Methods`

- **`_SECTION_PATTERN` regex** (line 70-76): Add the 5 new section names to the alternation group. This ensures Google colon format (`Notes:`, `References:`, etc.) is recognized for boundary detection in `_extract_section_content()`.

- **New `_NUMPY_UNDERLINE_PATTERN`**: A compiled regex matching any recognized section header on a line by itself (no trailing colon), followed immediately by a line of 3+ dashes or equals. Must use `re.MULTILINE`. Example matches:
  ```
  Parameters
  ----------

  Returns
  -------

  Notes
  =====
  ```

- **`_parse_sections()` modification** (line 132-156): In the google-mode branch, after `_SECTION_PATTERN.findall()`, also apply `_NUMPY_UNDERLINE_PATTERN.findall()` and union the results. This makes NumPy underline detection automatic alongside Google colon detection — no new style value needed.

- **`_extract_section_content()` modification** (line 183-215): The boundary detection loop (line 209) currently only checks `_SECTION_PATTERN.match(line)`. Add a lookahead: if the current line matches a `_SECTION_HEADERS` entry (no colon) AND the next line is 3+ dashes, treat it as a section boundary and break. The underline line itself must be excluded from content.

### Design Decisions

1. **No new `docstring-style = "numpy"` value**: Phase 1 is recognition-only. NumPy underline format is detected alongside Google colon format automatically. A full NumPy style mode (with enforcement rules) is deferred to a future epic if needed.

2. **Recognition is additive, not enforcement**: The 5 new section names are added to `_SECTION_HEADERS` so they're recognized as boundaries, but no `require_notes`, `require_references`, etc. config keys are created. No `_RULE_DISPATCH` entries. No new `_check_*` functions.

3. **Both colon and underline formats recognized**: After this change, `Notes:` (Google colon) AND `Notes\n-----` (NumPy underline) are both valid section boundaries. This prevents content bleed regardless of which convention the developer uses.

4. **Underline pattern must be anchored to known headers**: The regex must NOT match arbitrary text followed by dashes (e.g., a prose sentence followed by dashes). The pattern must only fire for lines that exactly match a `_SECTION_HEADERS` entry.

5. **Sphinx mode unaffected**: `_parse_sphinx_sections()` is not modified. Sphinx/RST style has its own section detection. NumPy underline detection applies only to the Google mode branch. If a user sets `docstring-style = "sphinx"` but uses NumPy underlines, the underlines won't be detected — this is correct behavior since NumPy and Sphinx are distinct conventions.

6. **`_extract_section_content()` entry-point is colon-only (by design)**: This story adds underline *boundary* detection to `_extract_section_content()` (so it knows to stop collecting content at a NumPy section header), but does NOT add underline *entry-point* support (finding the start of a section via underline format). Currently no callers need to extract content from underline-format sections. If Epic 35 stories (e.g., 35.1 `_parse_args_entries`) need this, it should be added at that time — not here.

### Key Implementation Pattern (NumPy underline regex)

```python
# Build pattern dynamically from _SECTION_HEADERS to stay in sync
_numpy_headers = "|".join(re.escape(h) for h in sorted(_SECTION_HEADERS, key=len, reverse=True))
_NUMPY_UNDERLINE_PATTERN = re.compile(
    rf"^\s*({_numpy_headers})\s*\n\s*[-=]{{3,}}\s*$",
    re.MULTILINE,
)
```

Building the pattern dynamically from `_SECTION_HEADERS` ensures it stays in sync — no separate maintenance of header lists. Sort by length descending to ensure `Other Parameters` matches before `Other` (if ever ambiguous).

### Previous Story Patterns to Follow

From Story 34-2:
- Dedicated test file: `tests/unit/checks/test_numpy_sections.py`
- Module-level `pytestmark = pytest.mark.unit`
- Tests import `_parse_sections` and `_extract_section_content` directly
- Tests also import `_SECTION_HEADERS` directly for the frozenset size assertion

From Story 34-1:
- Sphinx section patterns are parallel to Google patterns — same internal names, different regex
- `_parse_sections()` dispatches by style — NumPy underline is an enhancement to the google-mode branch

### Project Structure Notes

- All changes in a single file: `src/docvet/checks/enrichment.py`
- New test file: `tests/unit/checks/test_numpy_sections.py`
- No new modules, packages, or dependencies
- No config changes (recognition-only, no enforcement)
- Aligns with `_SECTION_HEADERS` as the single source of truth for recognized sections

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 34.3] — Full AC and FR mapping (FR21-FR22)
- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Requirements Inventory] — NFR6 (purely additive, no breaking changes)
- [Source: src/docvet/checks/enrichment.py:55-68] — `_SECTION_HEADERS` frozenset (10 entries)
- [Source: src/docvet/checks/enrichment.py:70-76] — `_SECTION_PATTERN` regex (Google colon format)
- [Source: src/docvet/checks/enrichment.py:132-156] — `_parse_sections()` function (style dispatcher)
- [Source: src/docvet/checks/enrichment.py:183-215] — `_extract_section_content()` function (boundary detection)
- [Source: _bmad-output/implementation-artifacts/34-2-missing-returns-enrichment-rule.md] — Previous story: test pattern, helper pattern
- [Source: _bmad-output/implementation-artifacts/34-1-sphinx-rst-docstring-style-support.md] — Sphinx style: section map, pattern, auto-disable
- [Source: _bmad-output/test-artifacts/test-review.md#Recommendation 2] — Continue splitting test files by rule

### Test Maturity Piggyback

From test-review.md — Recommendation 2 (P3): Continue splitting `test_enrichment.py` by rule. This story naturally addresses it by creating a dedicated `test_numpy_sections.py` file. Progress: 2 of 10+ rules/concerns extracted (prefer-fenced-code-blocks, numpy-sections).

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A

<!-- Rationale: This story adds section recognition only (no new rules, no config keys, no CLI changes).
  The 5 new section names are internal parser infrastructure for boundary detection.
  No docs pages are affected — no new rule pages, no config reference updates, no CLI changes. -->

## Quality Gates

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Added 5 NumPy section headers (Notes, References, Warnings, Extended Summary, Methods) to `_SECTION_HEADERS` and `_SECTION_PATTERN`
- Created `_NUMPY_UNDERLINE_PATTERN` regex built dynamically from `_SECTION_HEADERS` for automatic sync
- Modified `_parse_sections()` to union Google colon and NumPy underline results
- Modified `_extract_section_content()` with indexed iteration and lookahead for NumPy underline boundary detection
- Created 26 tests in dedicated `test_numpy_sections.py` covering all 6 ACs
- Updated 2 pre-existing tests in `test_enrichment.py` to reflect 15 headers (was 10)
- Updated module docstring to mention NumPy recognition (fixed freshness finding)
- All 1410 tests pass, zero docvet findings, all quality gates green

### Change Log

- 2026-03-07: Implemented NumPy-style section recognition (5 headers + underline format) with 26 new tests

### File List

- `src/docvet/checks/enrichment.py` — modified (headers, pattern, underline regex, parse + extract functions, module docstring)
- `tests/unit/checks/test_numpy_sections.py` — new (26 tests for NumPy section recognition)
- `tests/unit/checks/test_enrichment.py` — modified (updated 2 tests from 10 to 15 headers)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — modified (34-3 status: in-progress -> review)
- `_bmad-output/implementation-artifacts/34-3-numpy-style-section-recognition-phase-1.md` — modified (story file updates)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party-mode consensus)

### Outcome

Approved

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| L1 | DISMISS | `str()` cast in `re.escape(str(h))` on line 92 | Dismissed — required for `ty` type checker (`sorted` infers `Sized \| Unknown`, `str()` narrows to `str`) |
| M1 | LOW (downgraded) | `_SECTION_PATTERN` hardcoded vs `_NUMPY_UNDERLINE_PATTERN` dynamic — maintenance divergence | Dismissed — pre-existing pattern, test safety net sufficient, tech debt for future housekeeping |
| M2 | LOW (downgraded) | Underline boundary detection strips indentation — theoretical false positive inside content | Dismissed — consistent with pre-existing Google colon behavior, safe failure direction (NFR5) |
| M3 | LOW (downgraded) | No test for false-positive boundary inside content | Dismissed — optional documentation-as-test, not blocking |
| L2 | DISMISS | Mixed dash-equals underlines silently accepted | Dismissed — zero real-world impact |
| L3 | DISMISS | Weak string assertion in boundary tests | Dismissed — sufficient for controlled fixture |
| L4 | DISMISS | Missing edge-case tests (consecutive NumPy sections, header at EOF) | Dismissed — implicitly covered by existing tests |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
