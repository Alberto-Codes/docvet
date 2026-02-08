---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
status: 'complete'
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
