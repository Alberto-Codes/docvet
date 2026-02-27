---
title: 'Reduce _output_and_exit cognitive complexity'
slug: 'reduce-output-and-exit-cc'
created: '2026-02-27'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python 3.12+', 'typer', 'enum.StrEnum']
files_to_modify: ['src/docvet/cli.py']
code_patterns: ['private _ helper extraction', 'ternary format resolution', 'ctx.obj option passing', 'StrEnum for CLI choices']
test_patterns: ['mock-based TestOutputAndExit (19 tests)', 'transitive coverage of private helpers']
---

# Tech-Spec: Reduce _output_and_exit cognitive complexity

**Created:** 2026-02-27

## Overview

### Problem Statement

SonarQube scan on `main` (`da8e51d`) flags `_output_and_exit()` at `src/docvet/cli.py:248` with cognitive complexity 17 (threshold 15, target ≤12). The JSON format branch added in #177 pushed it over.

### Solution

Two changes, no behavior change: (1) Collapse 3-branch format resolution to a single ternary expression (~2 CC reduction). (2) Extract `_emit_findings()` helper for the format dispatch block (~4-5 CC reduction).

### Scope

**In Scope:**
- Refactor `_output_and_exit()` in `src/docvet/cli.py`
- Collapse format resolution if/elif/else to ternary
- Extract `_emit_findings()` private helper
- Docstrings for `_emit_findings` (new) and `_output_and_exit` (update)

**Out of Scope:**
- New tests or test modifications
- New features or behavior changes
- Changes to other functions
- Changes to `reporting.py` or other modules

## Context for Development

### Codebase Patterns

