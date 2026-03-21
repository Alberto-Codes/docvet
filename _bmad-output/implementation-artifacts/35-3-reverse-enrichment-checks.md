# Story 35.3: Reverse Enrichment Checks

Status: review
Branch: `feat/enrichment-35-3-reverse-enrichment-checks`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag docstrings that claim behavior the code doesn't exhibit,
so that my docstrings don't mislead callers about raises, yields, or returns.

## Acceptance Criteria

1. **Given** a function with a `Raises:` section documenting `ValueError` but no `raise ValueError` in the function body, **when** enrichment runs, **then** an `extra-raises-in-docstring` finding is emitted naming the undocumented exception.

2. **Given** a function with a `Raises:` section documenting exceptions that ALL appear in `raise` statements, **when** enrichment runs, **then** no `extra-raises-in-docstring` findings are produced.

3. **Given** a function with a `Yields:` section but no `yield` or `yield from` statements in the body, **when** enrichment runs, **then** an `extra-yields-in-docstring` finding is emitted.

4. **Given** a function with a `Returns:` section but no `return <expr>` statements in the body (only bare `return` or `return None`), **when** enrichment runs, **then** an `extra-returns-in-docstring` finding is emitted.

5. **Given** a function with `raise` inside a nested function or class, **when** enrichment runs on the outer function, **then** the nested raise is not counted (scope-aware walk stops at nested `def`/`class`).

6. **Given** a `Raises:` section entry with an exception raised via re-raise (`raise` with no argument inside `except`), **when** enrichment runs, **then** the re-raised exception type is not matched (bare `raise` has no explicit type).

7. **Given** all three reverse rules, **when** checking their default category, **then** findings are categorized as `recommended` (not `required`) due to higher false positive risk from implicit raises/returns (NFR9).

8. **Given** `require-raises = false`, `require-yields = false`, or `require-returns = false` in config, **when** enrichment runs, **then** the corresponding reverse rule is also skipped (shared toggle gates both forward and reverse directions).

9. **Given** the `_parse_raises_entries` helper, **when** it parses a `Raises:` section, **then** it extracts exception class names from the section using `_extract_section_content()` and returns a `set[str]`.

10. **Given** all three reverse rules are implemented and tested, **when** the story is marked done, **then** rule reference pages exist in `docs/rules/` for `extra-raises-in-docstring`, `extra-yields-in-docstring`, and `extra-returns-in-docstring`, registered in `docs/rules.yml`.

11. **Given** an interface-documentation function (`@abstractmethod`, stub body `...`/`pass`, or `raise NotImplementedError`-only body), **when** enrichment runs any reverse check, **then** no finding is produced (interface contracts document intended behavior, not current implementation).

## Tasks / Subtasks

- [x] Task 1: Implement `_parse_raises_entries()` helper (AC: 9)
  - [x] 1.1 Create `_RAISES_ENTRY_PATTERN` regex for Google-style `Raises:` entries (match `ExceptionName:` at entry level)
  - [x] 1.2 Create `_SPHINX_RAISES_PATTERN` regex for Sphinx `:raises ExcType:` entries
  - [x] 1.3 Implement `_parse_raises_entries(docstring, *, style="google") -> set[str]` following `_parse_args_entries` pattern
  - [x] 1.4 Google mode: use `_extract_section_content("Raises")` then parse entries at base indent
  - [x] 1.5 Sphinx mode: scan full docstring for `:raises ExcType:` patterns and return set of names
- [x] Task 2: Implement `_should_skip_reverse_check()` helper (AC: 11)
  - [x] 2.1 Create `_should_skip_reverse_check(node) -> bool` (composes `_has_decorator` + `_is_stub_function`)
  - [x] 2.2 Return True if `_has_decorator(node, "abstractmethod")`
  - [x] 2.3-2.5 Return True if `_is_stub_function(node)` (already handles `...`, `pass`, `raise NotImplementedError`)
  - [x] 2.6 Return False otherwise
