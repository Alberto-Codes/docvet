# Story 34.4: `overload-has-docstring` Check

Status: review
Branch: `feat/presence-34-4-overload-has-docstring`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag `@overload`-decorated functions that have docstrings,
so that documentation lives only on the implementation function where `help()` and doc generators expect it.

## Acceptance Criteria

1. **Given** a function decorated with `@overload` (from `typing` or `typing_extensions`) that has a docstring, **When** the check runs, **Then** a finding is emitted: `overload-has-docstring` with message identifying the function name.

2. **Given** a function decorated with `@typing.overload` (attribute access form) that has a docstring, **When** the check runs, **Then** a finding is emitted (both `@overload` name form and `@typing.overload` attribute form are detected).

3. **Given** an `@overload`-decorated function with no docstring, **When** the check runs, **Then** no finding is produced.

4. **Given** the implementation function (no `@overload` decorator) with a docstring, **When** the check runs, **Then** no finding is produced (only overloads are flagged).

5. **Given** `check-overload-docstrings = false` in `[tool.docvet.presence]`, **When** the check runs, **Then** the rule is skipped entirely.

6. **Given** the `overload-has-docstring` rule, **When** inspecting its wiring, **Then** the rule lives in the presence layer (not enrichment) since it's about whether a docstring should exist.

7. **Given** the `overload-has-docstring` rule is implemented and tested, **When** the story is marked done, **Then** a rule reference page exists in `docs/site/rules/` and is registered in `docs/rules.yml` following the existing pattern.

## Tasks / Subtasks

- [x] Task 1: Add `check_overload_docstrings` to `PresenceConfig` and config parsing (AC: 5)
  - [x] 1.1 Add `check_overload_docstrings: bool = True` field to `PresenceConfig` dataclass in `src/docvet/config.py` (after `ignore_private`, line ~188)
  - [x] 1.2 Add `"check-overload-docstrings"` to `_VALID_PRESENCE_KEYS` frozenset (line ~294-296)
  - [x] 1.3 The existing `_parse_presence()` loop already handles `bool` keys generically — verify it converts `check-overload-docstrings` to `check_overload_docstrings` via `key.replace("-", "_")`
  - [x] 1.4 Add `("check_overload_docstrings", "check-overload-docstrings")` to the `format_config_toml()` presence section field list (line ~965-971)

- [x] Task 2: Implement overload detection in `src/docvet/checks/presence.py` (AC: 1, 2, 3, 4, 6)
  - [x] 2.1 Add `import ast` (already present) — no new imports needed
  - [x] 2.2 Create `_has_overload_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool` helper that checks `node.decorator_list` for:
    - `ast.Name` with `id == "overload"` (bare `@overload`)
    - `ast.Attribute` with `attr == "overload"` (e.g., `@typing.overload`, `@typing_extensions.overload`)
  - [x] 2.3 Create `_check_overload_docstrings(tree: ast.Module, file_path: str) -> list[Finding]` that walks the tree with `ast.walk()`, finds `FunctionDef`/`AsyncFunctionDef` nodes where `_has_overload_decorator()` is True AND `ast.get_docstring(node)` is truthy, and produces findings
  - [x] 2.4 Wire into `check_presence()`: after the main symbol loop, if `config.check_overload_docstrings` is True, call `_check_overload_docstrings(tree, file_path)` and extend findings
  - [x] 2.5 Finding fields: `file=file_path`, `line=node.lineno`, `symbol=node.name`, `rule="overload-has-docstring"`, `message="Overloaded function '{name}' should not have a docstring — document the implementation instead"`, `category="required"`

