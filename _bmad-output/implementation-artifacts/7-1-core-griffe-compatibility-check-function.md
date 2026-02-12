# Story 7.1: Core Griffe Compatibility Check Function

Status: done

## Story

As a developer,
I want a `check_griffe_compat` function that loads a Python package via griffe, captures parser warnings, and produces findings for rendering compatibility issues,
So that I can detect docstrings that will render incorrectly in mkdocs-material documentation before deployment.

## Acceptance Criteria

1. **Given** a Python package with a function whose Args parameter lacks a type annotation in both docstring and signature, **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns a `Finding` with `rule="griffe-missing-type"`, `category="recommended"`, the specific line number from the warning, and a message including the symbol name and griffe's warning text.

2. **Given** a Python package with a function that documents a parameter not in the function signature, **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns a `Finding` with `rule="griffe-unknown-param"`, `category="required"`, and a message identifying the phantom parameter.

3. **Given** a Python package with a function whose docstring has formatting issues (confusing indentation, malformed entries), **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns a `Finding` with `rule="griffe-format-warning"`, `category="recommended"`.

4. **Given** a function with 3 untyped parameters, **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns 3 separate `griffe-missing-type` findings (one per parameter, not deduplicated per symbol — FR88).

5. **Given** a well-documented package where all parameters have type annotations and match the function signature, **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns an empty list (zero findings — FR89, NFR41).

6. **Given** griffe is not installed (`griffe is None`), **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns an empty list immediately without raising exceptions (FR90, NFR42).

7. **Given** an empty `files` list, **When** `check_griffe_compat(src_root, files)` is called, **Then** it returns an empty list immediately without invoking griffe package loading.

8. **Given** a package that fails to load via griffe (syntax errors in user code, missing imports), **When** `check_griffe_compat(src_root, files)` is called, **Then** it catches the exception (`LoadingError`, `ModuleNotFoundError`, `OSError`, `SyntaxError`) and continues to the next package (FR91).

9. **Given** `src_root` contains multiple packages (multiple child directories with `__init__.py`), **When** `check_griffe_compat(src_root, files)` is called, **Then** it loads each package in sorted order and produces findings from all loadable packages; a failure in one package does not abort others.

10. **Given** a griffe warning with an unrecognized message format (from a future griffe version), **When** `_classify_warning(message)` is called, **Then** it returns `("griffe-format-warning", "recommended")` as the catch-all classification (FR92, NFR43).

11. **Given** the `_classify_warning` function receives a message containing `"does not appear in the function signature"`, **When** called, **Then** it returns `("griffe-unknown-param", "required")` — checked before `griffe-missing-type` (priority order).

12. **Given** the `_classify_warning` function receives a message containing `"No type or annotation for"`, **When** called, **Then** it returns `("griffe-missing-type", "recommended")`.

13. **Given** the `_WarningCollector` logging handler attached to `logging.getLogger("griffe")`, **When** griffe emits WARNING-level log records during docstring parsing, **Then** the handler collects all records in its `records` list.

14. **Given** the `_WarningCollector` handler, **When** griffe emits DEBUG or INFO level records, **Then** the handler ignores them (level filter set to WARNING).

15. **Given** the logging handler lifecycle, **When** `check_griffe_compat` completes (normally or via exception), **Then** the handler is removed from the griffe logger via try/finally (FR96 — no permanent global state modification).

16. **Given** the `files` parameter contains only files outside the loaded griffe package, **When** `_walk_objects(package, file_set)` walks the object tree, **Then** all objects are filtered out and zero findings are produced (FR93).

17. **Given** the `_walk_objects` generator encounters an alias object (`obj.is_alias`), **When** walking the griffe object tree, **Then** it skips the alias without accessing its attributes (avoids `AliasResolutionError`).

18. **Given** a griffe object with `obj.docstring is None`, **When** `_walk_objects` encounters it, **Then** it skips the object (no docstring to parse, no warnings to produce).

19. **Given** the `_build_finding_from_record` helper receives a log record whose `getMessage()` matches `_WARNING_PATTERN` (`^(.+?):(\d+): (.+)$`), **When** called with the record and griffe object, **Then** it extracts the line number from the warning (group 2), classifies the message text (group 3), and constructs a `Finding` with `file=str(obj.filepath)`, `line=parsed_line`, `symbol=obj.name`, and the classified rule/category.

