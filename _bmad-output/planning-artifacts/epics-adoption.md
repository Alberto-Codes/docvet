---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
status: complete
completedAt: '2026-02-24'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/planning-artifacts/epics-docs-publish.md'
  - 'action.yml'
  - 'release-please-config.json'
  - '.release-please-manifest.json'
  - '.github/workflows/release-please.yml'
  - '.github/workflows/ci.yml'
  - '.pre-commit-hooks.yaml'
  - 'CHANGELOG.md'
  - 'README.md'
  - 'gh-issue-75'
  - 'gh-issue-92'
  - 'party-mode-session-2026-02-24'
---

# docvet - Epic Breakdown (Adoption & Integration)

## Overview

This document provides the epic and story breakdown for docvet's **Adoption & Integration** phase — lowering barriers to discovery, installation, and enforcement of docvet across CI, marketplace, and documentation touchpoints. The tool is published (v1.0.0+ on PyPI), the docs site is live, and all 19 rules are implemented. This phase focuses on making docvet easy to find, adopt, and enforce.

## Requirements Inventory

### Functional Requirements

**Release Pipeline Cleanup:**

- FR-A1: The release-please changelog must not contain duplicate entries — each logical change appears exactly once per release, regardless of develop→main merge strategy
- FR-A2: The develop→main merge workflow must produce clean, non-repetitive commit history that release-please can parse without duplication
- FR-A3: (OPTIONAL) The CHANGELOG.md v1.0.1 and v1.0.2 entries may be cleaned up to remove duplicate lines — not required if forward-fix resolves duplication for future releases

**GitHub Marketplace Publishing:**

- FR-A4: The `action.yml` must include a `branding` block with `icon` and `color` fields from the GitHub-approved sets (Feather icons, GitHub color palette)
- FR-A5: The `action.yml` `description` field must be expanded for marketplace SEO — conveying value proposition and keywords within the 125-char display limit
- FR-A6: The GitHub Action must be published to the GitHub Actions Marketplace via a release with the "Publish this Action to the GitHub Marketplace" checkbox enabled
- FR-A7: The marketplace listing name "docvet" must be verified as available before publication — **VERIFIED 2026-02-24: name is available**

