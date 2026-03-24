# Story 32.1: Fix Feasibility Spike

Status: review
Branch: `feat/fix-32-1-feasibility-spike`

## Story

As a **project maintainer**,
I want confidence that AST-based docstring insertion works reliably and that the scaffold finding category is well-designed,
so that the fix command can be built on a validated foundation with proper lifecycle enforcement.

## Acceptance Criteria

1. **Given** a Python function with a one-line docstring and missing Raises/Args sections, **when** the spike's proof-of-concept inserts scaffolded sections using AST line numbers, **then** the modified file is valid Python and `docvet check` produces zero findings for the scaffolded sections.

2. **Given** a function with an existing multi-section docstring (Args exists, Raises missing), **when** the spike inserts the missing Raises section, **then** existing Args content is preserved byte-for-byte and Raises is inserted after the last existing section.

3. **Given** the spike runs insertion twice on the same file, **when** the second run executes, **then** no changes are made (idempotency validated).

4. **Given** the spike results, **when** reviewed, **then** a decision document records: chosen insertion strategy (string ops + AST line numbers vs libcst), edge cases identified, and go/no-go recommendation.

5. **Given** the spike evaluates the fix lifecycle, **when** the scaffold category design is reviewed, **then** the decision document also records: the `scaffold` finding category design (required severity, actionable message format "fill in [Section] — describe [items]"), the placeholder marker specification (e.g. `[TODO: describe]`), and how scaffold findings integrate with reporting, exit codes, and JSON output.

## Tasks / Subtasks

- [x] Task 1: Research insertion strategies (AC: 4)
  - [x] 1.1 Evaluate string ops + AST `lineno` approach — can we reliably find insertion points within docstrings using `ast.get_docstring_range()` (3.14+) or manual line counting?
  - [x] 1.2 Evaluate `textwrap`/`inspect` for indentation detection from surrounding code
  - [x] 1.3 Evaluate libcst as alternative — document trade-offs, note NFR4 (zero runtime deps) conflict
  - [x] 1.4 Document decision: chosen approach with rationale

- [x] Task 2: Build proof-of-concept insertion (AC: 1, 2, 3)
  - [x] 2.1 Implement POC function: `scaffold_missing_sections(source: str, tree: ast.Module, findings: list[Finding]) -> str`
  - [x] 2.2 Handle one-line docstring expansion (AC 1)
  - [x] 2.3 Handle multi-section docstring insertion after last existing section (AC 2)
  - [x] 2.4 Handle indentation detection and preservation
  - [x] 2.5 Verify idempotency — second run produces no changes (AC 3)

- [x] Task 3: Identify edge cases (AC: 4)
  - [x] 3.1 Test with: decorators, nested classes, `@property`, classmethods, staticmethods
  - [x] 3.2 Test with: empty docstrings (`""" """`), single-line docstrings, raw docstrings
  - [x] 3.3 Test with: tabs vs spaces, mixed indentation
  - [x] 3.4 Test with: class Attributes section, module-level docstrings
  - [x] 3.5 Document all edge cases and how the chosen strategy handles them

- [x] Task 4: Design scaffold finding category (AC: 5)
  - [x] 4.1 Design `scaffold` category on Finding dataclass (required severity)
  - [x] 4.2 Define placeholder marker format: `[TODO: describe]` vs alternatives
  - [x] 4.3 Define actionable message format: "fill in [Section] — describe [items]"
  - [x] 4.4 Define exit code behavior: scaffold = non-zero (same as required)
  - [x] 4.5 Define reporting integration: terminal, markdown, JSON output handling
  - [x] 4.6 Document all decisions in spike output

- [x] Task 5: Write decision document (AC: 4, 5)
  - [x] 5.1 Create `_bmad-output/implementation-artifacts/32-1-spike-decision.md`
  - [x] 5.2 Include: insertion strategy choice + rationale
  - [x] 5.3 Include: scaffold category design spec
  - [x] 5.4 Include: edge case catalog
  - [x] 5.5 Include: go/no-go recommendation for Story 32.2

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | POC test_ac1_oneliner: one-line → valid Python, `docvet enrichment` zero findings | PASS |
| 2 | POC test_ac2_multisection: Args preserved byte-for-byte, Raises after Returns | PASS |
| 3 | POC test_ac3_idempotency: `first_pass == second_pass` | PASS |
| 4 | Decision document `32-1-spike-decision.md` — sections 1-3, 5-6 | PASS |
| 5 | Decision document section 4 — scaffold category design spec | PASS |

