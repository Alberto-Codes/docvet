# Story 32.2: Fix Core -- Section Scaffolding Engine

Status: review
Branch: `feat/fix-32-2-section-scaffolding-engine`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want `docvet fix` to generate missing docstring sections from AST analysis,
so that I get a skeleton I can fill in instead of writing sections from scratch.

## Acceptance Criteria

1. **Given** a function with missing Args, Returns, and Raises sections, **when** `scaffold_missing_sections()` runs on the file with the corresponding enrichment findings, **then** all three sections are scaffolded with parameter names from the signature and exception names from the body, using `[TODO: describe]` placeholders. Each scaffolded section produces a `scaffold` category finding with an actionable message (e.g. "fill in Args — describe parameters: data, timeout").

2. **Given** a function that already has an Args section but is missing Raises, **when** the scaffolding engine runs, **then** only the Raises section is added; existing Args content is preserved byte-for-byte.

3. **Given** a class with missing Attributes section (dataclass/NamedTuple/TypedDict), **when** the scaffolding engine runs, **then** an Attributes section is scaffolded listing all fields from the class definition.

4. **Given** a generator function missing Yields and Receives sections, **when** the scaffolding engine runs, **then** both sections are scaffolded with `[TODO: describe]` placeholders.

5. **Given** a symbol missing an Examples section (and `require_examples` config matches its type), **when** the scaffolding engine runs, **then** an Examples section is scaffolded with a fenced code block placeholder. A `scaffold` finding is produced: "fill in Examples section".

6. **Given** the scaffolding engine produces output, **when** the same input is processed, **then** output is deterministic (same input = same output, always).

7. **Given** the scaffolding engine has already run on a file, **when** it runs again on the same file, **then** no changes are made (idempotent).

8. **Given** a file with mixed symbols -- some needing fixes, some already complete, **when** the scaffolding engine runs, **then** only symbols with missing sections are modified; complete symbols are untouched.

9. **Given** `scaffold_missing_sections()` has scaffolded missing sections in a file, **when** `docvet check` runs enrichment on that file, **then** the original missing-section findings (e.g. `missing-raises`) are gone, replaced by `scaffold-incomplete` findings for each `[TODO: describe]` marker. Scaffold findings use the `scaffold` category and block CI (non-zero exit when enrichment is in `fail-on`).

10. **Given** the scaffolding engine produces findings, **when** findings are generated, **then** each scaffold finding uses the `scaffold` category on the Finding dataclass, with the `scaffold-incomplete` rule name, and a message format: "fill in [Section] for '[symbol]' — describe [items]" where [items] are the specific parameters, exceptions, or fields that need descriptions.

## Tasks / Subtasks

- [x] Task 1: Extend Finding dataclass with `"scaffold"` category (AC: 9, 10)
  - [x] 1.1 Add `"scaffold"` to `category: Literal["required", "recommended", "scaffold"]` in `src/docvet/checks/_finding.py`
  - [x] 1.2 Update `_CATEGORY_TO_SEVERITY` mapping in `src/docvet/reporting.py` — scaffold maps to `"medium"` severity
  - [x] 1.3 Update terminal output color for scaffold category (use CYAN to distinguish from RED/required and YELLOW/recommended)
  - [x] 1.4 Update summary count format to include scaffold: `"N findings (X required, Y recommended, Z scaffold)"`
  - [x] 1.5 Update markdown report to include scaffold findings section
  - [x] 1.6 Unit tests: Finding with `category="scaffold"` constructs correctly, reporting renders scaffold findings

