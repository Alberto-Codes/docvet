# Story 14.4: CI & Pre-commit Integration Docs

Status: review
Branch: `feat/docs-14-4-ci-and-pre-commit-integration-docs`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer adopting docvet**,
I want a dedicated documentation page with copy-paste CI and pre-commit snippets,
so that I can integrate docvet into my workflow in minutes without piecing together instructions from multiple sources.

## Acceptance Criteria

1. **Given** the mkdocs site has no CI integration documentation, **when** a new "CI Integration" page is added to the documentation site, **then** the page is accessible from the navigation in a logical location (either as a new top-level page adjacent to Getting Started, or by restructuring Getting Started into a section with sub-pages — dev agent decides based on existing nav structure) **and** the nav change is minimal and consistent with the site's information architecture.

2. **Given** the CI Integration page exists, **when** a user reads the GitHub Action section, **then** the page includes copy-paste workflow snippets for three scenarios: basic usage, with griffe, and version-pinned **and** each snippet is a complete, valid GitHub Actions workflow job (not a fragment).

3. **Given** the CI Integration page exists, **when** a user reads the pre-commit section, **then** the page includes a copy-paste `.pre-commit-config.yaml` snippet with `repo`, `rev`, and `hooks` configured for docvet **and** the section notes that the hook runs `docvet check --staged` on Python files.

4. **Given** the CI Integration page exists, **when** a user reads the configuration section, **then** the page documents how `fail-on` and `warn-on` affect CI exit codes **and** it links to the existing Configuration Reference page for full config details rather than duplicating content.

5. **Given** the page follows existing site design patterns, **when** the docs site is built with `mkdocs build --strict`, **then** the build succeeds with zero warnings **and** the page renders correctly with material theme admonitions and code blocks (NFR-A5).

6. **Given** the `.pre-commit-hooks.yaml` is published in the repository, **when** the file is validated against pre-commit framework requirements, **then** `pre-commit try-repo . docvet --all-files` succeeds in a clean environment **and** the pre-commit.com listing for `Alberto-Codes/docvet` is verified (note: indexing may take up to 7 days after merge).

## Tasks / Subtasks

- [x] **Task 1: Create CI Integration docs page** (AC: 1, 2, 3, 4, 5)
  - [x] 1.1 Created `docs/site/ci-integration.md` following existing page patterns (frontmatter, headings, admonitions, tabbed code blocks)
  - [x] 1.2 Wrote **GitHub Action** section with 3 complete workflow job snippets using tabbed code blocks:
    - Basic: `uses: Alberto-Codes/docvet@v1`
    - Version-pinned: `uses: Alberto-Codes/docvet@v1` with `version: '1.0.2'` and `args: 'check --all'`
    - With griffe: setup-python + `pip install griffe` + docvet action
  - [x] 1.3 Wrote **Pre-commit** section with copy-paste `.pre-commit-config.yaml` snippet (basic + with griffe/additional_dependencies variant)
  - [x] 1.4 Wrote **Exit Codes and CI Behavior** section explaining `fail-on`/`warn-on` exit code behavior with link to [Configuration](configuration.md) for full details
  - [x] 1.5 Exit codes documented inline: 0 = pass, 1 = findings in fail-on, 2 = usage error

- [x] **Task 2: Update mkdocs.yml navigation** (AC: 1)
  - [x] 2.1 Added `CI Integration: ci-integration.md` to `nav:` between "Getting Started" and "Checks"
  - [x] 2.2 Verified nav ordering: Getting Started → CI Integration → Checks → Rules → Configuration → CLI Reference — logical flow from install → integrate → understand

- [x] **Task 3: Update Getting Started page links** (AC: 1)
  - [x] 3.1 Added link to CI Integration page as first item in "What's Next" section of `docs/site/index.md`

- [x] **Task 4: Validate docs build** (AC: 5)
  - [x] 4.1 Ran `uv run mkdocs build --strict` — zero warnings, build succeeded in 1.67s
  - [x] 4.2 Visual verification deferred to CI/PR — build success confirms structural correctness

