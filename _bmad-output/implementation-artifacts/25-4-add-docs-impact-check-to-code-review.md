# Story 25.4: Add Docs-Impact Check to Code Review

Status: done
Branch: `feat/bmad-25-4-docs-impact-code-review`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/202

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **code reviewer using the BMAD code review workflow**,
I want the workflow to flag when source files changed without corresponding docs updates,
so that documentation drift is caught during review, not after shipping.

## Acceptance Criteria

1. **Given** the BMAD code-review workflow (`_bmad/bmm/workflows/4-implementation/code-review/`)
   **When** source files in `src/docvet/` are modified in the PR
   **Then** the workflow includes a blocking check: "Were corresponding docs pages updated?"

2. **Given** a PR that modifies user-facing behavior without touching docs
   **When** the code review runs
   **Then** the docs-impact gap is flagged as a finding (not just a suggestion)

3. **Given** a PR that modifies only tests, CI, or internal tooling
   **When** the code review runs
   **Then** no docs-impact finding is produced (internal changes don't require docs updates)

## Tasks / Subtasks

- [x] Task 1: Strengthen Documentation Impact Verification in code-review instructions.xml (AC: 1, 2, 3)
  - [x] 1.1: Replace the existing advisory `<action>` (lines 88-94) with a structured check that uses the same decision tree from create-story instructions.xml to classify changed files
  - [x] 1.2: Add file-classification logic: if any changed file matches `src/docvet/cli.py`, `src/docvet/config.py`, `src/docvet/checks/*.py`, or other user-facing patterns → require docs verification
  - [x] 1.3: Add explicit exclusion list for non-user-facing paths: `tests/`, `.github/`, `_bmad/`, `_bmad-output/`, `.claude/`, internal CI config — these should NOT trigger docs-impact findings
  - [x] 1.4: Ensure docs-impact gaps are flagged as findings (MEDIUM severity minimum) with actionable message, not just noted as an observation
- [x] Task 2: Add cross-reference to story's Documentation Impact section (AC: 1, 2)
  - [x] 2.1: The check should reference the story file's Documentation Impact section to compare "pages listed" vs "pages actually changed in File List"
  - [x] 2.2: If Documentation Impact says "None" but changed files include user-facing source code, flag as HIGH finding (story classification was wrong)
- [x] Task 3: Verify workflow produces correct findings (AC: 1, 2, 3)
  - [x] 3.1: Mentally trace for a user-facing PR (e.g., "add new config key to enrichment") — confirm docs-impact gap is flagged as a finding
  - [x] 3.2: Mentally trace for an internal-only PR (e.g., "standardize pytestmark") — confirm no docs-impact finding is produced
  - [x] 3.3: Mentally trace for a PR with correct docs updates — confirm no finding is produced

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Mental trace: user-facing PR (config key change) → Step A classifies `src/docvet/config.py` as user-facing, Step C CASE 2/3 produces finding. Blocking check present in workflow Step 3. Happy path: PR lists `docs/site/configuration.md` AND updates it → CASE 4, no finding. | PASS |
| 2 | Mental trace: PR modifying `src/docvet/checks/enrichment.py` without docs → Step C CASE 2 produces HIGH finding: "Documentation Impact says 'None' but PR modifies user-facing files" | PASS |
| 3 | Mental trace: internal-only PR (pytestmark standardization, all files in `tests/`) → Step A classifies all as INTERNAL, Step C CASE 5 produces no finding | PASS |

## Dev Notes

- **This is a BMAD workflow-only story** — no Python source code, no new tests. Deliverables are edits to the BMAD code-review workflow configuration file.
- **Source**: Epic 22 retrospective action item 2 — features shipped without corresponding docs-site updates.
- **Companion to Story 25.3**: Story 25.3 enforced docs identification at story *creation* time. This story enforces docs verification at code *review* time. Together they form a two-gate system: plan docs up front (25.3), verify docs were actually updated (25.4).
- **Pattern from 25.3**: The create-story workflow was strengthened by replacing advisory `<action>` tags with gating `<template-output>` tags and adding a decision tree. The code-review workflow needs a parallel improvement — not `<template-output>` (that's for document generation), but a structured check that produces findings.

### Current State (Code-Review instructions.xml)

**Lines 88-94** currently have this Documentation Impact Verification:
```xml
<!-- Documentation Impact Verification -->
<action>Check story's Dev Notes → Documentation Impact section:
  1. If pages are listed: verify each listed page was actually updated in the File List
  2. If "None": verify the story truly has no user-facing doc impact (config changes, new rules, CLI behavior)
  3. If section is missing or empty: flag as MEDIUM finding (process gap)
  4. If pages listed but not updated: flag as HIGH finding (documentation drift)
</action>
```

This is already structured with 4 checks, but it's a single `<action>` tag embedded inside the broader "Execute adversarial review" step 3. The fix: expand it with the decision tree for file classification so the reviewer knows *which* docs to expect based on changed files, and ensure gaps produce actual findings in the findings table.

### Decision Tree (from create-story instructions.xml step 5)

The same classification logic should be used here:
1. `src/docvet/cli.py` or CLI flags → `docs/site/cli-reference.md`
2. Config keys in `[tool.docvet]` → `docs/site/configuration.md`
3. Check behavior changes → `docs/site/checks/{check_name}.md`
4. Rule changes → `docs/site/rules/{rule_name}.md`
5. Public API surface → `reference/` (auto-generated)
6. User workflow changes → `README.md` and/or relevant `docs/site/` page

Non-user-facing paths (no docs required): `tests/`, `.github/`, `_bmad/`, `_bmad-output/`, `.claude/`, `pyproject.toml` (unless config key changes), internal CI

### What NOT to Change

- Do NOT modify the create-story workflow — that's Story 25.3's scope (already done)
- Do NOT add CI automation — that's Story 25.5's scope (spike)
- Do NOT touch any Python source files or test files
- Do NOT change the code-review workflow.yaml — only modify instructions.xml

### Files to Modify

1. **`_bmad/bmm/workflows/4-implementation/code-review/instructions.xml`** — Strengthen Documentation Impact Verification with decision tree and finding-level enforcement

### Project Structure Notes

- BMAD code-review workflow files are in `_bmad/bmm/workflows/4-implementation/code-review/`
- The `instructions.xml` uses the same tag semantics as create-story: `<action>` (advisory), `<check>` (conditional)
- The code-review workflow is an action-workflow (template: false) — it produces findings, not documents
- Changed files are discovered via `git status --porcelain`, `git diff --name-only`, and `git diff --cached --name-only` in step 1

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 25, Story 25.4]
- [Source: _bmad/bmm/workflows/4-implementation/code-review/instructions.xml:88-94 — current Documentation Impact Verification]
- [Source: _bmad/bmm/workflows/4-implementation/create-story/instructions.xml:328-363 — decision tree (source of truth for classification)]
- [Source: _bmad-output/implementation-artifacts/25-3-enforce-docs-updates-in-story-creation.md — companion story, pattern reference]
- [Source: _bmad-output/implementation-artifacts/epic-22-retro-2026-02-27.md — action item 2 (origin of this requirement)]
- [Source: GitHub Issue #188 — add docs-impact check to code review workflow]

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A — this story modifies BMAD workflow configuration, not docvet user-facing docs

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

- Replaced single advisory `<action>` tag (lines 88-94) with enhanced 3-step structured check (Steps A, B, C)
- Step A: File classification using 6 user-facing patterns + internal exclusion list (mirrors create-story decision tree)
- Step B: Extract story's Documentation Impact section (Pages + Nature of update fields)
- Step C: Cross-reference with 6 cases: missing section (MEDIUM), wrong "None" (HIGH), listed but not updated (HIGH), correctly delivered (no finding), correctly internal (no finding), unlisted expected pages (MEDIUM)
- Added XML comment header identifying enhancement origin: `(Enhanced — Story 25.4)`
- Mental traces verified all 3 AC scenarios: user-facing gap flagged, internal-only PR clean, correct docs PR clean
- All 6 quality gates pass: ruff, format, ty, pytest (971 passed), docvet, interrogate (100%)
- No Python source code or test files modified — BMAD workflow config only

### Change Log

- 2026-02-28: Enhanced Documentation Impact Verification in code-review instructions.xml with 3-step structured check (file classification, story cross-reference, finding production)
- 2026-02-28: Code review — fixed 3 findings: CASE 3 "File List" ambiguity (M1), Pattern 5 wording precision (L1), AC-to-Test CASE 4 trace (L2)

### File List

- `_bmad/bmm/workflows/4-implementation/code-review/instructions.xml` — Enhanced Documentation Impact Verification (replaced lines 88-94 with 3-step structured check: Steps A, B, C)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approve (all findings fixed)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | CASE 3 references ambiguous "File List" — could produce false HIGH findings when docs updated but not in story File List | Fixed: changed to "comprehensive review list (File List + git changes)" |
| L1 | LOW | Pattern 5 (API surface) wording less precise than create-story source of truth — could cause reviewer to look for reference/ file changes instead of source docstring updates | Fixed: added "update source code docstrings, not docs files directly" clarification |
| L2 | LOW | AC-to-Test table lacks explicit happy-path trace for CASE 4 (docs planned and delivered) | Fixed: added CASE 4 happy-path trace to AC 1 row |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
