---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
inputDocuments:
  - 'gh-issue-320'
  - 'gh-issue-321'
  - 'gh-issue-322'
  - 'gh-issue-323'
  - 'gh-issue-324'
  - 'gh-issue-325'
  - 'gh-issue-326'
  - 'gh-issue-327'
  - 'gh-issue-328'
  - 'gh-issue-329'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/prd.md'
workflowType: 'epics'
projectName: 'docvet'
featureScope: 'multi-style-enrichment-expansion'
---

# docvet - Epic Breakdown: Multi-Style Support & Enrichment Expansion

## Overview

This document provides the epic and story breakdown for docvet's enrichment expansion wave, sourced from 10 GitHub issues (#320-#329) validated by running docvet against boto3 (the most downloaded PyPI package). Covers multi-style docstring support (Sphinx/RST, NumPy), 8 new enrichment rules, and bidirectional verification — filling the darglint vacuum and unlocking adoption for the majority of the Python ecosystem.

## Requirements Inventory

### Functional Requirements

FR1: (#320) A `docstring-style` config key shall accept `"google"` (default) and `"sphinx"` values in `[tool.docvet]`.

FR2: (#320) When `docstring-style = "sphinx"`, section detection shall recognize RST equivalents: `:param:`/`:type:` as Args, `:returns:`/`:rtype:` as Returns, `:raises:` as Raises, `:ivar:`/`:cvar:` as Attributes, `.. seealso::` or inline `:py:*:` as See Also, `>>>`/`::`/`.. code-block::` as Examples.

FR3: (#320) When `docstring-style = "sphinx"`, rules with no RST equivalent (require\_yields, require\_receives, require\_warns, require\_other\_parameters) shall be auto-disabled.

FR4: (#320) When `docstring-style = "sphinx"`, `prefer-fenced-code-blocks` shall be auto-disabled (RST code patterns are correct).

FR5: (#320) When `docstring-style = "sphinx"`, `missing-cross-references` shall accept Sphinx roles (`:py:class:`, `:py:meth:`, etc.) anywhere in the docstring body.

FR6: (#320) When `docstring-style = "sphinx"`, the griffe check shall be auto-skipped (Google parser incompatible).

FR7: (#321) `missing-returns` rule shall detect functions with `return <expr>` statements but no `Returns:` section in their docstring.

FR8: (#321) `missing-returns` shall exclude bare `return`/`return None`, `@property` methods, `__init__`, and all dunder methods.

FR9: (#322) `missing-param-in-docstring` rule shall detect function signature parameters not documented in the `Args:` section.

FR10: (#322) `extra-param-in-docstring` rule shall detect `Args:` entries that do not correspond to a parameter in the function signature.

FR11: (#322) Param agreement checks shall always exclude `self`/`cls` and configurably exclude `*args`/`**kwargs` (default: exclude).

FR12: (#323) `missing-deprecation` rule shall detect functions with deprecation patterns in code but no deprecation notice in their docstring.

FR13: (#323) Deprecation detection shall cover `warnings.warn(..., DeprecationWarning)`, `PendingDeprecationWarning`, `FutureWarning`, and `@deprecated` decorator.

FR14: (#324) `extra-raises-in-docstring` rule shall detect exception names documented in `Raises:` that do not appear in `raise` statements in the function body.

FR15: (#324) `extra-yields-in-docstring` rule shall detect `Yields:` sections on functions with no `yield`/`yield from` statements.

FR16: (#324) `extra-returns-in-docstring` rule shall detect `Returns:` sections on functions with no `return <expr>` statements.

FR17: (#325) `trivial-docstring` rule shall detect docstrings whose summary line is a subset restatement of the symbol name with no additional information.

FR18: (#325) Trivial detection shall decompose `snake_case` and `CamelCase` into word sets, filter stop words, and compare summary words against name words.

FR19: (#326) `missing-return-type` rule shall detect functions with a `Returns:` section where the entry has no type AND the function has no `->` return annotation.

FR20: (#326) Either a typed `Returns:` entry OR a return annotation shall satisfy the check (either is sufficient).

FR21: (#327) Section parser shall recognize `Notes`, `References`, `Warnings`, `Extended Summary`, and `Methods` as valid section headers.

FR22: (#327) Section parser shall detect NumPy underline format (`---` delimited sections) alongside Google colon format.

FR23: (#328) `undocumented-init-params` rule shall detect classes with parameterized `__init__` but no `Args:`/`Parameters:` section in either the class docstring or `__init__` docstring.

FR24: (#328) `Args:` in either the class docstring or `__init__` docstring shall satisfy the check.

FR25: (#329) `overload-has-docstring` rule shall detect `@overload`-decorated functions (from `typing` or `typing_extensions`) that have docstrings.

### NonFunctional Requirements

NFR1: (#320) No RST parser dependency — Sphinx detection shall use pattern matching only, keeping docvet dependency-free.

NFR2: (all) No new runtime dependencies for any issue — stdlib + typer only.

NFR3: (all) All new `_check_*` functions shall follow the established uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`.

NFR4: (all) All new rules shall wire into the `_RULE_DISPATCH` table with zero dispatch machinery changes.

NFR5: (#320) Style auto-disable logic shall preserve user config overrides — explicit settings beat auto-disable defaults.

NFR6: (#327) Section recognition additions shall be purely additive — no breaking changes to existing section parsing behavior.

NFR7: (all) All new rules shall follow existing test patterns: one file per module, fixtures in `tests/fixtures/`, `@pytest.mark.unit` markers.

NFR8: (#320) Sphinx/RST style support must land before enrichment rules that reference style dispatch in their "Sphinx/RST interaction" sections.

NFR9: (#324) Reverse checks shall default to `recommended` category due to higher false positive risk from implicit raises/returns.

NFR10: (#326) `missing-return-type` shall default to `False` (opt-in) as a stricter check that may not suit all projects.

### Additional Requirements

- From architecture: `_RULE_DISPATCH` table-driven dispatch (from Epic 12 CC refactor) absorbs new rules with zero architecture change. Each `_check_*` function is independently testable.
- From architecture: Config gating lives in the orchestrator, not inside `_check_*` functions. Boolean toggles are checked before dispatch; list toggles are checked inside the function.
- From architecture: `_parse_sections()` is the extension point for style-aware section detection. `_SECTION_HEADERS` frozenset is the single place to add recognized sections.
- From architecture: `_extract_section_content()` is the foundation for Args entry parsing (#322) and Raises entry parsing (#324).
- From architecture: Scope-aware AST walking (stop at nested `def`/`class`) is the established pattern for all body-inspection rules.
- From architecture: `node_index` line-based lookup provides O(1) access per rule per symbol.
- From party-mode consensus (2026-03-07): #320 is the architectural foundation — style dispatch mechanism that all other issues reference. Ship first.
- From party-mode consensus (2026-03-07): Remaining enrichment issues (#322-#326, #328) can be batched into a follow-up epic after the foundation lands.
- From boto3 validation: 678 Sphinx/RST markers across 34 files, 0 Google-style markers. Sphinx/RST is the dominant style for Django, Flask, SQLAlchemy, requests, boto3/botocore, CPython stdlib, Celery.
- Sphinx section patterns are parallel to Google patterns — same internal section names, different regex. Implementation adds a `_SPHINX_SECTION_MAP` alongside existing `_SECTION_PATTERN`.
- NumPy section recognition (Phase 1) is additive only — no enforcement rules, just preventing content bleed in section-boundary parsing.
- `overload-has-docstring` (#329) may live in presence layer rather than enrichment — placement is a design decision.
- From party-mode consensus (2026-03-07 story review): Every rule story must include a docs-page AC — rule reference page in `docs/rules/` registered in `docs/rules.yml`.
- From party-mode consensus (2026-03-07 story review): Story 35.4 (trivial-docstring) must handle CamelCase acronym edge case — consecutive uppercase treated as one word until lowercase transition (e.g., `HTTPSConnection` → `{https, connection}`).
- From party-mode consensus (2026-03-07 story review): Epic 35 implementation order should prioritize unique rules (35.2, 35.4, 35.6) before pydoclint-overlap rules (35.1, 35.3, 35.5). Sprint priority decided by SM.
- From party-mode consensus (2026-03-07 story review): Story 35.3 (reverse checks, 3 rules in 1 M story) may be split into 3 S stories at sprint time if velocity requires.
- From competitor research (2026-03-07): pydoclint v0.8.3 is the primary active competitor — supports Google/Sphinx/NumPy with 21 DOC rules covering param/return/yield/raise agreement. Ruff has DOC201/202/402/403/501/502 in preview (unstable). Neither tool covers freshness, rendering, or discoverability — docvet layers 4-6 are uncontested.

### FR Coverage Map

| FR | Epic | Story | Description |
|----|------|-------|-------------|
| FR1 | 34 | 34.1 | `docstring-style` config key |
| FR2 | 34 | 34.1 | Sphinx RST section pattern detection |
| FR3 | 34 | 34.1 | Auto-disable inapplicable rules in sphinx mode |
| FR4 | 34 | 34.1 | Auto-disable prefer-fenced-code-blocks in sphinx mode |
| FR5 | 34 | 34.1 | Sphinx cross-reference roles in body |
| FR6 | 34 | 34.1 | Auto-skip griffe in sphinx mode |
| FR7 | 34 | 34.2 | missing-returns detection |
| FR8 | 34 | 34.2 | missing-returns exclusions |
| FR9 | 35 | 35.1 | missing-param-in-docstring detection |
| FR10 | 35 | 35.1 | extra-param-in-docstring detection |
| FR11 | 35 | 35.1 | Param agreement self/cls/*args/**kwargs handling |
| FR12 | 35 | 35.2 | missing-deprecation detection |
| FR13 | 35 | 35.2 | Deprecation pattern coverage |
| FR14 | 35 | 35.3 | extra-raises-in-docstring detection |
| FR15 | 35 | 35.3 | extra-yields-in-docstring detection |
| FR16 | 35 | 35.3 | extra-returns-in-docstring detection |
| FR17 | 35 | 35.4 | trivial-docstring detection |
| FR18 | 35 | 35.4 | Word decomposition and stop word filtering |
| FR19 | 35 | 35.5 | missing-return-type detection |
| FR20 | 35 | 35.5 | Type in docstring OR annotation satisfies check |
| FR21 | 34 | 34.3 | NumPy section header recognition |
| FR22 | 34 | 34.3 | NumPy underline format detection |
| FR23 | 35 | 35.6 | undocumented-init-params detection |
| FR24 | 35 | 35.6 | Class or __init__ docstring satisfies check |
| FR25 | 34 | 34.4 | overload-has-docstring detection |

## Epic List

### Epic 34: Multi-Style Support & Foundation Rules

Developers using Sphinx/RST or NumPy-style docstrings get meaningful enrichment checks without false positives, and three quick-win rules ship alongside the style infrastructure — unlocking docvet adoption for the majority of the Python ecosystem.

**FRs covered:** FR1-FR8, FR21-FR22, FR25
**Stories:** 4

- **Story 34.1:** Sphinx/RST docstring style support (FR1-FR6 + NFR1, NFR5) — L
- **Story 34.2:** `missing-returns` enrichment rule (FR7-FR8 + NFR3, NFR4) — S
- **Story 34.3:** NumPy-style section recognition Phase 1 (FR21-FR22 + NFR6) — XS
- **Story 34.4:** `overload-has-docstring` check (FR25 + NFR3) — XS

### Epic 35: Enrichment Depth — Correctness & Completeness Rules

Developers get bidirectional docstring verification — both "code has behavior, docstring should document it" AND "docstring claims behavior, code should exhibit it" — plus parameter agreement, deprecation notices, trivial docstring detection, return type completeness, and init param documentation. Fills the darglint vacuum completely.

**FRs covered:** FR9-FR20, FR23-FR24
**Stories:** 6

- **Story 35.1:** Docstring-parameter agreement checks (FR9-FR11 + NFR3, NFR4) — M
- **Story 35.2:** `missing-deprecation` enrichment rule (FR12-FR13 + NFR3, NFR4) — S
- **Story 35.3:** Reverse enrichment checks (FR14-FR16 + NFR3, NFR4, NFR9) — M
- **Story 35.4:** `trivial-docstring` enrichment rule (FR17-FR18 + NFR3, NFR4) — S
- **Story 35.5:** `missing-return-type` enrichment rule (FR19-FR20 + NFR3, NFR4, NFR10) — S
- **Story 35.6:** `undocumented-init-params` enrichment rule (FR23-FR24 + NFR3, NFR4) — S

---

## Epic 34: Multi-Style Support & Foundation Rules

### Story 34.1: Sphinx/RST docstring style support

As a developer maintaining a Sphinx/RST-style codebase,
I want docvet to recognize RST section patterns and auto-disable incompatible rules,
So that I get meaningful enrichment findings without false positives.

**Acceptance Criteria:**

**Given** a pyproject.toml with `docstring-style = "sphinx"` under `[tool.docvet]`
**When** docvet loads the configuration
**Then** the `docstring_style` field is set to `"sphinx"` and all style-aware behavior switches to RST patterns

**Given** `docstring-style = "sphinx"` is set
**When** enrichment parses a docstring containing `:param name:`, `:type name:`, `:returns:`, `:rtype:`, `:raises ExcType:`, `:ivar name:`, `:cvar name:`, `.. seealso::`, or `>>>` / `::` / `.. code-block::`
**Then** each RST pattern is mapped to its Google-equivalent internal section name (Args, Returns, Raises, Attributes, See Also, Examples)

**Given** `docstring-style = "sphinx"` is set
**When** enrichment evaluates rules that have no RST equivalent (`require-yields`, `require-receives`, `require-warns`, `require-other-parameters`)
**Then** those rules are auto-disabled and produce no findings

**Given** `docstring-style = "sphinx"` is set
**When** enrichment evaluates `prefer-fenced-code-blocks`
**Then** the rule is auto-disabled (RST `::` and `>>>` patterns are correct in Sphinx mode)

**Given** `docstring-style = "sphinx"` is set
**When** enrichment evaluates `missing-cross-references`
**Then** Sphinx roles (`:py:class:`, `:py:meth:`, `:py:func:`, etc.) anywhere in the docstring body satisfy the cross-reference check

**Given** `docstring-style = "sphinx"` is set
**When** the CLI runs `docvet check` or `docvet griffe`
**Then** the griffe compatibility check is auto-skipped (Google parser is incompatible with RST)

**Given** `docstring-style = "sphinx"` is set AND the user has explicitly set `require-yields = true` in their config
**When** enrichment evaluates the yields rule
**Then** the explicit user setting overrides auto-disable and the rule runs (NFR5: explicit settings beat auto-disable defaults)

**Given** `docstring-style` is omitted from config
**When** docvet loads the configuration
**Then** the default value is `"google"` and all existing behavior is unchanged

**Given** `docstring-style` is set to an invalid value (e.g., `"numpy"`, `"plain"`)
**When** docvet loads the configuration
**Then** a clear validation error is raised listing valid options

**Given** a Sphinx-style docstring with `:param name:` entries
**When** `_parse_sections()` runs in sphinx mode
**Then** section detection uses pattern matching only — no RST parser dependency (NFR1)

**Given** a Google-style docstring with `Args:`, `Returns:`, `Raises:` headers
**When** `_parse_sections()` runs in google mode (default)
**Then** behavior is identical to the current implementation — zero regression

**Given** `docstring-style = "sphinx"` is set
**When** running `docvet check --all` against boto3
**Then** false positives from RST-style docstrings are eliminated (the 678 RST markers across 34 files produce section matches, not missing-section findings)

**Given** `docstring-style` is a new top-level config key under `[tool.docvet]`
**When** the story is marked done
**Then** the configuration reference page in `docs/` documents the key with valid values (`"google"`, `"sphinx"`), default (`"google"`), and behavior summary including auto-disable rules

### Story 34.2: `missing-returns` enrichment rule

As a developer,
I want docvet to flag functions that return values but have no Returns section,
So that callers know what the function returns by reading its docstring.

**Acceptance Criteria:**

**Given** a function with `return <expr>` statements and a docstring with no `Returns:` section
**When** enrichment runs
**Then** a finding is emitted: `missing-returns` with message identifying the function name

**Given** a function with only bare `return` or `return None` statements
**When** enrichment runs
**Then** no `missing-returns` finding is produced (control flow returns are not meaningful)

**Given** a function with a mix of `return value` and bare `return` statements
**When** enrichment runs
**Then** a `missing-returns` finding IS produced (at least one meaningful return exists)

**Given** a `@property` method, `__init__`, or any dunder method (`__repr__`, `__len__`, `__bool__`, etc.)
**When** enrichment runs
**Then** no `missing-returns` finding is produced (skip set applies)

**Given** a function with `return <expr>` inside a nested function or class
**When** enrichment runs on the outer function
**Then** no `missing-returns` finding is produced for the outer function (scope-aware AST walk stops at nested `def`/`class`)

**Given** a function with a `Returns:` section already present
**When** enrichment runs
**Then** no `missing-returns` finding is produced

**Given** `require-returns = false` in `[tool.docvet.enrichment]`
**When** enrichment runs
**Then** the `missing-returns` rule is skipped entirely

**Given** `require-returns = true` (the default)
**When** the rule is dispatched
**Then** `_check_missing_returns` follows the uniform signature `(symbol, sections, node_index, config, file_path) -> Finding | None` and is wired into `_RULE_DISPATCH` with zero dispatch changes

**Given** a function with no docstring
**When** enrichment runs
**Then** no `missing-returns` finding is produced (enrichment only runs on functions that have docstrings)

**Given** the `missing-returns` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern (macros scaffold in `docs/main.py`)

### Story 34.3: NumPy-style section recognition Phase 1

As a developer maintaining a NumPy-style codebase,
I want docvet's section parser to recognize NumPy sections and underline format,
So that section-boundary parsing doesn't bleed content across sections.

**Acceptance Criteria:**

**Given** a docstring with `Notes`, `References`, `Warnings`, `Extended Summary`, or `Methods` as section headers
**When** `_parse_sections()` runs
**Then** these headers are recognized as valid section boundaries (added to `_SECTION_HEADERS` frozenset)

**Given** a docstring with NumPy underline format (e.g., `Parameters\n----------`)
**When** `_parse_sections()` runs
**Then** the underline format is detected alongside Google colon format as a section delimiter

**Given** a docstring with a `Notes` section followed by a `Returns` section
**When** `_extract_section_content()` extracts `Returns` content
**Then** `Notes` content does not bleed into the `Returns` section (correct boundary detection)

**Given** existing Google-style docstrings with `Args:`, `Returns:`, `Raises:` headers
**When** `_parse_sections()` runs after the NumPy additions
**Then** all existing section detection behavior is identical — zero regression (NFR6)

**Given** a NumPy-style `Notes` section exists in a docstring
**When** enrichment rules run
**Then** no enforcement rules fire for `Notes` — recognition is additive only, no new required-section rules

**Given** the `_SECTION_HEADERS` frozenset after this story
**When** inspecting the codebase
**Then** exactly 5 new entries are added: `Notes`, `References`, `Warnings`, `Extended Summary`, `Methods`

### Story 34.4: `overload-has-docstring` check

As a developer,
I want docvet to flag `@overload`-decorated functions that have docstrings,
So that documentation lives only on the implementation function where `help()` and doc generators expect it.

**Acceptance Criteria:**

**Given** a function decorated with `@overload` (from `typing` or `typing_extensions`) that has a docstring
**When** the check runs
**Then** a finding is emitted: `overload-has-docstring` with message identifying the function name

**Given** a function decorated with `@typing.overload` (attribute access form) that has a docstring
**When** the check runs
**Then** a finding is emitted (both `@overload` name form and `@typing.overload` attribute form are detected)

**Given** an `@overload`-decorated function with no docstring
**When** the check runs
**Then** no finding is produced

**Given** the implementation function (no `@overload` decorator) with a docstring
**When** the check runs
**Then** no finding is produced (only overloads are flagged)

**Given** `check-overload-docstrings = false` in config
**When** the check runs
**Then** the rule is skipped entirely

**Given** the `overload-has-docstring` rule
**When** inspecting its wiring
**Then** the rule lives in the presence layer (not enrichment) since it's about whether a docstring should exist, following the `_check_*` uniform signature (NFR3)

**Given** the `overload-has-docstring` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern

---

## Epic 35: Enrichment Depth — Correctness & Completeness Rules

> **Implementation order note (party-mode consensus 2026-03-07):** Stories are numbered for reference, not execution order. Recommended sprint sequencing prioritizes unique rules before pydoclint-overlap rules: 35.2 (missing-deprecation) → 35.4 (trivial-docstring) → 35.6 (undocumented-init-params) → 35.1 (param agreement) → 35.5 (missing-return-type) → 35.3 (reverse checks). SM decides final sprint priority.
>
> **Splitting note:** Story 35.3 packs 3 rules into one M story. If velocity wobbles, split into 3 S stories at sprint time — the ACs already separate the three rules cleanly.

### Story 35.1: Docstring-parameter agreement checks

As a developer,
I want docvet to flag signature parameters missing from `Args:` and `Args:` entries not in the signature,
So that my docstrings accurately reflect the function's actual interface.

**Acceptance Criteria:**

**Given** a function with an `Args:` section where a signature parameter is not documented
**When** enrichment runs
**Then** a `missing-param-in-docstring` finding is emitted naming the undocumented parameter

**Given** a function with an `Args:` section that documents a name not in the signature
**When** enrichment runs
**Then** an `extra-param-in-docstring` finding is emitted naming the stale/incorrect entry

**Given** a method with `self` or `cls` as the first parameter
**When** enrichment runs
**Then** `self`/`cls` are always excluded from agreement checks (never expected in `Args:`)

**Given** a function with `*args` and `**kwargs` parameters and default config
**When** enrichment runs
**Then** `*args`/`**kwargs` are excluded from agreement checks (default: exclude)

**Given** `exclude-args-kwargs = false` in `[tool.docvet.enrichment]`
**When** enrichment runs on a function with `*args`/`**kwargs` not in `Args:`
**Then** findings are emitted for the undocumented `*args`/`**kwargs`

**Given** a function with a docstring but no `Args:` section
**When** enrichment runs
**Then** no param agreement findings are produced (missing section is a different concern)

**Given** a function with parameters that all appear in `Args:` and vice versa
**When** enrichment runs
**Then** zero param agreement findings are produced

**Given** `_parse_args_entries` helper
**When** it parses an `Args:` section
**Then** it extracts parameter names using `_extract_section_content()` and returns a `set[str]` of documented names

**Given** `require-param-agreement = false` in config
**When** enrichment runs
**Then** both `missing-param-in-docstring` and `extra-param-in-docstring` rules are skipped

**Given** both param agreement rules are implemented and tested
**When** the story is marked done
**Then** rule reference pages exist in `docs/rules/` for both `missing-param-in-docstring` and `extra-param-in-docstring`, registered in `docs/rules.yml`

### Story 35.2: `missing-deprecation` enrichment rule

As a developer,
I want docvet to flag functions with deprecation patterns in code but no deprecation notice in their docstring,
So that users reading documentation know to migrate away from deprecated APIs.

**Acceptance Criteria:**

**Given** a function body containing `warnings.warn(..., DeprecationWarning)`
**When** enrichment runs and the docstring does not contain the word "deprecated" (case-insensitive)
**Then** a `missing-deprecation` finding is emitted

**Given** a function body containing `warnings.warn(..., PendingDeprecationWarning)` or `warnings.warn(..., FutureWarning)`
**When** enrichment runs and the docstring has no deprecation notice
**Then** a `missing-deprecation` finding is emitted (all three warning categories are covered)

**Given** a function decorated with `@deprecated` (from `typing_extensions` or `warnings`)
**When** enrichment runs and the docstring has no deprecation notice
**Then** a `missing-deprecation` finding is emitted

**Given** a function with a deprecation pattern in code AND the word "deprecated" anywhere in the docstring
**When** enrichment runs
**Then** no finding is produced (intentionally loose matching avoids false positives)

**Given** a function with no deprecation patterns in code
**When** enrichment runs
**Then** no `missing-deprecation` finding is produced

**Given** a deprecation `warnings.warn(...)` inside a nested function
**When** enrichment runs on the outer function
**Then** no finding is produced for the outer function (scope-aware AST walk)

**Given** `require-deprecation-notice = false` in config
**When** enrichment runs
**Then** the rule is skipped entirely

**Given** the `missing-deprecation` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern

### Story 35.3: Reverse enrichment checks

As a developer,
I want docvet to flag docstrings that claim behavior the code doesn't exhibit,
So that my docstrings don't mislead callers about raises, yields, or returns.

**Acceptance Criteria:**

**Given** a function with a `Raises:` section documenting `ValueError` but no `raise ValueError` in the function body
**When** enrichment runs
**Then** an `extra-raises-in-docstring` finding is emitted naming the undocumented exception

**Given** a function with a `Raises:` section documenting exceptions that ALL appear in `raise` statements
**When** enrichment runs
**Then** no `extra-raises-in-docstring` findings are produced

**Given** a function with a `Yields:` section but no `yield` or `yield from` statements in the body
**When** enrichment runs
**Then** an `extra-yields-in-docstring` finding is emitted

**Given** a function with a `Returns:` section but no `return <expr>` statements in the body (only bare `return` or `return None`)
**When** enrichment runs
**Then** an `extra-returns-in-docstring` finding is emitted

**Given** a function with `raise` inside a nested function or class
**When** enrichment runs on the outer function
**Then** the nested raise is not counted (scope-aware walk stops at nested `def`/`class`)

**Given** a `Raises:` section entry with an exception raised via re-raise (`raise` with no argument inside `except`)
**When** enrichment runs
**Then** the re-raised exception type is not matched (bare `raise` has no explicit type)

**Given** all three reverse rules
**When** checking their default category
**Then** findings are categorized as `recommended` (not `required`) due to higher false positive risk from implicit raises/returns (NFR9)

**Given** `require-extra-raises-check = false`, `require-extra-yields-check = false`, or `require-extra-returns-check = false` in config
**When** enrichment runs
**Then** the corresponding rule is skipped

**Given** the `_parse_raises_entries` helper
**When** it parses a `Raises:` section
**Then** it extracts exception class names from the section using `_extract_section_content()` and returns a `set[str]`

**Given** all three reverse rules are implemented and tested
**When** the story is marked done
**Then** rule reference pages exist in `docs/rules/` for `extra-raises-in-docstring`, `extra-yields-in-docstring`, and `extra-returns-in-docstring`, registered in `docs/rules.yml`

### Story 35.4: `trivial-docstring` enrichment rule

As a developer,
I want docvet to flag docstrings that trivially restate the symbol name,
So that docstrings add real information value beyond what the name already communicates.

**Acceptance Criteria:**

**Given** a function `get_user` with docstring `"""Get user."""`
**When** enrichment runs
**Then** a `trivial-docstring` finding is emitted (summary word set `{get, user}` == name word set `{get, user}`)

**Given** a class `UserManager` with docstring `"""User manager."""`
**When** enrichment runs
**Then** a `trivial-docstring` finding is emitted (`CamelCase` decomposed to `{user, manager}`)

**Given** a function `process_data` with docstring `"""Process the data."""`
**When** enrichment runs
**Then** a `trivial-docstring` finding is emitted (stop words like "the" are filtered, leaving `{process, data}` ⊆ `{process, data}`)

**Given** a function `get_user` with docstring `"""Fetch a user from the database by their ID."""`
**When** enrichment runs
**Then** no `trivial-docstring` finding is produced (summary adds "database", "ID", "fetch" — not a subset)

**Given** a `_STOP_WORDS` frozenset
**When** word filtering runs
**Then** common English articles and prepositions (`a`, `an`, `the`, `of`, `for`, `to`, `in`, `is`, `it`, `and`, `or`, `this`, `that`, `with`, `from`, `by`, `on`) are excluded from comparison

**Given** both `snake_case` and `CamelCase` symbol names
**When** word decomposition runs
**Then** `snake_case` splits on `_` and `CamelCase` splits on uppercase boundaries, both lowercased

**Given** a CamelCase name with consecutive uppercase letters like `HTTPSConnection` or `HTMLParser`
**When** word decomposition runs
**Then** consecutive uppercase letters are treated as one word until a lowercase transition, producing `{https, connection}` and `{html, parser}` respectively (not letter-by-letter splitting)

**Given** `check-trivial-docstrings = false` in config
**When** enrichment runs
**Then** the rule is skipped entirely

**Given** the `trivial-docstring` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern

### Story 35.5: `missing-return-type` enrichment rule

As a developer,
I want docvet to flag functions with a `Returns:` section that has no type when the function also lacks a return annotation,
So that callers can determine the return type from either the docstring or the signature.

**Acceptance Criteria:**

**Given** a function with a `Returns:` section where the first entry has no type AND the function has no `->` return annotation
**When** enrichment runs
**Then** a `missing-return-type` finding is emitted

**Given** a function with a `Returns:` section where the first entry has a type (e.g., `dict: The result.`)
**When** enrichment runs
**Then** no finding is produced (typed Returns entry satisfies the check)

**Given** a function with a `Returns:` section with no type BUT the function has a `-> dict` return annotation
**When** enrichment runs
**Then** no finding is produced (return annotation satisfies the check — FR20)

**Given** an `__init__`, `__del__`, or property setter method
**When** enrichment runs
**Then** no `missing-return-type` finding is produced (excluded by skip set)

**Given** `require-return-type = true` in `[tool.docvet.enrichment]`
**When** enrichment runs
**Then** the rule is active

**Given** `require-return-type` is not set in config (default)
**When** enrichment runs
**Then** the rule is skipped (defaults to `false` / opt-in per NFR10)

**Given** a `_RETURNS_TYPE_PATTERN` regex
**When** it examines the first non-empty line under `Returns:`
**Then** it matches `word:` patterns (type followed by colon) to determine if a type is present

**Given** the `missing-return-type` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern

### Story 35.6: `undocumented-init-params` enrichment rule

As a developer,
I want docvet to flag classes whose `__init__` takes parameters but neither the class docstring nor `__init__` has an Args section,
So that constructor parameters are documented somewhere for users.

**Acceptance Criteria:**

**Given** a class with `__init__(self, name, timeout)` and neither the class docstring nor `__init__` docstring has an `Args:` or `Parameters:` section
**When** enrichment runs
**Then** an `undocumented-init-params` finding is emitted naming the class and listing the undocumented parameters

**Given** a class with `__init__(self, name)` and the class docstring has an `Args:` section
**When** enrichment runs
**Then** no finding is produced (class docstring satisfies the check — FR24)

**Given** a class with `__init__(self, name)` and `__init__` itself has a docstring with an `Args:` section
**When** enrichment runs
**Then** no finding is produced (`__init__` docstring satisfies the check — FR24)

**Given** a class with `__init__(self)` (no parameters beyond self)
**When** enrichment runs
**Then** no finding is produced (no parameters to document)

**Given** a class with no `__init__` method defined
**When** enrichment runs
**Then** no finding is produced (inherits default `__init__`)

**Given** a class with `__init__(self, *args, **kwargs)` only (pass-through)
**When** enrichment runs and default config excludes `*args`/`**kwargs`
**Then** no finding is produced (all params excluded)

**Given** `require-init-params = false` in config
**When** enrichment runs
**Then** the rule is skipped entirely

**Given** the `undocumented-init-params` rule is implemented and tested
**When** the story is marked done
**Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern
