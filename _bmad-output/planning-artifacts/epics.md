---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
  - 'freshness-step-01'
  - 'freshness-step-02'
  - 'freshness-step-03'
  - 'freshness-step-04'
  - 'coverage-step-01'
  - 'coverage-step-02'
  - 'coverage-step-03'
  - 'coverage-step-04'
  - 'griffe-step-01'
  - 'griffe-step-02'
  - 'griffe-step-03'
  - 'griffe-step-04'
  - 'reporting-step-01'
  - 'reporting-step-02'
  - 'reporting-step-03'
  - 'reporting-step-04'
  - 'v1-publish-step-01'
  - 'v1-publish-step-02'
  - 'v1-publish-step-03'
  - 'v1-publish-step-04'
v1PublishCompletedAt: '2026-02-19'
reportingStartedAt: '2026-02-11'
freshnessStartedAt: '2026-02-09'
coverageStartedAt: '2026-02-11'
griffeStartedAt: '2026-02-11'
v1PublishStartedAt: '2026-02-19'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - 'docs/product-vision.md'
---

# docvet v1.0 Polish & Publish - Epic Breakdown

## Overview

This document provides the epic and story breakdown for docvet's **v1.0 "Polish & Publish" phase** — the packaging, presentation, and integration infrastructure required to ship docvet as a credible, installable, and discoverable Python developer tool. All check modules and reporting are complete (678 tests, 19 rules, 5 subcommands); this phase wraps them for public consumption.

## Requirements Inventory

### Functional Requirements

- **FR111:** The system can be installed from PyPI via `pip install docvet` with no compilation step — pure Python package with typer as the only required runtime dependency
- **FR112:** The system can expose an optional `griffe` extra via `pip install docvet[griffe]` for users who want rendering compatibility checks — **ALREADY SATISFIED** (`pyproject.toml` lines 14-17)
- **FR113:** The system can publish PyPI package metadata that includes classifiers for Development Status (Production/Stable), Environment (Console), Python versions (3.12, 3.13), and tags including adjacent tool names (interrogate, pydocstyle, darglint, docstring, mkdocs) for search discoverability
- **FR114:** The system can provide a `.pre-commit-hooks.yaml` in the repository root with hook id `docvet` that runs `docvet check` on staged Python files, using `language: python` and `types: [python]`
- **FR115:** The pre-commit hook respects `[tool.docvet]` configuration from `pyproject.toml`, including `fail-on`, `warn-on`, and per-check configuration sections — **ALREADY SATISFIED** (hook runs `docvet check`, CLI reads config)
- **FR116:** The system can provide a first-party composite GitHub Action (`runs-using: composite`) that runs `docvet check` with three configurable inputs: `version` (default: `latest`), `args` (default: `check`), and `src` (default: `.`), supporting version pinning via explicit input or automatic detection from `pyproject.toml`
- **FR117:** The GitHub Action produces exit codes compatible with GitHub Actions pass/fail semantics — exit 0 on success, exit 1 when `fail-on` checks produce findings — **ALREADY SATISFIED** (Action runs `docvet check`, which has correct exit codes)
- **FR118:** The README includes a comparison table showing layer coverage for docvet vs ruff, interrogate, and pydoclint across the six-layer quality model
- **FR119:** The README includes a single-command quickstart (`pip install docvet && docvet check --all`) and a pre-commit configuration snippet — a developer can go from discovery to first findings in under 2 minutes
- **FR120:** The README includes a badge row (PyPI version, CI status, license, Python versions, "docs vetted | docvet"), a copy-paste badge snippet for adopters to display in their own projects, and a "Used By" section
- **FR121:** The system can serve a documentation site built with mkdocs-material, containing at minimum 6 pages: Getting Started, Enrichment Check, Freshness Check, Coverage Check, Griffe Check, and CLI Reference
- **FR122:** The system can generate documentation that includes client-side full-text search via mkdocs-material's built-in search plugin, and a Configuration page documenting every `[tool.docvet]` key with defaults, types, and examples
- **FR123:** Each of the 19 rule identifiers has a dedicated documentation page showing the rule code, check type, default severity, and category
- **FR124:** Each rule reference page follows the What/Why/Example/Fix template: "What it does", "Why is this bad?", "Example" (code showing violation), and "Fix" (code showing corrected version)
- **FR125:** Running `docvet check --all` on docvet's own codebase produces zero findings — the tool's own documentation meets its own quality standards. **CURRENT STATE: 23 findings (8 required, 15 recommended) across 5 files**
- **FR126:** The README displays a "docs vetted | docvet" shields.io badge linking to the project, serving as a self-referential credibility signal
- **FR127:** All public modules define `__all__` exports, ensuring only intentional symbols are part of the stable v1 public API. **CURRENT STATE: 2 of 11 modules have `__all__`; 9 need it added**

