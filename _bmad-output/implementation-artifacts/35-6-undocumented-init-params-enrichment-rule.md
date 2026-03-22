# Story 35.6: `undocumented-init-params` Enrichment Rule

Status: done
Branch: `feat/enrichment-35-6-undocumented-init-params`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag classes whose `__init__` takes parameters but neither the class docstring nor `__init__` has an Args section,
so that constructor parameters are documented somewhere for users.

## Acceptance Criteria

1. **Given** a class with `__init__(self, name, timeout)` and neither the class docstring nor `__init__` docstring has an `Args:` or `Parameters:` section, **When** enrichment runs, **Then** an `undocumented-init-params` finding is emitted naming the class and listing the undocumented parameters.

2. **Given** a class with `__init__(self, name)` and the class docstring has an `Args:` section, **When** enrichment runs, **Then** no finding is produced (class docstring satisfies the check — FR24).

3. **Given** a class with `__init__(self, name)` and `__init__` itself has a docstring with an `Args:` section, **When** enrichment runs, **Then** no finding is produced (`__init__` docstring satisfies the check — FR24).

4. **Given** a class with `__init__(self)` (no parameters beyond self), **When** enrichment runs, **Then** no finding is produced (no parameters to document).

5. **Given** a class with no `__init__` method defined, **When** enrichment runs, **Then** no finding is produced (inherits default `__init__`).

6. **Given** a class with `__init__(self, *args, **kwargs)` only (pass-through), **When** enrichment runs and default config excludes `*args`/`**kwargs`, **Then** no finding is produced (all params excluded).

7. **Given** `require-init-params = false` in config (default), **When** enrichment runs, **Then** the rule is skipped entirely.

8. **Given** the `undocumented-init-params` rule is implemented and tested, **When** the story is marked done, **Then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern.

9. **Given** Sphinx-style docstrings and a class with `__init__` params and `:param name:` directives in the class or `__init__` docstring, **When** enrichment runs, **Then** no finding is produced (`:param` maps to `"Args"` via `_SPHINX_SECTION_MAP`).

## Tasks / Subtasks

- [x] Task 1: Add `require_init_params` config field (AC: 7)
  - [x] 1.1 Add `require_init_params: bool = False` field to `EnrichmentConfig` dataclass in `config.py`
  - [x] 1.2 Add `"require-init-params"` to `_VALID_ENRICHMENT_KEYS` frozenset
  - [x] 1.3 Add docstring entry for the new field in `EnrichmentConfig`
