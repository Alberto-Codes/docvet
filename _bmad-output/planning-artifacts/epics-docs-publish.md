---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/implementation-artifacts/epic-11-retro-2026-02-22.md'
---

# docvet - Epic Breakdown (Documentation Publishing & API Reference)

## Overview

This document provides the epic and story breakdown for docvet's **Documentation Publishing & API Reference** phase — deploying the docs site to GitHub Pages and adding auto-generated API reference pages. The handwritten documentation site (Getting Started, check pages, configuration, CLI reference, 19 rule pages) is complete from Epic 11. This phase makes it publicly accessible and adds auto-generated API docs from source code.

## Requirements Inventory

### Functional Requirements

- **FR121** (partial): The system can serve a documentation site built with mkdocs-material — site is built but not yet publicly deployed/accessible
- **FR-D1:** The documentation site is deployed to GitHub Pages via `actions/deploy-pages@v4`, accessible at the project's GitHub Pages URL
- **FR-D2:** The docs deployment runs automatically as part of the release workflow (alongside PyPI publish), or can be triggered manually
- **FR-D3:** The documentation site includes auto-generated API reference pages for all public modules using mkdocstrings, rendering docstrings and `__all__` exports from `src/docvet/`
- **FR-D4:** A `scripts/gen_ref_pages.py` script walks `src/docvet/**/*.py` and generates mkdocstrings `::: docvet.module` directives at build time via mkdocs-gen-files
- **FR-D5:** The auto-generated API reference navigation is produced by mkdocs-literate-nav from a generated `SUMMARY.md` file
- **FR-D6:** mkdocstrings renders full API docs from source docstrings using Google-style parser with `paths: [src]` configuration
- **FR-D7:** The documentation site includes a glossary page defining ~20 docvet domain terms (e.g., "Google-style docstring," "symbol," "required/recommended," "six-layer model," "freshness drift," "griffe") with inline tooltips on rule pages and guide pages via mkdocs-ezglossary-plugin

### NonFunctional Requirements

- **NFR57:** The documentation site loads in under 3 seconds, includes client-side search, and renders without layout breaks on viewports >= 320px wide through 1920px
- **NFR58:** Every CLI flag documented in the docs site matches the actual `docvet --help` output — no drift between documentation and implementation
- **NFR64:** The public API surface (`Finding` dataclass, check functions, CLI command names, CLI option names) is stable for v1 — no breaking changes within the v1.x lifecycle
- **NFR-D1:** Auto-generated API reference produces zero drift by construction — docs ARE the code (mkdocstrings reads source directly)
- **NFR-D2:** The docs site builds successfully with `mkdocs build --strict` after adding all new plugins and API reference pages

### Additional Requirements

**From Architecture Decision 2 (Documentation Site Architecture):**
- mkdocstrings[python] for API reference generation from docstrings
- mkdocs-gen-files for auto-generating reference page stubs at build time
- mkdocs-literate-nav for generated navigation from SUMMARY.md
- mkdocs-section-index for section index pages
- Plugin ordering per Pattern 6: search → gen-files → literate-nav → section-index → mkdocstrings → macros
- `scripts/gen_ref_pages.py` (~30 lines) walks `src/docvet/**/*.py`
- API reference under `docs/site/reference/` is fully auto-generated — never hand-edit

**From Architecture Docs Deployment:**
- `actions/deploy-pages@v4` (modern GitHub Actions approach, not `mkdocs gh-deploy`)
- Deployment protection rules, shows in Environments tab
- Can run alongside publish in the release workflow or as standalone workflow

**From Architecture Deferred Items (now in scope):**
- ezglossary for domain terms (~20 terms) — INCLUDED per user decision
- `ignore_case: true`, `plurals: en` for automatic matching
- Tooltips appear on rule pages, getting started, and concepts pages
- Single markdown file (`docs/site/glossary.md`), ~20 terms

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR121 (partial) | Epic 13 | Deploy docs site to GitHub Pages |
| FR-D1 | Epic 13 | GitHub Pages via actions/deploy-pages@v4 |
| FR-D2 | Epic 13 | Deployment in release workflow or manual trigger |
| FR-D3 | Epic 13 | Auto-generated API reference via mkdocstrings |
| FR-D4 | Epic 13 | gen_ref_pages.py script via mkdocs-gen-files |
| FR-D5 | Epic 13 | literate-nav from generated SUMMARY.md |
| FR-D6 | Epic 13 | mkdocstrings Google-style parser config |
| FR-D7 | Epic 13 | Glossary with ezglossary (~20 terms) |