#### Gap FRs (identified during party-mode review)

- **FR-G1:** The project includes a LICENSE file at the repository root and a `license` field in `pyproject.toml` — required for PyPI credibility and corporate adoption
- **FR-G2:** The package version is bumped to `1.0.0` in `pyproject.toml` and is accessible via `docvet --version` at the CLI
- **FR-G3:** The project includes a CHANGELOG.md with a v1.0.0 release entry summarizing the complete feature set
- **FR-G4:** The package is validated on TestPyPI before production PyPI publish — install, import, and `docvet check --help` verified in a fresh virtual environment
- **FR-G5:** The build configuration (`[tool.hatch.build]`) excludes non-distribution files (tests/, fixtures/, _bmad-output/, docs source, .github/) from the published wheel and sdist

### NonFunctional Requirements

- **NFR55:** The PyPI package installs cleanly in a fresh virtual environment with no compilation step and no system-level dependencies (pure Python wheel)
- **NFR56:** The package size stays under 500KB — no bundled binaries, test data, fixture files, or development artifacts in the published distribution
- **NFR57:** The documentation site loads in under 3 seconds, includes client-side search, and renders without layout breaks on viewports >= 320px wide through 1920px
- **NFR58:** Every CLI flag documented in the docs site matches the actual `--help` output — no drift between documentation and implementation
- **NFR59:** The pre-commit hook executes in under 10 seconds for 50 staged Python files on commodity hardware
- **NFR60:** The GitHub Action runs in under 60 seconds for a 200-file codebase on a standard GitHub Actions runner
- **NFR61:** The pre-commit hook works with pre-commit framework v3.x and v4.x without version-specific workarounds
- **NFR62:** The GitHub Action works with `ubuntu-latest`, `macos-latest`, and `windows-latest` runners without platform-specific code paths
- **NFR63:** docvet's own codebase maintains zero findings from `docvet check --all` as a CI gate
- **NFR64:** The public API surface (`Finding` dataclass, check functions, CLI command names, CLI option names) is stable for v1 — no breaking changes within the v1.x lifecycle
- **NFR65:** All public modules define `__all__` exports — importing `from docvet.checks import *` or `from docvet import *` produces only the intended public symbols
- **NFR66:** The v1 API stability commitment covers: `Finding` (6 fields), `check_enrichment`, `check_freshness_diff`, `check_freshness_drift`, `check_coverage`, `check_griffe_compat`, and all CLI subcommand names

### Additional Requirements

**From Architecture:**
- No new runtime dependencies beyond typer (and optional griffe) — stdlib-only architecture
- `Finding` dataclass shape is frozen for v1 — 6 fields, no additions or removals
- All check modules are isolated — no cross-imports between check modules
- Module layout follows `src/docvet/` structure with `checks/` subpackage
- Google-style docstrings assumed throughout

**From Product Vision:**
- Package targets PyPI publication as `docvet` — short, memorable, zero-conflict name
- Fills the gap between style linting (ruff D rules) and presence checking (interrogate)
- Layers 1-2 delegated to existing tools; layers 3-6 are docvet's territory
- Target consumers: Python projects using Google-style docstrings, especially mkdocs-material + mkdocstrings workflows
- Positioning: "ruff checks how your docstrings look. interrogate checks if they exist. docvet checks if they're right."

