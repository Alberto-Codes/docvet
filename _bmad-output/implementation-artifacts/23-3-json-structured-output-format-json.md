# Story 23.3: JSON Structured Output (`--format json`)

Status: review
Branch: `feat/cli-23-3-json-structured-output`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an AI agent or CI pipeline consuming docvet output,
I want a `--format json` flag that produces structured JSON output,
so that I can parse findings programmatically without regex on text output.

## Acceptance Criteria

1. **Given** a user runs `docvet check --format json`, **when** findings exist, **then** stdout contains a JSON object with a `findings` array where each finding has: `file`, `line`, `symbol`, `rule`, `message`, `category`, `severity` — where `severity` is `"high"` for `required` findings and `"low"` for `recommended` findings (FR130).

2. **Given** a user runs `docvet check --format json`, **when** the check completes, **then** the JSON object includes a `summary` with: `total` count, `by_category` counts, and `files_checked` count (FR131).

3. **Given** a user runs `docvet check --format json`, **when** findings exist, **then** the exit code is 1; when no findings exist, exit code is 0 — identical to text mode (FR132).

4. **Given** a user runs any subcommand with `--format json`, **when** `enrichment`, `freshness`, `coverage`, or `griffe` is invoked, **then** all subcommands produce the same JSON schema (FR133).

5. **Given** a user runs `docvet check --format text` or omits `--format`, **when** the default format is used, **then** output is identical to current behavior (no regression).

6. **Given** a user runs `docvet check --format json` with no findings, **when** the check completes, **then** stdout contains a JSON object with an empty `findings` array and `summary.total` of 0.

## Tasks / Subtasks

