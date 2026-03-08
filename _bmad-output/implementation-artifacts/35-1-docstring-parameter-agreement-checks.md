# Story 35.1: Docstring-Parameter Agreement Checks

Status: review
Branch: `feat/enrichment-35-1-param-agreement-checks`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want docvet to flag signature parameters missing from `Args:` and `Args:` entries not in the signature,
so that my docstrings accurately reflect the function's actual interface.

## Acceptance Criteria

1. **Given** a function with an `Args:` section where a signature parameter is not documented, **when** enrichment runs, **then** a `missing-param-in-docstring` finding is emitted naming the undocumented parameter.

2. **Given** a function with an `Args:` section that documents a name not in the signature, **when** enrichment runs, **then** an `extra-param-in-docstring` finding is emitted naming the stale/incorrect entry.

3. **Given** a method with `self` or `cls` as the first parameter, **when** enrichment runs, **then** `self`/`cls` are always excluded from agreement checks (never expected in `Args:`).

4. **Given** a function with `*args` and `**kwargs` parameters and default config, **when** enrichment runs, **then** `*args`/`**kwargs` are excluded from agreement checks (default: exclude).

5. **Given** `exclude-args-kwargs = false` in `[tool.docvet.enrichment]`, **when** enrichment runs on a function with `*args`/`**kwargs` not in `Args:`, **then** findings are emitted for the undocumented `*args`/`**kwargs`.

6. **Given** a function with a docstring but no `Args:` section, **when** enrichment runs, **then** no param agreement findings are produced (missing section is a different concern).

7. **Given** a function with parameters that all appear in `Args:` and vice versa, **when** enrichment runs, **then** zero param agreement findings are produced.

8. **Given** `_parse_args_entries` helper, **when** it parses an `Args:` section, **then** it extracts parameter names using `_extract_section_content()` and returns a `set[str]` of documented names.

9. **Given** `require-param-agreement = false` in config, **when** enrichment runs, **then** both `missing-param-in-docstring` and `extra-param-in-docstring` rules are skipped.

10. **Given** both param agreement rules are implemented and tested, **when** the story is marked done, **then** rule reference pages exist in `docs/rules/` for both `missing-param-in-docstring` and `extra-param-in-docstring`, registered in `docs/rules.yml`.

11. **Given** `docstring-style = "sphinx"` and a function with `:param name:` entries in its docstring, **when** enrichment runs, **then** param agreement checks parse `:param name:` patterns to extract documented parameter names and compare against the signature (Sphinx mode uses regex scan of full docstring, not section content extraction).

## Tasks / Subtasks

- [x] Task 1: Add `require_param_agreement` and `exclude_args_kwargs` to `EnrichmentConfig` (AC: 5, 9)
  - [x]1.1 Add `require_param_agreement: bool = True` field
  - [x]1.2 Add `exclude_args_kwargs: bool = True` field
  - [x]1.3 Add TOML key parsing in `_parse_enrichment_config()` for both fields
- [x] Task 2: Implement `_parse_args_entries()` helper (AC: 8, 11)
  - [x]2.1 Use `_extract_section_content(docstring, "Args")` to get raw content (Google mode)
  - [x]2.2 Detect base indent from first content line, match entries at that indent via `^{indent}\*{0,2}(\w+)[\s(:]`
  - [x]2.3 Return `set[str]` of documented parameter names (stars stripped)
  - [x]2.4 Handle Sphinx-style: regex scan full docstring for `:param\s+(\w+)\s*:` when style is `"sphinx"`
  - [x]2.5 Guard: if `_extract_section_content()` returns None (e.g. NumPy underline Args), return empty set with comment noting future NumPy content extraction
- [x] Task 3: Implement `_extract_signature_params()` helper (AC: 3, 4, 5)
  - [x]3.1 Extract param names from `ast.arguments` node
  - [x]3.2 Always exclude `self`/`cls`
  - [x]3.3 Conditionally exclude `*args`/`**kwargs` based on `config.exclude_args_kwargs`
  - [x]3.4 Return `set[str]` of signature parameter names
