---
stepsCompleted:
  - 'step-01-init'
  - 'step-02-discovery'
  - 'step-03-success'
  - 'step-04-journeys'
  - 'step-05-domain-skipped'
  - 'step-06-innovation-skipped'
  - 'step-07-project-type'
  - 'step-08-scoping'
  - 'step-09-functional'
  - 'step-10-nonfunctional'
  - 'step-11-polish'
  - 'step-12-complete'
status: 'complete'
classification:
  projectType: 'cli_tool'
  domain: 'developer_tooling'
  complexity: 'medium'
  projectContext: 'brownfield'
inputDocuments:
  - '_bmad-output/project-context.md'
  - 'docs/product-vision.md'
  - 'docs/architecture.md'
  - 'docs/project-overview.md'
  - 'docs/development-guide.md'
  - 'docs/source-tree-analysis.md'
  - 'docs/index.md'
  - '_bmad-output/implementation-artifacts/tech-spec-4-cli-scaffold.md'
  - '_bmad-output/implementation-artifacts/tech-spec-ci-workflow.md'
  - '_bmad-output/implementation-artifacts/tech-spec-config-reader.md'
  - '_bmad-output/implementation-artifacts/tech-spec-file-discovery.md'
  - '_bmad-output/implementation-artifacts/tech-spec-7-ast-helpers.md'
  - '_bmad-output/implementation-artifacts/tech-spec-wire-discovery-cli.md'
  - 'gh-issue-8'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 14
workflowType: 'prd'
projectName: 'docvet'
featureScope: 'enrichment-check'
---

# Product Requirements Document - docvet

**Author:** Alberto-Codes
**Date:** 2026-02-08

## Executive Summary

docvet is a Python CLI tool for comprehensive docstring quality vetting. This PRD defines requirements for the **enrichment check module** (Layer 3: completeness) — the first real check module in docvet's six-layer quality model.

The enrichment check fills a 4-year ecosystem gap by detecting missing docstring sections (Raises, Yields, Attributes, Examples, and more) through AST analysis. It complements ruff (style) and interrogate (presence) rather than competing with them. darglint — the only prior tool in this space — has been unmaintained since 2022; ruff stops at D417 (param completeness).

**Target users:** Python developers writing Google-style docstrings, teams using mkdocs-material + mkdocstrings.

**Scope:** 10 rule identifiers covering 14 detection scenarios, `required` vs `recommended` categorization, full config customization via `[tool.docvet.enrichment]` in pyproject.toml.

### Key Terms