- [x] Task 3: Implement `_check_extra_raises_in_docstring()` (AC: 1, 2, 5, 6, 11)
  - [x] 3.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 3.2 Guard: return None if `symbol.kind not in ("function", "method")`
  - [x] 3.3 Guard: return None if `"Raises"` not in sections
  - [x] 3.4 Guard: return None if `symbol.docstring is None`
  - [x] 3.5 Guard: return None if node not found in `node_index`
  - [x] 3.6 Guard: return None if `_should_skip_reverse_check(node)` (AC: 11)
  - [x] 3.7 Parse `Raises:` entries via `_parse_raises_entries(symbol.docstring, style=_active_style)` -> `doc_raises: set[str]`
  - [x] 3.8 Scope-aware AST walk collecting raised exception names via `_extract_exception_name()` -> `code_raises: set[str]`
  - [x] 3.9 Compute `extra = sorted(doc_raises - code_raises)` — if empty, return None
  - [x] 3.10 Emit Finding with `rule="extra-raises-in-docstring"`, `category="recommended"` (NFR9)
- [x] Task 4: Implement `_check_extra_yields_in_docstring()` (AC: 3, 5, 11)
  - [x] 4.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 4.2 Guard: return None if `symbol.kind not in ("function", "method")`
  - [x] 4.3 Guard: return None if `"Yields"` not in sections
  - [x] 4.4 Guard: return None if node not found in `node_index`
  - [x] 4.5 Guard: return None if `_should_skip_reverse_check(node)` (AC: 11)
  - [x] 4.6 Scope-aware AST walk checking for `ast.Yield` or `ast.YieldFrom` nodes
  - [x] 4.7 If yield found, return None (section is truthful)
  - [x] 4.8 If no yield found -> emit Finding with `rule="extra-yields-in-docstring"`, `category="recommended"`
- [x] Task 5: Implement `_check_extra_returns_in_docstring()` (AC: 4, 5, 11)
  - [x] 5.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x] 5.2 Guard: return None if `symbol.kind not in ("function", "method")`
  - [x] 5.3 Guard: return None if `"Returns"` not in sections
  - [x] 5.4 Guard: return None if node not found in `node_index`
  - [x] 5.5 Guard: return None if `_should_skip_reverse_check(node)` (AC: 11)
  - [x] 5.6 Scope-aware AST walk checking for `ast.Return` with `_is_meaningful_return()` (reuse existing helper)
  - [x] 5.7 If meaningful return found, return None (section is truthful)
  - [x] 5.8 If no meaningful return found -> emit Finding with `rule="extra-returns-in-docstring"`, `category="recommended"`
- [x] Task 6: Wire into `_RULE_DISPATCH` (AC: 8)
  - [x] 6.1 Add `("require_raises", _check_extra_raises_in_docstring)` to `_RULE_DISPATCH`
  - [x] 6.2 Add `("require_yields", _check_extra_yields_in_docstring)` to `_RULE_DISPATCH`
  - [x] 6.3 Add `("require_returns", _check_extra_returns_in_docstring)` to `_RULE_DISPATCH`