## Epic List

### Epic 13: Documentation Publishing & API Reference

A developer can visit the publicly hosted docs site, browse auto-generated API reference for all public modules, and understand docvet-specific terminology through inline glossary tooltips — the documentation site is complete and live.

**FRs covered:** FR121 (partial), FR-D1, FR-D2, FR-D3, FR-D4, FR-D5, FR-D6, FR-D7
**NFRs addressed:** NFR57, NFR58, NFR64, NFR-D1, NFR-D2
**Depends on:** Epic 11 (docs site built), Epic 9 (`__all__` exports for mkdocstrings)

**Recommended Story Order:** 13.1 → 13.2 → 13.3. Glossary first (smallest scope, improves existing pages, inserts ezglossary at correct Pattern 6 position). API reference second (heaviest lift, extends plugin stack sequentially). Deployment last (deploys all content together).

| Story | Theme | FRs Covered | Scope |
|-------|-------|-------------|-------|
| 13.1 | Domain Glossary | FR-D7 | ezglossary plugin, ~20 terms, tooltips on existing pages |
| 13.2 | Auto-generated API Reference | FR-D3, FR-D4, FR-D5, FR-D6 | mkdocstrings + gen-files + literate-nav + section-index, gen_ref_pages.py |
| 13.3 | GitHub Pages Deployment | FR121, FR-D1, FR-D2 | deploy-pages@v4 workflow, manual + release triggers |

#### Story 13.1: Domain Glossary with Inline Tooltips

As a **developer reading docvet documentation**,
I want **domain-specific terms (like "six-layer model," "freshness drift," "symbol") to show inline tooltip definitions when I hover over them**,
So that **I can understand docvet terminology without leaving the page I'm reading**.

**Acceptance Criteria:**

**Given** the docs optional dependency group in `pyproject.toml`
**When** a developer runs `uv sync --extra docs`
**Then** `mkdocs-ezglossary-plugin` is installed alongside existing docs dependencies

**Given** the `mkdocs.yml` plugins section (currently `search` and `macros`)
**When** the ezglossary plugin is configured
**Then** the resulting plugin order is `search → ezglossary → macros`, with `ignore_case: true` and `plurals: en` settings on the ezglossary entry

**Given** a new file `docs/site/glossary.md`
**When** a developer reads it
**Then** it defines at least 15 docvet domain terms using ezglossary's definition-list markdown syntax, including at minimum: "Google-style docstring," "symbol," "required," "recommended," "six-layer model," "freshness drift," "griffe," "enrichment check," "freshness check," "coverage check," "griffe compatibility check," "finding," "rule," "AST," and "docstring"

**Given** the `mkdocs.yml` nav section
**When** the glossary page is added
**Then** it appears as a top-level nav entry after "CLI Reference" (e.g., `- Glossary: glossary.md`)

**Given** existing rule pages, check pages, and the Getting Started page
**When** `mkdocs build --strict` runs
**Then** ezglossary produces inline tooltips on hover for matched glossary terms across those pages, with no build warnings or errors

**Given** the complete docs site with ezglossary configured
**When** `mkdocs build --strict` runs
**Then** the build succeeds with zero warnings (NFR-D2)

#### Story 13.2: Auto-generated API Reference

As a **developer integrating docvet programmatically**,
I want **auto-generated API reference pages for all public modules rendered from source docstrings**,
So that **I can browse the public API without reading source code, with zero drift between docs and implementation**.

**Dependencies:** Epic 9 Story 9.2 (`__all__` exports on all public modules — prerequisite for complete mkdocstrings rendering)

**Acceptance Criteria:**

