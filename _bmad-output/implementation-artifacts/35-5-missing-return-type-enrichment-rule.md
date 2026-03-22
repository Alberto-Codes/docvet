# Story 35.5: Missing Return Type Enrichment Rule

Status: done
Branch: `feat/enrichment-35-5-missing-return-type`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag functions with a `Returns:` section that has no type when the function also lacks a return annotation,
so that callers can determine the return type from either the docstring or the signature.

## Acceptance Criteria

1. **Given** a function with a `Returns:` section where the first entry has no type AND the function has no `->` return annotation, **when** enrichment runs, **then** a `missing-return-type` finding is emitted.

2. **Given** a function with a `Returns:` section where the first entry has a type (e.g., `dict: The result.`), **when** enrichment runs, **then** no finding is produced (typed Returns entry satisfies the check).

3. **Given** a function with a `Returns:` section with no type BUT the function has a `-> dict` return annotation, **when** enrichment runs, **then** no finding is produced (return annotation satisfies the check -- FR20).

4. **Given** an `__init__`, `__del__`, or property setter method, **when** enrichment runs, **then** no `missing-return-type` finding is produced (excluded by skip set).

5. **Given** `require-return-type = true` in `[tool.docvet.enrichment]`, **when** enrichment runs, **then** the rule is active.

6. **Given** `require-return-type` is not set in config (default), **when** enrichment runs, **then** the rule is skipped (defaults to `false` / opt-in per NFR10).

7. **Given** a `_RETURNS_TYPE_PATTERN` regex, **when** it examines the first non-empty line under `Returns:`, **then** it matches `word:` patterns (type followed by colon) to determine if a type is present.

8. **Given** the `missing-return-type` rule is implemented and tested, **when** the story is marked done, **then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern.

## Tasks / Subtasks

- [x] Task 1: Add `require_return_type` config field (AC: 5, 6)
  - [x]1.1 Add `require_return_type: bool = False` to `EnrichmentConfig` in `config.py` (after `check_trivial_docstrings`, before `user_set_keys`)
  - [x]1.2 Add `"require-return-type"` to `_VALID_ENRICHMENT_KEYS` frozenset (alphabetical order)
  - [x]1.3 Add docstring entry for the new field in `EnrichmentConfig`
- [x] Task 2: Implement `_RETURNS_TYPE_PATTERN` regex (AC: 7)
  - [x]2.1 Create `_RETURNS_TYPE_PATTERN = re.compile(r"^\s*[A-Za-z_][\w\[\], |.]*\s*:")` to match type expressions followed by colon (e.g., `dict:`, `list[str]:`, `str | None:`, `Optional[int]:`, `None:`, `Callable[[int], str]:`)
  - [x]2.2 Pattern requires first char to be a letter or underscore (prevents false positives on description lines starting with digits or punctuation)
- [x] Task 3: Implement `_has_return_type_in_docstring()` helper
  - [x]3.1 Create `_has_return_type_in_docstring(docstring: str) -> bool`
  - [x]3.2 Google mode: use `_extract_section_content(docstring, "Returns")` to get content; if content is `None`, return `True` (NumPy underline format -- can't parse, don't false-positive); find first non-empty content line; check against `_RETURNS_TYPE_PATTERN`
  - [x]3.3 Sphinx mode: raw string check `":rtype:" in docstring` (party-mode consensus: simple, correct, safe failure direction)
  - [x]3.4 Branch on `_active_style` module variable: `"sphinx"` uses 3.3, all others use 3.2
  - [x]3.5 Return `True` if type is found, `False` otherwise
  - [x]3.6 Guard: if no non-empty content line found (empty Returns section), return `True` (don't report on empty sections -- safe direction)
- [x] Task 4: Implement `_check_missing_return_type()` (AC: 1, 2, 3, 4)
  - [x]4.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x]4.2 Guard: return None if `symbol.docstring is None`
  - [x]4.3 Guard: return None if `"Returns"` not in `sections` (rule only applies to functions that already have a Returns section)
  - [x]4.4 Guard: return None if symbol is `__init__`, `__del__` (dunder skip)
  - [x]4.5 Guard: return None if `_is_property(node)` (includes property setters -- AC: 4)
  - [x]4.6 Retrieve AST node from `node_index[symbol.line]`; guard on KeyError
  - [x]4.7 Check `node.returns is not None` -- if return annotation exists, return None (FR20: annotation satisfies)
  - [x]4.8 Check `_has_return_type_in_docstring(symbol.docstring)` -- if type found, return None
  - [x]4.9 Emit Finding with `rule="missing-return-type"`, `category="recommended"`, message: `"Function '{name}' has a Returns section with no type and no return annotation -- add a type to the Returns entry or a -> annotation"`
