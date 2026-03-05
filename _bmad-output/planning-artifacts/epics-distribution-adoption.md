---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
inputDocuments:
  - 'gh-issue-157'
  - 'gh-issue-150'
  - 'gh-issue-227'
  - 'gh-issue-232'
  - 'gh-issue-262'
  - 'gh-issue-263'
  - 'gh-issue-264'
  - 'gh-issue-278'
  - '_bmad-output/planning-artifacts/prd.md (context)'
  - '_bmad-output/planning-artifacts/architecture.md (context)'
  - 'party-mode consensus (2026-03-04)'
outputFile: '_bmad-output/planning-artifacts/epics-distribution-adoption.md'
---

# docvet - Epic Breakdown (Wave 3: Distribution & Adoption)

## Overview

This document provides the epic and story breakdown for docvet's third wave, covering distribution, onboarding, documentation maturity, and developer experience improvements. The centerpiece is a GitHub Action that creates passive adoption through CI feedback loops. Sourced from 8 GitHub issues prioritized via party-mode consensus (17/17 agents).

## Requirements Inventory

### Functional Requirements

FR1: (#157) Docvet shall provide a first-party GitHub Action that runs checks on pull requests and posts inline annotations on files with docstring findings.

FR2: (#157) The GitHub Action shall support configurable check selection (all, enrichment, freshness, coverage, griffe, presence) via action input.

FR3: (#157) The GitHub Action shall map docvet findings to GitHub workflow annotation commands (`::warning` / `::error`) for inline PR display.

FR4: (#157) The GitHub Action shall exit non-zero when findings exist, integrating with GitHub's required checks enforcement.

FR5: (#150) Docvet shall provide a `docvet init` command that scaffolds `[tool.docvet]` configuration in pyproject.toml.

FR6: (#150) The `docvet init` command shall optionally generate agent instruction snippets for Claude Code (CLAUDE.md), Cursor (.cursorrules), and GitHub Copilot (.github/copilot-instructions.md).

FR7: (#150) The `docvet init` command shall be non-destructive, appending to existing files without overwriting.

FR8: (#264) The docs site shall include a Concepts page bridging Getting Started and Architecture, explaining the six-layer quality model, the ecosystem gap docvet fills, and when to use each check.

FR9: (#264) The Concepts page shall include a before/after showcase demonstrating a Python function with docstring gaps, docvet output, and the fixed version.

FR10: (#263) The docs site glossary shall include definitions for all terms used across the docs that trigger mkdocs-material tooltip hover behavior.

FR11: (#263) The glossary shall fix the six-layer model definition to reflect that docvet now implements layers 1 and 3-6 (presence check covers layer 1).

FR12: (#278) The `_RULE_CATALOG` in mcp.py shall use a TypedDict with per-field types instead of `dict[str, str | None]`.

FR13: (#232) A scheduled GitHub Actions workflow shall run `uv lock --upgrade` weekly and open a PR with updated dependencies.

FR14: (#227) The `prefer-fenced-code-blocks` enrichment rule shall report all non-fenced patterns (both `>>>` doctest and `::` rST) per symbol in a single pass, not short-circuit on the first match.

FR15: (#262) The docs site shall display a copyright footer on every page via mkdocs.yml `copyright` field.

FR16: (#262) The docs site shall include a license note or page referencing the MIT License.

### NonFunctional Requirements

NFR1: (#157) The GitHub Action shall be a composite action using `docvet check --format json` — no custom Docker image.

NFR2: (#157) The GitHub Action shall support configuration via both action inputs and `[tool.docvet]` in pyproject.toml.

NFR3: (#150) The `docvet init` command shall introduce no new runtime dependencies — use typer prompts and stdlib file I/O only.

NFR4: (#150) The `docvet init` command shall detect which agent config files are present and offer relevant options.

NFR5: (#264) The Concepts page shall position docvet as complementary to ruff (style) and interrogate (presence), not competitive.

NFR6: (#263) Glossary additions shall produce working tooltips verified by hovering on the built docs site.

NFR7: (#278) The TypedDict refactor shall not change any runtime behavior — existing tests must pass unchanged.

NFR8: (#232) The uv lock upgrade workflow shall use `peter-evans/create-pull-request` to open PRs automatically.

NFR9: (#227) The dispatch machinery change shall maintain backward compatibility with all other enrichment rules returning `Finding | None`.

NFR10: (#262) License attribution changes shall be verified by `mkdocs build --strict`.

### Additional Requirements

- From architecture: GitHub Action lives in repo root as `action.yml` (composite action pattern). Uses `docvet check --format json` and maps JSON findings to `::warning file={file},line={line}::{message}` workflow commands.
- From architecture: `docvet init` is a new typer subcommand in `src/docvet/cli.py`. Configuration scaffolding writes to `pyproject.toml` using stdlib `tomllib` (read) and string formatting (write — no tomli-w dependency).
- From architecture: `_RULE_CATALOG` in `src/docvet/mcp.py` is the target for TypedDict refactor. `_RULE_TO_CHECK` derivation uses `str()` wrappers that become unnecessary with proper field types.
- From architecture: `_check_prefer_fenced_code_blocks` in `src/docvet/checks/enrichment.py:1228-1300` currently returns `Finding | None` via `_RULE_DISPATCH`. Multi-finding approach: accumulate in `check_enrichment()` orchestrator after dispatch, not change dispatch contract.
- From architecture: Docs site uses mkdocs-material with `content.tooltips` feature. Glossary at `docs/site/glossary.md`. Concepts page would go at `docs/site/concepts.md`.
- From project conventions: No new runtime deps except typer (already present) and optionally griffe/mcp.
- From PRD: GitHub Action (FR111-FR113), `docvet init` (FR114-FR116) already specified in v1.0 Publish phase of PRD.
- From party-mode: Stories 30.1-30.3 are quick specs suitable for parallel execution. Story 30.4 is critical path. Stories 30.5-30.8 are independent. Existing `v1` floating tag reused for Action versioning. `docvet init` uses zero-prompt defaults with `--interactive` for agent config selection.
- Deferred from this wave: #148 (negation patterns), #160 (VS Code extension), #163 (SARIF), #265 (architecture diagrams), #72 (WebMCP).
- Epic 31 candidates: #164 (flagship runs), #158 (example project), #256 (dynamic badge).

### FR Coverage Map

| FR | Story | Description |
|----|-------|-------------|
| FR1 | 30.4 | GitHub Action runs checks on PRs |
| FR2 | 30.4 | Configurable check selection in Action |
| FR3 | 30.4 | Map findings to workflow annotation commands |
| FR4 | 30.4 | Non-zero exit on findings |
| FR5 | 30.7 | `docvet init` scaffolds pyproject.toml config |
| FR6 | 30.7 | Agent instruction snippet generation |
| FR7 | 30.7 | Non-destructive append to existing files |
| FR8 | 30.5 | Concepts page with six-layer model narrative |
| FR9 | 30.5 | Before/after showcase |
| FR10 | 30.6 | Glossary expansion for all tooltip terms |
| FR11 | 30.6 | Fix six-layer model definition (layers 1, 3-6) |
| FR12 | 30.2 | TypedDict for _RULE_CATALOG |
| FR13 | 30.1 | Scheduled uv lock --upgrade workflow |
| FR14 | 30.8 | Multi-finding prefer-fenced-code-blocks |
| FR15 | 30.3 | Copyright footer in mkdocs.yml |
| FR16 | 30.3 | License note/page on docs site |

## Epic List

### Epic 30: Distribution & Adoption

After this epic, docvet has a CI presence (GitHub Action posts findings on PRs), a frictionless onboarding path (`docvet init`), polished documentation (Concepts page, complete glossary, license attribution), cleaner internals (TypedDict, multi-finding), and automated dependency hygiene. Teams adopting docvet go from `pip install` to CI-integrated quality checks in minutes.

**FRs covered:** FR1-FR16 (all)
**Stories:** 8

**Sprint Strategy:** Stories 30.1-30.3 are quick specs suitable for parallel execution in a single session. Story 30.4 (GitHub Action) is the critical path and centerpiece. Stories 30.5-30.8 are independent and can be reordered based on velocity.

- **Story 30.1:** Scheduled uv lock upgrade workflow (FR13 + NFR8) — quick spec
- **Story 30.2:** TypedDict for _RULE_CATALOG (FR12 + NFR7) — quick spec
- **Story 30.3:** License attribution to docs site (FR15, FR16 + NFR10) — quick spec
- **Story 30.4:** GitHub Action for PR inline docstring comments (FR1-FR4 + NFR1, NFR2) — L
- **Story 30.5:** Concepts page (FR8, FR9 + NFR5) — M
- **Story 30.6:** Glossary expansion (FR10, FR11 + NFR6) — S-M
- **Story 30.7:** docvet init command (FR5-FR7 + NFR3, NFR4) — M
- **Story 30.8:** Multi-finding prefer-fenced-code-blocks (FR14 + NFR9) — M

---

## Epic 30: Distribution & Adoption

After this epic, docvet has a CI presence (GitHub Action posts findings on PRs), a frictionless onboarding path (`docvet init`), polished documentation (Concepts page, complete glossary, license attribution), cleaner internals (TypedDict, multi-finding), and automated dependency hygiene.

### Story 30.1: Scheduled uv lock upgrade workflow

As a **project maintainer**,
I want a weekly CI workflow that upgrades all dependencies and opens a PR,
So that I don't accumulate stale transitive dependencies with potential CVEs.

**Acceptance Criteria:**

**Given** the scheduled workflow triggers (weekly cron, e.g., Monday 06:00 UTC)
**When** the workflow runs on the `main` branch
**Then** it executes `uv lock --upgrade` to pull all deps to latest compatible versions
**And** uses `peter-evans/create-pull-request` to open a PR with title `chore(deps): weekly uv lock upgrade` if the lock file changed

**Given** `uv lock --upgrade` produces no changes to `uv.lock`
**When** the workflow completes
**Then** no PR is created (nothing to commit)

**Given** a dependency upgrade PR is already open from a previous run
**When** the workflow runs again with new changes
**Then** the existing PR is updated (not a duplicate) via `peter-evans/create-pull-request` branch reuse

**Given** the workflow file
**When** reviewing it
**Then** it also supports `workflow_dispatch` for manual triggering

**Implementation notes:**
- Single file: `.github/workflows/uv-lock-upgrade.yml`
- Quick spec — no code tests, CI YAML only
- Branch name: `chore/uv-lock-upgrade` (static, enables PR reuse)

### Story 30.2: TypedDict for _RULE_CATALOG

As a **developer working on the MCP module**,
I want `_RULE_CATALOG` to use a TypedDict with per-field types,
So that the type checker correctly narrows field types and `str()` wrappers in `_RULE_TO_CHECK` become unnecessary.

**Acceptance Criteria:**

**Given** the `_RULE_CATALOG` definition in `src/docvet/mcp.py`
**When** it is refactored to use a `RuleCatalogEntry` TypedDict
**Then** the TypedDict has fields: `name: str`, `check: str`, `description: str`, `category: str`, `guidance: str`, `fix_example: str | None`

**Given** the `_RULE_TO_CHECK` derivation that uses `str()` wrappers
**When** the TypedDict provides correct per-field type narrowing
**Then** the `str()` wrappers are removed as unnecessary

**Given** the existing test suite
**When** all tests run after the refactor
**Then** all tests pass unchanged (no behavior change per NFR7)

**Given** the refactored code
**When** `uv run ty check` is run
**Then** no new type errors are introduced

**Implementation notes:**
- Quick spec — ~20 lines changed in `src/docvet/mcp.py`
- Behavior-neutral refactor — existing tests are the quality gate

### Story 30.3: License attribution on docs site

As a **visitor to the docvet docs site**,
I want to see license information in the footer and a license page,
So that I can trust the project's licensing and know it's MIT-licensed.

**Acceptance Criteria:**

**Given** the `mkdocs.yml` configuration
**When** the `copyright` field is added (e.g., `Copyright &copy; 2026 Alberto-Codes — MIT License`)
**Then** every page of the docs site displays the copyright footer

**Given** the docs site
**When** a visitor looks for license information
**Then** a brief license note exists (either a standalone page or a section in an existing page) that references the MIT License and links to the LICENSE file in the repository

**Given** all documentation changes
**When** `mkdocs build --strict` is run
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Quick spec — two changes: `mkdocs.yml` copyright field + license note content
- Quality gate: `mkdocs build --strict`

### Story 30.4: GitHub Action for PR inline docstring comments

As a **team lead adding docvet to CI**,
I want a first-party GitHub Action that runs docvet on pull requests and posts inline annotations,
So that every PR gets automatic docstring quality feedback without developers running docvet locally.

**Acceptance Criteria:**

**Given** a repository using the docvet GitHub Action in a workflow
**When** a pull request is opened or updated
**Then** the Action installs docvet, runs `docvet check --format json` on the repository, and maps each finding to a GitHub workflow annotation command (`::warning file={file},line={line}::{message}`)

**Given** the Action's `checks` input is set (e.g., `checks: "enrichment,freshness"`)
**When** the Action runs
**Then** only the specified checks are executed (each check runs as a separate `docvet {check} --format json` subcommand invocation, results merged)

**Given** the Action's `checks` input is not set or set to `all`
**When** the Action runs
**Then** all enabled checks run via `docvet check --format json`

**Given** docvet finds one or more findings
**When** the Action completes
**Then** the Action exits with a non-zero exit code, causing the GitHub check to fail

**Given** docvet finds zero findings
**When** the Action completes
**Then** the Action exits with exit code 0, causing the GitHub check to pass

**Given** the repository has a `[tool.docvet]` section in pyproject.toml
**When** the Action runs
**Then** it respects the project's configuration (exclude patterns, check configs, thresholds)

**Given** the Action definition (`action.yml`)
**When** reviewing the implementation
**Then** it is a composite action (not Docker-based per NFR1) that installs docvet via `pip install docvet`, runs the CLI, and processes JSON output with a shell script

**Given** the Action input `docvet-version`
**When** a specific version is provided (e.g., `docvet-version: "1.9.0"`)
**Then** that version is installed; when omitted, the latest version is installed

**Given** the Action input `python-version`
**When** a specific version is provided (e.g., `python-version: "3.12"`)
**Then** Python is set up with that version; when omitted, a sensible default is used (e.g., `3.12`)

**Given** a developer wants to add docvet to their repo
**When** they visit the docvet README or docs site
**Then** a copy-paste workflow snippet is prominently displayed showing how to use the Action in a GitHub Actions workflow

**Implementation notes:**
- `action.yml` in repo root — composite action
- Shell script step: install docvet, run checks, parse JSON, emit `::warning` commands
- Consumers reference `Alberto-Codes/docvet@v1` (existing floating tag)
- Action inputs: `checks` (default: `all`), `docvet-version` (default: latest), `python-version` (default: `3.12`)
- Each selected check runs as a separate subcommand invocation (no `--checks` filter exists on CLI)
- Test approach: use `uses: ./` (local action reference) during development on feature branch; create a test workflow in `.github/workflows/` that exercises the action against the docvet repo itself (dogfooding)
- Ensure copy-paste workflow snippet is README-visible, not buried in docs only

### Story 30.5: Concepts page

As a **developer evaluating docvet**,
I want a Concepts page that explains why each check matters and how docvet fits in the ecosystem,
So that I understand the value proposition before diving into configuration or architecture.

**Acceptance Criteria:**

**Given** a visitor navigates the docs site
**When** they look at the navigation between Getting Started and CI Integration
**Then** a "Concepts" page exists at `docs/site/concepts.md` bridging the gap

**Given** the Concepts page content
**When** a visitor reads the "The Problem" section
**Then** it explains that docstrings lie — code changes, docstrings don't — and positions the gap between ruff (style), interrogate (presence), and actual docstring quality

**Given** the Concepts page content
**When** a visitor reads the six-layer model section
**Then** it provides a narrative walkthrough (not just the technical table from Getting Started) explaining what each layer catches with concrete examples

**Given** the Concepts page content
**When** a visitor reads the before/after showcase
**Then** it shows a realistic Python function with real docstring gaps, the docvet output, and the corrected version — the "aha moment" that converts visitors to users

**Given** the Concepts page content
**When** a visitor reads the "When to Use Each Check" section
**Then** each check has a one-paragraph explanation of its use case (enrichment for completeness, freshness for staleness, presence for coverage, coverage for mkdocs visibility, griffe for rendering)

**Given** the Concepts page content
**When** a visitor reads the ecosystem positioning
**Then** docvet is positioned as complementary to ruff and interrogate, not competitive (per NFR5)

**Given** the `mkdocs.yml` navigation
**When** the Concepts page is added
**Then** it appears between Getting Started and CI Integration in the nav

**Given** all documentation changes
**When** `mkdocs build --strict` is run
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Content sourced from `docs/product-vision.md` (internal doc with excellent narrative)
- ~200 lines of markdown
- Use a realistic function example for the before/after showcase, not a toy example
- Quality gate: `mkdocs build --strict`

### Story 30.6: Glossary expansion and layer fix

As a **developer reading the docvet docs site**,
I want all technical terms to show tooltip definitions when hovered,
So that I can understand terminology without leaving the current page.

**Acceptance Criteria:**

**Given** the glossary at `docs/site/glossary.md`
**When** Tier 1 terms are added (LSP, Fail-on, Threshold, Staged, Sweep, Pyproject.toml, Public symbol, Docstring coverage, Mode, Suppress/Ignore)
**Then** each term has a clear, concise definition that renders as a tooltip via mkdocs-material's `content.tooltips` feature

**Given** the glossary
**When** Tier 2 terms are added (Magic method/dunder, Src-root, Exclude/extend-exclude, Markdown/JSON output formats, Interrogate)
**Then** each term has a definition consistent with existing glossary style

**Given** the six-layer model glossary entry
**When** it is updated
**Then** it reflects that docvet now implements layers 1 and 3-6 (presence check covers layer 1), with a note that layers 1-2 can alternatively be handled by interrogate and ruff

**Given** the Drift mode glossary entry
**When** it is updated
**Then** it mentions both `drift-threshold` and `age-threshold`

**Given** the Hunk glossary entry
**When** it is updated
**Then** it includes context about hunk-to-symbol mapping in diff mode

**Given** all glossary changes
**When** `mkdocs build --strict` is run
**Then** the build succeeds with zero warnings

**Given** the built docs site
**When** a user hovers over any newly-defined term on any page
**Then** the tooltip appears with the glossary definition (manual verification required alongside `mkdocs build --strict` per NFR6)

**Implementation notes:**
- ~20-25 new or updated glossary entries
- Quality gate: `mkdocs build --strict` for structural correctness + manual tooltip hover verification for rendering
- Term inventory from GitHub issue #263

### Story 30.7: docvet init command

As a **Python developer adopting docvet**,
I want to run `docvet init` to scaffold configuration and agent instructions,
So that I can go from install to configured in one command instead of manually editing files.

**Acceptance Criteria:**

**Given** a user runs `docvet init` in a project with a `pyproject.toml`
**When** no `[tool.docvet]` section exists
**Then** the command appends a `[tool.docvet]` section with sensible defaults (enabled checks, no custom excludes)
**And** prints a summary of what was added

**Given** a user runs `docvet init` in a project that already has `[tool.docvet]`
**When** the existing configuration is detected
**Then** the command informs the user that configuration already exists and does not overwrite it (per FR7)

**Given** a user runs `docvet init --interactive`
**When** prompted about agent instruction snippets
**Then** the command detects which agent config files exist (CLAUDE.md, .cursorrules, .github/copilot-instructions.md) and offers to append docvet instructions to each detected file

**Given** a user runs `docvet init` (without `--interactive`)
**When** the command completes
**Then** only `pyproject.toml` configuration is added — no prompts, no agent snippets (zero-prompt defaults)

**Given** a user runs `docvet init --interactive` and selects agent snippet generation
**When** the snippet is appended to an existing agent config file (e.g., CLAUDE.md)
**Then** the content is appended (not prepended or overwritten) with a clear section header (e.g., `## Docstring Quality`)

**Given** a project with no `pyproject.toml`
**When** a user runs `docvet init`
**Then** an error message explains that `pyproject.toml` is required

**Given** the `docvet init` implementation
**When** reviewing dependencies
**Then** no new runtime dependencies are introduced — stdlib `tomllib` for reading, string formatting for writing (per NFR3)

**Implementation notes:**
- New typer subcommand in `src/docvet/cli.py`
- `tomllib` (stdlib, read-only) for detecting existing config
- String append for pyproject.toml writing (no tomli-w dependency)
- Agent snippet is a small markdown block (~5 lines) recommending `docvet check --files <changed_files>` and `docvet check --staged`
- No `--force` flag for v1 — YAGNI; users can manually edit existing config
- Tests: file I/O (pyproject.toml append), non-destructive behavior, agent config detection

### Story 30.8: Multi-finding prefer-fenced-code-blocks

As a **Python developer fixing docstring issues**,
I want `prefer-fenced-code-blocks` to report all non-fenced patterns in one pass,
So that I can fix both `>>>` doctest and `::` rST blocks in a single run instead of a whack-a-mole cycle.

**Acceptance Criteria:**

**Given** a docstring's `Examples:` section contains both `>>>` (doctest) and `::` (rST) non-fenced patterns
**When** enrichment runs the `prefer-fenced-code-blocks` check
**Then** 2 findings are returned — one for each pattern type — with distinct messages identifying the pattern type

**Given** a docstring's `Examples:` section contains only `>>>` (doctest) non-fenced pattern
**When** enrichment runs the check
**Then** 1 finding is returned for the `>>>` pattern (unchanged from current behavior)

**Given** a docstring's `Examples:` section contains only `::` (rST) non-fenced pattern
**When** enrichment runs the check
**Then** 1 finding is returned for the `::` pattern (unchanged from current behavior)

**Given** a docstring with no `>>>` or `::` patterns
**When** enrichment runs the check
**Then** zero findings are returned (unchanged from current behavior)

**Given** a docstring with multiple `>>>` blocks but no `::` patterns
**When** enrichment runs the check
**Then** 1 finding is returned (deduplicated per pattern type, not per occurrence — max 2 findings per symbol)

**Given** the `_RULE_DISPATCH` table
**When** reviewing the implementation approach
**Then** the dispatch contract (`Finding | None`) is unchanged — accumulation of multiple findings happens in `check_enrichment()` orchestrator, not in the dispatch machinery (per NFR9)

**Given** the enrichment check runs on a file with multiple symbols, each with different pattern combinations
**When** results are collected
**Then** each symbol's findings are independent — a symbol with both patterns gets 2 findings, a symbol with one pattern gets 1

**Given** the existing enrichment test suite
**When** all tests run after the change
**Then** all existing tests pass (no regressions in other rules)

**Implementation notes:**
- Approach: `_check_prefer_fenced_code_blocks` continues returning `Finding | None` (first match via dispatch). After dispatch, `check_enrichment()` does a targeted second pass for the remaining pattern type on the same symbol. This keeps dispatch contract unchanged.
- Findings are deduplicated per pattern type (max 2 per symbol: one `>>>`, one `::`)
- Tests: add multi-pattern fixtures, assert `len(findings) == 2`, verify distinct messages, add deduplication test