**From PRD Market Research:**
- 73% of developers demand hands-on value within minutes — zero-config trial essential
- Documentation quality is the #1 trust signal (34.2%) for Python developer tool adoption
- Pre-commit hooks serve as viral distribution channels
- 8 deliverables mapped to GitHub issues #49-#56: dogfooding, README, docs site, rule reference, pre-commit, GitHub Action, PyPI publish, API surface audit

### FR Triage (party-mode review)

#### Bucket 1: Already Satisfied (verify only)

| FR | Description | Evidence |
|----|-------------|----------|
| FR112 | Optional `griffe` extra | `pyproject.toml` already declares `[project.optional-dependencies] griffe` |
| FR115 | Pre-commit hook respects config | Hook runs `docvet check`, CLI already reads `pyproject.toml` |
| FR117 | GitHub Action exit codes | Action runs `docvet check`, which already has correct exit codes |

#### Bucket 2: New Artifact Creation

| FR | Description | Artifact |
|----|-------------|----------|
| FR113 | PyPI classifiers + tags | `pyproject.toml` `[project]` section update |
| FR114 | `.pre-commit-hooks.yaml` | New file, ~10 lines YAML |
| FR116 | GitHub Action composite | New `action.yml`, ~30-40 lines |
| FR118 | README comparison table | README content |
| FR119 | README quickstart + snippet | README content |
| FR120 | README badge row | README content |
| FR121 | mkdocs-material docs site | `mkdocs.yml` + docs pages — **largest artifact** |
| FR122 | Search + Configuration page | Part of docs site |
| FR123 | 19 rule reference pages | 19 markdown files — **high volume, templated** |
| FR124 | What/Why/Example/Fix per rule | Content for each of 19 pages |
| FR126 | "docs vetted" badge | Badge markdown in README |
| FR-G1 | LICENSE file | New file + `pyproject.toml` field |
| FR-G3 | CHANGELOG.md | New file with v1.0.0 entry |

#### Bucket 3: Code Changes

| FR | Description | Scope |
|----|-------------|-------|
| FR111 | Installable from PyPI | Build config audit, license field, version bump |
| FR125 | Zero findings on own codebase | **23 findings to fix** across 5 files |
| FR127 | `__all__` on all public modules | 9 modules need `__all__` added |
| FR-G2 | Version bump to 1.0.0 | `pyproject.toml` + verify `--version` works |
| FR-G4 | TestPyPI validation | Build + upload + install verification |
| FR-G5 | Build exclusions | `[tool.hatch.build]` config in `pyproject.toml` |

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR111 | Epic 10 | PyPI installable, pure Python |
| FR112 | — | Already satisfied (griffe extra exists) |
| FR113 | Epic 10 | PyPI classifiers and tags |
| FR114 | Epic 10 | `.pre-commit-hooks.yaml` |
| FR115 | — | Already satisfied (CLI reads config) |
| FR116 | Epic 10 | GitHub Action composite |
| FR117 | — | Already satisfied (correct exit codes) |
| FR118 | Epic 10 | README comparison table |
| FR119 | Epic 10 | README quickstart + snippet |
| FR120 | Epic 10 | README badge row |
| FR121 | Epic 11 | mkdocs-material docs site |
| FR122 | Epic 11 | Search + Configuration page |
| FR123 | Epic 11 | 19 rule reference pages |
| FR124 | Epic 11 | What/Why/Example/Fix template |
| FR125 | Epic 9 | Zero findings on own codebase |
| FR126 | Epic 10 | "docs vetted" badge |
| FR127 | Epic 9 | `__all__` exports on all modules |
| FR-G1 | Epic 10 | LICENSE file |
| FR-G2 | Epic 9 | Version bump to 1.0.0 |
| FR-G3 | Epic 10 | CHANGELOG.md |
| FR-G4 | Epic 10 | TestPyPI validation |
| FR-G5 | Epic 9 | Build exclusions config |

## Epic List

### Epic 9: Dogfooding & API Hardening

Fix all 23 docvet findings on docvet's own codebase, add `__all__` exports to all public modules, bump version to 1.0.0, and configure build exclusions — proving the tool works on itself and locking down the v1 public API surface.

