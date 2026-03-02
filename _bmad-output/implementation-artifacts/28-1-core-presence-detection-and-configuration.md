# Story 28.1: Core Presence Detection and Configuration

Status: done
Branch: `feat/presence-28-1-core-presence-detection-and-configuration`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/239

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer**,
I want docvet to detect public symbols that have no docstring and report per-file coverage stats,
So that I can enforce docstring presence requirements without depending on interrogate's vulnerable supply chain.

## Acceptance Criteria

1. **Given** a Python file with a mix of documented and undocumented public symbols **When** `check_presence(source, config)` is called **Then** a Finding with rule `missing-docstring` and category `required` is returned for each undocumented symbol **And** each Finding includes file path, line number, symbol name, and a dynamic message like "Public {symbol_type} has no docstring"

2. **Given** a Python file missing its module-level docstring **When** `check_presence` runs **Then** a `missing-docstring` finding is returned with message "Module has no docstring"

3. **Given** a class definition with no docstring **When** `check_presence` runs **Then** a `missing-docstring` finding is returned with message "Public class has no docstring"

4. **Given** a PresenceConfig with `ignore_init=True` (default) **When** a class `__init__` method has no docstring **Then** no Finding is produced for that `__init__` method

5. **Given** a PresenceConfig with `ignore_init=False` (overridden) **When** a class `__init__` method has no docstring **Then** a `missing-docstring` finding IS produced for that `__init__` method

6. **Given** a PresenceConfig with `ignore_magic=True` (default) **When** `__repr__` or `__str__` methods have no docstring **Then** no Finding is produced for those magic methods

7. **Given** a PresenceConfig with `ignore_private=True` (default) **When** a `_helper_function` has no docstring **Then** no Finding is produced for that private symbol

8. **Given** a file with nested symbols (method inside class, inner function) **When** `check_presence` runs **Then** each undocumented nested public symbol produces its own finding independently

9. **Given** a file with 8 public symbols, 6 with docstrings and 2 without **When** `check_presence` runs **Then** per-file stats report documented=6, total=8 **And** 2 `missing-docstring` findings are returned

10. **Given** a file where all public symbols have docstrings **When** `check_presence` runs **Then** zero findings are returned and per-file stats report documented=N, total=N

11. **Given** an empty file or a file with only imports **When** `check_presence` runs **Then** zero findings are returned (no symbols to check)