- [x] Task 3: Write comprehensive tests in `tests/unit/checks/test_overload_docstring.py` (AC: 1-5)
  - [x] 3.1 Create `tests/unit/checks/test_overload_docstring.py` with `pytestmark = pytest.mark.unit`
  - [x] 3.2 Test: `@overload` (bare name) with docstring -> 1 finding (AC: 1)
  - [x] 3.3 Test: `@typing.overload` (attribute form) with docstring -> 1 finding (AC: 2)
  - [x] 3.4 Test: `@typing_extensions.overload` with docstring -> 1 finding (AC: 2)
  - [x] 3.5 Test: `@overload` without docstring -> 0 findings (AC: 3)
  - [x] 3.6 Test: implementation function (no `@overload`) with docstring -> 0 findings (AC: 4)
  - [x] 3.7 Test: `check_overload_docstrings = False` -> rule skipped, 0 findings (AC: 5)
  - [x] 3.8 Test: all 6 Finding fields verified (file, line, symbol, rule, message, category)
  - [x] 3.9 Test: multiple overloads with docstrings -> multiple findings
  - [x] 3.10 Test: mix of overload-with-docstring and overload-without-docstring -> correct count
  - [x] 3.11 Test: `@overload` on a method inside a class with docstring -> finding
  - [x] 3.12 Test: `@overload` on async function with docstring -> finding
  - [x] 3.13 Negative test: decorator named `overload` from non-typing module -> still detected (name-only check, intentionally broad — matches `from typing import overload` and `from typing_extensions import overload`)

- [x] Task 4: Create rule reference page and docs (AC: 7)
  - [x] 4.1 Add rule entry to `docs/rules.yml`
  - [x] 4.2 Create `docs/site/rules/overload-has-docstring.md` with `rule_header()`, `rule_fix()` macros, What it detects, Why is this a problem, Example (tabbed Violation/Fix). Mentions ruff D418 equivalence.
  - [x] 4.3 Add nav entry under `Rules: > Presence:` in `mkdocs.yml`: `- overload-has-docstring: rules/overload-has-docstring.md`
  - [x] 4.4 Update `docs/site/checks/presence.md` Rules table: add row for `overload-has-docstring`, update rule count in intro paragraph from "1 rule" to "2 rules"

- [x] Task 5: Update config docs and dogfooding (AC: 5, 7)
  - [x] 5.1 Update `docs/site/checks/presence.md` Configuration table: add `check-overload-docstrings` row with type `bool`, default `true`, description
  - [x] 5.2 Update `docs/site/configuration.md` — added `check-overload-docstrings` row to presence keys table
  - [x] 5.3 Run `docvet check --all` -> zero findings
  - [x] 5.4 Run `mkdocs build --strict` -> zero warnings
  - [x] 5.5 All quality gates pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `TestOverloadBareNameWithDocstring::test_bare_overload_with_docstring` | Pass |
| 2 | `TestOverloadAttributeFormWithDocstring::test_typing_dot_overload_with_docstring`, `test_typing_extensions_dot_overload_with_docstring` | Pass |
| 3 | `TestOverloadWithoutDocstring::test_bare_overload_no_docstring` | Pass |
| 4 | `TestImplementationWithDocstring::test_implementation_not_flagged` | Pass |
| 5 | `TestConfigToggle::test_disabled_produces_no_findings` | Pass |
| 6 | Rule implemented in `src/docvet/checks/presence.py` (presence layer) — verified by module location | Pass |
| 7 | Rule page at `docs/site/rules/overload-has-docstring.md`, registered in `docs/rules.yml`, nav entry in `mkdocs.yml`, `mkdocs build --strict` passes | Pass |

## Dev Notes

### Architecture — Presence Layer Extension

**Why presence, not enrichment:** The `overload-has-docstring` rule is about whether a docstring **should exist** at all — a Layer 1 (Presence) concern. Enrichment (Layer 3) checks completeness of existing docstrings. An `@overload` function with a docstring has the opposite problem: the docstring should be absent. This makes it the inverse of `missing-docstring` — both live in the presence layer.

**Key constraint — Symbol lacks AST node:** The `Symbol` dataclass (`src/docvet/ast_utils.py:38-108`) does NOT hold a reference to the original AST node. Its fields are: `name`, `kind`, `line`, `end_line`, `definition_start`, `docstring`, `docstring_range`, `signature_range`, `body_range`, `parent`. There is no `node` or `decorators` field.

**Implementation approach — direct tree walk:** Since `check_presence()` already has the `tree` from `ast.parse()`, the overload check walks the tree directly using `ast.walk()` to find `FunctionDef`/`AsyncFunctionDef` nodes with `@overload` decorators and docstrings. This avoids modifying the `Symbol` dataclass (which would affect all check modules).