**FRs covered:** FR125, FR127, FR-G2, FR-G5
**NFRs addressed:** NFR63, NFR65, NFR56
**Prerequisite for:** Epic 10, Epic 11

### Epic 10: Package, Publish & Integrations

Ship docvet as a credible PyPI package with LICENSE, classifiers, CHANGELOG, README (comparison table, quickstart, badges), pre-commit hook, GitHub Action, and TestPyPI validation — a developer can discover, install, and integrate docvet into their workflow.

**FRs covered:** FR111, FR113, FR114, FR116, FR118, FR119, FR120, FR126, FR-G1, FR-G3, FR-G4
**NFRs addressed:** NFR55, NFR56, NFR59, NFR60, NFR61, NFR62
**Depends on:** Epic 9

### Epic 11: Documentation Site & Rule Reference

Build an mkdocs-material documentation site with Getting Started, per-check pages, Configuration, CLI Reference, and 19 dedicated rule reference pages following the What/Why/Example/Fix template — a developer who receives a finding can understand and fix it in 30 seconds.

**FRs covered:** FR121, FR122, FR123, FR124
**NFRs addressed:** NFR57, NFR58
**Depends on:** Epic 9 (soft — docs can be written in parallel with Epic 10)

---

## Epic 9: Dogfooding & API Hardening

Fix all 23 docvet findings on docvet's own codebase, add `__all__` exports to all public modules, bump version to 1.0.0, and configure build exclusions — proving the tool works on itself and locking down the v1 public API surface.

### Story 9.1: Fix Docvet Findings on Own Codebase

As a docvet maintainer,
I want all 23 docstring findings on docvet's own source code resolved to zero,
So that the tool credibly dogfoods itself before publication.

**Acceptance Criteria:**

**Given** the docvet codebase at current state with 23 findings (8 required, 15 recommended)
**When** findings are resolved (via docstring fixes or config adjustments — e.g., narrowing `require-examples` in `[tool.docvet.enrichment]` for internal enums is a valid approach)
**Then** `docvet check --all` produces zero findings
**And** all quality gates pass (`ruff check`, `ruff format --check`, `ty check`, `interrogate`) — fixes do not introduce new violations
**And** all existing tests continue to pass (`uv run pytest`)

### Story 9.2: Add `__all__` Exports to All Public Modules

As a Python developer importing from docvet,
I want only intentional public symbols exported from each module,
So that the v1 API surface is explicit and stable.

**Acceptance Criteria:**

**Given** 11 modules in `src/docvet/` (9 currently lack `__all__`)
**When** `__all__` is defined in every module
**Then** each module's `__all__` lists only its intended public symbols per NFR66 (`Finding`, `check_enrichment`, `check_freshness_diff`, `check_freshness_drift`, `check_coverage`, `check_griffe_compat`, and supporting public types)
**And** `from docvet.checks import *` produces only `Finding` and the check functions — no internal helpers
**And** `from docvet import *` produces only the intended top-level API
**And** internal helpers (prefixed with `_`) are not accessible via `*` import from any module (negative assertion)
**And** modules that already have `__all__` (`checks/__init__.py`, `checks/coverage.py`) are unchanged or verified as correct
**And** all existing tests continue to pass

### Story 9.3: Version Bump and Build Configuration

As a package maintainer preparing for v1.0 release,
I want the version set to 1.0.0 and non-distribution files excluded from the build,
So that the published package is correctly versioned and contains only production code.

**Acceptance Criteria:**