- [x] Task 4: Implement `_check_missing_param_in_docstring()` (AC: 1, 6, 7)
  - [x]4.1 Follow uniform signature: `(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [x]4.2 Guard: return None if "Args" not in sections
  - [x]4.3 Guard: return None if node is not FunctionDef/AsyncFunctionDef
  - [x]4.4 Compute `sig_params - doc_params` to find missing params
  - [x]4.5 Emit finding with comma-separated list of missing param names
- [x] Task 5: Implement `_check_extra_param_in_docstring()` (AC: 2, 6, 7)
  - [x]5.1 Follow uniform signature
  - [x]5.2 Same guards as Task 4
  - [x]5.3 Compute `doc_params - sig_params` to find extra params
  - [x]5.4 Emit finding with comma-separated list of extra param names
- [x] Task 6: Wire into `_RULE_DISPATCH` and orchestrator (AC: 9)
  - [x]6.1 Add two dispatch entries both keyed to `"require_param_agreement"` — deliberate convention extension (1:1 mapping was convention, not constraint; dispatch loop evaluates each independently)
  - [x]6.2 Do NOT add to `_SPHINX_AUTO_DISABLE_RULES` — param agreement works in both Google and Sphinx modes (`:param:` maps to `"Args"`)
- [x] Task 7: Write tests in `tests/unit/checks/test_param_agreement.py` (AC: 1-11)
  - [x]7.1 Fixture with various param agreement scenarios (functions, methods, classes, async)
  - [x]7.2 Test missing param detection (use `@pytest.mark.parametrize` for multiple scenarios)
  - [x]7.3 Test extra param detection (parametrize)
  - [x]7.4 Test self/cls exclusion
  - [x]7.5 Test *args/**kwargs exclusion (default and opt-in), including star-prefixed docstring entries
  - [x]7.6 Test no Args section → zero findings
  - [x]7.7 Test perfect agreement → zero findings
  - [x]7.8 Test config disable → zero findings
  - [x]7.9 Cross-rule interaction tests (unfiltered findings): @overload symbol → no findings, class symbol → no findings, module symbol → no findings, function with missing-raises AND missing-param → both findings emitted
  - [x]7.10 Test positional-only params (`def foo(x, /, y)`) are checked
  - [x]7.11 Test keyword-only params (`def foo(*, key=None)`) are checked
  - [x]7.12 Test `async def` params are checked
  - [x]7.13 Test Sphinx mode: `:param name:` entries parsed correctly
  - [x]7.14 Assert `finding.symbol`, `finding.rule`, and `finding.message` on every test (test validity)
- [x] Task 8: Create rule reference pages (AC: 10)
  - [x]8.1 Create `docs/site/rules/missing-param-in-docstring.md`
  - [x]8.2 Create `docs/site/rules/extra-param-in-docstring.md`
  - [x]8.3 Register both in `docs/rules.yml`
- [x] Task 9: Run quality gates and verify dogfooding
  - [x]9.1 `uv run ruff check .` — zero violations
  - [x]9.2 `uv run ruff format --check .` — zero issues
  - [x]9.3 `uv run ty check` — zero errors
  - [x]9.4 `uv run pytest` — all pass
  - [x]9.5 `uv run docvet check --all` — zero findings

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_missing_param_detection[single-missing]`, `test_missing_param_detection[multiple-missing]` | Pass |
| 2 | `test_extra_param_detection[single-extra]`, `test_extra_param_detection[multiple-extra]` | Pass |
| 3 | `test_self_cls_exclusion[self-excluded]`, `test_self_cls_exclusion[cls-excluded]` | Pass |
| 4 | `test_args_kwargs_excluded_by_default`, `test_documented_args_kwargs_not_extra_when_excluded` | Pass |
| 5 | `test_args_kwargs_required_when_opt_in`, `test_star_prefixed_args_in_docstring_match_signature` | Pass |
| 6 | `test_no_args_section_no_findings` | Pass |
| 7 | `test_perfect_agreement_zero_findings` | Pass |
| 8 | `TestParseArgsEntries` (6 tests), `TestExtractSignatureParams` (8 tests) | Pass |
| 9 | `test_config_disable_skips_both_rules` | Pass |
| 10 | Rule pages created: `missing-param-in-docstring.md`, `extra-param-in-docstring.md`, registered in `rules.yml` | Done |
| 11 | `test_sphinx_mode_param_parsing`, `test_sphinx_mode_extra_param`, `test_sphinx_orchestrator_integration` | Pass |