- [x] Task 1: Add `JSON` value to `OutputFormat` enum (AC: #1, #4)
  - [x] 1.1 Add `JSON = "json"` to `OutputFormat` in `cli.py`
  - [x] 1.2 Update `main()` docstring to mention json format
- [x] Task 2: Create `format_json()` in `reporting.py` (AC: #1, #2, #6)
  - [x] 2.1 Create `format_json(findings, file_count)` that returns a JSON string
  - [x] 2.2 Map `category` to `severity` in serialization: `"required"` -> `"high"`, `"recommended"` -> `"low"`
  - [x] 2.3 Build `summary` object with `total`, `by_category`, `files_checked`
  - [x] 2.4 Always return a valid JSON object (empty `findings` array when no findings)
- [x] Task 3: Update `_output_and_exit()` to handle JSON format (AC: #1, #3, #5, #6)
  - [x] 3.1 Add `"json"` branch to format resolution in `_output_and_exit`
  - [x] 3.2 Pass `file_count` to `format_json()` for the `files_checked` summary field
  - [x] 3.3 Always emit JSON to stdout (even when no findings — empty array)
  - [x] 3.4 Ensure exit code logic is unchanged (still uses `determine_exit_code`)
- [x] Task 4: Update `write_report()` to handle JSON format (AC: #1)
  - [x] 4.1 Add `"json"` case to `write_report()` in `reporting.py`
- [x] Task 5: Write unit tests for `format_json()` (AC: #1, #2, #6)
  - [x] 5.1 Test JSON output contains all 7 finding fields (file, line, symbol, rule, message, category, severity)
  - [x] 5.2 Test severity mapping: required -> high, recommended -> low
  - [x] 5.3 Test summary object with total, by_category, files_checked
  - [x] 5.4 Test empty findings produces valid JSON with empty array and zero summary
  - [x] 5.5 Test findings are sorted by (file, line) like other formats
  - [x] 5.6 Test output is valid parseable JSON (json.loads round-trip)
- [x] Task 6: Write CLI integration tests for `--format json` (AC: #1, #3, #4, #5)
  - [x] 6.1 Test `--format json` with findings produces valid JSON on stdout with exit code 1
  - [x] 6.2 Test `--format json` with no findings produces JSON with empty array and exit code 0
  - [x] 6.3 Test all 5 subcommands accept `--format json` (check, enrichment, freshness, coverage, griffe)
  - [x] 6.4 Test `--format text` (default) is unchanged
  - [x] 6.5 Test `--format json --output report.json` writes JSON to file
- [x] Task 7: Update documentation (AC: #1)
  - [x] 7.1 Update `docs/site/cli-reference.md` to document `--format json`
- [x] Task 8: Run quality gates (AC: #1-#6)
  - [x] 8.1 All 6 quality gates pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 (7 fields + severity) | `TestFormatJson::test_all_seven_fields_present`, `test_severity_mapping_required_to_high`, `test_severity_mapping_recommended_to_low`, `test_field_values_preserved_exactly`, `TestOutputAndExit::test_format_json_calls_format_json_with_findings` | PASS |
| AC2 (summary object) | `TestFormatJson::test_summary_structure`, `test_empty_findings_produces_valid_json_with_zero_summary` | PASS |
| AC3 (exit codes) | `test_check_with_format_json_exit_code_1_when_findings`, `test_check_with_format_json_valid_json_output` (exit 0) | PASS |
| AC4 (all subcommands) | `test_check_when_invoked_with_format_json_exits_successfully`, `test_enrichment_when_invoked_...`, `test_freshness_when_invoked_...`, `test_coverage_when_invoked_...`, `test_griffe_when_invoked_...` | PASS |
| AC5 (no regression) | `test_check_with_format_text_output_unchanged` | PASS |
| AC6 (empty JSON) | `TestFormatJson::test_empty_findings_produces_valid_json_with_zero_summary`, `TestOutputAndExit::test_format_json_emits_even_with_zero_findings`, `test_check_with_format_json_empty_findings_returns_empty_array` | PASS |

## Dev Notes

### Design: Severity Derivation (Not a New Field)

The `Finding` dataclass has a documented "6-field shape is stable for v1" contract. Do NOT add a `severity` field to `Finding`. Instead, derive severity from `category` during JSON serialization:

```python
_CATEGORY_TO_SEVERITY: dict[str, str] = {
    "required": "high",
    "recommended": "low",
}
```

This mapping lives in `reporting.py` alongside the existing `_COLORS` mapping. The `severity` key appears only in JSON output — it is not part of the `Finding` dataclass. `severity` has exactly two values (`"high"`, `"low"`) and is a convenience alias derived from `category` — it is not a separate signal. Document this in the CLI reference so consumers do not assume richer granularity.

### Design: JSON Schema (NFR68 — Stable Contract)

The JSON output schema is part of the v1 API commitment. Field names and structure must not change:

```json
{
  "findings": [
    {
      "file": "src/foo.py",
      "line": 42,
      "symbol": "my_func",
      "rule": "missing-raises",
      "message": "Function 'my_func' raises ValueError but...",
      "category": "required",
      "severity": "high"
    }
  ],
  "summary": {
    "total": 1,
    "by_category": {
      "required": 1,
      "recommended": 0
    },
    "files_checked": 12
  }
}
```

When no findings exist, output an object with an empty `findings` array and zeroed summary — never omit the top-level keys.

### Design: `format_json()` Signature

```python
def format_json(findings: list[Finding], file_count: int) -> str:
```

Unlike `format_terminal()` and `format_markdown()`, `format_json()` takes a `file_count` parameter because the JSON schema includes `summary.files_checked`. This is needed because `file_count` comes from the CLI layer, not from the findings themselves.

### Design: Output Pipeline Changes

In `_output_and_exit()` (cli.py:239), the JSON format integrates into the existing pipeline:

1. **Format resolution**: JSON is never auto-selected. It must be explicitly requested via `--format json`. The current auto-selection logic (`terminal` for stdout, `markdown` for `--output`) is unchanged.
2. **Always emit**: Unlike terminal/markdown (which return empty string for zero findings), JSON always emits a full object to stdout — agents need parseable output even on clean runs.
3. **no_color**: Irrelevant for JSON. No change needed.
4. **Summary on stderr**: The `format_summary()` line still goes to stderr when `--format json` (unless `--quiet`). The JSON blob is stdout-only.
5. **Exit code**: Unchanged — `determine_exit_code()` is format-independent.

### Design: `write_report()` Extension

Add `"json"` as a valid `fmt` value in `write_report()`. When writing JSON to a file via `--format json --output report.json`, use `format_json()` with the `file_count` parameter. This means `write_report()` needs a `file_count` parameter (defaulting to 0 for backward compatibility) — or pass the pre-formatted JSON string.

Simpler approach: have `_output_and_exit()` always produce the formatted string first, then either write to file or stdout. This avoids changing `write_report()`'s signature. Check how markdown/terminal paths currently handle this — they call `write_report()` which internally calls `format_*()`. For JSON, either:
- Add `file_count` parameter to `write_report()` (slight signature change, but `write_report` is `__all__ = []` — internal)
- Or write the formatted JSON string directly in `_output_and_exit()` and bypass `write_report()` for JSON

Recommendation: Add `file_count: int = 0` parameter to `write_report()` — minimal change, backward compatible.

### What NOT to Change

- Do NOT modify the `Finding` dataclass — no new fields, no breaking the 6-field v1 contract
- Do NOT change `determine_exit_code()` — exit codes are format-independent
- Do NOT change any check module (enrichment, freshness, coverage, griffe)
- Do NOT change discovery or config — this is purely output-layer
- Do NOT suppress progress/summary on stderr for `--format json` — stderr is for humans, stdout is for machines. Agents can use `--quiet` if they want clean stderr.
- Do NOT use `dataclasses.asdict()` — it doesn't produce the `severity` field. Build the dict manually.

### Serialization: Use `json.dumps()` (stdlib)

Use `json.dumps(obj, indent=2)` for human-readable JSON. No new dependencies — `json` is stdlib. Add `ensure_ascii=False` to preserve unicode in messages. **Whitespace and indentation are NOT part of the schema contract** — consumers must parse with `json.loads()`, not rely on formatting. This matches ruff's convention (pretty-printed but no formatting guarantee).

### Scope: No `json-lines` Support

The epic specifies `--format json` only. Do NOT implement `--format json-lines` (NDJSON / one-object-per-line). If streaming output becomes relevant, that's a separate future story. Stick to the single JSON object envelope.

### Key Source Files

| File | Lines | Relevance |
|------|-------|-----------|
| `src/docvet/cli.py` | 68-86 | `OutputFormat` enum — add JSON |
| `src/docvet/cli.py` | 239-302 | `_output_and_exit` — add JSON branch |
| `src/docvet/cli.py` | 542-598 | `main()` callback — `--format` option already handles `OutputFormat` |
| `src/docvet/reporting.py` | Full | Add `format_json()`, update `write_report()` |
| `src/docvet/checks/_finding.py` | Full | DO NOT MODIFY — reference only |
| `tests/unit/test_reporting.py` | Full | Add `format_json` tests |
| `tests/unit/test_cli.py` | Full | Add `--format json` CLI tests |
| `docs/site/cli-reference.md` | TBD | Document `--format json` |

### Previous Story Intelligence (23.2)

- **CLI test pattern**: Tests use `CliRunner` from `typer.testing` with an autouse fixture that mocks `load_config`, `discover_files`, and all 4 `_run_*` functions. Follow this exact pattern.
- **Typer error messages**: Long error messages get word-wrapped by typer's rich box formatting (~62 usable chars per line), breaking substring test assertions. Keep messages short.
- **Quality gates**: 909 tests at end of 23.2. All 6 gates pass.
- **Zero-debug goal**: Stories 23.1 and 23.2 were both zero-debug implementations. Aim for the same.
- **docvet dogfooding**: After modifying `cli.py` or `reporting.py`, run `docvet check --all` — it will flag stale docstrings if module docstrings aren't updated.

### Git Intelligence

Recent commits (last 5):
- `dee57cc feat(cli): add positional file arguments to all subcommands (#175)`
- `e418fbc feat(ci): add cross-platform CI matrix and path normalization (#174)`
- `4f49014 chore(meta): audit and expand discoverability metadata (#173)`
- `4ff286f feat(docs): add CONTRIBUTING.md contributor guide (#172)`
- `bc662a2 feat(docs): add AGENTS.md and AI Agent Integration docs page (#171)`

The CLI surface (`cli.py`) was last modified in story 23.2 (positional args). The reporting module has not changed since Epic 21 (output overhaul). Both are stable.

### Project Structure Notes

- All production changes stay within `cli.py` and `reporting.py` — no new modules
- Test additions go in existing `tests/unit/test_reporting.py` and `tests/unit/test_cli.py`
- Doc updates in `docs/site/cli-reference.md`

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 23, Story 23.3]
- [Source: GitHub Issue #151 — feat: add structured JSON output]
- [Source: src/docvet/cli.py:68-86 — `OutputFormat` enum]
- [Source: src/docvet/cli.py:239-302 — `_output_and_exit` pipeline]
- [Source: src/docvet/reporting.py — format_terminal, format_markdown, write_report]
- [Source: src/docvet/checks/_finding.py — Finding 6-field v1 contract]

### Documentation Impact

- Pages: `docs/site/cli-reference.md`
- Nature of update: Add `json` to the `--format` option values table, add a "JSON Output" section with schema example and usage examples for CI/agent integration

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 932 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug implementation.

### Completion Notes List

- `format_json()` derives severity from category at serialization time, preserving the 6-field Finding contract
- JSON branch in `_output_and_exit()` always emits (even empty findings), unlike terminal/markdown
- `_extract_json()` helper handles CliRunner mixed stderr/stdout output in tests
- Fixed 3 ty type errors by moving `format_json` mock into `_mock_reporting` fixture instead of manual monkey-patching
- Fixed 4 docvet freshness findings by updating docstrings on `_output_and_exit`, `FreshnessMode`, `format_markdown`, `format_summary`

### Change Log

- `src/docvet/cli.py`: Added `JSON = "json"` to `OutputFormat` enum, added `format_json` import, added JSON branch in `_output_and_exit()`, updated docstrings
- `src/docvet/reporting.py`: Added `format_json()`, `_CATEGORY_TO_SEVERITY` mapping, updated `write_report()` with `file_count` param and JSON case, updated module docstring
- `tests/unit/test_reporting.py`: Added `TestFormatJson` (9 tests), `TestWriteReportJson` (2 tests), updated `test_invalid_fmt_raises` to use `"xml"`
- `tests/unit/test_cli.py`: Added `_extract_json()` helper, 3 `TestOutputAndExit` JSON tests, 5 subcommand acceptance tests, 4 functional JSON tests
- `docs/site/cli-reference.md`: Added `json` to `--format` values, JSON Output section, JSON example commands

### File List

| File | Action |
|------|--------|
| `src/docvet/cli.py` | Modified |
| `src/docvet/reporting.py` | Modified |
| `tests/unit/test_cli.py` | Modified |
| `tests/unit/test_reporting.py` | Modified |
| `docs/site/cli-reference.md` | Modified |

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