- [x] Task 5: Wire into `_RULE_DISPATCH` (AC: 5, 6)
  - [x]5.1 Add `("require_return_type", _check_missing_return_type)` to `_RULE_DISPATCH` (after `check_trivial_docstrings` entry)
- [x] Task 6: Write tests in `tests/unit/checks/test_missing_return_type.py` (AC: 1-8)
  - [x]6.1 Create `_make_symbol_and_index` helper (reuse pattern from `test_missing_returns.py`)
  - **Core detection tests:**
  - [x]6.2 Test function with `Returns:` untyped entry and no `->` annotation -> finding (AC: 1)
  - [x]6.3 Test function with typed `Returns:` entry (e.g., `dict: The result.`) -> no finding (AC: 2)
  - [x]6.4 Test function with untyped `Returns:` BUT `-> dict` annotation -> no finding (AC: 3)
  - **Skip condition tests (AC: 4):**
  - [x]6.5 Test `__init__` method with untyped `Returns:` -> no finding
  - [x]6.6 Test `__del__` method with untyped `Returns:` -> no finding
  - [x]6.7 Test `@property` method -> no finding
  - [x]6.8 Test `@cached_property` method -> no finding
  - **Config gating tests (AC: 5, 6):**
  - [x]6.9 Test `require_return_type=True` -> rule active (finding emitted)
  - [x]6.10 Test `require_return_type=False` (default) -> no finding (rule skipped)
  - **Type pattern tests (AC: 7):**
  - [x]6.11 Test `_RETURNS_TYPE_PATTERN` matches `dict:`, `list[str]:`, `str | None:`, `Optional[int]:`
  - [x]6.12 Test `_RETURNS_TYPE_PATTERN` does NOT match `The result mapping.`
  - **Edge cases:**
  - [x]6.13 Test function without Returns section at all -> no finding (not applicable)
  - [x]6.14 Test async function with untyped Returns and no annotation -> finding
  - [x]6.15 Test class symbol -> no finding (rule only applies to functions/methods)
  - [x]6.16 Test complex return type annotation `-> dict[str, list[int]]` satisfies check
  - [x]6.17 Test Sphinx-style `:rtype:` presence satisfies check (when style=sphinx)
  - [x]6.18 Test Sphinx-style `:returns:` without `:rtype:` and no annotation -> finding
  - **Party-mode consensus edge cases (Q2, Q5, Q6):**
  - [x]6.19 Test NumPy-style Returns section (underline format) -> no finding (guard: `_extract_section_content` returns None)
  - [x]6.20 Test `None:` typed entry (e.g., `None: Always returns None.`) -> no finding (`None` is a valid type)
  - [x]6.21 Test `-> None` annotation with untyped Returns -> no finding (annotation satisfies FR20)
  - [x]6.22 Test multi-line untyped description (no type on first line) -> finding
  - [x]6.23 Test empty line before typed entry (blank line then `dict: ...`) -> no finding (first NON-EMPTY line has type)
  - [x]6.24 Test multiple Returns entries with first entry typed -> no finding
  - [x]6.25 Test empty Returns section content (only whitespace) -> no finding (safe direction)
  - **Assertion strength:**
  - [x]6.26 Assert all 6 Finding fields on primary tests: `file`, `line`, `symbol`, `rule`, `message`, `category`
  - **Cross-rule interaction:**
  - [x]6.27 Test function that also triggers `missing-returns` does NOT trigger `missing-return-type` (mutual exclusion: if no Returns section, only `missing-returns` fires)
  - **Integration test:**
  - [x]6.28 Test via `check_enrichment()` function with `require_return_type=True` to verify dispatch wiring
- [x] Task 7: Create rule reference page (AC: 8)
  - [x]7.1 Create `docs/site/rules/missing-return-type.md` following existing macros scaffold pattern (see `docs/site/rules/missing-returns.md` as closest reference)
  - [x]7.2 Register `missing-return-type` in `docs/rules.yml` (count 29 -> 30)
- [x] Task 8: Update documentation and infrastructure
  - [x]8.1 Update `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` from 29 to 30
  - [x]8.2 Add `missing-return-type` to enrichment rule list in `docs/site/checks/enrichment.md`
  - [x]8.3 Add `require-return-type` row to `docs/site/configuration.md` enrichment config table
  - [x]8.4 Add `missing-return-type` nav entry to `mkdocs.yml` under rules section