## Dev Notes

- **This is a research spike, not a production implementation.** The POC code lives in the decision document or a scratch file — it does NOT ship as production code. Story 32.2 builds the real engine.
- **Interaction Risk:** None — new capability, no existing rules affected by the spike itself. The scaffold category design will affect Story 32.2's implementation of Finding.

### Architecture Constraints

- **No libcst dependency (NFR4):** "Fix insertion uses AST line numbers for positioning — no libcst dependency." The spike evaluates libcst as an alternative but the architecture explicitly rejects it. If string ops + AST proves infeasible, this is a go/no-go blocker.
- **Zero runtime dependencies (NFR3):** Fix command uses stdlib only (ast, textwrap, etc.)
- **Byte-for-byte preservation:** Existing docstring content must not change when inserting new sections.
- **Deterministic + idempotent:** Same input → same output, always. Second run → no changes.

### Current Finding Dataclass

```python
# src/docvet/checks/_finding.py
@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    symbol: str
    rule: str
    message: str
    category: Literal["required", "recommended"]
```

The spike designs (but does NOT implement) the addition of `"scaffold"` as a third category value. Implementation happens in Story 32.2.

### Key Technical Approaches to Evaluate

1. **String ops + AST line numbers:** Use `ast.parse()` to get docstring line ranges, then use string slicing to insert new sections. Indentation detected from the existing docstring's first line.
2. **libcst (CST preservation):** Full concrete syntax tree that preserves whitespace and comments. Adds a runtime dependency (rejected by NFR4) but is the most robust approach.
3. **Hybrid:** Use AST for analysis, string ops for insertion, with heuristic indentation detection.

### Project Structure Notes

- POC code: `_bmad-output/implementation-artifacts/32-1-spike-decision.md` (not in src/)
- Decision document: same file
- No production code ships from this story

### References

- [Source: _bmad-output/planning-artifacts/epics-quick-wins-lifecycle-visibility.md#Epic 32]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-03-23.md]
- [Source: src/docvet/checks/_finding.py] — Current Finding dataclass
- [Source: src/docvet/checks/enrichment/__init__.py] — Enrichment orchestrator (where scaffold findings would be generated)
- [Source: .claude/rules/python.md#Module Size Gate] — Module size gate rule

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A (research spike produces a decision document, not shipped code)

### Test Maturity Piggyback

No test-review.md found — run `/bmad-tea-testarch-test-review` to establish baseline.

## Quality Gates

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1660 passed, zero regressions
- [x] `uv run docvet check --all` — no findings, 100% coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- POC run at `/tmp/poc_scaffold.py` — 14/14 tests pass
- AC1 docvet verification: `docvet enrichment --files /tmp/ac1_full.py` → "no findings"

### Completion Notes List

- Task 1: Evaluated 3 insertion strategies. String ops + AST line numbers chosen (zero deps, leverages existing `Symbol.docstring_range`). textwrap/inspect rejected (removes indent, doesn't detect it). libcst rejected (NFR4 violation).
- Task 2: Built ~120-line POC function `scaffold_missing_sections()`. Key insights: closing `"""` line indentation reliably indicates section header indent; reverse-order processing preserves line numbers; existing section detection via regex enables idempotency.
- Task 3: Tested 14 scenarios — all pass. Edge cases handled: nested methods, multiple sections, decorators, dataclasses, async, raw/single-quote docstrings, tabs, module-level. Documented 7 unhandled edge cases (rare, for Story 32.2).
- Task 4: Designed `scaffold` category — required severity, `[TODO: describe]` placeholder, `scaffold-incomplete` rule, non-zero exit code, reporting integration for terminal/JSON/markdown.
- Task 5: Decision document written with all 6 sections. GO recommendation for Story 32.2.

### Change Log

- 2026-03-23: Created decision document `32-1-spike-decision.md` with insertion strategy evaluation, POC results, edge case catalog, scaffold category design, and go/no-go recommendation.

### File List

- `_bmad-output/implementation-artifacts/32-1-spike-decision.md` (new) — Decision document with POC code and design specs
- `_bmad-output/implementation-artifacts/32-1-fix-feasibility-spike.md` (modified) — Story file with task completion, AC mapping, dev record
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Status: ready-for-dev → in-progress

## Code Review

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
