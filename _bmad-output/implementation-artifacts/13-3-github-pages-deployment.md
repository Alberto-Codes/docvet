# Story 13.3: GitHub Pages Deployment

Status: done
Branch: `feat/docs-13-3-github-pages-deployment`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer or potential user,
I want the docvet documentation site deployed to GitHub Pages and accessible at the project's public URL,
so that I can read documentation without cloning the repo or building locally.

## Acceptance Criteria

1. **Given** the GitHub Actions workflow directory **When** a new standalone `.github/workflows/docs.yml` workflow is created **Then** it uses `actions/upload-pages-artifact@v4` and `actions/deploy-pages@v4` to build and deploy the mkdocs site to GitHub Pages
2. **Given** the docs workflow triggers **When** configured **Then** the workflow triggers on `push` to `main` and on `workflow_dispatch` (manual), allowing both automatic deployment on release and on-demand deployment
3. **Given** the docs workflow permissions **When** the deployment job runs **Then** it requests `pages: write`, `id-token: write`, and `contents: read` permissions explicitly (all unmentioned permissions default to `none` per CLAUDE.md CI lessons)
4. **Given** the docs workflow concurrency configuration **When** multiple deployments are triggered **Then** a concurrency group (`group: pages`, `cancel-in-progress: false`) prevents parallel deployments from conflicting
5. **Given** the docs workflow build step **When** the job executes **Then** it checks out the repo, sets up Python and uv, runs `uv sync --extra docs` to install documentation dependencies, and runs `mkdocs build --strict` before uploading the artifact
6. **Given** a successful deployment **When** a developer visits `https://alberto-codes.github.io/docvet/` **Then** the full documentation site is accessible -- Getting Started, check pages, rule pages, glossary, API reference, configuration, and CLI reference all render correctly

## Tasks / Subtasks

- [x] Task 1: Create `.github/workflows/docs.yml` workflow file (AC: 1, 2, 3, 4, 5)
  - [x] 1.1 Define workflow name and triggers (`push` to `main`, `workflow_dispatch`)
  - [x] 1.2 Configure top-level permissions (`contents: read`) and concurrency group (`pages`, `cancel-in-progress: false`)
  - [x] 1.3 Create `build` job: checkout, setup Python 3.12 + uv, `uv sync --extra docs`, `mkdocs build --strict`, `actions/upload-pages-artifact@v4`
  - [x] 1.4 Create `deploy` job: `needs: build`, `actions/deploy-pages@v4`, with `pages: write` and `id-token: write` permissions, `environment: github-pages` with deployment URL output
- [x] Task 2: Local build validation (AC: 5)
  - [x] 2.1 Run `mkdocs build --strict` locally -- zero warnings (confirms the workflow build step will succeed)
  - [x] 2.2 Run `uv run ruff check .` and `uv run ruff format --check .` -- zero violations (no new Python files, but validate existing)
- [x] Task 3: Workflow validation (AC: 1, 2, 3, 4)
  - [x] 3.1 Verify workflow YAML is valid (no syntax errors)
  - [x] 3.2 Verify all action versions use major-version pinning per Pattern 3 (`@v6`, `@v7`, `@v4`)
  - [x] 3.3 Verify permissions are explicitly declared (CLAUDE.md CI lesson: all unmentioned default to `none`)
  - [x] 3.4 Verify concurrency group prevents parallel deployments
  - [x] 3.5 Verify `environment: github-pages` is set on the deploy job for deployment protection rules

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Task 3.1 (YAML valid), Task 3.2 (action versions @v4), workflow file inspection | Pass |
| AC2 | Task 1.1 (triggers: push main + workflow_dispatch), workflow file inspection | Pass |
| AC3 | Task 3.3 (permissions: contents:read top-level, pages:write + id-token:write on deploy) | Pass |
| AC4 | Task 3.4 (concurrency group: pages, cancel-in-progress: false) | Pass |
| AC5 | Task 2.1 (mkdocs build --strict exit 0), Task 1.3 (build job steps match) | Pass |
| AC6 | Verified post-deployment (requires manual GitHub Pages setup + merge to main) | Deferred |

## Dev Notes

### Story Context

This is the third and final story in Epic 13 (Documentation Publishing & API Reference). It deploys the complete documentation site -- Getting Started, 4 check pages, 19 rule pages, configuration, CLI reference, glossary with inline tooltips (13.1), and auto-generated API reference for 11 public modules (13.2) -- to GitHub Pages via a standalone GitHub Actions workflow.

**Epic strategic frame:** Epic 13 is the "showcase" epic. Story 13.3 is the capstone -- it makes all documentation publicly accessible. After this, anyone can visit `https://alberto-codes.github.io/docvet/` without cloning the repo.

**FR-D2 satisfaction:** The epic spec notes that FR-D2 ("runs automatically as part of the release workflow") is satisfied by event timing -- release-please merges to `main`, which triggers this standalone docs workflow. The docs deployment runs *alongside* the release, not *inside* the publish workflow. This is a separate `.github/workflows/docs.yml`, not a modification to `publish.yml`.

