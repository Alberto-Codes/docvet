# Story 35.2: Missing Deprecation Enrichment Rule

Status: review
Branch: `feat/enrichment-35-2-missing-deprecation`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag functions with deprecation patterns in code but no deprecation notice in their docstring,
so that users reading documentation know to migrate away from deprecated APIs.

## Acceptance Criteria

1. **Given** a function body containing `warnings.warn(..., DeprecationWarning)`, **when** enrichment runs and the docstring does not contain the word "deprecated" (case-insensitive), **then** a `missing-deprecation` finding is emitted.

2. **Given** a function body containing `warnings.warn(..., PendingDeprecationWarning)` or `warnings.warn(..., FutureWarning)`, **when** enrichment runs and the docstring has no deprecation notice, **then** a `missing-deprecation` finding is emitted (all three warning categories are covered).

3. **Given** a function decorated with `@deprecated` (from `typing_extensions` or `warnings`), **when** enrichment runs and the docstring has no deprecation notice, **then** a `missing-deprecation` finding is emitted.

4. **Given** a function with a deprecation pattern in code AND the word "deprecated" anywhere in the docstring, **when** enrichment runs, **then** no finding is produced (intentionally loose matching avoids false positives).

5. **Given** a function with no deprecation patterns in code, **when** enrichment runs, **then** no `missing-deprecation` finding is produced.

6. **Given** a deprecation `warnings.warn(...)` inside a nested function, **when** enrichment runs on the outer function, **then** no finding is produced for the outer function (scope-aware AST walk).

7. **Given** `require-deprecation-notice = false` in config, **when** enrichment runs, **then** the rule is skipped entirely.

8. **Given** the `missing-deprecation` rule is implemented and tested, **when** the story is marked done, **then** a rule reference page exists in `docs/rules/` and is registered in `docs/rules.yml` following the existing pattern.

## Tasks / Subtasks

- [x] Task 1: Add `require_deprecation_notice` to `EnrichmentConfig` (AC: 7)
  - [x] 1.1 Add `require_deprecation_notice: bool = True` field to `EnrichmentConfig` dataclass
  - [x] 1.2 Add `"require-deprecation-notice"` to `_VALID_ENRICHMENT_KEYS` frozenset
  - [x] 1.3 Add `("require_deprecation_notice", "require-deprecation-notice")` to `format_config_toml` enrichment field list
  - [x] 1.4 Update `EnrichmentConfig` docstring to document the new field
- [x] Task 2: Implement `_is_deprecation_warn_call()` helper (AC: 1, 2)
  - [x] 2.1 Create helper that checks if a `warnings.warn()` call has a deprecation category argument
  - [x] 2.2 Match `DeprecationWarning`, `PendingDeprecationWarning`, `FutureWarning` as second positional arg or `category` keyword arg
  - [x] 2.3 Handle both `ast.Name` (bare) and `ast.Attribute` (qualified) forms for the category
  - [x] 2.4 Note: `warnings.warn("msg")` with no explicit category defaults to `UserWarning` — do NOT match these
- [x] Task 2b: Implement `_has_deprecated_decorator()` helper (AC: 3)
  - [x] 2b.1 Create dedicated helper — do NOT modify `_has_decorator` (13+ callers, bare-decorator contract)
  - [x] 2b.2 Check `ast.Call` wrapper: `@deprecated("reason")` produces `Call(func=Name(id="deprecated"))`
  - [x] 2b.3 Check qualified `ast.Call`: `@typing_extensions.deprecated("reason")` produces `Call(func=Attribute(attr="deprecated"))`
  - [x] 2b.4 Do NOT check bare `ast.Name`/`ast.Attribute` — PEP 702 requires a mandatory `msg` argument, so real-world `@deprecated` is always `ast.Call`
- [x] Task 3: Implement `_check_missing_deprecation()` (AC: 1-6)
  - [x] 3.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 3.2 Guard: return None if `symbol.kind not in ("function", "method")`
  - [x] 3.3 Guard: return None if node not found in `node_index`
  - [x] 3.4 Check docstring for "deprecated" (case-insensitive) — if found, return None early
  - [x] 3.5 Check `@deprecated` decorator via `_has_deprecated_decorator(node)` (NOT `_has_decorator` — see party-mode consensus)
  - [x] 3.6 Scope-aware AST walk for `warnings.warn()` calls with deprecation categories
  - [x] 3.7 Emit finding if decorator or warn call found without docstring notice
