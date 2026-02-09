# Story 3.2: Format and Cross-Reference Rules

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect untyped `Attributes:` sections, missing cross-reference syntax in `See Also:` sections, missing `See Also:` on `__init__.py` modules, and `Examples:` using doctest format instead of fenced code blocks,
so that my docstrings follow best practices for readability and mkdocs rendering.

## Acceptance Criteria

1. **Given** a class with an `Attributes:` section using `name: description` format (no type), **When** `check_enrichment` is called, **Then** it returns a `Finding` with `rule="missing-typed-attributes"`, `category="recommended"`
2. **Given** a class with an `Attributes:` section using `name (type): description` format, **When** `check_enrichment` is called, **Then** it returns zero findings for `missing-typed-attributes`
3. **Given** `config.require_typed_attributes = False`, **When** `check_enrichment` is called, **Then** it returns zero findings for `missing-typed-attributes`
4. **Given** a symbol with a `See Also:` section that lacks cross-reference syntax, **When** `check_enrichment` is called, **Then** it returns a `Finding` with `rule="missing-cross-references"`, `category="recommended"`
5. **Given** `config.require_cross_references = False`, **When** `check_enrichment` is called, **Then** it returns zero findings for `missing-cross-references`
6. **Given** an `__init__.py` module with a module-level docstring and no `See Also:` section, **When** `check_enrichment` is called with `file_path` ending in `__init__.py`, **Then** it returns a `Finding` with `rule="missing-cross-references"` for the module-level symbol
7. **Given** a regular Python file (not `__init__.py`) with no `See Also:` section, **When** `check_enrichment` is called, **Then** it does NOT produce a `missing-cross-references` finding for the module-level symbol
8. **Given** a symbol with an `Examples:` section using `>>>` doctest format, **When** `check_enrichment` is called, **Then** it returns a `Finding` with `rule="prefer-fenced-code-blocks"`, `category="recommended"`
9. **Given** a symbol with an `Examples:` section using fenced code blocks (triple backticks), **When** `check_enrichment` is called, **Then** it returns zero findings for `prefer-fenced-code-blocks`
10. **Given** `config.prefer_fenced_code_blocks = False`, **When** `check_enrichment` is called, **Then** it returns zero findings for `prefer-fenced-code-blocks`
11. **Given** a symbol with no `Examples:` section at all, **When** `check_enrichment` is called, **Then** it returns zero findings for `prefer-fenced-code-blocks` (rule only applies when `Examples:` exists)

## Tasks / Subtasks

- [x] Task 1: Implement `_check_missing_typed_attributes` (AC: 1, 2, 3)
  - [x] 1.1: Add `_check_missing_typed_attributes` function after `_check_missing_attributes` in taxonomy order
  - [x] 1.2: Parse `Attributes:` section content from docstring — check each entry for `name (type): description` pattern
  - [x] 1.3: Return `Finding(rule="missing-typed-attributes", category="recommended")` when untyped entries found
  - [x] 1.4: Add config gating in orchestrator (`config.require_typed_attributes`)
  - [x] 1.5: Write tests: typed attrs pass, untyped attrs fire, mixed entries fire, config disabled, no Attributes section = no finding, module-level symbols
- [x] Task 2: Implement `_check_missing_cross_references` (AC: 4, 5, 6, 7)
  - [x] 2.1: Add `_check_missing_cross_references` function after `_check_missing_examples` in taxonomy order
  - [x] 2.2: Implement dual detection: (a) `__init__.py` modules missing `See Also:` entirely, (b) any symbol with `See Also:` lacking cross-reference syntax
  - [x] 2.3: Define cross-reference detection regex patterns (backtick identifiers, Markdown reference links, Sphinx roles)
  - [x] 2.4: Return `Finding(rule="missing-cross-references", category="recommended")`
  - [x] 2.5: Add config gating in orchestrator (`config.require_cross_references`)
  - [x] 2.6: Write tests: missing See Also on `__init__.py`, See Also without xrefs, See Also with valid xrefs (all 3 patterns), non-`__init__.py` without See Also = no finding, config disabled
- [x] Task 3: Implement `_check_prefer_fenced_code_blocks` (AC: 8, 9, 10, 11)
  - [x] 3.1: Add `_check_prefer_fenced_code_blocks` function last in taxonomy order
  - [x] 3.2: Check for `>>>` pattern in `Examples:` section content
  - [x] 3.3: Return `Finding(rule="prefer-fenced-code-blocks", category="recommended")` when doctest format found
  - [x] 3.4: Add config gating in orchestrator (`config.prefer_fenced_code_blocks`)
  - [x] 3.5: Write tests: doctest format fires, fenced code blocks pass, no Examples section = no finding, mixed Examples content, config disabled
