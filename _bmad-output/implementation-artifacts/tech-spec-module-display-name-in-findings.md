---
title: 'Replace <module> sentinel with Python module display names in findings'
slug: 'module-display-name-in-findings'
created: '2026-03-07'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python', 'ast']
files_to_modify: ['src/docvet/ast_utils.py', 'src/docvet/checks/enrichment.py', 'src/docvet/checks/presence.py', 'src/docvet/checks/freshness.py', 'src/docvet/checks/coverage.py']
code_patterns: ['module_display_name helper', 'Finding symbol field', 'Finding message field']
test_patterns: ['unit tests for helper edge cases', 'assertion updates for <module> sentinel']
---

# Tech-Spec: Replace `<module>` sentinel with Python module display names in findings

**Created:** 2026-03-07

## Overview

### Problem Statement

Module-level findings use the AST sentinel `<module>` in both the `symbol` field and `message` text of Finding records. In CI logs and GitHub Actions step summaries, this produces dozens of identical, untriageable lines like `Module '<module>' has no See Also: section` with no indication of which file is affected. The `file=` parameter in `::warning` annotations places findings on the correct file in the PR diff, but the message text itself is useless — especially in the log view where file context is absent, and in the step summary table where all module findings look identical.

This was shipped in v1.0.0 and remains unfixed on `main` as of v1.0.2.

### Solution

Add a `module_display_name(file_path)` helper to `ast_utils.py` that converts file paths to dotted Python module names (e.g., `src/gepa_adk/config.py` -> `gepa_adk.config`). Use it in all four check modules for both the `symbol` and `message` fields on module-kind findings, replacing the `<module>` sentinel with a human-readable, Python-native identifier.

### Scope

**In Scope:**

- New `module_display_name(file_path: str) -> str` public helper in `ast_utils.py`
- Update all module-kind `symbol=` fields in enrichment (8 callsites: 3 module-branched + 5 generic), presence (1), freshness (1 in `_build_finding`), coverage (1)
- Update all module-kind `message=` templates in enrichment (8 sites: 3 module-branched + 5 generic — same sites as `symbol=`), presence (1), and freshness (3 caller sites: diff mode, drift mode, age mode)
- Unit tests for the helper (edge cases: `src/` prefix, no prefix, `__init__.py`, nested packages, `lib/` prefix, flat scripts)
- Update 23 existing test assertions across 5 test files that match `"<module>"` or old message text
- Add 1 new test: module-level freshness finding asserts display name in `symbol` and `message` fields (no existing tests cover this path)

**Out of Scope:**

- `ast_utils.py` Symbol constructor (`name="<module>"` stays — AST layer remains pure)
- `action.yml` changes (annotation format is correct, only message text was broken)
- New CLI flags or config options
- Coverage message text (already uses directory path, not `symbol.name`)
- `griffe_compat.py` — uses `obj.name` from griffe's own parser which provides real module names, not `<module>`

## Context for Development

### Codebase Patterns

- Finding messages follow the pattern `{Kind} '{name}' has no {section} section` — functions use the function name, classes use the class name, modules should use the dotted module path
- All `_check_*` functions in enrichment receive `file_path: str` as their last parameter — the data needed for conversion is already available at every callsite
- `presence.py` and `freshness.py` also receive `file_path` at their check function level
- `coverage.py` hardcodes `symbol="<module>"` directly in the Finding constructor; `representative` file path variable is available
- The `Symbol` dataclass in `ast_utils.py` is frozen — the `name="<module>"` value is set at construction and cannot be mutated; conversion must happen at the consumer (check) layer
- Enrichment has two categories of callsites: **module-branched** (guarded by `symbol.kind == "module"`) and **generic** (handle all kinds via `kind_display` lookup). Both need the fix — generic sites use a conditional: `module_display_name(file_path) if symbol.kind == "module" else symbol.name`
- Freshness builds messages at 3 caller sites then passes them to `_build_finding`; the `symbol=` fix goes in `_build_finding`, the `message=` fix goes in each caller
- `griffe_compat.py` uses `obj.name` from griffe's own parser — griffe provides real module names, not `<module>`, so no fix needed

### Callsite Map

**Enrichment (`enrichment.py`) — 8 `symbol=` + 8 `message=` sites:**