- [x] Task 4: Wire into `_RULE_DISPATCH` (AC: 7)
  - [x] 4.1 Add single entry: `("require_deprecation_notice", _check_missing_deprecation)`
  - [x] 4.2 Do NOT add to `_SPHINX_AUTO_DISABLE_RULES` — deprecation notice is body text, works in all styles
- [x] Task 5: Write tests in `tests/unit/checks/test_missing_deprecation.py` (AC: 1-8)
  - [x] 5.1 Test `warnings.warn(..., DeprecationWarning)` without docstring notice → finding
  - [x] 5.2 Test `PendingDeprecationWarning` and `FutureWarning` → finding (parametrize)
  - [x] 5.3 Test `@deprecated("reason")` decorator → finding (`ast.Call` form — the only real-world form per PEP 702)
  - [x] 5.4 Test "deprecated" in docstring → no finding (case-insensitive)
  - [x] 5.5 Test no deprecation patterns → no finding
  - [x] 5.6 Test nested function with warn call → no finding for outer (scope-aware)
  - [x] 5.7 Test config disable → no finding
  - [x] 5.8 Test class/module symbol → no finding (guard)
  - [x] 5.9 Cross-rule interaction: function with `warnings.warn(DeprecationWarning)` and no Warns section → both `missing-warns` AND `missing-deprecation` emit (unfiltered findings check)
  - [x] 5.10 Test `@overload` symbol → no finding (enrichment skips overloads)
  - [x] 5.11 Test qualified form `warnings.warn("msg", category=DeprecationWarning)` keyword arg
  - [x] 5.12 Test bare `warn("msg", DeprecationWarning)` after `from warnings import warn`
  - [x] 5.13 Test `@typing_extensions.deprecated("reason")` qualified form → finding
  - [x] 5.14 Test `@warnings.deprecated("reason")` qualified form → finding
  - [x] 5.15 Test `warnings.warn("msg")` with NO explicit category → no finding (defaults to `UserWarning`)
  - [x] 5.16 Assert `finding.symbol`, `finding.rule`, `finding.message`, `finding.category` on every test
- [x] Task 6: Create rule reference page (AC: 8)
  - [x] 6.1 Create `docs/site/rules/missing-deprecation.md`
  - [x] 6.2 Register in `docs/rules.yml` with id `missing-deprecation`
- [x] Task 7: Update documentation
  - [x] 7.1 Add `require-deprecation-notice` to `docs/site/configuration.md` enrichment options table
