---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-02-design-epics-phase3'
  - 'step-03-create-stories-phase3'
  - 'step-04-final-validation-phase3'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics-cli-ux.md'
  - '_bmad-output/planning-artifacts/prd-validation-report.md'
  - 'GitHub Issues: #72, #148, #149, #150, #154, #157, #158, #160, #163, #164, #176, #181, #182, #186, #187, #188, #189, #190, #191'
  - 'Phase 3 GitHub Issues (Tiers 1-3): #204, #208, #207, #206, #154, #220, #221'
---

# docvet - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for docvet, decomposing the requirements from the PRD, Architecture, CLI UX epics, and open GitHub issues into implementable stories. The project is at v1.4.0 on PyPI with all 19 rules implemented (737 tests), docs site live, and 13 epics complete (plus Epics 14-24 for LSP, CLI UX, and more). This epic breakdown covers the **next phase** of development informed by open GitHub issues.

## Requirements Inventory

### Functional Requirements

**From PRD (FR1-FR127) — All Complete:**
FR1-FR15: Section Detection (enrichment) — COMPLETE
FR16-FR22: Finding Production — COMPLETE
FR23-FR25: Rule Management — COMPLETE
FR26-FR31: Configuration — COMPLETE
FR32-FR38: Symbol Analysis — COMPLETE
FR39-FR42: Integration — COMPLETE
FR43-FR49: Diff Mode Detection (freshness) — COMPLETE
FR50-FR54: Drift Mode Detection (freshness) — COMPLETE
FR55-FR58: Freshness Edge Cases — COMPLETE
FR59-FR62: Freshness Finding Production — COMPLETE
FR63-FR65: Freshness Configuration — COMPLETE
FR66-FR68: Freshness Integration — COMPLETE
FR69-FR74: Coverage Detection — COMPLETE
FR75-FR76: Coverage Finding Production — COMPLETE
FR77-FR80: Coverage Integration — COMPLETE
FR81-FR85: Griffe Detection — COMPLETE
FR86-FR89: Griffe Finding Production — COMPLETE
FR90-FR93: Griffe Edge Cases — COMPLETE
FR94-FR97: Griffe Integration — COMPLETE
FR98-FR102: Reporting Output — COMPLETE
FR103-FR104a: Reporting File Output — COMPLETE
FR105-FR107: Exit Code Logic — COMPLETE
FR108-FR110: Reporting Integration — COMPLETE
FR111-FR113: Packaging & Distribution — COMPLETE
FR114-FR115: Pre-commit Integration — COMPLETE
FR116-FR117: GitHub Action — COMPLETE
FR118-FR120: README — COMPLETE
FR121-FR122: Documentation Site — COMPLETE
FR123-FR124: Rule Reference — COMPLETE
FR125-FR126: Dogfooding — COMPLETE
FR127: API Surface — COMPLETE

**From CLI UX Epics (FR-UX1 through FR-UX16) — NEW:**
FR-UX1: Unconditional "Vetted" summary line on stderr
FR-UX2: "Vetted" brand verb in output
FR-UX3: Check list in summary line
FR-UX4: Omit skipped checks (griffe not installed) from summary
FR-UX5: Silent overlap resolution for default warn-on
FR-UX6: Preserve warning for explicit both-set conflict
FR-UX7: Explicit-vs-default detection based on TOML key presence
FR-UX8: --verbose dual-registration (app callback + subcommand)
FR-UX9: Logical OR for verbose in both positions
FR-UX10: Verbose tier content unchanged
FR-UX11: -q/--quiet flag suppresses non-finding output
FR-UX12: Quiet preserves findings on stdout
FR-UX13: Quiet beats verbose when both specified
FR-UX14: Quiet dual-registration pattern
FR-UX15: Individual subcommands follow three-tier output model
FR-UX16: Subcommand summary with own check name only

**From GitHub Issues — NEW:**
FR-GH176: Freshness diff mode shall not produce false positives on symbols adjacent to changed hunks (tighten hunk-to-symbol mapping to changed lines only)
FR-GH186: Documentation site shall include an Editor Integration page covering LSP server, Claude Code plugin, and severity mapping
FR-GH191: CONTRIBUTING.md shall include `docs` as a valid commit scope
FR-GH181: pytestmark usage shall be standardized across all unit test files (either all have it or none)
FR-GH182: Codecov setup shall be audited — app install, codecov.yml config, and badge reliability
FR-GH187: Story creation workflow shall enforce docs-site update identification in ACs
FR-GH188: Code review workflow shall include a blocking docs-impact check
FR-GH189: CI shall detect when source files change without corresponding docs pages
FR-GH190: Docs site shall include at least one Mermaid architecture diagram
FR-GH148: Exclude configuration shall support negation patterns (!pattern)

**Phase 3 — From GitHub Issues (Tiers 1-3, 2026-02-28):**
FR-GH204: Replace nested conditional expression (S3358) in `_output_and_exit` format resolution with flat if/elif/else to clear SonarQube quality gate ERROR
FR-GH208: Add `docvet.lsp` to `_ALL_DOCVET_MODULES` list in `tests/unit/test_exports.py` so export verification includes the LSP module
FR-GH207: Update CLAUDE.md test structure tree — remove stale references to `test_freshness_diff.py`, `test_freshness_drift.py`, and `stale_signature.py` fixture
FR-GH206: Document three CLI output features in `docs/site/cli-reference.md`: progress bar (TTY vs piped), per-check `--verbose` timing, and "Vetted N files" summary format
FR-GH154: Create new docs page with agent workflow loop diagram, setup instructions, before/after examples, and CI integration guidance