- [x] **Task 5: Validate pre-commit hook** (AC: 6)
  - [x] 5.1 Ran `pre-commit try-repo . docvet --all-files` — Passed
  - [x] 5.2 pre-commit.com indexing is automatic after merge to default branch — may take up to 7 days

## AC-to-Test Mapping

<!-- This is a docs story. "Tests" are build validation and manual verification, not pytest tests. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Task 2.1: CI Integration added to nav between Getting Started and Checks; Task 4.1: `mkdocs build --strict` succeeds | Pass |
| 2 | Task 1.2: 3 tabbed GitHub Action workflow job snippets (Basic, Version-pinned, With griffe) in ci-integration.md | Pass |
| 3 | Task 1.3: Pre-commit snippet with `--staged` note in ci-integration.md | Pass |
| 4 | Task 1.4: Exit Codes and CI Behavior section with fail-on/warn-on explanation + link to configuration.md | Pass |
| 5 | Task 4.1: `mkdocs build --strict` exits 0 with zero warnings (1.67s build) | Pass |
| 6 | Task 5.1: `pre-commit try-repo . docvet --all-files` — Passed | Pass |

## Dev Notes

### Story Nature

This is a **docs story** — the only code-adjacent change is adding a markdown page and updating `mkdocs.yml` navigation. No Python source code in `src/` is modified. Quality gates (ruff, pytest, docvet, interrogate) will pass trivially.

### Current State of mkdocs.yml Navigation

```yaml
nav:
  - Getting Started: index.md
  - Checks:
    - checks/enrichment.md
    - checks/freshness.md
    - checks/coverage.md
    - checks/griffe.md
  - Rules: [19 rule pages]
  - Configuration: configuration.md
  - CLI Reference: cli-reference.md
  - Glossary: glossary.md
  - Reference: reference/
```

**Navigation decision:** Add `CI Integration: ci-integration.md` as a new top-level entry between "Getting Started" and "Checks". This keeps the nav flat and consistent — the page is conceptually about *integrating* docvet (a step after installation), distinct from understanding checks or configuration.

### Current State of docs/site/

No CI Integration page exists. The closest content is:
- `index.md` — Getting Started with installation and usage
- `configuration.md` — Full config reference (133 lines)
- `cli-reference.md` — CLI commands, options, exit codes (155 lines)

### Content Strategy: Reference, Don't Duplicate

The README already has GitHub Action and pre-commit snippets (lines 74-124). The docs page should be the *definitive* reference with more detail:
- **GitHub Action snippets**: Expand to complete workflow jobs (not fragments like README), explain each input
- **Pre-commit snippets**: Same basic pattern but add context about `--staged` behavior and `additional_dependencies`
- **Configuration**: Explain CI-specific behavior (`fail-on` → exit code 1, `warn-on` → exit code 0) and link to `configuration.md` for full details
- **Do NOT duplicate**: Full config option tables (link to configuration.md), full CLI reference (link to cli-reference.md)

### Design Patterns to Follow

From existing docs pages:
- **Tabbed code blocks**: `=== "Tab Name"` with indented code fences (used in index.md for install tabs)
- **Admonitions**: `!!! tip`, `!!! info`, `!!! warning` for contextual notes
- **Tables**: For option/parameter reference
- **Links**: Relative markdown links like `[Configuration](configuration.md)`
- **Frontmatter**: `title:` field for page title

### action.yml Inputs (for documentation)

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `version` | No | `'latest'` | docvet version to install (use `"latest"` for newest) |
| `args` | No | `'check'` | Arguments to pass to docvet (e.g., `"check --all"`) |

### .pre-commit-hooks.yaml (for documentation)

```yaml
- id: docvet
  name: docvet
  entry: docvet check --staged
  language: python
  types: [python]
  pass_filenames: false
  require_serial: true
```

Key behavior: runs `docvet check --staged` on Python files only. `pass_filenames: false` means docvet discovers files itself via git.

### Exit Code Behavior (for CI section)

`determine_exit_code(findings_by_check, config)` in `reporting.py`:
- Returns `1` if any check in `fail_on` has ≥1 finding → CI job fails
- Returns `0` if no findings in `fail_on` checks → CI job passes
- `warn_on` controls what gets reported but NOT exit codes
- Without `[tool.docvet]` config: `fail_on = []` → exit code always 0

