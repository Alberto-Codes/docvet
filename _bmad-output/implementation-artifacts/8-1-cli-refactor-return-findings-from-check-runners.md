# Story 8.1: CLI Refactor — Return Findings from Check Runners

Status: ready-for-dev

## Story

As a developer,
I want the CLI check runners to return structured findings instead of printing inline,
So that findings can be routed to a unified reporting pipeline for formatting and CI exit code logic.

## Acceptance Criteria

1. **Given** `_run_enrichment` processing files with enrichment findings
   **When** `_run_enrichment(files, config)` is called
   **Then** it returns a `list[Finding]` containing all enrichment findings across all files
   **And** no `typer.echo()` calls are made for individual findings

2. **Given** `_run_freshness` in diff mode processing files with freshness findings
   **When** `_run_freshness(...)` is called in diff mode
   **Then** it returns a `list[Finding]` containing all diff-mode findings
   **And** the early return pattern with two separate branches is preserved

3. **Given** `_run_freshness` in drift mode processing files with freshness findings
   **When** `_run_freshness(...)` is called in drift mode
   **Then** it returns a `list[Finding]` containing all drift-mode findings

4. **Given** `_run_coverage` processing files with coverage findings
   **When** `_run_coverage(files, config)` is called
   **Then** it returns a `list[Finding]` containing all coverage findings

5. **Given** `_run_griffe` processing files with griffe findings
   **When** `_run_griffe(files, config)` is called
   **Then** it returns a `list[Finding]` containing all griffe findings
   **And** all skip paths (`find_spec` check, `src_root.is_dir()`) return `[]` not `None`

6. **Given** `_run_griffe` when griffe is not installed
   **When** `_run_griffe(files, config)` is called
   **Then** it returns an empty list `[]`
   **And** the existing stderr warning about griffe not installed is preserved

7. **Given** existing stderr messages in `_run_*` functions (warnings, verbose notes)
   **When** any `_run_*` function is called
   **Then** all existing stderr messages are preserved unchanged (only finding-printing `typer.echo()` calls are removed)

8. **Given** a `pyproject.toml` with a check name appearing in both `fail-on` and `warn-on`
   **When** the config is loaded
   **Then** a warning is printed to stderr: `docvet: '<check>' appears in both fail-on and warn-on; using fail-on`
   **And** the check name is dropped from `warn_on` (fail_on precedence)

9. **Given** a shared test fixture `make_finding`
   **When** `tests/conftest.py` is imported
   **Then** a `make_finding` factory fixture is available that creates `Finding` instances with sensible defaults for all 6 fields

10. **Given** existing CLI tests for `_run_*` functions
    **When** tests are updated
    **Then** they verify the new `list[Finding]` return type
    **And** existing behavior tests (file discovery, config loading) continue to pass

## Tasks / Subtasks

