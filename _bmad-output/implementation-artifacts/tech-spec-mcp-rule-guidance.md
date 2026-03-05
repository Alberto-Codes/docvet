---
title: 'MCP Rule Guidance for AI Agents'
slug: 'mcp-rule-guidance'
created: '2026-03-04'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python', 'mcp', 'fastmcp']
files_to_modify: ['src/docvet/mcp.py', 'tests/unit/test_mcp.py']
code_patterns: ['_RULE_CATALOG dict extension', '_serialize_finding unchanged']
test_patterns: ['catalog key assertions', 'parametrized round-trip fixture tests', 'structural validation']
---

# Tech-Spec: MCP Rule Guidance for AI Agents

**Created:** 2026-03-04

## Overview

### Problem Statement

AI agents using docvet's MCP server (`docvet_check` and `docvet_rules` tools) cannot fix docstring findings on the first attempt because the rule catalog provides only diagnostic descriptions ("what's wrong") without prescriptive guidance ("how to fix it"). Phase 1 validation on a realistic test module showed a 43% first-attempt failure rate across enrichment rules, with `missing-cross-references` being completely unguessable (requires mkdocstrings `[`symbol`][]` syntax) and `missing-examples` defaulting to doctest format instead of the required fenced code blocks.

### Solution

Add `guidance` and `fix_example` fields to each entry in `_RULE_CATALOG` (in `mcp.py`), fix the misleading `missing-cross-references` description, and update the `docvet_check` tool docstring to reference `docvet_rules` for fix guidance. The guidance flows through the existing `docvet_rules` MCP tool automatically — no new tools or endpoints needed.

### Scope

**In Scope:**

- `guidance` (brief prescriptive text) + `fix_example` (canonical docstring snippet or `null`) for all 20 rules
  - **Format-fixable rules** (enrichment + griffe, 14 rules): `guidance` + `fix_example`
  - **Action-oriented rules** (freshness + coverage, 6 rules): `guidance` only, `fix_example: null`
- Fix `missing-cross-references` description to cover both Branch A (missing section) and Branch B (lacks link syntax)
- Update `docvet_check` tool docstring to add: "Call docvet_rules() for per-rule fix guidance and format examples."
- Tests asserting all catalog entries have `guidance` + `fix_example` keys
- Round-trip tests proving format-fixable `fix_example` snippets pass docvet checks
- Structural validation tests on `fix_example` content

**Out of Scope:**

- Per-finding `fix_hint` field in `_serialize_finding` (additive later if needed)
- CLI `docvet rules` guidance output
- Extracting `_RULE_CATALOG` to a shared module
- Changes to core enrichment engine messages
- Changes to LSP server diagnostic messages

## Context for Development

### Codebase Patterns