20. **Given** a log record whose `getMessage()` does not match `_WARNING_PATTERN`, **When** `_build_finding_from_record` is called, **Then** it returns `None` (defensive — unrecognized format skipped).

21. **Given** the `tests/fixtures/griffe_pkg/` fixture package with known-bad docstrings, **When** `check_griffe_compat` is called with real griffe loading (integration test, requires `pytest.importorskip("griffe")`), **Then** it produces the expected findings for all 3 rule types and zero findings for the well-documented function.

22. **Given** the `_build_finding_from_record` helper constructs a Finding, **Then** the `message` field follows format `"{obj.kind.value.capitalize()} '{obj.name}' {message_text}"` — consistent with enrichment/freshness message patterns.

## Tasks / Subtasks

- [x] Task 1: Create `_WarningCollector` handler class and `_classify_warning` function (AC: #10, #11, #12, #13, #14)
  - [x] 1.1 Create `src/docvet/checks/griffe_compat.py` with module docstring, `from __future__ import annotations`, imports
  - [x] 1.2 Add conditional griffe import (`try/except ImportError` with `TYPE_CHECKING` guard)
  - [x] 1.3 Add module-level constants: `_MISSING_TYPE_PATTERN`, `_UNKNOWN_PARAM_PATTERN`, `_WARNING_PATTERN`
  - [x] 1.4 Implement `_WarningCollector(logging.Handler)` with `level=WARNING` and `records: list[LogRecord]`
  - [x] 1.5 Implement `_classify_warning(message: str) -> tuple[str, str]` with priority-ordered substring matching
  - [x] 1.6 Write unit tests for `_WarningCollector` (collects WARNING, ignores DEBUG/INFO)
  - [x] 1.7 Write unit tests for `_classify_warning` (all 3 rules + catch-all + priority order)

- [x] Task 2: Create `_walk_objects`, `_resolve_file_set`, and `_build_finding_from_record` helpers (AC: #16, #17, #18, #19, #20, #22)
  - [x] 2.1 Implement `_resolve_file_set(files: Sequence[Path]) -> set[Path]` using `.resolve()` for absolute paths
  - [x] 2.2 Implement `_walk_objects(obj: GriffeObject, file_set: set[Path]) -> Iterator[GriffeObject]` with alias skip, no-docstring skip, file filter
  - [x] 2.3 Implement `_build_finding_from_record(record: LogRecord, obj: GriffeObject) -> Finding | None` with regex parse, classify, construct
  - [x] 2.4 Write unit tests for `_walk_objects` (alias skip, no-docstring skip, file filter, nested members)
  - [x] 2.5 Write unit tests for `_build_finding_from_record` (matching format, non-matching format, all Finding fields verified)

- [x] Task 3: Create `check_griffe_compat` orchestrator (AC: #1, #2, #3, #4, #5, #6, #7, #8, #9, #15)
  - [x] 3.1 Implement `check_griffe_compat(src_root: Path, files: Sequence[Path]) -> list[Finding]` with guard clauses, handler lifecycle, package discovery, load/walk/parse pipeline
  - [x] 3.2 Write unit tests: griffe not installed returns `[]` (AC #6)
  - [x] 3.3 Write unit tests: empty files returns `[]` (AC #7)
  - [x] 3.4 Write unit tests: happy path with mocked griffe.load returning mock package (AC #1, #2, #3)
  - [x] 3.5 Write unit tests: multiple findings per symbol not deduplicated (AC #4)
  - [x] 3.6 Write unit tests: well-documented code returns `[]` (AC #5)
  - [x] 3.7 Write unit tests: load failure skips package and continues (AC #8)
  - [x] 3.8 Write unit tests: multiple packages loaded in sorted order (AC #9)
  - [x] 3.9 Write unit tests: handler removed in finally (AC #15)
  - [x] 3.10 Write unit tests: files outside package produce zero findings (AC #16)

- [x] Task 4: Create integration test fixture and smoke test (AC: #21)
  - [x] 4.1 Create `tests/fixtures/griffe_pkg/__init__.py` (empty)
  - [x] 4.2 Create `tests/fixtures/griffe_pkg/bad_docstrings.py` with known-bad docstrings triggering all 3 rules + one well-documented function
  - [x] 4.3 Create `tests/integration/test_griffe_compat.py` with `pytest.importorskip("griffe")` and smoke test validating full pipeline
  - [x] 4.4 Run full test suite (`uv run pytest`) and verify all pass

- [x] Task 5: Fill AC-to-Test Mapping table and verify completeness
  - [x] 5.1 Map every AC to at least one test function name
  - [x] 5.2 Verify all tests pass and no AC is uncovered

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `TestCheckGriffeCompat::test_happy_path_missing_type`, `TestGriffeCompatSmoke::test_missing_type_findings_for_untyped_params` | PASS |
| #2 | `TestCheckGriffeCompat::test_happy_path_unknown_param`, `TestGriffeCompatSmoke::test_unknown_param_finding_for_phantom` | PASS |
| #3 | `TestCheckGriffeCompat::test_happy_path_format_warning`, `TestGriffeCompatSmoke::test_format_warning_findings_for_bad_format` | PASS |
| #4 | `TestCheckGriffeCompat::test_multiple_findings_per_symbol_not_deduplicated`, `TestGriffeCompatSmoke::test_missing_type_findings_for_untyped_params` | PASS |
| #5 | `TestCheckGriffeCompat::test_well_documented_code_returns_empty`, `TestGriffeCompatSmoke::test_well_documented_function_produces_no_findings` | PASS |
| #6 | `TestCheckGriffeCompat::test_griffe_not_installed_returns_empty` | PASS |
| #7 | `TestCheckGriffeCompat::test_empty_files_returns_empty`, `TestGriffeCompatSmoke::test_empty_files_with_real_griffe` | PASS |
| #8 | `TestCheckGriffeCompat::test_load_failure_skips_package_and_continues`, `test_load_failure_module_not_found`, `test_load_failure_syntax_error`, `test_load_failure_os_error` | PASS |
| #9 | `TestCheckGriffeCompat::test_multiple_packages_sorted_order` | PASS |
| #10 | `TestClassifyWarning::test_catchall_returns_format_warning`, `test_empty_message_returns_catchall`, `test_confusing_indentation_message` | PASS |
| #11 | `TestClassifyWarning::test_unknown_param_returns_required`, `test_unknown_param_checked_before_missing_type` | PASS |
| #12 | `TestClassifyWarning::test_missing_type_returns_recommended` | PASS |
| #13 | `TestWarningCollector::test_collects_warning_records`, `test_collects_multiple_warnings` | PASS |
| #14 | `TestWarningCollector::test_ignores_debug_records`, `test_ignores_info_records` | PASS |
| #15 | `TestCheckGriffeCompat::test_handler_removed_in_finally` | PASS |
| #16 | `TestWalkObjects::test_skips_objects_outside_file_set`, `TestCheckGriffeCompat::test_files_outside_package_produce_zero_findings` | PASS |
| #17 | `TestWalkObjects::test_skips_alias_objects`, `test_skips_alias_child_but_continues_siblings` | PASS |
| #18 | `TestWalkObjects::test_skips_objects_without_docstring` | PASS |
| #19 | `TestBuildFindingFromRecord::test_matching_format_returns_finding`, `test_unknown_param_finding_fields`, `test_format_warning_finding_fields` | PASS |
| #20 | `TestBuildFindingFromRecord::test_non_matching_format_returns_none` | PASS |
| #21 | `TestGriffeCompatSmoke::test_full_pipeline_produces_expected_findings` | PASS |
| #22 | `TestBuildFindingFromRecord::test_message_format_matches_convention` | PASS |

## Dev Notes

### Architecture Decisions (6 decisions from architecture.md)

**Decision 1 — Single file organization:** `griffe_compat.py` with one public function (`check_griffe_compat`). File order: module docstring → future annotations → stdlib imports → conditional griffe import → local imports → constants → `_WarningCollector` class → helpers (`_classify_warning`, `_build_finding_from_record`, `_resolve_file_set`, `_walk_objects`) → orchestrator.

**Decision 2 — Warning capture via `_WarningCollector(logging.Handler)`:** Custom handler subclass with `level=WARNING` and `records: list[LogRecord]`. Per-object attribution via snapshot pattern (`before:after` slice on `handler.records`). Try/finally for guaranteed handler cleanup.

**Decision 3 — Three-phase pipeline (Load → Walk → Parse):**
- Phase 1: `griffe.load(package_name, search_paths=[str(src_root)], docstring_parser="google", allow_inspection=False)`
- Phase 2: `_walk_objects` recursive generator — skip aliases, skip no-docstring, filter by `file_set`
- Phase 3: Trigger `obj.docstring.parsed` per object, collect warnings via snapshot

**Decision 4 — Substring classification with priority order:**
- `"does not appear in the function signature"` → `("griffe-unknown-param", "required")` (checked FIRST)
- `"No type or annotation for"` → `("griffe-missing-type", "recommended")`
- Catch-all → `("griffe-format-warning", "recommended")`

**Decision 5 — Layered exception handling:**
- Layer 1: `griffe.load()` wrapped with explicit `(LoadingError, ModuleNotFoundError, OSError, SyntaxError)` → `continue`
- Layer 2: `obj.is_alias` proactive skip in `_walk_objects`
- Layer 3: Handler cleanup via try/finally

**Decision 6 — Finding message format:** `f"{obj.kind.value.capitalize()} '{obj.name}' {message_text}"`. Line from parsed warning (not `obj.lineno`). File from `str(obj.filepath)`.

### Key Constraints

- **Zero config dependency** — no `GriffeConfig` dataclass, no config parameters. This is unique among check modules.
- **Conditional import** — `try: import griffe except ImportError: griffe = None` with `# type: ignore[assignment]`. Use `TYPE_CHECKING` guard for type hints referencing griffe types.
- **Package-level operation** — griffe loads entire packages, not individual files. The `files` parameter post-filters via `_walk_objects`.
- **No AST, no git, no subprocess** — griffe handles all parsing internally. Only imports: `logging`, `re`, `pathlib`, `typing`, `collections.abc`, and conditionally `griffe`.
- **Warning message regex:** `_WARNING_PATTERN = re.compile(r"^(.+?):(\d+): (.+)$")` — use `record.getMessage()` not `record.message`.
- **Trust griffe for dedup** — no docvet-level deduplication in MVP.
- **`str(obj.filepath)` for Finding.file** — absolute path, consistent with discovery.

### Naming Patterns (from enforcement guidelines)

- Constants: `_MISSING_TYPE_PATTERN`, `_UNKNOWN_PARAM_PATTERN`, `_WARNING_PATTERN`
- Handler class: `_WarningCollector` (describes behavior, not library)
- Helpers: `_classify_warning`, `_walk_objects`, `_resolve_file_set`, `_build_finding_from_record`
- Public function: `check_griffe_compat` (last function in file)

### Test Strategy

**Unit tests (`tests/unit/checks/test_griffe_compat.py`):**
- `_classify_warning` — pure function, test all 3 rules + catch-all + priority order (no mocks needed)
- `_WarningCollector` — emit records to `logging.getLogger("griffe")`, verify collection by level
- `_walk_objects` — use `MagicMock(spec=griffe.Function)` with configured `name`, `kind`, `filepath`, `docstring`, `is_alias`, `members`
- `_build_finding_from_record` — mock `LogRecord` with `getMessage()` returning known format strings, mock griffe object
- `check_griffe_compat` — mock `griffe.load` to return mock packages; mock `griffe` to `None` for FR90 path
- **Assertion strength:** verify ALL 6 Finding fields on every happy-path test
- **Edge cases:** empty files, griffe not installed, load failures, files outside package, non-matching log format

**Integration tests (`tests/integration/test_griffe_compat.py`):**
- Use `pytest.importorskip("griffe")` at module level
- Smoke test with `tests/fixtures/griffe_pkg/` fixture package
- Verify findings for all 3 rule types + zero findings for well-documented function

**Fixture package (`tests/fixtures/griffe_pkg/`):**
- `__init__.py` — empty, makes directory a package
- `bad_docstrings.py` — at least: one function with untyped param, one with phantom param, one with formatting issue, one well-documented function

### Quality Checklist (gated from Epic 6 retro)

- [x] AC-to-test traceability: every AC has >= 1 mapped test
- [x] Assertion strength: verify all 6 Finding fields (file, line, symbol, rule, message, category)
- [x] Edge case coverage: boundary tests, mix scenarios, skip conditions
- [x] Task tracking: verify code change exists before marking subtask done

### Project Structure Notes

**New files (this story):**
- `src/docvet/checks/griffe_compat.py` — core check function (~200-300 lines estimated)
- `tests/unit/checks/test_griffe_compat.py` — all unit tests (mocked griffe objects)
- `tests/integration/test_griffe_compat.py` — smoke test with real griffe loading
- `tests/fixtures/griffe_pkg/__init__.py` — empty package init
- `tests/fixtures/griffe_pkg/bad_docstrings.py` — known-bad docstrings fixture

**No modifications to existing files.** CLI wiring is Story 7.2.

**Module dependency boundary:**
```
checks/griffe_compat.py
  → imports Finding from docvet.checks
  → imports griffe conditionally (try/except ImportError)
  → NEVER imports from cli, discovery, config, ast_utils
  → NEVER imports from checks.enrichment, checks.freshness, checks.coverage
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Griffe Core Architectural Decisions] — Decisions 1-6
- [Source: _bmad-output/planning-artifacts/architecture.md#Griffe Implementation Patterns & Consistency Rules] — Naming, structure, enforcement
- [Source: _bmad-output/planning-artifacts/architecture.md#Griffe Test Strategy Patterns] — Mock strategy mapping
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.1] — AC definitions, FR coverage
- [Source: _bmad-output/planning-artifacts/epics.md#Griffe Detection (FR81-FR85)] — Functional requirements
- [Source: _bmad-output/planning-artifacts/epics.md#Griffe Non-Functional Requirements] — NFR39-NFR48
- [Source: _bmad-output/implementation-artifacts/epic-6-retro-2026-02-11.md] — Quality gating patterns
- [Source: src/docvet/checks/__init__.py] — Finding dataclass (6 fields, frozen, with __post_init__ validation)
- [Source: src/docvet/cli.py:312-319] — `_run_griffe` stub signature

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- One test fix: `test_handler_removed_in_finally` initially failed because `mock_griffe.LoadingError = Exception` catches `RuntimeError` (subclass). Fixed by using `type("LoadingError", (Exception,), {})` for a narrow exception class.
- Lint fixes: ruff auto-fixed import ordering; manually fixed E402 (importorskip pattern) with `noqa` and E501 (line length) by shortening docstrings.

### Completion Notes List

- Task 1: Created `_WarningCollector` handler class and `_classify_warning` function with 3-rule priority-ordered classification. 12 unit tests.
- Task 2: Created `_resolve_file_set`, `_walk_objects` (iterative stack with alias/docstring/file filtering), and `_build_finding_from_record` (regex parse + classify + Finding construction). 14 unit tests.
- Task 3: Created `check_griffe_compat` orchestrator with guard clauses (griffe=None, empty files), package discovery (sorted directory scan), handler lifecycle (try/finally), and load-walk-parse pipeline. 14 unit tests.
- Task 4: Created fixture package (`tests/fixtures/griffe_pkg/`) with known-bad docstrings triggering griffe-missing-type (3 untyped params), griffe-unknown-param (phantom param), and well-documented function (zero findings). 5 integration tests with real griffe loading.
- Task 5: Filled AC-to-Test Mapping table — all 22 ACs mapped to 45 tests (40 unit + 5 integration).
- Total: 603 tests (46 new), 0 regressions, all lint clean.

### File List

New files:
- `src/docvet/checks/griffe_compat.py`
- `tests/unit/checks/test_griffe_compat.py`
- `tests/integration/test_griffe_compat.py`
- `tests/fixtures/griffe_pkg/__init__.py`
- `tests/fixtures/griffe_pkg/bad_docstrings.py`

### Change Log

- 2026-02-11: Implemented Story 7.1 — core griffe compatibility check function (`check_griffe_compat`). Added 3 griffe rules (griffe-missing-type, griffe-unknown-param, griffe-format-warning) with warning capture via custom logging handler, griffe object tree walking with alias/file filtering, and layered exception handling. 45 tests (40 unit, 5 integration).
- 2026-02-11: Code review fixes — (H1) Added `bad_format` fixture function triggering `griffe-format-warning` and integration test covering all 3 rule types for AC #21. (M1) Strengthened assertions in `test_happy_path_unknown_param` (4→6 fields) and `test_happy_path_format_warning` (2→6 fields). (M2) Restructured `check_griffe_compat` to match architecture spec: `src_root.iterdir()` now inside try/finally, renamed `logger` to `griffe_logger`. (M3) Checked off quality checklist items. 603 tests, 0 regressions.