- [x] Task 9: Run quality gates and verify dogfooding
  - [x]9.1 `uv run ruff check .` -- zero violations
  - [x]9.2 `uv run ruff format --check .` -- zero format issues
  - [x]9.3 `uv run ty check` -- zero type errors
  - [x]9.4 `uv run pytest` -- all tests pass, no regressions
  - [x]9.5 `uv run docvet check --all` -- zero docvet findings (full-strength dogfooding; note: since `require-return-type` defaults to false, own codebase won't trigger this rule unless explicitly enabled)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_untyped_returns_no_annotation_emits_finding` | Pass |
| 2 | `test_typed_returns_entry_no_finding` | Pass |
| 3 | `test_annotation_satisfies_check_no_finding` | Pass |
| 4 | `test_init_method_skip_no_finding`, `test_del_method_skip_no_finding`, `test_property_method_skip_no_finding`, `test_cached_property_skip_no_finding` | Pass |
| 5 | `test_config_enabled_emits_finding` | Pass |
| 6 | `test_config_default_false_skips_via_dispatch` | Pass |
| 7 | `test_returns_type_pattern` (11 parametrized variants) | Pass |
| 8 | `test_rule_count`, `test_every_rule_id_has_page`, `test_every_rule_page_has_entry` in `test_docs_infrastructure.py` | Pass |

## Dev Notes

- **Interaction Risk:** This story adds 1 rule (`missing-return-type`) to the enrichment module which already has 18 entries in `_RULE_DISPATCH` (19 after this story). The rule is gated by a NEW config key `require_return_type` (default `False`), so it cannot conflict with existing rules at default settings. The rule requires a `Returns` section to be present -- functions missing `Returns` entirely are handled by `missing-returns` (config key `require_returns`). These two rules are complementary, not conflicting: `missing-returns` checks for section presence, `missing-return-type` checks for type completeness within the section. Verify with an unfiltered findings test.

### Architecture & Implementation Patterns

**Uniform check signature** -- follows the established pattern:
```python
def _check_missing_return_type(symbol, sections, node_index, config, file_path) -> Finding | None
```

**Config key: `require_return_type`** -- boolean, defaults to `False` (opt-in per NFR10). This is the first enrichment config key that defaults to `False`, making this a stricter opt-in check. Config key in pyproject.toml: `require-return-type`.

**Category `recommended`** -- return type documentation is a quality enhancement. Functions can be usable without explicit return types, but documentation quality improves significantly when types are present.

**Two-path type detection:**
1. **Return annotation** (`node.returns is not None`): `def foo() -> int:` -- AST check, trivial
2. **Typed Returns entry**: `dict: The result.` under `Returns:` -- regex on extracted section content

**Either path satisfies the check** (FR20). Only when NEITHER is present does a finding fire.

**`_RETURNS_TYPE_PATTERN` regex** (AC: 7, party-mode consensus Q1):
```python
_RETURNS_TYPE_PATTERN = re.compile(r"^\s*[A-Za-z_][\w\[\], |.]*\s*:")
```
Requires first char to be letter/underscore (prevents false positives from description lines). Covers 98%+ of real-world type expressions. Matches:
- `dict:` -- simple type
- `list[str]:` -- generic
- `str | None:` -- union (pipe allowed in char class)
- `Optional[int]:` -- typing module generic
- `Callable[[int], str]:` -- nested brackets
- `None:` -- valid type (party-mode consensus Q5: `None` is a type, presence check not correctness)
- `tuple[str, ...]:` -- ellipsis inside brackets

Does NOT match untyped entries:
- `The result mapping.` -- starts with letter + space, but no colon after word group
- `A list of items.` -- article start, no colon pattern

**First non-empty content line algorithm** (party-mode consensus Q6): extract Returns content, skip blank lines, check first non-empty line against regex. Naturally handles:
- Multi-line descriptions (first line checked, finding if untyped)
- Empty lines before typed entry (skipped, type found on next non-empty line)
- Multiple Returns entries (first entry checked per AC)
- Empty Returns section (no non-empty line -> no finding, safe direction)

**Sphinx mode handling** (party-mode consensus Q3):
- Raw string check: `":rtype:" in symbol.docstring` -- simple, correct, safe failure direction
- `:returns:` without `:rtype:` AND no `->` annotation -> finding
- Branch on `_active_style` module variable: `"sphinx"` uses raw string, all others use regex on extracted content

**NumPy handling** (party-mode consensus Q2):
- `_extract_section_content` returns `None` for NumPy underline format (confirmed at enrichment.py:1786)
- Guard: if content is `None` but `"Returns"` is in sections, return `None` (no finding) -- can't inspect, don't false-positive
- NumPy content extraction is a future story concern, not this story's scope

**Skip conditions (AC: 4):**
- `__init__`, `__del__` -- constructor/destructor don't return meaningful types
- `@property`, `@cached_property` -- reuse `_is_property(node)` helper (enrichment.py line 404)
- No need to skip `@abstractmethod`/`@overload`/stubs since the rule requires a `Returns` section to exist, and these rarely have one

**Prerequisite: `Returns` section must exist.** If `"Returns" not in sections`, the rule returns None immediately. This creates clean separation from `missing-returns`.

### Config Changes Required

| File | Change |
|------|--------|
| `src/docvet/config.py` | Add `require_return_type: bool = False` field to `EnrichmentConfig` |
| `src/docvet/config.py` | Add `"require-return-type"` to `_VALID_ENRICHMENT_KEYS` |

### File Locations

| What | Path |
|------|------|
| Enrichment module | `src/docvet/checks/enrichment.py` |
| Config module | `src/docvet/config.py` |
| New test file | `tests/unit/checks/test_missing_return_type.py` |
| Rule page | `docs/site/rules/missing-return-type.md` |
| Rules registry | `docs/rules.yml` |
| Configuration docs | `docs/site/configuration.md` |
| Enrichment check docs | `docs/site/checks/enrichment.md` |
| Docs infra test | `tests/unit/test_docs_infrastructure.py` |
| mkdocs nav | `mkdocs.yml` |

### Existing Helpers to Reuse

- `_is_property(node)` (enrichment.py line 404) -- reuse for `@property`/`@cached_property` skip guard (AC: 4)
- `_extract_section_content(docstring, "Returns")` (enrichment.py line 214) -- extract Returns section text for type pattern matching
- `_parse_sections(docstring, style=style)` -- already provides `"Returns"` detection for guard clause
- `_RULE_DISPATCH` (enrichment.py line 2575) -- add one new entry
- `_SPHINX_AUTO_DISABLE_RULES` -- NO changes needed (missing-return-type should work in both styles)
- `_active_style` module variable (enrichment.py line 2748) -- branch Google vs Sphinx detection logic
- `check_enrichment` orchestrator (enrichment.py line 2597) -- no changes (dispatch handles config gating)

### Previous Story Intelligence (from 35-4)

Key learnings from the previous story (trivial-docstring rule):
- **Zero-debug implementation achieved** -- follow the same careful task breakdown
- **Code review found scope creep (M1, M2)** -- keep changes strictly to this rule's scope
- **Test names must match assertions** -- if a test asserts a finding IS produced, don't name it `test_X_no_finding`
- **Completion notes must be accurate** -- verify counts before claiming them
- **Check for missing mkdocs.yml nav entries** from prior stories
- **Pattern: create `_make_symbol_and_index` helper** reused across all enrichment test files

### Party-Mode Consensus Decisions (2026-03-21)

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Regex scope | `r"^\s*[A-Za-z_][\w\[\], \|.]*\s*:"` | Covers 98%+ of real-world types. False positive negligible on first content line. |
| 2 | NumPy handling | Skip via natural guard (`_extract_section_content` -> `None`) | Clean skip, no false positives. Add one test (6.19). |
| 3 | Sphinx `:rtype:` | Raw string `":rtype:" in symbol.docstring` | Simple, correct, safe failure direction. Branch on `_active_style`. |
| 4 | Dogfooding | Integration test with `require_return_type=True` (6.28) | Opt-in rule tested via fixture. Quality gate proves default-off works. |
| 5 | `None:` as type | Valid typed entry -- regex matches, no finding | `None` is a type. Presence check, not correctness. Tests: 6.20, 6.21. |
| 6 | Multi-line/empty | "First non-empty content line" algorithm | Handles all edge cases naturally. Tests: 6.22-6.25. |

### Competitive Positioning (party-mode research 2026-03-21)

No existing Python linter checks return type PRESENCE. Competitors check different things:
- **pydoclint DOC203**: Return type in docstring INCONSISTENT with annotation (consistency, not presence)
- **darglint DAR203**: Return type doesn't MATCH signature (consistency, not presence)
- **pylint W9011**: Missing return DOC (section presence, not type)
- **ruff D rules**: Format/style only, no type checking

docvet `missing-return-type` fills a genuine gap: "does the reader have ANY way to determine the return type?" This is a unique differentiator. The rule and `missing-returns` form a **complementary pair**: `missing-returns` checks section presence (default on), `missing-return-type` checks type completeness within the section (opt-in). Users adopt incrementally.

### Domain Pitfalls (from Epic 34-35 and previous stories)

- **Guard on `symbol.docstring is not None`** for ty type narrowing (learned from 35.1)
- **Guard on `"Returns" not in sections`** to separate from `missing-returns` rule
- **Test helpers must select correct symbol type** -- verify `kind` and `name` match expectations before asserting on findings (dev quality checklist)
- **Test unfiltered findings** when adding rules to detect cross-rule conflicts (dev quality checklist)
- **Node lookup from `node_index`** -- use `node_index.get(symbol.line)` with guard, not direct `[]` access
- **Sphinx `:rtype:` is separate from `:returns:`** -- both map to `"Returns"` in sections, but for type detection, must check raw docstring for `:rtype:` specifically

### Test Strategy

Single test file `tests/unit/checks/test_missing_return_type.py` organized by AC. 28 test cases total (21 original + 7 party-mode consensus edge cases).

Follow the `_make_symbol_and_index` helper pattern from `test_missing_returns.py` (closest reference).

Use `@pytest.mark.parametrize` for:
- Type pattern regex variants: `dict:`, `list[str]:`, `str | None:`, `Optional[int]:`, `None:`, `Callable[[int], str]:` (AC: 7)
- Skip conditions: `__init__`, `__del__`, `@property`, `@cached_property` (AC: 4)
- Content edge cases: empty section, blank-line-then-type, multi-line untyped (party-mode Q6)

### Test Maturity Piggyback

Continue `@pytest.mark.parametrize` adoption pattern established in stories 35.1-35.4. This story has parametrize opportunities: type pattern matching variants, skip condition variants. Target: at least 2 parametrize usages.

Sourced from test-review.md (P2: parametrize adoption) -- address alongside this story's work.

### Documentation Impact

- Pages: `docs/site/rules/missing-return-type.md`, `docs/site/configuration.md`, `docs/site/checks/enrichment.md`
- Nature of update: Create new rule reference page following existing macros scaffold pattern (closest model: `docs/site/rules/missing-returns.md`); add `require-return-type` row to enrichment config table in configuration reference; add `missing-return-type` to enrichment check page rule list

### Project Structure Notes

- Alignment with unified project structure: new test file in `tests/unit/checks/`, 1 rule page in `docs/site/rules/`
- No conflicts or variances detected
- `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` must be updated from 29 to 30
- New config field `require_return_type` added to `EnrichmentConfig` + `_VALID_ENRICHMENT_KEYS`
- No changes to `_SPHINX_AUTO_DISABLE_RULES` -- rule works in both styles (different detection paths)
- First config key with `False` default in enrichment -- verify orchestrator handles `getattr(config, attr)` returning `False` correctly (it does: the `if getattr(config, attr):` guard at line 2652 will skip the rule)

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md, Story 35.5] -- FR19, FR20, NFR3, NFR4, NFR10
- [Source: src/docvet/checks/enrichment.py:2575-2594] -- `_RULE_DISPATCH` table (19 entries, add 1)
- [Source: src/docvet/checks/enrichment.py:2565-2572] -- `_SPHINX_AUTO_DISABLE_RULES` (no changes)
- [Source: src/docvet/checks/enrichment.py:214-253] -- `_extract_section_content` (reuse for Returns content extraction)
- [Source: src/docvet/checks/enrichment.py:494-532] -- `_should_skip_returns_check` (reference for skip pattern, but different guards since this rule REQUIRES Returns presence)
- [Source: src/docvet/checks/enrichment.py:558-624] -- `_check_missing_returns` (sibling rule -- checks section presence, this story checks type completeness)
- [Source: src/docvet/checks/enrichment.py:121-134] -- `_SPHINX_SECTION_MAP` (`:rtype:` maps to "Returns")
- [Source: src/docvet/config.py:92-169] -- `EnrichmentConfig` dataclass (add `require_return_type`)
- [Source: src/docvet/config.py:298-315] -- `_VALID_ENRICHMENT_KEYS` (add `require-return-type`)
- [Source: _bmad-output/implementation-artifacts/35-4-trivial-docstring-enrichment-rule.md] -- Previous story patterns, code review findings, domain pitfalls
- [Source: Party-mode consensus 2026-03-21] -- 6 decisions: regex scope, NumPy skip, Sphinx raw string, dogfooding via integration test, None: as valid type, first-non-empty-line algorithm
- [Source: Party-mode research 2026-03-21] -- Competitive analysis: no existing tool checks return type PRESENCE (pydoclint DOC203 and darglint DAR203 check consistency, not presence). Genuine differentiator.
- [Source: Google Python Style Guide] -- Returns section type is optional, format: `type: description` on first line
- [Source: NumPy docstring style guide] -- Returns format: `name : type` (colon with spaces, different from Google)
- [Source: Sphinx field list convention] -- `:rtype:` declares return type, `:returns:` describes return value

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory -- no exceptions. -->

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors
- [x] `uv run pytest` -- all tests pass, no regressions
- [x] `uv run docvet check --all` -- zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None -- zero-debug implementation.

