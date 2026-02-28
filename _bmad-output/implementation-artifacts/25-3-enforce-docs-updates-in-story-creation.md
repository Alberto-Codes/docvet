# Story 25.3: Enforce Docs Updates in Story Creation

Status: done
Branch: `feat/bmad-25-3-enforce-docs-updates`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/200

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **docvet contributor using the BMAD story creation workflow**,
I want the workflow to require identification of affected docs pages in acceptance criteria,
so that documentation updates are planned alongside code changes, not forgotten after.

## Acceptance Criteria

1. **Given** the BMAD create-story workflow (`_bmad/bmm/workflows/4-implementation/create-story/`)
   **When** a story touches user-facing behavior
   **Then** the workflow requires listing specific docs pages to update (e.g., "update `docs/site/cli.md`") as concrete ACs

2. **Given** a story that does NOT touch user-facing behavior (e.g., internal refactor, test-only)
   **When** the workflow processes the story
   **Then** the docs requirement is acknowledged as "N/A — no user-facing changes" rather than silently skipped

3. **Given** the updated workflow
   **When** a contributor runs `/bmad-bmm-create-story`
   **Then** the docs-page identification step appears as an explicit gate, not a suggestion

## Tasks / Subtasks

- [x] Task 1: Strengthen Documentation Impact step in instructions.xml (AC: 1, 2, 3)
  - [x] 1.1: Promote the existing "Documentation Impact Assessment" action in step 5 from an advisory action to a gating `<template-output>` section that requires explicit docs-page identification or N/A acknowledgment
  - [x] 1.2: Add classification logic: if story touches `src/docvet/` files or changes CLI behavior or config keys, require concrete page names; otherwise allow "None — no user-facing changes"
  - [x] 1.3: Add examples of correct docs impact entries (concrete page names, not vague "update docs if needed")
- [x] Task 2: Enhance template.md Documentation Impact section (AC: 1, 2)
  - [x] 2.1: Upgrade the Documentation Impact placeholder from a suggestion to a required field with clearer guidance
  - [x] 2.2: Add inline examples: `docs/site/configuration.md` for config changes, `docs/site/checks/enrichment.md` for check behavior, `docs/site/cli-reference.md` for CLI changes, "None" for internal-only stories
- [x] Task 3: Verify workflow produces correct output (AC: 1, 2, 3)
  - [x] 3.1: Mentally trace the updated workflow for a user-facing story (e.g., "add new config key") — confirm it gates on specific page names
  - [x] 3.2: Mentally trace for a non-user-facing story (e.g., "standardize pytestmark") — confirm it produces "None" acknowledgment

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Verified: instructions.xml `<template-output>` decision tree requires concrete page names for user-facing stories (CLI, config, checks, rules, API, workflow) | PASS |
| 2 | Verified: instructions.xml decision tree bottom clause produces "None — no user-facing changes" for internal stories; template.md includes "None" guidance | PASS |
| 3 | Verified: `<template-output>` tag (lines 328-356) replaces `<action>` — workflow engine saves content and pauses for user review (gating, not advisory) | PASS |

## Dev Notes

- **This is a BMAD workflow-only story** — no Python source code, no new tests. Deliverables are edits to BMAD workflow configuration files.
- **Source**: Epic 22 retrospective action item 1 — features shipped without corresponding docs-site updates (ironic for a documentation quality tool).
- **Pattern from 25.1/25.2**: Previous stories in this epic were also convention/config/process changes. Clear decision documentation and honest deferred-item tracking are essential.
- **Key insight from 25.1 code review (M1)**: Enforcement at the process level (workflow gates) is valuable but has limits — LLM agents may still skip. The gate makes it harder to skip, not impossible.

### Files to Modify

1. **`_bmad/bmm/workflows/4-implementation/create-story/instructions.xml`** — Promote Documentation Impact from advisory action to gating `<template-output>` step
2. **`_bmad/bmm/workflows/4-implementation/create-story/template.md`** — Enhance Documentation Impact section with clearer guidance and examples

### Current State (Verified 2026-02-28)

**instructions.xml step 5** has this action (lines ~328-336):
```xml
<action>Identify documentation pages affected by this story's changes:
  - Configuration reference (docs/site/configuration.md) if new config keys or behavior changes
  - Check pages (docs/site/checks/*.md) if check behavior changes
  - Rule pages (docs/rules/*.md) if new rules or rule behavior changes
  - API reference if public API surface changes
  - README if user-facing workflow changes
  - Set to "None" if story is purely internal with no user-facing impact
</action>
<action>Fill the Documentation Impact section in Dev Notes with affected pages and nature of updates needed</action>
```