- [x] Task 4: Update orchestrator and fixtures (AC: all)
  - [x] 4.1: Add dispatch entries for 3 new rules in `check_enrichment` in taxonomy-table order
  - [x] 4.2: Update `tests/fixtures/complete_module.py` — add `See Also:` sections with valid cross-references, ensure `Attributes:` use typed format, ensure `Examples:` use fenced code blocks
  - [x] 4.3: Update "all rules disabled" test to include the 3 new config toggles
  - [x] 4.4: Run full test suite and confirm zero regressions

## Dev Notes

### Rule Characteristics

All 3 rules are **docstring-only** — they inspect docstring text content without needing AST body walks or node_index lookups. This is the simplest rule tier per the architecture complexity tiering. All 3 produce `category="recommended"` findings.

### Implementation Details by Rule

#### Rule 1: `missing-typed-attributes` (FR11)

**What to detect:** An `Attributes:` section exists but entries use `name: description` instead of `name (type): description`.

**Section content extraction:** You need the raw text of the `Attributes:` section (not just whether the header exists). This requires a new helper to extract section content from the docstring. Approach:
- After confirming `"Attributes"` is in `sections`, extract the text between the `Attributes:` header and the next section header (or end of docstring)
- Parse each non-empty, indented line as an attribute entry
- Check if each entry matches the typed pattern: `^\s+(\w+)\s+\(.*\)\s*:` (name followed by parenthesized type, then colon)
- If ANY entry lacks the `(type)` pattern, fire the finding

**Typed attribute pattern (valid):**
```
    name (str): The user's name
    age (int): The user's age
    items (list[str]): Collection of items
```

**Untyped attribute pattern (violation):**
```
    name: The user's name
    age: The user's age
```

**Guard: Only applies when `"Attributes"` section exists.** No Attributes section = no finding (this rule checks format, not presence — `missing-attributes` handles presence).

**Guard: Only applies to class symbols** (`symbol.kind == "class"`). Module-level `Attributes:` sections in `__init__.py` document exports, not typed class fields — typing is not applicable.

**Message format (Decision 4):**
```
Attributes: section in class '{symbol.name}' lacks typed format (name (type): description)
```

#### Rule 2: `missing-cross-references` (FR12, FR13)

**Dual detection branches:**

**Branch A — Missing `See Also:` on `__init__.py` modules (FR13):**
- Applies when `symbol.kind == "module"` AND `_is_init_module(file_path)` AND `"See Also"` not in `sections`
- This is a **presence check** (like `missing-attributes` branch 5)
- Message: `Module '{symbol.name}' is an __init__.py but has no See Also: section`