- [x] Task 2: Implement `_check_undocumented_init_params` check function (AC: 1, 2, 3, 4, 5, 6)
  - [x] 2.1 Add `_check_undocumented_init_params(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 2.2 Guard: skip if `symbol.kind` is not `"class"` (all class types — dataclass, protocol, enum, namedtuple, typeddict — use `kind="class"` in `ast_utils.py`)
  - [x] 2.3 Guard: skip if no `__init__` found via `_find_init_method()`
  - [x] 2.4 Extract `__init__` params, filter `self`, and optionally filter `*args`/`**kwargs` via `config.exclude_args_kwargs`
  - [x] 2.5 Guard: skip if no documentable params remain after filtering
  - [x] 2.6 Check class docstring sections for `"Args"` or `"Parameters"`
  - [x] 2.7 Check `__init__` docstring (via `ast.get_docstring()` + `_parse_sections()`) for `"Args"` or `"Parameters"`
  - [x] 2.8 Emit `Finding` if neither location has the section
- [x] Task 3: Wire into `_RULE_DISPATCH` table (AC: 7)
  - [x] 3.1 Add `("require_init_params", _check_undocumented_init_params)` entry to `_RULE_DISPATCH`
- [x] Task 4: Write unit tests (AC: 1-9)
  - [x] 4.1 Create `tests/unit/checks/test_undocumented_init_params.py` (dedicated file)
  - [x] 4.2 Test AC1: undocumented params → finding with all 6 Finding fields
  - [x] 4.3 Test AC2: class docstring has Args → no finding
  - [x] 4.4 Test AC3: `__init__` docstring has Args → no finding
  - [x] 4.5 Test AC4: no params beyond self → no finding
  - [x] 4.6 Test AC5: no `__init__` → no finding (plain class)
  - [x] 4.7 Test AC5 variants: `@dataclass`, `NamedTuple`, `TypedDict` without explicit `__init__` → no finding
  - [x] 4.8 Test AC6: only `*args, **kwargs` with `exclude_args_kwargs=True` → no finding
  - [x] 4.9 Test AC7: config disabled → skipped (via dispatch)
  - [x] 4.10 Test AC9: Sphinx `:param` in class docstring → no finding (maps to `"Args"`)
  - [x] 4.11 Skipped: `Parameters:` not in `_SECTION_HEADERS` — parser doesn't recognize it (separate concern)
  - [x] 4.12 Test: cross-rule non-interference with `require_param_agreement` and `require_attributes`
  - [x] 4.13 Test: non-class symbol (function) → no finding (kind guard)
  - [x] 4.14 Test: mixed regular + `*args` params with `exclude_args_kwargs=True` → finding for regular params only
  - [x] 4.15 Test: `__init__` docstring has `:param` (Sphinx) → no finding
- [x] Task 5: Documentation (AC: 8)
  - [x] 5.1 Create `docs/site/rules/undocumented-init-params.md` rule page
  - [x] 5.2 Add entry to `docs/rules.yml`
  - [x] 5.3 Add nav entry to `mkdocs.yml` under Enrichment rules
  - [x] 5.4 Update `docs/site/checks/enrichment.md` rule count (19 → 20)
  - [x] 5.5 Add `require-init-params` row to `docs/site/configuration.md`
  - [x] 5.6 Update `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` (30 → 31)
- [x] Task 6: Quality gates
  - [x] 6.1 `uv run ruff check .` — zero violations
  - [x] 6.2 `uv run ruff format --check .` — zero format issues
  - [x] 6.3 `uv run ty check` — zero type errors
  - [x] 6.4 `uv run pytest` — 1652 passed
  - [x] 6.5 `uv run docvet check --all` — zero findings

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_undocumented_init_params_emits_finding` | Pass |
| 2 | `test_class_docstring_has_args_no_finding` | Pass |
| 3 | `test_init_docstring_has_args_no_finding` | Pass |
| 4 | `test_no_params_beyond_self_no_finding` | Pass |
| 5 | `test_no_init_method_no_finding`, `test_structural_types_no_init_no_finding[dataclass/namedtuple/typeddict]` | Pass |
| 6 | `test_only_args_kwargs_excluded_no_finding`, `test_args_kwargs_not_excluded_emits_finding` | Pass |
| 7 | `test_config_default_false_skips_via_dispatch` | Pass |
| 8 | `test_docs_infrastructure.py` tests (rule count, nav, rules.yml) | Pass |
| 9 | `test_sphinx_param_in_class_docstring_no_finding`, `test_sphinx_param_in_init_docstring_no_finding` | Pass |

## Dev Notes

### Architecture & Implementation Guide

**Check function signature** (NFR3 — uniform 5-parameter dispatch):
```python
def _check_undocumented_init_params(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
```

**Symbol kind guard**: Only run on class symbols. All class types (dataclass, protocol, enum, namedtuple, typeddict) use `kind="class"` in `ast_utils.py` — there are no specialized kind values. Guard with `if symbol.kind != "class": return None`. Unlike `_check_missing_attributes` (which also handles modules), this rule only applies to classes.

**Existing helpers to reuse** (DO NOT reinvent):
- `_find_init_method(node)` at line 1084 — finds `__init__` in class body, returns the AST node
- `_parse_sections(docstring, style=style)` — parses section headers from docstring text
- `_is_property(node)` — not needed here but template for guard patterns
- `ast.get_docstring(init_node)` — stdlib, gets `__init__`'s docstring if present
- `config.exclude_args_kwargs` — already exists, reuse for `*args`/`**kwargs` filtering