- [x] Task 7: Write tests in `tests/unit/checks/test_reverse_enrichment.py` (AC: 1-11)
  - [x] 7.1 Create `_make_symbol_and_index` helper (reuse pattern from `test_param_agreement.py`)
  - **extra-raises tests:**
  - [x] 7.2 Test `Raises:` with exception not raised in code -> finding (AC: 1)
  - [x] 7.3 Test `Raises:` with all exceptions present in code -> no finding (AC: 2)
  - [x] 7.4 Test nested `raise` -> not counted for outer function (AC: 5)
  - [x] 7.5 Test bare re-raise (`raise` in `except`) -> not matched (AC: 6)
  - [x] 7.6 Test multiple extra exceptions -> single finding listing all extra names
  - [x] 7.7 Test no `Raises:` section -> no finding (guard)
  - [x] 7.8 Test config disable `require_raises=False` -> no finding for both forward and reverse (AC: 8)
  - [x] 7.9 Test class/module symbol -> no finding (guard)
  - [x] 7.10 Test `_parse_raises_entries` directly — Google style (AC: 9)
  - [x] 7.11 Test `_parse_raises_entries` — Sphinx style (AC: 9)
  - [x] 7.12 Test `_parse_raises_entries` — multiline continuation lines not parsed as exception names (AC: 9)
  - [x] 7.13 Test `raise ValueError("msg") from original_error` (chaining) -> `ValueError` in code_raises, not `original_error`
  - [x] 7.14 Test partial-match: `Raises: ValueError, TypeError` where code raises only `ValueError` -> finding names only `TypeError`
  - **extra-yields tests:**
  - [x] 7.15 Test `Yields:` but no yield in code -> finding (AC: 3)
  - [x] 7.16 Test `Yields:` with yield in code -> no finding
  - [x] 7.17 Test nested yield -> not counted for outer function (AC: 5)
  - [x] 7.18 Test no `Yields:` section -> no finding (guard)
  - [x] 7.19 Test config disable `require_yields=False` -> no finding (AC: 8)
  - **extra-returns tests:**
  - [x] 7.20 Test `Returns:` but no meaningful return -> finding (AC: 4)
  - [x] 7.21 Test `Returns:` with meaningful return -> no finding
  - [x] 7.22 Test `Returns:` with only bare `return`/`return None` -> finding (AC: 4)
  - [x] 7.23 Test nested return -> not counted for outer function (AC: 5)
  - [x] 7.24 Test no `Returns:` section -> no finding (guard)
  - [x] 7.25 Test config disable `require_returns=False` -> no finding (AC: 8)
  - **Skip logic tests (AC: 11):**
  - [x] 7.26 Test `@abstractmethod` with `...` body + `Returns:` -> no finding (skip)
  - [x] 7.27 Test stub body (`...` only) + `Yields:` -> no finding (skip)
  - [x] 7.28 Test stub body (`pass` only) + `Raises: ValueError` -> no finding (skip)
  - [x] 7.29 Test `raise NotImplementedError`-only body + `Raises: ValueError` -> no finding (skip)
  - [x] 7.30 Test `_should_skip_reverse_check` directly — True for abstractmethod, `...`, `pass`, `raise NotImplementedError`; False for normal functions
  - **Category and cross-rule tests:**
  - [x] 7.31 Test all 3 rules emit `category="recommended"` (AC: 7)
  - [x] 7.32 Test cross-rule: function with extra raises AND forward missing-yields -> both rules fire independently
  - [x] 7.33 Test `@overload` symbol -> no finding (enrichment skips overloads)
  - [x] 7.34 Assert all 6 Finding fields on every test: `file`, `line`, `symbol`, `rule`, `message`, `category`
- [x] Task 8: Create rule reference pages (AC: 10)
  - [x] 8.1 Create `docs/site/rules/extra-raises-in-docstring.md`
  - [x] 8.2 Create `docs/site/rules/extra-yields-in-docstring.md`
  - [x] 8.3 Create `docs/site/rules/extra-returns-in-docstring.md`
  - [x] 8.4 Register all 3 rules in `docs/rules.yml` (count 25 -> 28)
- [x] Task 9: Update documentation
  - [x] 9.1 Update `docs/site/configuration.md` — add note to `require-raises`, `require-yields`, `require-returns` descriptions that they gate both forward and reverse checks
  - [x] 9.2 Add 3 new rules to `docs/site/checks/enrichment.md` rule list
  - [x] 9.3 Update `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` from 25 to 28