### Key Implementation Patterns

**Decorator detection helper:**

```python
def _has_overload_decorator(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Check if a function node has an @overload decorator."""
    for decorator in node.decorator_list:
        # @overload (bare name import)
        if isinstance(decorator, ast.Name) and decorator.id == "overload":
            return True
        # @typing.overload or @typing_extensions.overload (attribute access)
        if isinstance(decorator, ast.Attribute) and decorator.attr == "overload":
            return True
    return False
```

**Overload check function:**

```python
def _check_overload_docstrings(
    tree: ast.Module,
    file_path: str,
) -> list[Finding]:
    """Find @overload-decorated functions that have docstrings."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _has_overload_decorator(node) and ast.get_docstring(node):
            findings.append(Finding(
                file=file_path,
                line=node.lineno,
                symbol=node.name,
                rule="overload-has-docstring",
                message=(
                    f"Overloaded function '{node.name}' should not have "
                    "a docstring \u2014 document the implementation instead"
                ),
                category="required",
            ))
    return findings
```

**Wiring in check_presence() (after existing symbol loop):**

```python
# After existing findings loop, before return:
if config.check_overload_docstrings:
    findings.extend(_check_overload_docstrings(tree, file_path))
```

### Config Changes

**File: `src/docvet/config.py`**

1. `PresenceConfig` (line ~151-188): Add `check_overload_docstrings: bool = True`
2. `_VALID_PRESENCE_KEYS` (line ~294-296): Add `"check-overload-docstrings"`
3. `_parse_presence()` (line ~534-562): No change needed — existing generic `bool` parsing handles it via `key.replace("-", "_")`
4. `format_config_toml()` (line ~962-976): Add `("check_overload_docstrings", "check-overload-docstrings")` to presence fields

### Stats Impact

The overload check does NOT affect `PresenceStats`. An `@overload` function with a docstring is still "documented" in the coverage sense — the overload finding is a separate concern about misplaced documentation, not coverage.

### PresenceStats Interaction

Overloaded functions with docstrings are counted as "documented" in stats. The `overload-has-docstring` findings are appended after the main loop, so they don't alter the `total_documented` / `total_total` aggregation in `_run_presence()`.

### Previous Story Patterns

From Story 34-3 (NumPy sections):
- Dedicated test file: `tests/unit/checks/test_numpy_sections.py`
- Module-level `pytestmark = pytest.mark.unit`
- Zero-debug implementation (XS story)
- No new config keys (but this story DOES add a config key)

From Story 34-2 (missing-returns):
- `_check_*` helper follows uniform pattern: isolated, testable function
- Test pattern: verify all 6 Finding fields, include positive and negative cases
- Config gating: boolean toggle checked before calling the helper

From Story 34-1 (Sphinx/RST):
- Config key naming: kebab-case in TOML, snake_case in Python
- `_VALID_*_KEYS` frozenset updated
- `format_config_toml()` field list updated

### Git Intelligence

Recent commits show Epic 34 momentum:
- `62ce6ed feat(enrichment): add NumPy-style section recognition (#344)` — Story 34.3
- `31faf3d feat(enrichment): add missing-returns rule (#334)` — Story 34.2
- `1bbd18f feat(enrichment): add Sphinx/RST docstring style support (#332)` — Story 34.1

All three previous stories in this epic followed the same pattern: implementation + tests + quality gates. This story is XS size — simpler than all three predecessors.

### Project Structure Notes

- **Modified files:**
  - `src/docvet/config.py` — add config field, valid key, format entry
  - `src/docvet/checks/presence.py` — add `_has_overload_decorator()`, `_check_overload_docstrings()`, wire into `check_presence()`
  - `docs/rules.yml` — add rule entry
  - `docs/site/checks/presence.md` — add rule to table, update rule count, add config row
  - `mkdocs.yml` — add nav entry
- **New files:**
  - `tests/unit/checks/test_overload_docstring.py` — dedicated test file
  - `docs/site/rules/overload-has-docstring.md` — rule reference page