**Class node lookup**: Use `node_index.get(symbol.start_line)` to get the `ast.ClassDef` node, then pass to `_find_init_method()`.

**Parameter extraction from `__init__`**: Use `init_node.args` (an `ast.arguments` object):
- `init_node.args.args[1:]` — positional params (skip index 0 = `self`, always present in `__init__`)
- `init_node.args.posonlyargs` — positional-only params
- `init_node.args.kwonlyargs` — keyword-only params
- `init_node.args.vararg` — `*args` (filter if `config.exclude_args_kwargs`)
- `init_node.args.kwarg` — `**kwargs` (filter if `config.exclude_args_kwargs`)

**Section check logic** (FR24 — either location satisfies):
1. Check `sections` parameter (already parsed from class docstring) for `"Args" in sections or "Parameters" in sections`
2. If not found, get `__init__` docstring via `ast.get_docstring(init_node)`
3. If `__init__` has docstring, parse its sections with `_parse_sections(docstring, style=_active_style)`
4. Check for `"Args" in init_sections or "Parameters" in init_sections`
5. If neither → emit finding

**CRITICAL**: `_parse_sections()` does NOT normalize "Parameters" to "Args". Google-colon `Args:` returns `"Args"`. NumPy-underline `Parameters\n----------` returns `"Parameters"`. Sphinx `:param` maps to `"Args"`. Always check both: `"Args" in sections or "Parameters" in sections`.

**Finding construction**:
```python
return Finding(
    file=file_path,
    line=symbol.start_line,
    symbol=symbol.name,
    rule="undocumented-init-params",
    message=f"class '{symbol.name}' __init__ has parameters ({param_list}) but no Args section in class or __init__ docstring",
    category="required",
)
```

**Config default**: `False` (opt-in, per NFR10). This means the rule is gated by `getattr(config, "require_init_params")` in the dispatch loop. Only fires when user explicitly enables `require-init-params = true`.

**Interaction Risk:** Complementary with two existing rules — verify with unfiltered findings tests:
- `missing-attributes` (checks `Attributes:` section) — different section, different concern. Both can fire on the same class (one for missing Attributes, one for missing Args). Intentional — not duplication.
- `missing-param-in-docstring` (checks individual params in Args section) — different scope. `undocumented-init-params` fires when the ENTIRE Args section is missing. `missing-param-in-docstring` fires when Args exists but individual params are missing. They never overlap: if Args exists, `undocumented-init-params` doesn't fire; if Args doesn't exist, `missing-param-in-docstring` doesn't fire (no section to check against).

### Key Design Decisions (Party-Mode Consensus 2026-03-22)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Category: `required` | Severity is orthogonal to default. Undocumented constructor params are a completeness gap, same class as `missing-raises`. |
| 2 | Default: `False` (opt-in) | Every major linter defaults new rules to disabled. Adoption safety (NFR10). |
| 3 | `Attributes:` does NOT satisfy check | Rule checks for `Args`/`Parameters` only. `Attributes:` documents object state, not constructor interface. pydoclint also separates these (DOC1xx vs DOC6xx). Dataclasses without explicit `__init__` are naturally skipped anyway (`_find_init_method()` returns `None`). |
| 4 | Structural types naturally skipped | `@dataclass`, `NamedTuple`, `TypedDict` auto-generate `__init__` at runtime — it's NOT in the source AST. `_find_init_method()` returns `None`, rule skips. Only fires on explicit `__init__` definitions. |
| 5 | Section check: trust the parser | Check `"Args" in sections or "Parameters" in sections`. `_parse_sections()` does NOT normalize "Parameters" to "Args" — they are distinct return values. Google returns `"Args"`, NumPy may return `"Parameters"` (underline format), Sphinx maps `:param` to `"Args"` via `_SPHINX_SECTION_MAP`. No ad-hoc regex in the check function. |
| 6 | Sphinx: no raw string check needed | `:param` already maps to `"Args"` via `_SPHINX_SECTION_MAP`. Just check `"Args" in sections` — works for both Google and Sphinx. |
| 7 | One finding per class, param names listed | Section-level check (no Args section at all), not per-param. Complementary with `missing-param-in-docstring` which handles per-param granularity when Args section exists. |
| 8 | `self` filtering only, no `cls` | `__init__` always takes `self`, never `cls`. `cls` appears in `__new__`, `__init_subclass__`, `@classmethod` — not this rule's scope. Skip `args.args[0]` (always `self`). |
| 9 | Config reuse: `exclude_args_kwargs` | Shared with `require_param_agreement` (Story 35.1). Reuse identically for consistent `*args`/`**kwargs` behavior. |
| 10 | `since` version: `"1.14.0"` | Matches other Epic 35 stories (35-4, 35-5). |