**Given** the docs optional dependency group in `pyproject.toml`
**When** a developer runs `uv sync --extra docs`
**Then** `mkdocstrings[python]`, `mkdocs-gen-files`, `mkdocs-literate-nav`, and `mkdocs-section-index` are installed alongside existing docs dependencies

**Given** the `mkdocs.yml` plugins section (currently `search → ezglossary → macros` from Story 13.1)
**When** the four new plugins are configured
**Then** the resulting plugin order is `search → ezglossary → gen-files → literate-nav → section-index → mkdocstrings → macros` per Pattern 6, with `gen-files` pointing to `scripts/gen_ref_pages.py`, `literate-nav` reading `SUMMARY.md`, and `mkdocstrings` configured with `handlers.python.paths: [src]` and `docstring_style: google`

**Given** a new script `scripts/gen_ref_pages.py`
**When** mkdocs build runs
**Then** the script walks `src/docvet/**/*.py`, generates one `::: docvet.module` directive page per module, produces a `reference/SUMMARY.md` for literate-nav, and skips `__pycache__` directories

**Given** the generated API reference pages
**When** a developer browses the Reference section
**Then** reference pages exist for all 11 public modules: `docvet`, `docvet.cli`, `docvet.config`, `docvet.discovery`, `docvet.ast_utils`, `docvet.reporting`, `docvet.checks`, `docvet.checks.enrichment`, `docvet.checks.freshness`, `docvet.checks.coverage`, and `docvet.checks.griffe_compat` — each rendering its `__all__` exports, docstrings, type annotations, and function signatures

**Given** the `mkdocs.yml` nav section
**When** the API reference is added
**Then** a top-level "Reference" nav entry appears using the `- Reference: reference/` trailing-slash pattern, delegating navigation to literate-nav's generated `SUMMARY.md`

**Given** the `mkdocs-section-index` plugin
**When** a developer clicks the "Reference" nav header
**Then** it serves as a clickable index page for the API reference section (not just a non-clickable group label)

**Given** the complete docs site with all plugins configured
**When** `mkdocs build --strict` runs
**Then** the build succeeds with zero warnings, all 11 API reference pages render correctly, and no broken cross-references exist (NFR-D2)

#### Story 13.3: GitHub Pages Deployment

As a **developer or potential user**,
I want **the docvet documentation site deployed to GitHub Pages and accessible at the project's public URL**,
So that **I can read documentation without cloning the repo or building locally**.

**Note:** FR-D2 ("runs automatically as part of the release workflow") is satisfied by event timing — release-please merges to `main`, which triggers this standalone workflow. Docs deploy runs *alongside* the release, not *inside* the publish workflow.

**Setup Note:** GitHub Pages source must be set to "GitHub Actions" (not "Deploy from a branch") in the repository Settings → Pages. This is a one-time manual configuration, not automatable via workflow code.

**Acceptance Criteria:**

**Given** the GitHub Actions workflow directory
**When** a new standalone `.github/workflows/docs.yml` workflow is created
**Then** it uses `actions/upload-pages-artifact@v4` and `actions/deploy-pages@v4` to build and deploy the mkdocs site to GitHub Pages

**Given** the docs workflow triggers
**When** configured
**Then** the workflow triggers on `push` to `main` and on `workflow_dispatch` (manual), allowing both automatic deployment on release and on-demand deployment

**Given** the docs workflow permissions
**When** the deployment job runs
**Then** it requests `pages: write`, `id-token: write`, and `contents: read` permissions explicitly (all unmentioned permissions default to `none` per CLAUDE.md CI lessons)

**Given** the docs workflow concurrency configuration
**When** multiple deployments are triggered
**Then** a concurrency group (`group: pages`, `cancel-in-progress: false`) prevents parallel deployments from conflicting

**Given** the docs workflow build step
**When** the job executes
**Then** it checks out the repo, sets up Python and uv, runs `uv sync --extra docs` to install documentation dependencies, and runs `mkdocs build --strict` before uploading the artifact

**Given** a successful deployment
**When** a developer visits `https://alberto-codes.github.io/docvet/`
**Then** the full documentation site is accessible — Getting Started, check pages, rule pages, glossary, API reference, configuration, and CLI reference all render correctly