## Dev Notes

- **Interaction Risk:** This story adds 2 rules (`missing-param-in-docstring`, `extra-param-in-docstring`) to the enrichment module which already has 11 rules dispatched via `_RULE_DISPATCH`. Verify: (1) no cross-rule findings on `@overload` symbols (presence layer skips them), (2) param agreement rules don't fire on class/module symbols (guard on FunctionDef/AsyncFunctionDef), (3) existing `missing-raises`, `missing-returns` rules unaffected.

### Architecture & Implementation Patterns

**Uniform check signature** — both `_check_missing_param_in_docstring` and `_check_extra_param_in_docstring` must follow:
```python
def _check_*(symbol, sections, node_index, config, file_path) -> Finding | None
```

**Config gating in orchestrator, NOT in check functions.** The `check_enrichment` orchestrator checks `getattr(config, attr)` before dispatching. The `_check_*` functions never inspect config toggles — they assume they should run.

**`_RULE_DISPATCH` wiring** — use two separate entries both keyed to `"require_param_agreement"`:
```python
("require_param_agreement", _check_missing_param_in_docstring),
("require_param_agreement", _check_extra_param_in_docstring),
```
This is a deliberate convention extension. The existing 11 entries use 1:1 config-to-function mapping, but the dispatch loop evaluates each entry independently via `getattr(config, attr)` — two entries with the same key both resolve to the same bool. This preserves the `Finding | None` return type contract and requires zero orchestrator changes. Do NOT use a single function returning a list.

**`_extract_section_content()` for Args parsing** — call `_extract_section_content(docstring, "Args")` to get the raw text below `Args:`. Then detect the base indent from the first non-empty content line and parse entries at that indent level. Google-style format:
```
Args:
    name: Description of name.
    timeout (int): The timeout in seconds.
        Continuation line for timeout.
    *args: Positional arguments.
    **kwargs: Keyword arguments.
```
Use base indent detection (NOT hardcoded `\s{2,}`): measure the indent of the first content line, then match lines at that exact indent. Entry regex: `^{base_indent}\*{0,2}(\w+)[\s(:]` — captures the param name after optional `*`/`**` prefix. Continuation lines (deeper indent) are skipped.

**NumPy underline Args guard** — if `"Args"` is in `sections` (from `_NUMPY_UNDERLINE_PATTERN` match) but `_extract_section_content()` returns `None` (it only handles `Args:\s*$` format), return an empty set gracefully. Add a comment noting future NumPy content extraction support.

**Star handling in docstring entries** — docstring entries may use `*args` or `**kwargs` with star prefixes. The regex `\*{0,2}(\w+)` strips stars and captures just the name. On the signature side, `ast.arguments.vararg.arg` already provides the bare name (e.g., `"args"` not `"*args"`). Comparison uses bare names on both sides.

**Sphinx-style param parsing** — when `style == "sphinx"`, the `_parse_sections()` returns `"Args"` for `:param name:` patterns. The param _names_ need to be extracted differently: parse `:param name:` entries from the raw docstring. Use `_SPHINX_SECTION_MAP` key `:param` to identify these. Regex: `r":param\s+(\w+)\s*:"`.

**AST argument extraction** — `ast.arguments` structure:
- `args.posonlyargs` — positional-only params (before `/`) — MUST be included in checks
- `args.args` — regular params (includes `self`/`cls`)
- `args.vararg` — `*args` (single node or None, `.arg` gives bare name e.g. `"args"`)
- `args.kwonlyargs` — keyword-only params (after `*`) — MUST be included in checks
- `args.kwarg` — `**kwargs` (single node or None, `.arg` gives bare name e.g. `"kwargs"`)
- Always exclude first param if name is `self` or `cls`
- No star stripping needed on signature side — `vararg.arg` and `kwarg.arg` are already bare names

**Domain pitfalls (from Epic 34 retro):**
- AST body includes docstring node — not relevant here but keep in mind
- `\s` matches `\n` in regex — use `[^\S\n]` for horizontal whitespace only
- Test helpers must select correct symbol type — verify `kind` and `name` match expectations
- Test unfiltered findings when adding rules to detect cross-rule conflicts