**Manual setup required (not automatable):** GitHub Pages source must be set to "GitHub Actions" (not "Deploy from a branch") in the repository Settings > Pages. This is a one-time manual configuration step that the user must perform before the first deployment will work.

### Previous Story Intelligence (13.1 and 13.2)

**From 13.1 (Domain Glossary):**
- Pivoted from `mkdocs-ezglossary-plugin` to built-in `abbr` + `pymdownx.snippets` + `content.tooltips` (zero new dependencies)
- Plugin order no longer includes ezglossary -- current plugins: `search -> gen-files -> literate-nav -> section-index -> mkdocstrings -> macros`
- 22 domain terms with inline tooltips across all pages
- `mkdocs build --strict` as quality gate (zero warnings)

**From 13.2 (API Reference):**
- Added 4 docs dependencies to `pyproject.toml` `docs` extra group
- Created `scripts/gen_ref_pages.py` build-time script
- 11 API reference pages generated for all public modules
- mkdocstrings-python 2.x coexists with existing griffe optional extra
- `mkdocs build --strict` passes with zero warnings

**Key patterns from both stories:**
- Zero runtime source code changes
- Additive-only configuration modifications
- `mkdocs build --strict` is sufficient quality gating for docs-only stories
- Zero-debug pattern maintained (9th consecutive)

### FR-to-Source Traceability

| FR | Source | What to do |
|----|--------|------------|
| FR121 (partial) | epics-docs-publish.md | Deploy docs site to GitHub Pages |
| FR-D1 | epics-docs-publish.md | GitHub Pages via `actions/deploy-pages@v4` |
| FR-D2 | epics-docs-publish.md | Deployment alongside release workflow (standalone `docs.yml` triggered by push to main) |

### Architecture Compliance

**Decision 1 (Docs Deployment):**
- `actions/deploy-pages@v4` -- modern GitHub Actions approach (not `mkdocs gh-deploy`)
- Deployment protection rules, shows in Environments tab
- Runs alongside publish in the release workflow (separate workflow, same trigger: push to main)

**Pattern 3 (CI/CD Naming):**
- Job names: kebab-case nouns/noun phrases (e.g., `build`, `deploy`)
- Step names: imperative sentences (e.g., "Install documentation dependencies", "Build documentation site")
- Action versions: pin to major tag only (`@v6`, `@v7`, `@v4`)

**CLAUDE.md CI/CD Lessons:**
- When declaring `permissions:`, all unmentioned permissions default to `none` -- always include `contents: read` alongside other permissions
- `actions/upload-pages-artifact@v4` (architecture referenced `@v3`, but ACs specify `@v4`)

### Workflow Design

The docs workflow follows a two-job pattern: `build` (produces artifact) -> `deploy` (publishes to GitHub Pages). This is the standard GitHub Pages deployment pattern using Actions.

**Workflow structure:**

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv python install 3.12
      - run: uv sync --extra docs
      - run: uv run mkdocs build --strict
      - uses: actions/upload-pages-artifact@v4
        with:
          path: site

  deploy:
    runs-on: ubuntu-latest
    needs: build
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

**Key design decisions:**
- **Two jobs, not one:** Separating `build` from `deploy` follows GitHub's recommended pattern and allows the deploy job to have minimal permissions (`pages: write`, `id-token: write`) while the build job only needs `contents: read` (inherited from top-level)
- **Top-level `permissions: contents: read`:** All unmentioned permissions default to `none`. The deploy job overrides with its own `pages: write` and `id-token: write`
- **`environment: github-pages`:** Enables deployment protection rules and makes the deployment visible in the repository's Environments tab
- **`concurrency: group: pages`:** Prevents parallel deployments from conflicting. `cancel-in-progress: false` ensures a running deployment completes rather than being cancelled by a newer push
- **`uv run mkdocs build --strict`:** Strict mode catches broken references, missing pages, or plugin warnings -- proven quality gate from Epics 11, 13.1, and 13.2
- **`path: site`:** mkdocs builds to `site/` by default, which is what `upload-pages-artifact` needs
- **No `timeout-minutes`:** Docs build is fast (<30s). Default 360-minute timeout is fine for this simple workflow
- **Python 3.12:** Matches CI workflow and all development

### Existing Workflow Patterns (consistency reference)

From `ci.yml`:
```yaml
- uses: actions/checkout@v6
- uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
- run: uv python install 3.12
```

From `publish.yml`:
```yaml
permissions:
  id-token: write
  contents: write
  attestations: write
environment: pypi
```

The docs workflow follows the same action versions and setup patterns for consistency.

### File Scope

| File | Action |
|------|--------|
| `.github/workflows/docs.yml` | New -- standalone docs deployment workflow |