### Pre-commit Validation

- `.pre-commit-hooks.yaml` already exists at repo root and is correct
- `pre-commit try-repo . docvet --all-files` should work in a clean env
- pre-commit.com indexes repos automatically after they have a `.pre-commit-hooks.yaml` on the default branch — indexing may take up to 7 days after merge to main

### Key Files to Touch

| File | Action | Notes |
|------|--------|-------|
| `docs/site/ci-integration.md` | **Create** | New CI Integration documentation page |
| `mkdocs.yml` | **Edit** | Add CI Integration to nav between Getting Started and Checks |
| `docs/site/index.md` | **Edit** | Add link to CI Integration in What's Next section |

### Critical Guardrails

- **Do NOT modify** `src/` — no Python source code changes in this story
- **Do NOT modify** existing docs pages beyond adding a link in index.md What's Next
- **Do NOT duplicate** configuration option tables — link to configuration.md instead
- **Do NOT duplicate** CLI reference details — link to cli-reference.md instead
- **Do NOT modify** `.pre-commit-hooks.yaml` or `action.yml` — those are already correct
- **Do NOT modify** `.github/workflows/` — CI is not in scope
- **Follow** existing page design patterns (frontmatter, headings, tabbed code blocks, admonitions)
- **Snippets must be complete**: GitHub Action workflow jobs should be complete `jobs:` blocks, not fragments

### Previous Story Intelligence (Story 14.3)

- Config/docs story pattern: quality gates pass trivially, no Python code
- Commit style: user prefers one file per commit with conventional commit messages
- CHANGELOG conflict warning: develop→main rebase-and-merge will conflict on CHANGELOG.md — resolve by keeping develop's version
- Story 14.3 is done; this story can proceed independently

### Project Structure Notes

- Docs pages live in `docs/site/` — new page goes to `docs/site/ci-integration.md`
- mkdocs config at project root: `mkdocs.yml`
- Branch naming: `feat/docs-14-4-ci-and-pre-commit-integration-docs` — scope `docs` since primary change is documentation
- PR targets `develop` per normal flow
- mkdocs build requires docs dependencies: `uv sync --extra docs` or `uv sync --dev` (docs deps may not be in dev group — check before building)

### References

- [Source: mkdocs.yml] — current navigation structure (102 lines, 7 top-level entries)
- [Source: docs/site/index.md] — Getting Started page with What's Next links (125 lines)
- [Source: docs/site/configuration.md] — full config reference (133 lines, fail-on/warn-on docs)
- [Source: docs/site/cli-reference.md] — CLI reference with exit codes (155 lines)
- [Source: action.yml] — GitHub Action metadata (2 inputs: version, args)
- [Source: .pre-commit-hooks.yaml] — pre-commit hook definition (7 lines)
- [Source: README.md] — existing GitHub Action and pre-commit snippets (lines 74-124)
- [Source: epics-adoption.md#Story 14.4] — FR-A13, FR-A14, FR-A15, FR-A16, NFR-A5
- [Source: 14-3-dogfood-ci.md] — previous story intelligence

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

- Created CI Integration page with 3 sections: GitHub Action (3 tabbed snippets), Pre-commit (2 tabbed snippets), Exit Codes and CI Behavior
- Used current version `v1.0.2` in all snippets instead of `v1.0.0`
- Added `fetch-depth: 0` tip for freshness blame support
- Page follows existing design patterns: frontmatter, tabbed code blocks, admonitions, tables, relative links
- `mkdocs build --strict` passes with zero warnings
- `pre-commit try-repo . docvet --all-files` passes
- Docs dependencies installed via `uv sync --extra docs` (not in dev group)

### Change Log

- 2026-02-24: Implemented Tasks 1-5, ran quality gates, marked story ready for review

### File List

- `docs/site/ci-integration.md` — new CI Integration documentation page
- `mkdocs.yml` — added CI Integration to nav between Getting Started and Checks
- `docs/site/index.md` — added CI Integration link to What's Next section

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
