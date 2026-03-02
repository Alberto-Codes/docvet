---
title: 'Fix prefer-fenced-code-blocks to detect :: indented code blocks'
slug: '225-fix-rst-indented-block-detection'
created: '2026-03-01'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python', 'ast', 'regex']
files_to_modify:
  - 'src/docvet/checks/enrichment.py'
  - 'tests/unit/checks/test_enrichment.py'
  - 'src/docvet/__init__.py'
  - 'src/docvet/ast_utils.py'
  - 'src/docvet/cli.py'
  - 'src/docvet/config.py'
  - 'src/docvet/discovery.py'
  - 'src/docvet/lsp.py'
  - 'src/docvet/reporting.py'
  - 'src/docvet/checks/_finding.py'
  - 'src/docvet/checks/coverage.py'
  - 'src/docvet/checks/freshness.py'
  - 'src/docvet/checks/griffe_compat.py'
  - 'docs/main.py'
  - 'docs/site/rules/prefer-fenced-code-blocks.md'
  - 'docs/rules.yml'
  - 'docs/site/checks/enrichment.md'
  - 'docs/site/configuration.md'
code_patterns:
  - 'table-driven dispatch via _RULE_DISPATCH'
  - 'helper extraction for CC control'
  - '_extract_section_content for section scoping'
test_patterns:
  - 'source factory fixtures in conftest.py'
  - 'one test file per check module'
  - 'assert all Finding fields'
  - 'module-level symbol: inline [s for s in symbols if s.kind == "module"][0] pattern (no helper)'
---

# Tech-Spec: Fix `prefer-fenced-code-blocks` to detect `::` indented code blocks

**Created:** 2026-03-01

## Overview

### Problem Statement

The `prefer-fenced-code-blocks` rule (enrichment check) only detects `>>>` doctest patterns via `_DOCTEST_PATTERN = re.compile(r"^\s*>>>")`. It completely misses reStructuredText `::` indented code blocks in `Examples:` sections.

This is a genuine rendering gap — not a style preference. Research confirmed:
- **mkdocstrings** only supports rST field lists (`:param:`, `:returns:`), not full rST markup like `::` directives
- **Material for MkDocs** provides no syntax highlighting, copy button, or annotations for indented code blocks — its code blocks reference is entirely fenced-block oriented
- **Griffe** recommends fenced code blocks and only auto-parses `>>>` in Examples sections

Result: `::` blocks in docstrings rendered through mkdocs-material + mkdocstrings produce unstyled monospace text with no syntax highlighting, no copy button, and no annotations. The `::` literal may even render as visible text.

Docvet's own codebase has **22 instances** across 13 source files — all inside `Examples:` sections — that pass silently.

### Solution

Extend the existing `_check_prefer_fenced_code_blocks` function with a second regex pattern (`_RST_BLOCK_PATTERN`) and a forward-scan indentation verification helper. Convert all 22 `::` instances in own codebase to fenced code blocks. Update 4 docs pages. Deliver atomically (pre-commit hook `docvet check --staged` enforces all-or-nothing).

### Scope

**In Scope:**
- Add `_RST_BLOCK_PATTERN` regex and `_has_rst_indented_block` helper to `enrichment.py`
- Extend `_check_prefer_fenced_code_blocks` to detect `::` alongside `>>>`
- Emit a distinct Finding message for `::` vs `>>>`
- Unit tests: positive, negative, edge cases for `::` detection
- Convert all 22 `::` instances across 13 source files to fenced code blocks (includes `docs/main.py`)
- Update `_check_prefer_fenced_code_blocks` docstring to mention `::` alongside `>>>`
- Update 4 docs pages: rule page, rules.yml, enrichment check page, configuration page

**Out of Scope:**
- New rule creation (extending existing rule)
- New docs pages (updating existing pages only)
- `::` detection outside `Examples:` sections (all 22 instances are inside Examples, zero outside)
- Config schema changes (same rule name, same toggle)
- Detection of `::` inside fenced code block content (documented limitation)

