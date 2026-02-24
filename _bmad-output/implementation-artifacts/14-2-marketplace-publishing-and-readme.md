# Story 14.2: Marketplace Publishing & README

Status: review
Branch: `feat/ci-14-2-marketplace-publishing-and-readme`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer searching for docstring tooling**,
I want to find docvet on the GitHub Actions Marketplace with clear branding and a README that immediately shows how to integrate it,
so that I can evaluate and adopt docvet without hunting through the repository.

## Acceptance Criteria

1. **Given** the `action.yml` has no `branding` block, **when** a `branding` block is added with `icon: 'shield'` and `color: 'purple'`, **then** the branding fields match GitHub's approved Feather icon set and color palette **and** the branding visually aligns with the docs site's purple theme.

2. **Given** the `action.yml` `description` is "Run docvet docstring quality checks", **when** the description is updated to a value that conveys the value proposition and keywords, **then** the description fits within the marketplace's ~120-char recommended display limit **and** includes key capability terms (completeness, freshness, rendering, coverage).

3. **Given** the README has the GitHub Action section at line ~95 (below Configuration and Pre-commit), **when** the README is restructured for marketplace visitors, **then** the GitHub Action section is reachable within one click or one scroll from the top of the README **and** the README serves both repo visitors and marketplace visitors effectively.

4. *(Maintainer action)* **Given** the release pipeline is fixed (Story 14.1) and code changes are merged to main, **when** a new GitHub release is created via release-please, **then** the "Publish this Action to the GitHub Marketplace" checkbox is enabled during release creation **and** the marketplace listing displays correct name ("docvet"), description, branding icon/color, and links to the repository README.

## Tasks / Subtasks

- [x] **Task 1: Add branding block to action.yml** (AC: 1)
  - [x] 1.1 Add `branding:` block after the `description:` field (before `inputs:`) with `icon: 'shield'` and `color: 'purple'`
  - [x] 1.2 Verify `shield` is in the approved Feather icon list and `purple` is in the approved color palette (both confirmed via research)
  - [x] 1.3 Verify action.yml still parses correctly — verified via Python string parsing (yaml module not available in dev env)

- [x] **Task 2: Update action.yml description** (AC: 2)
  - [x] 2.1 Update `description` field from "Run docvet docstring quality checks" to "Comprehensive docstring quality checks — completeness, freshness, rendering, and coverage for Python projects" (109 chars)
  - [x] 2.2 Verify the description is under 120 characters for clean marketplace card display — 109 chars confirmed

- [x] **Task 3: Restructure README for marketplace visitors** (AC: 3)
  - [x] 3.1 Add a navigation/links section near the top of the README (after the pydoclint comparison paragraph) with anchor links to Quickstart, GitHub Action, Pre-commit, Configuration, and Docs
  - [x] 3.2 Chose Option A (navigation links) per story recommendation — keeps current section order intact for repo visitors while giving marketplace visitors a one-click shortcut to GitHub Action section
  - [x] 3.3 Verified all anchor links match actual section headings via automated check; README renders standard GitHub-flavored markdown

- [ ] **Task 4: (Maintainer) Publish to GitHub Actions Marketplace** (AC: 4) *(Maintainer actions — dev agent prepares, maintainer executes)*
  - [ ] 4.1 Merge the PR to develop via squash merge (normal PR flow)
  - [ ] 4.2 *(Maintainer)* Merge develop to main using rebase and merge — CHANGELOG.md may conflict if develop→main hasn't been synced since Story 14.1; resolve by keeping develop's version
  - [ ] 4.3 *(Maintainer)* When release-please creates the release PR, merge it
  - [ ] 4.4 *(Maintainer)* During release creation, check "Publish this Action to the GitHub Marketplace" checkbox — requires 2FA enabled and Marketplace Developer Agreement accepted
  - [ ] 4.5 *(Maintainer)* Select primary category (e.g., "Code quality") from the marketplace category dropdown
  - [ ] 4.6 *(Maintainer)* Verify marketplace listing shows correct name, description, branding icon/color, and README content

## AC-to-Test Mapping

<!-- This is a config/docs story with no Python code changes. "Tests" are manual verification steps, not pytest tests. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Task 1.2-1.3: Verified `shield` in approved icons, `purple` in approved colors; action.yml parses correctly | Pass |
| 2 | Task 2.2: Description is 109 chars (under 120 limit), includes all 4 capability terms | Pass |
| 3 | Task 3.3: All 4 anchor links verified to match actual section headings; standard markdown syntax | Pass |
| 4 | Task 4.6: Verify marketplace listing after publish | Pending (maintainer) |

## Dev Notes

### Story Nature

This is a **config/docs story** — no Python source code changes in `src/`. The deliverables are `action.yml` metadata updates and `README.md` restructuring. Quality gates (ruff, pytest, docvet, interrogate) will pass trivially since no Python code is modified.

### Current State of action.yml

34 lines. Structure: `name` → `description` → `inputs` (version, args) → `runs` (composite with 3 steps: setup-python, install docvet, run docvet). No `branding` block. No `author` field. No `outputs` block (acceptable for a tool-runner action).

### Current State of README.md