- [x] Task 8: Run quality gates and verify dogfooding
  - [x] 8.1 `uv run ruff check .` — zero violations
  - [x] 8.2 `uv run ruff format --check .` — zero issues
  - [x] 8.3 `uv run ty check` — zero errors
  - [x] 8.4 `uv run pytest` — 1503 passed
  - [x] 8.5 `uv run docvet check --all` — zero required findings (2 recommended stale-body on modified modules, expected)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_warn_deprecation_warning_emits_finding` | Pass |
| 2 | `test_other_deprecation_categories[PendingDeprecationWarning]`, `test_other_deprecation_categories[FutureWarning]` | Pass |
| 3 | `test_deprecated_decorator_emits_finding`, `test_typing_extensions_deprecated_emits_finding`, `test_warnings_deprecated_emits_finding` | Pass |
| 4 | `test_deprecated_in_docstring_no_finding` (4 parametrized variants) | Pass |
| 5 | `test_no_deprecation_patterns_no_finding` | Pass |
| 6 | `test_nested_function_scope_isolation` | Pass |
| 7 | `test_config_disable_no_finding` | Pass |
| 8 | Rule page created: `missing-deprecation.md`, registered in `rules.yml` | Done |

## Dev Notes

- **Interaction Risk:** This story adds 1 rule (`missing-deprecation`) to the enrichment module which already has 13 entries in `_RULE_DISPATCH`. Key interaction: a function with `warnings.warn("msg", DeprecationWarning)` and no `Warns:` section will trigger BOTH `missing-warns` (from existing rule) and `missing-deprecation` (new rule). This is correct — they detect different concerns (Warns section vs deprecation notice). Verify with unfiltered findings test (Task 5.9).

### Architecture & Implementation Patterns

**Uniform check signature** — `_check_missing_deprecation` must follow:
```python
def _check_missing_deprecation(symbol, sections, node_index, config, file_path) -> Finding | None
```

**Config gating in orchestrator, NOT in check function.** The orchestrator checks `getattr(config, "require_deprecation_notice")` before dispatching. The check function never inspects config toggles.

**`_RULE_DISPATCH` wiring** — single entry:
```python
("require_deprecation_notice", _check_missing_deprecation),
```

**Closest existing pattern: `_check_missing_warns`** (enrichment.py:763). The deprecation rule uses the same scope-aware AST walk pattern but with three key differences:
1. Instead of matching any `warnings.warn()` call, it matches only calls with an explicit deprecation category argument (`DeprecationWarning`, `PendingDeprecationWarning`, `FutureWarning`). Note: `warnings.warn("msg")` with no explicit category defaults to `UserWarning`, NOT `DeprecationWarning` — do not match these.
2. It also checks for the `@deprecated` decorator via a NEW `_has_deprecated_decorator` helper (not `_has_decorator` — see below)
3. The docstring check is loose: word "deprecated" anywhere (case-insensitive), not a specific section

**Deprecation pattern detection — AST details:**

For `warnings.warn("msg", DeprecationWarning)`:
- `node.args[1]` is `ast.Name(id="DeprecationWarning")` or `ast.Attribute(attr="DeprecationWarning")`

For `warnings.warn("msg", category=DeprecationWarning)`:
- Look in `node.keywords` for `keyword.arg == "category"` with same value patterns

Target category names: `{"DeprecationWarning", "PendingDeprecationWarning", "FutureWarning"}`

Create `_is_deprecation_warn_call(node: ast.Call) -> bool` helper:
1. First check `_is_warn_call(node)` to confirm it's a warn call at all
2. Then check the second positional arg OR `category` keyword for a deprecation class name
3. Match both `ast.Name(id=name)` and `ast.Attribute(attr=name)` forms

**`@deprecated` decorator detection (party-mode consensus 2026-03-21):**

**Do NOT use `_has_decorator(node, "deprecated")`.** PEP 702's `@deprecated` requires a mandatory `msg` argument — `@deprecated("Use new_func instead")`. This means the decorator is ALWAYS an `ast.Call` node in real-world usage, never bare `ast.Name`/`ast.Attribute`. The existing `_has_decorator` only checks `ast.Name`/`ast.Attribute` — it does NOT unwrap `ast.Call`. It would return `False` for every real-world `@deprecated` usage.

**Do NOT modify `_has_decorator`.** It has 13+ callers (`_is_property`, `_should_skip_returns_check` for `abstractmethod`/`overload`) that all use bare decorators. Changing its contract risks regressions.

Create a dedicated `_has_deprecated_decorator(node)` helper:
```python
_DEPRECATED_NAMES: frozenset[str] = frozenset({"deprecated"})

def _has_deprecated_decorator(node: _NodeT) -> bool:
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name) and dec.func.id in _DEPRECATED_NAMES:
                return True
            if isinstance(dec.func, ast.Attribute) and dec.func.attr in _DEPRECATED_NAMES:
                return True
    return False
```

This handles:
- `@deprecated("msg")` → `Call(func=Name(id="deprecated"))`
- `@typing_extensions.deprecated("msg")` → `Call(func=Attribute(attr="deprecated"))`
- `@warnings.deprecated("msg")` → `Call(func=Attribute(attr="deprecated"))`

Check decorator BEFORE the AST walk — if decorator found and no "deprecated" in docstring, emit immediately.

**Docstring check:**
```python
if "deprecated" in symbol.docstring.lower():
    return None
```
This is intentionally loose — matching the word anywhere avoids false positives from different deprecation notice formats (Google `Deprecated:` section, inline mentions, `.. deprecated::` Sphinx directive).

**Scope-aware walk pattern** (copy from `_check_missing_warns`):
```python
stack = list(ast.iter_child_nodes(node))
while stack:
    child = stack.pop()
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        continue  # Stop at nested scope boundaries
    if isinstance(child, ast.Call) and _is_deprecation_warn_call(child):
        has_deprecation = True
        break
    stack.extend(ast.iter_child_nodes(child))