| Lines | Rule | Kind guard | Notes |
|-------|------|-----------|-------|
| 926-933 | `missing-attributes` | `symbol.kind == "module"` + `_is_init_module` | Module-branched |
| 1063-1070 | `missing-examples` | `symbol.kind == "module"` | Module-branched |
| 1159-1166 | `missing-cross-references` Branch A | `symbol.kind == "module"` | Module-branched |
| 1185-1195 | `missing-cross-references` Branch B | Any kind | Generic — uses `kind_display` |
| 1275-1285 | `prefer-fenced-code-blocks` (doctest) | Any kind | Generic — uses `kind_display` |
| 1289-1300 | `prefer-fenced-code-blocks` (RST) | Any kind | Generic — uses `kind_display` |
| 1342-1353 | `prefer-fenced-code-blocks` extra (RST) | Any kind | Generic — uses `kind_display` |
| 1358-1368 | `prefer-fenced-code-blocks` extra (doctest) | Any kind | Generic — uses `kind_display` |

**Presence (`presence.py`) — 1 `symbol=` + 1 `message=` site:**

| Lines | Notes |
|-------|-------|
| 144-157 | Message is `"Module has no docstring"` (doesn't use `symbol.name`); update to include display name. `symbol=symbol.name` needs fix. |

**Freshness (`freshness.py`) — 1 `symbol=` + 3 `message=` sites:**

| Lines | Rule | Notes |
|-------|------|-------|
| 77-84 | `_build_finding` helper | `symbol=symbol.name` — fix with conditional |
| 244-247 | `stale-docstring` (diff mode) | Message: `f"{kind} '{symbol.name}' {classification} changed..."` |
| 439-443 | `stale-drift` | Message: `f"{kind} '{sym.name}' code modified..."` |
| 467-468 | `stale-age` | Message: `f"{kind} '{sym.name}' docstring untouched..."` |

**Coverage (`coverage.py`) — 1 `symbol=` site:**

| Lines | Notes |
|-------|-------|
| 104-111 | Hardcoded `symbol="<module>"` — replace with `module_display_name(representative)` |

### Test Assertion Map

| Category | File | Count | Action |
|----------|------|-------|--------|
| STAYS | `test_ast_utils.py` (lines 160, 185) | 2 | No change — AST layer |
| STAYS | `test_freshness.py` (line 513) | 1 | No change — Symbol fixture |
| UPDATE | `test_enrichment.py` (symbol assertions) | 6 | Change expected from `"<module>"` to `"regular"` or `"__init__"` |
| UPDATE | `test_enrichment.py` (message assertions) | 5 | Change `"Module '<module>'"` to `"Module 'regular'"` etc. |
| UPDATE | `test_presence.py` (symbol filters) | 6 | Change filter from `f.symbol == "<module>"` to derived name |
| UPDATE | `test_coverage.py` (symbol assertions) | 2 | Change expected to derived name |
| UPDATE | `test_cli.py` (Finding fixtures + assertions) | 4 | Change `symbol="<module>"` to derived name |
| ADD | `test_freshness.py` | 1 | New test: module-level freshness finding |
| **Total** | | **27** | 3 stays, 23 updates, 1 new + generic-rule module tests |

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/ast_utils.py` | Home for new `module_display_name()` helper, alongside `Symbol` dataclass |
| `src/docvet/checks/enrichment.py` | 8 `symbol=` + 8 `message=` sites (3 module-branched + 5 generic) |
| `src/docvet/checks/presence.py` | 1 `symbol=` + 1 `message=` site (line 144-157) |
| `src/docvet/checks/freshness.py` | 1 `symbol=` in `_build_finding` (line 80) + 3 caller messages (lines 245, 440, 467) |
| `src/docvet/checks/coverage.py` | 1 hardcoded `symbol="<module>"` (line 107) |
| `src/docvet/checks/griffe_compat.py` | Uses `obj.name` from griffe — already correct, no changes |
| `src/docvet/checks/_finding.py` | Finding dataclass — no changes needed |

### Technical Decisions

- **Helper location**: `ast_utils.py` — it's the "symbol identity" module. The function extends that identity to file-path-derived names. All four check modules already import from `ast_utils`.
- **Public function**: `module_display_name` (no underscore) since it's consumed cross-module.
- **AST layer unchanged**: `Symbol.name` stays `"<module>"` at construction. The display name conversion happens at the check layer where `file_path` is available.
- **Conversion logic**: Normalize backslashes → find source root marker via `rfind("/src/")` or `rfind("/lib/")` for absolute paths, fall back to `startswith("src/")` / `startswith("lib/")` for relative paths → drop `.py` extension → replace `/` with `.` → collapse trailing `.__init__` to package name. Guard: return `"<module>"` on empty string input.
- **Generic callsite pattern**: For sites that handle all symbol kinds, use `display_name = module_display_name(file_path) if symbol.kind == "module" else symbol.name` to avoid changing non-module behavior.
- **Freshness pattern**: Fix `symbol=` inside `_build_finding` (single point), fix messages at each of the 3 caller sites.
- **Coverage pattern**: Use `dir_rel.replace("/", ".")` for the `symbol` field — coverage findings are directory-level (missing `__init__.py`), not module-level. `dir_rel` is already computed (e.g., `"pkg/sub"` → `"pkg.sub"`). Semantically correct: the symbol represents the package that's broken, not a specific file.

## Implementation Plan

### Tasks

- [x] Task 1: Add `module_display_name()` helper to `ast_utils.py`
  - File: `src/docvet/ast_utils.py`
  - Action: Add a public function after the `get_documented_symbols()` function. Logic: (1) return `"<module>"` if input is empty string, (2) normalize backslashes to forward slashes, (3) find source root marker via `rfind("/src/")` or `rfind("/lib/")` for absolute paths — strip everything up to and including the marker; fall back to `startswith("src/")` / `startswith("lib/")` for relative paths, (4) drop `.py` extension, (5) replace `/` with `.`, (6) collapse trailing `.__init__` to package name. Add Google-style docstring with Args, Returns, Examples.
  - Notes: Public (no underscore) — consumed by enrichment, presence, freshness, coverage. Backslash normalization is needed because `cli.py` passes `str(file_path)` which uses OS-native separators on Windows. `discover_files()` returns **absolute** paths (e.g., `/home/user/project/src/pkg/mod.py`) so `rfind` is critical — a simple `startswith("src/")` would never match. No new imports required — pure string manipulation.

- [x] Task 2: Add unit tests for `module_display_name()`
  - File: `tests/unit/test_ast_utils.py`
  - Action: Add a new test class `TestModuleDisplayName` with edge-case tests:
    - `"src/pkg/mod.py"` -> `"pkg.mod"` (relative with src/)
    - `"pkg/mod.py"` -> `"pkg.mod"` (no src/ prefix)
    - `"mod.py"` -> `"mod"` (flat script)
    - `"src/pkg/__init__.py"` -> `"pkg"` (init collapse)
    - `"__init__.py"` -> `"__init__"` (bare init, no parent)
    - `"lib/pkg/mod.py"` -> `"pkg.mod"` (lib prefix)
    - `"src/a/b/c.py"` -> `"a.b.c"` (deep nesting)
    - `"src/pkg/sub/__init__.py"` -> `"pkg.sub"` (nested init)
    - `"src\\pkg\\mod.py"` -> `"pkg.mod"` (Windows backslash path)
    - `"/home/user/project/src/pkg/mod.py"` -> `"pkg.mod"` (absolute path with /src/)
    - `"/opt/lib/pkg/mod.py"` -> `"pkg.mod"` (absolute path with /lib/)
    - `""` -> `"<module>"` (empty string guard)
    - `"Makefile"` -> `"Makefile"` (extensionless file, no .py)
  - Notes: Run tests after this task to confirm helper works before touching check modules.

- [x] Task 3: Update enrichment module-branched callsites
  - File: `src/docvet/checks/enrichment.py`
  - Action: At the 3 module-branched sites (lines ~929, ~1066, ~1162), replace `symbol.name` with `module_display_name(file_path)` in both `symbol=` and `message=` fields. Add `from docvet.ast_utils import module_display_name` to imports.
  - Notes: These sites are already guarded by `symbol.kind == "module"`, so no conditional needed.

- [x] Task 4: Update enrichment generic callsites
  - File: `src/docvet/checks/enrichment.py`
  - Action: At the 5 generic sites (lines ~1188, ~1278, ~1292, ~1345, ~1361), replace `symbol.name` with a conditional: `module_display_name(file_path) if symbol.kind == "module" else symbol.name` for both `symbol=` and `message=` fields.
  - Notes: Compute `display_name` once per Finding construction to avoid repeating the conditional. Non-module behavior must remain unchanged.

- [x] Task 5: Update enrichment test assertions and add generic-rule module tests
  - File: `tests/unit/checks/test_enrichment.py`
  - Action: Update 11 assertions (6 symbol + 5 message) that reference `"<module>"`. Tests passing `file_path="regular.py"` expect `"regular"`. Tests passing `file_path="__init__.py"` expect `"__init__"`. Additionally, add new tests that exercise module-kind symbols through generic rules (e.g., `prefer-fenced-code-blocks`, `missing-cross-references` Branch B) to verify the conditional `module_display_name(file_path) if symbol.kind == "module" else symbol.name` produces the correct display name for module kinds in generic paths.
  - Notes: Do NOT change tests in `test_ast_utils.py` — those validate Symbol construction which is unchanged.

- [x] Task 6: Update presence check
  - File: `src/docvet/checks/presence.py`
  - Action: At line ~153, replace `symbol=symbol.name` with `symbol=module_display_name(file_path)` when `symbol.kind == "module"`. At line ~145, update message from `"Module has no docstring"` to `f"Module '{module_display_name(file_path)}' has no docstring"`. Add import.
  - Notes: Non-module symbols (function, class, method) continue using `symbol.name` unchanged.

- [x] Task 7: Update presence test assertions
  - File: `tests/unit/checks/test_presence.py`
  - Action: Update 6 symbol filter assertions from `f.symbol == "<module>"` to the derived name based on each test's `file_path`: `"mod"` (for `"mod.py"`), `"imports"` (for `"imports.py"`), `"app"` (for `"app.py"`), `"script"` (for `"script.py"`), `"legacy"` (for `"legacy.py"`).
  - Notes: Also update any message assertions if presence message now includes the module name.

- [x] Task 8: Update freshness check
  - File: `src/docvet/checks/freshness.py`
  - Action: In `_build_finding` (line ~80), replace `symbol=symbol.name` with conditional: `symbol=module_display_name(file_path) if symbol.kind == "module" else symbol.name`. At lines ~245, ~440, ~467, replace `symbol.name`/`sym.name` with conditional display name in message construction. Add import.
  - Notes: `_build_finding` receives both `file_path` and `symbol` — all data available.

- [x] Task 9: Add freshness module-level finding test
  - File: `tests/unit/checks/test_freshness.py`
  - Action: Add a new test that exercises a module-level freshness finding (e.g., module body changed but docstring not updated) and asserts the `symbol` field uses the display name and the message says `"Module 'test' body changed..."` instead of `"Module '<module>' body changed..."`.
  - Notes: Existing Symbol fixture at line 513 stays unchanged (it tests `_classify_changed_lines`, not Finding construction).

- [x] Task 10: Update coverage check
  - File: `src/docvet/checks/coverage.py`
  - Action: At line ~107, replace `symbol="<module>"` with `symbol=dir_rel.replace("/", ".")`. The `dir_rel` variable is already computed at line ~98.
  - Notes: No import needed — pure string operation. Coverage findings are directory-level, so `dir_rel` (e.g., `"pkg.sub"`) is semantically correct.

- [x] Task 11: Update coverage test assertions
  - File: `tests/unit/checks/test_coverage.py`
  - Action: Update 2 assertions from `symbol == "<module>"` to the dotted directory name (e.g., `"pkg/sub"` -> `"pkg.sub"`, `"pkg"` -> `"pkg"`).

- [x] Task 12: Update CLI test Finding fixtures
  - File: `tests/unit/test_cli.py`
  - Action: Update 3 Finding fixture constructions and 1 assertion from `symbol="<module>"` to the dotted directory name matching what coverage now produces (e.g., `"pkg.sub"` for `dir_rel="pkg/sub"`, `"pkg"` for `dir_rel="pkg"`).

- [x] Task 13: Run full test suite and verify
  - Action: Run `uv run pytest` to confirm all tests pass. Run `uv run ruff check .` and `uv run ruff format --check .` to confirm lint/format compliance.
  - Notes: If any tests fail, fix assertion values — the helper conversion table in Task 2 is the source of truth.

### Acceptance Criteria

- [x] AC 1: Given a file path `"src/gepa_adk/config.py"`, when `module_display_name()` is called, then it returns `"gepa_adk.config"`.
- [x] AC 2: Given a file path `"src/pkg/__init__.py"`, when `module_display_name()` is called, then it returns `"pkg"` (trailing `.__init__` collapsed).
- [x] AC 3: Given a file path `"mod.py"` (flat script, no prefix), when `module_display_name()` is called, then it returns `"mod"`.
- [x] AC 4: Given a file path `"__init__.py"` (bare init), when `module_display_name()` is called, then it returns `"__init__"` (no parent to collapse into).
- [x] AC 5: Given a module-level enrichment finding for file `"src/pkg/config.py"`, when the finding is constructed, then `symbol == "pkg.config"` and message contains `"Module 'pkg.config'"` (not `"<module>"`).
- [x] AC 6: Given a module-level enrichment finding via a generic rule (e.g., `prefer-fenced-code-blocks`) for file `"src/pkg/config.py"`, when the finding is constructed, then `symbol` and message use the display name for module kind, and non-module symbols are unchanged.
- [x] AC 7: Given a module without a docstring checked by presence for file `"app.py"`, when the finding is constructed, then `symbol == "app"` and message is `"Module 'app' has no docstring"`.
- [x] AC 8: Given a module-level freshness finding (body changed, docstring not updated) for file `"src/pkg/utils.py"`, when the finding is constructed, then `symbol` uses the display name and message contains `"Module 'pkg.utils'"` and does not contain `"<module>"`.
- [x] AC 9: Given a coverage finding for directory `"pkg/sub"` lacking `__init__.py`, when the finding is constructed, then `symbol == "pkg.sub"` (dotted directory name, not `"<module>"`).
- [x] AC 10: Given a function-level finding via a generic enrichment rule (e.g., `prefer-fenced-code-blocks`) for file `"src/pkg/config.py"`, when the finding is constructed, then `symbol` uses the function name (e.g., `"run_check"`), NOT the module display name — the conditional only applies to module-kind symbols.
- [x] AC 11: Given an absolute file path `/home/user/project/src/pkg/mod.py`, when `module_display_name()` is called, then it returns `"pkg.mod"` (rfind locates `/src/` marker regardless of leading path components).
- [x] AC 12: Given the full test suite, when `uv run pytest` is executed, then all tests pass (including updated assertions and new helper tests).
- [x] AC 13: Given the `Symbol` dataclass in `ast_utils.py`, when a module symbol is created by `get_documented_symbols()`, then `name` is still `"<module>"` (AST layer unchanged).

## Additional Context

### Dependencies

None — no new runtime or dev dependencies. Pure string manipulation using stdlib only.

### Testing Strategy

- **Helper unit tests** (Task 2): Dedicated `TestModuleDisplayName` class in `test_ast_utils.py` covering 13 edge cases (AC 1-4, AC 11). Run after Task 1 to confirm helper before touching check modules.
- **Enrichment assertion updates** (Task 5): 11 assertions across existing tests. Expected values derived from `file_path` each test passes (`"regular.py"` -> `"regular"`, `"__init__.py"` -> `"__init__"`).
- **Presence assertion updates** (Task 7): 6 filter assertions. Each test uses a different `file_path` (`"mod.py"`, `"app.py"`, `"imports.py"`, `"script.py"`, `"legacy.py"`).
- **Coverage assertion updates** (Task 11): 2 assertions. Expected values derived from `dir_rel` (`"pkg/sub"` -> `"pkg.sub"`, `"pkg"` -> `"pkg"`).
- **CLI fixture updates** (Task 12): 4 Finding constructions/assertions. Values must match what coverage now produces.
- **New freshness test** (Task 9): Module-level finding validates `symbol` and `message` use display name. No existing test covers this path.
- **`test_ast_utils.py` unchanged**: Symbol construction tests (`name == "<module>"`) remain — they validate AST-layer behavior (AC 13).
- **Full suite gate** (Task 13): `uv run pytest` must pass all tests.

### Notes

- Discovered via real-world usage of `docvet@v1` GitHub Action in `gepa-adk` CI (run 22805146741)
- Party mode consensus: team unanimously agreed on dotted-path approach over filename-only or raw-path options
- Coverage uses `dir_rel.replace("/", ".")` instead of `module_display_name()` — semantically correct for directory-level findings
- This is a patch-level fix (`fix(checks): replace <module> sentinel with display names in findings`)
- Risk: low — pure display change, no behavioral or config impact. All changes are to `symbol` and `message` string values in Finding records.
- **Presence message format change**: The presence module's message changes from `"Module has no docstring"` to `"Module '{display_name}' has no docstring"`. This is a message-text-only change — no behavioral impact — but consumers parsing exact message strings should be aware.
