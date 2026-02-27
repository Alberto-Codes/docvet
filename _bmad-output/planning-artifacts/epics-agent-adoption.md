---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - 'gh-issue-63'
  - 'gh-issue-101'
  - 'gh-issue-104'
  - 'gh-issue-151'
  - 'gh-issue-152'
  - 'gh-issue-153'
  - 'gh-issue-155'
  - 'gh-issue-156'
  - 'gh-issue-159'
  - 'gh-issue-161'
  - 'gh-issue-162'
workflowType: 'epics'
projectName: 'docvet'
featureScope: 'agent-adoption-and-distribution'
---

# docvet - Epic Breakdown: Agent Adoption & Distribution

## Overview

This document provides the epic and story breakdown for docvet's agent adoption and distribution initiative, transforming docvet from a locally-used CLI tool into a tool that AI coding agents discover, integrate, and use autonomously. The scope covers documentation, metadata, structured output, pre-commit support, cross-platform CI, LSP server, and Claude Code plugin — sourced from 11 GitHub issues prioritized by impact/effort ratio.

## Requirements Inventory

### Functional Requirements

FR128: The CLI accepts positional file arguments (`docvet check src/foo.py src/bar.py`) as an alternative to the `--files` flag, matching ruff/ty ergonomics and pre-commit conventions (#152)
FR129: The CLI supports a `--format` flag with values `text` (default, current behavior) and `json` for structured output (#151)
FR130: JSON output includes a `findings` array where each finding has: `file`, `line`, `symbol`, `rule`, `message`, `category`, `severity` (#151)
FR131: JSON output includes a `summary` object with: `total`, `by_category` counts, and `files_checked` (#151)
FR132: Exit codes are unchanged regardless of format: 0 = clean, 1 = findings (#151)
FR133: All subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) support `--format json` (#151)
FR134: A `.pre-commit-hooks.yaml` file at the repo root defines a `docvet` hook with `language: python`, `types: [python]`, and entry point that accepts positional filenames (#152)
FR135: The `docvet lsp` subcommand starts a Language Server Protocol server via STDIO using pygls (#159)
FR136: The LSP server publishes diagnostics on `textDocument/didOpen` and `textDocument/didSave` events (#159)
FR137: Each `Finding` maps to an LSP `Diagnostic` with: `line` → `range`, `message` → `message`, `rule` → `code`, `category` → `source` (#159)
FR138: Finding severity maps to LSP DiagnosticSeverity: HIGH → Error, MEDIUM → Warning, LOW → Information, suggestions → Hint (#159)
FR139: The LSP server runs enrichment, coverage, and griffe_compat checks on individual files (single-file checks only, no git context) (#159)
FR140: `pygls` is an optional dependency installable via `docvet[lsp]` (#159)
FR141: A Claude Code plugin `plugin.json` configures `docvet lsp` as an LSP server for Python files (#63)
FR142: The plugin maps `.py` files to the `python` language for LSP activation (#63)
FR143: Each of the 19 rule documentation pages includes a structured "How to Fix" section with a concrete code example showing the correct docstring (#155)
FR144: The `rules.yml` data source is extended with a `fix` field per rule, rendered automatically by rule page templates (#155)
FR145: The README includes an "AI Agent Integration" section with: CLAUDE.md snippet, pyproject.toml config example, and subcommand quick reference (#153)
FR146: The README includes a "Why docvet?" section with a comparison table showing ruff, interrogate, pydoclint, and docvet coverage across the six-layer quality model (#162)
FR147: An `AGENTS.md` file at the repo root documents docvet development conventions for cross-tool AI agent consumption (#161)
FR148: A `CONTRIBUTING.md` file at the repo root covers: dev setup, coding standards, PR process, commit conventions, and testing expectations (#104)
FR149: GitHub repository topics include agent/AI-oriented terms alongside existing topics (#156)
FR150: PyPI classifiers and keywords are audited and expanded for discoverability (#156)

### NonFunctional Requirements

NFR67: JSON output serialization adds less than 10ms overhead compared to text output for typical codebases (<100 files) (#151)
NFR68: JSON output schema is stable — field names and structure are part of the v1 API commitment (#151)
NFR69: The LSP server responds to didSave events within 500ms for typical Python files (#159)
NFR70: The LSP server has no impact when not installed — `pygls` is optional, `docvet lsp` fails gracefully with a clear message if pygls is missing (#159)
NFR71: The pre-commit hook works with pre-commit framework versions 2.x and 3.x (#152)
NFR72: Positional file arguments work identically to `--files` flag — same discovery logic, same output (#152)
NFR73: All tests pass on Ubuntu, macOS, and Windows CI runners (#101)
NFR74: Windows path separators in test assertions are handled correctly (#101)
NFR75: Git line ending differences (CRLF) do not cause false positives in freshness diff parsing (#101)
NFR76: The Claude Code plugin requires no dependencies beyond docvet itself with the `[lsp]` extra (#63)
NFR77: "How to Fix" sections use the same Google-style docstring conventions documented throughout the project (#155)
NFR78: All documentation changes (README, AGENTS.md, CONTRIBUTING.md, rule pages) follow the project's existing documentation standards (#153, #162, #161, #104)

### Additional Requirements

From Architecture:
- The `Finding` dataclass (6 fields: file, line, symbol, rule, message, category) is the shared contract for all output formats — JSON serialization must preserve all 6 fields
- Check modules are isolated — the LSP server calls check functions directly as library code, not via subprocess
- No cross-check imports — the LSP server orchestrates checks at the same level as `cli.py`
- `pygls` is the only new runtime dependency, and it is optional (`docvet[lsp]`)
- The LSP server follows the same "defensive parsers, no try/except" pattern — returns empty diagnostics on bad input

From PRD Growth & Vision (Section 239):
- JSON/SARIF output was already identified as a growth feature
- Editor/LSP integration was already identified in the vision
- Pre-commit hook was scoped in v1.0 publish phase (partially delivered — `.pre-commit-hooks.yaml` file exists in concept but positional arg support is missing)

### FR Coverage Map

FR128: Epic 23 — Positional file arguments (pre-commit prerequisite)
FR129: Epic 23 — `--format` flag with text/json values
FR130: Epic 23 — JSON findings array with all fields
FR131: Epic 23 — JSON summary object
FR132: Epic 23 — Exit codes unchanged for JSON
FR133: Epic 23 — All subcommands support `--format json`
FR134: Epic 23 — `.pre-commit-hooks.yaml` definition
FR135: Epic 24 — `docvet lsp` subcommand (pygls STDIO)
FR136: Epic 24 — Diagnostics on didOpen/didSave
FR137: Epic 24 — Finding → Diagnostic field mapping
FR138: Epic 24 — Severity → DiagnosticSeverity mapping
FR139: Epic 24 — Single-file checks in LSP (enrichment, coverage, griffe)
FR140: Epic 24 — `pygls` optional dependency (`docvet[lsp]`)
FR141: Epic 24 — Claude Code `plugin.json`
FR142: Epic 24 — `.py` → python language mapping
FR143: Epic 22 — "How to Fix" sections on all 19 rule pages
FR144: Epic 22 — `rules.yml` extended with `fix` field
FR145: Epic 22 — README "AI Agent Integration" section
FR146: Epic 22 — README "Why docvet?" comparison table
FR147: Epic 22 — `AGENTS.md` for cross-tool agent discovery
FR148: Epic 22 — `CONTRIBUTING.md` contributor guide
FR149: Epic 22 — GitHub topics (agent/AI terms)
FR150: Epic 22 — PyPI classifiers/keywords audit

## Epic List

### Epic 22: Discoverable and Understandable

A developer or AI agent searching for docstring quality tools finds docvet, instantly understands its value proposition, knows how to integrate it with their AI coding workflow, and can fix any finding by reading the rule page — all without writing a single line of code.

**FRs covered:** FR143, FR144, FR145, FR146, FR147, FR148, FR149, FR150
**NFRs addressed:** NFR77, NFR78
**Issues:** #155, #153, #162, #161, #104, #156
**Story order:** How to Fix (rules.yml schema → 19 rule pages) → README + positioning → AGENTS.md → CONTRIBUTING.md → discoverability audit

### Epic 23: Machine-Readable and Cross-Platform

Agents and CI pipelines consume docvet output as structured JSON, projects use docvet as a pre-commit hook with standard positional file args, and all of this works reliably on macOS and Windows alongside Linux. Docvet becomes a tool that integrates into any automated workflow.

**FRs covered:** FR128, FR129, FR130, FR131, FR132, FR133, FR134
**NFRs addressed:** NFR67, NFR68, NFR71, NFR72, NFR73, NFR74, NFR75
**Issues:** #101, #152, #151
**Story order:** Cross-platform CI (trust gate) → positional file args → JSON output → pre-commit hook

### Epic 24: Real-Time Diagnostics for IDEs and Agents

IDE users see docvet findings as inline squiggles and Claude Code users get automatic docstring quality diagnostics on every Python file without running any command. The LSP server makes docvet a first-class citizen in the editor, and the Claude Code plugin puts it on the marketplace.

**FRs covered:** FR135, FR136, FR137, FR138, FR139, FR140, FR141, FR142
**NFRs addressed:** NFR69, NFR70, NFR76
**Issues:** #159, #63
**Story order:** LSP server → Claude Code plugin

---

## Epic 22: Discoverable and Understandable

### Story 22.1: Add "How to Fix" Guidance to All 19 Rule Pages

As a developer or AI agent that receives a docvet finding,
I want each rule page to include a concrete "How to Fix" section with a correct code example,
So that I can resolve findings without searching for documentation conventions elsewhere.

**Acceptance Criteria:**

**Given** the `rules.yml` data source exists with entries for all 19 rules
**When** a `fix` field is added to each rule entry containing a before/after code example
**Then** every rule in `rules.yml` has a non-empty `fix` field with Google-style docstring examples

**Given** the rule page template renders rule data from `rules.yml`
**When** a rule page is generated
**Then** a "How to Fix" section appears with the `fix` content rendered as a fenced code block

**Given** all 19 rule pages are regenerated
**When** a user or agent visits any rule page (e.g., `missing-raises`, `stale-signature`, `griffe-unknown-param`, `missing-init`)
**Then** each page displays a "How to Fix" section with a concrete, correct docstring example following Google-style conventions (NFR77)

**FRs:** FR143, FR144
**Issue:** #155

---

### Story 22.2: Rewrite README with AI Agent Section and Competitive Positioning

As a developer or AI agent evaluating docstring quality tools,
I want the README to explain how to integrate docvet with AI coding workflows and how it compares to alternatives,
So that I can immediately understand docvet's value and adopt it.

**Acceptance Criteria:**

**Given** the current README exists
**When** an "AI Agent Integration" section is added
**Then** the section includes: a CLAUDE.md snippet showing recommended docvet configuration, a `pyproject.toml` config example with `[tool.docvet]`, and a subcommand quick reference table

**Given** the README is being updated
**When** a "Why docvet?" section is added
**Then** it includes a comparison table with columns for ruff, interrogate, pydoclint, and docvet, showing coverage across the six-layer quality model (presence, style, completeness, accuracy, rendering, visibility)

**Given** the updated README
**When** a developer or agent reads it
**Then** both sections follow existing documentation standards (NFR78) and the README renders correctly on GitHub and PyPI

**FRs:** FR145, FR146
**Issues:** #153, #162

---

### Story 22.3: Create AGENTS.md for Cross-Tool Agent Discovery

As an AI coding agent (Codex, Cursor, Copilot, Cline, Claude Code),
I want an `AGENTS.md` file at the repo root documenting docvet development conventions,
So that I can understand how to contribute to or use docvet without additional prompting.

**Acceptance Criteria:**

**Given** no `AGENTS.md` exists at the repo root
**When** `AGENTS.md` is created
**Then** it includes: project overview, build/test commands, architecture summary, coding conventions, commit format, and docvet-specific patterns (check module structure, Finding dataclass, defensive parser pattern)

**Given** `AGENTS.md` exists
**When** an AI agent operating in the docvet repo reads it
**Then** the agent has sufficient context to: run checks, understand module layout, follow coding style, and make contributions without reading additional files

**Given** `AGENTS.md` follows the emerging cross-tool standard
**When** Codex, Cursor, Copilot, Windsurf, or Kilo Code enters the repo
**Then** the agent discovers and reads `AGENTS.md` automatically (standard root-level file convention)

**FR:** FR147
**Issue:** #161

---

### Story 22.4: Create CONTRIBUTING.md Contributor Guide

As a human contributor or AI agent submitting a pull request,
I want a `CONTRIBUTING.md` file at the repo root with clear development setup and process documentation,
So that I can contribute effectively without trial-and-error.

**Acceptance Criteria:**

**Given** no `CONTRIBUTING.md` exists at the repo root
**When** `CONTRIBUTING.md` is created
**Then** it covers: dev setup (`uv sync --dev`), coding standards (ruff, ty, Google-style docstrings), PR process (draft PRs, squash-merge), commit conventions (conventional commits), and testing expectations (unit + integration, pytest markers)

**Given** `CONTRIBUTING.md` exists
**When** a new contributor follows its instructions
**Then** they can set up a working dev environment, run all checks, and submit a properly formatted PR

**Given** GitHub's contribution guidelines convention
**When** a user clicks "Contributing" in the GitHub UI or an agent looks for contribution instructions
**Then** GitHub surfaces `CONTRIBUTING.md` automatically (standard root-level file convention)

**FR:** FR148
**Issue:** #104

---

### Story 22.5: Audit and Expand Discoverability Metadata

As a developer searching for docstring quality tools on GitHub or PyPI,
I want docvet to appear in relevant searches through optimized topics, classifiers, and keywords,
So that I can discover docvet when looking for tools in this space.

**Acceptance Criteria:**

**Given** the current GitHub repository topics
**When** topics are audited and expanded
**Then** agent/AI-oriented terms are added (e.g., `ai-coding`, `llm-tools`, `code-quality`, `docstring-linter`) alongside existing topics

**Given** the current PyPI classifiers in `pyproject.toml`
**When** classifiers are audited
**Then** relevant classifiers are added or confirmed present (e.g., `Framework :: Pytest` if applicable, `Topic :: Software Development :: Documentation`)

**Given** the current PyPI keywords in `pyproject.toml`
**When** keywords are audited and expanded
**Then** agent/AI-oriented keywords are added (e.g., `ai-agent`, `code-review`, `static-analysis`, `pre-commit`) to improve search ranking

**FRs:** FR149, FR150
**Issue:** #156

---

## Epic 23: Machine-Readable and Cross-Platform

### Story 23.1: Cross-Platform CI Matrix (Trust Gate)

As a maintainer,
I want all tests to pass on Ubuntu, macOS, and Windows CI runners,
So that contributors on any platform can trust docvet works correctly.

**Acceptance Criteria:**

**Given** the current GitHub Actions CI workflow runs on `ubuntu-latest` only
**When** `macos-latest` and `windows-latest` are added to the CI matrix
**Then** the full test suite runs on all three platforms on every push and PR

**Given** tests contain path assertions with forward slashes
**When** tests run on Windows
**Then** path separators are handled correctly so all assertions pass (NFR74)

**Given** freshness diff parsing operates on git diff output
**When** the repository uses CRLF line endings (Windows default)
**Then** diff parsing produces identical results to LF — no false positives from line ending differences (NFR75)

**Given** the CI matrix is green on all three platforms
**When** a contributor checks CI status
**Then** all 729+ tests pass on Ubuntu, macOS, and Windows (NFR73)

**NFRs:** NFR73, NFR74, NFR75
**Issue:** #101

---

### Story 23.2: Positional File Arguments for CLI

As a developer or pre-commit hook,
I want to pass file paths as positional arguments (`docvet check src/foo.py src/bar.py`),
So that docvet matches ruff/ty ergonomics and works with pre-commit's filename convention.

**Acceptance Criteria:**

**Given** a user runs `docvet check src/foo.py src/bar.py`
**When** positional arguments are provided without the `--files` flag
**Then** docvet discovers and checks exactly those files, producing identical output to `--files src/foo.py --files src/bar.py` (NFR72)

**Given** a user runs `docvet enrichment src/foo.py`
**When** any subcommand receives positional file arguments
**Then** all subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) accept positional args

**Given** a user runs `docvet check --files src/foo.py`
**When** the existing `--files` flag is used
**Then** the flag continues to work identically (backward compatible)

**Given** both positional args and `--files` are provided
**When** the CLI parses arguments
**Then** docvet produces a clear error or merges them consistently (no silent data loss)

**FR:** FR128
**NFR:** NFR72
**Issue:** #152

---

### Story 23.3: JSON Structured Output (`--format json`)

As an AI agent or CI pipeline consuming docvet output,
I want a `--format json` flag that produces structured JSON output,
So that I can parse findings programmatically without regex on text output.

**Acceptance Criteria:**

**Given** a user runs `docvet check --format json`
**When** findings exist
**Then** stdout contains a JSON object with a `findings` array where each finding has: `file`, `line`, `symbol`, `rule`, `message`, `category`, `severity` (FR130)

**Given** a user runs `docvet check --format json`
**When** the check completes
**Then** the JSON object includes a `summary` with: `total` count, `by_category` counts, and `files_checked` count (FR131)

**Given** a user runs `docvet check --format json`
**When** findings exist
**Then** the exit code is 1; when no findings exist, exit code is 0 — identical to text mode (FR132)

**Given** a user runs any subcommand with `--format json`
**When** `enrichment`, `freshness`, `coverage`, or `griffe` is invoked
**Then** all subcommands produce the same JSON schema (FR133)

**Given** a user runs `docvet check --format text` or omits `--format`
**When** the default format is used
**Then** output is identical to current behavior (no regression)

**Given** a typical codebase of <100 files
**When** `--format json` is used instead of `--format text`
**Then** serialization adds less than 10ms overhead (NFR67)

**FRs:** FR129, FR130, FR131, FR132, FR133
**NFRs:** NFR67, NFR68
**Issue:** #151

---

### Story 23.4: Pre-Commit Hook Definition

As a project maintainer,
I want to add docvet as a pre-commit hook via a standard `.pre-commit-hooks.yaml`,
So that docstring quality is checked automatically on every commit without manual setup.

**Acceptance Criteria:**

**Given** no `.pre-commit-hooks.yaml` exists at the repo root (or the current one is incomplete)
**When** the hook definition file is created or updated
**Then** it defines a `docvet` hook with `language: python`, `types: [python]`, and an entry point that accepts positional filenames

**Given** a project adds `repo: https://github.com/Alberto-Codes/docvet` to their `.pre-commit-config.yaml`
**When** `pre-commit run --all-files` is executed
**Then** docvet runs on all Python files and reports findings

**Given** the pre-commit framework version is 2.x or 3.x
**When** the hook is installed and run
**Then** it works correctly on both major versions (NFR71)

**FR:** FR134
**NFR:** NFR71
**Issue:** #152

---

## Epic 24: Real-Time Diagnostics for IDEs and Agents

### Story 24.1: LSP Server for Real-Time Diagnostics

As an IDE user,
I want a `docvet lsp` command that starts an LSP server publishing diagnostics on open and save,
So that I see docstring quality findings as inline squiggles without running CLI commands.

**Acceptance Criteria:**

**Given** docvet is installed with the `[lsp]` extra (`pip install docvet[lsp]`)
**When** a user runs `docvet lsp`
**Then** a pygls-based LSP server starts on STDIO, ready to accept client connections (FR135)

**Given** the LSP server is running and a client opens a Python file
**When** the `textDocument/didOpen` event fires
**Then** the server publishes diagnostics for that file (FR136)

**Given** the LSP server is running and a client saves a Python file
**When** the `textDocument/didSave` event fires
**Then** the server re-runs checks and publishes updated diagnostics (FR136)

**Given** a `Finding` is produced by a check module
**When** it is converted to an LSP `Diagnostic`
**Then** `line` maps to `range`, `message` maps to `message`, `rule` maps to `code`, and `category` maps to `source` (FR137)

**Given** a Finding has a severity level
**When** it is mapped to `DiagnosticSeverity`
**Then** HIGH maps to Error, MEDIUM to Warning, LOW to Information, and suggestions to Hint (FR138)

**Given** a single Python file is opened or saved
**When** the LSP server runs checks
**Then** it runs enrichment, coverage, and griffe_compat checks on that individual file (no git context required) (FR139)

**Given** docvet is installed without the `[lsp]` extra
**When** a user runs `docvet lsp`
**Then** the command fails gracefully with a clear message explaining how to install pygls (NFR70)

**Given** a typical Python file (< 500 lines)
**When** the LSP server processes a `didSave` event
**Then** diagnostics are published within 500ms (NFR69)

**FRs:** FR135, FR136, FR137, FR138, FR139, FR140
**NFRs:** NFR69, NFR70
**Issue:** #159

---

### Story 24.2: Claude Code Plugin Configuration

As a Claude Code user,
I want a `plugin.json` that registers docvet's LSP server for Python files,
So that I get automatic docstring diagnostics in Claude Code without manual setup.

**Acceptance Criteria:**

**Given** docvet is installed with `[lsp]` extra
**When** Claude Code reads the `plugin.json` file
**Then** it discovers and starts `docvet lsp` as an LSP server for Python files (FR141)

**Given** a `.py` file is opened in Claude Code
**When** the plugin configuration is active
**Then** the file is mapped to the `python` language, triggering LSP activation (FR142)

**Given** the plugin is installed
**When** its dependencies are checked
**Then** no additional dependencies beyond `docvet[lsp]` are required (NFR76)

**FRs:** FR141, FR142
**NFR:** NFR76
**Issue:** #63