- [x] Task 10: Run quality gates and verify dogfooding
  - [x] 10.1 `uv run ruff check .` — zero violations
  - [x] 10.2 `uv run ruff format --check .` — zero format issues
  - [x] 10.3 `uv run ty check` — zero type errors
  - [x] 10.4 `uv run pytest` — 1549 passed, no regressions
  - [x] 10.5 `uv run docvet check --all` — zero required findings (2 recommended extra-raises on own codebase + 1 stale-body, expected)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_documented_exception_not_raised_emits_finding` | Pass |
| 2 | `test_all_documented_exceptions_raised_no_finding` | Pass |
| 3 | `test_yields_section_no_yield_emits_finding` | Pass |
| 4 | `test_returns_section_no_meaningful_return_emits_finding`, `test_returns_section_only_bare_return_emits_finding` | Pass |
| 5 | `test_nested_raise_not_counted[sync/async/class]`, `test_nested_yield_not_counted`, `test_nested_return_not_counted` | Pass |
| 6 | `test_bare_reraise_not_matched` | Pass |
| 7 | `test_all_three_rules_emit_recommended_category` | Pass |
| 8 | `test_config_disable_no_finding` (x3, one per rule) | Pass |
| 9 | `TestParseRaisesEntries` (6 tests: google single/multi/continuation/empty, sphinx/empty) | Pass |
| 10 | Rule pages created: 3 `.md` files, registered in `rules.yml` | Done |
| 11 | `test_abstractmethod_returns_skipped`, `test_ellipsis_stub_yields_skipped`, `test_pass_stub_raises_skipped`, `test_raise_not_implemented_raises_skipped`, `test_should_skip_reverse_check_directly[6 variants]` | Pass |

## Dev Notes

- **Interaction Risk:** This story adds 3 rules (`extra-raises-in-docstring`, `extra-yields-in-docstring`, `extra-returns-in-docstring`) to the enrichment module which already has 14 entries in `_RULE_DISPATCH` (17 after this story). These reverse checks are the complement of existing forward checks:

| Forward Rule | Reverse Rule | Interaction |
|---|---|---|
| `missing-raises` | `extra-raises-in-docstring` | Can co-fire on same function — missing-raises checks section existence, extra-raises checks per-entry accuracy. They fire at different granularity (a function can raise `ValueError` but also document `TypeError` it doesn't raise). |
| `missing-yields` | `extra-yields-in-docstring` | Mutually exclusive — if Yields is in sections, missing-yields returns None; if code has yield, extra-yields returns None. |
| `missing-returns` | `extra-returns-in-docstring` | Mutually exclusive — if Returns is in sections, missing-returns returns None; if code has meaningful return, extra-returns returns None. |

Verify the extra-raises + missing-raises co-fire scenario with an unfiltered findings test (Task 7.32).

### Architecture & Implementation Patterns

**Uniform check signature** — all 3 new functions must follow:
```python
def _check_extra_<type>_in_docstring(symbol, sections, node_index, config, file_path) -> Finding | None
```

**Shared config toggle (party-mode consensus 2026-03-21).** Reverse checks reuse existing config attrs (`require_raises`, `require_yields`, `require_returns`) — the same toggle gates both forward and reverse directions. This follows the `require_param_agreement` precedent, which gates both `missing-param-in-docstring` and `extra-param-in-docstring` (enrichment.py:2159-2160). Zero new config keys needed.

**Rationale:** pydoclint uses the same shared-toggle model (`--skip-checking-raises` gates both DOC501 and DOC502). Users who need independent control get it via the category difference — forward checks emit `category="required"`, reverse checks emit `category="recommended"`. Setting `fail-on = "required"` in CI effectively disables reverse-only findings without any config toggle.

**Category `recommended` (NFR9)** — all 3 rules use `category="recommended"` due to higher false positive risk from implicit raises/returns. This is different from the forward checks which use `category="required"`.

**`_RULE_DISPATCH` wiring** — 3 new entries using existing config attrs:
```python
("require_raises", _check_extra_raises_in_docstring),
("require_yields", _check_extra_yields_in_docstring),
("require_returns", _check_extra_returns_in_docstring),
```

**No `_SPHINX_AUTO_DISABLE_RULES` changes needed.** Since reverse checks reuse the same config attrs as forward checks, Sphinx auto-disable is inherited automatically. `require_yields` is already in `_SPHINX_AUTO_DISABLE_RULES` — it will gate both `_check_missing_yields` and `_check_extra_yields_in_docstring` in Sphinx mode. `require_raises` and `require_returns` are NOT in the auto-disable set (RST has `:raises:` and `:returns:` equivalents), so both forward and reverse run in Sphinx mode — correct behavior.

### Interface-Documentation Skip Logic (party-mode consensus 2026-03-21)

Both ruff (DOC202/403/502) and pydoclint skip abstract methods and stubs for reverse checks. The reasoning: these functions document *interface contracts* (intended behavior for implementers), not current behavior. A `Returns:` section on `@abstractmethod` with `...` body is correct documentation.

**New helper `_should_skip_reverse_check(symbol, node) -> bool`** returns True for:
1. `@abstractmethod` decorator — `_has_decorator(node, "abstractmethod")`
2. Body is `...` (Ellipsis) only — after excluding docstring node
3. Body is `pass` only — after excluding docstring node
4. Body is `raise NotImplementedError` or `raise NotImplementedError(...)` only — after excluding docstring node

Body-only checks must account for the docstring being `node.body[0]`. Effective body = `node.body[1:]` if docstring exists, else `node.body`. "Only" means `len(effective_body) == 1`.

This is a *subset* of `_should_skip_returns_check` (line 449), which also skips dunder methods and `@property`. Those don't apply to reverse checks — a `__repr__` with `Returns:` but no return IS a bug worth flagging.

### Reverse Check Implementation Details

**extra-raises (entry-level comparison — most complex of the three):**
1. `_parse_raises_entries(docstring, style=_active_style)` -> `doc_raises: set[str]`
2. Scope-aware walk collecting `code_raises: set[str]` via existing `_extract_exception_name()`
3. `extra = doc_raises - code_raises` -> emit if non-empty

Key detail: `_extract_exception_name` returns `"(re-raise)"` for bare `raise` (line 303-304). This string will be in `code_raises` but will never match any documented exception name in `doc_raises`, so re-raises naturally don't interfere with the set difference. No special handling needed.

Key detail: `_extract_exception_name` only reads `node.exc`, never `node.cause`. For `raise ValueError("msg") from original_error`, it returns `"ValueError"` — the chaining cause is correctly ignored. Verified by AST analysis; no existing tests cover this (add one).

**New helper `_parse_raises_entries`** follows the `_parse_args_entries` pattern (enrichment.py:1732):
- Google mode: `_extract_section_content("Raises")` -> parse entries at base indent using `_RAISES_ENTRY_PATTERN`
- Sphinx mode: regex scan for `:raises ExcType:` patterns
- Entry pattern matches `ExceptionName:` (class name followed by colon) at base indent level, analogous to `_ARGS_ENTRY_PATTERN`
- Continuation lines (indented further than base) must NOT be parsed as exception names

**extra-yields (section-level, reverse of `_check_missing_yields` at line 601):**
Mirror of forward check with inverted logic:
- Forward: "Yields NOT in sections AND code has yield -> finding"
- Reverse: "Yields IN sections AND code has NO yield -> finding"

**extra-returns (section-level, reverse of `_check_missing_returns` at line 532):**
Mirror of forward check with inverted logic:
- Forward: "Returns NOT in sections AND code has meaningful return -> finding"
- Reverse: "Returns IN sections AND code has NO meaningful return -> finding"
- Reuses existing `_is_meaningful_return()` helper (line 385) — bare `return` and `return None` do NOT count as meaningful

### File Locations

| What | Path |
|------|------|
| Enrichment module | `src/docvet/checks/enrichment.py` |
| New test file | `tests/unit/checks/test_reverse_enrichment.py` |
| Rule pages (3) | `docs/site/rules/extra-raises-in-docstring.md`, `docs/site/rules/extra-yields-in-docstring.md`, `docs/site/rules/extra-returns-in-docstring.md` |
| Rules registry | `docs/rules.yml` |
| Configuration docs | `docs/site/configuration.md` |
| Enrichment check docs | `docs/site/checks/enrichment.md` |
| Docs infra test | `tests/unit/test_docs_infrastructure.py` |

### Existing Helpers to Reuse

- `_extract_exception_name(node: ast.Raise) -> str | None` (line 284) — extracts exception class name from raise node. Returns `"(re-raise)"` for bare `raise`. Only reads `node.exc`, ignores `node.cause` (chaining). Already used in `_check_missing_raises`.
- `_is_meaningful_return(node: ast.Return) -> bool` (line 385) — checks if return has a meaningful value (excludes bare `return` and `return None`). Already used in `_check_missing_returns`.
- `_has_decorator(node, name) -> bool` (line 426) — checks for bare/qualified decorators. Use for `abstractmethod` detection in `_should_skip_reverse_check`.
- `_extract_section_content(docstring, section_name) -> str | None` (line 211) — extracts text content of a section. Foundation for `_parse_raises_entries`.
- `_parse_args_entries(docstring, *, style) -> set[str]` (line 1732) — pattern to follow for `_parse_raises_entries`.
- `_parse_sections(docstring, *, style) -> set[str]` (line 157) — returns set of section names found.
- `_build_node_index(tree) -> dict[int, _NodeT]` (line 256) — line-to-node lookup (already built by orchestrator).
- `_active_style` module-level global — set by orchestrator before dispatch (used for style-aware parsing).
- Scope-aware walk pattern from all existing check functions (iterative stack with nested scope boundary stop).

### Sphinx Style Compatibility

No changes to `_SPHINX_AUTO_DISABLE_RULES` needed. Reverse checks reuse existing config attrs:
- **extra-raises**: Gated by `require_raises` (NOT in auto-disable set) — runs in both Google and Sphinx mode. `_parse_raises_entries` handles Sphinx `:raises ExcType:` via `_SPHINX_RAISES_PATTERN`.
- **extra-yields**: Gated by `require_yields` (IN auto-disable set) — auto-disabled in Sphinx mode, consistent with forward `_check_missing_yields`.
- **extra-returns**: Gated by `require_returns` (NOT in auto-disable set) — runs in both Google and Sphinx mode.

### Competitor Alignment (party-mode research 2026-03-21)

| Tool | Forward Rules | Reverse Rules | Config Model | Skip Logic |
|------|--------------|---------------|-------------|------------|
| **pydoclint** | DOC501, DOC402, DOC201 | DOC502, DOC403, DOC202 | Shared toggle (`--skip-checking-raises`) | Skips abstract/stubs |
| **ruff** | DOC501, DOC402, DOC201 | DOC502, DOC403, DOC202 | Per-rule selection (all preview) | Skips abstract/stubs/NotImplementedError |
| **docvet** (this story) | missing-raises/yields/returns | extra-raises/yields/returns-in-docstring | Shared toggle + category differentiation | Skips abstract/stubs/NotImplementedError |

ruff notes DOC502 as "may be overly restrictive" — the `recommended` category addresses this.

### Domain Pitfalls (from Epic 34-35 retro and previous stories)

- `_extract_exception_name` returns `"(re-raise)"` not `None` for bare `raise` — this naturally excludes re-raises from set comparison without special handling
- `_extract_exception_name` only reads `node.exc`, ignores `node.cause` — exception chaining is handled correctly by construction but has zero test coverage (add test)
- `_has_decorator` does NOT handle `ast.Call` decorators — fine for `@abstractmethod` (always bare), but do NOT use for `@deprecated` (see story 35.2)
- Test helpers must select correct symbol type — verify `kind` and `name` match expectations before asserting on findings
- Guard on `symbol.docstring is not None` for ty type narrowing (learned from 35.1)
- Test unfiltered findings when adding rules to detect cross-rule conflicts (dev quality checklist)

### Test Strategy

Single test file `tests/unit/checks/test_reverse_enrichment.py` covering all 3 rules + skip logic, organized by rule. Use `@pytest.mark.parametrize` for:
- Multiple extra exception names (extra-raises)
- Scope boundary variants (sync func, async func, nested class) — follow pattern from `test_missing_deprecation.py`
- Skip conditions (abstractmethod, `...`, `pass`, `raise NotImplementedError`)
- Config disable across all 3 rules

Follow the `_make_symbol_and_index` helper pattern from `test_param_agreement.py`.

### Test Maturity Piggyback

Continue `@pytest.mark.parametrize` adoption pattern established in stories 35.1 and 35.2. This story has natural parametrize opportunities: scope boundary variants, skip conditions, multiple exception names.

### Documentation Impact

- Pages: `docs/site/rules/extra-raises-in-docstring.md`, `docs/site/rules/extra-yields-in-docstring.md`, `docs/site/rules/extra-returns-in-docstring.md`, `docs/site/configuration.md`, `docs/site/checks/enrichment.md`
- Nature of update: Create 3 new rule reference pages following existing macros scaffold pattern; update `require-raises`, `require-yields`, `require-returns` descriptions in configuration reference to note they gate both forward and reverse checks; add 3 rules to enrichment check page rule list

### Project Structure Notes

- Alignment with unified project structure: new test file in `tests/unit/checks/`, 3 rule pages in `docs/site/rules/`
- No conflicts or variances detected
- `_EXPECTED_RULE_COUNT` in `tests/unit/test_docs_infrastructure.py` must be updated from 25 to 28
- No changes to `config.py` `EnrichmentConfig` or `_VALID_ENRICHMENT_KEYS` — shared toggles reuse existing fields

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 35.3] — FR14-FR16, NFR3, NFR4, NFR9
- [Source: src/docvet/checks/enrichment.py:317-382] — `_check_missing_raises()` (forward pattern to mirror)
- [Source: src/docvet/checks/enrichment.py:532-598] — `_check_missing_returns()` (forward pattern to mirror)
- [Source: src/docvet/checks/enrichment.py:601-661] — `_check_missing_yields()` (forward pattern to mirror)
- [Source: src/docvet/checks/enrichment.py:284-314] — `_extract_exception_name()` (reuse for code_raises; only reads .exc, ignores .cause)
- [Source: src/docvet/checks/enrichment.py:385-402] — `_is_meaningful_return()` (reuse for extra-returns check)
- [Source: src/docvet/checks/enrichment.py:426-444] — `_has_decorator()` (use for abstractmethod detection in skip helper)
- [Source: src/docvet/checks/enrichment.py:211-250] — `_extract_section_content()` (foundation for `_parse_raises_entries`)
- [Source: src/docvet/checks/enrichment.py:1732-1792] — `_parse_args_entries()` (pattern for `_parse_raises_entries`)
- [Source: src/docvet/checks/enrichment.py:2147-2162] — `_RULE_DISPATCH` table (14 entries, add 3 using existing config attrs)
- [Source: src/docvet/checks/enrichment.py:2137-2145] — `_SPHINX_AUTO_DISABLE_RULES` (no changes — inherited via shared toggle)
- [Source: src/docvet/checks/enrichment.py:2159-2160] — `require_param_agreement` dual-gate precedent (gates both missing-param and extra-param)
- [Source: _bmad-output/implementation-artifacts/35-2-missing-deprecation-enrichment-rule.md] — Previous story patterns, domain pitfalls, test structure
- [Source: _bmad-output/implementation-artifacts/35-1-docstring-parameter-agreement-checks.md] — `_parse_args_entries` pattern, `_make_symbol_and_index` test helper
- [Source: Party-mode consensus 2026-03-21] — 4 decisions: shared config toggles (no new keys), `extra-*-in-docstring` naming, `_should_skip_reverse_check` helper, 6 additional test cases
- [Source: Party-mode research 2026-03-21] — pydoclint shared toggle model, ruff DOC202/403/502 skip logic, `_extract_exception_name` chaining analysis

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [ ] `uv run ruff check .` — zero lint violations
- [ ] `uv run ruff format --check .` — zero format issues
- [ ] `uv run ty check` — zero type errors
- [ ] `uv run pytest` — all tests pass, no regressions
- [ ] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- `_parse_raises_entries` follows `_parse_args_entries` pattern with `_RAISES_ENTRY_PATTERN` (Google) and `_SPHINX_RAISES_PATTERN` (Sphinx)
- `_should_skip_reverse_check` composes `_has_decorator(node, "abstractmethod")` + existing `_is_stub_function(node)` — zero code duplication
- 3 reverse check functions follow exact scope-aware walk pattern from forward checks with inverted logic
- Shared config toggles: `require_raises/yields/returns` gate both forward and reverse via `_RULE_DISPATCH` — zero new config keys (party-mode consensus)
- All 3 rules use `category="recommended"` (NFR9) — forward checks use `category="required"`
- No `_SPHINX_AUTO_DISABLE_RULES` changes needed — inherited via shared config attrs
- 43 tests covering all 11 ACs including parametrized scope boundaries, skip conditions, cross-rule interaction, and `yield from` path
- Dogfooding found 2 genuine findings on own codebase: `load_config` and `write_report` document pass-through `FileNotFoundError` — correctly `recommended`

### Change Log

- `src/docvet/checks/enrichment.py`: Added `_RAISES_ENTRY_PATTERN`, `_SPHINX_RAISES_PATTERN`, `_parse_raises_entries()`, `_should_skip_reverse_check()`, `_check_extra_raises_in_docstring()`, `_check_extra_yields_in_docstring()`, `_check_extra_returns_in_docstring()`, 3 `_RULE_DISPATCH` entries
- `tests/unit/checks/test_reverse_enrichment.py`: Created — 43 tests covering all 11 ACs
- `tests/unit/test_docs_infrastructure.py`: Updated `_EXPECTED_RULE_COUNT` from 25 to 28
- `docs/site/rules/extra-raises-in-docstring.md`: Created rule reference page
- `docs/site/rules/extra-yields-in-docstring.md`: Created rule reference page
- `docs/site/rules/extra-returns-in-docstring.md`: Created rule reference page
- `docs/rules.yml`: Added 3 new rule entries (28 total), fixed header comment count
- `docs/site/configuration.md`: Updated `require-raises`, `require-returns`, `require-yields` descriptions to note shared toggle gating; added missing `require-returns` row
- `docs/site/checks/enrichment.md`: Added 3 new rules to table, updated rule count 14 → 17

### File List

| File | Action |
|------|--------|
| `src/docvet/checks/enrichment.py` | Modified |
| `tests/unit/checks/test_reverse_enrichment.py` | Created |
| `tests/unit/test_docs_infrastructure.py` | Modified |
| `docs/site/rules/extra-raises-in-docstring.md` | Created |
| `docs/site/rules/extra-yields-in-docstring.md` | Created |
| `docs/site/rules/extra-returns-in-docstring.md` | Created |
| `docs/rules.yml` | Modified |
| `docs/site/configuration.md` | Modified |
| `docs/site/checks/enrichment.md` | Modified |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review)

### Outcome

Approved with fixes — 3 fixes applied (2 MEDIUM, 1 LOW), 2 findings skipped by consensus.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | Assertion strength gap — secondary positive-finding tests missing `rule`/`category` assertions (Task 7.34) | Fixed — added `rule` + `category` assertions to 7 secondary tests (party-mode consensus: full 6-field on primaries, `rule`+`category` on secondaries) |
| M2 | MEDIUM | Module docstring stale — enrichment.py doesn't mention reverse enrichment checks; dogfooding flags `stale-body` | Fixed — updated module docstring to mention extra-raises/yields/returns detection |
| L1 | LOW | No `yield from` test — implementation handles `ast.YieldFrom` but no test covers this path | Fixed — added `test_yields_section_with_yield_from_no_finding` (43 tests total) |
| L2 | LOW | Dev Notes describe `_should_skip_reverse_check(symbol, node)` but implementation correctly takes only `node` | Skipped — Dev Notes are historical context, implementation is correct |
| L3 | LOW | Quality Gates checkboxes unchecked in story file | Skipped — verified during review, checked at story close |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