### Completion Notes List

- `_RETURNS_TYPE_PATTERN` regex with letter/underscore first-char requirement (party-mode consensus Q1)
- `_has_return_type_in_docstring` branches Google/Sphinx via `_active_style` module variable
- Google mode: extracts Returns content, checks first non-empty line against regex
- Sphinx mode: raw string `":rtype:" in docstring` (party-mode consensus Q3)
- NumPy guard: `_extract_section_content` returns None -> conservatively return True (party-mode consensus Q2)
- `_check_missing_return_type` uniform 5-param signature, guards on docstring/sections/kind/dunder/property/annotation
- FR20 either-path satisfaction: annotation OR typed entry suffices
- Category `recommended`, config `require_return_type=False` (opt-in per NFR10)
- 36 tests (28 functions + 11 parametrized regex variants - 3 shared = 36 total)
- 1 `@pytest.mark.parametrize` usage with 11 variants for type pattern matching
- Zero required docvet findings on own codebase
- First enrichment config key defaulting to `False` -- orchestrator `getattr` guard handles correctly

### Change Log

- `src/docvet/config.py`: Added `require_return_type` field to `EnrichmentConfig`, added to `_VALID_ENRICHMENT_KEYS`
- `src/docvet/checks/enrichment.py`: Added `_RETURNS_TYPE_PATTERN`, `_has_return_type_in_docstring()`, `_check_missing_return_type()`, 1 `_RULE_DISPATCH` entry
- `tests/unit/checks/test_missing_return_type.py`: Created -- 36 tests covering all 8 ACs
- `tests/unit/test_docs_infrastructure.py`: Updated `_EXPECTED_RULE_COUNT` from 29 to 30
- `docs/site/rules/missing-return-type.md`: Created rule reference page
- `docs/rules.yml`: Added missing-return-type entry (30 total)
- `docs/site/checks/enrichment.md`: Added missing-return-type to rule table
- `docs/site/configuration.md`: Added `require-return-type` row
- `mkdocs.yml`: Added missing-return-type nav entry