**Given** `pyproject.toml` with `version = "0.1.0"`, no build exclusions, and no `--version` CLI flag
**When** the version is bumped, a `--version` flag is added, and sdist build exclusions are configured
**Then** `pyproject.toml` shows `version = "1.0.0"`
**And** a `--version` CLI callback is implemented (via `importlib.metadata` or typer's version callback) so that `docvet --version` outputs `1.0.0`
**And** `[tool.hatch.build.targets.sdist]` excludes non-distribution directories (`tests/`, `_bmad-output/`, `_bmad/`, `.github/`, `docs/`, fixture files) — wheel exclusions are unnecessary as hatchling's `src` layout already scopes the wheel to `src/docvet/`
**And** `uv build` produces both wheel and sdist, each under 500KB (NFR56)
**And** the wheel contains only `src/docvet/` package files (verified via `zipfile -l`)
**And** all existing tests continue to pass

---

## Epic 10: Package, Publish & Integrations

Ship docvet as a credible PyPI package with LICENSE, classifiers, CHANGELOG, README (comparison table, quickstart, badges), pre-commit hook, GitHub Action, and TestPyPI validation — a developer can discover, install, and integrate docvet into their workflow.

### Story 10.1: LICENSE and Package Metadata

As a Python developer evaluating docvet,
I want to see a clear license and proper PyPI classifiers,
So that I can confirm the tool is safe to adopt in my project.

**Acceptance Criteria:**

**Given** `pyproject.toml` has no `license` field or classifiers
**When** LICENSE file and metadata are added
**Then** a LICENSE file exists at the repository root (MIT or Apache-2.0)
**And** `pyproject.toml` includes a `license` field referencing the LICENSE file
**And** `pyproject.toml` includes classifiers: Development Status (Production/Stable), Environment (Console), Intended Audience (Developers), License, Programming Language (Python :: 3.12, Python :: 3.13), Topic (Software Development :: Quality Assurance)
**And** `pyproject.toml` includes `keywords` with: `docstring`, `linter`, `mkdocs`, `interrogate`, `pydocstyle`, `darglint`, `documentation`, `quality`
**And** all existing tests continue to pass (`uv run pytest`)

### Story 10.2: README with Comparison Table, Quickstart, and Badges

As a developer discovering docvet on PyPI or GitHub,
I want to understand what it does, how it compares to alternatives, and how to start using it in under 2 minutes,
So that I can make an informed adoption decision quickly.

**Acceptance Criteria:**

**Given** an empty `README.md`
**When** the README is written
**Then** it includes a badge row: PyPI version, CI status, license, Python versions, "docs vetted | docvet"
**And** it includes a one-line tagline and the six-layer quality model summary
**And** it includes a comparison table showing layer coverage for ruff, interrogate, pydoclint, and docvet
**And** it includes a single-command quickstart: `pip install docvet && docvet check --all`
**And** it includes a 3-line pre-commit configuration YAML snippet
**And** it includes a copy-paste badge snippet for adopters (`[![docs vetted | docvet]...]`)
**And** it includes a "Used By" section placeholder
**And** the README renders correctly as PyPI long description — verified via `twine check dist/*` or `python -m readme_renderer README.md` (no rendering errors, no broken links)

### Story 10.3: Pre-commit Hook and GitHub Action

As a developer integrating docvet into CI,
I want a pre-commit hook and GitHub Action available with minimal configuration,
So that I can automate documentation quality gating in my workflow.

**Acceptance Criteria:**

**Given** no `.pre-commit-hooks.yaml` or `action.yml` exists
**When** both integration files are created
**Then** `.pre-commit-hooks.yaml` exists at repo root with `id: docvet`, `language: python`, `types: [python]`, `entry: docvet check`
**And** the hook is verified via `pre-commit try-repo . docvet --all-files` against the local repo (manual verification — not automatable in CI until published)
**And** `action.yml` exists at repo root as a composite GitHub Action with inputs: `version` (default: `latest`), `args` (default: `check`), `src` (default: `.`)
**And** the Action installs docvet, runs `docvet` with the provided args, and propagates the exit code
**And** the README's pre-commit snippet references the correct repo URL and hook id

### Story 10.4: CHANGELOG and Publication Pipeline

As a package maintainer,
I want a CHANGELOG documenting v1.0.0 and a validated publish pipeline,
So that the package is professionally released with an auditable history.

**Acceptance Criteria:**

**Given** no CHANGELOG exists and the package has never been published
**When** CHANGELOG and publish pipeline are prepared
**Then** `CHANGELOG.md` exists with a v1.0.0 entry summarizing: 4 check modules (enrichment, freshness, coverage, griffe), 19 rules, reporting module, CLI with 5 subcommands
**And** `uv build` produces both wheel and sdist
**And** the wheel installs cleanly in a fresh virtual environment (`pip install dist/docvet-1.0.0-py3-none-any.whl`)
**And** `docvet check --help` works after install from wheel
**And** `import docvet` works after install from wheel
**And** the package is validated on TestPyPI: upload, install from TestPyPI, verify `docvet --version` outputs `1.0.0` (prerequisite: TestPyPI account and API token configured — infrastructure setup, not a code change)
**And** all existing tests continue to pass (`uv run pytest`)

---

## Epic 11: Documentation Site & Rule Reference

Build an mkdocs-material documentation site with Getting Started, per-check pages, Configuration, CLI Reference, and 19 dedicated rule reference pages following the What/Why/Example/Fix template — a developer who receives a finding can understand and fix it in 30 seconds.

### Story 11.1: Documentation Site Scaffold and Core Pages

As a developer who just installed docvet,
I want a documentation site with Getting Started and CLI Reference pages,
So that I can learn how to use the tool without reading source code.

**Acceptance Criteria:**

**Given** no `mkdocs.yml` or documentation site exists
**When** the docs site is scaffolded
**Then** `mkdocs.yml` exists with mkdocs-material theme, navigation, and search plugin enabled
**And** a Getting Started page exists with installation instructions (`pip install docvet`, `pip install docvet[griffe]`), quickstart command, and a brief overview of the four checks
**And** a CLI Reference page exists documenting all 5 subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) and all global options (`--format`, `--output`, `--verbose`, `--staged`, `--all`, `--files`)
**And** `mkdocs serve` builds the site without errors
**And** client-side search returns results for "enrichment", "freshness", "coverage", "griffe"

