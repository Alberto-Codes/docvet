---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - "GitHub Issue #256: Dynamic docvet badge"
  - "GitHub Issue #305: docvet fix command"
  - "GitHub Issue #306: --summary flag"
  - "GitHub Issue #308: Inline suppression comments"
  - "GitHub Issue #309: config --show-defaults"
  - "GitHub Issue #160: VS Code extension"
  - "GitHub Issue #163: SARIF output format"
  - "GitHub Issue #164: Flagship OSS runs"
  - "GitHub Issue #158: Example project template"
  - "GitHub Issue #265: Architecture diagrams"
  - "GitHub Issue #310: Incomplete section detection (exploration)"
  - "Party-mode consensus (2026-03-06): Epic 31-34 structure"
  - "PRD Growth items audit (2026-03-06)"
---

# docvet - Epic Breakdown (Epics 31-34)

## Overview

This document provides the epic and story breakdown for docvet's post-v1.0 growth phase (Epics 31-34), decomposing GitHub issues, PRD Growth items, and party-mode consensus into implementable stories. All v1.0 PRD requirements (FR1-FR127, NFR1-NFR66) are fully satisfied. This wave targets adoption, conversion, and platform expansion.

## Requirements Inventory

### Functional Requirements

FR1: Dynamic badge endpoint writes shields.io-compatible JSON (pass/fail/findings count) to a GitHub Gist after each CI run (#256)
FR2: `--summary` flag prints per-check quality percentages and overall score alongside normal output (#306)
FR3: Summary output works with `--format json` for machine consumption (#306)
FR4: `docvet config --show-defaults` prints effective merged configuration in TOML format (#309)
FR5: Config show-defaults distinguishes user-configured values from built-in defaults (#309)
FR6: `docvet fix` generates missing docstring sections from pure AST analysis (#305)
FR7: Fix is deterministic — same input always produces same output (#305)
FR8: Fix is idempotent — running twice produces no additional changes (#305)
FR9: Fix preserves existing docstring content byte-for-byte (#305)
FR10: Fix supports `--dry-run` showing diff without modifying files (#305)
FR11: Fix supports all file discovery modes (diff, staged, all, positional args) (#305)
FR12: Fix scaffolds Args, Returns, Raises, Yields, Receives, Warns, Attributes, Examples sections (#305)
FR13: Line-level suppression via `# docvet: ignore[rule-id]` on def/class line (#308)
FR14: Line-level suppression via `# docvet: ignore` (all rules) on def/class line (#308)
FR15: File-level suppression via `# docvet: ignore-file[rule-id]` at top of file (#308)
FR16: File-level suppression via `# docvet: ignore-file` (all rules) at top of file (#308)
FR17: Suppressed findings reported in verbose mode for transparency (#308)
FR18: Suppression implemented as post-filter on findings list, not per-check modification (#308)
FR19: VS Code extension launches `docvet lsp` via STDIO and publishes diagnostics to Problems panel (#160)
FR20: VS Code extension contributes Language Model Tools for Copilot agent mode (#160)
FR21: `--format sarif` produces SARIF v2.1.0 compliant output with rule definitions and locations (#163)
FR22: SARIF output compatible with `github/codeql-action/upload-sarif@v3` (#163)
FR23: Flagship OSS runs produce documented findings on 3+ major projects (FastAPI, Pydantic, typer) (#164)
FR24: Flagship results published as docs page or blog post (#164)
FR25: Example project template shows full docvet + mkdocstrings pipeline (#158)

### NonFunctional Requirements

NFR1: Badge JSON endpoint uses shields.io schema v1 (`schemaVersion`, `label`, `message`, `color`)
NFR2: Summary percentage calculation: `(symbols_checked - symbols_with_findings) / symbols_checked`
NFR3: Fix command adds zero runtime dependencies — AST-only, stdlib
NFR4: Fix insertion uses AST line numbers for positioning — no libcst dependency
NFR5: Suppression comment parsing uses tokenize module or AST comment extraction
NFR6: Suppression syntax follows established conventions (`# tool: directive[args]`)
NFR7: VS Code extension is a thin LSP wrapper — minimal TypeScript, no bundled Python
NFR8: SARIF output reuses ~60% of existing JSON formatter code
NFR9: All new features maintain zero-dependency core (typer only)
NFR10: All new subcommands follow existing CLI patterns (`_output_and_exit` pipeline)

### Additional Requirements

- Party-mode consensus (2026-03-06): unanimous 17/17 agent agreement on epic sequencing
- Epic 31 ships first as quick wins (days, not weeks)
- Fix command requires architecture spike before full implementation
- Incomplete section detection (#310) requires exploration spike before committing
- Example project (#158) can fold into flagship runs (#164) as a single deliverable
- Architecture diagrams (#265) are lowest priority — contributor DX only
- Parking lot items (#148, #72, #307) tracked but not committed

### FR Coverage Map

FR1:  Epic 31, Story 31.1 - Dynamic badge endpoint (shields.io JSON to Gist)
FR2:  Epic 31, Story 31.2 - --summary flag with per-check percentages
FR3:  Epic 31, Story 31.2 - Summary works with --format json
FR4:  Epic 31, Story 31.3 - config --show-defaults in TOML format
FR5:  Epic 31, Story 31.3 - Config distinguishes defaults vs user-configured
FR6:  Epic 32, Story 32.2 - docvet fix generates missing sections from AST
FR7:  Epic 32, Story 32.2 - Fix is deterministic
FR8:  Epic 32, Story 32.2 - Fix is idempotent
FR9:  Epic 32, Story 32.2 - Fix preserves existing content
FR10: Epic 32, Story 32.3 - Fix supports --dry-run
FR11: Epic 32, Story 32.3 - Fix supports all discovery modes
FR12: Epic 32, Story 32.2 - Fix scaffolds all section types
FR13: Epic 32, Story 32.4 - Line-level ignore with rule ID
FR14: Epic 32, Story 32.4 - Line-level ignore all rules
FR15: Epic 32, Story 32.4 - File-level ignore with rule ID
FR16: Epic 32, Story 32.4 - File-level ignore all rules
FR17: Epic 32, Story 32.4 - Suppressed findings in verbose mode
FR18: Epic 32, Story 32.4 - Suppression as post-filter
FR19: Epic 33, Story 33.1 - VS Code extension with LSP
FR20: Epic 33, Story 33.1 - VS Code Language Model Tools for Copilot
FR21: Epic 33, Story 33.3 - SARIF v2.1.0 output format
FR22: Epic 33, Story 33.3 - SARIF compatible with codeql upload action
FR23: Epic 33, Story 33.2 - Flagship runs on 3+ major projects
FR24: Epic 33, Story 33.2 - Flagship results published
FR25: Epic 33, Story 33.2 - Example project (folded into flagship runs)

## Epic List

### Epic 31: Project Health Visibility
Users can see at-a-glance docstring quality metrics, display a dynamic badge on their README, and inspect their effective configuration -- giving them a complete picture of their project's documentation health without digging through individual findings.
**FRs covered:** FR1, FR2, FR3, FR4, FR5
**NFRs covered:** NFR1, NFR2, NFR10

### Epic 32: Linter Lifecycle -- Fix & Suppress
Users can automatically scaffold missing docstring sections with `docvet fix` and selectively suppress findings for intentional deviations with inline comments -- completing the linter lifecycle from detection through resolution.
**FRs covered:** FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18
**NFRs covered:** NFR3, NFR4, NFR5, NFR6, NFR10

### Epic 33: Ecosystem Visibility & Editor Integration
Users can see docvet findings directly in VS Code, validate docvet against flagship OSS projects for social proof, access a reference example showing the full pipeline, and upload findings to GitHub Code Scanning via SARIF.
**FRs covered:** FR19, FR20, FR21, FR22, FR23, FR24, FR25
**NFRs covered:** NFR7, NFR8

### Deferred (Post-Epic 33 Candidates)
Reassess after Epic 33 ships based on user demand and landscape changes.
- #310: Incomplete section detection (exploration spike)
- #265: Architecture Mermaid diagrams
- #148: Negation pattern support in exclude
- #72: WebMCP integration
- #307: Ruff plugin exploration

## Epic 31: Project Health Visibility

Users can see at-a-glance docstring quality metrics, display a dynamic badge on their README, and inspect their effective configuration -- giving them a complete picture of their project's documentation health without digging through individual findings.

### Story 31.1: Dynamic Badge Endpoint

As a **project maintainer**,
I want a dynamic badge that shows my docvet pass/fail status and findings count,
So that my README communicates documentation health at a glance and encourages adoption.

**Acceptance Criteria:**

**Given** the docvet GitHub Action runs in CI
**When** the check completes with zero findings
**Then** a shields.io-compatible JSON file is written to a GitHub Gist with `{"schemaVersion":1, "label":"docvet", "message":"passing", "color":"brightgreen"}`

**Given** the docvet GitHub Action runs in CI
**When** the check completes with findings
**Then** the JSON file shows `"message":"N findings"` with color `"yellow"` (warnings only) or `"red"` (failures)

**Given** a user configures `shields.io/endpoint?url=<gist-raw-url>` in their README
**When** the badge renders
**Then** it displays the current pass/fail status from the latest CI run

**Given** the `schneegans/dynamic-badges-action` step is added to the GitHub Action workflow
**When** the Gist does not yet exist
**Then** the action creates it using the configured `GIST_SECRET` token

### Story 31.2: Summary Flag for Quality Percentages

As a **developer**,
I want a `--summary` flag that prints per-check quality percentages,
So that I can quickly assess my project's overall documentation health without reading individual findings.

**Acceptance Criteria:**

**Given** a codebase with mixed findings across checks
**When** the user runs `docvet check --all --summary`
**Then** output includes files scanned, symbols checked, per-check percentages (enrichment, freshness, coverage, griffe), and an overall score

**Given** the `--summary` flag is used with `--format json`
**When** the check completes
**Then** summary data is included in the JSON output as a `summary` object with numeric fields

**Given** the `--summary` flag is used with a subcommand (e.g., `docvet enrichment --summary`)
**When** the check completes
**Then** only the relevant check's percentage is shown

**Given** a codebase with zero findings
**When** `--summary` is used
**Then** all percentages show 100% and overall score is 100%

**Given** the percentage calculation
**When** computed
**Then** the formula is `(symbols_checked - symbols_with_findings) / symbols_checked * 100`, rounded to nearest integer

**Given** the summary needs a total symbol count
**When** computed
**Then** the count is derived from `get_documented_symbols()` calls already in the check pipeline, not from a separate AST pass

### Story 31.3: Config Show-Defaults Command

As a **developer**,
I want a `docvet config --show-defaults` command that prints my effective configuration,
So that I can debug why specific rules are running and onboard onto available settings.

**Acceptance Criteria:**

**Given** a project with no `[tool.docvet]` in pyproject.toml
**When** the user runs `docvet config --show-defaults`
**Then** all built-in defaults are printed in TOML format, suitable for copy-paste into pyproject.toml

**Given** a project with partial `[tool.docvet]` configuration
**When** the user runs `docvet config --show-defaults`
**Then** the merged effective config is printed, with comments indicating which values are user-configured vs defaults

**Given** the user runs `docvet config --show-defaults --format json`
**When** output is produced
**Then** the effective config is printed as a JSON object

**Given** no pyproject.toml exists in the current directory or parents
**When** `docvet config --show-defaults` is run
**Then** all defaults are printed with a note that no config file was found

## Epic 32: Linter Lifecycle -- Fix & Suppress

Users can automatically scaffold missing docstring sections with `docvet fix` and selectively suppress findings for intentional deviations with inline comments -- completing the linter lifecycle from detection through resolution.

### Story 32.1: Fix Feasibility Spike

As a **project maintainer**,
I want confidence that AST-based docstring insertion works reliably,
So that the fix command can be built on a validated foundation.

**Acceptance Criteria:**

**Given** a Python function with a one-line docstring and missing Raises/Args sections
**When** the spike's proof-of-concept inserts scaffolded sections using AST line numbers
**Then** the modified file is valid Python and `docvet check` produces zero findings for the scaffolded sections

**Given** a function with an existing multi-section docstring (Args exists, Raises missing)
**When** the spike inserts the missing Raises section
**Then** existing Args content is preserved byte-for-byte and Raises is inserted after the last existing section

**Given** the spike runs insertion twice on the same file
**When** the second run executes
**Then** no changes are made (idempotency validated)

**Given** the spike results
**When** reviewed
**Then** a decision document records: chosen insertion strategy (string ops + AST line numbers vs libcst), edge cases identified, and go/no-go recommendation

**Given** the spike evaluates the fix lifecycle
**When** the scaffold category design is reviewed
**Then** the decision document also records: the `scaffold` finding category design (required severity, actionable message format "fill in [Section] — describe [items]"), the placeholder marker specification (e.g. `[TODO: describe]`), and how scaffold findings integrate with reporting, exit codes, and JSON output

### Story 32.2: Fix Core -- Section Scaffolding Engine

As a **developer**,
I want `docvet fix` to generate missing docstring sections from AST analysis,
So that I get a skeleton I can fill in instead of writing sections from scratch.

**Acceptance Criteria:**

**Given** a function with missing Args, Returns, and Raises sections
**When** `docvet fix` runs on the file
**Then** all three sections are scaffolded with parameter names from the signature and exception names from the body, using `[TODO: describe]` placeholders. Each scaffolded section produces a `scaffold` category finding with an actionable message (e.g. "fill in Args — describe parameters: data, timeout")

**Given** a function that already has an Args section but is missing Raises
**When** `docvet fix` runs
**Then** only the Raises section is added; existing Args content is preserved byte-for-byte

**Given** a class with missing Attributes section (dataclass/NamedTuple/TypedDict)
**When** `docvet fix` runs
**Then** an Attributes section is scaffolded listing all fields from the class definition

**Given** a generator function missing Yields and Receives sections
**When** `docvet fix` runs
**Then** both sections are scaffolded with `[TODO: describe]` placeholders

**Given** a symbol missing an Examples section (and `require_examples` config matches its type)
**When** `docvet fix` runs
**Then** an Examples section is scaffolded with a fenced code block placeholder. A `scaffold` finding is produced: "fill in Examples section"

**Given** fix produces output
**When** the same input is processed
**Then** output is deterministic (same input = same output, always)

**Given** fix has already run on a file
**When** fix runs again on the same file
**Then** no changes are made (idempotent)

**Given** a file with mixed symbols -- some needing fixes, some already complete
**When** `docvet fix` runs
**Then** only symbols with missing sections are modified; complete symbols are untouched

**Given** `docvet fix` has scaffolded missing sections in a file
**When** `docvet check` runs on that file
**Then** the original missing-section findings (e.g. `missing-raises`) are gone, replaced by `scaffold` category findings for each scaffolded section. Scaffold findings are `required` severity and block CI.

**Given** the scaffolding engine produces output
**When** findings are generated
**Then** each scaffold finding uses the `scaffold` category on the Finding dataclass, with a message format: "fill in [Section] — describe [items]" where [items] are the specific parameters, exceptions, or fields that need descriptions

### Story 32.3: Fix CLI Wiring -- Subcommand, Dry-Run, and Discovery

As a **developer**,
I want the fix command integrated into the CLI with dry-run and file discovery support,
So that I can preview changes before applying them and use fix with the same workflows as check.

**Acceptance Criteria:**

**Given** the user runs `docvet fix --dry-run`
**When** files have missing sections
**Then** a unified diff is printed to stdout showing what would change, without modifying any files

**Given** the user runs `docvet fix` (no flags)
**When** files in the git diff have missing sections
**Then** those files are modified in-place with scaffolded sections

**Given** the user runs `docvet fix --staged`
**When** staged files have missing sections
**Then** only staged files are modified

**Given** the user runs `docvet fix --all`
**When** the codebase has files with missing sections
**Then** all matching files are modified

**Given** the user runs `docvet fix path/to/file.py`
**When** the specified file has missing sections
**Then** only that file is modified

**Given** the user runs `docvet fix` on a file with no missing sections
**When** fix completes
**Then** no files are modified and a message indicates "No fixes needed"

**Given** fix modifies files
**When** the user subsequently runs `docvet check` on those files
**Then** the original missing-section findings are gone, replaced by `scaffold` category findings for each scaffolded section. The scaffold findings have actionable messages guiding the user to fill in real content. Once the user replaces placeholders with descriptions, `docvet check` produces zero findings (full roundtrip validation).

### Story 32.4: Inline Suppression Comments

As a **developer**,
I want to suppress specific docvet findings with inline comments,
So that I can mark intentional deviations without disabling rules globally.

**Acceptance Criteria:**

**Given** a function definition with `# docvet: ignore[missing-raises]` on the `def` line
**When** `docvet check` runs
**Then** any `missing-raises` finding for that symbol is suppressed from output

**Given** a function with `# docvet: ignore[missing-raises,missing-yields]` (comma-separated)
**When** `docvet check` runs
**Then** both `missing-raises` and `missing-yields` findings are suppressed for that symbol

**Given** a function with `# docvet: ignore` (no rule specified)
**When** `docvet check` runs
**Then** all findings for that symbol are suppressed

**Given** a file with `# docvet: ignore-file[missing-examples]` before the first class/function definition
**When** `docvet check` runs on that file
**Then** all `missing-examples` findings in the entire file are suppressed

**Given** a file with `# docvet: ignore-file` (no rule specified) before the first class/function definition
**When** `docvet check` runs
**Then** all findings in the entire file are suppressed

**Given** suppressed findings exist and `--verbose` is active
**When** output is rendered
**Then** suppressed findings are listed separately with a note indicating suppression reason

**Given** the suppression filter
**When** implemented
**Then** it operates as a post-filter on the findings list -- no `_check_*` functions are modified

**Given** an invalid rule ID in a suppression comment (e.g., `# docvet: ignore[nonexistent-rule]`)
**When** `docvet check` runs
**Then** a warning is emitted that the rule ID is not recognized

## Epic 33: Ecosystem Visibility & Editor Integration

Users can see docvet findings directly in VS Code, validate docvet against flagship OSS projects for social proof, access a reference example showing the full pipeline, and upload findings to GitHub Code Scanning via SARIF.

### Story 33.1: VS Code Extension

As a **VS Code user**,
I want a docvet extension that shows docstring findings in the Problems panel,
So that I see quality issues inline while editing without switching to the terminal.

**Acceptance Criteria:**

**Given** the docvet VS Code extension is installed and a Python file is open
**When** the file contains symbols with docstring findings
**Then** diagnostics appear in the Problems panel with rule ID, message, file, and line number

**Given** the extension activates
**When** it launches the language server
**Then** it starts `docvet lsp --stdio` as a subprocess and connects via STDIO

**Given** the user edits a Python file and saves
**When** the LSP server re-analyzes the file
**Then** diagnostics update in real-time to reflect the current state

**Given** the extension is published to VS Code Marketplace
**When** a user searches "docvet"
**Then** the extension appears with proper metadata (description, icon, categories)

**Given** the extension contributes Language Model Tools
**When** a user asks Copilot agent mode about docstring quality
**Then** Copilot can invoke `docvet.check` as a tool and return findings contextually

**Given** the user does not have docvet installed
**When** the extension activates
**Then** a helpful error message explains how to install docvet (`pip install docvet`)

**Given** the VS Code extension needs a separate repository
**When** the story begins
**Then** a `docvet-vscode` repo is created with package.json, extension.ts, and CI for VS Code Marketplace publishing

### Story 33.2: Flagship OSS Runs & Example Guide

As a **potential adopter**,
I want to see docvet findings on real-world projects I know,
So that I can evaluate whether docvet finds genuine issues and is worth adopting.

**Acceptance Criteria:**

**Given** docvet is run against FastAPI, Pydantic, and typer (or 3+ comparable Google-style mkdocs projects)
**When** `docvet check --all` completes on each
**Then** findings are documented with counts by rule, notable examples, and false positive assessment

**Given** findings are genuine and fixable
**When** small PRs (5-10 fixes each) are opened on target projects
**Then** PRs credit docvet and link to the docs site, demonstrating the fix workflow

**Given** the findings data is compiled
**When** published
**Then** a docs page or blog post titled "What we found running docvet on the Python ecosystem" is live on the docs site

**Given** a user wants to replicate the docvet + mkdocstrings pipeline
**When** they visit the flagship results page
**Then** configuration snippets (mkdocs.yml, pyproject.toml) and a step-by-step guide are included

**Given** the guide content
**When** a user follows the steps
**Then** they can configure docvet + mkdocstrings on their own project and verify with `docvet check --all`

**Given** docvet produces findings on a flagship project
**When** findings are reviewed
**Then** false positive rate is documented and any false positives are filed as bugs against docvet

### Story 33.3: SARIF Output Format

As a **CI/CD engineer**,
I want `--format sarif` output for GitHub Code Scanning integration,
So that docvet findings appear in the Security tab and PR annotations without custom scripting.

**Acceptance Criteria:**

**Given** the user runs `docvet check --all --format sarif`
**When** findings exist
**Then** output is valid SARIF v2.1.0 JSON with `$schema`, `version`, `runs[].tool.driver` (name, version, rules[]), and `runs[].results[]`

**Given** SARIF output includes rule definitions
**When** the `rules[]` array is populated
**Then** each rule has `id`, `shortDescription`, `helpUri` (linking to the docs site rule page), and `defaultConfiguration.level`

**Given** SARIF output includes results
**When** each finding is serialized
**Then** it has `ruleId`, `message.text`, `locations[].physicalLocation` (artifactLocation.uri, region.startLine), and `level`

**Given** no findings exist
**When** `--format sarif` is used
**Then** valid SARIF is produced with an empty `results[]` array

**Given** the SARIF file is uploaded via `github/codeql-action/upload-sarif@v3`
**When** GitHub processes it
**Then** findings appear as code scanning alerts on the repository's Security tab

**Given** the SARIF output
**When** generated with `--format sarif`
**Then** the formatter reuses the existing JSON findings pipeline, adding SARIF envelope structure