- `_RULE_CATALOG` is a `list[dict[str, str]]` at module level in `mcp.py` — each entry has `name`, `check`, `description`, `category`
- `docvet_rules()` returns `json.dumps({"rules": _RULE_CATALOG})` — any new fields added to catalog entries flow through automatically
- `_serialize_finding()` converts `Finding` → dict with 6 keys — this stays unchanged (per consensus: lean findings, rich catalog)
- `_RULE_TO_CHECK` is derived from `_RULE_CATALOG` — adding new keys doesn't affect it

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/mcp.py` | MCP server — `_RULE_CATALOG` (lines 91-212), `docvet_check` (line 508), `docvet_rules` (line 591) |
| `tests/unit/test_mcp.py` | MCP unit tests — `TestDocvetRules.test_rules_have_all_required_fields` (line 222), `TestRuleCatalogStaleness.test_rule_catalog_entries_have_required_keys` (line 498) |
| `src/docvet/checks/enrichment.py` | Enrichment check rules — reference for what each rule expects |
| `docs/site/rules/*.md` | 20 rule reference pages with "How to Fix" sections — source of truth for guidance wording |

### Technical Decisions

1. **Catalog-only guidance** — `guidance` and `fix_example` live in `_RULE_CATALOG`, not in serialized findings. Agents call `docvet_rules()` once, cache the catalog, look up fixes by rule name. Avoids payload bloat when many findings share the same rule.
2. **`fix_example` is `null` for non-format rules** — Freshness rules (`stale-*`) and coverage (`missing-init`) don't have docstring format fixes. Their `guidance` gives contextual advice; `fix_example` is `null`.
3. **Description fix scoped to `missing-cross-references` only** — The only factually wrong description. Others stay as-is.
4. **Type annotation update** — `_RULE_CATALOG` type changes from `list[dict[str, str]]` to `list[dict[str, str | None]]` to accommodate `fix_example: null`.
5. **Guidance length** — Brief prescriptive text, no one-sentence constraint. Most rules need one sentence; `missing-cross-references` may need two. The `fix_example` carries the heavy lifting.
6. **Round-trip test isolation** — Use `EnrichmentConfig` per-rule toggles to isolate each test. Config disables all rules except the one under test, preventing cross-rule contamination.
7. **Round-trip test scope** — 10 enrichment rules (core) + 3 griffe rules (gated behind `importorskip("griffe")`). Skip `missing-docstring` (presence check, not enrichment), `missing-init` (file creation), and all freshness rules (`fix_example: null`).
8. **Test location** — New test classes in `test_mcp.py` (catalog lives in `mcp.py`, so tests stay co-located).

## Implementation Plan

### Tasks

- [x] Task 1: Add `guidance` and `fix_example` fields to all 20 `_RULE_CATALOG` entries
  - File: `src/docvet/mcp.py`
  - Action: Extend each dict in `_RULE_CATALOG` (lines 91-212) with two new keys. Update type annotation from `list[dict[str, str]]` to `list[dict[str, str | None]]`. Source guidance text from `docs/site/rules/*.md` "How to Fix" sections.
  - Notes: `fix_example` values use 4-space indentation and fenced code blocks where applicable. Freshness and coverage rules get `fix_example: None`. Guidance text for each rule:

  | Rule | `guidance` | `fix_example` |
  | --- | --- | --- |
  | `missing-docstring` | Add a Google-style docstring with a one-line summary ending in a period, followed by a detailed description. | `"""One-line summary.\n\nDetailed description.\n"""` |
  | `missing-raises` | Add a Raises: section listing each exception type and the condition that triggers it. | `Raises:\n    ValueError: If the input is negative.` |
  | `missing-yields` | Add a Yields: section describing what values the generator produces. | `Yields:\n    Row data as a dictionary with column names as keys.` |
  | `missing-receives` | Add a Receives: section documenting values accepted via .send(). | `Receives:\n    Numeric value to add to the running total.` |
  | `missing-warns` | Add a Warns: section listing each warning category and the condition. | `Warns:\n    UserWarning: If timeout is less than 5 seconds.` |
  | `missing-other-parameters` | Add an Other Parameters: section documenting *args and/or **kwargs. | `Other Parameters:\n    **kwargs: Arbitrary keyword arguments passed to the\n        underlying handler.` |
  | `missing-attributes` | Add an Attributes: section listing all public instance attributes with types and descriptions. | `Attributes:\n    name (str): The user's display name.\n    email (str): The user's email address.` |
  | `missing-typed-attributes` | Use typed attribute format: name (type): description. | `Attributes:\n    host (str): The server hostname.\n    port (int): The server port number.` |
  | `missing-examples` | Add an Examples: section with a brief description followed by a fenced code block using ```python. | `Examples:\n    Create a widget with default settings:\n\n    ```python\n    widget = Widget()\n    assert widget.is_active\n    ``` ` |
  | `missing-cross-references` | Add a See Also: section using mkdocstrings cross-reference syntax: [`fully.qualified.Name`][]. Each entry uses bracket-backtick-bracket format for linkable references. | `See Also:\n    [`mypackage.Config`][]: Application configuration.\n    [`mypackage.utils`][]: Utility functions.` |
  | `prefer-fenced-code-blocks` | Replace >>> doctest or :: reST indented code blocks with fenced ```python blocks. | `Examples:\n    Run the check:\n\n    ```python\n    result = check(data)\n    ``` ` |
  | `stale-signature` | Update the docstring Args, Returns, and Raises sections to match the changed function signature. | `null` |
  | `stale-body` | Review and update the docstring description and sections to reflect the changed function behavior. | `null` |
  | `stale-import` | Review the docstring for references to changed imports and update accordingly. | `null` |
  | `stale-drift` | Review and refresh the docstring to reflect cumulative code changes since the last docstring edit. | `null` |
  | `stale-age` | Review and confirm the docstring still accurately describes the symbol's current behavior. | `null` |
  | `missing-init` | Create an __init__.py file with a module docstring in the directory. | `null` |
  | `griffe-unknown-param` | Remove or rename the documented parameter in the Args: section to match the actual function signature. | `Args:\n    name (str): The user's display name.` |
  | `griffe-missing-type` | Add parenthesized type annotations to parameter entries: name (type): description. | `Args:\n    name (str): The user's display name.` |
  | `griffe-format-warning` | Fix docstring formatting: ensure proper indentation (4 spaces), correct section headers, and valid Google-style syntax. | `Args:\n    data (dict): The input data to process.` |

- [x] Task 2: Fix `missing-cross-references` description
  - File: `src/docvet/mcp.py`
  - Action: Change description from `"Docstring references other symbols without cross-reference links."` to `"Module missing See Also section, or existing See Also entries lack cross-reference link syntax."`

- [x] Task 3: Update `docvet_check` and `docvet_rules` tool docstrings
  - File: `src/docvet/mcp.py`
  - Action:
    - `docvet_check` docstring: Add sentence after the Returns paragraph: `"Call docvet_rules() for per-rule fix guidance and format examples."`
    - `docvet_rules` docstring: Update the Returns description to mention the new fields: `"JSON string with a rules array containing objects with name, check, description, category, guidance, and fix_example keys."`

- [x] Task 4: Update existing catalog key assertion tests
  - File: `tests/unit/test_mcp.py`
  - Action: Update two tests that assert exact key sets:
    - `TestDocvetRules.test_rules_have_all_required_fields` (line 225): change expected keys from `{"name", "check", "description", "category"}` to `{"name", "check", "description", "category", "guidance", "fix_example"}`
    - `TestRuleCatalogStaleness.test_rule_catalog_entries_have_required_keys` (line 499): same change

- [x] Task 5: Add catalog guidance completeness tests
  - File: `tests/unit/test_mcp.py`
  - Action: Add new test class `TestRuleCatalogGuidance` with tests:
    - `test_all_entries_have_guidance_string` — assert every entry has `guidance` as a non-empty string
    - `test_format_fixable_rules_have_fix_example` — assert enrichment + griffe + presence rules have non-null `fix_example`
    - `test_action_rules_have_null_fix_example` — assert freshness + coverage rules have `fix_example is None`
    - `test_cross_references_description_covers_both_branches` — assert the `missing-cross-references` description contains language covering both "missing" (Branch A) and "lack" (Branch B)

- [x] Task 6: Add structural validation tests for fix_example content
  - File: `tests/unit/test_mcp.py`
  - Action: Add parametrized test `test_fix_example_structural_validity` in `TestRuleCatalogGuidance`:
    - Iterate all catalog entries where `fix_example is not None` **and** `check != "presence"` (presence `fix_example` is a full docstring, not a section snippet — different indentation semantics)
    - Assert no tab characters
    - Assert fenced code blocks have matching ` ``` ` delimiters (even count)
    - Assert non-header lines (lines after the first) start with 4+ spaces of indentation

- [x] Task 7: Add round-trip tests for enrichment rules
  - File: `tests/unit/test_mcp.py`
  - Action: Add `TestRuleCatalogGuidanceRoundTrip` class with parametrized before/after fixture pairs for **10** enrichment rules (`missing-docstring` is presence, not enrichment — skip it). Each test:
    1. Creates a `before` source string that triggers exactly one rule
    2. Runs `check_enrichment` with an isolated `EnrichmentConfig` (see config factory below)
    3. Asserts at least one finding with the expected rule name
    4. Creates an `after` source string that includes the fix (informed by `fix_example`)
    5. Runs `check_enrichment` again with same config
    6. Asserts zero findings for that rule
  - Notes: Use `pytest.mark.parametrize` with `(rule_name, before_source, after_source, config)` tuples.

  **Config isolation factory (F1 fix):** Create a test helper that returns an `EnrichmentConfig` with ALL toggles disabled except the target rule. Every boolean toggle defaults to `True` in `EnrichmentConfig`, so the factory must explicitly set all to `False` and only enable the target:

  ```python
  def _isolated_config(rule_name: str) -> EnrichmentConfig:
      base = EnrichmentConfig(
          require_raises=False,
          require_yields=False,
          require_receives=False,
          require_warns=False,
          require_other_parameters=False,
          require_attributes=False,
          require_typed_attributes=False,
          require_examples=[],
          require_cross_references=False,
          require_fenced_code_blocks=False,
      )
      # Enable only the target rule
      match rule_name:
          case "missing-raises": base = replace(base, require_raises=True)
          case "missing-yields": base = replace(base, require_yields=True)
          # ... etc for each rule
      return base
  ```

  **Fixture requirements table (F2/F3/F4/F5/F6/F15 fix):** Each rule requires specific AST patterns in its `before` fixture:

  | Rule | Fixture symbol kind | Trigger requirement | `after` fix |
  | --- | --- | --- | --- |
  | `missing-raises` | Function | Body contains `raise ValueError(...)` | Add `Raises:\n    ValueError: ...` section |
  | `missing-yields` | Function | Body contains `yield` | Add `Yields:\n    ...` section |
  | `missing-receives` | Function | Body contains `value = yield` (send pattern) | Add `Receives:\n    ...` section |
  | `missing-warns` | Function | Body contains `warnings.warn(...)` | Add `Warns:\n    UserWarning: ...` section |
  | `missing-other-parameters` | Function | Signature has `**kwargs` | Add `Other Parameters:\n    **kwargs: ...` section |
  | `missing-attributes` | Class | `__init__` assigns `self.name = ...` | Add `Attributes:\n    name (str): ...` section |
  | `missing-typed-attributes` | Class | Has `Attributes:` section but untyped (`name: desc`) | Change to `name (type): desc` format |
  | `missing-examples` | Class | Any class (config: `require_examples=["class"]`) | Add `Examples:\n    ...\n    ```python\n    ...\n    ``` ` section |
  | `missing-cross-references` | Module docstring | Module-level docstring missing `See Also:` | Add `See Also:\n    [`symbol`][]: ...` section |
  | `prefer-fenced-code-blocks` | Any symbol | `Examples:` section containing `>>>` doctest syntax | Replace `>>>` with fenced ` ```python ` block |

- [x] Task 8: Add round-trip tests for griffe rules (gated)
  - File: `tests/unit/test_mcp.py`
  - Action: Add `TestRuleCatalogGuidanceRoundTripGriffe` class gated behind `pytest.importorskip("griffe")`. Parametrized before/after for 3 griffe rules using `check_griffe_compat`.
  - Notes: Unlike enrichment round-trips (which parse in-memory strings), griffe requires **files on disk**. Write `before` and `after` sources to `tmp_path` files, then call `check_griffe_compat(src_root=tmp_path, files=[file_path])`. The `tmp_path` fixture provides the temp directory.

### Acceptance Criteria

- [x] AC 1: Given the MCP server is running, when an agent calls `docvet_rules()`, then every rule in the response has `guidance` (non-empty string) and `fix_example` (string or null) fields.
- [x] AC 2: Given a rule with `fix_example` is not null, when the example content is applied to a docstring triggering that rule, then `check_enrichment` (or `check_griffe_compat`) reports zero findings for that rule.
- [x] AC 3: Given the `missing-cross-references` rule, when an agent reads the catalog, then the `description` covers both Branch A (missing section) and Branch B (lacks link syntax), and the `guidance` explicitly shows the `[`symbol`][]` mkdocstrings syntax.
- [x] AC 4: Given the `docvet_check` tool, when an agent reads its description, then it includes a reference to call `docvet_rules()` for fix guidance.
- [x] AC 5: Given any `fix_example` string in the catalog, when inspected structurally, then it contains no tabs, has matching fenced block delimiters, and uses consistent 4-space indentation.
- [x] AC 6: Given the existing test suite, when all changes are applied, then `uv run pytest tests/unit/test_mcp.py` passes with zero failures (existing tests updated, new tests green).

## Additional Context

### Dependencies

- No new runtime dependencies
- No new test dependencies
- Griffe round-trip tests gated behind optional `griffe` extra

### Testing Strategy

**Unit tests (all in `test_mcp.py`):**

1. **Existing tests updated** (Task 4): Two exact-match key assertions expanded to include `guidance` and `fix_example`
2. **Catalog completeness** (Task 5): 4 new tests — guidance present, fix_example present for format-fixable, fix_example null for action-oriented, cross-references description covers both branches
3. **Structural validation** (Task 6): Parametrized test on non-null fix_example entries (excluding presence) — no tabs, matching fences, 4-space relative indent
4. **Round-trip enrichment** (Task 7): 10 parametrized before/after pairs — each rule isolated via `_isolated_config` factory that disables all other toggles
5. **Round-trip griffe** (Task 8): 3 parametrized pairs gated behind importorskip, using tmp_path files on disk

**Verification command:** `uv run pytest tests/unit/test_mcp.py -v`

### Notes

- **Guidance text is part of the API contract** — once shipped, agents may depend on specific wording. Be deliberate with phrasing; source from the existing docs/site/rules/*.md "How to Fix" sections for consistency.
- **The `_RULE_CATALOG` serialization is automatic** — `docvet_rules()` does `json.dumps({"rules": _RULE_CATALOG})`, so new fields appear in the MCP response with zero wiring changes.
- **`_serialize_finding` is deliberately unchanged** — per consensus, findings stay lean. If per-finding hints are needed later, it's an additive change.
- **`fix_example` strings must use `\n` for newlines** — they are JSON-serialized, so the raw string in Python uses actual newlines inside the string literal, which `json.dumps` escapes to `\n`.
- **Type annotation `str | None` may trigger ty warnings** — `_RULE_TO_CHECK` accesses `r["name"]` and `r["check"]` which are always strings, but the dict value type is now `str | None`. If `ty check` flags this, narrow the type via assertion or use a cast. Verify with `uv run ty check` during implementation.
