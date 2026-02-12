# Story 8.2: Core Reporting Functions

Status: ready-for-dev

## Story

As a developer,
I want a reporting module with pure formatting functions and exit code logic,
So that findings can be rendered consistently for terminal, markdown, and CI contexts.

## Acceptance Criteria

1. **Given** a list of findings from multiple files
   **When** `format_terminal(findings)` is called
   **Then** it returns a string with one `file:line: rule message [category]` line per finding, findings sorted by `(file, line)`, blank lines between file groups, and a summary line

2. **Given** a list of findings all from the same file
   **When** `format_terminal(findings)` is called
   **Then** no blank-line separators appear between findings (blank lines only separate different file groups)

3. **Given** a list of findings with mixed categories
   **When** `format_terminal(findings, no_color=False)` is called (default)
   **Then** `[required]` tags are colored red and `[recommended]` tags are colored yellow via ANSI codes
   **And** the rest of each line (file, line number, rule, message) is uncolored

4. **Given** a list of findings
   **When** `format_terminal(findings, no_color=True)` is called
   **Then** the output contains zero ANSI escape sequences (`\033[` not present)
   **And** all content is otherwise identical to the colored version

5. **Given** an empty list of findings
   **When** `format_terminal([])` is called
   **Then** it returns an empty string (no summary line, no headers, no newlines)

6. **Given** a list of findings from multiple files
   **When** `format_markdown(findings)` is called
   **Then** it returns a valid GFM markdown table with columns: File, Line, Rule, Symbol, Message, Category
   **And** findings are sorted by `(file, line)`
   **And** a bold summary line is appended: `**N findings** (X required, Y recommended)`

7. **Given** a finding whose message contains a pipe character `|`
   **When** `format_markdown(findings)` is called
   **Then** the pipe is escaped as `\|` in the table cell to prevent GFM table breakage

8. **Given** an empty list of findings
   **When** `format_markdown([])` is called
   **Then** it returns an empty string

9. **Given** `format_markdown` output
   **When** examined for ANSI escape sequences
   **Then** none are present (markdown output is always ANSI-free regardless of any parameter)

10. **Given** 12 files and checks `["enrichment", "freshness"]`
    **When** `format_verbose_header(12, ["enrichment", "freshness"])` is called
    **Then** it returns `"Checking 12 files [enrichment, freshness]\n"`

11. **Given** findings and an output path with an existing parent directory
    **When** `write_report(findings, output_path, fmt="markdown")` is called
    **Then** it writes the `format_markdown` output to the file

12. **Given** findings and `fmt="terminal"`
    **When** `write_report(findings, output_path, fmt="terminal")` is called
    **Then** it writes `format_terminal` output with `no_color=True` (ANSI always stripped for files)

13. **Given** an output path whose parent directory does not exist
    **When** `write_report(findings, output_path)` is called
    **Then** it raises `FileNotFoundError`

14. **Given** `findings_by_check = {"enrichment": [finding1], "freshness": []}` and `config.fail_on = ["enrichment"]`
    **When** `determine_exit_code(findings_by_check, config)` is called
    **Then** it returns `1` (enrichment is in fail_on and has findings)

15. **Given** `findings_by_check = {"enrichment": [finding1]}` and `config.fail_on = []`
    **When** `determine_exit_code(findings_by_check, config)` is called
    **Then** it returns `0` (no checks in fail_on, all findings are advisory)

16. **Given** `findings_by_check = {"enrichment": [], "freshness": []}` (all empty)
    **When** `determine_exit_code(findings_by_check, config)` is called
    **Then** it returns `0` regardless of `fail_on` contents

17. **Given** `findings_by_check = {"freshness": [finding1]}` and `config.fail_on = ["enrichment"]`
    **When** `determine_exit_code(findings_by_check, config)` is called
    **Then** it returns `0` (freshness is not in fail_on)

