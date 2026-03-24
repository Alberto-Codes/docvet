# Sprint Change Proposal — 2026-03-23

## Issue Summary

During pre-development review of Epic 32 (Linter Lifecycle: Fix & Suppress), a design gap was identified: the existing ACs assume `docvet fix` scaffolds stubs and `docvet check` then produces zero findings — silently accepting empty placeholders as complete documentation. This defeats docvet's purpose.

**Decision:** Scaffolded stubs must NOT pass `docvet check`. A new `scaffold` finding category (required severity) with actionable messages guides users to fill in real content.

## Impact Analysis

- **Epic Impact:** Epic 32 only. No other epics affected.
- **Story Impact:** Stories 32-1, 32-2, 32-3 require AC modifications. Story 32-4 unaffected.
- **Artifact Conflicts:** `Finding` dataclass needs a new `scaffold` category. Reporting, exit codes, and JSON output need to handle it. No PRD or architecture changes.
- **Technical Impact:** Minor — one new category value, one new detection rule, message formatting.

## Recommended Approach

**Direct Adjustment.** Modify existing story ACs. No new stories, no resequencing.

- Effort: Low
- Risk: Low
- Timeline impact: None — stories haven't started

## Detailed Changes

| Story | Change |
|-------|--------|
| **32-1** | Add scaffold category design + placeholder marker spec to spike deliverables |
| **32-2** | Change "zero findings" ACs to "scaffold findings." Add ACs for scaffold category on Finding, actionable message format |
| **32-3** | Change roundtrip AC to expect scaffold findings until user fills in real content |
| **32-4** | No change |

## Handoff

**Scope: Minor** — all changes are pre-development AC refinements applied directly to the epic file.

**File modified:** `_bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md`

**Status:** Approved and applied on 2026-03-23.