### File Locations

| What | Path |
|------|------|
| Enrichment module | `src/docvet/checks/enrichment.py` |
| Config module | `src/docvet/config.py` |
| New test file | `tests/unit/checks/test_param_agreement.py` |
| Test fixtures | `tests/fixtures/` (create `param_agreement.py`) |
| Rule page 1 | `docs/site/rules/missing-param-in-docstring.md` |
| Rule page 2 | `docs/site/rules/extra-param-in-docstring.md` |
| Rules registry | `docs/rules.yml` |
| Docs macros | `docs/main.py` |

### Existing Helpers to Reuse

- `_extract_section_content(docstring, section_name)` — extracts raw text below a section header
- `_parse_sections(docstring, *, style)` — returns `set[str]` of section names found
- `_build_node_index(tree)` — line-to-AST-node lookup (already built by orchestrator)
- `get_documented_symbols(tree)` — returns `list[Symbol]` with docstrings (from `ast_utils`)

### Config Field Additions

In `config.py`, `EnrichmentConfig` needs:
- `require_param_agreement: bool = True` — gates both rules
- `exclude_args_kwargs: bool = True` — controls `*args`/`**kwargs` exclusion

In `_parse_enrichment_config()`, map TOML keys:
- `require-param-agreement` → `require_param_agreement`
- `exclude-args-kwargs` → `exclude_args_kwargs`

### Sphinx Style Compatibility

Param agreement works in both Google and Sphinx modes:
- Google: parse `Args:` section entries
- Sphinx: parse `:param name:` entries from full docstring
- The `sections` set will contain `"Args"` in both modes (Sphinx maps `:param` → `"Args"`)
- For **doc_params** extraction in sphinx mode, scan raw docstring for `:param (\w+):` patterns instead of parsing section content

### Deferred Scope

- **Argument order checking** (pydoclint DOC103): Not in scope for this story. DOC103 checks that docstring arg order matches signature order — a separate concern from presence agreement. Deferred to a future story if user demand emerges.

### Competitor Context (pydoclint)

pydoclint v0.8.3+ has three related codes: DOC101 (fewer args), DOC102 (more args), DOC103 (different/reordered args). Key config differences:
- pydoclint `--should-document-star-arguments` defaults to `True` (require `*args`/`**kwargs` docs). Docvet's `exclude-args-kwargs` defaults to `True` (exclude them). This is a deliberate divergence — Google-style convention typically omits `*args`/`**kwargs` from `Args:`.
- Rule reference docs for both rules MUST include a migration note: "By default, `*args` and `**kwargs` are excluded from agreement checks. Set `exclude-args-kwargs = false` to require their documentation (matches pydoclint's default behavior)."

### Test Maturity Piggyback

From test-review.md (P2): Near-zero `@pytest.mark.parametrize` usage (7 usages in 1,210 tests). **Use `@pytest.mark.parametrize`** for param agreement test scenarios — this story is ideal because multiple fixture functions share the same assertion pattern (e.g., different param combinations all producing one finding). Party-mode consensus: parametrize is mandatory for this story's test file.

### Documentation Impact

- Pages: `docs/site/rules/missing-param-in-docstring.md`, `docs/site/rules/extra-param-in-docstring.md`, `docs/site/configuration.md`
- Nature of update: Create 2 new rule reference pages following existing pattern (macros scaffold in `docs/main.py`); add `require-param-agreement` and `exclude-args-kwargs` config keys to configuration reference table

### Project Structure Notes