- Private helpers in `cli.py` are prefixed with `_` (e.g., `_get_git_diff`, `_output_and_exit`)
- Format resolution currently uses 3-branch if/elif/else at lines 295-300
- Format dispatch block at lines 302-315 handles JSON, markdown, and terminal output paths
- `--format` is typed as `OutputFormat | None` (`StrEnum` at line 70) with default `None`
- At line 611: `ctx.obj["format"] = fmt.value if fmt is not None else None` — so `fmt_opt` is always `None` or one of `"terminal"`, `"markdown"`, `"json"` (never empty string)
- `format_json(all_findings, file_count)` requires `file_count` — the helper needs 5 params

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/cli.py:248-318` | Target function `_output_and_exit()` |
| `src/docvet/cli.py:70-94` | `OutputFormat` StrEnum — confirms `fmt_opt` is `None` or valid string |
| `src/docvet/cli.py:611` | Format option stored in `ctx.obj` — confirms no empty string possible |
| `tests/unit/test_cli.py:1574-1825` | `TestOutputAndExit` — 19 tests, must pass unchanged |
| `src/docvet/reporting.py` | `format_json`, `format_markdown`, `format_terminal`, `write_report` — called by emission block |

### Technical Decisions

1. **Keep format resolution and emission separate** — resolution is policy (CLI flags/defaults), emission is I/O. Clean boundary prevents parameter overloading.
2. **Name the helper `_emit_findings`** — verb "emit" signals I/O side effects; more accurate than "write" since not all paths write to a file.
3. **Zero test additions** — `_emit_findings` is a private helper tested transitively through existing `TestOutputAndExit` suite. Direct tests would couple to implementation details.
4. **Ternary is safe** — `fmt_opt` is always `None` or a truthy string (verified via `OutputFormat` StrEnum + line 611). `fmt_opt or (...)` is equivalent to the if/elif/else.
5. **`_emit_findings` signature** — `(resolved_fmt, all_findings, output_path, no_color, file_count) -> None`. Five params, pure side effects, no return value.
6. **Placement** — `_emit_findings` goes immediately before `_output_and_exit` (follows `cli.py` convention: helpers before callers, top-down reading order).
7. **Docstring for `_emit_findings`** — new symbol needs Google-style docstring per project convention ("every symbol deserves its natural language representation").
8. **Update `_output_and_exit` docstring** — reflect delegation to `_emit_findings` to avoid self-inflicted freshness finding from `docvet` dogfooding.

## Implementation Plan

### Tasks

- [x] Task 1: Extract `_emit_findings` helper
  - File: `src/docvet/cli.py`
  - Action: Create `_emit_findings(resolved_fmt, all_findings, output_path, no_color, file_count) -> None` immediately before `_output_and_exit`. Move lines 302-315 (the format dispatch block) into this new function. Add a Google-style docstring covering Args and the three output paths (JSON always emits, file write, stdout).
  - Notes: Pure extraction — the body of the helper is a verbatim move of the existing block. No logic changes.

- [x] Task 2: Collapse format resolution to ternary
  - File: `src/docvet/cli.py`
  - Action: Replace the 3-branch if/elif/else at lines 295-300 with: `resolved_fmt = fmt_opt or ("markdown" if output_path else "terminal")`
  - Notes: Equivalence verified — `fmt_opt` is always `None` (falsy) or a valid format string (truthy). The ternary produces identical results for all input combinations.

- [x] Task 3: Wire `_output_and_exit` to call `_emit_findings`
  - File: `src/docvet/cli.py`
  - Action: Replace the removed dispatch block (old lines 302-315) with a single call: `_emit_findings(resolved_fmt, all_findings, output_path, no_color, file_count)`
  - Notes: This is the other half of Task 1 — Task 1 creates the target, Task 3 wires the call site.

- [x] Task 4: Update `_output_and_exit` docstring
  - File: `src/docvet/cli.py`
  - Action: Update the docstring to reflect that the function now resolves format via ternary and delegates emission to `_emit_findings` rather than handling output inline. Keep the existing Args/Raises sections accurate.
  - Notes: Prevents `docvet freshness` from flagging this as a stale docstring after the code change.

- [x] Task 5: Validate
  - Action: Run `uv run pytest tests/unit/test_cli.py::TestOutputAndExit -v` to confirm all existing tests pass unchanged. Run `uv run ruff check src/docvet/cli.py` and `uv run ruff format --check src/docvet/cli.py` for lint/format compliance. Use SonarQube `analyze_code_snippet` on the refactored `_output_and_exit` to verify CC ≤ 12.
  - Notes: No new tests. Existing tests are the acceptance gate.

### Acceptance Criteria

- [x] AC 1: Given both `_emit_findings` and `_output_and_exit`, when analyzed with SonarQube `analyze_code_snippet`, then zero issues are reported (covers CC ≤ 12 and all other rules).
- [x] AC 2: Given the refactored code, when `uv run pytest tests/unit/test_cli.py::TestOutputAndExit -v` is run, then all existing tests pass with zero modifications to test code.
- [x] AC 3: Given `_emit_findings` is a new symbol, when inspected, then it has a Google-style docstring with Args section documenting all five parameters.
- [x] AC 4: Given `_output_and_exit` was refactored, when its docstring is inspected, then it accurately describes the current implementation (ternary resolution + delegation to `_emit_findings`).
- [x] AC 5: Given the refactored code, when `uv run ruff check src/docvet/cli.py` and `uv run ruff format --check src/docvet/cli.py` are run, then both pass with zero violations.
- [x] AC 6: Given the refactored code, when `docvet check src/docvet/cli.py` is run, then zero new findings are introduced (no self-inflicted freshness or enrichment violations).

## Additional Context

### Dependencies

None — pure refactor of existing code.

### Testing Strategy

Run existing `TestOutputAndExit` suite unchanged. Verify all 19 tests pass. Validate CC ≤ 12 via SonarQube `analyze_code_snippet`. Run ruff check + format. Run `docvet check` on the modified file to verify zero self-inflicted findings.

### Notes

- Issue: #178
- Party mode consensus: all three design questions resolved unanimously (session 1), three additional items surfaced in session 2 (placement, docstrings, dogfooding)
- Risk: Minimal — single file, pure refactor, comprehensive existing test coverage
- Tasks 1-3 are logically one atomic change but broken out for clarity; they should be implemented together in a single commit

## Review Notes

- Adversarial review completed: 10 findings total
- Fixed: 2 (F1 — identity check preserved, F3 — docstring clarification)
- Skipped: 8 (F2 out-of-scope per spec, F4-F5 behavior changes, F6-F10 noise/pre-existing)
- Resolution approach: party mode consensus (walk-through + selective fix)
