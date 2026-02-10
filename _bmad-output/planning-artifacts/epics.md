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
status: 'complete'
freshnessStartedAt: '2026-02-09'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/prd-validation-report.md'
---

# docvet - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for docvet, decomposing the requirements from the PRD and Architecture into implementable stories for the **enrichment check module** (Layer 3: completeness).

## Requirements Inventory

### Functional Requirements

**Section Detection (FR1-FR15):**

- FR1: The system can detect functions and methods that contain `raise` statements but lack a `Raises:` section in their docstring
- FR2: The system can detect generator functions that contain `yield` expressions but lack a `Yields:` section in their docstring
- FR3: The system can detect generators that use the `value = yield` send pattern but lack a `Receives:` section in their docstring
- FR4: The system can detect functions that call `warnings.warn()` but lack a `Warns:` section in their docstring
- FR5: The system can detect functions with `**kwargs` parameters but lack an `Other Parameters:` section in their docstring
- FR6: The system can detect classes with `__init__` self-assignments that lack an `Attributes:` section in their docstring
- FR7: The system can detect dataclasses, NamedTuples, and TypedDicts with fields that lack an `Attributes:` section in their docstring
- FR8: The system can detect `__init__.py` modules that lack an `Attributes:` section documenting their exports
- FR9: The system can detect public symbols (configurable by type) that lack an `Examples:` section in their docstring
- FR10: The system can detect `__init__.py` modules that lack an `Examples:` section in their docstring
- FR11: The system can detect `Attributes:` sections that lack typed format (`name (type): description`)
- FR12: The system can detect `See Also:` sections that lack cross-reference syntax
- FR13: The system can detect `__init__.py` modules that lack a `See Also:` section in their docstring
- FR14: The system can detect `Examples:` sections that use `>>>` doctest format instead of fenced code blocks
- FR15: The system can recognize `Args:` and `Returns:` section headers for docstring parsing context without checking for their absence

**Finding Production (FR16-FR22):**

- FR16: The system can produce a structured finding for each detected issue, carrying file path, line number, symbol name, rule identifier, human-readable message, and category
- FR17: The system can categorize each finding as `required` (misleading omission) or `recommended` (improvement opportunity) based on the rule definition
- FR18: The system can produce at most one finding per symbol per rule, even when multiple detection branches match the same symbol
- FR19: The system can produce zero findings when analyzing well-documented code with complete docstrings
- FR20: The system can produce zero findings for symbols that have no docstring
- FR21: The system can produce findings only for missing sections, not for sections that exist but are incomplete
- FR22: The system can provide Finding as an immutable (frozen) dataclass that cannot be modified after creation

**Rule Management (FR23-FR25):**

- FR23: The system can identify each finding with a stable, human-readable kebab-case rule identifier (e.g., `missing-raises`, `missing-yields`)
- FR24: A developer can reference rule identifiers in configuration, output filtering, and issue tracking
- FR25: The system can map 14 detection scenarios to 10 distinct rule identifiers, applying the same rule ID across related detection contexts

**Configuration (FR26-FR31):**

- FR26: A developer can enable or disable each of the 10 rules independently via boolean toggles in `[tool.docvet.enrichment]`
- FR27: A developer can configure which symbol types trigger the `missing-examples` rule via a list of type names (class, protocol, dataclass, enum)
- FR28: The system can validate `require-examples` entries against known symbol types, rejecting unrecognized entries at config load time
- FR29: A developer can disable all enrichment findings by setting `require-examples = []` and all boolean toggles to `false`
- FR30: The system can apply defaults (all rules enabled, `require-examples = ["class", "protocol", "dataclass", "enum"]`) when no enrichment configuration is provided
- FR31: The system can recognize 8 Google-style section headers (`Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:`) for missing section detection

**Symbol Analysis (FR32-FR38):**