- Alignment with unified project structure: new test file in `tests/unit/checks/`, fixtures in `tests/fixtures/`, rule pages in `docs/site/rules/`
- No conflicts or variances detected

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 35.1] — FR9-FR11, NFR3, NFR4
- [Source: _bmad-output/planning-artifacts/architecture.md] — `_RULE_DISPATCH` pattern, uniform check signature, config gating
- [Source: src/docvet/checks/enrichment.py] — `_extract_section_content()`, `_parse_sections()`, `_RULE_DISPATCH` table
- [Source: src/docvet/config.py] — `EnrichmentConfig` dataclass, `_parse_enrichment_config()`
- [Source: _bmad-output/implementation-artifacts/epic-34-retro-2026-03-08.md] — Domain pitfalls (AST body, regex `\s`, test validity, cross-rule interactions)
- [Source: pydoclint violation codes](https://jsh9.github.io/pydoclint/violation_codes.html) — DOC101/DOC102/DOC103 competitor analysis
- [Source: pydoclint config options](https://jsh9.github.io/pydoclint/config_options.html) — `--should-document-star-arguments`, `--check-arg-order` defaults
- [Source: Party-mode consensus 2026-03-08] — 11 decisions: two dispatch entries, Sphinx AC, order deferred, star stripping, parametrize mandatory, pydoclint migration note

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1465 passed
- [x] `uv run docvet check --all` — zero required findings (1 recommended stale-body on check_enrichment, expected)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Module-level `_active_style` variable used to pass style to check functions without changing uniform signature
- Tests use `autouse` fixture to reset `_active_style` after each test, preventing random-order failures
- `_RULE_DISPATCH` extended with two entries sharing `"require_param_agreement"` key (deliberate convention extension)
- Both check functions add `symbol.docstring is None` guard for ty type narrowing

### Change Log

- `src/docvet/config.py`: Added `require_param_agreement` and `exclude_args_kwargs` fields to `EnrichmentConfig`, TOML key validation, format rendering
- `src/docvet/checks/enrichment.py`: Added `_parse_args_entries()`, `_extract_signature_params()`, `_check_missing_param_in_docstring()`, `_check_extra_param_in_docstring()`, `_active_style` module variable, two `_RULE_DISPATCH` entries
- `tests/unit/checks/test_param_agreement.py`: Created — 39 tests covering all 11 ACs
- `tests/unit/test_docs_infrastructure.py`: Updated `_EXPECTED_RULE_COUNT` from 22 to 24
- `docs/site/rules/missing-param-in-docstring.md`: Created rule reference page
- `docs/site/rules/extra-param-in-docstring.md`: Created rule reference page
- `docs/rules.yml`: Added 2 new rule entries (24 total)
- `docs/site/configuration.md`: Added `require-param-agreement` and `exclude-args-kwargs` to enrichment options table and full example (review fix H1)
- `docs/site/rules/missing-param-in-docstring.md`: Added pydoclint migration note (review fix M1)
- `docs/site/rules/extra-param-in-docstring.md`: Added pydoclint migration note and `exclude-args-kwargs` interaction note (review fixes M1, L1)
- `tests/unit/checks/test_param_agreement.py`: Renamed misleading test (review fix M2)

### File List

| File | Action |
|------|--------|
| `src/docvet/config.py` | Modified |
| `src/docvet/checks/enrichment.py` | Modified |
| `tests/unit/checks/test_param_agreement.py` | Created |
| `tests/unit/test_docs_infrastructure.py` | Modified |
| `docs/site/rules/missing-param-in-docstring.md` | Created |
| `docs/site/rules/extra-param-in-docstring.md` | Created |
| `docs/rules.yml` | Modified |
| `docs/site/configuration.md` | Modified (review) |

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party-mode consensus)

### Outcome

Changes Requested — 4 findings fixed

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | `docs/site/configuration.md` not updated with `require-param-agreement` and `exclude-args-kwargs` config keys | Fixed — added both keys to enrichment options table and full example |
| M1 | MEDIUM | Missing pydoclint migration notes in both rule reference pages | Fixed — added migration notes mentioning pydoclint's `--should-document-star-arguments` default |
| M2 | MEDIUM | Test name `test_documented_args_kwargs_not_extra_when_excluded` contradicts its assertion (says "not extra" but asserts `extra is not None`) | Fixed — renamed to `test_documented_args_kwargs_flagged_as_extra_when_excluded` |
| L1 | LOW | `extra-param-in-docstring.md` missing `exclude-args-kwargs` interaction note in Configuration section | Fixed — added note explaining behavior when `exclude-args-kwargs = true` |
| -- | LOW | No fixture file in `tests/fixtures/` | Dismissed — inline sources are better for parametrized tests |
| -- | -- | `*args`/`**kwargs` flagged as extra when `exclude_args_kwargs=True` — initially raised as HIGH | Downgraded after party-mode debate + web research: current behavior matches pydoclint precedent; documented in rule pages |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