- **Detection scenario**: A specific code pattern that triggers a check (e.g., "function with `raise` but no `Raises:` section"). 14 total.
- **Rule identifier**: A stable kebab-case name emitted in findings (e.g., `missing-raises`). 10 total — multiple scenarios can share one rule ID.
- **Required vs recommended**: Category baked into each rule definition. Required = misleading omission; recommended = improvement opportunity.
- **Missing vs incomplete**: MVP detects *missing* sections only (no `Raises:` section at all). *Incomplete* sections (has `Raises:` but doesn't list all exceptions) are a Growth feature.

## Success Criteria

### User Success

- A developer runs `docvet enrichment` and gets a clear, prioritized list of missing docstring sections across their codebase
- Each finding is immediately actionable: file, line, symbol name, a human-readable kebab-case rule identifier (e.g., `missing-raises`), and a concise message explaining what's missing and why
- Findings are categorized as `required` (misleading omission) or `recommended` (improvement opportunity), so developers can triage effectively
- Well-documented code produces zero findings -- no false positives on complete docstrings
- The check respects existing `EnrichmentConfig` toggles, so teams customize which rules run without noise

### Business Success

- Fills the explicit gap between ruff D417 (param completeness) and full section completeness -- no existing tool covers this
- Positions docvet as a credible addition to the Python quality toolchain alongside ruff, ty, and interrogate
- Rule identifiers follow industry convention (ty-style kebab-case), making docvet feel native to modern Python workflows
- All 14 detection scenarios (10 rule identifiers) ship together, delivering complete Layer 3 coverage in a single release

### Technical Success

- `check_enrichment(source, tree, config, file_path)` returns `list[Finding]` with zero side effects -- pure function, deterministic output
- Each `Finding` carries: `file`, `line`, `symbol`, `rule` (kebab-case stable identifier), `message`, `category` (`required` | `recommended`)
- All 14 detection scenarios (mapping to 10 distinct rule identifiers) implemented and individually toggleable via `EnrichmentConfig`
- No new runtime dependencies -- stdlib `ast` + existing `ast_utils.Symbol` infrastructure
- Checks are isolated -- no imports from other check modules, no shared mutable state
- Quality gates pass: ruff, ty, pytest with >=85% coverage, interrogate

### Measurable Outcomes

- `tests/fixtures/missing_raises.py` produces exactly the expected `missing-raises` finding
- `tests/fixtures/missing_yields.py` produces exactly the expected `missing-yields` finding
- `tests/fixtures/complete_module.py` produces zero findings
- Each of the 10 rule identifiers has at least one dedicated unit test with a source string fixture
- `EnrichmentConfig` toggles (`require-raises = false`, etc.) suppress the corresponding rule's findings

## Product Scope

### Competitive Context

darglint -- the only tool that partially addressed Args/Returns/Raises alignment -- has been unmaintained since 2022. Ruff's D rules stop at D417 (param completeness) and explicitly chose not to go deeper into section completeness. This leaves a 4-year vacuum in the ecosystem for docstring completeness checking. docvet fills this gap by complementing ruff (style) and interrogate (presence) rather than competing with them -- the six-layer quality model makes the composability explicit: layers 1-2 are delegated to existing tools, layers 3-6 are docvet's territory.

### MVP - Minimum Viable Product

The MVP delivers all 10 rule identifiers (14 detection scenarios), the shared `Finding` type, full `EnrichmentConfig` integration, and comprehensive unit tests. See "Project Scoping & Phased Development > MVP Feature Set" for the authoritative implementation checklist.

### Growth & Vision

Growth features include inline suppression, JSON output, and incomplete section detection. Vision includes editor/LSP integration and additional docstring style support. See "Project Scoping & Phased Development > Post-MVP Features" for the full Phase 2 and Phase 3 roadmap.

## User Journeys

### Journey 1: Dev During Development -- "The Missing Raises Catch"

**Persona:** Maya, a mid-level Python developer working on a data pipeline library. She writes Google-style docstrings diligently but sometimes forgets edge cases.

**Opening Scene:** Maya just finished implementing a new `parse_config()` function. It validates input and raises `ValueError` on bad keys and `FileNotFoundError` when the config path is missing. She wrote a clean docstring with `Args:` and `Returns:` sections but didn't add a `Raises:` section -- she was focused on the happy path.

**Rising Action:** Before committing, she runs `docvet enrichment` on her working directory. The terminal shows:

```
src/pipeline/config.py:42: missing-raises Function 'parse_config' raises ValueError, FileNotFoundError but has no Raises: section
```

One finding. Clear file, line, symbol, rule name, and a message that tells her exactly which exceptions she missed.

**Climax:** Maya opens the file, adds the `Raises:` section documenting both exceptions with descriptions. She runs `docvet enrichment` again -- zero findings. She knows her docstring now accurately describes the function's behavior.

**Resolution:** The downstream developer who calls `parse_config()` next week sees the `Raises:` section in their IDE tooltip and adds proper error handling. Maya's docstring prevented a silent failure in production.

### Journey 2: PR Workflow -- "The Pre-Commit Safety Net"

**Persona:** Raj, a senior developer on a team that runs `docvet check --staged` before every commit.

**Opening Scene:** Raj refactored a data validation class, converting it from a plain class to a `dataclass` with 6 fields. He updated the class docstring's summary line but didn't add an `Attributes:` section for the new fields.

**Rising Action:** He stages his changes and runs `docvet check --staged`. The enrichment check fires alongside freshness, coverage, and griffe:

```
src/models/validation.py:15: missing-attributes Dataclass 'ValidationResult' has 6 fields but no Attributes: section
```

The other three checks pass clean. Just this one enrichment finding.

**Climax:** Raj adds the `Attributes:` section with types and descriptions for all 6 fields. He re-stages and runs `docvet check --staged` again -- all clear. He commits with confidence.

**Resolution:** During PR review, the reviewer sees the complete `Attributes:` section and understands the dataclass instantly. No review comment asking "what does `threshold` do?" -- the docstring already answers it.

**Edge Case -- The Disagreement:** A week later, Raj gets a `missing-examples` finding on a private helper function `_normalize_path()`. He doesn't think a private utility needs an `Examples:` section. He adjusts `require-examples = ["class", "protocol", "dataclass"]` in `pyproject.toml`, removing the recommendation for plain functions. Next run, the finding is gone. The tool respects his judgment -- it's a guardrail, not a mandate.

### Journey 3: CI Pipeline -- "The Automated Gate"

**Persona:** The CI system running on a GitHub Actions PR workflow for a team using docvet with default configuration.

**Opening Scene:** A junior developer opens a PR that adds a generator function with `yield` statements but no `Yields:` section in the docstring. The PR triggers the CI pipeline.

**Rising Action:** The CI job runs `docvet check`. With default config, `enrichment` is in `warn-on` -- advisory mode. The enrichment check produces:

```
src/stream/processor.py:88: missing-yields Generator 'stream_events' uses yield but has no Yields: section
```

Docvet exits with code 0. The CI check passes green, but the finding appears in the build log as a warning.

**Climax:** The tech lead notices the warning in the PR log during review. She asks the developer to fix it. After three similar PRs in a row, she decides the team is ready for enforcement. She moves `enrichment` to `fail-on` in `pyproject.toml`:

```toml
[tool.docvet]
fail-on = ["enrichment"]
```

Now enrichment findings cause non-zero exit. CI goes red on incomplete docstrings.

**Resolution:** The next PR with a missing `Yields:` section fails CI automatically. The developer sees the failed check, reads the clear message, and fixes it before review. The team's documentation standard is enforced without human reviewers spending time on it. The gradual promotion from `warn-on` to `fail-on` let the team adopt at their own pace.

### Journey 4: Tech Lead Audit -- "The Codebase Sweep"

**Persona:** Carlos, a tech lead adopting docvet for his team's mkdocs-material documentation site. He wants to understand the documentation debt across the codebase.

**Opening Scene:** Carlos configures `[tool.docvet.enrichment]` in `pyproject.toml`, keeping all defaults (`require-raises = true`, `require-yields = true`, etc.) but setting `require-examples` to only `["protocol", "dataclass"]` -- his team doesn't need examples on every public function yet.

**Rising Action:** He runs `docvet enrichment --all`. The terminal shows 47 findings across 12 files. He sees a mix of `required` and `recommended` categories:

```
src/core/engine.py:23: missing-raises ...
src/core/engine.py:91: missing-warns ...
src/models/schema.py:15: missing-attributes ...
src/models/schema.py:44: missing-typed-attributes ...
src/protocols/handler.py:8: missing-examples ...
```

**Climax:** Carlos triages by rule. He creates a team issue for the 12 `missing-raises` findings (highest impact -- actively misleading callers). He deprioritizes the 5 `missing-examples` findings on protocols as a future sprint item. The kebab-case rule identifiers make it easy to grep, filter, and assign.

**Resolution:** Over two sprints, the team systematically works through the findings. Each sprint they re-run `docvet enrichment --all` and watch the count drop. Carlos eventually moves `enrichment` to `fail-on` to prevent new debt from accumulating.

### Journey 5: New Adopter -- "The First Run"

**Persona:** Priya, a developer who just heard about docvet and wants to try it on her existing Django REST framework project with ~200 Python files.

**Opening Scene:** Priya installs docvet (`pip install docvet`) and runs `docvet enrichment --all` with zero configuration. Default `EnrichmentConfig` applies -- all rules enabled.

**Rising Action:** The output is overwhelming: 183 findings scroll past. Every function that raises an exception, every generator, every class missing `Attributes:`. Priya's stomach drops -- "Is my code really this bad?"

**Climax:** But then she sees the summary at the bottom:

```
183 findings (34 required, 149 recommended)
```

That single line changes everything. 34 real issues where her docstrings actively mislead developers. 149 nice-to-haves that would make the docs better but aren't urgent. She's not drowning -- she has a clear path forward.

She adds targeted configuration to focus on what matters first:

```toml
[tool.docvet.enrichment]
require-warns = false
require-other-parameters = false
require-cross-references = false
prefer-fenced-code-blocks = false
require-examples = []
```

She re-runs: 34 findings. All `required` -- missing `Raises:`, `Yields:`, and `Attributes:` sections. Manageable.

**Resolution:** Priya fixes the 8 most critical findings in her core modules, commits, and sets up docvet in CI with `enrichment` in `warn-on`. She'll tighten the config as the team catches up. The tool met her where she was instead of demanding perfection on day one.

### Journey Requirements Traceability

All journey-revealed capabilities are formally captured in the Functional Requirements section below. CLI/reporting layer dependencies (output formatting, summary line, exit codes, discovery modes) are out of enrichment module scope but required for full journey completion in the same release.

## Enrichment Module Specification

### Project-Type Overview

docvet is a non-interactive, scriptable CLI tool in the tradition of ruff, ty, and interrogate. The enrichment check (`check_enrichment`) is a pure function that produces a flat list of `Finding` objects -- it has no awareness of the CLI layer, output formatting, or exit codes. The CLI layer is the consumer: it calls the check, formats findings for terminal output, and maps `fail-on` / `warn-on` configuration to exit codes.

### Integration Contract

**Public API:**

```python
def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
) -> list[Finding]:
```

- **Pure function**: no I/O, no side effects, deterministic output
- **Caller provides AST**: the function does not call `ast.parse()` -- the caller handles `SyntaxError`
- **`file_path` enables context-aware detection**: needed for `__init__.py` module rules and for populating `Finding.file` -- the function owns full `Finding` construction
- **Config toggles respected**: disabled rules produce zero findings, period
- **Returns empty list on clean code**: not `None`, not a sentinel
- **One finding per symbol per rule**: if multiple detection branches match the same symbol for the same rule (e.g., a `@dataclass` that also has `__init__` self-assignments), only one `missing-attributes` finding is emitted

**`Finding` dataclass (lives in `src/docvet/checks/__init__.py`):**

```python
@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    symbol: str
    rule: str        # kebab-case stable identifier
    message: str
    category: Literal["required", "recommended"]
```

**Import contract:**

- `checks/__init__.py` exports `Finding` only -- it is a shared types module, not a barrel file
- Each check module exports its own public function: `checks.enrichment.check_enrichment`, `checks.freshness.check_freshness`, etc.
- The CLI imports `Finding` from `docvet.checks` and `check_enrichment` from `docvet.checks.enrichment` independently
- No cross-imports between check modules -- each check depends only on `checks.Finding` and `ast_utils`

### Rule Taxonomy

The vision doc lists 14 detection scenarios. After consolidation, these map to **10 distinct rule identifiers**. The difference: multiple scenarios can emit the same rule ID when they detect the same kind of omission in different contexts.

| Rule Identifier | Category | Config Toggle | Detection Scenarios |
|----------------|----------|---------------|-------------------|
| `missing-raises` | required | `require-raises` | Functions/methods with `raise` statements lacking `Raises:` section |
| `missing-yields` | required | `require-yields` | Generator functions with `yield` lacking `Yields:` section |
| `missing-receives` | required | `require-receives` | Generators using `value = yield` lacking `Receives:` section |
| `missing-warns` | required | `require-warns` | Functions calling `warnings.warn()` lacking `Warns:` section |
| `missing-other-parameters` | recommended | `require-other-parameters` | Functions with `**kwargs` lacking `Other Parameters:` section |
| `missing-attributes` | required | `require-attributes` | Classes with `__init__` self-assignments, dataclasses, NamedTuples, TypedDicts, `__init__.py` modules -- all lacking `Attributes:` section |
| `missing-typed-attributes` | recommended | `require-typed-attributes` | `Attributes:` sections without `name (type): desc` format |
| `missing-examples` | recommended | `require-examples` (list) | Public symbols in the `require-examples` list (class, protocol, dataclass, enum) lacking `Examples:` section; `__init__.py` modules lacking `Examples:` |
| `missing-cross-references` | recommended | `require-cross-references` | `See Also:` sections without cross-reference syntax; `__init__.py` modules lacking `See Also:` section |
| `prefer-fenced-code-blocks` | recommended | `prefer-fenced-code-blocks` | `Examples:` sections using `>>>` doctest format instead of fenced code blocks |

**Key consolidations:**

- **`missing-attributes` covers all class-like constructs**: plain classes (via `__init__` self-assignments), dataclasses, NamedTuples, TypedDicts, and `__init__.py` module-level exports. One rule, one identifier, one toggle -- the detection logic branches internally by construct type. This is the most complex rule with 5 detection branches, but the output is always one finding per symbol.
- **`__init__.py` module rules are not separate rules**: they are existing rules (`missing-attributes`, `missing-examples`, `missing-cross-references`) applied to module-level symbols. No new rule identifiers needed.
- **`missing-examples` is controlled by a list, not a boolean**: `require-examples = ["class", "protocol", "dataclass", "enum"]` specifies which symbol types trigger the rule. Empty list disables it entirely.

### Config Schema Update

The existing `EnrichmentConfig` has 9 boolean toggles + 1 list. The rule taxonomy reveals one config gap:

**New toggle needed:** `require-attributes: bool = True`

This controls the `missing-attributes` rule. Without it, there's no way to disable Attributes checking for teams that don't document class fields in docstrings (preferring type annotations alone). Since `missing-attributes` is a `required` category rule, the toggle defaults to `True`. This is a backward-compatible addition -- new field with a default value, no existing code breaks.

**Updated `EnrichmentConfig` (10 booleans + 1 list):**

```toml
[tool.docvet.enrichment]
require-raises = true              # missing-raises
require-yields = true              # missing-yields
require-receives = true            # missing-receives
require-warns = true               # missing-warns
require-other-parameters = true    # missing-other-parameters
require-attributes = true          # missing-attributes (NEW)
require-typed-attributes = true    # missing-typed-attributes
require-cross-references = true    # missing-cross-references
prefer-fenced-code-blocks = true   # prefer-fenced-code-blocks
require-examples = ["class", "protocol", "dataclass", "enum"]  # missing-examples
```

Every rule now has a corresponding toggle. No always-on rules -- every team can customize to their needs.

### Scripting & CI Support

- **Exit codes**: `0` = no findings (or all findings in `warn-on` checks), `1` = findings in `fail-on` checks. Controlled by top-level `fail-on` / `warn-on` lists, not by individual rules.
- **Output format**: `file:line: rule message` (one finding per line) -- greppable, parseable, familiar to ruff/ty users.
- **Summary line**: `N findings (X required, Y recommended)` -- printed after all findings when count > 0. Part of the CLI/reporting layer, not the enrichment module.
- **Composability**: `docvet enrichment` runs only the enrichment check. `docvet check` runs all enabled checks. Each check produces `list[Finding]` independently -- no shared state between checks.

### Technical Guidance for Implementation

- **Section detection**: Google-style docstring section headers (`Args:`, `Returns:`, `Raises:`, etc.) detected via regex/string matching on the raw docstring text. No third-party parser needed.
- **AST infrastructure**: Reuses existing `ast_utils.Symbol` dataclass for symbol extraction. `Symbol.kind` distinguishes functions, classes, methods, and modules. `Symbol.docstring` provides the raw docstring text for section analysis.
- **`__init__.py` detection**: `file_path` parameter enables checking `file_path.endswith("__init__.py")`. When true, apply module-specific rules (`missing-attributes` for exports, `missing-examples`, `missing-cross-references`) to the module-level symbol.
- **Dataclass/NamedTuple/TypedDict detection**: AST decorator inspection for `@dataclass`, base class inspection for `NamedTuple`/`TypedDict`. These are well-defined AST patterns.
- **Deduplication**: `missing-attributes` detection branches (plain class, dataclass, NamedTuple, TypedDict, module) are checked in priority order. First match emits the finding; subsequent branches for the same symbol are skipped.
- **No new runtime dependencies**: stdlib `ast` + existing `ast_utils` + `re` for section header matching.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP -- deliver the specific capability that fills the 4-year ecosystem gap in docstring section completeness checking. The scaffolding (CLI, config, discovery, AST helpers) is already implemented; this MVP adds the first real check module.

**Scope boundary — missing vs incomplete:** MVP rules detect **missing sections only**. A function that raises `ValueError` and `TypeError` but has no `Raises:` section at all triggers `missing-raises`. A function that has a `Raises:` section documenting `ValueError` but not `TypeError` does **not** trigger a finding -- that's an *incomplete* section, which is a Growth feature (analogous to how ruff D417 checks param completeness but docvet Layer 3 checks section presence). This boundary keeps detection logic simple and false-positive risk low.

### MVP Feature Set (Phase 1)

**Core User Journeys Enabled:** All five journeys. The enrichment module is the single deliverable that enables all journeys. Note: Journey 3 (CI exit codes) and Journey 5 (summary line) also depend on CLI/reporting layer behavior that exists as stubs -- full journey completion requires wiring those stubs, which is out of enrichment module scope but in the same release scope.

**Prerequisite Deliverables (ship before main enrichment PR):**

1. **Config update PR:** Add `require-attributes: bool = True` to `EnrichmentConfig`, update `_VALID_ENRICHMENT_KEYS`, update `_parse_enrichment` validation, update affected tests. Small, isolated change.
2. **`checks` package PR:** Create `src/docvet/checks/__init__.py` with `Finding` dataclass. Establishes the shared type contract for all future checks. `Finding` is a frozen API -- its 6-field shape (`file`, `line`, `symbol`, `rule`, `message`, `category`) must remain stable across checks.

**Main Deliverable:**

- `check_enrichment(source, tree, config, file_path) -> list[Finding]` pure function in `checks/enrichment.py`
- All 10 rule identifiers covering 14 detection scenarios (missing section detection only, not incomplete section detection)
- Full respect for all 11 config toggles (10 booleans + `require-examples` list)
- Google-style section header detection for: `Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:` (8 headers detected; `Args:` and `Returns:` recognized but not checked for absence -- that's ruff's territory)
- One finding per symbol per rule (deduplication guarantee)
- Zero findings on complete, well-documented code
- Comprehensive unit tests using source string fixtures (≥85% project-wide coverage; aim for ≥90% on `checks/enrichment.py` specifically)
- Tests against existing fixture files (`missing_raises.py`, `missing_yields.py`, `complete_module.py`)
- CLI wiring via existing `_run_enrichment` stub in `cli.py`

### Post-MVP Features

**Phase 2 (Growth):**

Sequencing TBD based on early adopter feedback. Candidates:

- Inline suppression: `# docvet: ignore[missing-raises]`
- JSON output format for CI integration pipelines
- Incomplete section detection (e.g., `Raises:` section exists but doesn't cover all raised exceptions)
- `--fix` suggestions (auto-insert empty section skeletons)
- Rule documentation URLs in findings (ruff pattern)
- Per-rule severity override in config
- SARIF output format

**Phase 3 (Vision):**

- Editor/LSP integration for real-time feedback
- GitHub Actions annotation format for PR inline comments
- Cross-check intelligence (enrichment + freshness combined findings)
- Numpy/Sphinx docstring style support

### Risk Mitigation Strategy

**Technical Risks:**

- `missing-attributes` has 5 detection branches with deduplication -- mitigated by implementing and testing each branch independently before composition
- Section header regex accuracy -- mitigated by starting with strict matching (exact names, correct indentation) and relaxing based on user feedback
- `Finding` is a frozen API consumed by all future checks -- mitigated by shipping it as a prerequisite PR with deliberate review before enrichment logic builds on it

**Market Risks:** Minimal -- verified ecosystem gap (darglint unmaintained since 2022, ruff stops at D417). No competing tool covers this space.

**Resource Risks:** Solo developer, but module is self-contained with no external dependencies. Scaffolding already built. Three-PR sequencing (config → Finding → enrichment) keeps each PR reviewable and CI-friendly. Risk is timeline, not feasibility.

## Functional Requirements

### Section Detection

- **FR1:** The system can detect functions and methods that contain `raise` statements but lack a `Raises:` section in their docstring
- **FR2:** The system can detect generator functions that contain `yield` expressions but lack a `Yields:` section in their docstring
- **FR3:** The system can detect generators that use the `value = yield` send pattern but lack a `Receives:` section in their docstring
- **FR4:** The system can detect functions that call `warnings.warn()` but lack a `Warns:` section in their docstring
- **FR5:** The system can detect functions with `**kwargs` parameters but lack an `Other Parameters:` section in their docstring
- **FR6:** The system can detect classes with `__init__` self-assignments that lack an `Attributes:` section in their docstring
- **FR7:** The system can detect dataclasses, NamedTuples, and TypedDicts with fields that lack an `Attributes:` section in their docstring
- **FR8:** The system can detect `__init__.py` modules that lack an `Attributes:` section documenting their exports
- **FR9:** The system can detect public symbols (configurable by type) that lack an `Examples:` section in their docstring
- **FR10:** The system can detect `__init__.py` modules that lack an `Examples:` section in their docstring
- **FR11:** The system can detect `Attributes:` sections that lack typed format (`name (type): description`)
- **FR12:** The system can detect `See Also:` sections that lack cross-reference syntax
- **FR13:** The system can detect `__init__.py` modules that lack a `See Also:` section in their docstring
- **FR14:** The system can detect `Examples:` sections that use `>>>` doctest format instead of fenced code blocks
- **FR15:** The system can recognize `Args:` and `Returns:` section headers for docstring parsing context without checking for their absence

### Finding Production

- **FR16:** The system can produce a structured finding for each detected issue, carrying file path, line number, symbol name, rule identifier, human-readable message, and category
- **FR17:** The system can categorize each finding as `required` (misleading omission) or `recommended` (improvement opportunity) based on the rule definition
- **FR18:** The system can produce at most one finding per symbol per rule, even when multiple detection branches match the same symbol
- **FR19:** The system can produce zero findings when analyzing well-documented code with complete docstrings
- **FR20:** The system can produce zero findings for symbols that have no docstring
- **FR21:** The system can produce findings only for missing sections, not for sections that exist but are incomplete
- **FR22:** The system can provide Finding as an immutable (frozen) dataclass that cannot be modified after creation

### Rule Management

- **FR23:** The system can identify each finding with a stable, human-readable kebab-case rule identifier (e.g., `missing-raises`, `missing-yields`)
- **FR24:** A developer can reference rule identifiers in configuration, output filtering, and issue tracking
- **FR25:** The system can map 14 detection scenarios to 10 distinct rule identifiers, applying the same rule ID across related detection contexts

### Configuration

- **FR26:** A developer can enable or disable each of the 10 rules independently via boolean toggles in `[tool.docvet.enrichment]`
- **FR27:** A developer can configure which symbol types trigger the `missing-examples` rule via a list of type names (class, protocol, dataclass, enum)
- **FR28:** The system can validate `require-examples` entries against known symbol types, rejecting unrecognized entries at config load time
- **FR29:** A developer can disable all enrichment findings by setting `require-examples = []` and all boolean toggles to `false`
- **FR30:** The system can apply defaults (all rules enabled, `require-examples = ["class", "protocol", "dataclass", "enum"]`) when no enrichment configuration is provided
- **FR31:** The system can recognize 8 Google-style section headers (`Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:`) for missing section detection

### Symbol Analysis

- **FR32:** The system can analyze function and method symbols for raise statements, yield expressions, send patterns, warnings calls, and kwargs parameters
- **FR33:** The system can analyze class symbols to determine construct type (plain class with `__init__`, dataclass, NamedTuple, TypedDict)
- **FR34:** The system can analyze module symbols to determine if the source file is an `__init__.py`
- **FR35:** The system can extract and parse raw docstring text from symbols to identify which sections are present
- **FR36:** The system can analyze any symbol with a non-empty docstring, regardless of docstring length or section count
- **FR37:** The system can distinguish between symbols that have a docstring (analyze for completeness) and symbols with no docstring (skip -- presence checking is interrogate's job)
- **FR38:** The system can process docstrings with broken indentation, missing section-header colons, or non-standard header names without raising exceptions, producing zero findings for symbols whose docstrings cannot be reliably parsed

### Integration

- **FR39:** The system can accept source code, a parsed AST, configuration, and file path as inputs and return a list of findings as output
- **FR40:** The system can operate as a pure function with no I/O, no side effects, and deterministic output
- **FR41:** The system can provide `Finding` as a shared type importable by all check modules without cross-check dependencies
- **FR42:** A developer can run the enrichment check standalone via `docvet enrichment` or as part of all checks via `docvet check`

## Non-Functional Requirements

### Performance

- **NFR1:** The enrichment check can analyze a single file (≤1000 lines) in under 50ms -- aspirational benchmark validated during implementation, not a CI-enforced gate
- **NFR2:** The enrichment check can process a 200-file codebase via `docvet enrichment --all` in under 5 seconds on commodity hardware -- aspirational benchmark; the real gate is "fast enough for pre-commit hooks and CI pipelines without noticeable delay"
- **NFR3:** The enrichment check adds no measurable overhead beyond AST parsing
- **NFR4:** Memory usage scales linearly with file count, not quadratically -- each file is processed independently with no cross-file state (design invariant, not tested explicitly)

### Correctness

- **NFR5:** The enrichment check produces zero false positives on well-documented code with complete docstrings (deterministic, reproducible)
- **NFR6:** The enrichment check produces identical output for identical input regardless of execution environment, time, or ordering
- **NFR7:** Malformed docstrings (broken indentation, missing colons, non-standard headers) result in zero findings for that symbol, never a crash or traceback
- **NFR8:** The enrichment check never modifies input data -- `source`, `tree`, and `config` remain unchanged after execution
- **NFR9:** Finding messages are actionable -- each message names the specific symbol, the specific issue, and what section is missing, enabling the developer to fix the problem without additional context

### Maintainability

- **NFR10:** Each of the 10 rules can be understood, modified, and tested independently without knowledge of other rules
- **NFR11:** Adding a new detection rule requires changes to at most 3 files: the rule implementation (`enrichment.py`), its config toggle (`config.py`), and its tests (`test_enrichment.py`)
- **NFR12:** Test coverage on `checks/enrichment.py` targets ≥90% (aspirational, not CI-enforced), with project-wide coverage maintaining the ≥85% CI gate
- **NFR13:** All quality gates pass: ruff check, ruff format, ty check, pytest, interrogate (95% docstring coverage)

### Compatibility

- **NFR14:** The enrichment check works on Python 3.12 and 3.13 (CI tests both versions)
- **NFR15:** The enrichment check works on Linux, macOS, and Windows without platform-specific code paths
- **NFR16:** No new runtime dependencies -- stdlib `ast`, `re`, and existing `ast_utils` only

### Integration

- **NFR17:** `Finding`'s 6-field shape (`file`, `line`, `symbol`, `rule`, `message`, `category`) is stable for v1 -- no fields are added, removed, or renamed within the v1 lifecycle
- **NFR18:** The enrichment check integrates with the existing CLI dispatch pattern (`_run_enrichment` stub) without requiring changes to CLI argument parsing or global option handling
- **NFR19:** Config additions (`require-attributes` toggle) are backward-compatible -- existing `pyproject.toml` files without this key continue to work with the default value