**Dogfood CI (Issue #75):**

- FR-A8: The CI workflow (`.github/workflows/ci.yml`) must include a `docvet` job that runs `docvet check` on the codebase, alongside existing lint, type-check, test, and interrogate jobs
- FR-A9: The CI docvet job must run `uv run docvet check` to test the local checkout (not the PyPI-published version), ensuring current code is validated
- FR-A10: The CI docvet job must fail the workflow when `fail-on` checks produce findings (exit code 1)

**README Restructure:**

- FR-A11: The README must position the GitHub Action section more prominently — either moved higher (after Quickstart) or linked from a navigation section near the top
- FR-A12: The README must include a visible anchor or link from the top section to the GitHub Action usage for marketplace visitors who land on the README

**CI Integration Docs:**

- FR-A13: The mkdocs site must include a new "CI Integration" page documenting GitHub Action usage, pre-commit hook setup, and `fail-on`/`warn-on` configuration for CI contexts
- FR-A14: The CI Integration page must include copy-paste workflow snippets for common scenarios (basic, with griffe, version-pinned)

**Pre-commit Hook Polish:**

- FR-A15: The `.pre-commit-hooks.yaml` must be documented in the mkdocs site CI Integration page with copy-paste `.pre-commit-config.yaml` snippet
- FR-A16: The pre-commit hook discoverability must be verified on pre-commit.com (listed under `Alberto-Codes/docvet`)

**Docvet Badge:**

- FR-A17: A shields.io badge (`docs vetted | docvet`) must be available with consistent purple branding matching the docs site and marketplace color
- FR-A18: The README must include the badge in the badge row and provide a copy-paste snippet for adopters to add to their own projects

### NonFunctional Requirements

- NFR-A1: The changelog must be human-readable — no duplicate entries, no noise from merge strategy artifacts
- NFR-A2: The GitHub Action marketplace listing must display correct metadata (name, description, branding) and link to the repository README
- NFR-A3: The CI docvet job must complete in under 30 seconds for the docvet codebase
- NFR-A4: The README must serve both GitHub repo visitors and marketplace visitors effectively — key integration paths visible within the first scroll
- NFR-A5: The CI Integration docs page must follow the existing mkdocs site design patterns (material theme, admonitions, code tabs)
- NFR-A6: All changes in this epic must flow through the fixed release pipeline — validating the pipeline fix is itself a success criterion

### Additional Requirements

**From Party Mode Discussion (2026-02-24):**

- Marketplace branding: `shield` icon + `purple` color to match docs site theme
- Improved `action.yml` description: "Comprehensive docstring quality checks — completeness, freshness, rendering, and coverage for Python projects"
- Story ordering: fix release pipeline first, then push releases through it
- CI Integration docs page deferred as separate story (not bundled into marketplace publishing)
- Badge design: purple to match marketplace and docs site branding

**From Changelog Analysis:**

- v1.0.2 contains 6 duplicate pairs (same message, different commit SHAs) — caused by squash merge on develop + merge commit to main preserving both versions
- v1.0.1 and v1.0.2 have nearly identical content — suggests release-please re-processed commits across releases
- Root cause: the develop→main merge commit strategy preserves individual commits that are duplicates of the squash-merged PR commits already on develop
- Potential fixes: switch to squash merge for develop→main, use release-please `exclude-paths`, or restructure the branching strategy

**From Existing PRD FRs (already delivered but relevant):**

- FR116: First-party composite GitHub Action — DELIVERED (action.yml exists)
- FR117: Exit codes compatible with GitHub Actions pass/fail — DELIVERED
- FR120: Badge row in README — PARTIALLY DELIVERED (badge row exists, but marketplace badge not yet possible)
- FR126: "docs vetted | docvet" shields.io badge — DELIVERED in README but can be enhanced with marketplace link

### FR Coverage Map

```
FR-A1:  Epic 14, Story 14.1 — Deduplicate changelog entries
FR-A2:  Epic 14, Story 14.1 — Diagnose and fix develop→main merge duplication
FR-A3:  Epic 14, Story 14.1 — (Optional) Clean up historical v1.0.x entries
FR-A4:  Epic 14, Story 14.2 — Add branding block to action.yml
FR-A5:  Epic 14, Story 14.2 — Improve action.yml description for marketplace SEO
FR-A6:  Epic 14, Story 14.2 — Publish to GitHub Actions Marketplace
FR-A7:  VERIFIED — "docvet" is available on marketplace (checked 2026-02-24)
FR-A11: Epic 14, Story 14.2 — Elevate GitHub Action section in README
FR-A12: Epic 14, Story 14.2 — Add navigation anchor for marketplace visitors
FR-A8:  Epic 14, Story 14.3 — Add docvet job to CI workflow
FR-A9:  Epic 14, Story 14.3 — Run uv run docvet check (local checkout)
FR-A10: Epic 14, Story 14.3 — Fail CI on findings
FR-A13: Epic 14, Story 14.4 — New CI Integration docs page
FR-A14: Epic 14, Story 14.4 — Copy-paste workflow snippets
FR-A15: Epic 14, Story 14.4 — Pre-commit hook documentation
FR-A16: Epic 14, Story 14.4 — Verify pre-commit.com listing
FR-A17: Epic 14, Story 14.5 — Purple shields.io badge
FR-A18: Epic 14, Story 14.5 — Copy-paste badge snippet for adopters
```

NFR coverage: NFR-A1 (Story 14.1), NFR-A2 (Story 14.2), NFR-A3 (Story 14.3), NFR-A4 (Story 14.2), NFR-A5 (Story 14.4), NFR-A6 (cross-cutting, validated by Story 14.2 flowing through fixed pipeline).

## Epic List

### Epic 14: Adoption & Integration

**Goal:** Python developers can discover docvet on the GitHub Actions Marketplace, integrate it into CI and pre-commit workflows with copy-paste snippets, trust clean changelogs, and signal adoption with a badge — lowering every barrier between "heard about docvet" and "enforcing it in CI."

### Recommended Story Ordering

```
14.1 → 14.3 → 14.2 → 14.4 → 14.5
```

- **14.1 first**: Fix the release pipeline before pushing releases through it
- **14.3 before 14.2**: Dogfood CI before going public on marketplace — CI badge is green when marketplace visitors inspect the repo (first impressions)
- **14.2 after dogfooding**: Marketplace publish with credibility already established
- **14.4 after marketplace**: Docs support the new marketplace visitors
- **14.5 last**: Badge is the social proof layer after everything else is polished

---

## Epic 14: Adoption & Integration

Python developers can discover docvet on the GitHub Actions Marketplace, integrate it into CI and pre-commit workflows with copy-paste snippets, trust clean changelogs, and signal adoption with a badge — lowering every barrier between "heard about docvet" and "enforcing it in CI."

### Story 14.1: Release Pipeline Cleanup

As a **project maintainer**,
I want the release pipeline to produce clean, non-repetitive changelogs,
So that each release tells a clear story of what changed without confusing duplicate entries.

**Acceptance Criteria:**

**Given** the current develop→main merge strategy produces duplicate changelog entries (same message, different SHAs)
**When** the root cause is diagnosed and a fix is implemented (release-please config, merge strategy change, or branching adjustment)
**Then** the next release-please PR after a develop→main merge contains zero duplicate entries
**And** each logical change appears exactly once in the generated changelog section

**Given** the fix is applied to the release pipeline
**When** a test merge from develop to main is performed and release-please generates a changelog
**Then** the generated changelog section contains zero duplicate entries (verified by comparing against `git log --oneline <last-release-tag>..main`)
**And** the root cause diagnosis and chosen fix are documented in the PR description

**Given** the CHANGELOG.md contains historical duplicate entries from v1.0.1 and v1.0.2
**When** the maintainer optionally chooses to clean up historical entries
**Then** duplicate lines are removed and each release section contains only unique entries
*(This AC is optional — forward-fix is the priority)*

**FRs covered:** FR-A1, FR-A2, FR-A3 (optional)
**NFRs covered:** NFR-A1
**Dependency:** Must complete before Story 14.2

### Story 14.2: Marketplace Publishing & README

As a **Python developer searching for docstring tooling**,
I want to find docvet on the GitHub Actions Marketplace with clear branding and a README that immediately shows how to integrate it,
So that I can evaluate and adopt docvet without hunting through the repository.

**Acceptance Criteria:**

**Given** the `action.yml` has no `branding` block
**When** a `branding` block is added with `icon: 'shield'` and `color: 'purple'`
**Then** the branding fields match GitHub's approved Feather icon set and color palette
**And** the branding visually aligns with the docs site's purple theme

**Given** the `action.yml` `description` is "Run docvet docstring quality checks"
**When** the description is updated to "Comprehensive docstring quality checks — completeness, freshness, rendering, and coverage for Python projects"
**Then** the description conveys the value proposition and fits within the marketplace's 125-char display limit

**Given** the README has the GitHub Action section at line ~95 (below Configuration and Pre-commit)
**When** the README is restructured for marketplace visitors
**Then** the GitHub Action section is reachable within one click or one scroll from the top of the README
**And** the README serves both repo visitors and marketplace visitors effectively (NFR-A4)

**Given** the release pipeline is fixed (Story 14.1) and code changes are merged to main
**When** a new GitHub release is created via release-please
**Then** the "Publish this Action to the GitHub Marketplace" checkbox is enabled during release creation
**And** the marketplace listing displays correct name ("docvet"), description, branding icon/color, and links to the repository README (NFR-A2)

*Note: The marketplace publish is a manual step during GitHub release creation — code changes flow through the normal PR process, but the marketplace checkbox can only be ticked when cutting the release.*

**FRs covered:** FR-A4, FR-A5, FR-A6, FR-A7 (verified), FR-A11, FR-A12
**NFRs covered:** NFR-A2, NFR-A4, NFR-A6

### Story 14.3: Dogfood CI

As a **project maintainer**,
I want docvet to enforce its own docstring quality standards in CI,
So that the project's CI badge reflects genuine docstring quality and establishes credibility for marketplace visitors.

**Acceptance Criteria:**

**Given** the CI workflow (`.github/workflows/ci.yml`) has lint, type-check, test, and interrogate jobs but no docvet job
**When** a `docvet` job is added that runs `uv run docvet check --all`
**Then** the job runs successfully alongside the existing jobs
**And** the job installs dev dependencies via `uv sync --dev` before running the check

**Given** the docvet CI job is configured with `--all` flag
**When** `docvet check --all` finds findings in checks listed in the default `fail-on` (`["enrichment", "freshness"]`)
**Then** the job exits with code 1, failing the workflow
**And** findings are printed to the job log for developer visibility

**Given** the docvet CI job is configured with `--all` flag
**When** `docvet check --all` finds zero findings in `fail-on` checks
**Then** the job exits with code 0, passing the workflow

**Given** the CI docvet job is being added
**When** `docvet check --all` is run against the current `develop` branch before enabling the gate
**Then** it produces zero findings in `fail-on` checks (exit code 0)
**And** if findings exist, they are fixed before the CI job is merged
*(Prerequisite AC — validates the codebase is clean before enabling the gate)*

**FRs covered:** FR-A8, FR-A9, FR-A10
**NFRs covered:** NFR-A3

### Story 14.4: CI & Pre-commit Integration Docs

As a **Python developer adopting docvet**,
I want a dedicated documentation page with copy-paste CI and pre-commit snippets,
So that I can integrate docvet into my workflow in minutes without piecing together instructions from multiple sources.

**Acceptance Criteria:**

**Given** the mkdocs site has no CI integration documentation
**When** a new "CI Integration" page is added to the documentation site
**Then** the page is accessible from the navigation in a logical location (either as a new top-level page adjacent to Getting Started, or by restructuring Getting Started into a section with sub-pages — dev agent decides based on existing nav structure)
**And** the nav change is minimal and consistent with the site's information architecture

**Given** the CI Integration page exists
**When** a user reads the GitHub Action section
**Then** the page includes copy-paste workflow snippets for three scenarios: basic usage, with griffe, and version-pinned
**And** each snippet is a complete, valid GitHub Actions workflow job (not a fragment)

**Given** the CI Integration page exists
**When** a user reads the pre-commit section
**Then** the page includes a copy-paste `.pre-commit-config.yaml` snippet with `repo`, `rev`, and `hooks` configured for docvet
**And** the section notes that the hook runs `docvet check --staged` on Python files

**Given** the CI Integration page exists
**When** a user reads the configuration section
**Then** the page documents how `fail-on` and `warn-on` affect CI exit codes
**And** it links to the existing Configuration Reference page for full config details rather than duplicating content

**Given** the page follows existing site design patterns
**When** the docs site is built with `mkdocs build --strict`
**Then** the build succeeds with zero warnings
**And** the page renders correctly with material theme admonitions and code blocks (NFR-A5)

**Given** the `.pre-commit-hooks.yaml` is published in the repository
**When** the file is validated against pre-commit framework requirements
**Then** `pre-commit try-repo . docvet --all-files` succeeds in a clean environment
**And** the pre-commit.com listing for `Alberto-Codes/docvet` is verified (note: indexing may take up to 7 days after merge)

**FRs covered:** FR-A13, FR-A14, FR-A15, FR-A16
**NFRs covered:** NFR-A5

### Story 14.5: Docvet Badge

As a **project maintainer who uses docvet**,
I want a shields.io badge I can add to my README,
So that I can signal docstring quality to visitors and advertise docvet to the broader Python community.

**Acceptance Criteria:**

**Given** the README has an existing Badge section (line ~137) with a "docs vetted | docvet" badge
**When** the badge is enhanced with purple color branding matching the docs site and marketplace theme
**Then** the badge renders correctly at the shields.io URL with consistent purple styling
**And** the badge links to the docvet marketplace listing (once published) or repository

**Given** the README badge row exists (PyPI version, CI status, license, Python versions)
**When** the docvet badge is verified in the badge row
**Then** it appears alongside existing badges with consistent sizing and spacing

**Given** adopters want to add the badge to their own projects
**When** they read the Badge section in the README
**Then** a copy-paste markdown snippet is provided that they can add directly to their own README
**And** the snippet includes the shields.io URL and a link target to the docvet marketplace or repository

**FRs covered:** FR-A17, FR-A18