**Branch B — `See Also:` exists but lacks cross-reference syntax (FR12):**
- Applies to **any symbol** with `"See Also"` in `sections`
- Extract `See Also:` section content (same extraction approach as `missing-typed-attributes`)
- Check if any line matches one of the cross-reference patterns:
  - Backtick-quoted identifier: `` `qualified.name` `` → regex: `` `[^`]+` ``
  - Markdown reference link: `[text][identifier]` or `[identifier][]` → regex: `\[[^\]]+\]\[`
  - Sphinx/intersphinx role: `:role:\`target\`` → regex: `:\w+:`[^`]+``
- If **no line** in the section matches any pattern → fire finding
- Message: `See Also: section in {symbolKind} '{symbol.name}' lacks cross-reference syntax`

**Implementation note:** Branch A fires first (module missing section entirely). If `See Also:` section exists, check branch B (format). This is still one `_check_*` function returning at most one Finding per symbol (FR18).

**`_is_init_module` helper already exists** — reuse it from `_check_missing_attributes`.

#### Rule 3: `prefer-fenced-code-blocks` (FR14)

**What to detect:** An `Examples:` section exists and contains `>>>` (doctest/REPL format) instead of fenced code blocks.

**Detection approach:**
- Only applies when `"Examples"` is in `sections`
- Extract `Examples:` section content
- Check for `>>>` pattern anywhere in the section content: regex `^\s*>>>`
- If `>>>` found → fire finding

**No `Examples:` section = no finding.** This rule checks format of existing Examples, not presence (that's `missing-examples`).

**Message format (Decision 4):**
```
Examples: section in {symbolKind} '{symbol.name}' uses doctest format (>>>) instead of fenced code blocks
```

### Section Content Extraction Helper

All 3 rules need to extract the text content of a specific section from the docstring. Create a shared private helper:

```python
def _extract_section_content(docstring: str, section_name: str) -> str | None:
```

**Behavior:**
- Find the line matching `^\s*{section_name}:\s*$`
- Collect subsequent lines until the next section header (matching `_SECTION_PATTERN`) or end of docstring
- Return the collected text (may be empty if section header exists but has no content)
- Return `None` if section not found

**This helper is used by:** `_check_missing_typed_attributes`, `_check_missing_cross_references` (branch B), `_check_prefer_fenced_code_blocks`

### Symbol Kind Display Names

For the format-rule message pattern (`{symbolKind}`), use these display names derived from `symbol.kind`:
- `"function"` → `"function"` (also covers methods — `symbol.kind` is `"method"` but `symbol.parent` distinguishes; for messages, use `"method"` when `symbol.kind == "method"`)
- `"class"` → `"class"`
- `"module"` → `"module"`

### Taxonomy-Table Insertion Points

New functions go in this order within `enrichment.py`:

1. `_check_missing_attributes` (existing)
2. **`_check_missing_typed_attributes`** ← NEW (line ~787, marked by comment)
3. `_check_missing_examples` (existing)
4. **`_check_missing_cross_references`** ← NEW
5. **`_check_prefer_fenced_code_blocks`** ← NEW (last rule)
6. `check_enrichment` orchestrator (existing, last function)

Orchestrator dispatch additions (in taxonomy order, after existing entries):
```python
if config.require_typed_attributes:
    if f := _check_missing_typed_attributes(symbol, sections, node_index, config, file_path):
        findings.append(f)
# ... existing missing-examples dispatch ...
if config.require_cross_references:
    if f := _check_missing_cross_references(symbol, sections, node_index, config, file_path):
        findings.append(f)
if config.prefer_fenced_code_blocks:
    if f := _check_prefer_fenced_code_blocks(symbol, sections, node_index, config, file_path):
        findings.append(f)
```

### Config Toggles (Already Exist)

All 3 config fields are **already defined** in `EnrichmentConfig` (`config.py`):
- `require_typed_attributes: bool = True`
- `require_cross_references: bool = True`
- `prefer_fenced_code_blocks: bool = True`

They are also in `_VALID_ENRICHMENT_KEYS`. **No config changes needed** — only enrichment.py and tests.

### Cross-Reference Detection Regex Constants

Define as module-level compiled patterns (following `_SECTION_PATTERN` convention):

```python
_XREF_BACKTICK = re.compile(r"`[^`]+`")
_XREF_MD_LINK = re.compile(r"\[[^\]]+\]\[")
_XREF_SPHINX = re.compile(r":\w+:`[^`]+`")
```

### Edge Cases to Test

**From retrospectives — known categories to cover:**

1. **Scope boundary:** Nested class/function within a class — `missing-typed-attributes` should only fire on the outer class's Attributes section, not be confused by inner class attrs
2. **No Attributes section:** `missing-typed-attributes` returns `None` (not a finding) when there's no Attributes section
3. **Module-level symbols:** `missing-typed-attributes` should NOT fire on module-level Attributes (module attrs document exports, not typed fields)
4. **Empty section content:** `Attributes:` header with no entries below → no finding for `missing-typed-attributes` (nothing to check)
5. **Mixed typed/untyped entries:** If even one entry lacks type → fire finding
6. **Cross-platform paths:** `_is_init_module` already handles `/` and `\` — reuse it
7. **No docstring symbols:** Orchestrator skips them — all 3 rules never see undocumented symbols
8. **See Also with only plain text:** `See Also:\n    some_module` (no backticks, no links) → fire `missing-cross-references`
9. **See Also with backtick xrefs:** `` See Also:\n    `some.module` `` → no finding
10. **See Also with Markdown links:** `See Also:\n    [module][some.module]` → no finding
11. **See Also with Sphinx roles:** `See Also:\n    :mod:\`some.module\`` → no finding
12. **Examples with only fenced blocks:** No `>>>` anywhere → no finding for `prefer-fenced-code-blocks`
13. **Examples with `>>>` in fenced block:** The `>>>` is inside a fenced code block — this is an edge case. For simplicity, fire the finding anyway (the docstring contains doctest-style content regardless of wrapping).
14. **No Examples section:** `prefer-fenced-code-blocks` returns `None`

### "All Rules Disabled" Test

The test at the bottom of `test_enrichment.py` dynamically discovers config toggles. It was updated in Story 3.1 to be dynamic. Verify it still works with 3 new rules by running it — no manual update should be needed if the dynamic approach works correctly.

### Previous Story Intelligence

**From Story 3.1 (missing-examples):**
- List-config gating pattern: `_check_missing_examples` reads `config.require_examples` internally. The 3 new rules DON'T need this — they use simple boolean gating in the orchestrator.
- Classification helpers (`_is_protocol`, `_is_enum`) already exist and are available if needed.
- `_is_init_module(file_path)` helper already exists — reuse for `missing-cross-references` branch A.
- The "all rules disabled" test was made dynamic in Story 3.1.

**From Epic 2 retrospective action items:**
- Cross-platform and async-variant categories should be in edge case testing (covered above).
- FR12 cross-reference syntax is now defined in architecture doc (3 patterns: backtick, Markdown, Sphinx).
- "All rules disabled" test should not need manual update if dynamic approach from Story 3.1 holds.

**From Epic 1 retrospective:**
- Scope-aware walk not needed for these 3 rules (docstring-only, no AST body walk).
- Edge case test reminders included above.

### Files to Modify

| File | Change |
|------|--------|
| `src/docvet/checks/enrichment.py` | Add `_extract_section_content` helper, 3 new `_check_*` functions, 3 new cross-reference regex constants, 3 new orchestrator dispatch entries |
| `tests/unit/checks/test_enrichment.py` | Add tests for all 3 rules (expect ~40-50 new tests) |
| `tests/fixtures/complete_module.py` | Add `See Also:` sections with valid xrefs, ensure typed `Attributes:`, ensure fenced code blocks in `Examples:` |

### Project Structure Notes

- All changes are within existing files — no new files created
- Taxonomy-table ordering maintained for new function definitions and dispatch
- `_extract_section_content` helper goes in the "Shared helper functions" section of enrichment.py (after `_parse_sections`, before rule-specific helpers)
- 3 new regex constants go after `_SECTION_PATTERN` in the module-level constants section

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 3.2 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Rule-to-function mapping, cross-reference syntax definition (FR12), complexity tiering]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR11, FR12, FR13, FR14 definitions]
- [Source: `_bmad-output/implementation-artifacts/3-1-missing-examples-detection.md` — Previous story patterns, dynamic test approach]
- [Source: `_bmad-output/implementation-artifacts/epic-2-retro-2026-02-08.md` — Edge case categories, action items]
- [Source: `_bmad-output/implementation-artifacts/epic-1-retro-2026-02-08.md` — Scope-aware walk, test gap patterns]
- [Source: `src/docvet/checks/enrichment.py` — Current module structure, insertion points]
- [Source: `src/docvet/config.py` — Existing config fields for 3 rules]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- ty type-narrowing: added `if not symbol.docstring` guards in 3 new `_check_*` functions to satisfy `ty` even though orchestrator already guards
- Multiline attribute description continuation lines: initial implementation matched continuation lines as entries; fixed by detecting base indentation level