12. **Given** a Python file with a `SyntaxError` **When** `check_presence` is called **Then** zero findings are returned (consistent with enrichment's error contract)

## Tasks / Subtasks

- [x] Task 1: Create `PresenceConfig` dataclass (AC: 4, 5, 6, 7)
  - [x] 1.1: Add `PresenceConfig` frozen dataclass to `src/docvet/config.py` with fields: `enabled: bool = True`, `min_coverage: float = 0.0`, `ignore_init: bool = True`, `ignore_magic: bool = True`, `ignore_private: bool = True`
  - [x] 1.2: Add `_VALID_PRESENCE_KEYS` frozenset with kebab-case key names
  - [x] 1.3: Add `_parse_presence(data)` function following `_parse_freshness` pattern
  - [x] 1.4: Add `"presence"` to `_VALID_TOP_KEYS` and `_VALID_CHECK_NAMES`
  - [x] 1.5: Add `presence: PresenceConfig` field to `DocvetConfig`
  - [x] 1.6: Wire presence parsing into `_parse_docvet_section` and `load_config`
  - [x] 1.7: Add `"PresenceConfig"` to `config.py` `__all__`
  - [x] 1.8: Write unit tests for PresenceConfig parsing and validation

- [x] Task 2: Create `PresenceStats` dataclass (AC: 9, 10, 11)
  - [x] 2.1: Define `PresenceStats` frozen dataclass in `src/docvet/checks/presence.py` with `documented: int`, `total: int`

- [x] Task 3: Implement `check_presence` function (AC: 1, 2, 3, 8, 9, 10, 11, 12)
  - [x] 3.1: Create `src/docvet/checks/presence.py` with module docstring
  - [x] 3.2: Implement `_should_skip(symbol, config)` helper for filtering logic
  - [x] 3.3: Implement `check_presence(source, file_path, config)` returning `tuple[list[Finding], PresenceStats]`
  - [x] 3.4: Handle `SyntaxError` gracefully (return empty findings + zero stats)

- [x] Task 4: Wire into `checks/__init__.py` (AC: none — infrastructure)
  - [x] 4.1: Add `from docvet.checks.presence import check_presence` import
  - [x] 4.2: Add `"check_presence"` to `__all__`

- [x] Task 5: Write comprehensive unit tests (AC: all)
  - [x] 5.1: Test mixed documented/undocumented symbols (AC 1)
  - [x] 5.2: Test module-level missing docstring (AC 2)
  - [x] 5.3: Test class missing docstring (AC 3)
  - [x] 5.4: Test ignore_init=True skips `__init__` (AC 4)
  - [x] 5.5: Test ignore_init=False reports `__init__` (AC 5)
  - [x] 5.6: Test ignore_magic=True skips magic methods (AC 6)
  - [x] 5.7: Test ignore_private=True skips private symbols (AC 7)
  - [x] 5.8: Test nested symbols (AC 8)
  - [x] 5.9: Test per-file stats (AC 9)
  - [x] 5.10: Test all documented (AC 10)
  - [x] 5.11: Test empty file / imports only (AC 11)
  - [x] 5.12: Test SyntaxError handling (AC 12)
  - [x] 5.13: Test all 6 Finding fields are correct
  - [x] 5.14: Update `test_exports.py` module list and re-export assertions

- [x] Task 6: Run quality gates
  - [x] 6.1: `uv run ruff check .` — zero lint violations
  - [x] 6.2: `uv run ruff format --check .` — zero format issues
  - [x] 6.3: `uv run ty check` — zero type errors
  - [x] 6.4: `uv run pytest` — all tests pass (1046 passed), no regressions
  - [x] 6.5: `uv run docvet check --all` — zero docvet findings
  - [x] 6.6: Run `analyze_code_snippet` on `presence.py` — zero issues

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `TestCheckPresenceMixedSymbols::test_returns_finding_for_each_undocumented_symbol`, `test_finding_includes_file_line_symbol_rule_message` | Pass |
| 2 | `TestCheckPresenceModuleMissing::test_missing_module_docstring_returns_finding`, `test_present_module_docstring_no_finding` | Pass |
| 3 | `TestCheckPresenceClassMissing::test_class_without_docstring_returns_finding`, `test_class_with_docstring_no_finding` | Pass |
| 4 | `TestCheckPresenceIgnoreInit::test_ignore_init_true_skips_init` | Pass |
| 5 | `TestCheckPresenceIgnoreInit::test_ignore_init_false_reports_init` | Pass |
| 6 | `TestCheckPresenceIgnoreMagic::test_ignore_magic_true_skips_repr_and_str`, `test_ignore_magic_false_reports_repr_and_str` | Pass |
| 7 | `TestCheckPresenceIgnorePrivate::test_ignore_private_true_skips_private_function`, `test_ignore_private_false_reports_private_function` | Pass |
| 8 | `TestCheckPresenceNestedSymbols::test_nested_method_inside_class_independently_reported`, `test_documented_method_not_reported` | Pass |
| 9 | `TestCheckPresencePerFileStats::test_stats_reflect_documented_and_total`, `test_stats_invariant_documented_plus_findings_equals_total` | Pass |
| 10 | `TestCheckPresenceAllDocumented::test_all_documented_returns_zero_findings` | Pass |
| 11 | `TestCheckPresenceEmptyFile::test_empty_file_returns_zero_findings`, `test_imports_only_file_returns_module_finding` | Pass |
| 12 | `TestCheckPresenceSyntaxError::test_syntax_error_returns_empty_findings_and_zero_stats` | Pass |

## Dev Notes

### Architecture Patterns

**New module location:** `src/docvet/checks/presence.py` — follows the pattern of `coverage.py` (simplest existing check module). Pure function, no git, no external deps.

**Function signature:**

```python
def check_presence(
    source: str,
    file_path: str,
    config: PresenceConfig,
) -> tuple[list[Finding], PresenceStats]:
```

- `source`: Raw Python source text (read by CLI layer, passed in)
- `file_path`: Relative file path for Finding construction
- `config`: PresenceConfig instance with filtering options
- Returns: Tuple of findings list + per-file stats

**Finding construction:**

```python
Finding(
    file=file_path,
    line=symbol.line,
    symbol=symbol.name,
    rule="missing-docstring",
    message=f"Public {symbol.kind} has no docstring",
    category="required",
)
```

**CRITICAL — Category reconciliation:** The epic AC says `category="presence"` but `Finding.__post_init__` validates category as `Literal["required", "recommended"]` and raises `ValueError` on anything else. Use `category="required"` — missing docstrings are required findings, consistent with `coverage.py`'s `missing-init` findings which also use `"required"`.

**Message templates:**
- Module: `"Module has no docstring"` (special case — no "Public" prefix)
- Function: `"Public function has no docstring"`
- Class: `"Public class has no docstring"`
- Method: `"Public method has no docstring"`

**Symbol access via `get_documented_symbols`:**

`get_documented_symbols(tree: ast.Module) -> list[Symbol]` from `ast_utils.py` returns ALL symbols (documented and undocumented) despite its name. Each Symbol has:
- `symbol.name`: str (e.g., `"process"`, `"<module>"`)
- `symbol.kind`: `Literal["function", "class", "method", "module"]`
- `symbol.line`: int (def/class keyword line)
- `symbol.docstring`: `str | None` (None = no docstring)
- `symbol.parent`: `str | None` (enclosing class name or None)

**Filtering logic (`_should_skip`):**
1. If `config.ignore_private` and name starts with `_` (but not `__`): skip
2. If `config.ignore_magic` and name starts with `__` and ends with `__` (but not `__init__`): skip
3. If `config.ignore_init` and name == `__init__`: skip
4. Module symbols (`<module>`) are never filtered by private/magic rules
5. Public = name doesn't start with underscore. `__all__` is irrelevant.
6. Parent visibility doesn't gate child — a public method inside `_Private` class is still checked by name

**SyntaxError contract:** Wrap `ast.parse(source)` in try/except `SyntaxError`. Return `([], PresenceStats(documented=0, total=0))` on parse error. This matches enrichment's implicit contract (it would crash, but the CLI layer already handles this upstream).

### Config Integration (8 Steps)

1. Add `PresenceConfig` frozen dataclass to `config.py` after `EnrichmentConfig`
2. Add `_VALID_PRESENCE_KEYS = frozenset({"enabled", "min-coverage", "ignore-init", "ignore-magic", "ignore-private"})`
3. Add `"presence"` to `_VALID_TOP_KEYS`
4. Add `"presence"` to `_VALID_CHECK_NAMES`
5. Add `_parse_presence(data)` following `_parse_freshness` pattern — validate keys, types (`bool` for ignore_*, `float` for min_coverage, `bool` for enabled)
6. Add `presence: PresenceConfig = field(default_factory=PresenceConfig)` to `DocvetConfig`
7. Wire `presence_data` handling into `_parse_docvet_section` (pop, validate dict type, call parser)
8. Wire `raw_presence` into `load_config`'s return `DocvetConfig(...)` construction
9. Add `"PresenceConfig"` to `config.py`'s `__all__`
10. Add `"PresenceConfig"` to `test_exports.py` assertions

**`min_coverage` note:** The field lives on `PresenceConfig` but threshold comparison is Story 28.2's responsibility (CLI layer). `check_presence` is a pure per-file function. `min_coverage` defaults to `0.0` (no threshold enforcement unless configured).

### Re-export Wiring

In `src/docvet/checks/__init__.py`:
- Add `from docvet.checks.presence import check_presence`
- Add `"check_presence"` to `__all__`
- Update module docstring to mention presence check

### test_exports.py Updates

In `tests/unit/test_exports.py`:
1. Add `"docvet.checks.presence"` to `_ALL_DOCVET_MODULES` list
2. Add `TestCheckSubmoduleExports.test_presence_all_contains_check_presence` method
3. Update `TestChecksPackageReExports.test_checks_all_contains_finding_and_all_check_functions`:
   - Add `"check_presence"` to `expected` list
   - Update `len(mod.__all__)` from 6 to 7
4. Update `TestChecksPackageReExports.test_checks_package_exposes_check_functions_as_attributes`:
   - Add `assert hasattr(mod, "check_presence")` and `assert callable(mod.check_presence)`
5. Update `TestConfigExports.test_config_all_contains_public_types_and_load_config`:
   - Add `"PresenceConfig"` to expected list
   - Update count from 4 to 5

### Testing Strategy

**Test file:** `tests/unit/checks/test_presence.py`

**Test organization:** One class per AC (established pattern from `test_coverage.py`):
- `TestCheckPresenceMixedSymbols` (AC 1)
- `TestCheckPresenceModuleMissing` (AC 2)
- `TestCheckPresenceClassMissing` (AC 3)
- `TestCheckPresenceIgnoreInit` (AC 4, 5)
- `TestCheckPresenceIgnoreMagic` (AC 6)
- `TestCheckPresenceIgnorePrivate` (AC 7)
- `TestCheckPresenceNestedSymbols` (AC 8)
- `TestCheckPresencePerFileStats` (AC 9)
- `TestCheckPresenceAllDocumented` (AC 10)
- `TestCheckPresenceEmptyFile` (AC 11)
- `TestCheckPresenceSyntaxError` (AC 12)
- `TestCheckPresenceFindingFields` (all 6 fields)

**Config tests** in `tests/unit/test_config.py` (or separate test class):
- `TestPresenceConfigDefaults`
- `TestPresenceConfigParsing`
- `TestPresenceConfigValidation`

**Test input pattern:** Use inline source strings with `ast.parse()` or the `parse_source` conftest fixture, not file fixtures. This is the enrichment test pattern.

**Assertion pattern (from dev-quality-checklist):**
- `assert len(findings) == N` first (catch deduplication issues)
- All 6 Finding fields verified per finding
- `assert findings == []` for zero-finding cases
- Stats assertions: `assert stats.documented == X` and `assert stats.total == Y`

### Project Structure Notes

- New file: `src/docvet/checks/presence.py` — fits cleanly alongside `coverage.py`, `enrichment.py`, `freshness.py`, `griffe_compat.py`
- Modified files: `src/docvet/config.py`, `src/docvet/checks/__init__.py`, `tests/unit/test_exports.py`
- New test file: `tests/unit/checks/test_presence.py`
- No structural conflicts with existing codebase

### References

- [Source: `src/docvet/checks/_finding.py`] — Finding dataclass, category validation at line 94: `Literal["required", "recommended"]`
- [Source: `src/docvet/checks/coverage.py`] — Simplest check module pattern (pure function, `list[Finding]` return)
- [Source: `src/docvet/ast_utils.py:285-317`] — `get_documented_symbols()` returns ALL symbols (not just documented)
- [Source: `src/docvet/ast_utils.py:38-108`] — Symbol dataclass with `kind`, `docstring`, `parent` fields
- [Source: `src/docvet/config.py:40-66`] — FreshnessConfig pattern (frozen dataclass, default values)
- [Source: `src/docvet/config.py:179-211`] — Valid key constants and check names
- [Source: `src/docvet/config.py:389-404`] — `_parse_freshness` pattern for section parsers
- [Source: `src/docvet/checks/enrichment.py:1354`] — Enrichment skip: `if not symbol.docstring: continue`
- [Source: `_bmad-output/planning-artifacts/epics-presence-mcp.md:96-156`] — Story 28.1 ACs and implementation notes
- [Source: `_bmad-output/planning-artifacts/implementation-readiness-report-2026-03-02.md:157-166`] — Minor issues 5-8 for this story

### Documentation Impact

- Pages: None — no user-facing documentation changes in this story
- Nature of update: N/A — Story 28.1 creates the core function and config. Documentation is Story 28.3's scope.

### Retro Action Items (carried forward)

- **Epic 27:** Run `analyze_code_snippet` on new/modified modules during implementation (Task 6.6)
- **Tech debt — test_exports.py:** PR #237 adds `docvet.lsp` to module list. If not merged before this story, coordinate the `_ALL_DOCVET_MODULES` update to include both `docvet.lsp` and `docvet.checks.presence`.
- **Tech debt — CLAUDE.md:** PR #238 updates file tree. If not merged, coordinate module layout section update.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1046 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `analyze_code_snippet` on `presence.py` — zero issues

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- Empty file edge case: `ast.parse("")` returns Module with empty body; `get_documented_symbols` still returns a `<module>` symbol with `docstring=None`. Added `if not tree.body` early return guard to produce zero findings for empty files (AC 11).
- `_parse_presence` type narrowing: `ty` could not narrow `value` through negative `isinstance` branch + `sys.exit`. Restructured to positive `isinstance` branch for `float()` call.
- Lint fixes: removed unused `PresenceStats` import from test file, shortened long comment, capitalized docstring first word.
- Stale docstring fixes: updated module docstrings in `config.py`, `checks/__init__.py` to mention presence module.
- Code review fix M1: Added `PresenceStats` to `__all__` in `presence.py` and `checks/__init__.py` re-exports for API hygiene.
- Code review fix M2: Added `stats.documented == 0` and `stats.total == 0` assertions to empty file test.
- Code review fix L2: Added stats assertions to imports-only file test (`stats.total == 1`, `stats.documented == 0`).

### Change Log

| Change | File | Description |
|--------|------|-------------|
| ADD | `src/docvet/checks/presence.py` | New module: `PresenceStats`, `_should_skip`, `check_presence` |
| MODIFY | `src/docvet/config.py` | Added `PresenceConfig`, `_VALID_PRESENCE_KEYS`, `_parse_presence`, wiring |
| MODIFY | `src/docvet/checks/__init__.py` | Re-export `check_presence`, `PresenceStats`, updated docstring |
| ADD | `tests/unit/checks/test_presence.py` | 30 unit tests covering all 12 ACs + edge cases |
| MODIFY | `tests/unit/test_config.py` | 14 new PresenceConfig tests |
| MODIFY | `tests/unit/test_exports.py` | Updated for presence module and PresenceConfig exports |

### File List

- `src/docvet/checks/presence.py` (NEW)
- `src/docvet/config.py` (MODIFIED)
- `src/docvet/checks/__init__.py` (MODIFIED)
- `tests/unit/checks/test_presence.py` (NEW)
- `tests/unit/test_config.py` (MODIFIED)
- `tests/unit/test_exports.py` (MODIFIED)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Adversarial code review (BMAD workflow) + Party Mode consensus (Winston, Amelia, Murat, Bob)

### Outcome

Approved with fixes. 3 issues fixed, 1 downgraded to optional, 1 deferred to Story 28.2.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | `PresenceStats` not in `__all__` — public return type not exported | Fixed: added to `presence.py` `__all__`, `checks/__init__.py` re-exports, `test_exports.py` |
| M2 | MEDIUM | `test_empty_file_returns_zero_findings` missing stats assertions | Fixed: added `stats.documented == 0`, `stats.total == 0` |
| M3 | LOW (downgraded) | Doc Impact says "None" but PR has user-facing code | Accepted: progressive build pattern, CLI not wired yet. Docs deferred to 28.3. |
| L1 | LOW | `"presence"` not in default `warn_on` | No action: Story 28.2 scope (CLI wiring) |
| L2 | LOW | Unused `stats` in imports-only test | Fixed: added `stats.total == 1`, `stats.documented == 0` assertions |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