## Context for Development

### Codebase Patterns

- Table-driven dispatch: `_RULE_DISPATCH` in `enrichment.py:1256+` maps config keys to check functions. No change needed — same function, same entry.
- Section extraction: `_extract_section_content(symbol.docstring, "Examples")` at `enrichment.py:1232` scopes the scan to `Examples:` content only.
- Helper extraction pattern: used throughout enrichment.py to keep check function CC under 15 (e.g., `_SYMBOL_KIND_DISPLAY`, `_extract_section_content`).
- Finding dataclass: all 6 fields (`file`, `line`, `symbol`, `rule`, `message`, `category`) must be populated.
- Pre-commit constraint: `docvet check --staged` runs on every commit. The rule implementation and all docstring conversions must land together.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/checks/enrichment.py:1195-1252` | Current `_check_prefer_fenced_code_blocks` implementation |
| `src/docvet/checks/enrichment.py:1112-1117` | `_SYMBOL_KIND_DISPLAY` map (has `"module"` — no change needed) |
| `src/docvet/checks/enrichment.py:100-132` | `_extract_section_content` — preserves original indentation |
| `src/docvet/checks/enrichment.py:1256-1275` | `_RULE_DISPATCH` table (no change needed) |
| `tests/unit/checks/test_enrichment.py:3750-3930` | Existing `_check_prefer_fenced_code_blocks` tests (8 tests) |
| `tests/unit/checks/test_enrichment.py:262-273` | `_make_symbol_and_index` helper — filters OUT module symbols |
| `docs/site/rules/prefer-fenced-code-blocks.md` | Rule page: macros + static "What it detects", example tabs |
| `docs/rules.yml:150-167` | YAML catalog: `summary` + `fix` fields (feed macros) |
| `docs/site/checks/enrichment.md:22` | Enrichment check page rule table row |
| `docs/site/configuration.md:129` | Configuration page rule description |
| `docs/main.py:40-98` | Macros: `rule_header()` renders summary, `rule_fix()` renders fix |

### Technical Decisions

1. **Extend, don't split**: Single rule covers both `>>>` and `::` — same intent (prefer fenced blocks), same config toggle.
2. **`Examples:` scope only**: All 22 codebase instances are inside `Examples:` sections. Zero instances outside. No practical benefit to expanding.
3. **Two-step detection for `::` **: Match `line.rstrip().endswith("::")` then verify next non-blank line has greater indentation **relative to the `::` line's own indent** (not absolute column 0). `_extract_section_content` preserves original docstring indentation, so relative comparison is required.
4. **Helper extraction**: `_has_rst_indented_block(lines, index)` keeps the main check function's CC unchanged.
5. **Detection order**: Scan for `>>>` first (existing loop), then `::` second. Return on first match — one Finding per symbol. This preserves backward compatibility: any docstring that currently triggers `>>>` detection continues to produce the same Finding.
6. **Distinct messages**: `::` findings say "uses reStructuredText indented code block (::)" vs existing "uses doctest format (>>>)".
7. **Language markers for conversions**: CLI examples (`$ docvet ...`) get ```` ```bash ````, Python import/API examples get ```` ```python ````, YAML config snippets get ```` ```yaml ````, Jinja2 template syntax get ```` ```jinja2 ````.
8. **Module-level symbols supported**: `_SYMBOL_KIND_DISPLAY` has `"module": "module"` entry (`enrichment.py:1116`). Message generation works for all symbol kinds.
9. **Docs macros pull from YAML**: `rule_header()` renders `rules.yml` `summary` field. `rule_fix()` renders `rules.yml` `fix` field. No hardcoded text in `docs/main.py` macros. Static markdown sections ("What it detects", "Why is this a problem?", example tabs) in the rule page need manual update.

## Implementation Plan

### Tasks

- [ ] Task 1: Add `_RST_BLOCK_PATTERN` regex and `_has_rst_indented_block` helper
  - File: `src/docvet/checks/enrichment.py`
  - Action: Add `_RST_BLOCK_PATTERN = re.compile(r"::\s*$")` near `_DOCTEST_PATTERN` (line ~1198). **Use `.search()` (not `.match()`)** for this pattern — unlike `_DOCTEST_PATTERN` which has `^\s*` prefix for `.match()`, `_RST_BLOCK_PATTERN` has no start anchor, so `.match()` would fail on lines with leading text/whitespace. Add `_has_rst_indented_block(lines: list[str], index: int) -> bool` helper that: (a) gets the indent level of `lines[index]` (the `::` line), (b) scans forward from `index + 1` skipping blank lines, (c) returns `True` if the first non-blank line has strictly greater indentation than the `::` line, `False` otherwise (including if no non-blank line follows).

- [ ] Task 2: Extend `_check_prefer_fenced_code_blocks` to detect `::` blocks
  - File: `src/docvet/checks/enrichment.py`
  - Action: After the existing `>>>` for-loop (lines 1238-1250), add a second scan: split content into lines, enumerate them, use `_RST_BLOCK_PATTERN.search(line)` to detect `::` (must be `.search()`, not `.match()`), call `_has_rst_indented_block` to confirm. If confirmed, return a Finding with message `f"Examples: section in {kind_display} '{symbol.name}' uses reStructuredText indented code block (::) instead of fenced code blocks"` and `category="recommended"`. Preserve existing behavior: `>>>` detection first, `::` second, return on first match.

- [ ] Task 3: Update `_check_prefer_fenced_code_blocks` docstring
  - File: `src/docvet/checks/enrichment.py`
  - Action: Update the function docstring (lines 1208-1225) to mention `::` detection alongside `>>>`. Update the summary line, the description body, and the Returns section to reference both patterns.

- [ ] Task 4: Write unit tests for `::` detection
  - File: `tests/unit/checks/test_enrichment.py`
  - Action: Add the following tests after the existing `_check_prefer_fenced_code_blocks` test block (after line ~3930):
    - `test_fenced_blocks_when_rst_indented_block_returns_finding` — class docstring with `Typical usage::` + indented code in Examples. Assert Finding with `rule="prefer-fenced-code-blocks"`, `category="recommended"`, `"::"` in message.
    - `test_fenced_blocks_when_rst_no_indented_follow_returns_none` — `::` at end of line but next non-blank line has same or less indentation. Assert `None`. Fixture shape: `Examples:` section with `    Not a code block::` (4-space indent) followed by blank line then `    This is not indented more.` (also 4-space indent). Helper returns `False` because follow-on indent is not strictly greater.
    - `test_fenced_blocks_when_rst_trailing_whitespace_returns_finding` — `::` followed by trailing spaces (`::   `). Assert Finding fires.
    - `test_fenced_blocks_when_mixed_doctest_and_rst_returns_doctest_finding` — Examples with `>>>` before `::`. Assert Finding message contains `">>>"` (not `"::"`), confirming `>>>` takes precedence.
    - `test_fenced_blocks_when_module_rst_block_returns_finding` — Module-level docstring with `::` block. Use inline `[s for s in symbols if s.kind == "module"][0]` pattern. Assert Finding with `"module"` in message.
    - `test_fenced_blocks_when_bare_double_colon_line_with_indent_returns_finding` — Bare `::` on its own line followed by indented code. Assert Finding fires.
    - `test_fenced_blocks_when_rst_block_config_disabled_returns_no_finding` — Full orchestrator test with `prefer_fenced_code_blocks=False` and `::` block. Assert zero findings for this rule.
    - `test_fenced_blocks_when_rst_block_orchestrator_fires_when_enabled` — Full orchestrator test with `prefer_fenced_code_blocks=True` and `::` block. Assert exactly 1 finding.

- [ ] Task 5: Convert `::` docstrings in source files (13 files, 22 instances)
  - Files: `src/docvet/__init__.py` (2), `src/docvet/ast_utils.py` (1), `src/docvet/cli.py` (3), `src/docvet/config.py` (1), `src/docvet/discovery.py` (2), `src/docvet/lsp.py` (3), `src/docvet/reporting.py` (3), `src/docvet/checks/_finding.py` (1), `src/docvet/checks/coverage.py` (1), `src/docvet/checks/enrichment.py` (1), `src/docvet/checks/freshness.py` (1), `src/docvet/checks/griffe_compat.py` (1), `docs/main.py` (2)
  - Action: For each `::` instance: (a) remove `::` from the directive line (e.g., `Run all checks on changed files::` becomes `Run all checks on changed files:`), (b) replace the indented block with a fenced code block using the appropriate language marker — `bash` for CLI examples (`$ docvet ...`), `python` for import/API examples, `yaml` for YAML config snippets, `jinja2` for Jinja2 template syntax (e.g., `docs/main.py` line 13). (c) Verify indentation is consistent with surrounding docstring.

- [ ] Task 6: Update `docs/rules.yml`
  - File: `docs/rules.yml`
  - Action: Update line 155 `summary` to: `Examples section uses doctest (>>>) or reStructuredText (::) indented code blocks instead of fenced code blocks`. Update `fix` field (lines 157-166) to mention both `>>>` and `::` patterns with fix guidance for each.

- [ ] Task 7: Update rule reference page
  - File: `docs/site/rules/prefer-fenced-code-blocks.md`
  - Action: (a) Update "What it detects" to mention `::` alongside `>>>`. (b) Update "Why is this a problem?" if needed. (c) Add a second Violation/Fix example tab pair showing `::` indented block (Violation) converted to fenced block (Fix).

- [ ] Task 8: Update enrichment check page and configuration page
  - Files: `docs/site/checks/enrichment.md`, `docs/site/configuration.md`
  - Action: Update rule description in the table row (enrichment.md line 22, configuration.md line 129) to mention `::` alongside `>>>`.

- [ ] Task 9: Validate
  - Action: (a) Run `uv run pytest` — all tests pass. (b) Run `uv run ruff check .` and `uv run ruff format .` — no issues. (c) Run `docvet check --all` — zero findings (all `src/` `::` instances converted). (d) Run `docvet enrichment docs/main.py` — zero findings (`docs/main.py` is outside `src/` and not covered by `--all` discovery). (e) Run `mkdocs build --strict` — docs build clean. (f) Run `uv run ty check` — no type errors.

### Acceptance Criteria

- [ ] AC 1: Given a class docstring with an `Examples:` section containing `Typical usage::` followed by an indented code block, when `_check_prefer_fenced_code_blocks` runs, then a Finding is returned with `rule="prefer-fenced-code-blocks"`, `category="recommended"`, and `"::"` in the message.

- [ ] AC 2: Given a class docstring with an `Examples:` section containing `::` at end of line but the next non-blank line has equal or less indentation, when `_check_prefer_fenced_code_blocks` runs, then `None` is returned (no false positive).

- [ ] AC 3: Given a module-level docstring with an `Examples:` section containing `::` followed by an indented code block, when `_check_prefer_fenced_code_blocks` runs, then a Finding is returned with `"module"` in the message.

- [ ] AC 4: Given a docstring with both `>>>` and `::` patterns in the `Examples:` section (with `>>>` appearing first), when `_check_prefer_fenced_code_blocks` runs, then the Finding message contains `">>>"` and not `"::"` (precedence preserved).

- [ ] AC 5: Given `EnrichmentConfig(prefer_fenced_code_blocks=False)` and a docstring with `::` indented blocks, when `check_enrichment` runs, then zero findings with `rule="prefer-fenced-code-blocks"` are returned.

- [ ] AC 6: Given the docvet codebase with all 22 `::` instances converted to fenced code blocks, when `docvet check --all` runs, then zero `prefer-fenced-code-blocks` findings are reported.

- [ ] AC 7: Given the updated docs pages, when `mkdocs build --strict` runs, then the build succeeds with no warnings.

## Additional Context

### Dependencies

- No new dependencies. Regex and string operations only (stdlib).
- No config schema changes — existing `prefer-fenced-code-blocks` bool toggle covers both patterns.

### Testing Strategy

- **Unit tests (positive)**: Fixture with `::` + indented block inside `Examples:` section, assert Finding emitted with correct rule, message, and category.
- **Unit tests (negative)**: `::` at end of line followed by non-indented line — must NOT fire.
- **Unit tests (edge cases)**: `::` with trailing whitespace, bare `::` on own line, mixed `>>>` and `::` in same docstring (assert `>>>` fires first), `::` preceded by text (`Typical usage::`).
- **Unit tests (module-level)**: Module-level docstring with `::` block, using established inline pattern `[s for s in symbols if s.kind == "module"][0]`. Assert Finding message includes "module" kind display.
- **Dogfood validation**: After fix, `docvet enrichment --all` must fire on own codebase (pre-conversion) and produce zero findings (post-conversion).
- **Docs validation**: `mkdocs build --strict` passes after docs updates.

### Gaps Identified and Resolved (Step 2)

| # | Gap | Resolution |
|---|-----|-----------|
| 1 | Indentation comparison | Relative to `::` line's indent, not absolute. Specified in Technical Decision #3. |
| 2 | Detection order | `>>>` first, `::` second, return first match. Specified in Technical Decision #5. |
| 3 | Module-level test fixture | No new helper needed. Inline `[s for s in symbols if s.kind == "module"][0]` pattern used 20+ times in test file. |
| 4 | `_SYMBOL_KIND_DISPLAY` for module | Confirmed: `"module": "module"` at `enrichment.py:1116`. |
| 5 | Macro tracing | `rule_header()` and `rule_fix()` both pull from `rules.yml` — no hardcoded text. Static sections in rule `.md` need manual update. |
| 6 | Frontmatter duplicate | Fixed in Step 1 revision. |

### Notes

**High-Risk Items:**
- Docstring conversions (Task 5) are the highest-risk task — 22 manual edits across 13 files where incorrect indentation or wrong language marker could break docstring parsing or rendered output. Mitigated by dogfood validation (Task 9c) and docs build (Task 9d).
- CC budget: the helper extraction (Task 1) is designed to keep `_check_prefer_fenced_code_blocks` CC unchanged. Verify with `analyze_code_snippet` after Task 2.

**Known Limitations:**
- `::` inside a fenced code block's content would false-positive if it appears in `Examples:` section text (documented out-of-scope — same behavior as existing `>>>` inside fenced blocks per test at line 3908).
- Rule only scans `Examples:` sections. `::` in other docstring sections (Args preamble, module description) is not detected. All 22 known instances are in `Examples:` so this is acceptable.
- **`>>>` masks `::` detection**: If a docstring's `Examples:` section contains both `>>>` and `::` patterns, only `>>>` is reported (detection order per Technical Decision #5). A `::` block in the same section will not be flagged until the `>>>` is fixed. This is by design to preserve backward compatibility, but users may be surprised if they fix `>>>` and a new `::` finding appears.

**References:**
- GitHub Issue: #225
- Party mode consensus: four sessions confirmed approach, scope, delivery constraint, and identified + resolved 6 gaps
- Research sources: Griffe docs, mkdocstrings#278, Material for MkDocs code blocks reference, mkdocs#282
- Pre-commit makes this atomic — rule impl + all 22 docstring conversions + docs updates must land in one PR