### Competitive Landscape

No existing tool handles this cleanly for Google-style docstrings:
- **pydoclint**: Closest — DOC101/DOC103 check params, but enforces one-location-only via `allow-init-docstring` toggle. Complex config.
- **darglint**: Archived. Never supported class-docstring params (Issue #25). Known gap.
- **ruff DOC rules**: Preview/unstable. Inherits pydoclint behavior.
- **pylint docparams**: Opt-in, buggy. `__init__` docstring path broken (Issue #6692).
- **docvet opportunity**: Simple, opinionated rule accepting EITHER location. Fills the darglint vacuum without pydoclint's complexity.

### Project Structure Notes

- Alignment: New check function goes in `src/docvet/checks/enrichment.py` near existing class-level checks (`_check_missing_attributes` at line 1193)
- Test file: `tests/unit/checks/test_undocumented_init_params.py` (dedicated file per P3 test-review recommendation)
- Rule page: `docs/site/rules/undocumented-init-params.md` (follows existing rule page pattern)
- No new modules or packages needed

### References

- [Source: _bmad-output/planning-artifacts/epics-35.md — Story 35.6 ACs and FR23/FR24]
- [Source: src/docvet/checks/enrichment.py:1084 — `_find_init_method()` helper]
- [Source: src/docvet/checks/enrichment.py:1193 — `_check_missing_attributes()` for class-level check pattern]
- [Source: src/docvet/checks/enrichment.py:2684-2704 — `_RULE_DISPATCH` table]
- [Source: src/docvet/config.py:92-173 — `EnrichmentConfig` dataclass]
- [Source: src/docvet/config.py:302-321 — `_VALID_ENRICHMENT_KEYS` set]
- [Source: src/docvet/config.py:557-571 — `_parse_enrichment()` function]
- [Source: tests/unit/checks/test_missing_return_type.py — template for dedicated test file]
- [Source: docs/rules.yml — rule catalog format]
- [Source: docs/site/rules/missing-return-type.md — rule page template]
- [Source: 35-5 story file — previous story learnings]

### Previous Story Intelligence (from 35-5: missing-return-type)

- **Zero-debug pattern**: Careful task breakdown following 35-4 patterns achieved zero-debug implementation
- **Interaction risk verification**: Always test unfiltered findings to detect cross-rule conflicts
- **Code review caught docs drift**: enrichment.md intro rule count was wrong, config table missing rows. Check counts before claiming completion
- **mkdocs.yml nav**: Verify nav entry placement matches alphabetical/logical ordering
- **Config page**: When adding a new config key, also check if any PRIOR stories' config keys are missing from `docs/site/configuration.md`
- **`_EXPECTED_RULE_COUNT`**: Must be incremented (30 → 31) in `tests/unit/test_docs_infrastructure.py`

### Git Intelligence (recent Epic 35 commits)

Recent commits show consistent pattern:
1. Single PR per story, squash-merged to main
2. Files touched: `enrichment.py`, `config.py`, `test_docs_infrastructure.py`, `rules.yml`, `enrichment.md`, `configuration.md`, `mkdocs.yml`, plus new test file and rule page
3. Branch naming: `feat/enrichment-35-N-description`
4. PR title: `feat(enrichment): add <rule-name> rule`

### Test Maturity Piggyback

**P3 (Low) — Continue splitting test_enrichment.py by rule** (from test-review.md, 2026-03-21)

This story naturally contributes to P3 by creating a dedicated `test_undocumented_init_params.py` file rather than adding tests to the monolithic `test_enrichment.py`. Current extraction rate: 4/14 enrichment rules with dedicated files → this story makes it 5/15.

### Documentation Impact

- Pages: `docs/site/rules/undocumented-init-params.md` (new), `docs/rules.yml`, `docs/site/checks/enrichment.md`, `docs/site/configuration.md`, `mkdocs.yml`
- Nature of update: Create rule reference page; add rule entry to catalog; update enrichment rule count (19 → 20); add `require-init-params` config row; add nav entry

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [ ] `uv run ruff check .` — zero lint violations
- [ ] `uv run ruff format --check .` — zero format issues
- [ ] `uv run ty check` — zero type errors
- [ ] `uv run pytest` — all tests pass, no regressions
- [ ] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Zero-debug implementation. All 19 tests passed on first run.

### Completion Notes List

- Implemented `_check_undocumented_init_params` check function with 5 guard clauses
- Config field `require_init_params: bool = False` (opt-in, party-mode consensus)
- Category `required` (severity orthogonal to default — party-mode consensus)
- Reused `_find_init_method()`, `_parse_sections()`, `config.exclude_args_kwargs`
- 19 tests in dedicated file covering all 9 ACs + edge cases + cross-rule + structural types
- Structural types (dataclass, NamedTuple, TypedDict) naturally skipped — `_find_init_method()` returns None for auto-generated `__init__`
- Sphinx support via `_SPHINX_SECTION_MAP` (`:param` → `"Args"`) — no ad-hoc matching
- Updated module docstrings to clear freshness stale-body findings
- Task 4.11 (NumPy `Parameters:` test) skipped — `Parameters` not in `_SECTION_HEADERS`, so parser never returns it. Separate parser concern, not this rule's scope.

### Change Log

- 2026-03-22: Implemented undocumented-init-params rule, 19 tests, rule page, docs updates
- 2026-03-22: Code review fixes — positional-only params bug (H1), test assertions (M1+M2), config key ordering (L1)

### File List

- `src/docvet/config.py` — Added `require_init_params` field, `_VALID_ENRICHMENT_KEYS` entry, docstring
- `src/docvet/checks/enrichment.py` — Added `_check_undocumented_init_params()`, dispatch entry, module docstring update
- `tests/unit/checks/test_undocumented_init_params.py` — New: 19 tests
- `tests/unit/test_docs_infrastructure.py` — Updated `_EXPECTED_RULE_COUNT` (30 → 31)
- `docs/site/rules/undocumented-init-params.md` — New: rule reference page
- `docs/rules.yml` — Added undocumented-init-params entry
- `docs/site/checks/enrichment.md` — Updated rule count (19 → 20)
- `docs/site/configuration.md` — Added `require-init-params` config row
- `mkdocs.yml` — Added nav entry

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Adversarial code review (AI) — 2026-03-22

### Outcome

Changes Requested → Fixed

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Positional-only params bug: `self` included in param list + regular params lost after `/` due to `args[1:]` assumption. Confirmed with AST verification. | Fixed — branch-free `(posonlyargs + args)[1:]` approach per party-mode consensus. |
| M1 | MEDIUM | `test_posonly_params_emits_finding` missing `assert "self" not in finding.message` — masked H1. | Fixed — negative assertion added. |
| M2 | MEDIUM | Missing test for mixed posonly + regular: `def __init__(self, a, /, b)` — the worst H1 variant where `b` is silently lost. | Fixed — `test_mixed_posonly_and_regular_params` added. |
| L1 | LOW | `_VALID_ENRICHMENT_KEYS` non-alphabetical: `require-init-params` placed after `require-receives`. | Fixed — reordered alphabetically. |
| L2 | LOW | Quality Gates section checkboxes unchecked vs Tasks 6.1-6.5 checked. | Skipped — QG section is review-time checklist. |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass (1653 passed, ruff clean, format clean)
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