This is an `<action>` tag (advisory) — the LLM can and does skip it. The fix: wrap it as a `<template-output>` tag so the workflow engine saves progress and pauses for user review.

**template.md** has this section:
```markdown
### Documentation Impact
<!-- SM: List documentation pages that may need updating based on this story's changes. Use "None" if no docs are affected. -->
- Pages: [e.g., docs/site/configuration.md, docs/site/checks/enrichment.md, or "None"]
- Nature of update: [e.g., "Add new config key to reference table", "Update CLI examples", or "N/A"]
```

This is a placeholder with examples — adequate but could be strengthened with explicit required/optional language.

### What NOT to Change

- Do NOT modify the code-review workflow (`instructions.xml` for code-review) — that's Story 25.4's scope
- Do NOT add CI automation for docs-freshness — that's Story 25.5's scope (spike)
- Do NOT touch any Python source files or test files

### Project Structure Notes

- BMAD workflow files are in `_bmad/bmm/workflows/4-implementation/create-story/`
- The `instructions.xml` uses XML tags defined in `_bmad/core/tasks/workflow.xml`: `<action>` (advisory), `<template-output>` (gating checkpoint), `<check>` (conditional)
- The `template.md` is written to the output file at initialization and updated section-by-section via `<template-output>` tags

### References

- [Source: GitHub Issue #187] — enforce docs-site updates in story creation Definition of Done
- [Source: _bmad-output/implementation-artifacts/epic-22-retro-2026-02-27.md] — action item 1 (origin of this requirement)
- [Source: _bmad/bmm/workflows/4-implementation/create-story/instructions.xml:328-336] — current Documentation Impact actions
- [Source: _bmad/bmm/workflows/4-implementation/create-story/template.md:49-53] — current Documentation Impact template section
- [Source: _bmad/core/tasks/workflow.xml:70-92] — workflow engine tag semantics (`<template-output>` = gating save point)
- [Source: _bmad/bmm/workflows/4-implementation/code-review/instructions.xml:88-94] — existing Documentation Impact Verification in code-review workflow (pattern to mirror)

### Documentation Impact

- Pages: None — this story modifies BMAD workflow configuration files, not docvet user-facing docs
- Nature of update: N/A — no docvet behavior changes

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 971 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% (>= 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug sessions required. BMAD workflow-only story with zero implementation issues.

### Completion Notes List

- Replaced advisory `<action>` tags (lines 328-336) with gating `<template-output>` tag in instructions.xml
- Added decision tree with 6 classification branches (CLI, config, checks, rules, API, workflow) plus "None" fallback
- Added correct/incorrect examples to prevent vague entries like "update docs if needed"
- Upgraded template.md Documentation Impact from suggestion to REQUIRED field
- Added decision tree as HTML comment reference in template.md
- Mental trace verified: user-facing story gates on concrete page names, internal story produces "None" acknowledgment

### Change Log

- 2026-02-28: Replaced `<action>` with `<template-output>` in instructions.xml step 5 (Task 1)
- 2026-02-28: Enhanced template.md Documentation Impact with REQUIRED markers and decision tree (Task 2)
- 2026-02-28: Verified workflow traces for both user-facing and internal stories (Task 3)
- 2026-02-28: Code review — 5 findings (3M, 2L), 4 fixed, 1 accepted as-is (L2)

### File List

- `_bmad/bmm/workflows/4-implementation/create-story/instructions.xml` — Promoted Documentation Impact from advisory `<action>` to gating `<template-output>` with decision tree
- `_bmad/bmm/workflows/4-implementation/create-story/template.md` — Enhanced Documentation Impact section with REQUIRED markers and decision tree reference
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Story status updated (backlog → done)
- `_bmad-output/implementation-artifacts/25-3-enforce-docs-updates-in-story-creation.md` — Story file updates

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approved with minor fixes (all applied)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | Medium→Low | sprint-status.yaml missing from File List | Added to File List |
| M2 | Medium | Decision tree CI ambiguity — "CI" in both branch 6 and None clause | Added "internal" qualifier to None clause in both files |
| M3 | Medium | Two copies of decision tree (divergence risk) | Added source-of-truth comment in template.md pointing to instructions.xml |
| L1 | Low | Branch 6 text mismatch — template.md missing "and/or relevant docs/site/ page" | Synced template.md with instructions.xml |
| L2 | Low | Sprint status transition skipped (backlog → review) | Accepted — process limitation for BMAD-only stories |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