```

**Domain pitfalls (from Epic 34 retro + party-mode 2026-03-21):**
- `_has_decorator` does NOT handle `ast.Call` decorators — use `_has_deprecated_decorator` for `@deprecated("reason")`
- `warnings.warn("msg")` defaults to `UserWarning`, not `DeprecationWarning` — only match explicit deprecation categories
- Test helpers must select correct symbol type — verify `kind` and `name` match expectations
- Test unfiltered findings when adding rules to detect cross-rule conflicts
- Guard on `symbol.docstring is not None` for ty type narrowing (learned from 35.1)

### File Locations

| What | Path |
|------|------|
| Enrichment module | `src/docvet/checks/enrichment.py` |
| Config module | `src/docvet/config.py` |
| New test file | `tests/unit/checks/test_missing_deprecation.py` |
| Rule page | `docs/site/rules/missing-deprecation.md` |
| Rules registry | `docs/rules.yml` |
| Configuration docs | `docs/site/configuration.md` |
| Docs macros | `docs/main.py` |

### Existing Helpers to Reuse

- `_is_warn_call(node)` — checks if a call is `warnings.warn()` (use as foundation for `_is_deprecation_warn_call`)
- `_has_decorator(node, name)` — checks for bare/qualified decorators. **Do NOT use for `@deprecated`** — it doesn't handle `ast.Call` wrappers (party-mode consensus)
- `_build_node_index(tree)` — line-to-AST-node lookup (already built by orchestrator)
- `get_documented_symbols(tree)` — returns `list[Symbol]` with docstrings (from `ast_utils`)
- Scope-aware walk pattern from `_check_missing_warns` (copy the stack-based iteration)

### Config Field Additions

In `config.py`, `EnrichmentConfig` needs:
- `require_deprecation_notice: bool = True` — gates the rule

In `_VALID_ENRICHMENT_KEYS`, add:
- `"require-deprecation-notice"`

In `format_config_toml`, add to enrichment field list:
- `("require_deprecation_notice", "require-deprecation-notice")`

In `format_config_json`, the field is auto-included via dataclass iteration (no manual change needed — verify).

### Sphinx Style Compatibility

Deprecation notice is checked in the docstring body (word "deprecated" case-insensitive), not in a section header. This works identically for Google and Sphinx styles — no Sphinx-specific handling needed. Do NOT add to `_SPHINX_AUTO_DISABLE_RULES`.

### Test Strategy

Use `@pytest.mark.parametrize` for multiple deprecation pattern variants (Task 5.1-5.3). Follow the dedicated test file pattern from `test_prefer_fenced_code_blocks.py` and `test_param_agreement.py` — create `_make_symbol_and_index` helper for boilerplate.

### Test Maturity Piggyback

From test-review.md (P2): Near-zero `@pytest.mark.parametrize` usage (7 usages in 1,210 tests). **Use `@pytest.mark.parametrize`** for deprecation pattern variants — this story is ideal because multiple warning categories and decorator forms share identical assertion logic. Story 35.1 already adopted this; continue the pattern.

### Documentation Impact

- Pages: `docs/site/rules/missing-deprecation.md`, `docs/site/configuration.md`
- Nature of update: Create 1 new rule reference page following existing macros scaffold pattern; add `require-deprecation-notice` config key to enrichment options table in configuration reference

### Project Structure Notes

- Alignment with unified project structure: new test file in `tests/unit/checks/`, rule page in `docs/site/rules/`
- No conflicts or variances detected
- `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` must be updated from 24 to 25

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 35.2] — FR12-FR13, NFR3, NFR4
- [Source: src/docvet/checks/enrichment.py:738-826] — `_is_warn_call()`, `_check_missing_warns()` (closest pattern)
- [Source: src/docvet/checks/enrichment.py:426-444] — `_has_decorator()` helper
- [Source: src/docvet/checks/enrichment.py:1960-1974] — `_RULE_DISPATCH` table
- [Source: src/docvet/config.py:92-160] — `EnrichmentConfig` dataclass
- [Source: src/docvet/config.py:288-303] — `_VALID_ENRICHMENT_KEYS`
- [Source: src/docvet/config.py:965-986] — `format_config_toml` enrichment field list
- [Source: _bmad-output/implementation-artifacts/35-1-docstring-parameter-agreement-checks.md] — Previous story patterns, domain pitfalls
- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Epic 35] — Implementation order note
- [Source: PEP 702](https://peps.python.org/pep-0702/) — `@deprecated` requires mandatory `msg` arg, always `ast.Call` in AST
- [Source: Python 3.12 warnings.warn docs](https://docs.python.org/3.12/library/warnings.html) — default category is `UserWarning`, not `DeprecationWarning`
- [Source: Party-mode consensus 2026-03-21] — 3 decisions: `_has_deprecated_decorator` helper (not `_has_decorator`), `ast.Call` only, `UserWarning` default confirmed

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1505 passed, no regressions
- [x] `uv run docvet check --all` — zero required findings (2 recommended stale-body on modified modules, expected)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- `_is_deprecation_warn_call` checks second positional arg or `category` keyword for `DeprecationWarning`/`PendingDeprecationWarning`/`FutureWarning`
- `_has_deprecated_decorator` handles only `ast.Call` form per PEP 702 party-mode consensus — does NOT modify `_has_decorator`
- `_check_missing_deprecation` follows exact pattern of `_check_missing_warns` with scope-aware walk
- Loose docstring check: "deprecated" anywhere case-insensitive
- 32 tests covering all 8 ACs + cross-rule interaction + edge cases
- `@pytest.mark.parametrize` used for warning categories and docstring notice variants

### Change Log

- `src/docvet/config.py`: Added `require_deprecation_notice` field to `EnrichmentConfig`, TOML key validation, format rendering
- `src/docvet/checks/enrichment.py`: Added `_DEPRECATION_CATEGORIES`, `_category_name()`, `_is_deprecation_warn_call()`, `_has_deprecated_decorator()`, `_check_missing_deprecation()`, one `_RULE_DISPATCH` entry
- `tests/unit/checks/test_missing_deprecation.py`: Created — 34 tests covering all ACs (includes parametrized scope boundary tests)
- `tests/unit/test_docs_infrastructure.py`: Updated `_EXPECTED_RULE_COUNT` from 24 to 25
- `docs/site/rules/missing-deprecation.md`: Created rule reference page
- `docs/rules.yml`: Added 1 new rule entry (25 total), fixed header comment count
- `docs/site/configuration.md`: Added `require-deprecation-notice` to enrichment options table and full example
- `docs/site/checks/enrichment.md`: Added 4 missing rules and 3 missing config keys to enrichment check page (review fix)
- `.claude/rules/sonarqube.md`: Widened S1172 known-pattern note to cover all dispatch params (review fix)

### File List

| File | Action |
|------|--------|
| `src/docvet/config.py` | Modified |
| `src/docvet/checks/enrichment.py` | Modified |
| `tests/unit/checks/test_missing_deprecation.py` | Created |
| `tests/unit/test_docs_infrastructure.py` | Modified |
| `docs/site/rules/missing-deprecation.md` | Created |
| `docs/rules.yml` | Modified |
| `docs/site/configuration.md` | Modified |
| `docs/site/checks/enrichment.md` | Modified (review fix) |
| `.claude/rules/sonarqube.md` | Modified (review fix) |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow + party-mode consensus)

### Outcome

Changes Requested → Fixed (all 7 findings addressed in review round)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | `_is_deprecation_warn_call` CC 19 (threshold 15) | Extracted `_category_name()` helper — CC dropped to ~7 (SonarQube: 0 findings) |
| M1 | MEDIUM | `rules.yml` header says "24 rules" but there are 25 | Fixed: "24" → "25" |
| M2 | MEDIUM | `docs/site/checks/enrichment.md` missing 4 rules + 3 config keys | Fixed: added all 4 rules and 3 config keys, updated count 10 → 14 |
| M3 | MEDIUM | Quality Gates section unchecked in story file | Fixed: checked after independent verification (1505 passed) |
| M4 | MEDIUM | No `AsyncFunctionDef`/`ClassDef` scope boundary tests | Fixed: parametrized 3-variant test (sync, async, class) — 34 tests now |
| L1 | LOW | Rule page example Fix tab shows Sphinx-style instead of Google-style | Fixed: changed to Google-style `Deprecated:` section |
| L2 | LOW | S1172 known-pattern note only mentions `node_index` | Fixed: widened to cover all 5 dispatch params |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
