---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - "GitHub issues (triaged in session: #149, #227, #232, #236)"
  - "Party mode consensus on presence check architecture"
  - "_bmad-output/planning-artifacts/prd.md (context only)"
  - "_bmad-output/planning-artifacts/architecture.md (context only)"
outputFile: "_bmad-output/planning-artifacts/epics-presence-mcp.md"
---

# docvet - Epic Breakdown (Wave 2: Presence & MCP)

## Overview

This document provides the epic and story breakdown for docvet's second major wave, covering two epics: docstring presence checking (filling the Layer 1 gap left by interrogate's removal) and MCP server for agentic AI integration (including Anthropic marketplace publishing). Additionally tracks two quick-win items outside of formal epics.

## Requirements Inventory

### Functional Requirements

FR1: (NEW) Docvet shall detect public symbols (modules, classes, functions, methods) with no docstring, providing coverage percentage and configurable threshold. Complements ruff D100-D107 by adding coverage metrics and pipeline integration.
FR2: (#149) Docvet shall expose check capabilities via a Model Context Protocol (MCP) server, allowing MCP-capable agents to run checks programmatically.
FR3: (#236) Docvet's LSP server and MCP server shall be published to Anthropic's marketplace/registry for Claude user discoverability.
FR4: (#232) The project shall have a scheduled CI workflow that runs uv lock --upgrade weekly and opens a PR with updated dependencies.
FR5: (#227) The prefer-fenced-code-blocks rule shall report ALL non-fenced patterns (both >>> doctest and :: rST) per symbol, not short-circuit on the first match.

### NonFunctional Requirements

NFR1: Zero new runtime dependencies — presence check uses stdlib AST only.
NFR2: Presence check must not double-count — enrichment continues to skip undocumented symbols.
NFR3: Presence config: min-coverage threshold, ignore-init, ignore-magic, ignore-private.
NFR4: Complementary to ruff — docs position docvet alongside Astral tools, never against.

### Additional Requirements

- New module: src/docvet/checks/presence.py (Option A from party-mode consensus)
- Run order: presence → enrichment → freshness → coverage → griffe
- Scope: modules, classes, functions, methods (same as interrogate). Properties deferred.
- Config section: [tool.docvet.presence] with PresenceConfig dataclass
- Output: individual missing-docstring findings + coverage summary in --verbose mode
- Documentation: check page, rule page, migration guide from interrogate, README update
- MCP server follows same pattern as LSP server: new module (mcp.py), new CLI subcommand (docvet mcp)
- Anthropic publishing follows same pattern as GitHub Marketplace publishing (Epic 14)
- FR4-FR5 are quick wins outside of epics
- FR6-FR8 (#150, #157, #163) remain in backlog for future wave
- Ruff D100-D107 overlap acknowledged — docvet differentiates via coverage metric, threshold, and integrated pipeline

### FR Coverage Map

FR1: Epic 28 - Presence detection, coverage metric, threshold enforcement
FR2: Epic 29 - MCP server exposing all checks as tools
FR3: Epic 29 (Story 29.3) - Anthropic marketplace publishing folded into MCP epic
FR4: Quick Win - uv lock --upgrade scheduled workflow (#232)
FR5: Quick Win - prefer-fenced-code-blocks all-patterns fix (#227)
NFR1: Epic 28 + 29 - Zero new runtime dependencies
NFR2: Epic 28 - No double-counting with enrichment
NFR3: Epic 28 - Presence config (min-coverage, ignore-init, ignore-magic, ignore-private)
NFR4: Epic 28 - Complementary positioning to ruff

## Epic List

### Epic 28: Docstring Presence Check

Users can detect undocumented public symbols and enforce docstring coverage thresholds — a zero-dependency replacement for interrogate's supply-chain-vulnerable coverage checking. After this epic, running `docvet check` detects missing docstrings alongside all existing quality checks. Users get a coverage percentage, configurable threshold, and can enforce "95% of public symbols must have docstrings" in CI. Teams migrating from interrogate have a documented migration path.

**FRs covered:** FR1, NFR1, NFR2, NFR3, NFR4
**Dependency:** None (standalone)
**Stories:**
- 28.1: Core presence detection + config (check_presence, get_undocumented_symbols, PresenceConfig)
- 28.2: CLI wiring + pipeline integration (docvet presence subcommand, run order, docvet check integration)
- 28.3: Documentation + migration guide (check page, rule page, interrogate migration, README update)

### Epic 29: MCP Server & Agentic Integration

AI agents can run docvet checks programmatically via Model Context Protocol, getting structured results without CLI parsing. After this epic, any MCP-capable tool (Claude Code, Cursor, etc.) can invoke all 6 checks as MCP tools with structured input/output. The MCP server is published to Anthropic's marketplace for discoverability.

**FRs covered:** FR2, FR3
**Dependency:** Requires Epic 28 complete (presence tool should be included)
**Stories:**
- 29.1: Core MCP server implementation (2 tools: docvet_check + docvet_rules)
- 29.2: CLI wiring + tests (docvet mcp subcommand, integration tests)
- 29.3: Documentation + marketplace publishing (docs, Anthropic registry submission)

### Quick Wins (no epic)

- **FR4** (#232): Scheduled uv lock --upgrade workflow — single YAML workflow file
- **FR5** (#227): prefer-fenced-code-blocks all-patterns fix — single function change

---

## Epic 28: Docstring Presence Check

Users can detect undocumented public symbols and enforce docstring coverage thresholds — a zero-dependency replacement for interrogate's supply-chain-vulnerable coverage checking.

### Story 28.1: Core Presence Detection and Configuration

As a **Python developer**,
I want docvet to detect public symbols that have no docstring and report per-file coverage stats,
So that I can enforce docstring presence requirements without depending on interrogate's vulnerable supply chain.

**Acceptance Criteria:**

**Given** a Python file with a mix of documented and undocumented public symbols
**When** `check_presence(source, config)` is called
**Then** a Finding with rule `missing-docstring` and category `presence` is returned for each undocumented symbol
**And** each Finding includes file path, line number, symbol name, and a dynamic message like "Public {symbol_type} has no docstring"

**Given** a Python file missing its module-level docstring
**When** `check_presence` runs
**Then** a `missing-docstring` finding is returned with message "Module has no docstring"

**Given** a class definition with no docstring
**When** `check_presence` runs
**Then** a `missing-docstring` finding is returned with message "Public class has no docstring"

**Given** a PresenceConfig with `ignore_init=True` (default)
**When** a class `__init__` method has no docstring
**Then** no Finding is produced for that `__init__` method

**Given** a PresenceConfig with `ignore_init=False` (overridden)
**When** a class `__init__` method has no docstring
**Then** a `missing-docstring` finding IS produced for that `__init__` method

**Given** a PresenceConfig with `ignore_magic=True` (default)
**When** `__repr__` or `__str__` methods have no docstring
**Then** no Finding is produced for those magic methods

**Given** a PresenceConfig with `ignore_private=True` (default)
**When** a `_helper_function` has no docstring
**Then** no Finding is produced for that private symbol

**Given** a file with nested symbols (method inside class, inner function)
**When** `check_presence` runs
**Then** each undocumented nested public symbol produces its own finding independently

**Given** a file with 8 public symbols, 6 with docstrings and 2 without
**When** `check_presence` runs
**Then** per-file stats report documented=6, total=8
**And** 2 `missing-docstring` findings are returned

**Given** a file where all public symbols have docstrings
**When** `check_presence` runs
**Then** zero findings are returned and per-file stats report documented=N, total=N

**Given** an empty file or a file with only imports
**When** `check_presence` runs
**Then** zero findings are returned (no symbols to check)

**Implementation notes:**
- Single rule `missing-docstring` (not split by symbol type — symbol type info is in the Finding message)
- Return type: `tuple[list[Finding], PresenceStats]` where `PresenceStats` is a dataclass with `documented: int`, `total: int`
- Public = name doesn't start with underscore. `__all__` is irrelevant to scope.
- Parent visibility doesn't gate child checking — a public method inside a `_Private` class is still checked by name.
- Per-file stats returned by the function. Aggregate coverage + threshold comparison is Story 28.2's responsibility.
- Deferred: `@property`/abstract/overridden method handling, TypedDict/NamedTuple special handling — implementation-time test decisions

### Story 28.2: CLI Wiring and Pipeline Integration

As a **Python developer using the CLI**,
I want to run `docvet presence` as a standalone subcommand and have presence checks included in `docvet check`,
So that I can enforce docstring presence through the same CLI workflow I use for all other checks.

**Acceptance Criteria:**

**Given** a user runs `docvet presence`
**When** the command completes
**Then** presence check runs on discovered files and outputs findings in the configured format (terminal/markdown/json)
**And** exit code is non-zero if any `missing-docstring` findings exist

**Given** a user runs `docvet check` (or `docvet check --all`)
**When** the check pipeline executes
**Then** presence runs **first** in the pipeline (before enrichment, freshness, coverage, griffe)
**And** findings from all checks are combined in the output

**Given** a symbol has no docstring
**When** both presence and enrichment checks run via `docvet check`
**Then** only a `missing-docstring` finding is produced (presence)
**And** enrichment does NOT produce additional findings for that symbol (regression guard — enrichment already skips undocumented symbols, no enrichment code change needed)

**Given** `[tool.docvet.presence]` has `min-coverage = 95.0` in pyproject.toml
**When** aggregate coverage across all processed files is below 95%
**Then** the exit code is non-zero
**And** default output includes coverage in summary: "Vetted N files [...] — X findings, 87.0% coverage. (0.3s)"
**And** verbose output includes full detail: "Docstring coverage: 87/100 symbols (87.0%) — below 95.0% threshold"

**Given** `[tool.docvet.presence]` has `min-coverage = 95.0`
**When** aggregate coverage is at or above 95%
**Then** the exit code is zero (assuming no other findings)
**And** default output includes "96.0% coverage" in the summary line
**And** verbose output includes "Docstring coverage: 96/100 symbols (96.0%) — passes 95.0% threshold"

**Given** a user runs `docvet check --quiet`
**When** presence findings or coverage threshold violations exist
**Then** no coverage information is printed (quiet = exit code only, consistent with all other checks)

**Given** a user runs `docvet check --format json`
**When** presence findings exist
**Then** the JSON output includes presence findings with `rule`, `category`, `file`, `line`, `symbol`, `message` fields
**And** a top-level `presence_coverage` object with `documented`, `total`, `percentage`, `threshold`, `passed` fields

**Given** `[tool.docvet.presence]` has `enabled = false`
**When** `docvet check` runs
**Then** presence check is skipped entirely

**Implementation notes:**
- Aggregate `PresenceStats` across all files in CLI layer (sum documented, sum total, compute percentage)
- `min_coverage` threshold comparison happens in CLI, not in per-file check function
- Subcommand follows exact same pattern as enrichment/freshness/coverage/griffe
- `_output_and_exit` handles presence findings identically to other check findings
- `reporting.py` gets touched for JSON schema addition (`presence_coverage` object)
- Config parsing: add `PresenceConfig` to `load_config()` and `DocvetConfig`
- Heavier than typical wiring story (~20-25 tests) due to aggregate stats + JSON schema

### Story 28.3: Documentation and Migration Guide

As a **Python developer evaluating or migrating to docvet**,
I want documentation for the presence check including a migration path from interrogate,
So that I can understand the feature, configure it for my project, and replace interrogate confidently.

**Acceptance Criteria:**

**Given** a user visits the docs site
**When** they navigate to the checks section
**Then** a "Presence" check page exists at `docs/site/checks/presence.md` documenting the check purpose, configuration options, example output, and relationship to ruff D100-D107

**Given** a user visits the rules section
**When** they look for presence rules
**Then** a `missing-docstring` rule page exists at `docs/site/rules/missing-docstring.md` with description, examples of triggering code, "How to Fix" guidance, and configuration to suppress

**Given** a user reads the presence check page
**When** they look for interrogate migration
**Then** a "Migrating from interrogate" section within the check page maps interrogate config options to `[tool.docvet.presence]` equivalents with a 4-step migration guide (remove interrogate, add docvet, map config, update CI)

**Given** the docs site configuration reference
**When** a user looks for presence configuration
**Then** the `[tool.docvet.presence]` section documents `enabled`, `min-coverage`, `ignore-init`, `ignore-magic`, `ignore-private` with types, defaults, and examples

**Given** the README comparison table
**When** a user compares docvet to other tools
**Then** the table shows docvet covering Layer 1 (Presence) in addition to Layers 3-6
**And** interrogate is marked as "unmaintained (CVE in transitive dep)"
**And** the positioning is complementary to ruff, with docvet as interrogate's successor

**Given** the six-layer model documentation
**When** a user reads about docvet's coverage
**Then** the docs reflect that docvet now covers Layers 1, 3-6 (with Layer 2 handled by ruff)

**Given** the docs site builds with `mkdocs build --strict`
**When** all documentation changes are applied
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Follow existing check page and rule page patterns exactly
- Add entry to `docs/rules.yml` catalog — macros scaffold (`docs/main.py`) picks it up automatically
- Migration guide is a section within the presence check page, not a standalone page
- Docs-only story — quality gated by `mkdocs build --strict`
- README positions docvet as successor to interrogate, not competitor. Complementary to Astral tools.

---

## Epic 29: MCP Server & Agentic Integration

AI agents can run docvet checks programmatically via Model Context Protocol, getting structured results without CLI parsing. The MCP server is published to Anthropic's marketplace for discoverability.

### Story 29.1: Core MCP Server Implementation

As an **AI agent (Claude Code, Cursor, etc.)**,
I want to invoke docvet checks via MCP protocol and receive structured findings,
So that I can analyze docstring quality programmatically without parsing CLI output.

**Acceptance Criteria:**

**Given** an MCP client connects to the docvet MCP server via stdio
**When** the client calls the `docvet_check` tool with a `path` parameter pointing to a Python file or directory
**Then** docvet runs all enabled checks on the discovered files
**And** returns a structured result with `findings` (list of Finding objects) and `summary` (files checked, total findings, per-check counts)

**Given** an MCP client calls `docvet_check` with `checks: ["presence", "enrichment"]`
**When** the tool executes
**Then** only the specified checks run (not freshness, coverage, or griffe)
**And** the result only contains findings from those checks

**Given** an MCP client calls `docvet_check` with `checks: ["presence"]`
**When** presence findings exist
**Then** the result includes a `presence_coverage` object with `documented`, `total`, `percentage`, `threshold`, `passed`

**Given** an MCP client calls the `docvet_rules` tool
**When** the tool executes
**Then** it returns a list of all available rules with `name`, `check` (which check module), `description`, and `category`

**Given** the `mcp` optional dependency is not installed
**When** a user runs `docvet mcp`
**Then** a clear error message explains that `pip install docvet[mcp]` is required

**Given** a project has a `[tool.docvet]` configuration in pyproject.toml
**When** the MCP server processes a request
**Then** it respects the project's docvet configuration (exclude patterns, check configs, thresholds)

**Given** an MCP client sends an invalid request (missing required params, unknown tool)
**When** the server processes it
**Then** it returns a proper MCP error response (not a crash or unhandled exception)

**Implementation notes:**
- New module: `src/docvet/mcp.py`
- `mcp` package as optional dependency in `pyproject.toml` under `[project.optional-dependencies]`
- Reuse existing check runners (`check_presence`, `check_enrichment`, etc.) — MCP is a thin adapter
- Server reads `pyproject.toml` config from the working directory, same as CLI
- Finding objects serialized to dicts for MCP response
- stdio transport only for v1

### Story 29.2: CLI Wiring and Tests

As a **developer setting up docvet's MCP server**,
I want a `docvet mcp` subcommand that starts the MCP server,
So that I can configure MCP clients to connect to docvet easily.

**Acceptance Criteria:**

**Given** a user runs `docvet mcp`
**When** the `mcp` optional dependency is installed
**Then** the MCP server starts on stdio and listens for requests

**Given** a user runs `docvet mcp` without the `mcp` package installed
**When** the command starts
**Then** a clear error message is shown: "MCP server requires the mcp extra: pip install docvet[mcp]"

**Given** an MCP client connects and calls `docvet_check` on a directory
**When** the check completes
**Then** the response contains structured findings matching the same results as `docvet check --format json` on the same input

**Given** an MCP client connects and calls `docvet_rules`
**When** the request completes
**Then** the response lists all 20+ rules (including `missing-docstring` from Epic 28)

**Given** the MCP server is running
**When** the client disconnects
**Then** the server shuts down cleanly without errors

**Implementation notes:**
- Subcommand follows same pattern as `docvet lsp`
- Integration tests: spawn server subprocess, send MCP requests via stdio, verify response schema
- Verify parity between MCP `docvet_check` results and `docvet check --format json`
- Add `docvet.mcp` to `_ALL_DOCVET_MODULES` in `test_exports.py`
- Add `mcp` to optional dependencies alongside `griffe`

### Story 29.3: Documentation and Marketplace Publishing

As a **Claude user or AI tool developer**,
I want to find docvet's MCP server on Anthropic's marketplace and in the docs,
So that I can discover and set up docvet integration with minimal friction.

**Acceptance Criteria:**

**Given** a user visits the docs site
**When** they navigate to editor/agent integration
**Then** an MCP server section documents: installation (`pip install docvet[mcp]`), starting the server (`docvet mcp`), available tools and their parameters, example requests and responses

**Given** a user looks at the docs site AI integration page
**When** they read the Claude Code section
**Then** it includes MCP server configuration for Claude Code's `mcp_servers` config

**Given** the Anthropic MCP registry/marketplace exists
**When** the submission process has been researched
**Then** docvet's MCP server is submitted with proper metadata, description, installation instructions, and tool documentation

**Given** the docs site builds with `mkdocs build --strict`
**When** all documentation changes are applied
**Then** the build succeeds with zero warnings

**Implementation notes:**
- Research Anthropic's MCP registry submission process as first step — AC 3 is research-driven and may need to adapt based on what's discovered
- If the registry requires specific packaging or manifest files, create them
- If the registry doesn't exist yet or is invite-only, document the MCP server setup for manual configuration and note the registry status
- Update `ai-integration.md` with MCP server details
- This story is partially research, partially docs — adapt scope based on findings