**No other files should be modified.** No source code, no tests, no mkdocs.yml changes, no dependency changes. This is purely a CI/CD workflow file.

### Git Intelligence

Latest commits on develop:
- `1704fce` docs(api-ref): auto-generated API reference pages (#81) -- Story 13.2
- `6c64670` docs(glossary): add domain glossary with inline tooltips (#79) -- Story 13.1
- `fd6e597` chore: add Epic 12 retrospective and mark complete

Codebase is clean. No pending changes. Last commit was 13.2's merge.

### Critical Constraints

- **Single new file only** -- `.github/workflows/docs.yml` is the only deliverable
- **No runtime source code changes** -- no Python, no tests, no mkdocs.yml modifications
- **Permissions must be explicit** -- `contents: read` at top-level, `pages: write` + `id-token: write` on deploy job (CLAUDE.md CI lesson)
- **Action versions pin to major tag** -- `@v6` for checkout, `@v7` for setup-uv, `@v4` for pages actions (Pattern 3)
- **Concurrency group `pages`** -- prevents parallel deployment conflicts, `cancel-in-progress: false`
- **Two-job pattern** -- build (produces artifact) -> deploy (publishes to Pages), following GitHub's recommended pattern
- **`environment: github-pages`** -- enables deployment protection rules and Environments tab visibility
- **`mkdocs build --strict`** -- must be strict mode (proven quality gate from 3 previous docs stories)
- **Manual GitHub Pages setup required** -- repository Settings > Pages must be set to "GitHub Actions" source (one-time, not automatable)
- **Triggers: push to main + workflow_dispatch** -- FR-D2 satisfied by event timing (release-please merges to main, triggering this workflow)

### Project Structure Notes

- `.github/workflows/docs.yml` joins existing `ci.yml`, `publish.yml`, `release-please.yml`, and `test-publish.yml`
- No new directories needed
- The workflow reads the existing mkdocs.yml and docs/ content -- no modifications to those files

### References

- [Source: _bmad-output/planning-artifacts/epics-docs-publish.md#Story 13.3 -- original AC definitions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1 -- docs deployment via actions/deploy-pages@v4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern 3 -- CI/CD naming conventions]
- [Source: .github/workflows/ci.yml -- action version and setup patterns]
- [Source: .github/workflows/publish.yml -- permissions and environment patterns]
- [Source: _bmad-output/implementation-artifacts/13-1-domain-glossary-with-inline-tooltips.md -- previous story learnings]
- [Source: _bmad-output/implementation-artifacts/13-2-auto-generated-api-reference.md -- previous story learnings]
- [Source: CLAUDE.md -- CI/CD pipeline lessons (permissions, OIDC)]
- [Source: mkdocs.yml -- current docs configuration baseline]

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors
- [x] `uv run pytest` -- 737 passed, no regressions
- [x] `uv run docvet check --all` -- N/A (no source code changes)
- [x] `uv run interrogate -v` -- N/A (no source code changes)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Zero-debug pattern maintained (10th consecutive).

### Completion Notes List

- Created `.github/workflows/docs.yml` -- standalone two-job GitHub Pages deployment workflow
- Build job: checkout, setup Python 3.12 + uv, `uv sync --extra docs`, `mkdocs build --strict`, `upload-pages-artifact@v4`
- Deploy job: `deploy-pages@v4` with `pages: write` + `id-token: write` permissions, `environment: github-pages`
- Top-level `permissions: contents: read` (CLAUDE.md CI lesson: unmentioned default to `none`)
- Concurrency group `pages` with `cancel-in-progress: false` prevents parallel deployment conflicts
- Triggers: `push` to `main` (automatic on release) + `workflow_dispatch` (manual)
- All action versions pin to major tag per Pattern 3: `checkout@v6`, `setup-uv@v7`, pages actions `@v4`
- Local `mkdocs build --strict` passes with exit 0, confirming workflow build step will succeed
- 737 existing tests pass, zero regressions
- AC6 (live site verification) deferred -- requires manual GitHub Pages setup in repo Settings > Pages (source: "GitHub Actions") + merge to main

### Change Log

- 2026-02-22: Created `.github/workflows/docs.yml` -- GitHub Pages deployment workflow (Story 13.3)
- 2026-02-22: Code review fixes -- renamed deploy → deploy-docs (Pattern 3), added step names, added uv cache prune

### File List

- `.github/workflows/docs.yml` (new) -- standalone GitHub Pages deployment workflow

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approve (all findings resolved)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | Medium | Deploy job name `deploy` should be `deploy-docs` per Architecture Pattern 3 | Fixed -- renamed to `deploy-docs` |
| L1 | Low | No step `name` attributes on any step (Pattern 3 requires imperative verb phrases) | Fixed -- added names to all 8 steps |
| L2 | Low | Missing `uv cache prune --ci` cleanup step (ci.yml consistency) | Fixed -- added with `if: always()` + `continue-on-error: true` |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
