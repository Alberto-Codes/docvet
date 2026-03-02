---
title: 'Fix nested ternary in _output_and_exit format resolution'
slug: '204-fix-nested-ternary'
created: '2026-02-28'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+', 'typer', 'ruff', 'pytest']
files_to_modify: ['src/docvet/cli.py']
code_patterns: ['flat if/elif/else for multi-branch assignment', 'numbered comment steps in _output_and_exit']
test_patterns: ['TestOutputAndExit class with _make_ctx helper and _call wrapper']
---

# Tech-Spec: Fix nested ternary in _output_and_exit format resolution

**Created:** 2026-02-28

## Overview

### Problem Statement

SonarQube flags `python:S3358` (nested conditional expression) on `src/docvet/cli.py:335-339`. The nested ternary was introduced in `40c86db` (PR #179) during a cognitive complexity refactoring. It causes the quality gate to report ERROR due to 1 new violation against a 0 threshold.

### Solution

Replace the nested ternary with a flat `if/elif/else` chain. This is behavior-preserving — three branches, three outcomes, identical logic. The flat chain actually *lowers* cognitive complexity compared to the nested ternary (no nesting penalty on `elif`), so CC improves slightly rather than regressing. The original `40c86db` commit introduced the ternary alongside an `_emit_findings` extraction as a coordinated CC reduction — reverting only the ternary half is safe because the flat chain scores lower CC, not higher.

### Scope

**In Scope:**
- Replace the nested ternary at `cli.py:334-339` with a flat `if/elif/else`

**Out of Scope:**
- No helper function extraction
- No new tests (existing tests cover all three branches)
- No other refactoring in `_output_and_exit` or elsewhere

## Context for Development

### Codebase Patterns

- `_output_and_exit` uses numbered comment steps (`# 1.` through `# 6.`) for its pipeline stages — preserve the `# 4. Resolve format` comment
- Local variable assignment pattern: `resolved_fmt = ...` in each branch, consistent with other assignments in the function
- Local variable assignment via flat `if/elif/else` is the idiomatic pattern in this codebase for multi-branch resolution

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/cli.py:334-339` | Target: nested ternary in `_output_and_exit` step 4 |
| `tests/unit/test_cli.py:1618` | `test_terminal_format_is_default_when_format_not_set` — branch 3 (`"terminal"`) |
| `tests/unit/test_cli.py:1625` | `test_format_markdown_selects_format_markdown` — branch 1 (explicit `fmt_opt`) |
| `tests/unit/test_cli.py:1642` | `test_output_without_format_defaults_to_markdown_for_file` — branch 2 (`"markdown"` fallback) |

### Technical Decisions

- **Flat `if/elif/else` over helper function**: Three branches is too trivial to extract. A helper would be over-engineering.
- **No match/case**: Overkill for a simple precedence check with `is not None` guards.
- **No new tests**: All three branches are already covered by existing `TestOutputAndExit` tests (verified in Step 2).

## Implementation Plan

### Tasks

- [x] Task 1: Replace nested ternary with flat `if/elif/else`
  - File: `src/docvet/cli.py`
  - Action: Replace lines 334-339 (the `# 4. Resolve format` block) with:
    ```python
    # 4. Resolve format
    if fmt_opt is not None:
        resolved_fmt = fmt_opt
    elif output_path is not None:
        resolved_fmt = "markdown"
    else:
        resolved_fmt = "terminal"
    ```
  - Notes: Preserves the `# 4. Resolve format` comment. No other lines in the function change.

- [x] Task 2: Run quality checks
  - Action: Verify no regressions
  - Commands:
    - `uv run ruff check src/docvet/cli.py`
    - `uv run ruff format --check src/docvet/cli.py`
    - `uv run ty check`
    - `uv run pytest tests/unit/test_cli.py -x`

- [x] Task 3: Verify S3358 resolution via SonarQube snippet analyzer
  - Action: Run `analyze_code_snippet` on the modified `cli.py` to confirm S3358 is no longer reported
  - Notes: The MCP snippet analyzer provides fast feedback. The full scanner (dashboard) is the source of truth but requires a merge-to-main scan cycle.

### Acceptance Criteria

- [ ] AC1: Given the nested ternary is replaced with flat `if/elif/else`, when `_output_and_exit` is called with `fmt_opt=None` and `output_path=None`, then format resolves to `"terminal"`.
- [ ] AC2: Given the nested ternary is replaced with flat `if/elif/else`, when `_output_and_exit` is called with `fmt_opt=None` and `output_path=Path("out.md")`, then format resolves to `"markdown"`.
- [ ] AC3: Given the nested ternary is replaced with flat `if/elif/else`, when `_output_and_exit` is called with `fmt_opt="markdown"`, then format resolves to `"markdown"` (explicit override).
- [ ] AC4: All existing tests in `tests/unit/test_cli.py` pass without modification.
- [ ] AC5: `ruff check`, `ruff format --check`, and `ty check` pass on the modified file.
- [ ] AC6: SonarQube `analyze_code_snippet` on the modified `cli.py` reports no S3358 finding.

## Additional Context

### Dependencies

None. Pure refactoring of existing code.

### Testing Strategy

Existing tests only — no new tests required. Three existing tests in `TestOutputAndExit` (lines 1618, 1625, 1642) cover all three format resolution branches. Run `uv run pytest tests/unit/test_cli.py -x` to verify.

### Notes

- Introduced by: `40c86db` (PR #179 — refactor(cli): reduce _output_and_exit cognitive complexity)
- SonarQube rule: `python:S3358` — nested conditional expression
- GitHub issue: 204
- Risk: Near zero — behavior-preserving, single-site change, full test coverage

## Review Notes

- Adversarial review completed (spec review + code review)
- Spec review findings: 12 total, 5 fixed (F1-F5), 7 noise
- Code review findings: 12 total, 0 fixed, 12 noise (confirmed by team consensus)
- Resolution approach: skip (all code findings noise — reviewer lacked SonarQube context by design)
