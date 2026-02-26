# Story 18.1: Rule Page Breadcrumb Back-Links

Status: done
Branch: `feat/docs-18-1-rule-page-back-links`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer reading docvet rule documentation**,
I want each rule reference page to show a back-link to its parent check page,
so that I can navigate from a specific rule to the broader check context without using the sidebar.

## Acceptance Criteria

1. **Given** the `docs/rules.yml` file contains a `check` field for each rule (e.g., `check: enrichment`)
   **When** the `rule_header()` macro in `docs/main.py` renders a rule page
   **Then** it generates a visible back-link with text "Part of: {Check} Check" (e.g., "Part of: Enrichment Check")
   **And** the link points to the corresponding check page (e.g., `checks/enrichment.md`)

2. **Given** a rule entry in `docs/rules.yml` with a valid `check` field
   **When** the docs site is built with `mkdocs build --strict`
   **Then** the build succeeds with zero warnings related to back-links

3. **Given** every rule page in the docs site
   **When** a developer visits any rule page
   **Then** the back-link is rendered consistently in the same position across all rule pages (via the macro, not manual content)

## Tasks / Subtasks

- [x] Task 1: Modify `rule_header()` macro in `docs/main.py` to include back-link (AC: #1, #3)
  - [x] 1.1: Add back-link generation using `check` field from `rules.yml`
  - [x] 1.2: Map check name to display name (capitalize: "enrichment" → "Enrichment")
  - [x] 1.3: Map check name to URL path (`checks/{check}.md`)
  - [x] 1.4: Position back-link consistently (above or below the metadata table)
- [x] Task 2: Verify docs build (AC: #2)
  - [x] 2.1: Run `mkdocs build --strict` — zero warnings, zero errors
  - [x] 2.2: Verify all 19 rule pages render back-links correctly
  - [x] 2.3: Verify links navigate to correct check pages
- [x] Task 3: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Verified via `mkdocs build --strict` + manual grep of rendered HTML for "Part of: {Check} Check" across all 4 check types. No automated unit test — no test harness for mkdocs macros exists. | PASS (build gate) |
| 2 | `mkdocs build --strict` exit code 0, zero warnings | PASS |
| 3 | Manual grep count of "Part of:" across all 19 rule page HTML outputs = 19; no individual rule `.md` files modified. No automated regression test. | PASS (build gate) |

## Dev Notes

### Implementation Approach

The entire change is in **one file**: `docs/main.py`. The `rule_header()` macro already has access to the `check` field from `rules.yml`. The back-link is added to the returned markdown string.

### Current `rule_header()` Output

The macro currently returns:

```
| | |
|---|---|
| **Check** | {check} |
| **Category** | {category} |
| **Applies to** | {applies_to} |
| **Since** | v{since} |

> {summary}
```

### Back-Link Implementation

Add a back-link line to the returned markdown. The mapping from `check` value to URL is straightforward:

| `check` value | Display Name | URL Path |
|----------------|-------------|----------|
| `enrichment` | Enrichment Check | `checks/enrichment.md` |
| `freshness` | Freshness Check | `checks/freshness.md` |
| `coverage` | Coverage Check | `checks/coverage.md` |
| `griffe` | Griffe Check | `checks/griffe.md` |

The URL uses a relative path from the rule page location (`rules/missing-raises.md`) to the check page (`checks/enrichment.md`). Since rule pages are under `rules/` and check pages are under `checks/`, the relative path from a rule page to a check page is `../checks/{check}.md`.

Alternatively, use an absolute site path `/checks/{check}/` (mkdocs resolves these). The simplest approach: use `../checks/{check}.md` or just `../checks/{check}/` — mkdocs-material handles both.

### Position Decision

Place the back-link **above** the metadata table, between the `{{ rule_header() }}` call result and the table. This follows the breadcrumb pattern (navigation context appears first, then details). The back-link text should be styled subtly — e.g., a small italic line or a line with an arrow icon.

Recommended format:
```markdown
:material-arrow-left: Part of: [Enrichment Check](../checks/enrichment.md)
```

Or simpler (without icon dependency concerns):
```markdown
*Part of: [Enrichment Check](../checks/enrichment.md)*
```

### Key Files

| File | Role | Change |
|------|------|--------|
| `docs/main.py` | Macros hook — `rule_header()` | Add back-link to return string |
| `docs/rules.yml` | Rule metadata catalog | **No change** — `check` field already exists |
| `docs/site/rules/*.md` | 19 rule pages | **No change** — all use `{{ rule_header() }}` |
| `mkdocs.yml` | Site config | **No change** |

### What NOT to Change

- Do NOT edit individual rule pages — the back-link must come from the macro (NFR3)
- Do NOT add new fields to `rules.yml` — `check` field already provides everything needed
- Do NOT add new plugins or dependencies

### Project Structure Notes

- `docs/main.py` is the macros hook loaded by mkdocs-macros-plugin (configured in `mkdocs.yml` line 84-85)
- `docs/rules.yml` is loaded by `define_env()` at build time and cached in `rules_by_id` dict
- Rule pages are in `docs/site/rules/` and check pages in `docs/site/checks/`
- The nav structure in `mkdocs.yml` groups rules under their check type, but rule pages themselves have no link back to the check page — this story adds that

### References

- [Source: docs/main.py] — `rule_header()` macro implementation (lines 21-51)
- [Source: docs/rules.yml] — Rule metadata with `check` field on all 19 rules
- [Source: mkdocs.yml#nav] — Navigation structure (lines 87-122)
- [Source: docs/site/rules/missing-raises.md] — Example rule page using `{{ rule_header() }}`
- [Source: epics-next.md#Story 2.1] — Original story specification

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (762 passed), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0% (>= 95%)
- [x] `mkdocs build --strict` — zero warnings, zero errors (docs-specific gate)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Single-file change, clean implementation.

### Completion Notes List

- Added back-link line to `rule_header()` macro output in `docs/main.py`
- Back-link uses italic text with format: `*Part of: [{Check} Check](../checks/{check}.md)*`
- Positioned above metadata table following breadcrumb navigation pattern
- Check name capitalized via `.capitalize()` for display ("enrichment" → "Enrichment")
- Relative path `../checks/{check}.md` resolves correctly from `rules/` to `checks/` directory
- All 19 rule pages render back-links automatically via the shared macro (no per-page edits)
- All 7 quality gates pass, 762 tests pass with zero regressions

### Change Log

- 2026-02-25: Added back-link to `rule_header()` macro — all 19 rule pages now show "Part of: {Check} Check" link to parent check page

### File List

- `docs/main.py` — Modified (27 insertions / 4 deletions): back-link generation in `rule_header()` + docstring enrichment (Examples, See Also on module, expanded summaries on `define_env` and `rule_header`)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approved with fixes applied

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | File List description understated scope — claimed "3+1 lines" but actual diff was 27 insertions / 4 deletions including docstring enrichment | Fixed: updated File List to reflect full scope |
| M2 | MEDIUM | AC-to-Test mapping claimed "PASS" but verification was manual grep, not automated tests — no test harness for mkdocs macros exists | Fixed: updated AC table to be transparent about build-gate-only verification |
| L1 | LOW | Redundant f-string `f"{back_link}"` on line 65 — equivalent to just `back_link` | Fixed: changed to `back_link +` |
| L2 | LOW | No defensive handling for missing `check` key in rules.yml entries | Accepted: controlled data file, `mkdocs build --strict` catches at dev time |
| L3 | LOW | Check name duplicated in back-link and metadata table | Accepted: breadcrumb (navigation) vs table row (reference) serve different purposes |
| L4 | LOW | `capitalize()` fragile for hypothetical compound check names | Accepted: YAGNI — all current check names are single words |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