- FR32: The system can analyze function and method symbols for raise statements, yield expressions, send patterns, warnings calls, and kwargs parameters
- FR33: The system can analyze class symbols to determine construct type (plain class with `__init__`, dataclass, NamedTuple, TypedDict)
- FR34: The system can analyze module symbols to determine if the source file is an `__init__.py`
- FR35: The system can extract and parse raw docstring text from symbols to identify which sections are present
- FR36: The system can analyze any symbol with a non-empty docstring, regardless of docstring length or section count
- FR37: The system can distinguish between symbols that have a docstring (analyze for completeness) and symbols with no docstring (skip -- presence checking is interrogate's job)
- FR38: The system can process docstrings with broken indentation, missing section-header colons, or non-standard header names without raising exceptions, producing zero findings for symbols whose docstrings cannot be reliably parsed

**Integration (FR39-FR42):**

- FR39: The system can accept source code, a parsed AST, configuration, and file path as inputs and return a list of findings as output
- FR40: The system can operate as a pure function with no I/O, no side effects, and deterministic output
- FR41: The system can provide `Finding` as a shared type importable by all check modules without cross-check dependencies
- FR42: A developer can run the enrichment check standalone via `docvet enrichment` or as part of all checks via `docvet check`

### NonFunctional Requirements

**Performance (NFR1-NFR4):**

- NFR1: The enrichment check can analyze a single file (<=1000 lines) in under 50ms (aspirational benchmark, not CI-enforced)
- NFR2: The enrichment check can process a 200-file codebase via `docvet enrichment --all` in under 5 seconds on commodity hardware (aspirational)
- NFR3: The enrichment check adds no measurable overhead beyond AST parsing
- NFR4: Memory usage scales linearly with file count, not quadratically (each file processed independently with no cross-file state)

**Correctness (NFR5-NFR9):**

- NFR5: The enrichment check produces zero false positives on well-documented code with complete docstrings (deterministic, reproducible)
- NFR6: The enrichment check produces identical output for identical input regardless of execution environment, time, or ordering
- NFR7: Malformed docstrings (broken indentation, missing colons, non-standard headers) result in zero findings for that symbol, never a crash or traceback
- NFR8: The enrichment check never modifies input data (source, tree, and config remain unchanged after execution)
- NFR9: Finding messages are actionable (each message names the specific symbol, the specific issue, and what section is missing)

**Maintainability (NFR10-NFR13):**

- NFR10: Each of the 10 rules can be understood, modified, and tested independently without knowledge of other rules
- NFR11: Adding a new detection rule requires changes to at most 3 files: the rule implementation, its config toggle, and its tests
- NFR12: Test coverage on `checks/enrichment.py` targets >=90% (aspirational), with project-wide coverage maintaining the >=85% CI gate
- NFR13: All quality gates pass: ruff check, ruff format, ty check, pytest, interrogate (95% docstring coverage)

**Compatibility (NFR14-NFR16):**

- NFR14: The enrichment check works on Python 3.12 and 3.13 (CI tests both versions)
- NFR15: The enrichment check works on Linux, macOS, and Windows without platform-specific code paths
- NFR16: No new runtime dependencies (stdlib `ast`, `re`, and existing `ast_utils` only)

**Integration (NFR17-NFR19):**

- NFR17: `Finding`'s 6-field shape (`file`, `line`, `symbol`, `rule`, `message`, `category`) is stable for v1
- NFR18: The enrichment check integrates with the existing CLI dispatch pattern (`_run_enrichment` stub) without requiring changes to CLI argument parsing or global option handling
- NFR19: Config additions (`require-attributes` toggle) are backward-compatible (existing `pyproject.toml` files without this key continue to work with the default value)

### Additional Requirements

**From Architecture:**

- No starter template needed -- brownfield project with scaffolding already implemented
- Prerequisite PR 1: Add `require_attributes: bool = True` to `EnrichmentConfig`, update `_VALID_ENRICHMENT_KEYS`, update `_parse_enrichment` validation, update affected tests
- Prerequisite PR 2: Create `src/docvet/checks/__init__.py` with `Finding` frozen dataclass (6 fields: `file`, `line`, `symbol`, `rule`, `message`, `category`)
- Implementation sequence: config toggle -> Finding dataclass -> section parsing constants/functions -> node index builder -> 10 `_check_*` functions -> `check_enrichment` orchestrator
- `missing-attributes` dispatch order is an architectural constraint: dataclass -> NamedTuple -> TypedDict -> plain class -> `__init__.py` module (first-match-wins, no fallthrough)
- Config gating lives in the orchestrator, not inside `_check_*` functions
- Defensive error handling: no try/except in MVP; correctness through design (regex returns empty set, `.get()` returns None)
- Dual testing strategy: simple rules tested through `check_enrichment` orchestrator; `missing-attributes` tested directly + per-helper + integration
- Private function per rule with uniform signature: `_check_*(symbol, sections, node_index, config, file_path) -> Finding | None`
- Single compiled regex for section header matching (`_SECTION_PATTERN`)
- Line-based node index (`_build_node_index`) for O(1) AST node lookup per symbol
- Finding construction uses literal strings for `rule` and `category` (no dynamic strings)
- Taxonomy-table order for both function definitions and dispatch

**From Validation Report:**

- FR12 ("cross-reference syntax") is the weakest FR -- never formally defined; tech spec must define what constitutes valid cross-reference syntax
- FR8 ambiguity: "exports" in `__init__.py` context needs clarification (is it `__all__`, public names, or both?)
- FR11 needs explicit pattern: `name (type): description` as expected match vs `name: description` as violation
- 4 rules lack user journey demonstration: `missing-receives`, `missing-other-parameters`, `missing-cross-references`, `prefer-fenced-code-blocks`
- Decorator alias detection (e.g., `from dataclasses import dataclass as dc`) is explicitly out of MVP scope
- `async` generator edge cases (`async for`/`async with` interaction with `missing-yields`/`missing-receives`) not explicitly addressed

### FR Coverage Map

| FR | Epic | Brief Description |
|----|------|-------------------|
| FR1 | Epic 1 | Detect missing Raises section |
| FR2 | Epic 1 | Detect missing Yields section |
| FR3 | Epic 1 | Detect missing Receives section |
| FR4 | Epic 1 | Detect missing Warns section |
| FR5 | Epic 1 | Detect missing Other Parameters section |
| FR6 | Epic 2 | Detect missing Attributes on plain classes |
| FR7 | Epic 2 | Detect missing Attributes on dataclasses/NamedTuples/TypedDicts |
| FR8 | Epic 2 | Detect missing Attributes on `__init__.py` modules |
| FR9 | Epic 3 | Detect missing Examples on configurable symbol types |
| FR10 | Epic 3 | Detect missing Examples on `__init__.py` modules |
| FR11 | Epic 3 | Detect untyped Attributes format |
| FR12 | Epic 3 | Detect missing cross-reference syntax in See Also |
| FR13 | Epic 3 | Detect missing See Also on `__init__.py` modules |
| FR14 | Epic 3 | Detect doctest format instead of fenced code blocks |
| FR15 | Epic 1 | Recognize Args/Returns headers for parsing context |
| FR16 | Epic 1 | Finding dataclass with 6 fields |
| FR17 | Epic 1 | Finding category (required/recommended) |
| FR18 | Epic 1 | One finding per symbol per rule deduplication |
| FR19 | Epic 1 | Zero findings on clean code |
| FR20 | Epic 1 | Zero findings for undocumented symbols |
| FR21 | Epic 1 | Missing-only detection (not incomplete) |
| FR22 | Epic 1 | Finding is frozen/immutable |
| FR23 | Epic 1 | Kebab-case rule identifiers |
| FR24 | Epic 1 | Rule IDs usable in config/filtering/tracking |
| FR25 | Epic 1 | 14 scenarios -> 10 rule ID mapping |
| FR26 | Epic 1 | Per-rule boolean config toggles |
| FR27 | Epic 3 | `require-examples` list config |
| FR28 | Epic 1 | Validate `require-examples` entries |
| FR29 | Epic 1 | Disable all findings via config |
| FR30 | Epic 1 | Sensible defaults when no config provided |
| FR31 | Epic 1 | Recognize 8 Google-style section headers |
| FR32 | Epic 1 | Analyze functions for raise/yield/warn/kwargs patterns |
| FR33 | Epic 2 | Analyze class construct types |
| FR34 | Epic 2 | Analyze module symbols for `__init__.py` |
| FR35 | Epic 1 | Extract and parse docstring sections |
| FR36 | Epic 1 | Analyze any symbol with non-empty docstring |
| FR37 | Epic 1 | Distinguish documented vs undocumented symbols |
| FR38 | Epic 1 | Handle malformed docstrings gracefully |
| FR39 | Epic 1 | Pure function API: source, tree, config, file_path -> findings |
| FR40 | Epic 1 | No I/O, no side effects, deterministic |
| FR41 | Epic 1 | Finding as shared type for all check modules |
| FR42 | Epic 1 | CLI wiring: `docvet enrichment` and `docvet check` |
| FR43 | Epic 4 | Parse git diff output for changed hunk line ranges |
| FR44 | Epic 4 | Map changed lines to AST symbols |
| FR45 | Epic 4 | Classify changed lines as signature/docstring/body |
| FR46 | Epic 4 | Detect code change without docstring update |
| FR47 | Epic 4 | HIGH severity for signature changes |
| FR48 | Epic 4 | MEDIUM severity for body-only changes |
| FR49 | Epic 4 | LOW severity for import/formatting-only changes |
| FR50 | Epic 5 | Parse git blame --line-porcelain for timestamps |
| FR51 | Epic 5 | Group timestamps by symbol |
| FR52 | Epic 5 | Detect drift exceeding threshold |
| FR53 | Epic 5 | Detect docstring age exceeding threshold |
| FR54 | Epic 4+5 | Skip no-docstring symbols (both modes) |
| FR55 | Epic 4 | Zero findings for new files |
| FR56 | Epic 4 | Handle deleted functions gracefully |
| FR57 | Epic 4 | Treat relocation as delete-plus-add |
| FR58 | Epic 4 | Skip binary/non-Python files |
| FR59 | Epic 4 | Structured finding production |
| FR60 | Epic 4 | Reuse shared Finding dataclass |
| FR61 | Epic 4+5 | One finding per symbol per rule, highest severity wins |
| FR62 | Epic 4+5 | Zero findings when docstrings are up-to-date |
| FR63 | Epic 5 | Configurable drift threshold |
| FR64 | Epic 5 | Configurable age threshold |
| FR65 | Epic 5 | Default thresholds |
| FR66 | Epic 4+5 | Pure function API (file_path, git output, AST → findings) |
| FR67 | Epic 4+5 | CLI: `docvet freshness` (Epic 4 diff, Epic 5 drift) |
| FR68 | Epic 4+5 | CLI: diff default (Epic 4), `--mode drift` (Epic 5) |

## Epic List

### Epic 1: Function-Level Enrichment Detection

A developer can run `docvet enrichment` and get findings for missing `Raises:`, `Yields:`, `Receives:`, `Warns:`, and `Other Parameters:` sections on functions and methods — end-to-end from CLI invocation to terminal output. Includes the shared `Finding` dataclass, config updates, section parser, node index, 5 function-level `_check_*` rules, `check_enrichment` orchestrator, and CLI wiring.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR28, FR29, FR30, FR31, FR32, FR35, FR36, FR37, FR38, FR39, FR40, FR41, FR42

### Story 1.1: Add `require_attributes` Config Toggle

As a developer,
I want a `require-attributes` boolean toggle in `[tool.docvet.enrichment]`,
So that teams can enable or disable Attributes checking for classes independently.

**Acceptance Criteria:**

**Given** an `EnrichmentConfig` with no explicit `require-attributes` setting
**When** the config is loaded from `pyproject.toml`
**Then** `require_attributes` defaults to `True`

**Given** a `pyproject.toml` with `require-attributes = false` under `[tool.docvet.enrichment]`
**When** the config is loaded
**Then** `require_attributes` is `False`

**Given** an existing `pyproject.toml` without a `require-attributes` key
**When** the config is loaded
**Then** all existing config fields retain their values and no error is raised (backward-compatible)

**Given** the `_VALID_ENRICHMENT_KEYS` set in `config.py`
**When** inspected
**Then** it includes `"require-attributes"`

**Given** the `_parse_enrichment` function
**When** it receives an unknown key (e.g., `require-foo = true`)
**Then** it rejects the key at config load time with a clear error message

**FRs:** FR26, FR29, FR30, NFR19

### Story 1.2: Create `Finding` Dataclass

As a developer,
I want a shared, immutable `Finding` dataclass in `checks/__init__.py`,
So that all check modules produce findings with a consistent, stable structure.

**Acceptance Criteria:**

**Given** the `checks/__init__.py` module
**When** imported
**Then** it exports `Finding` as the only public name

**Given** a `Finding` instance
**When** constructed with `file`, `line`, `symbol`, `rule`, `message`, `category`
**Then** all 6 fields are accessible and the instance is frozen (immutable)

**Given** a `Finding` instance
**When** any field assignment is attempted (e.g., `finding.rule = "new"`)
**Then** a `FrozenInstanceError` is raised

**Given** the `category` field
**When** a `Finding` is constructed
**Then** it accepts `"required"` or `"recommended"` as valid values

**Given** the `rule` field
**When** a `Finding` is constructed
**Then** it accepts any string (kebab-case rule identifiers like `"missing-raises"`)

**FRs:** FR16, FR17, FR22, FR23, FR41, NFR17

### Story 1.3: Section Header Parser and Node Index

As a developer,
I want shared infrastructure for parsing docstring sections and indexing AST nodes,
So that all enrichment rules can efficiently determine which sections exist and look up AST nodes.

**Acceptance Criteria:**

**Given** a docstring containing `Raises:`, `Yields:`, and `Args:` section headers
**When** `_parse_sections(docstring)` is called
**Then** it returns `{"Raises", "Yields", "Args"}`

**Given** a docstring with varied indentation (e.g., module-level with no indent, method-level with 8-space indent)
**When** `_parse_sections(docstring)` is called
**Then** it correctly identifies section headers regardless of leading whitespace

**Given** a docstring with no recognized section headers
**When** `_parse_sections(docstring)` is called
**Then** it returns an empty set (never raises an exception)

**Given** a malformed docstring with broken indentation or missing colons
**When** `_parse_sections(docstring)` is called
**Then** it returns an empty set (graceful degradation, no crash)

**Given** `_SECTION_HEADERS` constant
**When** inspected
**Then** it contains all 10 recognized headers: `Args`, `Returns`, `Raises`, `Yields`, `Receives`, `Warns`, `Other Parameters`, `Attributes`, `Examples`, `See Also`

**Given** an `ast.Module` tree with functions, classes, and async functions
**When** `_build_node_index(tree)` is called
**Then** it returns a `dict[int, ast.AST]` mapping line numbers to `FunctionDef | AsyncFunctionDef | ClassDef` nodes

**Given** a module-level symbol (line 1) with no corresponding AST node
**When** `node_index.get(symbol.line)` is called
**Then** it returns `None` (safe for rules to handle)

**FRs:** FR15, FR31, FR35, FR36, FR38, NFR7

### Story 1.4: Missing Raises Detection and Orchestrator

As a developer,
I want to detect functions that raise exceptions without documenting them in a `Raises:` section,
So that I can ensure my docstrings accurately describe error behavior for callers.

**Acceptance Criteria:**

**Given** a function with `raise ValueError` and a docstring with no `Raises:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-raises"`, `category="required"`, and a message naming the function and the exception

**Given** a function with `raise ValueError` and a docstring containing a `Raises:` section
**When** `check_enrichment` is called
**Then** it returns zero findings for that function (missing-only, not incomplete)

**Given** a function with no `raise` statements
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-raises` on that function

**Given** a function with `raise` but no docstring at all
**When** `check_enrichment` is called
**Then** it returns zero findings (undocumented symbols are skipped)

**Given** `config.require_raises = False`
**When** `check_enrichment` is called on a function with `raise` and no `Raises:` section
**Then** it returns zero findings for `missing-raises` (config toggle respected)

**Given** a well-documented file (`tests/fixtures/complete_module.py`)
**When** `check_enrichment` is called
**Then** it returns an empty list (zero findings)

**Given** `tests/fixtures/missing_raises.py`
**When** `check_enrichment` is called
**Then** it returns exactly the expected `missing-raises` finding

**Given** the `check_enrichment` orchestrator
**When** called with `source`, `tree`, `config`, `file_path`
**Then** it returns `list[Finding]` with no I/O and no side effects (pure function)

**FRs:** FR1, FR18, FR19, FR20, FR21, FR24, FR25, FR32, FR37, FR39, FR40, NFR5, NFR6, NFR8, NFR9

### Story 1.5: Missing Yields and Receives Detection

As a developer,
I want to detect generator functions missing `Yields:` and `Receives:` sections,
So that consumers of my generators understand what values are yielded and what can be sent in.

**Acceptance Criteria:**

**Given** a generator function with `yield` expressions and a docstring with no `Yields:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-yields"`, `category="required"`

**Given** a generator function with `yield` and a docstring containing a `Yields:` section
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-yields`

**Given** `tests/fixtures/missing_yields.py`
**When** `check_enrichment` is called
**Then** it returns exactly the expected `missing-yields` finding

**Given** a generator function using `value = yield` (send pattern) with no `Receives:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-receives"`, `category="required"`

**Given** a generator with `value = yield` and a `Receives:` section present
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-receives`

**Given** `config.require_yields = False`
**When** `check_enrichment` is called on a generator missing `Yields:`
**Then** it returns zero findings for `missing-yields`

**Given** `config.require_receives = False`
**When** `check_enrichment` is called on a generator with send pattern missing `Receives:`
**Then** it returns zero findings for `missing-receives`

**Given** an async generator function with `yield`
**When** `check_enrichment` is called
**Then** it detects the `yield` via `ast.walk` on the `AsyncFunctionDef` body and applies the same rules

**FRs:** FR2, FR3, FR32, NFR5, NFR6

### Story 1.6: Missing Warns and Other Parameters Detection

As a developer,
I want to detect functions that call `warnings.warn()` without a `Warns:` section and functions with `**kwargs` without an `Other Parameters:` section,
So that my docstrings fully describe warning behavior and extra keyword arguments.

**Acceptance Criteria:**

**Given** a function calling `warnings.warn()` with no `Warns:` section in its docstring
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-warns"`, `category="required"`

**Given** a function calling `warnings.warn()` with a `Warns:` section present
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-warns`

**Given** `config.require_warns = False`
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-warns`

**Given** a function with `**kwargs` parameter and no `Other Parameters:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-other-parameters"`, `category="recommended"`

**Given** a function with `**kwargs` and an `Other Parameters:` section present
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-other-parameters`

**Given** `config.require_other_parameters = False`
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-other-parameters`

**Given** a function that calls `warnings.warn()` via a qualified path (e.g., `warnings.warn(...)`)
**When** `check_enrichment` is called
**Then** it detects the `warn` call via AST `Call` node inspection

**Given** all 5 function-level rules enabled with a function that triggers none of them
**When** `check_enrichment` is called
**Then** it returns zero findings for that function

**FRs:** FR4, FR5, FR32, NFR5, NFR10

### Story 1.7: CLI Wiring for Enrichment Check

As a developer,
I want to run `docvet enrichment` from the command line and see findings in `file:line: rule message` format,
So that I can integrate enrichment checking into my development workflow and CI pipelines.

**Acceptance Criteria:**

**Given** a codebase with files containing functions missing `Raises:` sections
**When** `docvet enrichment` is run
**Then** findings are printed to terminal in `file:line: rule message` format (one per line)

**Given** a codebase with no enrichment issues
**When** `docvet enrichment` is run
**Then** it produces no output and exits with code 0

**Given** the existing `_run_enrichment` stub in `cli.py`
**When** the enrichment check is wired
**Then** it reads each discovered file, calls `ast.parse()`, and passes `source`, `tree`, `config.enrichment`, and `file_path` to `check_enrichment`

**Given** a file that fails `ast.parse()` with `SyntaxError`
**When** `docvet enrichment` processes it
**Then** the file is skipped with a warning (not passed to `check_enrichment`)

**Given** `docvet check` is run (all checks)
**When** enrichment is in the enabled checks
**Then** enrichment findings are included alongside findings from other checks

**Given** `docvet enrichment --all` is run on a project
**When** the run completes
**Then** all Python files in the project are analyzed (not just git diff files)

**FRs:** FR42, NFR18

---

**Epic 1 Summary:** 7 stories, covering all 30 FRs assigned to this epic. Each story builds on the previous without forward dependencies.

### Epic 2: Class & Module Enrichment Detection

A developer can detect missing `Attributes:` sections across all class-like constructs (plain classes, dataclasses, NamedTuples, TypedDicts) and `__init__.py` modules. The highest-complexity rule with 5 detection branches, first-match-wins deduplication, and dedicated helper functions.

**FRs covered:** FR6, FR7, FR8, FR33, FR34

## Epic 2: Class & Module Enrichment Detection

A developer can detect missing `Attributes:` sections across all class-like constructs (plain classes, dataclasses, NamedTuples, TypedDicts) and `__init__.py` modules. The highest-complexity rule with 5 detection branches, first-match-wins deduplication, and dedicated helper functions.

### Story 2.1: Dataclass, NamedTuple, and TypedDict Attributes Detection

As a developer,
I want to detect dataclasses, NamedTuples, and TypedDicts that lack an `Attributes:` section,
So that users of my data structures can see all fields documented in one place.

**Acceptance Criteria:**

**Given** a class decorated with `@dataclass` and a docstring with no `Attributes:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`, and a message naming the class and its field count

**Given** a class decorated with `@dataclasses.dataclass` (qualified form)
**When** `check_enrichment` is called
**Then** it detects the dataclass and applies the same rule

**Given** a class decorated with `@dataclass(frozen=True)` (decorator with arguments)
**When** `check_enrichment` is called
**Then** it detects the dataclass via `ast.Call` node inspection

**Given** a class inheriting from `NamedTuple` (e.g., `class Foo(NamedTuple):`)
**When** `check_enrichment` is called and the docstring has no `Attributes:` section
**Then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`

**Given** a class inheriting from `typing.NamedTuple` (qualified base class)
**When** `check_enrichment` is called
**Then** it detects the NamedTuple via `ast.Attribute` base class inspection

**Given** a class inheriting from `TypedDict`
**When** `check_enrichment` is called and the docstring has no `Attributes:` section
**Then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`

**Given** a dataclass with a docstring containing an `Attributes:` section
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-attributes` on that class

**Given** `config.require_attributes = False`
**When** `check_enrichment` is called on any class-like construct missing `Attributes:`
**Then** it returns zero findings for `missing-attributes`

**Given** a dataclass with no docstring at all
**When** `check_enrichment` is called
**Then** it returns zero findings (undocumented symbols skipped)

**Given** the `_is_dataclass`, `_is_namedtuple`, and `_is_typeddict` helper functions
**When** tested directly with AST nodes
**Then** each correctly identifies its construct type and returns `False` for non-matching nodes

**FRs:** FR7, FR33, NFR5, NFR10

### Story 2.2: Plain Class and `__init__.py` Module Attributes Detection

As a developer,
I want to detect plain classes with `__init__` self-assignments and `__init__.py` modules that lack `Attributes:` sections,
So that all class fields and module exports are documented for consumers.

**Acceptance Criteria:**

**Given** a plain class with an `__init__` method containing `self.x = value` assignments and a docstring with no `Attributes:` section
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`

**Given** a plain class with `__init__` containing annotated assignments (`self.x: int = 0`)
**When** `check_enrichment` is called and the docstring has no `Attributes:` section
**Then** it detects the self-assignments via `ast.AnnAssign` and returns a finding

**Given** a plain class with `__init__` but no `self.*` assignments
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-attributes` on that class (no fields to document)

**Given** an `__init__.py` module with a module-level docstring but no `Attributes:` section
**When** `check_enrichment` is called with `file_path` ending in `__init__.py`
**Then** it returns a `Finding` with `rule="missing-attributes"`, `category="required"`, applied to the module-level symbol

**Given** an `__init__.py` module with an `Attributes:` section in its module docstring
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-attributes`

**Given** a regular Python file (not `__init__.py`) with a module-level docstring
**When** `check_enrichment` is called
**Then** it does not apply `__init__.py`-specific rules

**Given** a class that is both a `@dataclass` and has `__init__` self-assignments
**When** `check_enrichment` is called
**Then** it produces at most one `missing-attributes` finding (dataclass branch wins per first-match-wins dispatch order)

**Given** the full `_check_missing_attributes` dispatch
**When** evaluated on any symbol
**Then** branches are checked in order: dataclass, NamedTuple, TypedDict, plain class, `__init__.py` module — first match wins, no fallthrough

**Given** the `_has_self_assignments` and `_is_init_module` helper functions
**When** tested directly
**Then** each correctly identifies its pattern and returns `False` for non-matching inputs

**FRs:** FR6, FR8, FR18, FR33, FR34, NFR5, NFR10

---

**Epic 2 Summary:** 2 stories, covering all 5 FRs assigned to this epic. Story 2.1 handles structured class variants (dataclass, NamedTuple, TypedDict). Story 2.2 adds plain class and module detection, completing the full 5-branch dispatch.

### Epic 3: Format & Recommended Rules

A developer can detect format and style improvements — missing `Examples:` sections (configurable by symbol type), untyped `Attributes:` format, missing cross-references, and doctest-to-fenced-code-block preferences. Enables required vs recommended triage for codebase sweeps.

**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14, FR27

## Epic 3: Format & Recommended Rules

A developer can detect format and style improvements — missing `Examples:` sections (configurable by symbol type), untyped `Attributes:` format, missing cross-references, and doctest-to-fenced-code-block preferences. Enables required vs recommended triage for codebase sweeps.

### Story 3.1: Missing Examples Detection

As a developer,
I want to detect public symbols and `__init__.py` modules that lack an `Examples:` section,
So that key API surfaces include usage examples for consumers.

**Acceptance Criteria:**

**Given** a class with a docstring and no `Examples:` section, and `config.require_examples = ["class"]`
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-examples"`, `category="recommended"`

**Given** a protocol with a docstring and no `Examples:` section, and `config.require_examples = ["protocol"]`
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-examples"`, `category="recommended"`

**Given** a class with a docstring and no `Examples:` section, and `config.require_examples = ["dataclass"]` (class not in list)
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-examples` on that class

**Given** `config.require_examples = []` (empty list)
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-examples` on any symbol (rule fully disabled)

**Given** the default config (`require_examples = ["class", "protocol", "dataclass", "enum"]`)
**When** `check_enrichment` is called on a dataclass with no `Examples:` section
**Then** it returns a `Finding` for `missing-examples`

**Given** a symbol with a docstring containing an `Examples:` section
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-examples` on that symbol

**Given** an `__init__.py` module with a module-level docstring and no `Examples:` section
**When** `check_enrichment` is called with `file_path` ending in `__init__.py` and `require_examples` is non-empty
**Then** it returns a `Finding` with `rule="missing-examples"` for the module-level symbol

**Given** a symbol with no docstring
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-examples` (undocumented symbols skipped)

**FRs:** FR9, FR10, FR27, NFR5, NFR10

### Story 3.2: Format and Cross-Reference Rules

As a developer,
I want to detect untyped `Attributes:` sections, missing cross-reference syntax in `See Also:` sections, missing `See Also:` on `__init__.py` modules, and `Examples:` using doctest format instead of fenced code blocks,
So that my docstrings follow best practices for readability and mkdocs rendering.

**Acceptance Criteria:**

**Given** a class with an `Attributes:` section using `name: description` format (no type)
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-typed-attributes"`, `category="recommended"`

**Given** a class with an `Attributes:` section using `name (type): description` format
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-typed-attributes`

**Given** `config.require_typed_attributes = False`
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-typed-attributes`

**Given** a symbol with a `See Also:` section that lacks cross-reference syntax
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="missing-cross-references"`, `category="recommended"`

**Given** `config.require_cross_references = False`
**When** `check_enrichment` is called
**Then** it returns zero findings for `missing-cross-references`

**Given** an `__init__.py` module with a module-level docstring and no `See Also:` section
**When** `check_enrichment` is called with `file_path` ending in `__init__.py`
**Then** it returns a `Finding` with `rule="missing-cross-references"` for the module-level symbol

**Given** a regular Python file (not `__init__.py`) with no `See Also:` section
**When** `check_enrichment` is called
**Then** it does not produce a `missing-cross-references` finding for the module-level symbol

**Given** a symbol with an `Examples:` section using `>>>` doctest format
**When** `check_enrichment` is called
**Then** it returns a `Finding` with `rule="prefer-fenced-code-blocks"`, `category="recommended"`

**Given** a symbol with an `Examples:` section using fenced code blocks (triple backticks)
**When** `check_enrichment` is called
**Then** it returns zero findings for `prefer-fenced-code-blocks`

**Given** `config.prefer_fenced_code_blocks = False`
**When** `check_enrichment` is called
**Then** it returns zero findings for `prefer-fenced-code-blocks`

**Given** a symbol with no `Examples:` section at all
**When** `check_enrichment` is called
**Then** it returns zero findings for `prefer-fenced-code-blocks` (rule only applies when `Examples:` exists)

**FRs:** FR11, FR12, FR13, FR14, NFR5, NFR10

---

**Epic 3 Summary:** 2 stories, covering all 7 FRs assigned to this epic. Story 3.1 handles the list-config `missing-examples` rule. Story 3.2 covers the remaining docstring-only format and cross-reference rules.

### Epic 4: Freshness Diff Mode Detection

A developer can run `docvet freshness` and get findings for symbols where code changed but docstrings were not updated — HIGH severity for signature changes (`stale-signature`), MEDIUM for body changes (`stale-body`), LOW for import/formatting changes (`stale-import`). Includes shared infrastructure (`_build_finding`, module constants), all diff-specific edge case handling, unit + integration tests, and CLI wiring for diff mode as the default.

**FRs covered:** FR43, FR44, FR45, FR46, FR47, FR48, FR49, FR54, FR55, FR56, FR57, FR58, FR59, FR60, FR61 (diff), FR62 (diff), FR66 (diff), FR67 (diff wiring), FR68 (diff as default)

### Epic 5: Freshness Drift Mode & CLI Integration

A developer can run `docvet freshness --mode drift` and get findings for docstrings that have drifted from their code (`stale-drift`) or aged past a configurable threshold (`stale-age`). Adds blame parsing, threshold computation, drift configuration consumption, and the `--mode drift` CLI flag.

**FRs covered:** FR50, FR51, FR52, FR53, FR54 (verified), FR61 (drift), FR62 (drift), FR63, FR64, FR65, FR66 (drift), FR67 (drift wiring), FR68 (`--mode drift` flag)

## Epic 4: Freshness Diff Mode Detection

A developer can run `docvet freshness` and get findings for symbols where code changed but docstrings were not updated — HIGH severity for signature changes (`stale-signature`), MEDIUM for body changes (`stale-body`), LOW for import/formatting changes (`stale-import`). Includes shared infrastructure (`_build_finding`, module constants), all diff-specific edge case handling, unit + integration tests, and CLI wiring for diff mode as the default.

### Story 4.1: Diff Hunk Parser and Shared Infrastructure

As a developer,
I want a parser that extracts changed line numbers from git diff output and a shared finding builder,
So that diff mode has reliable input processing and freshness findings are constructed consistently.

**Acceptance Criteria:**

**Given** a git diff output string containing `@@ -10,5 +12,8 @@` hunk headers
**When** `_parse_diff_hunks(diff_output)` is called
**Then** it returns a `set[int]` containing the expanded line numbers from the `+start,count` ranges (e.g., `{12, 13, 14, 15, 16, 17, 18, 19}`)

**Given** a git diff output with `--- /dev/null` (new file)
**When** `_parse_diff_hunks(diff_output)` is called
**Then** it returns an empty set (FR55 — no prior docstring to become stale)

**Given** a git diff output containing `Binary files ... differ`
**When** `_parse_diff_hunks(diff_output)` is called
**Then** it returns an empty set (FR58 — skip binary files)

**Given** a hunk header with no count (`@@ -1 +1 @@`, missing `,count`)
**When** `_parse_diff_hunks(diff_output)` is called
**Then** it treats the missing count as 1 and includes that single line number

**Given** an empty string as `diff_output`
**When** `_parse_diff_hunks(diff_output)` is called
**Then** it returns an empty set (no crash, no exception)

**Given** a git diff output with rename headers (`rename from ...` / `rename to ...`) or mode change lines
**When** `_parse_diff_hunks(diff_output)` is called
**Then** those lines are silently skipped and only hunk headers are processed

**Given** the `_build_finding` shared helper
**When** called with `file_path`, `symbol`, `rule`, `message`, `category`
**Then** it returns a `Finding` with `file=file_path`, `line=symbol.line`, `symbol=symbol.name`, and the provided `rule`, `message`, `category`

**Given** the `_HUNK_PATTERN` module-level constant
**When** inspected
**Then** it is a compiled regex matching `^@@ .+\+(\d+)(?:,(\d+))? @@`

**FRs:** FR43, FR55, FR58, FR59 (partial), FR60 (partial), NFR25, NFR29

### Story 4.2: Line Classification and Diff Mode Orchestrator

As a developer,
I want to classify changed lines per symbol by range (signature, body, docstring) and produce findings at the appropriate severity level,
So that stale docstrings are detected with correct severity and docstring updates suppress findings.

**Acceptance Criteria:**

**Given** a symbol with changed lines in its `signature_range` and no changed lines in its `docstring_range`
**When** `_classify_changed_lines(changed_lines, symbol)` is called
**Then** it returns `"signature"` (FR47 — HIGH severity)

**Given** a symbol with changed lines in its `body_range` but not in `signature_range`, and no changed lines in its `docstring_range`
**When** `_classify_changed_lines(changed_lines, symbol)` is called
**Then** it returns `"body"` (FR48 — MEDIUM severity)

**Given** a symbol with changed lines only outside its `signature_range`, `docstring_range`, and `body_range`
**When** `_classify_changed_lines(changed_lines, symbol)` is called
**Then** it returns `"import"` (FR49 — LOW severity)

**Given** a symbol with changed lines in both `signature_range` and `docstring_range`
**When** `_classify_changed_lines(changed_lines, symbol)` is called
**Then** it returns `None` (docstring updated, finding suppressed — FR46, FR62)

**Given** a symbol with changed lines in both `body_range` and `docstring_range`
**When** `_classify_changed_lines(changed_lines, symbol)` is called
**Then** it returns `None` (docstring updated alongside body change)

**Given** a class or module symbol with `signature_range is None`
**When** `_classify_changed_lines(changed_lines, symbol)` is called with body changes
**Then** it returns `"body"` (MEDIUM), never `"signature"` (signature check skipped for classes/modules — NFR23)

**Given** a file with a function whose signature changed and docstring was not updated
**When** `check_freshness_diff(file_path, diff_output, tree)` is called
**Then** it returns a `Finding` with `rule="stale-signature"`, `category="required"`, and a message like `Function 'name' signature changed but docstring not updated`

**Given** a file with a method whose body changed and docstring was not updated
**When** `check_freshness_diff(file_path, diff_output, tree)` is called
**Then** it returns a `Finding` with `rule="stale-body"`, `category="recommended"`

**Given** a file where only import lines near a symbol changed
**When** `check_freshness_diff(file_path, diff_output, tree)` is called
**Then** it returns a `Finding` with `rule="stale-import"`, `category="recommended"`

**Given** a file where a symbol has both signature and body changes (no docstring change)
**When** `check_freshness_diff` is called
**Then** it produces exactly one finding at the highest severity (`stale-signature`, not both — FR61)

**Given** a symbol with no docstring (`docstring_range is None`)
**When** `check_freshness_diff` is called
**Then** it returns zero findings for that symbol (FR54 — undocumented symbols skipped)

**Given** a function that was deleted (lines appear in diff's `-` side but not in current AST)
**When** `check_freshness_diff` is called
**Then** it produces zero findings for that deleted function (FR56 — not in `map_lines_to_symbols`)

**Given** a function relocated within a file (delete at old location, add at new location)
**When** `check_freshness_diff` is called
**Then** it treats the new location as a body change if the docstring wasn't updated (FR57)

**Given** a file where all changed symbols have correspondingly updated docstrings
**When** `check_freshness_diff` is called
**Then** it returns an empty list (FR62)

**Given** an empty `diff_output` string
**When** `check_freshness_diff` is called
**Then** it returns an empty list immediately (FR66, NFR25)

**Given** identical `diff_output` and identical `tree`
**When** `check_freshness_diff` is called multiple times
**Then** it produces identical output every time (NFR24 — deterministic)

**FRs:** FR44, FR45, FR46, FR47, FR48, FR49, FR54, FR56, FR57, FR59, FR60, FR61 (diff), FR62 (diff), FR66 (diff), NFR23, NFR24, NFR25, NFR26, NFR27

### Story 4.3: CLI Wiring for Freshness Diff Mode

As a developer,
I want to run `docvet freshness` from the command line and see stale docstring findings in the standard output format,
So that I can integrate freshness checking into my development workflow and CI pipelines.

**Acceptance Criteria:**

**Given** a codebase with files containing symbols with stale docstrings
**When** `docvet freshness` is run
**Then** findings are printed to terminal in `file:line: rule message` format (one per line)

**Given** a codebase with no stale docstrings
**When** `docvet freshness` is run
**Then** it produces no output and exits with code 0

**Given** the existing `_run_freshness` stub in `cli.py`
**When** the freshness check is wired for diff mode
**Then** it reads each discovered file, runs `git diff` (or `git diff --cached` for `--staged`), calls `ast.parse()`, and passes `file_path`, `diff_output`, and `tree` to `check_freshness_diff`

**Given** a file that fails `ast.parse()` with `SyntaxError`
**When** `docvet freshness` processes it
**Then** the file is skipped with a warning (not passed to `check_freshness_diff`)

**Given** `docvet check` is run (all checks)
**When** freshness is in the enabled checks
**Then** freshness diff findings are included alongside findings from other checks

**Given** `docvet freshness` is run with no `--mode` flag
**When** the command executes
**Then** it defaults to diff mode (FR68)

**Given** `docvet freshness --all` is run
**When** the run completes
**Then** all Python files in the project are analyzed using `git diff HEAD` (not just staged/unstaged)

**FRs:** FR67 (diff wiring), FR68 (diff as default), NFR20, NFR30

---

**Epic 4 Summary:** 3 stories, covering all 19 FRs assigned to this epic. Story 4.1 handles git diff parsing and shared infrastructure. Story 4.2 implements the core classification-to-finding pipeline. Story 4.3 wires diff mode into the CLI.

## Epic 5: Freshness Drift Mode & CLI Integration

A developer can run `docvet freshness --mode drift` and get findings for docstrings that have drifted from their code (`stale-drift`) or aged past a configurable threshold (`stale-age`). Adds blame parsing, threshold computation, drift configuration consumption, and the `--mode drift` CLI flag.

### Story 5.1: Blame Timestamp Parser

As a developer,
I want a parser that extracts per-line modification timestamps from `git blame --line-porcelain` output,
So that drift mode can determine when each line of code was last modified.

**Acceptance Criteria:**

**Given** a `git blame --line-porcelain` output string with multiple blame entries
**When** `_parse_blame_timestamps(blame_output)` is called
**Then** it returns a `dict[int, int]` mapping 1-based line numbers to Unix timestamps extracted from `author-time` fields

**Given** a blame entry with a 40-character SHA line containing the final line number as the 3rd field
**When** `_parse_blame_timestamps` parses it
**Then** it extracts the line number via `line.split()` (positional, no regex)

**Given** a blame entry with an `author-time 1707500000` header line
**When** `_parse_blame_timestamps` parses it
**Then** it extracts `1707500000` as the Unix timestamp for the current blame block

**Given** a blame entry with header fields like `author`, `author-mail`, `committer`, `summary`, etc.
**When** `_parse_blame_timestamps` parses it
**Then** those lines are silently skipped (only SHA and `author-time` are consumed)

**Given** an empty string as `blame_output`
**When** `_parse_blame_timestamps(blame_output)` is called
**Then** it returns an empty dict (no crash, no exception — NFR25)

**Given** a blame output from an initial commit (boundary commit)
**When** `_parse_blame_timestamps` parses it
**Then** it parses normally — `author-time` is still present on boundary commits

**Given** a blame output with uncommitted changes (zero SHA `0000000...`)
**When** `_parse_blame_timestamps` parses it
**Then** it parses normally — `author-time` reflects working copy time

**Given** lines that don't match any expected format (corrupted or truncated blame data)
**When** `_parse_blame_timestamps` encounters them
**Then** they are silently skipped (NFR25 — never raises exceptions)

**FRs:** FR50, NFR25, NFR29

### Story 5.2: Drift and Age Detection Orchestrator

As a developer,
I want to detect symbols where code has drifted ahead of its docstring by a configurable threshold or where the docstring has aged past a configurable limit,
So that periodic audits surface docstrings that may need review.

**Acceptance Criteria:**

**Given** a symbol where `max(code_timestamps) - max(docstring_timestamps) > drift_threshold * 86400`
**When** `check_freshness_drift` is called
**Then** it returns a `Finding` with `rule="stale-drift"`, `category="recommended"`, and a message including both dates and the day count (e.g., `Function 'process_batch' code modified 2025-12-14, docstring last modified 2025-10-02 (73 days drift)`)

**Given** a symbol where `now - max(docstring_timestamps) > age_threshold * 86400`
**When** `check_freshness_drift` is called
**Then** it returns a `Finding` with `rule="stale-age"`, `category="recommended"`, and a message including the docstring date and day count (e.g., `Function 'validate_schema' docstring untouched since 2025-09-15 (147 days)`)

**Given** a symbol that triggers both `stale-drift` and `stale-age`
**When** `check_freshness_drift` is called
**Then** it returns two findings for that symbol — the rules are independent (FR61 drift — per rule, not per mode)

**Given** a symbol where the drift is exactly at the threshold boundary (`code_max - doc_max == threshold * 86400`)
**When** `check_freshness_drift` is called
**Then** it does not emit a `stale-drift` finding (strict greater-than comparison `>`, not `>=`)

**Given** a symbol where the docstring age is exactly at the threshold boundary
**When** `check_freshness_drift` is called
**Then** it does not emit a `stale-age` finding (strict greater-than `>`)

**Given** a symbol with no docstring (`docstring_range is None`)
**When** `check_freshness_drift` is called
**Then** it produces zero findings for that symbol (FR54 — no docstring timestamps to evaluate)

**Given** a symbol with only a docstring (no code body, e.g., a stub)
**When** `check_freshness_drift` is called
**Then** `stale-drift` cannot trigger (no code timestamps) but `stale-age` can still trigger based on docstring age alone

**Given** a symbol where code timestamps and docstring timestamps are within the drift threshold
**When** `check_freshness_drift` is called
**Then** it produces zero `stale-drift` findings for that symbol (FR62)

**Given** `config.drift_threshold = 30` and `config.age_threshold = 90` (defaults)
**When** `check_freshness_drift` is called with no explicit config overrides
**Then** it applies the default thresholds (FR65)

**Given** `config.drift_threshold = 7` (custom override)
**When** `check_freshness_drift` is called on a symbol where code is 10 days newer than docstring
**Then** it emits a `stale-drift` finding (FR63 — configurable threshold)

**Given** `config.age_threshold = 180` (custom override)
**When** `check_freshness_drift` is called on a symbol whose docstring is 100 days old
**Then** it does not emit a `stale-age` finding (under the custom threshold — FR64)

**Given** a `now` parameter passed explicitly (Unix timestamp)
**When** `check_freshness_drift` is called
**Then** it uses the provided `now` instead of `time.time()` (test determinism)

**Given** no `now` parameter
**When** `check_freshness_drift` is called
**Then** it defaults to `time.time()` for the current UTC timestamp

**Given** an empty `blame_output` string
**When** `check_freshness_drift` is called
**Then** it returns an empty list immediately (NFR25)

**Given** identical `blame_output`, identical `tree`, and identical `now` timestamp
**When** `check_freshness_drift` is called multiple times
**Then** it produces identical output every time (deterministic)

**Given** the `_compute_drift` helper
**When** called with code timestamps, docstring timestamps, and threshold
**Then** it returns `True` if drift exceeds threshold, `False` otherwise

**Given** the `_compute_age` helper
**When** called with docstring timestamps, `now`, and threshold
**Then** it returns `True` if age exceeds threshold, `False` otherwise

**FRs:** FR51, FR52, FR53, FR54 (verified), FR61 (drift), FR62 (drift), FR63, FR64, FR65, FR66 (drift), NFR21, NFR22, NFR25, NFR26, NFR27, NFR28

### Story 5.3: CLI Wiring for Drift Mode

As a developer,
I want to run `docvet freshness --mode drift` from the command line and see drift/age findings,
So that I can perform periodic docstring health audits on my codebase.

**Acceptance Criteria:**

**Given** `docvet freshness --mode drift` is run on a codebase with committed history
**When** the command executes
**Then** it runs `git blame --line-porcelain` for each discovered file and passes the output to `check_freshness_drift`

**Given** a codebase with symbols whose docstrings have drifted beyond the default threshold
**When** `docvet freshness --mode drift` is run
**Then** findings are printed in `file:line: rule message` format (one per line)

**Given** a codebase with no drift or age threshold violations
**When** `docvet freshness --mode drift` is run
**Then** it produces no output and exits with code 0

**Given** `docvet freshness --mode drift` is run
**When** the command loads config
**Then** it reads `drift-threshold` and `age-threshold` from `[tool.docvet.freshness]` in `pyproject.toml` and passes `FreshnessConfig` to `check_freshness_drift`

**Given** no `[tool.docvet.freshness]` section in `pyproject.toml`
**When** `docvet freshness --mode drift` is run
**Then** it uses default thresholds (drift: 30 days, age: 90 days — FR65)

**Given** a file with no git history (untracked, no blame data)
**When** `docvet freshness --mode drift` processes it
**Then** the file is skipped (empty blame output produces empty list)

**Given** `docvet freshness` is run with no `--mode` flag
**When** the command executes
**Then** it still defaults to diff mode (FR68 — unchanged from Epic 4)

**Given** `docvet check` is run (all checks)
**When** freshness drift mode is not explicitly selected
**Then** freshness runs in diff mode by default alongside other checks

**FRs:** FR67 (drift wiring), FR68 (`--mode drift`), NFR21, NFR29

---

**Epic 5 Summary:** 3 stories, covering all 13 FRs assigned to this epic. Story 5.1 handles git blame parsing. Story 5.2 implements drift/age threshold logic and the orchestrator. Story 5.3 wires drift mode into the CLI with the `--mode` flag.

---

## Freshness Requirements Inventory

### Freshness Functional Requirements

**Diff Mode Detection (FR43-FR49):**

- FR43: The system can parse git diff output to extract changed hunk line ranges for a given file
- FR44: The system can map changed line ranges to AST symbols using the existing line-to-symbol mapping from `ast_utils`
- FR45: The system can classify each changed line within a symbol as belonging to the signature range, docstring range, or body range
- FR46: The system can detect symbols where code lines (signature or body) changed but docstring lines did not change
- FR47: The system can assign HIGH severity (category `required`) when a symbol's signature range contains changed lines
- FR48: The system can assign MEDIUM severity (category `recommended`) when a symbol's body range contains changed lines but its signature range does not
- FR49: The system can assign LOW severity (category `recommended`) when only lines within a symbol's enclosing line range but outside its signature, docstring, and body ranges changed, and no signature or body lines changed

**Drift Mode Detection (FR50-FR54):**

- FR50: The system can parse `git blame --line-porcelain` output to extract per-line modification timestamps for a given file
- FR51: The system can group per-line timestamps by symbol using the existing line-to-symbol mapping from `ast_utils`
- FR52: The system can detect symbols where the most recent code modification exceeds the most recent docstring modification by more than a configurable drift threshold (default: 30 days)
- FR53: The system can detect symbols where the docstring has not been modified within a configurable age threshold (default: 90 days)
- FR54: The system can skip symbols with no docstring in both diff and drift modes, producing zero findings for undocumented symbols

**Freshness Edge Cases (FR55-FR58):**

- FR55: The system can produce zero freshness findings for newly created files where all lines appear as additions in the git diff
- FR56: The system can handle functions that appear in a git diff's deleted lines but no longer exist in the current AST, producing zero findings for those symbols
- FR57: The system can treat code relocated within a file as a delete-plus-add (body change at the new location, no finding at the old location), without requiring `git diff --find-renames`
- FR58: The system can skip binary files and non-Python files present in git diff output without producing findings or raising exceptions

**Freshness Finding Production (FR59-FR62):**

- FR59: The system can produce a structured finding for each stale docstring, carrying file path, line number, symbol name, rule identifier, human-readable message, and category
- FR60: The system can produce freshness findings using the shared `Finding` dataclass without modification to the dataclass fields or behavior
- FR61: The system can produce at most one finding per symbol per rule, selecting the highest applicable severity when multiple change types affect the same symbol in diff mode
- FR62: The system can produce zero findings when analyzing code where all changed symbols have correspondingly updated docstrings

**Freshness Configuration (FR63-FR65):**

- FR63: A developer can configure the drift threshold (in days) via `drift-threshold` in `[tool.docvet.freshness]`
- FR64: A developer can configure the age threshold (in days) via `age-threshold` in `[tool.docvet.freshness]`
- FR65: The system can apply default thresholds (drift: 30 days, age: 90 days) when no `[tool.docvet.freshness]` section is provided in `pyproject.toml`

**Freshness Integration (FR66-FR68):**

- FR66: The system can accept file path, git output string (diff or blame), and parsed AST as inputs and return a list of findings as output
- FR67: A developer can run the freshness check standalone via `docvet freshness` or as part of all checks via `docvet check`
- FR68: A developer can select diff or drift mode via `--mode` CLI option, with diff as the default

### Freshness Non-Functional Requirements

**Freshness Performance (NFR20-NFR22):**

- NFR20: Diff mode can process a single file's git diff and produce findings in under 100ms
- NFR21: Drift mode performance is dominated by git blame I/O; the freshness pure function itself adds no measurable overhead beyond timestamp parsing and symbol comparison
- NFR22: Memory usage for freshness scales linearly with file count — each file is processed independently with no cross-file state

**Freshness Correctness (NFR23-NFR26):**

- NFR23: Non-signature code changes never produce HIGH severity findings — body-only changes produce at most MEDIUM severity (category `recommended`)
- NFR24: Identical git diff input and identical AST produce identical severity assignment for the same symbol, regardless of execution environment or ordering
- NFR25: Malformed git output (truncated diffs, corrupted blame data, empty strings) results in zero findings for affected files, never exceptions or tracebacks
- NFR26: Finding messages name the specific symbol, the severity level, and the type of change detected (signature, body, or drift), enabling the developer to locate and fix the stale docstring without additional context

**Freshness Maintainability (NFR27-NFR28):**

- NFR27: Diff mode and drift mode can be tested independently using mocked git output strings with no filesystem or git subprocess calls
- NFR28: Adding a new severity level or drift rule requires changes to at most 3 files: the freshness module (`freshness.py`), config (`config.py`), and tests (`test_freshness.py`)

**Freshness Compatibility (NFR29-NFR30):**

- NFR29: Freshness functions handle git diff and git blame output from git 2.x without version-specific code paths
- NFR30: Freshness functions handle both `git diff` (unstaged) and `git diff --cached` (staged) output identically, as both use the same unified diff hunk format

**Freshness Integration (NFR31-NFR32):**

- NFR31: Freshness reuses the shared `Finding` dataclass without modification — no new fields, no subclassing, no changes to the frozen 6-field shape
- NFR32: Freshness has no cross-imports with enrichment or any other check module — it depends only on `checks.Finding` and `ast_utils`

### Freshness Additional Requirements

**From Architecture (6 decisions, validated):**

- No prerequisite PRs needed — all shared infrastructure already implemented (`Symbol` range fields, `map_lines_to_symbols`, `Finding`, `FreshnessConfig`)
- Mode-oriented single `freshness.py` file: constants → shared helpers → diff block → `check_freshness_diff` → drift block → `check_freshness_drift`
- `_parse_diff_hunks(diff_output) -> set[int]` — line-by-line iteration, single pass, handles new files/binary files/rename headers
- `_parse_blame_timestamps(blame_output) -> dict[int, int]` — state machine, SHA line via split, author-time via startswith
- `_classify_changed_lines(changed_lines, symbol) -> str | None` — priority-ordered early returns: docstring→None, signature→HIGH, body→MEDIUM, else→LOW
- `_build_finding` shared helper for all finding construction (unlike enrichment's inline construction)
- Config asymmetry is intentional design invariant: `check_freshness_diff` has zero config dependency; only `check_freshness_drift` takes `FreshnessConfig`
- `check_freshness_drift` accepts optional `*, now=None` parameter for test determinism
- Defensive by design, no try/except — parsers return empty on bad input, public functions return `[]` on empty input
- CLI wiring (`_run_freshness` stub replacement) is a **separate integration story** — main freshness PR adds only `checks/freshness.py` and tests
- Integration test fixtures shared in `tests/integration/conftest.py` — diff needs staged/unstaged repo fixtures, drift needs committed history with blame
- Use `.splitlines()` not `.split("\n")`, set operations for range intersections, string literals for rule IDs

**From Validation Report:**

- FR61 says "per mode" but architecture correctly implements "per rule" — drift can emit 2 findings per symbol (`stale-drift` + `stale-age`). Treat as "per rule" during implementation