- [ ] Task 1: Refactor `_run_enrichment` to return `list[Finding]` (AC: #1, #7)
  - [ ] Remove `typer.echo()` loop for findings
  - [ ] Add `all_findings: list[Finding] = []` accumulator
  - [ ] Replace echo loop with `all_findings.extend(findings)`
  - [ ] Return `all_findings`
  - [ ] Keep stderr `SyntaxError` warning unchanged

- [ ] Task 2: Refactor `_run_freshness` to return `list[Finding]` (AC: #2, #3, #7)
  - [ ] Add `all_findings` accumulator in drift branch (lines 265-280)
  - [ ] Replace drift echo loop with `all_findings.extend(findings)`
  - [ ] Return `all_findings` from drift branch
  - [ ] Add `all_findings` accumulator in diff branch (lines 282-294)
  - [ ] Replace diff echo loop with `all_findings.extend(findings)`
  - [ ] Return `all_findings` from diff branch
  - [ ] Keep stderr `SyntaxError` warning unchanged in both branches

- [ ] Task 3: Refactor `_run_coverage` to return `list[Finding]` (AC: #4)
  - [ ] Return `check_coverage(...)` result directly (already returns `list[Finding]`)
  - [ ] Remove echo loop

- [ ] Task 4: Refactor `_run_griffe` to return `list[Finding]` (AC: #5, #6, #7)
  - [ ] Change `find_spec` skip path (line 328-333) to `return []`
  - [ ] Change `src_root.is_dir()` skip path (line 335-336) to `return []`
  - [ ] Add `all_findings` accumulator and replace echo loop
  - [ ] Return `all_findings`
  - [ ] Keep stderr warning messages unchanged

- [ ] Task 5: Add `fail_on`/`warn_on` overlap warning in `config.py` (AC: #8)
  - [ ] In `load_config`, after computing `fail_on_set` (line 409)
  - [ ] For each check in `warn_on` that appears in `fail_on_set`, print stderr warning
  - [ ] Warning format: `docvet: '<check>' appears in both fail-on and warn-on; using fail-on`
  - [ ] Existing silent-drop behavior (`final_warn_on` line 410) preserved

- [ ] Task 6: Add `make_finding` factory fixture in `tests/conftest.py` (AC: #9)
  - [ ] Import `Finding` from `docvet.checks`
  - [ ] Create `make_finding` fixture with defaults: `file="test.py"`, `line=1`, `symbol="func"`, `rule="test-rule"`, `message="test message"`, `category="required"`

- [ ] Task 7: Update existing CLI tests (AC: #10)
  - [ ] Add direct-call tests for each `_run_*` that assert `list[Finding]` return value and contents
  - [ ] Add direct-call test for `_run_freshness` drift mode with mixed files (some parseable, some SyntaxError) — verify returned list only contains findings from parseable files
  - [ ] Add test for `_run_griffe` skip paths returning `[]` (assert return value, not just output)
  - [ ] Existing `side_effect=_run_*` behavior tests still pass — bridge in subcommands preserves output
  - [ ] Ensure all existing behavior tests (file discovery, config loading) continue to pass

- [ ] Task 8: Add config overlap warning tests in `tests/unit/test_config.py` (AC: #8)
  - [ ] Test overlap emits stderr warning with check name
  - [ ] Test non-overlapping config emits no warning
  - [ ] Existing overlap behavior tests (silent drop) updated with stderr assertions

- [ ] Task 9: Temporarily update subcommand functions to consume `list[Finding]` returns (AC: #1-6)
  - [ ] In `check()` function: capture return values from all 4 `_run_*` calls, echo each finding
  - [ ] In `enrichment()` function: capture `_run_enrichment` return, echo findings
  - [ ] In `freshness()` function: capture `_run_freshness` return, echo findings
  - [ ] In `coverage()` function: capture `_run_coverage` return, echo findings
  - [ ] In `griffe()` function: capture `_run_griffe` return, echo findings
  - [ ] Bridge echo format: `f"{f.file}:{f.line}: {f.rule} {f.message}"` (same as current)
  - [ ] **Location:** Echo loops go in the subcommand functions (`check()`, `enrichment()`, etc.), NOT in `_run_*` functions
  - [ ] This is a bridge — Story 8.3 replaces with `_output_and_exit`

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|

## Dev Notes

### Refactoring Pattern (Architecture Reference)

Each `_run_*` function follows this transformation:

```python
# Before (current):
def _run_enrichment(files: list[Path], config: DocvetConfig) -> None:
    for file_path in files:
        ...
        for finding in findings:
            typer.echo(f"{finding.file}:{finding.line}: {finding.rule} {finding.message}")

# After (refactored):
def _run_enrichment(files: list[Path], config: DocvetConfig) -> list[Finding]:
    all_findings: list[Finding] = []
    for file_path in files:
        ...
        all_findings.extend(findings)
    return all_findings
```

[Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Implementation Patterns, Pattern 6]

### `_run_freshness` Special Case

Has two branches (diff vs drift) with early return. **Keep the early return pattern** — use two separate `all_findings` lists:

```python
def _run_freshness(...) -> list[Finding]:
    if freshness_mode is not FreshnessMode.DIFF:
        all_findings: list[Finding] = []
        for file_path in files:
            ...
            all_findings.extend(findings)
        return all_findings

    all_findings: list[Finding] = []
    for file_path in files:
        ...
        all_findings.extend(findings)
    return all_findings
```

Do NOT restructure to use one list — the early return pattern is architecturally mandated.
[Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 6, `_run_freshness` special case]

### `_run_coverage` Simplification

`check_coverage(src_root, files)` already returns `list[Finding]`. After removing the echo loop, `_run_coverage` can return the result directly:

```python
def _run_coverage(files: list[Path], config: DocvetConfig) -> list[Finding]:
    src_root = config.project_root / config.src_root
    return check_coverage(src_root, files)
```

### `_run_griffe` Skip Paths

All skip paths must return `[]` not `None`. Three exit points:

1. `find_spec` check (line 328-333) — griffe not installed → `return []`
2. `src_root.is_dir()` check (line 335-336) — src root doesn't exist → `return []`
3. Normal path — collect and return findings

Keep all stderr messages (warning about griffe not installed, verbose note) unchanged.

### Config Overlap Warning (AC #8)

In `config.py` `load_config`, insert warning emission **before** the existing silent-drop:

```python
# After computing fail_on_set (line 409 area):
fail_on_set = set(fail_on)
for check in warn_on:
    if check in fail_on_set:
        print(
            f"docvet: '{check}' appears in both fail-on and warn-on; using fail-on",
            file=sys.stderr,
        )
final_warn_on: list[str] = [c for c in warn_on if c not in fail_on_set]
```

[Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 3: fail_on/warn_on Conflict]

### `make_finding` Factory Fixture (AC #9)

Add to `tests/conftest.py`:

```python
@pytest.fixture
def make_finding():
    def _make(*, file="test.py", line=1, symbol="func", rule="test-rule",
              message="test message", category="required"):
        return Finding(file=file, line=line, symbol=symbol, rule=rule,
                       message=message, category=category)
    return _make
```

[Source: `_bmad-output/planning-artifacts/architecture.md` → Shared Test Infrastructure]

### Bridge Pattern for Subcommands (Task 9)

Story 8.3 adds `_output_and_exit` to handle formatting/exit codes. For this story, the **subcommand functions** need a temporary bridge to preserve current terminal output. The bridge echo loops go in the subcommand functions (`check()`, `enrichment()`, `freshness()`, `coverage()`, `griffe()`), **NOT in `_run_*` functions**:

```python
# In enrichment() subcommand function:
findings = _run_enrichment(discovered, config)
for f in findings:
    typer.echo(f"{f.file}:{f.line}: {f.rule} {f.message}")

# In check() subcommand function:
enrichment_findings = _run_enrichment(discovered, config)
freshness_findings = _run_freshness(discovered, config, discovery_mode=discovery_mode)
coverage_findings = _run_coverage(discovered, config)
griffe_findings = _run_griffe(discovered, config, verbose=ctx.obj.get("verbose", False))
for f in enrichment_findings + freshness_findings + coverage_findings + griffe_findings:
    typer.echo(f"{f.file}:{f.line}: {f.rule} {f.message}")
```

This is temporary and will be replaced in Story 8.3.

### Test Update Strategy

Existing behavior tests that use `side_effect=_run_*` (e.g., `test_run_enrichment_when_file_has_findings_prints_formatted_output`) will continue to pass after the refactor. The `side_effect` invokes the real `_run_*` which now returns `list[Finding]` instead of printing. The bridge in the subcommand function picks up the returned list and echoes it. Test assertions on `result.output` still hold.

**Additionally**, add direct-call tests for each `_run_*` that:
- Call the function directly (not through the CLI runner)
- Assert the return type is `list[Finding]`
- Assert the list contents (finding count, field values)
- Assert return value for edge cases (syntax errors skip files, griffe skip paths return `[]`)

This two-layer approach validates both the function contract (direct-call) and the end-to-end behavior (CLI runner with bridge).

### Files Modified

| File | Change |
|------|--------|
| `src/docvet/cli.py` | Refactor 4 `_run_*` functions, update 5 subcommands |
| `src/docvet/config.py` | Add overlap warning in `load_config` |
| `tests/conftest.py` | Add `make_finding` fixture |
| `tests/unit/test_cli.py` | Update `_run_*` tests for `list[Finding]` return |
| `tests/unit/test_config.py` | Add overlap warning stderr tests |

### Quality Checklist

- [ ] AC-to-test traceability: Every AC has mapped test(s)
- [ ] Assertion strength: Verify return type, list contents, and all Finding fields
- [ ] Edge cases: Empty file lists, syntax errors, griffe not installed, all skip paths, mixed parseable/unparseable files in drift mode
- [ ] Negative assertions: No `typer.echo()` for findings, stderr messages preserved
- [ ] Reviewer independently verifies AC-to-test mapping (Epic 7 retro action item #1)

### Project Structure Notes

- No new files created in `src/` — only modifications to existing files
- `make_finding` fixture in `tests/conftest.py` establishes shared test infrastructure for Stories 8.2 and 8.3
- Import `Finding` in conftest.py: `from docvet.checks import Finding`

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md` → Reporting Module sections]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → CLI Refactor Scope table]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Decision 3: fail_on/warn_on Conflict]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Pattern 6: CLI Refactor Pattern]
- [Source: `_bmad-output/planning-artifacts/architecture.md` → Shared Test Infrastructure]
- [Source: `_bmad-output/planning-artifacts/epics.md` → Story 8.1 ACs]
- [Source: `_bmad-output/implementation-artifacts/epic-7-retro-2026-02-11.md` → Action Items]
- [Source: `src/docvet/cli.py` → Current _run_* implementations]
- [Source: `src/docvet/config.py` → load_config fail_on/warn_on handling]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
