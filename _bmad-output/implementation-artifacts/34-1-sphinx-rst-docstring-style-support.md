# Story 34.1: Sphinx/RST Docstring Style Support

Status: review
Branch: `feat/enrichment-34-1-sphinx-rst-style-support`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer maintaining a Sphinx/RST-style codebase,
I want docvet to recognize RST section patterns and auto-disable incompatible rules,
so that I get meaningful enrichment findings without false positives.

## Acceptance Criteria

1. **Given** a pyproject.toml with `docstring-style = "sphinx"` under `[tool.docvet]`, **When** docvet loads the configuration, **Then** the `docstring_style` field is set to `"sphinx"` and all style-aware behavior switches to RST patterns.

2. **Given** `docstring-style = "sphinx"` is set, **When** enrichment parses a docstring containing `:param name:`, `:type name:`, `:returns:`, `:rtype:`, `:raises ExcType:`, `:ivar name:`, `:cvar name:`, `.. seealso::`, or `>>>` / `::` / `.. code-block::`, **Then** each RST pattern is mapped to its Google-equivalent internal section name (Args, Returns, Raises, Attributes, See Also, Examples).

3. **Given** `docstring-style = "sphinx"` is set, **When** enrichment evaluates rules that have no RST equivalent (`require-yields`, `require-receives`, `require-warns`, `require-other-parameters`), **Then** those rules are auto-disabled and produce no findings.

4. **Given** `docstring-style = "sphinx"` is set, **When** enrichment evaluates `prefer-fenced-code-blocks`, **Then** the rule is auto-disabled (RST `::` and `>>>` patterns are correct in Sphinx mode).

5. **Given** `docstring-style = "sphinx"` is set, **When** enrichment evaluates `missing-cross-references`, **Then** Sphinx roles (`:py:class:`, `:py:meth:`, `:py:func:`, etc.) anywhere in the docstring body satisfy the cross-reference check.

6. **Given** `docstring-style = "sphinx"` is set, **When** the CLI runs `docvet check` or `docvet griffe`, **Then** the griffe compatibility check is auto-skipped (Google parser is incompatible with RST).

7. **Given** `docstring-style = "sphinx"` is set AND the user has explicitly set `require-yields = true` in their config, **When** enrichment evaluates the yields rule, **Then** the explicit user setting overrides auto-disable and the rule runs (NFR5: explicit settings beat auto-disable defaults).

8. **Given** `docstring-style` is omitted from config, **When** docvet loads the configuration, **Then** the default value is `"google"` and all existing behavior is unchanged.

9. **Given** `docstring-style` is set to an invalid value (e.g., `"numpy"`, `"plain"`), **When** docvet loads the configuration, **Then** a clear validation error is raised listing valid options.

10. **Given** a Sphinx-style docstring with `:param name:` entries, **When** `_parse_sections()` runs in sphinx mode, **Then** section detection uses pattern matching only — no RST parser dependency (NFR1).

11. **Given** a Google-style docstring with `Args:`, `Returns:`, `Raises:` headers, **When** `_parse_sections()` runs in google mode (default), **Then** behavior is identical to the current implementation — zero regression.

12. **Given** `docstring-style` is a new top-level config key under `[tool.docvet]`, **When** the story is marked done, **Then** the configuration reference page documents the key with valid values, default, and behavior summary.

## Tasks / Subtasks

- [x] Task 1: Add `docstring_style` to config layer (AC: 1, 8, 9)
  - [x] 1.1 Add `docstring_style: str = "google"` field to `DocvetConfig` dataclass in `config.py`
  - [x] 1.2 Add `"docstring-style"` to `_VALID_TOP_KEYS` frozenset
  - [x] 1.3 Add validation in `_parse_docvet_section()` — accept `"google"` or `"sphinx"`, raise `ValueError` for anything else
  - [x] 1.4 Update `format_config_toml()` and `format_config_json()` to include `docstring-style` with source annotation
  - [x] 1.5 Write unit tests: default value, valid values, invalid value error, format output