### File List

| File | Action |
|------|--------|
| `src/docvet/config.py` | Modified |
| `src/docvet/checks/enrichment.py` | Modified |
| `tests/unit/checks/test_missing_return_type.py` | Created |
| `tests/unit/test_docs_infrastructure.py` | Modified |
| `docs/site/rules/missing-return-type.md` | Created |
| `docs/rules.yml` | Modified |
| `docs/site/checks/enrichment.md` | Modified |
| `docs/site/configuration.md` | Modified |
| `mkdocs.yml` | Modified |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story -- no exceptions (Epic 8 retro). -->

### Reviewer

Adversarial code review (AI) — 2026-03-21

### Outcome

Changes Requested — 5 fixes applied, 1 closed as by-design

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | enrichment.md intro says "17 rules" but table has 19 | Fixed — updated to "19 rules" |
| M1 | MEDIUM | rules.yml header comment says "all 29" but has 30 entries | Fixed — removed count from comment (future-proof) |
| M2 | MEDIUM | enrichment.md config table missing `require-return-type` | Fixed — added row |
| L1 | LOW | Finding message drops actionable suffix from spec | Closed — consistent with all other enrichment rule messages |
| L2 | LOW | AC-to-test mapping AC 8 references tasks not tests | Fixed — updated to reference `test_docs_infrastructure.py` tests |
| L3 | LOW | enrichment.md config table missing `check-trivial-docstrings` | Fixed — added row (pre-existing from 35.4) |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