- No new modules, packages, or runtime dependencies

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 34.4] — Full AC and FR mapping (FR25)
- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Requirements Inventory] — NFR3 (uniform signature)
- [Source: src/docvet/checks/presence.py] — Current presence check implementation (164 lines, 1 rule)
- [Source: src/docvet/config.py:151-188] — `PresenceConfig` dataclass (5 fields)
- [Source: src/docvet/config.py:294-296] — `_VALID_PRESENCE_KEYS` frozenset
- [Source: src/docvet/config.py:534-562] — `_parse_presence()` function
- [Source: src/docvet/config.py:962-976] — `format_config_toml()` presence section
- [Source: src/docvet/ast_utils.py:38-108] — `Symbol` dataclass (no AST node field — key constraint)
- [Source: docs/rules.yml] — Rule metadata catalog (21 rules currently)
- [Source: docs/site/rules/missing-docstring.md] — Existing presence rule page (template reference)
- [Source: docs/site/checks/presence.md] — Presence check overview page (1 rule currently)
- [Source: _bmad-output/implementation-artifacts/34-3-numpy-style-section-recognition-phase-1.md] — Previous story patterns

### Test Maturity Piggyback

From test-review.md — Recommendation 2 (P3): Continue splitting `test_enrichment.py` by rule. This story naturally contributes by creating a dedicated `test_overload_docstring.py` file for the new rule in the presence module. Progress: 3 of 10+ rules/concerns extracted (prefer-fenced-code-blocks, numpy-sections, overload-docstring).

### Documentation Impact

- Pages: docs/site/rules/overload-has-docstring.md (new), docs/site/checks/presence.md, docs/site/configuration.md (if presence keys are listed)
- Nature of update: New rule reference page with detection explanation, examples, and suppression guidance. Update presence check overview with new rule in table and config reference. Update configuration reference with new `check-overload-docstrings` key.

<!-- Decision tree:
  CLI changes → no
  Config key changes → yes: check-overload-docstrings in [tool.docvet.presence] → docs/site/checks/presence.md (config table), docs/site/configuration.md
  Check behavior changes → yes: presence check gains new rule → docs/site/checks/presence.md
  Rule changes → yes: new rule → docs/site/rules/overload-has-docstring.md
  Public API surface changes → no
  User workflow changes → no
-->

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1424 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Implemented `overload-has-docstring` rule in the presence layer (2 helper functions + 1 wiring line)
- Added `check_overload_docstrings` config toggle to `PresenceConfig` with full TOML parsing support
- 12 tests covering bare name, attribute access, async, class methods, config toggle, field verification, mixed/multiple scenarios
- Rule reference page with ruff D418 equivalence note, tabbed Violation/Fix example, suppression guidance
- Updated presence check page (rule count 1→2, rules table, config table)
- Updated configuration reference with new key
- Updated `docs/rules.yml` rule count comment (20→22) and added rule entry
- Updated `_EXPECTED_RULE_COUNT` in test infrastructure (21→22)
- Updated module and function docstrings to satisfy freshness stale-body checks
- All quality gates pass: ruff, ty, pytest (1424), docvet (zero findings), mkdocs build --strict

### Change Log

- 2026-03-08: Implemented overload-has-docstring rule — all tasks complete, all quality gates pass

### File List

- `src/docvet/config.py` — added `check_overload_docstrings` field, valid key, format entry, updated docstrings
- `src/docvet/checks/presence.py` — added `_has_overload_decorator()`, `_check_overload_docstrings()`, wired into `check_presence()`, updated docstrings
- `tests/unit/checks/test_overload_docstring.py` — new: 12 tests for overload-has-docstring rule
- `tests/unit/test_docs_infrastructure.py` — updated `_EXPECTED_RULE_COUNT` from 21 to 22
- `docs/rules.yml` — added `overload-has-docstring` rule entry, updated header comment
- `docs/site/rules/overload-has-docstring.md` — new: rule reference page
- `docs/site/checks/presence.md` — updated rule count, rules table, config table
- `docs/site/configuration.md` — added `check-overload-docstrings` to presence options table
- `mkdocs.yml` — added nav entry for overload-has-docstring rule page
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story status updated
- `_bmad-output/implementation-artifacts/34-4-overload-has-docstring-check.md` — story file updated

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