151 lines. Structure:
- Lines 1-5: Badge row (5 badges: PyPI, CI, License, Python, docs-vetted)
- Line 7: `# docvet` title
- Lines 9-22: Tagline + positioning comparison table
- Lines 24-36: What It Checks (4 categories, 19 rules)
- Lines 38-56: Quickstart (install + output example)
- Lines 58-70: Configuration (`[tool.docvet]`)
- Lines 72-93: Pre-commit (`.pre-commit-config.yaml` example)
- Lines 95-122: **GitHub Action** (3 usage examples: basic, pinned, with griffe)
- Lines 124-135: Better Docstrings, Better AI (research citations)
- Lines 137-143: Badge (self-referential badge snippet)
- Lines 145-147: Used By
- Lines 149-151: License

### GitHub Actions Marketplace Requirements

- `action.yml` must be at repo root — **confirmed** (it is)
- Repository must be public — **confirmed**
- `name` must be globally unique — **verified**: "docvet" is available on marketplace (checked 2026-02-24)
- `branding` block required for third-party marketplace listing
- Publishing is a manual checkbox during GitHub release creation — requires 2FA + Marketplace Developer Agreement
- No review process by GitHub — actions are published immediately
- Floating `v1` tag already exists for action consumers

### Approved Branding Values

**Colors:** `white`, `black`, `yellow`, `blue`, `green`, `orange`, `red`, `purple`, `gray-dark`

**Icons (relevant subset):** `shield`, `check-circle`, `check-square`, `file-text`, `search`, `eye`, `clipboard`, `book`, `code`

**Chosen:** `icon: 'shield'` + `color: 'purple'` — matches docs site theme and conveys quality/protection semantics. Confirmed from party mode discussion (2026-02-24).

### Key Files to Touch

| File | Action | Notes |
|------|--------|-------|
| `action.yml` | **Edit** | Add `branding` block, update `description` |
| `README.md` | **Edit** | Add navigation links near top, potentially reorder sections |

### Critical Guardrails

- **Do NOT modify** `src/` — no Python code changes in this story
- **Do NOT modify** `.github/workflows/` — CI/release pipelines are not in scope
- **Do NOT modify** `release-please-config.json` or `.release-please-manifest.json` — release pipeline config was handled in Story 14.1
- **Do NOT add** an `outputs:` block to action.yml unless there's a clear use case — tool-runner actions don't typically declare outputs
- **Do NOT add** an `author:` field to action.yml — it's optional and the repo already identifies the author
- **Preserve** the existing badge row in README — only add to it, don't reorganize existing badges
- **Preserve** the existing GitHub Action usage examples — they're already comprehensive with 3 scenarios (basic, pinned, griffe)

### README Restructuring Strategy

The key tension: repo visitors want Quickstart first; marketplace visitors want the GitHub Action section. Two approaches:

**Option A (Navigation links):** Add a short navigation section after the tagline with anchor links to key sections. Keeps current section order intact. Marketplace visitors click one link to reach the Action section.

**Option B (Move section):** Move GitHub Action section up to immediately after Quickstart. Puts it in the natural flow for both audiences but makes the README more Action-focused.

**Recommendation:** Option A — minimal disruption, serves both audiences. The current README flow (What It Checks → Quickstart → Config → Pre-commit → GitHub Action) is logical for repo visitors. A navigation row after the tagline gives marketplace visitors a one-click shortcut.

### Previous Story Intelligence (Story 14.1)

- Config/pipeline story pattern: quality gates pass trivially, no Python code
- CHANGELOG conflict: develop→main rebase-and-merge will conflict on CHANGELOG.md — resolve by keeping develop's version
- Commit style: user prefers one file per commit with conventional commit messages
- Story 14.1 is done but Task 4 (maintainer validation of develop→main merge) is still pending — this story's Task 4 depends on that merge happening

### Project Structure Notes

- No `src/` changes — this story operates on `action.yml` and `README.md` at project root
- Branch naming: `feat/ci-14-2-marketplace-publishing-and-readme` — scope `ci` since primary changes are CI/marketplace integration
- PR targets `develop` per normal flow; marketplace publish happens after develop→main merge + release

### References

- [Source: action.yml] — current action metadata (34 lines, no branding)
- [Source: README.md] — current README structure (151 lines, GitHub Action at line 95)
- [Source: epics-adoption.md#Story 14.2] — FR-A4, FR-A5, FR-A6, FR-A7, FR-A11, FR-A12
- [Source: 14-1-release-pipeline-cleanup.md] — release pipeline fix, CHANGELOG conflict warning
- [External: GitHub Marketplace publishing docs](https://docs.github.com/actions/creating-actions/publishing-actions-in-github-marketplace)
- [External: GitHub Action metadata syntax](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions)
- [External: Feather icons for GitHub Actions](https://haya14busa.github.io/github-action-brandings/)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 743 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Tasks 1-3 completed (dev agent scope); Task 4 is maintainer-executed
- action.yml: added branding block (`shield`/`purple`) and updated description to 109-char marketplace-ready text
- README.md: added navigation links row after positioning table (Option A per story recommendation)
- yaml module not available in dev environment — used Python string parsing for action.yml verification instead
- Description is 109 chars (not 98 as estimated in story) due to em dash being counted as 1 char

### Change Log

- 2026-02-24: Implemented Tasks 1-3, ran quality gates, marked story ready for review

### File List

- `action.yml` — added `branding:` block, updated `description` field
- `README.md` — added navigation links row at line 24

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