### Story 11.2: Check Pages and Configuration Reference

As a developer configuring docvet for their team,
I want dedicated pages for each check type and a configuration reference,
So that I understand what each check does and how to customize it.

**Acceptance Criteria:**

**Given** the docs site scaffold from Story 11.1
**When** check pages and config reference are added
**Then** an Enrichment Check page exists explaining the 10 enrichment rules, required vs recommended categories, and `[tool.docvet.enrichment]` config options
**And** a Freshness Check page exists explaining diff mode vs drift mode, the 5 freshness rules, severity levels, and `[tool.docvet.freshness]` config options
**And** a Coverage Check page exists explaining `missing-init` detection and `src-root` behavior
**And** a Griffe Check page exists explaining the 3 griffe rules, optional dependency, and graceful skip behavior
**And** a Configuration page exists documenting every `[tool.docvet]` key with its type, default value, and an example
**And** every CLI flag documented in the site matches the actual `docvet --help` output (NFR58)
**And** `mkdocs serve` builds without errors and all pages are navigable

### Story 11.3: Rule Reference Pages

As a developer who received a docvet finding,
I want to look up the rule by its identifier and understand what it means, why it matters, and how to fix it,
So that I can resolve findings quickly without guessing.

**Acceptance Criteria:**

**Given** the docs site with check pages from Story 11.2
**When** 19 rule reference pages are added
**Then** each of the 19 rule identifiers (`missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-other-parameters`, `missing-attributes`, `missing-typed-attributes`, `missing-examples`, `missing-cross-references`, `prefer-fenced-code-blocks`, `stale-signature`, `stale-body`, `stale-import`, `stale-drift`, `stale-age`, `griffe-missing-type`, `griffe-unknown-param`, `griffe-format-warning`, `missing-init`) has a dedicated page
**And** each page shows: rule code, check type (enrichment/freshness/coverage/griffe), default category (required/recommended)
**And** each page follows the What/Why/Example/Fix template: "What it detects" (1-2 sentences), "Why is this a problem?" (consequence explanation), "Example" (Python code showing the violation), "Fix" (Python code showing the corrected version)
**And** all 19 pages are linked from their parent check page
**And** navigation includes a "Rules" section listing all 19 rules
**And** all 19 rule pages are structurally consistent: same H2 headings (`What it detects`, `Why is this a problem?`, `Example`, `Fix`), same code fence language markers (`python`), same metadata fields (rule code, check type, category)
**And** `mkdocs serve` builds without errors
