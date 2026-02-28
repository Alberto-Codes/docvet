# Story {{epic_num}}.{{story_num}}: {{story_title}}

Status: ready-for-dev
Branch: `feat/{{scope}}-{{epic_num}}-{{story_num}}-{{description}}`
GitHub Issue: {{github_issue_url}}

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a {{role}},
I want {{action}},
so that {{benefit}}.

## Acceptance Criteria

1. [Add acceptance criteria from epics/PRD]

## Tasks / Subtasks

- [ ] Task 1 (AC: #)
  - [ ] Subtask 1.1
- [ ] Task 2 (AC: #)
  - [ ] Subtask 2.1

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- Cite all technical details with source paths and sections, e.g. [Source: docs/<file>.md#Section]

### Documentation Impact

<!-- REQUIRED: Every story must identify affected docs pages or explicitly acknowledge "None". Do NOT leave blank or use vague language like "update docs if needed". -->

- Pages: [REQUIRED — use concrete paths from the decision tree below, or "None — no user-facing changes"]
- Nature of update: [REQUIRED — describe the specific update per page, or "N/A"]

<!-- Decision tree for docs page identification (source of truth: instructions.xml step 5, documentation_impact_assessment):
  CLI changes (flags, subcommands) → docs/site/cli-reference.md
  Config key changes ([tool.docvet]) → docs/site/configuration.md
  Check behavior changes → docs/site/checks/{check_name}.md
  Rule changes → docs/rules/{rule_name}.md
  Public API surface changes → docs/site/api-reference.md
  User workflow changes (install, pre-commit, CI) → README.md and/or relevant docs/site/ page
  Internal-only (refactor, test, internal CI config, BMAD) → "None — no user-facing changes"
-->

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [ ] `uv run ruff check .` — zero lint violations
- [ ] `uv run ruff format --check .` — zero format issues
- [ ] `uv run ty check` — zero type errors
- [ ] `uv run pytest` — all tests pass, no regressions
- [ ] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [ ] `uv run interrogate -v` — docstring coverage ≥ 95%

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

### File List

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