**Backlog/Future (tracked but not scheduled):**
FR-GH149: MCP server for agentic AI integration
FR-GH150: `docvet init` command for agent-ready project scaffolding
FR-GH157: GitHub Action for PR inline docstring comments
FR-GH158: mkdocs-material + mkdocstrings example project template
FR-GH160: VS Code extension for docstring diagnostics
FR-GH163: SARIF output format
FR-GH164: Run docvet on flagship open-source projects
FR-GH72: Explore WebMCP integration for agent-friendly documentation

### NonFunctional Requirements

**From PRD (NFR1-NFR66) — All Complete/Applicable:**
NFR1-NFR4: Enrichment Performance — COMPLETE
NFR5-NFR9: Enrichment Correctness — COMPLETE
NFR10-NFR13: Enrichment Maintainability — COMPLETE
NFR14-NFR16: Enrichment Compatibility — COMPLETE
NFR17-NFR19: Enrichment Integration — COMPLETE
NFR20-NFR22: Freshness Performance — COMPLETE
NFR23-NFR26: Freshness Correctness — COMPLETE
NFR27-NFR28: Freshness Maintainability — COMPLETE
NFR29-NFR30: Freshness Compatibility — COMPLETE
NFR31-NFR32: Freshness Integration — COMPLETE
NFR33: Coverage Performance — COMPLETE
NFR34-NFR35: Coverage Correctness — COMPLETE
NFR36: Coverage Maintainability — COMPLETE
NFR37: Coverage Compatibility — COMPLETE
NFR38: Coverage Integration — COMPLETE
NFR39-NFR40: Griffe Performance — COMPLETE
NFR41-NFR43: Griffe Correctness — COMPLETE
NFR44-NFR45: Griffe Maintainability — COMPLETE
NFR46: Griffe Compatibility — COMPLETE
NFR47-NFR48: Griffe Integration — COMPLETE
NFR49: Reporting Performance — COMPLETE
NFR50-NFR51: Reporting Correctness — COMPLETE
NFR52-NFR53: Reporting Compatibility — COMPLETE
NFR54: Reporting Integration — COMPLETE
NFR55-NFR56: Packaging Quality — COMPLETE
NFR57-NFR58: Documentation Quality — APPLICABLE (ongoing)
NFR59-NFR60: CI Integration Quality — COMPLETE
NFR61-NFR62: v1.0 Compatibility — COMPLETE
NFR63: Dogfooding — APPLICABLE (ongoing CI gate)
NFR64-NFR66: API Stability — APPLICABLE (ongoing v1.x constraint)

**From CLI UX Epics (NFR-UX1 through NFR-UX8) — NEW:**
NFR-UX1: Summary line format stable for v1.x (scripts may parse it)
NFR-UX2: Stream separation maintained (findings stdout, metadata stderr)
NFR-UX3: Pre-commit output shows summary on stderr
NFR-UX4: GitHub Actions logs show summary clearly
NFR-UX5: No new runtime dependencies
NFR-UX6: All 729+ existing tests continue passing
NFR-UX7: --format markdown and --output work correctly with summary
NFR-UX8: Zero-file edge cases produce meaningful summary

**Phase 3 — From GitHub Issues (2026-02-28):**
NFR-NEW1: SonarQube quality gate must return to PASSED — zero new violations on main (drives FR-GH204)
NFR-NEW2: `docvet check --all` passes on own codebase with zero findings (dogfooding)
NFR-NEW3: `mkdocs build --strict` passes with zero warnings after docs changes
NFR-NEW4: All existing tests continue passing with zero regressions

### Additional Requirements

**From Architecture Document:**
- No starter template needed (brownfield project)
- Table-driven dispatch pattern for uniform-signature rule chains
- Scope-aware iterative walk for AST body-level inspection (prevents nested scope false positives)
- Finding construction uses literal rule/category strings (no dynamic computation)
- Config gating in orchestrator, not in _check_* functions
- No cross-check imports between check modules
- Checks are isolated — no shared mutable state
- All public modules define __all__ exports (API stability)

