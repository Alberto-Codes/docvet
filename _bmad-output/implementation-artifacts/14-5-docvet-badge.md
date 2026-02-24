# Story 14.5: Docvet Badge

Status: review
Branch: `feat/docs-14-5-docvet-badge`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **project maintainer who uses docvet**,
I want a shields.io badge I can add to my README,
so that I can signal docstring quality to visitors and advertise docvet to the broader Python community.

## Acceptance Criteria

1. **Given** the README has an existing badge row (line 5) with a "docs vetted | docvet" badge in blue, **when** the badge color is updated to purple, **then** the badge renders correctly at the shields.io URL with purple styling matching the marketplace branding (`color: 'purple'` in action.yml) **and** the badge links to the docvet repository (or marketplace listing if available).

2. **Given** the README badge row exists (PyPI version, CI status, license, Python versions, docs vetted), **when** the docvet badge is verified in the badge row, **then** it appears alongside existing badges with consistent sizing and spacing.

3. **Given** adopters want to add the badge to their own projects, **when** they read the Badge section in the README (line ~139), **then** a copy-paste markdown snippet is provided with the updated purple shields.io URL **and** the snippet includes a link target to the docvet repository.

4. **Given** the docs site has a badge row in `docs/site/index.md` (lines 7-10), **when** the "docs vetted" badge is optionally added to the docs site badge row, **then** it renders consistently with the other badges and uses the same purple URL.

## Tasks / Subtasks

- [x] **Task 1: Update badge color from blue to purple** (AC: 1, 2)
  - [x] 1.1 Change badge URL in README line 5 from `-blue)` to `-purple)` (shields.io named color)
  - [x] 1.2 Verify badge renders correctly via shields.io URL

- [x] **Task 2: Update Badge section copy-paste snippet** (AC: 3)
  - [x] 2.1 Update the markdown snippet in the Badge section (line ~143) to use purple instead of blue
  - [x] 2.2 Ensure snippet link target is consistent with the badge row link

- [x] **Task 3: Add badge to docs site** (AC: 4)
  - [x] 3.1 Add "docs vetted" purple badge to `docs/site/index.md` badge row (after existing badges)

- [x] **Task 4: Validate** (AC: 1, 2, 3, 4)
  - [x] 4.1 `mkdocs build --strict` — zero warnings (built in 1.66s)
  - [x] 4.2 Visual verification of badge rendering (shields.io URL accessible)

## AC-to-Test Mapping

<!-- This is a docs story. "Tests" are build validation and manual verification, not pytest tests. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Task 1.1: README badge URL changed to `-purple)`; Task 4.2: shields.io URL renders correctly | Pass |
| 2 | Task 1.1: Badge remains in badge row alongside PyPI, CI, License, Python badges | Pass |
| 3 | Task 2.1: Badge section snippet updated to purple; link target matches badge row | Pass |
| 4 | Task 3.1: Purple badge added to docs/site/index.md; Task 4.1: `mkdocs build --strict` passes | Pass |

## Dev Notes

### Story Nature

This is a **docs-only story** — only markdown files are modified. No Python source code in `src/` is changed. Quality gates (ruff, pytest, docvet, interrogate) will pass trivially.

### Current Badge State

**README line 5** (current — blue):
```markdown
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-blue)](https://github.com/Alberto-Codes/docvet)
```

**README Badge section (lines 139-145)** (current — blue):
```markdown
## Badge

Add a badge to your project to show your docs are vetted:

```markdown
[![docs vetted | docvet](https://img.shields.io/badge/docs%20vetted-docvet-blue)](https://github.com/Alberto-Codes/docvet)
```

**Docs site `index.md` badge row (lines 7-10)** — does NOT include the "docs vetted" badge:
```markdown
[![PyPI version](https://img.shields.io/pypi/v/docvet)](https://pypi.org/project/docvet/)
[![Python versions](https://img.shields.io/pypi/pyversions/docvet)](https://pypi.org/project/docvet/)
[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/docvet/ci.yml?branch=develop&label=CI)](https://github.com/Alberto-Codes/docvet/actions)
[![License](https://img.shields.io/pypi/l/docvet)](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE)
```

### Target Badge URL

Change from `blue` to `purple` (shields.io named color):
```
https://img.shields.io/badge/docs%20vetted-docvet-purple
```

This matches the GitHub Action marketplace branding (`color: 'purple'` in `action.yml`).

### Branding Consistency

- **action.yml**: `color: 'purple'` — GitHub marketplace branding
- **Docs site theme**: Deep Indigo (#16213e) + Gold (#ffd700) — the purple marketplace color is the closest GitHub-approved match to deep indigo
- **shields.io `purple`**: renders as `#9f36b7` — a standard purple that aligns with the marketplace branding intent

### Badge Row Discrepancy

The README badge row line 5 uses `docs vetted` as the alt text, but the Badge section snippet uses `docs vetted | docvet`. The badge row badge should match the snippet format. Decide: keep as-is (slight difference between own badge row and adopter snippet is fine) or align them.

### Key Files to Touch

| File | Action | Notes |
|------|--------|-------|
| `README.md` | **Edit** | Line 5: change `blue` → `purple` in badge URL |
| `README.md` | **Edit** | Line ~143-144: change `blue` → `purple` in Badge section snippet |
| `docs/site/index.md` | **Edit** | Add "docs vetted" purple badge to badge row |

### Critical Guardrails

- **Do NOT modify** `src/` — no Python source code changes
- **Do NOT modify** `action.yml`, `.pre-commit-hooks.yaml`, or `.github/workflows/`
- **Do NOT modify** `mkdocs.yml` — nav is unchanged
- **Changes are minimal**: just color values in badge URLs + one new badge in docs site
- **Follow** existing badge format patterns (README badge row style, docs site badge row style)

### Previous Story Intelligence (Story 14.4)

- Docs-only story pattern: quality gates pass trivially, no Python code
- Commit style: user prefers one file per commit with conventional commit messages
- `mkdocs build --strict` requires `uv sync --extra docs` (docs deps not in dev group)
- Story 14.4 is done; this story can proceed independently

### Project Structure Notes

- README at project root: `README.md`
- Docs pages live in `docs/site/` — badge row in `docs/site/index.md`
- Branch naming: `feat/docs-14-5-docvet-badge`
- PR targets `develop` per normal flow

### References

- [Source: README.md#line-5] — current badge row with blue "docs vetted" badge
- [Source: README.md#lines-139-145] — Badge section with copy-paste snippet
- [Source: docs/site/index.md#lines-7-10] — docs site badge row (no "docs vetted" badge)
- [Source: action.yml#lines-3-5] — marketplace branding: `icon: 'shield'`, `color: 'purple'`
- [Source: epics-adoption.md#Story-14.5] — FR-A17, FR-A18

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 743 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (exit code 0 with all 4 checks in fail-on)
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Changed badge color from `blue` to `purple` in README badge row (line 5) and Badge section snippet (line ~144)
- Added "docs vetted" purple badge to docs site `index.md` badge row after License badge
- `mkdocs build --strict` passes with zero warnings (1.66s build)
- All 6 quality gates pass

### Change Log

- 2026-02-24: Implemented Tasks 1-4, ran quality gates, marked story ready for review

### File List

- `README.md` — badge color changed from blue to purple (badge row + Badge section snippet)
- `docs/site/index.md` — added "docs vetted" purple badge to badge row

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