### Completion Notes List

- Implemented `_extract_section_content` shared helper for extracting section text from docstrings
- Implemented `_check_missing_typed_attributes` (FR11): detects untyped `name: description` entries in `Attributes:` sections, guards on class-only symbols, handles multiline descriptions via base indentation detection
- Implemented `_check_missing_cross_references` (FR12/FR13): dual-branch detection — Branch A fires on `__init__.py` modules missing `See Also:` entirely, Branch B fires on any symbol with `See Also:` lacking cross-reference syntax (backtick, Markdown link, or Sphinx role patterns)
- Implemented `_check_prefer_fenced_code_blocks` (FR14): detects `>>>` doctest format in `Examples:` sections
- Added 3 cross-reference regex constants (`_XREF_BACKTICK`, `_XREF_MD_LINK`, `_XREF_SPHINX`) and `_DOCTEST_PATTERN`, `_TYPED_ATTR_PATTERN`
- Added `_SYMBOL_KIND_DISPLAY` mapping for format-rule messages
- Added 3 new dispatch entries in `check_enrichment` orchestrator in taxonomy-table order
- Updated `tests/fixtures/complete_module.py`: typed Attributes format, See Also sections with backtick xrefs, fenced code blocks in Examples
- "All rules disabled" test verified — dynamic approach from Story 3.1 works with 3 new boolean toggles (no manual update needed)
- 36 new tests added (4 `_extract_section_content` + 11 `_check_missing_typed_attributes` + 13 `_check_missing_cross_references` + 8 `_check_prefer_fenced_code_blocks`), total 414 tests all passing

### File List

- `src/docvet/checks/enrichment.py` — Added `_extract_section_content` helper, 3 `_check_*` functions, 5 regex constants, `_SYMBOL_KIND_DISPLAY` dict, 3 orchestrator dispatch entries
- `tests/unit/checks/test_enrichment.py` — Added 36 new tests for all 3 rules + section content extraction helper
- `tests/fixtures/complete_module.py` — Updated Attributes to typed format, added See Also sections with xrefs

### Change Log

- 2026-02-09: Implemented Story 3.2 — Format and Cross-Reference Rules (missing-typed-attributes, missing-cross-references, prefer-fenced-code-blocks)