**Phase 3 — Process Improvements (2026-02-28):**
- AR-GH220: Add `analyze_code_snippet` as standard task in BMAD story template for code-changing stories — run SonarQube snippet analysis on modified functions before marking done (Source: #220, Epic 27 retro)
- AR-GH221: Document multi-layer review practice (adversarial + party mode + Copilot + codecov) as standard for non-trivial stories (Source: #221, Epic 27 retro)

**From CLI UX Research (Party Mode Session 2026-02-26):**
- "Vetted" chosen as brand verb — unique in Python tool ecosystem
- Three-tier output model (quiet/default/verbose) follows clig.dev best practices
- Config overlap warning is #1 noise source — fires 4x on common pattern
- --verbose dual-registration is standard Typer solution for placement flexibility
- Pre-commit captures stdout; GitHub Actions renders both streams

**From PRD Validation Report:**
- Overall quality rating: 5/5 Exemplary
- 130 FRs, 66 NFRs, 19 rules, 14 journeys — all complete
- Minor gaps: FR119 metric precision, dogfooding journey missing
- Zero critical gaps; document is execution-ready

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR-GH187 | 25 | Story creation DoD — enforce docs-site update identification |
| FR-GH188 | 25 | Code review docs-impact blocking check |
| FR-GH189 | 25 | CI file-mapping check for docs freshness |
| FR-GH181 | 25 | pytestmark standardization across unit tests |
| FR-GH182 | 25 | Codecov audit — app install, config, badge reliability |
| FR-GH186 | 26 | Editor Integration docs page (LSP + Claude Code plugin) |
| FR-GH190 | 26 | Mermaid architecture diagram on docs site |
| FR-GH191 | 26 | Add `docs` scope to CONTRIBUTING.md commit conventions |
| FR-GH176 | 27 | Freshness diff mode false positive fix (hunk-to-symbol tightening) |
| FR-UX1 | 28 | Unconditional "Vetted" summary line on stderr |
| FR-UX2 | 28 | "Vetted" brand verb in output |
| FR-UX3 | 28 | Check list in summary line |
| FR-UX4 | 28 | Omit skipped checks from summary |
| FR-UX5 | 28 | Silent overlap resolution for default warn-on |
| FR-UX6 | 28 | Preserve warning for explicit both-set conflict |
| FR-UX7 | 28 | Explicit-vs-default detection based on TOML key presence |
| FR-UX8 | 28 | --verbose dual-registration |
| FR-UX9 | 28 | Logical OR for verbose in both positions |
| FR-UX10 | 28 | Verbose tier content unchanged |
| FR-UX11 | 28 | -q/--quiet flag suppresses non-finding output |
| FR-UX12 | 28 | Quiet preserves findings on stdout |
| FR-UX13 | 28 | Quiet beats verbose when both specified |
| FR-UX14 | 28 | Quiet dual-registration pattern |
| FR-UX15 | 28 | Individual subcommands follow three-tier output model |
| FR-UX16 | 28 | Subcommand summary with own check name only |
| FR-GH204 | Standalone fix | Replace nested ternary — SonarQube S3358 (ships outside epic) |
| FR-GH208 | 29 | Add docvet.lsp to test_exports.py |
| FR-GH207 | 29 | Update CLAUDE.md test structure |
| AR-GH220 | 29 | Add snippet analysis to story template |
| AR-GH221 | 29 | Document multi-layer review practice |
| FR-GH206 | 29 | CLI reference — progress, timing, summary |
| FR-GH154 | 29 | Agent workflow docs page |
| FR-GH148 | Backlog | Negation pattern support for exclude config |
| FR-GH149 | Backlog | MCP server for agentic AI integration |
| FR-GH150 | Backlog | `docvet init` command |
| FR-GH157 | Backlog | GitHub Action for PR inline comments |
| FR-GH158 | Backlog | mkdocs + mkdocstrings example template |
| FR-GH160 | Backlog | VS Code extension |
| FR-GH163 | Backlog | SARIF output format |
| FR-GH164 | Backlog | Run docvet on flagship OSS projects |
| FR-GH72 | Backlog | WebMCP integration |

## Epic List

### Standalone Fix (pre-epic): fix(cli) nested ternary — #204
SonarQube quality gate ERROR (S3358). Ships immediately as a standalone PR, not wrapped in epic ceremony.
**FRs covered:** FR-GH204

### Epic 29: Post-Launch Polish
Maintainers and contributors work with complete test coverage, accurate project documentation, improved development process, and users find accurate CLI reference plus a clear agent workflow guide.
**FRs covered:** FR-GH208, FR-GH207, AR-GH220, AR-GH221, FR-GH206, FR-GH154
**GitHub Issues:** #208, #207, #220, #221, #206, #154

### Epic 25: Development Process & CI Quality
The development process prevents documentation drift and CI provides reliable, consistent quality signals. BMAD workflows enforce docs-site updates at story creation and code review time, CI detects source-without-docs changes, and testing/coverage infrastructure is standardized.
**FRs covered:** FR-GH187, FR-GH188, FR-GH189, FR-GH181, FR-GH182
**GitHub Issues:** #187, #188, #189, #181, #182

## Epic 25: Development Process & CI Quality

The development process prevents documentation drift and CI provides reliable, consistent quality signals. BMAD workflows enforce docs-site updates at story creation and code review time, CI detects source-without-docs changes, and testing/coverage infrastructure is standardized.

### Story 25.1: Standardize pytestmark Usage

As a **docvet contributor**,
I want pytestmark usage to be consistent across all unit test files,
So that test organization follows a clear convention and marker-based filtering works reliably if adopted.

**FRs covered:** FR-GH181

**Acceptance Criteria:**

AC 1:
**Given** the 13 unit test files (5 with `pytestmark`, 8 without)
**When** the convention decision is made
**Then** all unit test files either have `pytestmark = pytest.mark.unit` or none do — no split

AC 2:
**Given** the standardization decision
**When** applied to test files
**Then** `uv run pytest` passes with all 737+ tests green

AC 3:
**Given** the decision on whether to adopt or remove markers
**When** documented
**Then** `.github/instructions/pytest.instructions.md` includes the convention and rationale

AC 4:
**Given** markers are adopted (if that's the decision)
**When** a contributor checks CLAUDE.md or pytest instructions
**Then** `pytest -m unit` and `pytest -m integration` usage is documented

**Implementation notes:**
- Issue #181 lists all 13 files and their current state
- Decision point: does marker filtering provide value? CI runs `uv run pytest` without `-m` filtering today
- If removing: delete `pytestmark` from the 5 files that have it
- If adopting: add `pytestmark = pytest.mark.unit` to the 8 files missing it, add `pytestmark = pytest.mark.integration` to integration test files

---

### Story 25.2: Audit and Configure Codecov

As a **docvet maintainer**,
I want Codecov properly configured with reliable PR comments and badge updates,
So that coverage feedback is consistent and contributors see coverage impact on every PR.

**FRs covered:** FR-GH182

**Acceptance Criteria:**

AC 1:
**Given** the Codecov GitHub App is not installed
**When** the audit is complete
**Then** a decision is documented on whether to install the App (yes/no with rationale)

AC 2:
**Given** no `codecov.yml` exists
**When** the audit recommends adding one
**Then** `codecov.yml` is committed with project/patch coverage targets and PR comment configuration

AC 3:
**Given** the README badge `[![Coverage](https://codecov.io/gh/...)]`
**When** the badge strategy is decided
**Then** the badge updates reliably on pushes to main

AC 4:
**Given** a PR is opened against main
**When** CI runs and uploads coverage
**Then** Codecov PR comments appear consistently showing coverage delta

AC 5:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass

**Implementation notes:**
- Issue #182 details 5 decision points: App install, codecov.yml, components vs flags, badge strategy, `--cov-fail-under` location
- Components (free for OSS) can track coverage by area without splitting uploads
- Flags require separate pytest+upload steps in CI — evaluate cost vs benefit

---

### Story 25.3: Enforce Docs Updates in Story Creation

As a **docvet contributor using the BMAD story creation workflow**,
I want the workflow to require identification of affected docs pages in acceptance criteria,
So that documentation updates are planned alongside code changes, not forgotten after.

**FRs covered:** FR-GH187

**Acceptance Criteria:**

AC 1:
**Given** the BMAD create-story workflow (`_bmad/bmm/workflows/4-implementation/create-story/`)
**When** a story touches user-facing behavior
**Then** the workflow requires listing specific docs pages to update (e.g., "update `docs/site/cli.md`") as concrete ACs

AC 2:
**Given** a story that does NOT touch user-facing behavior (e.g., internal refactor, test-only)
**When** the workflow processes the story
**Then** the docs requirement is acknowledged as "N/A — no user-facing changes" rather than silently skipped

AC 3:
**Given** the updated workflow
**When** a contributor runs `/bmad-bmm-create-story`
**Then** the docs-page identification step appears as an explicit gate, not a suggestion

**Implementation notes:**
- Issue #187: direct process update to BMAD workflow configuration
- The requirement is for concrete page names, not vague "update docs if needed"
- Source: Epic 22 retrospective action item 1

---

### Story 25.4: Add Docs-Impact Check to Code Review

As a **code reviewer using the BMAD code review workflow**,
I want the workflow to flag when source files changed without corresponding docs updates,
So that documentation drift is caught during review, not after shipping.

**FRs covered:** FR-GH188

**Acceptance Criteria:**

AC 1:
**Given** the BMAD code-review workflow (`_bmad/bmm/workflows/4-implementation/code-review/`)
**When** source files in `src/docvet/` are modified in the PR
**Then** the workflow includes a blocking check: "Were corresponding docs pages updated?"

AC 2:
**Given** a PR that modifies user-facing behavior without touching docs
**When** the code review runs
**Then** the docs-impact gap is flagged as a finding (not just a suggestion)

AC 3:
**Given** a PR that modifies only tests, CI, or internal tooling
**When** the code review runs
**Then** no docs-impact finding is produced (internal changes don't require docs updates)

**Implementation notes:**
- Issue #188: direct process update to BMAD workflow configuration
- This is a gate, not a suggestion — if user-facing behavior changed and no docs were touched, it's a finding
- Source: Epic 22 retrospective action item 2

---

### Story 25.5: Investigate CI Docs-Freshness Check

As a **docvet maintainer**,
I want a CI check that warns when source files change without corresponding docs pages being updated,
So that documentation drift is caught automatically as a belt-and-suspenders complement to process enforcement.

**FRs covered:** FR-GH189

**Acceptance Criteria:**

AC 1:
**Given** a source-to-docs mapping concept (e.g., `cli.py` → `docs/site/cli.md`)
**When** the spike is complete
**Then** a proof-of-concept mapping file or configuration exists in the repository

AC 2:
**Given** the PoC mapping
**When** a PR modifies a mapped source file but not the corresponding docs file
**Then** the CI check produces a warning (not a blocking failure for the initial spike)

AC 3:
**Given** the PoC CI check
**When** evaluated against the last 5 merged PRs
**Then** the false positive rate and maintainability are documented with a recommendation on whether to adopt

AC 4:
**Given** the spike is complete
**When** the recommendation is "adopt"
**Then** the mapping file format and CI integration approach are documented for promotion to a real story in a future epic

**Implementation notes:**
- Issue #189: this is a spike — success is a recommendation with evidence, not necessarily a production-ready CI check
- Lightweight approach: YAML/JSON mapping file checked in CI via a shell script comparing `git diff` file lists
- Source: Epic 22 retrospective action item 3

---

## Epic 26: Documentation Completeness

Users and contributors find complete, accurate information — editor setup for LSP and Claude Code plugin, architecture overview via Mermaid diagrams, and contribution conventions with `docs` scope are all documented.

### Story 26.1: Add `docs` Scope to CONTRIBUTING.md

As a **docvet contributor**,
I want `docs` listed as a valid commit scope in CONTRIBUTING.md,
So that documentation-only commits follow the same conventions as code commits.

**FRs covered:** FR-GH191

**Acceptance Criteria:**

AC 1:
**Given** the commit conventions section in CONTRIBUTING.md
**When** updated
**Then** `docs` appears in the list of valid scopes

AC 2:
**Given** the updated CONTRIBUTING.md
**When** a contributor reads the conventions
**Then** usage examples show `docs` scope (e.g., `docs(rules): add missing-raises reference page`)

**Implementation notes:**
- Issue #191: trivial fix — direct edit to CONTRIBUTING.md
- Source: Epic 22 story 22.4 deferred code review finding

---

### Story 26.2: Add Editor Integration Page

As a **developer setting up docvet in their editor**,
I want a docs page explaining LSP server configuration and Claude Code plugin installation,
So that I can get real-time docstring diagnostics without reading source code.

**FRs covered:** FR-GH186

**Acceptance Criteria:**

AC 1:
**Given** the docs site
**When** a user navigates to the Editor Integration page
**Then** the page documents the `docvet lsp` command, which checks run (enrichment, coverage, griffe — not freshness), and how to configure in any LSP-capable editor

AC 2:
**Given** the Editor Integration page
**When** a user reads the Claude Code plugin section
**Then** the install command (`claude plugin install github:Alberto-Codes/docvet`), prerequisites (`pip install docvet[lsp]`), and expected diagnostics are documented

AC 3:
**Given** the Editor Integration page
**When** a user reads the severity mapping section
**Then** the mapping is documented: required rules → Warning, recommended rules → Hint

AC 4:
**Given** the Editor Integration page
**When** a user looks for VS Code support
**Then** a reference to issue #160 (future) is included as a planned enhancement

AC 5:
**Given** the updated docs site
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Issue #186: references `src/docvet/lsp.py`, `.claude-plugin/plugin.json`, `.claude-plugin/README.md`, `.lsp.json`
- Add page to `mkdocs.yml` nav and link from existing AI Integration page

---

### Story 26.3: Add Architecture Diagram to Docs Site

As a **docvet contributor or evaluator**,
I want a Mermaid architecture diagram on the docs site showing the system structure,
So that I can quickly understand how the modules, checks, and CLI fit together.

**FRs covered:** FR-GH190

**Acceptance Criteria:**

AC 1:
**Given** the docs site
**When** a user navigates to the architecture section
**Then** at least one Mermaid diagram is rendered showing the system architecture (modules, data flow, or component relationships)

AC 2:
**Given** the Mermaid diagram source
**When** inspected in the repository
**Then** it lives alongside the docs content (not generated externally)

AC 3:
**Given** the diagram
**When** rendered on the published docs site
**Then** it renders correctly via mkdocs-material's built-in Mermaid support

AC 4:
**Given** the updated docs site
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings

AC 5:
**Given** the project's Mermaid guidelines (`.claude/rules/mermaid.md`)
**When** the diagram is reviewed
**Then** it follows the guidelines: standard flowchart syntax (no C4 native syntax), `<br>` for line breaks, under 20 nodes, meaningful shapes

**Implementation notes:**
- Issue #190: proof-of-concept, not exhaustive — one diagram showing the check pipeline or module relationships
- mkdocs-material has built-in Mermaid support via `pymdownx.superfences` — no external tools needed
- Follow `.claude/rules/mermaid.md` conventions

---

### Story 26.4: Research Auto-Generated Mermaid Diagrams

As a **docvet maintainer**,
I want to understand what tools or patterns exist for auto-generating Mermaid diagrams from Python codebases,
So that architecture diagrams can stay current with the code automatically rather than requiring manual updates.

**FRs covered:** (user-requested research — no existing FR)

**Acceptance Criteria:**

AC 1:
**Given** the Python ecosystem
**When** researched
**Then** a summary documents at least 3 approaches or tools for auto-generating Mermaid diagrams from Python code (e.g., AST-based module dependency graphs, import analysis, class hierarchy extraction)

AC 2:
**Given** the research results
**When** evaluated against docvet's codebase
**Then** each approach is assessed for: compatibility with Google-style docstrings, ability to leverage existing AST infrastructure (`ast_utils.py`), output quality, and maintenance burden

AC 3:
**Given** docvet's own docstrings and module structure
**When** a proof-of-concept is attempted with the most promising approach
**Then** a sample auto-generated Mermaid diagram is produced and compared against the manual diagram from Story 26.3

AC 4:
**Given** the research is complete
**When** summarized
**Then** a recommendation is documented: adopt (with which tool/pattern), defer (promising but not worth it now), or skip (no viable approach)

**Implementation notes:**
- Areas to explore: `py2mermaid`, `pydeps`, `pyreverse` (pylint), custom AST walkers using docvet's own `ast_utils`, or griffe's object model as a diagram source
- Interesting angle: docvet's enrichment rules already parse docstrings for sections — could the same infrastructure feed a diagram generator?
- This is a spike — deliverable is a recommendation with evidence, not a production feature
- Not a hard dependency on Story 26.3 — the manual diagram ships regardless

---

## Epic 27: Freshness Accuracy

Developers trust freshness check results — unchanged symbols adjacent to modified code no longer produce false positives. Hunk-to-symbol mapping tightened to changed lines only, excluding git diff context lines.

### Story 27.1: Fix Hunk-to-Symbol False Positives

As a **developer running `docvet freshness`**,
I want unchanged symbols adjacent to modified code to not be flagged as stale,
So that I can trust freshness results without manually dismissing false positives.

**FRs covered:** FR-GH176

**Acceptance Criteria:**

AC 1:
**Given** a file where a new function is added immediately above an existing function
**When** `docvet freshness` runs on the diff
**Then** the existing function below the insertion point produces zero freshness findings (its code and docstring are unchanged)

AC 2:
**Given** a file where an import is added to the import block
**When** the import block change creates a diff hunk whose context overlaps with an adjacent class definition
**Then** the adjacent class produces zero freshness findings

AC 3:
**Given** a file where a new constant is added above an existing function
**When** the diff context lines extend into the function's definition region
**Then** the existing function produces zero freshness findings

AC 4:
**Given** a symbol whose signature genuinely changed (parameter added/removed/renamed)
**When** `docvet freshness` runs
**Then** the symbol is still correctly flagged as `stale-signature` (HIGH severity) — only false positives are eliminated, not true positives

AC 5:
**Given** the hunk-to-symbol mapping implementation
**When** inspecting changed lines within a hunk
**Then** only `+`/`-` lines (additions/deletions) are mapped to symbols — context lines (` ` prefix) are excluded from symbol matching

AC 6:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass
**And** existing freshness unit and integration tests continue to verify true positive detection

AC 7:
**Given** `docvet check --all` runs on docvet's own codebase
**When** the command completes
**Then** zero false positive freshness findings are produced

**Implementation notes:**
- Issue #176: root cause is that git's unified diff includes 3 context lines above/below each change; when a change occurs near a symbol boundary, context lines bleed into adjacent symbols
- Fix approach: in the hunk-to-symbol mapping logic, distinguish `+`/`-` lines from ` ` (context) lines — only map changed lines to symbols
- Affected code: `src/docvet/checks/freshness.py` hunk parsing and line-to-symbol mapping
- The 3 false positive examples from issue #176 (`FreshnessMode`, `format_summary`, `format_markdown`) should inform regression test cases

---

## Epic 28: CLI Output & User Experience

A developer running docvet in any context — terminal, CI, pre-commit, GitHub Actions — gets clear, brand-consistent feedback about what was vetted and what was found, using a three-tier output model (quiet/default/verbose) with the "Vetted" brand verb.

### Story 28.1: Default Output Overhaul

As a **developer running docvet for the first time**,
I want to see a clear summary of what was checked and whether my docs are clean,
So that I immediately understand the result without needing verbose mode or guessing from exit codes.

**FRs covered:** FR-UX1, FR-UX2, FR-UX3, FR-UX4

**Acceptance Criteria:**

AC 1:
**Given** `docvet check --all` runs on a codebase with zero findings
**When** the command completes
**Then** stderr contains a summary line matching the format: `Vetted {N} files [{checks}] — no findings. ({elapsed}s)`
**And** the check list includes only checks that actually ran (e.g., `griffe` omitted if not installed)

AC 2:
**Given** `docvet check --all` runs on a codebase with findings
**When** the command completes
**Then** stdout contains the finding lines (unchanged format)
**And** stderr contains a summary line: `Vetted {N} files [{checks}] — {count} findings ({required} required, {recommended} recommended). ({elapsed}s)`

AC 3:
**Given** `docvet check --all` runs with `--format markdown` or `--output report.md`
**When** the command completes
**Then** the summary line still appears on stderr (not in the markdown output or file)

AC 4:
**Given** zero files are discovered (empty repo or all excluded)
**When** the command completes
**Then** the summary line reads: `Vetted 0 files [{checks}] — no findings. ({elapsed}s)`

AC 5:
**Given** griffe is not installed
**When** `docvet check --all` runs
**Then** the check list in the summary omits `griffe` (e.g., `[enrichment, freshness, coverage]`)

AC 6:
**Given** the existing `Completed in Xs` output on stderr (`cli.py:615`)
**When** the summary line is implemented
**Then** the `Completed in Xs` line is **replaced** by the summary line (not duplicated)
**And** the timing information is embedded in the summary line's `({elapsed}s)` suffix

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass (existing output assertions updated as needed in this story for the `check` command only)

**Implementation notes:**
- Add `format_summary(file_count, checks, findings, elapsed)` to `reporting.py`
- Replace `cli.py:615` (`sys.stderr.write(f"Completed in {total_elapsed:.1f}s\n")`) with `sys.stderr.write(format_summary(...))`
- The `if verbose and not all_findings: sys.stdout.write("No findings.\n")` at `cli.py:259` can be removed — the summary line covers this
- The `format_verbose_header` function remains for verbose mode (separate concern, Story 28.3)

---

### Story 28.2: Config Warning Cleanup

As a **developer who set `fail-on` in their config**,
I want docvet to silently resolve the overlap with default `warn-on` values,
So that I don't see confusing warnings about a conflict I didn't create.

**FRs covered:** FR-UX5, FR-UX6, FR-UX7

**Acceptance Criteria:**

AC 1:
**Given** `pyproject.toml` with `fail-on = ["enrichment", "freshness", "coverage", "griffe"]` and no `warn-on` key
**When** docvet loads the configuration
**Then** the overlap between `fail-on` and default `warn-on` is resolved silently — zero warnings on stderr
**And** the resolved `warn-on` list is empty (all four checks promoted to fail-on)

AC 2:
**Given** `pyproject.toml` with `fail-on = ["enrichment"]` and no `warn-on` key
**When** docvet loads the configuration
**Then** zero warnings on stderr
**And** the resolved `warn-on` list is `["freshness", "griffe", "coverage"]` (defaults minus overlap)

AC 3:
**Given** `pyproject.toml` with both `fail-on = ["enrichment"]` and `warn-on = ["enrichment", "freshness"]` (explicit overlap)
**When** docvet loads the configuration
**Then** a warning is emitted: `docvet: 'enrichment' appears in both fail-on and warn-on; using fail-on`
**And** only the overlapping check produces a warning (one warning, not four)

AC 4:
**Given** `pyproject.toml` with neither `fail-on` nor `warn-on` set
**When** docvet loads the configuration
**Then** zero warnings on stderr (defaults don't conflict with themselves)

AC 5:
**Given** the detection mechanism for "user explicitly set" vs "default value"
**When** inspecting the implementation
**Then** detection is based on key presence in the parsed TOML `[tool.docvet]` section (checking if `"warn-on"` or `"warn_on"` key exists), not on value comparison

AC 6:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass (config test assertions updated for new warning behavior)

**Implementation notes:**
- In `config.py:load_config`, track whether `warn_on` was explicitly set: `warn_on_explicit = "warn_on" in parsed or "warn-on" in raw_section`
- Only emit overlap warnings when `warn_on_explicit is True`
- The overlap resolution logic (stripping from warn_on, fail_on wins) remains unchanged

---

### Story 28.3: Verbose & Quiet Flag Redesign

As a **developer using docvet in different contexts**,
I want `--verbose` to work after the subcommand name and a `--quiet` flag for minimal output,
So that I can control output verbosity naturally without memorizing flag ordering.

**FRs covered:** FR-UX8, FR-UX9, FR-UX10, FR-UX11, FR-UX12, FR-UX13, FR-UX14

**Acceptance Criteria:**

AC 1:
**Given** the `check` subcommand
**When** a user runs `docvet check --all --verbose`
**Then** the command succeeds with verbose output (per-check timing, file discovery, verbose header)
**And** the behavior is identical to `docvet --verbose check --all`

AC 2:
**Given** the `check` subcommand
**When** a user runs `docvet --verbose check --all --verbose` (both positions)
**Then** the command succeeds with verbose output (logical OR — both positions produce verbose)

AC 3:
**Given** the `check` subcommand
**When** a user runs `docvet check --all -q`
**Then** no summary line, timing, or config messages appear on stderr
**And** if there are findings, they still appear on stdout
**And** exit code reflects findings as usual

AC 4:
**Given** the `check` subcommand
**When** a user runs `docvet check --all -q --verbose` (both quiet and verbose)
**Then** quiet wins — no non-finding output on stderr

AC 5:
**Given** verbose mode is active
**When** `docvet check --all --verbose` runs
**Then** stderr shows (in order): file discovery count, per-check timing lines, summary line
**And** the summary line format is the same as default mode (from Story 28.1)

AC 6:
**Given** the `--verbose` and `-q`/`--quiet` flags
**When** inspecting the CLI help output for `docvet check --help`
**Then** both flags appear as options on the subcommand (not just on the app)

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass

**Implementation notes:**
- Add `verbose` and `quiet` parameters to `check` command signature with `typer.Option`
- Resolve in function body: `verbose = verbose or ctx.obj.get("verbose", False)`, `quiet = quiet or ctx.obj.get("quiet", False)`
- Gate summary line: `if not quiet: sys.stderr.write(format_summary(...))`
- Gate verbose output: `if verbose and not quiet: sys.stderr.write(...)`
- Apply same pattern to app callback for `-q`/`--quiet`

---

### Story 28.4: Subcommand Output Parity

As a **developer running a single docvet check**,
I want the individual subcommands (`enrichment`, `freshness`, `coverage`, `griffe`) to show the same summary format as `check`,
So that the output experience is consistent regardless of which command I use.

**FRs covered:** FR-UX15, FR-UX16

**Acceptance Criteria:**

AC 1:
**Given** `docvet enrichment --all` runs with zero findings
**When** the command completes
**Then** stderr shows: `Vetted {N} files [enrichment] — no findings. ({elapsed}s)`

AC 2:
**Given** `docvet freshness --all` runs with findings
**When** the command completes
**Then** stderr shows: `Vetted {N} files [freshness] — {count} findings (...). ({elapsed}s)`
**And** findings appear on stdout

AC 3:
**Given** `docvet coverage --all` runs
**When** the command completes
**Then** stderr shows the summary line with `[coverage]` in the check list

AC 4:
**Given** `docvet griffe --all` runs with griffe installed
**When** the command completes
**Then** stderr shows the summary line with `[griffe]` in the check list

AC 5:
**Given** any individual subcommand with `--verbose` flag (in either position)
**When** the command completes
**Then** verbose-tier output appears (per-check timing, file count) followed by the summary line

AC 6:
**Given** any individual subcommand with `-q` flag
**When** the command completes
**Then** quiet-tier behavior applies (no summary, findings-only on stdout)

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass

**Implementation notes:**
- Each `_run_*` subcommand function (`enrichment`, `freshness`, `coverage`, `griffe` in `cli.py`) currently has its own output handling
- Refactor to share the `format_summary` call with appropriate single-check name
- Apply the same `verbose`/`quiet` dual-registration pattern from Story 28.3

---

### Story 28.5: Test Migration & Documentation

As a **docvet contributor**,
I want all tests updated for the new output format and docs reflecting the three-tier model,
So that the test suite is green, docs are accurate, and future contributors understand the output design.

**Acceptance Criteria:**

AC 1:
**Given** any integration tests that assert on CLI output (e.g., checking for `Completed in`)
**When** updated for the new output format
**Then** assertions match the `Vetted N files [...]` summary line format
**And** all tests pass

AC 2:
**Given** the CLI Reference documentation page (`docs/site/cli-reference.md`)
**When** updated
**Then** it documents the three output tiers (quiet/default/verbose) with examples for each
**And** it documents the `-q`/`--quiet` flag and the `--verbose` dual-registration behavior
**And** example output uses the `Vetted` summary format

AC 3:
**Given** the CI Integration documentation page (`docs/site/ci-integration.md`)
**When** updated
**Then** it shows example GitHub Actions log output with the new summary format
**And** it shows example pre-commit output with the new summary format
**And** it documents the `-q` flag as useful for scripted/piped contexts

AC 4:
**Given** the Getting Started documentation page (`docs/site/getting-started.md`)
**When** updated
**Then** the quickstart example output matches the new default format

AC 5:
**Given** edge case tests
**When** the following scenarios are tested
**Then** each produces correct output:
- Zero files discovered → `Vetted 0 files [...] — no findings.`
- Griffe not installed → check list omits `griffe`
- `--format markdown` → summary on stderr, markdown on stdout/file
- `--output report.md` → summary on stderr, findings in file
- `--staged` with zero staged files → `Vetted 0 files [...]`
- Both `-q` and `--verbose` → quiet wins
- `--verbose` in both positions → verbose active

AC 6:
**Given** all changes across Stories 28.1–28.5
**When** `uv run pytest` is executed
**Then** all tests pass with zero failures
**And** `docvet check --all` on docvet's own codebase shows the new summary format

AC 7:
**Given** the docs site with updated pages
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Stories 28.1-28.4 each update tests for their own scope; this story catches any remaining test migrations and handles all docs updates
- Edge case tests may already exist from prior stories — this story ensures comprehensive coverage

---

## Standalone Fix (pre-epic): fix(cli) nested ternary — #204

SonarQube quality gate ERROR (S3358). Ships immediately as a standalone PR:

> **fix(cli): replace nested ternary in `_output_and_exit` format resolution**
> Replace nested conditional at `cli.py:338` with flat if/elif/else. Closes #204. Quality gate returns to PASSED.

**FRs covered:** FR-GH204

---

## Epic 29: Post-Launch Polish

Maintainers and contributors work with complete test coverage, accurate project documentation, improved development process, and users find accurate CLI reference plus a clear agent workflow guide.

### Story 29.1: Test & Documentation Hygiene

As a **docvet contributor**,
I want the test export coverage to include all public modules and the CLAUDE.md test structure to reflect the current codebase,
So that AI agents and contributors get accurate project context.

**FRs covered:** FR-GH208, FR-GH207

**Acceptance Criteria:**

AC 1:
**Given** the `_ALL_DOCVET_MODULES` list in `tests/unit/test_exports.py`
**When** `uv run pytest tests/unit/test_exports.py` is run before any changes
**Then** confirm the export test fails or is incomplete for `docvet.lsp` (verify gap exists)
**And** after adding `docvet.lsp` to the list, the test passes

AC 2:
**Given** the Architecture → Test Structure section in `CLAUDE.md`
**When** updated
**Then** stale references to `test_freshness_diff.py`, `test_freshness_drift.py`, and `stale_signature.py` fixture are removed
**And** the tree reflects the current `tests/` directory structure

AC 3:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass with zero regressions

**Implementation notes:**
- #208: add one string (`"docvet.lsp"`) to the module list
- #207: run `find tests/` to get current tree, replace the markdown block in CLAUDE.md
- Single PR, single commit

---

### Story 29.2: Development Process Updates

As a **docvet contributor using BMAD workflows**,
I want the story template to include SonarQube snippet analysis as a standard task and the multi-layer review practice to be documented,
So that quality issues are caught earlier in the development cycle and review practices are consistent.

**FRs covered:** AR-GH220, AR-GH221

**Acceptance Criteria:**

AC 1:
**Given** the BMAD dev-story workflow at `_bmad/bmm/workflows/4-implementation/dev-story/`
**When** the post-implementation quality checks step is updated
**Then** the step includes a task to run `analyze_code_snippet` on modified functions before marking the story done

AC 2:
**Given** the multi-layer review practice (adversarial review + party mode + Copilot PR review + codecov)
**When** documented as a new file at `.claude/rules/review-practice.md`
**Then** the file describes the four review layers, when to apply them (non-trivial stories), and the evidence that each layer catches distinct issue categories with zero overlap

AC 3:
**Given** the updated workflow
**When** a contributor runs `/bmad-bmm-dev-story`
**Then** the SonarQube analysis step appears in the workflow execution

**Implementation notes:**
- #220: edit the appropriate step file in `_bmad/bmm/workflows/4-implementation/dev-story/steps/`
- #221: create `.claude/rules/review-practice.md` with the four-layer review practice
- Single PR covering both template/process changes

---

### Story 29.3: CLI Reference Documentation Update

As a **docvet user reading the CLI reference**,
I want the docs to accurately describe progress bar behavior, per-check timing, and the vetted summary format,
So that I understand what output to expect in different contexts (TTY, piped, verbose).

**FRs covered:** FR-GH206

**Acceptance Criteria:**

AC 1:
**Given** `docs/site/cli-reference.md`
**When** updated
**Then** it documents progress bar behavior: displays on stderr when connected to a TTY, suppressed when piped or redirected

AC 2:
**Given** the CLI reference
**When** a user reads the verbose mode section
**Then** per-check timing is documented (e.g., `enrichment: 42 files in 0.3s`)
**And** total execution time in the summary line is documented

AC 3:
**Given** the CLI reference
**When** a user reads the output section
**Then** the vetted summary line format is documented, captured from a real `docvet check --all` run against the current released CLI (v1.6.1+)

AC 4:
**Given** the updated docs site
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings

**Implementation notes:**
- #206: three features from Epics 20-21 (progress bar PR #139, per-check timing PR #140, vetted summary PR #141) — all shipped in v1.6.x
- Document current released behavior; run `docvet check --all` to capture actual output
- Single page edit, no new pages needed

---

### Story 29.4: Agent Workflow Documentation Page

As a **developer evaluating docvet for AI-assisted workflows**,
I want a dedicated docs page showing exactly where docvet fits in the agent development loop,
So that I can set up docvet in my project and configure my AI agent to use it effectively.

**FRs covered:** FR-GH154

**Acceptance Criteria:**

AC 1:
**Given** the docs site navigation
**When** a user browses the top-level nav
**Then** an "Agent Workflow" page is visible, placed after the AI Agent Integration page in `mkdocs.yml`

AC 2:
**Given** the agent workflow page
**When** a user reads the workflow section
**Then** a Mermaid diagram illustrates the loop: code change → `docvet check` → read findings → fix docstrings → commit clean
**And** the diagram follows `.claude/rules/mermaid.md` conventions and uses styling consistent with the existing `docs/site/architecture.md` diagram

AC 3:
**Given** the agent workflow page
**When** a user reads the setup section
**Then** instructions cover pyproject.toml `[tool.docvet]` configuration and at minimum a CLAUDE.md agent instruction snippet, with optional examples for other agents (Cursor, Copilot) if tested

AC 4:
**Given** the agent workflow page
**When** a user reads the examples section
**Then** at least one before/after example shows: agent changes a function signature, docvet catches stale docstring, agent fixes it

AC 5:
**Given** the agent workflow page
**When** a user reads the CI section
**Then** GitHub Actions integration is documented showing how `docvet check` catches agent-generated PRs with docstring issues

AC 6:
**Given** the updated docs site
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings

**Implementation notes:**
- #154: creative deliverable — new page, not an edit
- Add to mkdocs.yml nav after AI Agent Integration
- Follow `.claude/rules/mermaid.md` for diagram styling; reference `docs/site/architecture.md` for visual consistency
- Cross-link from existing AI Agent Integration page