- [x] Task 2: Implement production `scaffold_missing_sections()` (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [x] 2.1 Create `src/docvet/checks/fix.py` with `scaffold_missing_sections(source: str, tree: ast.Module, findings: list[Finding]) -> str`
  - [x] 2.2 Implement canonical section order constant `SECTION_ORDER` and `RULE_TO_SECTION` mapping
  - [x] 2.3 Implement `_detect_indent()` — closing `"""` line indentation for multi-line, opening line for one-liners
  - [x] 2.4 Implement one-liner expansion: `"""Summary."""` → multi-line with sections
  - [x] 2.5 Implement multi-line insertion: scaffold lines before closing `"""` with blank-line handling
  - [x] 2.6 Implement section-specific placeholder enrichment via AST re-extraction (NOT message parsing — consensus decision). Import `_extract_raised_exceptions()` from `enrichment._forward`, `_extract_fields_from_class()` from `enrichment._class_module`, and use `node.returns` / `ast.unparse()` for return types. For each symbol with findings, re-extract specifics from the AST node directly.
  - [x] 2.7 Implement Examples section placeholder as fenced code block: `Examples:\n    >>> # [TODO: add example usage]`
  - [x] 2.8 Implement Attributes section with field names extracted from dataclass/NamedTuple/TypedDict class body via AST
  - [x] 2.9 Implement reverse-order processing (highest line number first) to preserve line numbers during multi-symbol insertion
  - [x] 2.10 Implement existing section detection for idempotency — skip sections already present
  - [x] 2.11 Handle quote style detection and preservation (`"""`, `'''`, `r"""`)
  - [x] 2.12 Handle newline style detection and preservation (`\n`, `\r\n`)
  - [x] 2.13 Unit tests: all 14 POC scenarios + section-specific enrichment (AST-extracted names) + Examples fenced code block + Attributes field extraction + empty findings + mixed symbols (~30 tests)

- [x] Task 3: Implement `scaffold-incomplete` enrichment rule (AC: 9, 10)
  - [x] 3.1 Add `_check_scaffold_incomplete()` function in `src/docvet/checks/enrichment/_late_rules.py` — detect `[TODO: ` markers in docstring content via simple regex `r'\[TODO: [^\]]+\]'` (party-mode consensus: full-docstring scan, no section-scoped detection — fix any false positives in own codebase per dogfooding convention)
  - [x] 3.2 Add `scaffold_incomplete: bool` field to `EnrichmentConfig` (default: `True`)
  - [x] 3.3 Register in `_RULE_DISPATCH` table in enrichment `__init__.py`
  - [x] 3.4 Produce `scaffold` category findings with rule name `scaffold-incomplete` and actionable message format
  - [x] 3.5 Parse section context from surrounding text to generate specific messages (e.g. "fill in Raises for 'validate' — describe ValueError")
  - [x] 3.6 Unit tests: detection of TODO markers, no false positives on real content, actionable message format, config disable

- [x] Task 4: Integration verification (AC: 1-10)
  - [x] 4.1 Integration test: enrichment finds missing-raises → scaffold_missing_sections inserts Raises → enrichment re-check finds scaffold-incomplete instead
  - [x] 4.2 Integration test: scaffold-incomplete findings have correct category, rule, message format
  - [x] 4.3 Integration test: complete roundtrip — missing sections → scaffold → fill in → zero findings
  - [x] 4.4 Verify JSON output includes scaffold category correctly
  - [x] 4.5 Run `docvet check --all` on own codebase — zero scaffold findings (no placeholders in production code)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | test_fix::TestOnelinerExpansion::test_oneliner_raises, test_oneliner_multiple_sections; TestSectionSpecificEnrichment::test_raises_with_multiple_exceptions, test_returns_with_annotation | PASS |
| 2 | test_fix::TestMultilineInsertion::test_existing_args_preserved_adds_raises, test_multiple_existing_sections_preserved | PASS |
| 3 | test_fix::TestClassAttributes::test_dataclass_attributes, test_namedtuple_attributes; TestEdgeCases::test_dataclass_with_decorator | PASS |
| 4 | test_fix::TestGeneratorSections::test_yields_and_receives | PASS |
| 5 | test_fix::TestExamplesSection::test_examples_fenced_code_placeholder | PASS |
| 6 | test_fix::TestDeterminism::test_deterministic_output | PASS |
| 7 | test_fix::TestIdempotency::test_second_run_no_changes, test_existing_section_not_duplicated | PASS |
| 8 | test_fix::TestMixedSymbols::test_complete_symbol_untouched | PASS |
| 9 | test_scaffold_roundtrip::TestEnrichmentToScaffoldRoundtrip::test_missing_raises_becomes_scaffold_incomplete, test_complete_roundtrip_zero_findings | PASS |
| 10 | test_scaffold_roundtrip::TestScaffoldFindingFormat::test_scaffold_finding_attributes, test_json_output_scaffold_category; test_scaffold_incomplete::TestMessageFormat | PASS |

## Dev Notes

- **Interaction Risk:** The `scaffold-incomplete` rule is added to the enrichment module alongside 19 existing rules. It operates on a different detection mechanism (regex for `[TODO: describe]` markers vs AST analysis for missing sections). Verify that `scaffold-incomplete` findings do NOT fire on symbols without `[TODO: describe]` markers. Verify existing rules are unaffected by running the full enrichment suite on `complete_module.py` fixture.
- **Production function signature differs from POC:** POC takes `source: str, findings: list[dict]`. Production takes `source: str, tree: ast.Module, findings: list[Finding]` — the tree is passed in to avoid double-parsing (POC parsed internally). Use `Finding` objects directly, not dicts.
- **Section-specific placeholder enrichment (party-mode consensus: option c — AST re-extraction):** Do NOT parse finding message strings for parameter/exception names. Instead, re-extract from the AST directly in `fix.py`. The tree is already available. Import extraction helpers from enrichment submodules (`_extract_raised_exceptions` from `_forward.py`, field extraction from `_class_module.py`). Cross-subpackage imports within `checks/` are acceptable — don't create a `_shared.py` abstraction prematurely. Expected output:
  - `missing-raises` → walk function body for `raise` statements → `Raises:\n    ValueError: [TODO: describe when this is raised]\n    TypeError: [TODO: describe when this is raised]`
  - `missing-returns` → inspect `node.returns` annotation → `Returns:\n    str: [TODO: describe return value]` (or generic `[TODO: describe]` if no annotation)
  - `missing-attributes` → extract fields from dataclass/NamedTuple/TypedDict class body → `Attributes:\n    host: [TODO: describe]\n    port: [TODO: describe]`
  - `missing-examples` → `Examples:\n    >>> # [TODO: add example usage]` (fenced doctest-style placeholder)
- **Config decision (spike M4):** Use the existing `fail_on` mechanism. Scaffold findings are enrichment findings. If `enrichment` is in `fail_on`, scaffold findings trigger exit code 1. No new top-level config key needed. The `scaffold_incomplete` boolean on `EnrichmentConfig` enables/disables the detection rule itself (not the exit behavior).
- **Canonical section order:** When inserting multiple sections, use Google-style canonical order: Args, Other Parameters, Returns, Yields, Receives, Raises, Warns, Attributes, Examples, See Also. This matches the POC's `SECTION_ORDER` constant and the enrichment module's `_SECTION_HEADERS`.
- **Module placement:** `src/docvet/checks/fix.py` for the scaffolding engine (new module). The `scaffold-incomplete` rule goes in `src/docvet/checks/enrichment/_late_rules.py` alongside other finishing rules. The `fix.py` module should export `scaffold_missing_sections` via `src/docvet/checks/__init__.py`.
- **Edge cases from spike (section 3.2):** Production should handle: closing `"""` on same line as content (split and reformat), empty docstrings (`"""  """`), and docstrings with only whitespace. These are rare but the POC documented them as unhandled. The 7 known edge cases are in the spike decision doc section 3.2.

### Project Structure Notes

- New file: `src/docvet/checks/fix.py` — scaffolding engine (~150-200 lines estimated)
- Modified: `src/docvet/checks/_finding.py` — extend category Literal
- Modified: `src/docvet/checks/enrichment/_late_rules.py` — add `_check_scaffold_incomplete()`
- Modified: `src/docvet/checks/enrichment/__init__.py` — register new rule in `_RULE_DISPATCH`
- Modified: `src/docvet/config/__init__.py` — add `scaffold_incomplete` to `EnrichmentConfig`
- Modified: `src/docvet/reporting.py` — update category mappings, colors, summary format
- Modified: `src/docvet/checks/__init__.py` — re-export `scaffold_missing_sections`
- New tests: `tests/unit/checks/test_fix.py`, `tests/unit/checks/test_scaffold_incomplete.py`
- Alignment with existing structure: follows the enrichment sub-package pattern for the new rule; the fix module is a peer to other check modules in `checks/`

### References

- [Source: _bmad-output/implementation-artifacts/32-1-spike-decision.md] — Insertion strategy evaluation, POC code, edge case catalog, scaffold category design
- [Source: _bmad-output/implementation-artifacts/32-1-fix-feasibility-spike.md] — Forward-carry notes, 14 POC test scenarios
- [Source: _bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md#Story 32.2] — Acceptance criteria, epic context
- [Source: src/docvet/checks/_finding.py] — Current Finding dataclass (category: Literal["required", "recommended"])
- [Source: src/docvet/checks/enrichment/__init__.py] — _RULE_DISPATCH table, _SECTION_PATTERN, _parse_sections(), check_enrichment() orchestrator
- [Source: src/docvet/checks/enrichment/_late_rules.py] — Late rules pattern (trivial docstring, return type, init params)
- [Source: src/docvet/ast_utils.py] — get_docstring_range(), Symbol dataclass with docstring_range
- [Source: src/docvet/reporting.py] — _CATEGORY_TO_SEVERITY mapping, terminal/markdown/JSON output
- [Source: src/docvet/config/__init__.py] — DocvetConfig.fail_on, EnrichmentConfig fields

### Documentation Impact

- Pages: docs/site/checks/enrichment.md, docs/site/rules/scaffold-incomplete.md (new), docs/site/configuration.md, docs/site/cli-reference.md
- Nature of update: Add scaffold-incomplete rule documentation to enrichment check page; create new rule reference page for scaffold-incomplete; add `scaffold_incomplete` config key to enrichment configuration reference table; document new `scaffold` category in CLI output format (summary line now shows scaffold count)

### Test Maturity Piggyback

No test-review.md found — run `/bmad-tea-testarch-test-review` to establish baseline.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1711 passed, zero regressions
- [x] `uv run docvet check --all` — zero findings, 100% coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- All 1711 tests pass (1660 existing + 51 new)
- All 5 quality gates green
- Dogfooding: zero findings on own codebase after fixing false positives in docstrings referencing TODO marker syntax

### Completion Notes List

- Task 1: Extended Finding.category Literal to include "scaffold". Updated reporting: _COLORS (CYAN), _CATEGORY_TO_SEVERITY ("medium"), terminal/markdown/JSON summary counts, format_summary. 11 new tests.
- Task 2: Created `src/docvet/checks/fix.py` (394 lines). Production `scaffold_missing_sections()` with AST re-extraction for section-specific placeholders (exception names, return types, class fields). Handles one-liner expansion, multi-line insertion, quote/newline preservation, reverse-order processing, idempotency. 26 unit tests.
- Task 3: Added `_check_scaffold_incomplete()` in `_late_rules.py`. Regex `[TODO: ...]` detection with section-context extraction for actionable messages. Config field `scaffold_incomplete: bool = True`. 10 unit tests.
- Task 4: Integration tests for full roundtrip (enrichment → scaffold → re-check → fill → zero findings). JSON output verification. Dogfooding on own codebase. 4 integration tests.
- Fixed 2 false positives in own codebase (docstrings that referenced `[TODO: ...]` syntax literally).

### Change Log

- 2026-03-23: Implemented scaffold category, scaffolding engine, scaffold-incomplete rule, integration tests. All quality gates pass.

### File List

- `src/docvet/checks/fix.py` (new) — Section scaffolding engine
- `src/docvet/checks/_finding.py` (modified) — Added "scaffold" to category Literal
- `src/docvet/checks/__init__.py` (modified) — Re-export scaffold_missing_sections
- `src/docvet/checks/enrichment/__init__.py` (modified) — Register scaffold-incomplete in _RULE_DISPATCH
- `src/docvet/checks/enrichment/_late_rules.py` (modified) — _check_scaffold_incomplete() function
- `src/docvet/config/__init__.py` (modified) — scaffold_incomplete field on EnrichmentConfig
- `src/docvet/reporting.py` (modified) — scaffold category in colors, severity, summary counts, JSON
- `tests/conftest.py` (modified) — Updated _Category type alias
- `tests/unit/checks/test_finding.py` (modified) — test_finding_accepts_scaffold_category
- `tests/unit/checks/test_fix.py` (new) — 26 unit tests for scaffolding engine
- `tests/unit/checks/test_scaffold_incomplete.py` (new) — 10 unit tests for scaffold-incomplete rule
- `tests/unit/test_reporting.py` (modified) — TestScaffoldCategory (11 tests)
- `tests/unit/test_exports.py` (modified) — Updated __all__ expectations
- `tests/integration/test_scaffold_roundtrip.py` (new) — 4 integration tests
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Story status updates

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