- [x] Task 2: Add Sphinx section detection to enrichment (AC: 2, 10, 11)
  - [x] 2.1 Create `_SPHINX_SECTION_MAP: dict[str, str]` mapping RST patterns to internal section names (`:param` → Args, `:returns:`/`:rtype:` → Returns, `:raises` → Raises, `:ivar:`/`:cvar:` → Attributes, `.. seealso::` → See Also, `>>>`/`::`/`.. code-block::` → Examples)
  - [x] 2.2 Create `_SPHINX_SECTION_PATTERN` regex to detect all RST section patterns
  - [x] 2.3 Extend `_parse_sections()` to accept a `style: str = "google"` parameter (direct param, not through config — it's a parsing concern). When `"sphinx"`, use body-scan regex against `_SPHINX_SECTION_PATTERN` (NOT line-by-line header matching like Google mode — RST patterns are inline with content e.g. `:param name: desc`) and map matches to internal names via `_SPHINX_SECTION_MAP`
  - [x] 2.4 Write unit tests: each RST pattern maps correctly, Google mode unchanged, mixed content, edge cases

- [x] Task 3: Implement auto-disable for incompatible rules in sphinx mode (AC: 3, 4, 7)
  - [x] 3.1 Define `_SPHINX_AUTO_DISABLE_RULES: frozenset[str]` = `{"require_yields", "require_receives", "require_warns", "require_other_parameters", "prefer_fenced_code_blocks"}`
  - [x] 3.2 In `check_enrichment()`, add style-aware gating: skip rules in `_SPHINX_AUTO_DISABLE_RULES` when `style == "sphinx"` UNLESS the user explicitly set the config toggle to `True`
  - [x] 3.3 Plumb `docstring_style` from `DocvetConfig` through to `check_enrichment()` — add `style: str = "google"` parameter
  - [x] 3.4 Determine "explicitly set" vs "default" — add `_user_set_keys: frozenset[str]` to `EnrichmentConfig`. **Critical timing**: populate from raw TOML dict keys in `_parse_enrichment()` BEFORE constructing the dataclass (field defaults make all keys look "set" after construction). Pass the set of present TOML keys into the constructor.
  - [x] 3.5 Write unit tests: auto-disable fires in sphinx mode, explicit override beats auto-disable, google mode unchanged

- [x] Task 4: Extend cross-reference check for Sphinx roles (AC: 5)
  - [x] 4.1 In `_check_missing_cross_references()`, add detection for Sphinx roles (`:py:class:`, `:py:meth:`, `:py:func:`, `:py:attr:`, `:py:mod:`, `:py:exc:`, `:py:data:`, `:py:const:`, `:py:obj:`) as satisfying the cross-reference requirement when style is sphinx
  - [x] 4.2 Plumb `style` parameter to `_check_missing_cross_references` or use config
  - [x] 4.3 Write unit tests: Sphinx roles satisfy cross-ref check in sphinx mode, Google backtick refs still work in google mode

- [x] Task 5: Auto-skip griffe check in sphinx mode (AC: 6)
  - [x] 5.1 In `cli.py` where griffe check is dispatched in `check()` (`if "griffe" in checks:`), add condition to skip when `config.docstring_style == "sphinx"`
  - [x] 5.2 In `cli.py` `griffe()` subcommand, add early exit when `config.docstring_style == "sphinx"` — emit skip message ("Griffe check skipped: incompatible with sphinx docstring style") and exit 0
  - [x] 5.3 Emit a verbose message or log when griffe is auto-skipped in `check()` (for user awareness)
  - [x] 5.4 Write unit tests: griffe skipped in sphinx mode (both `check` and `griffe` subcommands), griffe runs in google mode

- [x] Task 6: Documentation update (AC: 12)
  - [x] 6.1 Add `docstring-style` to `docs/site/configuration.md` under top-level options table with valid values, default, and behavior description
  - [x] 6.2 Update any relevant check pages that reference style-dependent behavior

- [x] Task 7: Integration verification
  - [x] 7.1 Run `docvet check --all` on own codebase (google mode) — zero regression
  - [x] 7.2 Create a Sphinx-style fixture file and verify sphinx mode produces correct findings
  - [x] 7.3 All quality gates pass

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `test_load_config_docstring_style_sphinx` | Pass |
| 2 | `test_parse_sections_sphinx_param_detected`, `test_parse_sections_sphinx_returns_detected`, `test_parse_sections_sphinx_raises_detected`, `test_parse_sections_sphinx_ivar_detected`, `test_parse_sections_sphinx_seealso_detected`, `test_parse_sections_sphinx_doctest_detected`, `test_parse_sections_sphinx_double_colon_detected`, `test_parse_sections_sphinx_code_block_detected`, `test_parse_sections_sphinx_multiple_sections` | Pass |
| 3 | `test_check_enrichment_sphinx_auto_disables_yields_rule`, `test_check_enrichment_sphinx_auto_disables_receives_rule`, `test_check_enrichment_sphinx_auto_disables_warns_rule` | Pass |
| 4 | `test_check_enrichment_sphinx_auto_disables_fenced_code_blocks_rule` | Pass |
| 5 | `test_check_enrichment_sphinx_role_satisfies_cross_ref_check`, `test_check_enrichment_sphinx_py_func_role_satisfies_cross_ref`, `test_check_enrichment_sphinx_no_roles_still_flags_missing_cross_ref` | Pass |
| 6 | `test_griffe_subcommand_sphinx_mode_skips_with_message`, `test_check_command_sphinx_mode_skips_griffe`, `test_check_command_google_mode_runs_griffe` | Pass |
| 7 | `test_check_enrichment_sphinx_explicit_override_beats_auto_disable` | Pass |
| 8 | `test_docvet_defaults_docstring_style_is_google`, `test_load_config_docstring_style_omitted_defaults_to_google` | Pass |
| 9 | `test_load_config_docstring_style_invalid_exits`, `test_load_config_docstring_style_wrong_type_exits` | Pass |
| 10 | `test_parse_sections_sphinx_param_detected` (pure regex, no RST parser) | Pass |
| 11 | `test_parse_sections_google_mode_unchanged`, `test_parse_sections_default_style_is_google`, `test_parse_sections_google_mode_ignores_sphinx_patterns` | Pass |
| 12 | `docs/site/configuration.md` updated with `docstring-style` section | Pass |

## Dev Notes

### Architecture — Config Layer Changes

**File: `src/docvet/config.py`**

- `DocvetConfig` is a frozen dataclass (line ~152). Add `docstring_style: str = "google"` field.
- `_VALID_TOP_KEYS` is a frozenset (line ~60). Add `"docstring-style"`.
- `_parse_docvet_section()` (line ~540) validates keys and converts kebab-case to snake_case. Add validation for `docstring-style` accepting only `"google"` and `"sphinx"` — raise `ValueError` with message listing valid options.
- `format_config_toml()` and `format_config_json()` need to include the new key.
- **No new dataclass needed** — `docstring_style` is a top-level config field, not a sub-section.

### Architecture — Enrichment Layer Changes

**File: `src/docvet/checks/enrichment.py`**

- **Section parsing**: `_parse_sections()` (line ~102) currently uses `_SECTION_PATTERN` regex (matches `SectionName:` format). For sphinx mode, create a parallel `_SPHINX_SECTION_PATTERN` that matches RST field-list patterns (`:param:`, `:returns:`, etc.) and a `_SPHINX_SECTION_MAP` to normalize to internal names.
- **Key insight**: Sphinx sections are NOT colon-header format. They use field-list syntax (`:param name: description`), directive syntax (`.. seealso::`), and inline patterns (`>>>`, `::`). The `_parse_sections()` approach must be fundamentally different for sphinx — pattern scan the entire docstring body, not look for header lines.
- **`_SECTION_HEADERS` frozenset** (line ~86) — used to recognize valid section boundaries. For sphinx mode, this isn't directly applicable since RST uses field-list syntax, not headers.
- **Rule dispatch**: `_RULE_DISPATCH` tuple (line ~1406) and the orchestrator loop (line ~1440). Auto-disable logic goes in the orchestrator loop, BEFORE the `getattr(config, attr)` check.
- **Auto-disable vs explicit override (NFR5)**: The current `EnrichmentConfig` uses defaults for all toggles (e.g., `require_yields: bool = True`). To distinguish "user explicitly set `require-yields = true`" from "default is `true`", need a mechanism to track which keys were user-provided. Options:
  - **Option A**: Add `_user_set_keys: frozenset[str]` field to `EnrichmentConfig` populated during parsing (preferred — minimal surface area, no production logic change)
  - **Option B**: Use sentinel `None` defaults and resolve later (changes field types, more invasive)
  - **Recommended**: Option A — parse `_parse_enrichment()` to record which keys were present in the TOML, store in a frozen set on the config. Auto-disable check: `if attr in _SPHINX_AUTO_DISABLE_RULES and style == "sphinx" and attr not in config._user_set_keys: skip`.

### Architecture — CLI Layer Changes

**File: `src/docvet/cli.py`**

- The `check()` subcommand (line ~600+) calls `check_enrichment(source, tree, config.enrichment, str(file_path))`. Need to pass `config.docstring_style` as the style parameter.
- The griffe dispatch (line ~750+): `if "griffe" in checks:` — add `and config.docstring_style != "sphinx"` guard.
- The `enrichment()` subcommand (line ~500+) also calls `check_enrichment()` directly — same style plumbing needed.

### Architecture — Cross-Reference Extension

**File: `src/docvet/checks/enrichment.py` — `_check_missing_cross_references()`**

- Currently checks for backtick-wrapped references (`\`ClassName\``) in the docstring body.
- For sphinx mode, Sphinx roles like `:py:class:\`ClassName\`` should also satisfy the check.
- Add a `_SPHINX_ROLE_PATTERN` regex: `r":py:\w+:`[^`]+`"` to detect any Sphinx cross-reference role.
- When `style == "sphinx"`, check for either backtick refs OR Sphinx roles.

### Architecture — Sphinx Section Detection Strategy

The fundamental difference from Google-style:
- **Google**: Section headers on their own line (`Args:\n`), content indented below
- **Sphinx/RST**: Field lists inline (`:param name: description`), directives (`.. seealso::`), code patterns (`>>>`, `::`)

**`_parse_sections()` for sphinx mode should:**
1. Scan docstring for `:param` or `:type` → return "Args" in sections set
2. Scan for `:returns:` or `:rtype:` → return "Returns"
3. Scan for `:raises ExcType:` → return "Raises"
4. Scan for `:ivar` or `:cvar` → return "Attributes"
5. Scan for `.. seealso::` or inline `:py:*:` roles → return "See Also"
6. Scan for `>>>` or `::` or `.. code-block::` → return "Examples"

This is a pure pattern-matching scan with regex, no RST parser needed (NFR1).

### Existing Patterns to Follow

- **Table-driven dispatch** (`_RULE_DISPATCH`): New auto-disable logic integrates at the dispatch level, NOT inside individual `_check_*` functions. Config gating is in the orchestrator.
- **Uniform rule signature**: `(symbol, sections, node_index, config, file_path) -> Finding | None`. Do NOT change this.
- **Style plumbing design decision (party-mode consensus)**: Pass `style` as a direct `str` parameter to `_parse_sections()` — it's a parsing concern, not a config toggle. The orchestrator reads `style` from `DocvetConfig.docstring_style` and passes it down. Do NOT add `docstring_style` to `EnrichmentConfig` — keep it at the top-level config.
- **`_extract_section_content()`**: For sphinx mode, this function needs style-awareness too if any rule calls it (e.g., future param agreement rules). For now, section detection (`_parse_sections()`) is the primary extension point.
- **Test pattern**: Use `_make_symbol_and_index()` helper, test all 6 Finding fields, test both positive and negative cases.
- **Fixture pattern**: Create `tests/fixtures/sphinx_style.py` with RST-style docstrings for integration-level verification.

### Critical Gotchas

1. **`_run_*` functions return `tuple[list[Finding], int]`** (not just `list[Finding]`) — established in Epic 31. Don't break this.
2. **`_user_set_keys` tracking**: The `_parse_enrichment()` function (line ~437 in config.py) iterates over TOML keys and validates types. Record which keys are present BEFORE applying defaults. The `EnrichmentConfig` constructor applies defaults via field defaults — so `_user_set_keys` must be populated from the raw TOML dict, not from the constructed config.
3. **Zero regression on google mode**: The default path must be identical. All new code paths should be gated on `style == "sphinx"`. The existing `_SECTION_PATTERN` regex and `_parse_sections()` logic must not be modified for google mode.
4. **`from __future__ import annotations`**: Every file. No exceptions.
5. **No new runtime deps**: Pattern matching only. No `docutils`, no `sphinx`, no RST parser.
6. **project-context.md line 121** says "Do not add support for numpy/sphinx style" — this is outdated. Epics 34-35 planning explicitly supersedes this rule. The story should NOT update project-context.md (that's a separate housekeeping task), but the dev agent should be aware this constraint no longer applies.

### Test Maturity Piggyback

From test-review.md — Recommendation #3 (P3): Add explicit `# Should not raise` comments to assertion-free tests in `tests/unit/test_config.py` (lines 824, 850). Since this story touches config.py validation, add these comments when working in the test_config.py file.

### Project Structure Notes

- All changes align with existing project structure
- New files: `tests/fixtures/sphinx_style.py` (fixture), possibly `tests/unit/checks/test_enrichment_sphinx.py` (dedicated test file for sphinx detection — follows recommendation #2 from test-review.md to split by feature)
- Modified files: `src/docvet/config.py`, `src/docvet/checks/enrichment.py`, `src/docvet/cli.py`, `tests/unit/test_config.py`, `tests/unit/checks/test_enrichment.py` (or new file), `docs/site/configuration.md`
- No new modules or packages needed

### References

- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Story 34.1] — Full AC and FR mapping
- [Source: _bmad-output/planning-artifacts/epics-multi-style-enrichment.md#Requirements Inventory] — FR1-FR6, NFR1, NFR3-NFR5, NFR8
- [Source: src/docvet/config.py] — Config loading, DocvetConfig, EnrichmentConfig, validation
- [Source: src/docvet/checks/enrichment.py] — _parse_sections, _SECTION_PATTERN, _SECTION_HEADERS, _RULE_DISPATCH, check_enrichment
- [Source: src/docvet/cli.py] — Check dispatch, griffe wiring, _output_and_exit
- [Source: src/docvet/checks/griffe_compat.py] — check_griffe_compat entry point
- [Source: _bmad-output/project-context.md] — Project rules (note: line 121 sphinx restriction is superseded by Epics 34-35)
- [Source: _bmad-output/test-artifacts/test-review.md#Recommendations] — Test maturity piggyback items

### Documentation Impact

- Pages: docs/site/configuration.md
- Nature of update: Add `docstring-style` to top-level config options table with valid values (`"google"`, `"sphinx"`), default (`"google"`), and behavior summary describing auto-disable rules, section pattern switching, and griffe auto-skip

## Quality Gates

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (1350), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Task 1: Added `docstring_style: str = "google"` field to `DocvetConfig`, `_VALID_DOCSTRING_STYLES` constant, validation in `_parse_docvet_section()`, and format output in both TOML and JSON formatters. 12 new config tests.
- Task 2: Created `_SPHINX_SECTION_MAP`, `_SPHINX_SECTION_PATTERN` regex, and `_parse_sphinx_sections()` helper. Extended `_parse_sections()` with `style` keyword parameter. 30 new tests in dedicated `test_enrichment_sphinx.py` file.
- Task 3: Added `_SPHINX_AUTO_DISABLE_RULES` frozenset, `user_set_keys` field to `EnrichmentConfig`, user key tracking in `_parse_enrichment()`, and style-aware gating in the orchestrator loop. Explicit user settings override auto-disable (NFR5). 10 new tests.
- Task 4: Added `_SPHINX_ROLE_PATTERN` regex for domain-qualified Sphinx roles. Orchestrator suppresses cross-reference findings when Sphinx roles are found anywhere in the docstring body. 4 new tests.
- Task 5: Auto-skip griffe in `check()` command and early exit in `griffe()` subcommand when style is sphinx. Verbose message emitted when skipped. 3 new CLI tests.
- Task 6: Added `docstring-style` to configuration.md with full behavior description, including auto-disable rules, cross-reference handling, griffe auto-skip, and explicit override example.
- Task 7: All quality gates pass. Sphinx fixture file created. Dogfooding clean.
- Bonus: Added `type: ignore[arg-type]` to existing enrichment test that ty flagged due to new `user_set_keys` field. Updated stale docstrings flagged by freshness check.

### Change Log

- 2026-03-07: Implemented Sphinx/RST docstring style support (Story 34.1) — config layer, enrichment section detection, auto-disable rules, cross-reference extension, griffe auto-skip, documentation update

### File List

New files:
- tests/unit/checks/test_enrichment_sphinx.py
- tests/fixtures/sphinx_style.py

Modified files:
- src/docvet/config.py
- src/docvet/checks/enrichment.py
- src/docvet/cli.py
- tests/unit/test_config.py
- tests/unit/test_cli.py
- tests/unit/checks/test_enrichment.py
- docs/site/configuration.md

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