18. **Given** two findings with the same `(file, line)` but different rules
    **When** either formatter is called
    **Then** they appear in stable order (matching insertion/check execution order)

19. **Given** a list of findings with count > 0
    **When** either formatter produces a summary line
    **Then** it always shows both category counts: `N findings (X required, Y recommended)` — even when one count is zero

20. **Given** `format_terminal` output for findings from multiple files
    **When** examined for visual structure
    **Then** a blank line appears before the summary line (matches ruff convention)

21. **Given** an empty findings list
    **When** `write_report([], output_path)` is called
    **Then** the file is written with empty content (empty string from formatter)

22. **Given** `findings_by_check = {"enrichment": [f1]}` and `config.fail_on = ["enrichment", "freshness"]`
    **When** `determine_exit_code(findings_by_check, config)` is called
    **Then** it returns `1` (enrichment is in fail_on and has findings — missing freshness key doesn't matter)

## Tasks / Subtasks

- [ ] Task 1: Create `src/docvet/reporting.py` with module structure (AC: all)
  - [ ] Add `from __future__ import annotations` and module docstring
  - [ ] Add imports: `collections.Counter`, `itertools.groupby`, `pathlib.Path`, `collections.abc.Sequence`
  - [ ] Add `typer` import for `typer.style()` and `typer.colors`
  - [ ] Add `Finding` import from `docvet.checks`
  - [ ] Add `DocvetConfig` import from `docvet.config`
  - [ ] Define `_COLORS` constant dict mapping `"required"` to `typer.colors.RED`, `"recommended"` to `typer.colors.YELLOW`

- [ ] Task 2: Implement `_colorize` helper (AC: #3, #4)
  - [ ] Signature: `_colorize(text: str, color: str, *, no_color: bool) -> str`
  - [ ] If `no_color` is True, return `text` unchanged
  - [ ] Otherwise return `typer.style(text, fg=color)`

- [ ] Task 3: Implement `format_terminal` (AC: #1, #2, #3, #4, #5, #18, #19, #20)
  - [ ] Signature: `format_terminal(findings: list[Finding], *, no_color: bool = False) -> str`
  - [ ] Return `""` if `not findings`
  - [ ] Sort by `(file, line)` via `sorted(findings, key=lambda f: (f.file, f.line))`
  - [ ] Use `itertools.groupby` on `f.file` for file grouping
  - [ ] Insert blank line (`""`) between file groups (check `if lines:` before each group)
  - [ ] Format each line: `f"{finding.file}:{finding.line}: {finding.rule} {finding.message} {tag}"`
  - [ ] `tag = _colorize(f"[{finding.category}]", _COLORS[finding.category], no_color=no_color)`
  - [ ] Append blank line before summary, then summary: `f"{len(findings)} findings ({counts['required']} required, {counts['recommended']} recommended)"`
  - [ ] Use `Counter(f.category for f in findings)` for counts
  - [ ] Return `"\n".join(lines) + "\n"`

- [ ] Task 4: Implement `format_markdown` (AC: #6, #7, #8, #9, #18, #19)
  - [ ] Signature: `format_markdown(findings: list[Finding]) -> str`
  - [ ] Return `""` if `not findings`
  - [ ] Sort by `(file, line)` (same as terminal)
  - [ ] Build GFM table with header: `| File | Line | Rule | Symbol | Message | Category |`
  - [ ] Add separator: `|------|------|------|--------|---------|----------|`
  - [ ] For each finding: `| {file} | {line} | {rule} | {symbol} | {escaped_message} | {category} |`
  - [ ] Escape pipes in message: `finding.message.replace("|", "\\|")`
  - [ ] Append blank line before summary
  - [ ] Summary: `f"**{len(findings)} findings** ({counts['required']} required, {counts['recommended']} recommended)"`
  - [ ] Return `"\n".join(lines) + "\n"`

- [ ] Task 5: Implement `format_verbose_header` (AC: #10)
  - [ ] Signature: `format_verbose_header(file_count: int, checks: Sequence[str]) -> str`
  - [ ] Return `f"Checking {file_count} files [{', '.join(checks)}]\n"`

- [ ] Task 6: Implement `write_report` (AC: #11, #12, #13, #21)
  - [ ] Signature: `write_report(findings: list[Finding], output: Path, *, fmt: str = "markdown") -> None`
  - [ ] If `fmt == "markdown"`: content = `format_markdown(findings)`
  - [ ] If `fmt == "terminal"`: content = `format_terminal(findings, no_color=True)`
  - [ ] Write content to `output` via `output.write_text(content)`
  - [ ] Let `FileNotFoundError` propagate naturally from `write_text` if parent doesn't exist

- [ ] Task 7: Implement `determine_exit_code` (AC: #14, #15, #16, #17, #22)
  - [ ] Signature: `determine_exit_code(findings_by_check: dict[str, list[Finding]], config: DocvetConfig) -> int`
  - [ ] For each check name in `config.fail_on`: if `findings_by_check.get(check, [])` is non-empty, return `1`
  - [ ] Otherwise return `0`

- [ ] Task 8: Create `tests/unit/test_reporting.py` with formatter tests (AC: #1-#9, #18-#20)
  - [ ] Test `format_terminal` with multi-file findings: assert sorted output, file grouping, summary line
  - [ ] Test `format_terminal` with single-file findings: no blank-line separators between findings
  - [ ] Test `format_terminal` with `no_color=False`: assert `"\033["` present in output
  - [ ] Test `format_terminal` with `no_color=True`: assert `"\033["` not in output
  - [ ] Test `format_terminal` with empty list: assert returns `""`
  - [ ] Test `format_terminal` summary shows both counts including zeros
  - [ ] Test `format_terminal` blank line before summary
  - [ ] Test `format_terminal` stable sort: two findings with same `(file, line)` preserve insertion order
  - [ ] Test `format_terminal` with 3+ files: verify multiple blank-line separators between groups
  - [ ] Test `format_markdown` with multi-file findings: assert table format, sorted, bold summary
  - [ ] Test `format_markdown` with pipe in message: assert `\|` escape
  - [ ] Test `format_markdown` with empty list: assert returns `""`
  - [ ] Test `format_markdown` no ANSI codes with mixed-category findings (assert `"\033["` not in result — use both required and recommended to cover all code paths)
  - [ ] Test `format_markdown` stable sort: two findings with same `(file, line)` preserve insertion order
  - [ ] Test `format_markdown` summary shows both counts including zeros

- [ ] Task 9: Add `format_verbose_header` tests (AC: #10)
  - [ ] Test with sample inputs: `format_verbose_header(12, ["enrichment", "freshness"])` returns `"Checking 12 files [enrichment, freshness]\n"`
  - [ ] Test with single check
  - [ ] Test with 4 checks (all enabled)

- [ ] Task 10: Add `write_report` tests (AC: #11, #12, #13, #21)
  - [ ] Test markdown write: write to `tmp_path / "report.md"`, read back, assert matches `format_markdown` output
  - [ ] Test terminal write: write with `fmt="terminal"`, read back, assert content matches `format_terminal(findings, no_color=True)` output exactly (verifies both ANSI stripping and content correctness)
  - [ ] Test missing parent directory: `tmp_path / "nonexistent" / "report.md"` raises `FileNotFoundError`
  - [ ] Test empty findings write: writes empty content to file

- [ ] Task 11: Add `determine_exit_code` tests (AC: #14, #15, #16, #17, #22)
  - [ ] Test fail_on check with findings: returns 1
  - [ ] Test empty fail_on: returns 0 regardless of findings
  - [ ] Test all empty findings: returns 0 regardless of fail_on
  - [ ] Test findings in non-fail_on check: returns 0
  - [ ] Test fail_on with missing key in findings_by_check: returns 1 if another fail_on check has findings
  - [ ] Test fail_on with check name not in findings_by_check: returns 0 (`.get()` returns empty list)
  - [ ] Test completely empty findings_by_check dict `{}` with non-empty fail_on: returns 0

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|

## Dev Notes

### Architecture Reference

This story creates `src/docvet/reporting.py` — a new module with 5 public functions and 1 private helper. All formatting functions are **pure** (no I/O, no env inspection, no side effects). Only `write_report` performs file I/O.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Module sections]

### File Organization Within `reporting.py`

```python
# 1. from __future__ import annotations
# 2. Imports (stdlib: collections, itertools, pathlib; third-party: typer; local: Finding, DocvetConfig)
# 3. Constants (_COLORS dict)
# 4. Private helpers (_colorize)
# 5. Public functions (format_terminal, format_markdown, format_verbose_header, write_report, determine_exit_code)
```

Order: constants -> helpers -> public functions. Matches established pattern from all check modules.

[Source: `_bmad-output/planning-artifacts/architecture.md` → File Organization Within `reporting.py`]

### Function Signatures (Architecture-Mandated)

```python
def _colorize(text: str, color: str, *, no_color: bool) -> str: ...
def format_terminal(findings: list[Finding], *, no_color: bool = False) -> str: ...
def format_markdown(findings: list[Finding]) -> str: ...
def format_verbose_header(file_count: int, checks: Sequence[str]) -> str: ...
def write_report(findings: list[Finding], output: Path, *, fmt: str = "markdown") -> None: ...
def determine_exit_code(findings_by_check: dict[str, list[Finding]], config: DocvetConfig) -> int: ...
```

**Critical:** `format_terminal` has NO `verbose` parameter. Verbose header is handled separately by `format_verbose_header` (printed to stderr by CLI in Story 8.3). `format_terminal` with empty input returns `""` regardless.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 1, Decision 2, Architectural Boundaries]

### String Building Pattern

Build a `list[str]` of output lines, join with `"\n"` at the end, append trailing `"\n"`. Never use `io.StringIO`, never use `+=` string concatenation. Never use `print()` inside formatting functions — they return strings, not print.

```python
lines: list[str] = []
# ... build lines ...
lines.append("")       # blank line before summary
lines.append(summary)
return "\n".join(lines) + "\n"
```

[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 1: String Building Pattern]

### Terminal Line Format

```
src/core/engine.py:23: missing-raises Function 'process_batch' raises ValueError but has no Raises: section [required]
```

Only `[category]` is ANSI-colored (red for required, yellow for recommended). Everything else is uncolored.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 6: Terminal Line Format]

### File Grouping (Terminal Only)

Use `itertools.groupby` on sorted findings to group by file. Insert blank line between groups. No file header lines, no indentation. Each line is self-contained and independently greppable.

```python
for file_path, group in groupby(sorted_findings, key=lambda f: f.file):
    if lines:
        lines.append("")  # blank line between file groups
    for finding in group:
        tag = _colorize(f"[{finding.category}]", _COLORS[finding.category], no_color=no_color)
        lines.append(f"{finding.file}:{finding.line}: {finding.rule} {finding.message} {tag}")
```

[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 3: File Grouping Pattern]

### Summary Line Format

- Terminal: `5 findings (3 required, 2 recommended)` — no bold, no color
- Markdown: `**5 findings** (3 required, 2 recommended)` — bold total count only
- Always show both category counts even when zero
- Use `Counter(f.category for f in findings)` for counts — `Counter` returns `0` for missing keys, so `counts['required']` and `counts['recommended']` are safe even if all findings are one category (no guard needed)
- Guard with `if findings:` — never produce summary for empty list

[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 5: Summary Line Format]

### ANSI Color Application

```python
_COLORS: dict[str, str] = {
    "required": typer.colors.RED,
    "recommended": typer.colors.YELLOW,
}

def _colorize(text: str, color: str, *, no_color: bool) -> str:
    if no_color:
        return text
    return typer.style(text, fg=color)
```

`format_markdown` never calls `_colorize` — markdown is ANSI-free by design.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 4: ANSI Color Application]

### Pipe Escape in Markdown

`finding.message.replace("|", "\\|")` before inserting into GFM table rows. Apply to `message` field only.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Gap Analysis, item 3]

### `determine_exit_code` Logic

Pure function. For each check name in `config.fail_on`, check if `findings_by_check.get(check, [])` is non-empty. Return `1` on first match, `0` otherwise. No mocking needed for tests — construct dict and config directly.

[Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 5, Architectural Boundaries]

### `write_report` Behavior

- `fmt="markdown"` -> call `format_markdown(findings)`
- `fmt="terminal"` -> call `format_terminal(findings, no_color=True)` (ANSI always stripped for files)
- Let `FileNotFoundError` propagate naturally from `Path.write_text()` if parent dir missing
- Never silently create parent directories

[Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 4]

### Test Patterns

- Use `make_finding` factory fixture from `tests/conftest.py` (established in Story 8.1)
- Assert exact output strings for small inputs (2-3 findings)
- Assert `"\033[" not in result` when `no_color=True` — input must have at least one finding
- Assert `"\033[" in result` when `no_color=False` — input must have at least one finding
- Assert `result == ""` when findings list is empty
- Use `tmp_path` for all `write_report` file I/O tests
- `determine_exit_code` tests: pure function — construct `dict[str, list[Finding]]` and `DocvetConfig` directly, no mocking
- Stable sort test: two findings with same `(file, line)` but different rules — verify order matches insertion order

[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 7: Test Patterns]

### Previous Story Intelligence (Story 8.1)

- `make_finding` fixture is already available in `tests/conftest.py` — reuse it, do not duplicate
- `Finding` dataclass is frozen with 6 fields: `file`, `line`, `symbol`, `rule`, `message`, `category`
- `category` is `Literal["required", "recommended"]`
- Story 8.1 completed cleanly with zero debug issues — architecture spec quality proven again
- 634 tests total after Story 8.1
- Import `Finding` from `docvet.checks`, `DocvetConfig` from `docvet.config`

### Git Intelligence

Recent commits follow established patterns:
- `refactor(cli): return list[Finding] from check runners (#46)` — Story 8.1 just completed
- Consistent conventional commit format: `type(scope): description`
- PR numbering continues incrementally

### Project Structure Notes

- **New file:** `src/docvet/reporting.py` — sibling to `cli.py`, NOT inside `checks/`
- **New file:** `tests/unit/test_reporting.py` — mirrors source layout
- Import direction: `cli.py` imports from `reporting.py`; `reporting.py` imports from `checks/__init__.py` and `config.py`. No reverse imports.
- No cross-imports with check modules (enrichment, freshness, coverage, griffe_compat)

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Module — Project Context Analysis]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Core Architectural Decisions (Decisions 1-6)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Implementation Patterns (Patterns 1-7)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Project Structure & Boundaries]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Architecture Validation Results]
- [Source: `_bmad-output/planning-artifacts/epics.md` → Epic 8, Story 8.2 ACs]
- [Source: `_bmad-output/planning-artifacts/prd.md` → FR98-FR110, NFR49-NFR54]
- [Source: `_bmad-output/implementation-artifacts/8-1-cli-refactor-return-findings-from-check-runners.md` → Previous story learnings]
- [Source: `_bmad-output/project-context.md` → Technology Stack, Testing Rules, Framework Rules]
- [Source: `src/docvet/checks/__init__.py` → Finding dataclass]
- [Source: `src/docvet/config.py` → DocvetConfig, fail_on/warn_on fields]
- [Source: `tests/conftest.py` → make_finding fixture]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
