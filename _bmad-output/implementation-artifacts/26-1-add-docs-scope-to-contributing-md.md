# Story 26.1: Add `docs` Scope to CONTRIBUTING.md

Status: done
Branch: `feat/docs-26-1-add-docs-scope`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/209

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **docvet contributor**,
I want `docs` listed as a valid commit scope in CONTRIBUTING.md,
so that documentation-only commits follow the same conventions as code commits.

## Acceptance Criteria

1. **Given** the commit conventions section in CONTRIBUTING.md **When** updated **Then** `docs` appears in the list of valid scopes
2. **Given** the updated CONTRIBUTING.md **When** a contributor reads the conventions **Then** usage examples show `docs` scope (e.g., `docs(rules): add missing-raises reference page`)

## Tasks / Subtasks

- [x] Task 1: Add `docs` to scope list in CONTRIBUTING.md (AC: 1)
  - [x] 1.1: Update `**Scopes:**` line at CONTRIBUTING.md:130 to include `docs`
- [x] Task 2: Add usage example showing `docs` scope (AC: 2)
  - [x] 2.1: Add a `docs` scope example to the commit conventions section
- [x] Task 3: Update scope list in related files for consistency (AC: 1)
  - [x] 3.1: Update `CLAUDE.md:156` scope list to include `docs`
  - [x] 3.2: Update `docs/development-guide.md:193` scope list to include `docs`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: verified `docs` appears in CONTRIBUTING.md:130, CLAUDE.md:156, development-guide.md:193 | PASS |
| 2 | Manual: verified `docs(rules): add missing-raises reference page` example at CONTRIBUTING.md:137 | PASS |

Note: This is a docs-only story — no automated tests needed. Quality gate is `mkdocs build --strict` succeeding (if docs site pages are touched).

## Dev Notes

- **Scope:** This is a trivial documentation edit. Three files need the same change (adding `docs` to the scope list):
  1. `CONTRIBUTING.md:130` — primary target per issue #191
  2. `CLAUDE.md:156` — must stay in sync with CONTRIBUTING.md
  3. `docs/development-guide.md:193` — must stay in sync with CONTRIBUTING.md
- **Source:** Deferred finding from Epic 22 story 22.4 code review (MEDIUM severity). Carried through retros until Epic 26 planning.
- **No code changes, no new tests, no new dependencies**
- The `docs` scope is already actively used in the project (e.g., `docs(rules): ...`, `docs(site): ...`) — this just documents the convention

### Project Structure Notes

- No structural changes — editing 3 existing files
- All 3 files are in the repo root or docs directory, already tracked

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 26.1]
- [Source: GitHub Issue #191]
- [Source: Epic 22 story 22.4 code review — deferred MEDIUM finding]
- [Source: Epic 22 retrospective — tech debt item]

### Documentation Impact

- Pages: CONTRIBUTING.md, docs/development-guide.md
- Nature of update: Add `docs` to the list of valid commit scopes in both files; add a usage example showing `docs` scope in CONTRIBUTING.md

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all 971 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100%
- [x] `mkdocs build --strict` — docs site builds cleanly (docs-only story gate)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — trivial docs-only edit, no debugging needed.

### Completion Notes List

- Added `docs` to the scope list in all 3 files (CONTRIBUTING.md, CLAUDE.md, docs/development-guide.md)
- Added an **Examples** block to CONTRIBUTING.md commit conventions section showing `feat`, `fix`, and `docs` scope usage
- All 6 quality gates pass, 971 tests with zero regressions

### Change Log

- 2026-02-28: Added `docs` scope to commit conventions in CONTRIBUTING.md, CLAUDE.md, and docs/development-guide.md. Added usage examples to CONTRIBUTING.md.
- 2026-02-28: Code review — 4 findings (2M, 2L). Party mode consensus: M2 fixed (added `mkdocs build --strict` gate), M1/L1/L2 dismissed. Story approved.

### File List

- CONTRIBUTING.md (modified — added `docs` scope + examples block)
- CLAUDE.md (modified — added `docs` scope)
- docs/development-guide.md (modified — added `docs` scope)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party mode consensus)

### Outcome

Approve — 1 finding fixed, 3 dismissed by team consensus

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | AC 2 conflates `docs` type with `docs` scope — no example uses `docs` in scope position | Dismissed: AC followed as written; examples + scope list are sufficient together |
| M2 | MEDIUM | `mkdocs build --strict` not verified — docs-only story gate missing | Fixed: ran `mkdocs build --strict` (pass), added to Quality Gates section |
| L1 | LOW | Documentation Impact omits CLAUDE.md | Dismissed: CLAUDE.md is AI tooling context, already captured in File List |
| L2 | LOW | No commit examples in development-guide.md (asymmetry with CONTRIBUTING.md) | Dismissed: intentional design — onboarding page vs reference page |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
