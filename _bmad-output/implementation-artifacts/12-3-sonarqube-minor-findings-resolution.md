# Story 12.3: SonarQube Minor Findings Resolution

Status: review
Branch: `feat/sonarqube-12-3-minor-findings`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a docvet contributor,
I want all remaining SonarQube code smell findings resolved,
so that the project achieves zero open issues on the SonarQube dashboard.

## Acceptance Criteria

1. **Given** the string `"See Also"` is used 4 times in `enrichment.py` **When** the developer extracts it into a module-level constant **Then** all 4 usages reference the constant **And** SonarQube S1192 finding for `enrichment.py` is resolved
2. **Given** the string `"[tool.docvet]"` is used 4 times in `config.py` **When** the developer extracts it into a module-level constant **Then** all 4 usages reference the constant **And** SonarQube S1192 finding for `config.py` is resolved
3. **Given** `_load_and_check_packages` in `griffe_compat.py` has CC 16 (1 above threshold) **When** the developer extracts a small helper to flatten nesting **Then** CC is at or below 15 **And** all existing griffe tests pass without modification
4. **Given** 3 S1172 findings for unused `node_index` parameters in `enrichment.py` were originally scoped **When** the developer checks the SonarQube dashboard **Then** either: (a) findings are already absent (12.1 refactoring resolved them) — document as resolved, or (b) findings still exist — mark each as "accepted" (won't-fix) with rationale: interface consistency for `_check_*` dispatch pattern
5. **Given** all findings addressed **When** `uv run pytest` is executed **Then** all tests pass with zero failures

## Tasks / Subtasks

- [x] Task 1: Extract `"See Also"` constant in `enrichment.py` (AC: 1)
  - [x] 1.1 Add module-level constant `_SEE_ALSO = "See Also"` near existing `_KNOWN_SECTIONS` (line ~28)
  - [x] 1.2 Replace `"See Also"` at line 38 (in `_KNOWN_SECTIONS` frozenset) with `_SEE_ALSO`
  - [x] 1.3 Replace `"See Also"` at line 1139 (`if "See Also" not in sections:`) with `_SEE_ALSO`
  - [x] 1.4 Replace `"See Also"` at line 1153 (`if "See Also" not in sections:`) with `_SEE_ALSO`
  - [x] 1.5 Replace `"See Also"` at line 1159 (`_extract_section_content(symbol.docstring, "See Also")`) with `_SEE_ALSO`
  - [x] 1.6 Do NOT touch line 45 (`_SECTION_PATTERN` regex) — the `"See Also"` there is inside a regex string, not a standalone literal
  - [x] 1.7 Verify with `analyze_code_snippet` — zero S1192 findings for `"See Also"`
- [x] Task 2: Extract `"[tool.docvet]"` constant in `config.py` (AC: 2)
  - [x] 2.1 Add module-level constant `_TOOL_SECTION = "[tool.docvet]"` in the constants area of `config.py`
  - [x] 2.2 Replace `"[tool.docvet]"` at line 383 (`_validate_keys(data, _VALID_TOP_KEYS, "[tool.docvet]")`) with `_TOOL_SECTION`
  - [x] 2.3 Replace `"[tool.docvet]"` at line 391 (`_validate_type(freshness_data, dict, "freshness", "[tool.docvet]")`) with `_TOOL_SECTION`
  - [x] 2.4 Replace `"[tool.docvet]"` at line 395 (`_validate_type(enrichment_data, dict, "enrichment", "[tool.docvet]")`) with `_TOOL_SECTION`
  - [x] 2.5 Replace `"[tool.docvet]"` at line 398 (`section = "[tool.docvet]"`) — replaced RHS with `_TOOL_SECTION`
  - [x] 2.6 Do NOT touch line 452 — that is a full error message string containing `[tool.docvet]` as part of a longer sentence, not a standalone literal
  - [x] 2.7 Do NOT touch docstrings (lines 1, 375, 378, 427, 433) — those are documentation, not code literals
  - [x] 2.8 Verify with `analyze_code_snippet` — zero S1192 findings for `"[tool.docvet]"`
- [x] Task 3: Fix `_load_and_check_packages` CC 16 in `griffe_compat.py` (AC: 3)
  - [x] 3.1 Extract `_collect_object_findings(obj: griffe.Object, handler: _WarningCollector) -> list[Finding]` — move the inner `for record in handler.records[before:after]` loop out of the nested `for obj` loop
  - [x] 3.2 Update `_load_and_check_packages` to call the new helper, flattening the triple-nested loop structure
  - [x] 3.3 Verify CC ≤ 15 via `analyze_code_snippet` — zero S3776 findings
  - [x] 3.4 Run `uv run pytest tests/unit/checks/test_griffe_compat.py` — all griffe tests pass
- [x] Task 4: Verify S1172 node_index findings status (AC: 4)
  - [x] 4.1 Check SonarQube dashboard for S1172 findings on `enrichment.py`
  - [x] 4.2 If findings exist: accept each as won't-fix with rationale "Interface consistency for `_check_*` dispatch pattern — all check functions share the same `(symbol, sections, node_index, config, file_path)` signature for table-driven dispatch in `check_enrichment`"
  - [x] 4.3 If findings are absent: document as already resolved by 12.1 refactoring
- [x] Task 5: Full regression suite (AC: 5)
  - [x] 5.1 Run `uv run pytest` — all tests pass (731 passed, 1 skipped)
  - [x] 5.2 Run `uv run ruff check .` — zero violations
  - [x] 5.3 Run `uv run ruff format --check .` — zero format issues
  - [x] 5.4 Run `uv run ty check` — zero type errors

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `tests/unit/checks/test_enrichment.py` (210 tests) — existing tests cover all `"See Also"` logic paths including `_check_missing_cross_references` branches A and B | PASS |
| 2 | `tests/unit/test_config.py` (64 tests) — existing tests cover `_parse_docvet_section` validation paths using `"[tool.docvet]"` | PASS |
| 3 | `tests/unit/checks/test_griffe_compat.py` (40 tests) — existing tests cover `_load_and_check_packages` finding collection, verified post-refactor | PASS |
| 4 | SonarQube dashboard query (`search_sonar_issues_in_projects`) — zero S1172 findings, confirmed absent (resolved by 12.1) | PASS |
| 5 | Full suite: 731 passed, 1 skipped; ruff check: all passed; ruff format: all formatted; ty check: all passed | PASS |

## Dev Notes

### Refactoring Strategy — Carry-Forward from 12.1/12.2

Stories 12.1 and 12.2 established the proven playbook:
- **Verify with SonarQube** — use `mcp__sonarqube__analyze_code_snippet` with `projectKey: "docvet"` after each change
- **Zero test modifications** — if a test fails, the change is wrong
- **Helpers stay private** — `_leading_underscore` prefix, no additions to `__all__`
- **All helpers need Google-style docstrings** — match existing patterns per module
- **`analyze_code_snippet` vs full scanner** — they can differ slightly on CC (12.2 review confirmed this). Use snippet analysis for fast feedback but note that the dashboard scan is the source of truth

### Per-Finding Detail

**S1192 — `"See Also"` in `enrichment.py`:**

The literal `"See Also"` appears in 4 code locations:
- Line 38: In `_KNOWN_SECTIONS` frozenset definition
- Line 1139: Conditional check in `_check_missing_cross_references` (Branch A)
- Line 1153: Conditional check in `_check_missing_cross_references` (Branch B)
- Line 1159: Argument to `_extract_section_content`

Line 45 (`_SECTION_PATTERN` regex) contains `See Also` inside a regex alternation string — this is NOT a standalone string literal and must NOT be changed. The regex must keep the raw text for pattern matching.

**Constant name:** `_SEE_ALSO = "See Also"` — place near `_KNOWN_SECTIONS` (line ~28 area) since they are semantically related.

**S1192 — `"[tool.docvet]"` in `config.py`:**

The literal `"[tool.docvet]"` appears in 4 code locations (all within `_parse_docvet_config`):
- Line 383: `_validate_keys(data, _VALID_TOP_KEYS, "[tool.docvet]")`
- Line 391: `_validate_type(freshness_data, dict, "freshness", "[tool.docvet]")`
- Line 395: `_validate_type(enrichment_data, dict, "enrichment", "[tool.docvet]")`
- Line 398: `section = "[tool.docvet]"` (local variable already partially consolidating)

Line 452 has `"docvet: [tool.docvet] in pyproject.toml must be a table"` — a full error message, NOT a standalone `"[tool.docvet]"` literal. Do not touch it.

Docstring references (lines 1, 375, 378, 427, 433) are documentation, not code.

**Constant name:** `_TOOL_SECTION = "[tool.docvet]"` — place in the module constants area near other `_VALID_*` constants. The local variable `section` at line 398 can be replaced with `_TOOL_SECTION` or removed entirely.

**S3776 — `_load_and_check_packages` CC 16 in `griffe_compat.py`:**

This function was extracted in Story 12.2 from `check_griffe_compat`. The full scanner reports CC 16 (1 over threshold). The CC driver is triple-nested loops:

```
for child in sorted(src_root.iterdir()):     # nesting 0
    ...
    for obj in _walk_objects(package, file_set):  # nesting 1
        ...
        for record in handler.records[before:after]:  # nesting 2
            if finding is not None:                    # nesting 3
```

**Strategy:** Extract the inner object-processing logic into a helper:
```python
def _collect_object_findings(
    obj: griffe.Object,
    handler: _WarningCollector,
) -> list[Finding]:
```
This helper triggers `obj.docstring.parsed`, captures new records, and converts to findings. This flattens the nesting depth by 1 level, bringing CC below 15.

Place the new helper immediately above `_load_and_check_packages` (line ~152 area).

### S1172 — `node_index` Unused Parameter (Verification Only)

The original epic scoped 3 S1172 findings for unused `node_index` parameters at:
- `_check_missing_attributes` (line 817) — actually USES `node_index.get(symbol.line)` at line 852
- `_check_missing_typed_attributes` (line 927) — parameter present for dispatch interface consistency
- `_check_missing_cross_references` (line 1109) — parameter present for dispatch interface consistency

The post-12.2 SonarQube scan found ZERO S1172 issues. Verify during implementation:
- If absent: document as already resolved
- If present: accept as won't-fix with rationale: "All `_check_*` functions share the same `(symbol, sections, node_index, config, file_path)` signature for table-driven dispatch via `_RULE_DISPATCH` in `check_enrichment`"

### S3626 — Redundant `continue` (Already Resolved)

The original epic flagged a redundant `continue` at `freshness.py` line 261. Story 12.2's refactoring of `_parse_blame_timestamps` (extracted `_classify_blame_line` helper) eliminated this. The post-12.2 SonarQube scan confirmed no S3626 findings. No action needed.

### Critical Constraints

- **Pure refactoring + constant extraction** — zero behavioral changes
- **No existing test modifications** — all tests must pass as-is
- **No new tests required** — these are mechanical fixes, not new logic
- **Constants are private** — `_CAPS_WITH_UNDER` naming per Python style
- **`from __future__ import annotations`** — already present in all files
- **Verify CC with SonarQube** — use `analyze_code_snippet` with `projectKey: "docvet"` after each change

### File Scope

| File | Action |
|------|--------|
| `src/docvet/checks/enrichment.py` | Add `_SEE_ALSO` constant, replace 4 usages |
| `src/docvet/config.py` | Add `_TOOL_SECTION` constant, replace 4 usages |
| `src/docvet/checks/griffe_compat.py` | Add `_collect_object_findings` helper, simplify `_load_and_check_packages` |

**No other files should be modified.** Tests, CLI, other checks — all untouched.

### Test Suite Context

| Test File | Test Count | Module Coverage |
|-----------|------------|-----------------|
| `tests/unit/checks/test_enrichment.py` | ~415 | `enrichment.py` — section detection, finding production |
| `tests/unit/test_config.py` | 64 | `config.py` — defaults, TOML parsing, validation |
| `tests/unit/checks/test_griffe_compat.py` | 40 | `griffe_compat.py` — warnings, traversal, package loading |
| **Total relevant** | **~519** | Safety net for all 3 files |

### Previous Story Intelligence (12.2)

**What worked:**
- Same pattern as 12.1: extract helpers, verify CC, run tests — zero-debug implementation
- Module-specific tests after each change, full suite only at end
- `analyze_code_snippet` for fast CC feedback, dashboard scan as final gate
- Code review caught: `sonar-project.properties` not in File List, Change Log had placeholders

**Key lesson for 12.3:**
- `analyze_code_snippet` and full scanner CAN differ on CC — the `_load_and_check_packages` CC 16 finding proves this. Always aim for CC well below 15 (target ≤ 12) to account for scanner variance

### Git Intelligence

Latest commits on develop:
- `3bccab1` chore: replace hardcoded LAN IP with env vars in sonarqube rule
- `45daeee` chore: update sonarqube rule with scanning workflow and LAN setup details
- `50aaf65` fix: remove sonar.branch.name property incompatible with Community Edition
- `2a191d3` refactor: reduce cognitive complexity of 7 functions across 5 non-enrichment modules (#74) — Story 12.2
- `64f0945` refactor(enrichment): reduce cognitive complexity of 5 functions below SonarQube threshold (#73) — Story 12.1

Codebase is clean. No pending changes.

### Project Structure Notes

- All 3 target files follow: module docstring → imports → constants → private helpers → public API
- New constants go in the constants area (after imports, before helpers)
- New helpers placed immediately above the function they serve
- `from __future__ import annotations` present in all files

### References

- [Source: _bmad-output/planning-artifacts/epics-housekeeping.md#Story 12.3]
- [Source: src/docvet/checks/enrichment.py — `_SEE_ALSO` target lines 38, 1139, 1153, 1159]
- [Source: src/docvet/config.py — `_TOOL_SECTION` target lines 383, 391, 395, 398]
- [Source: src/docvet/checks/griffe_compat.py — `_load_and_check_packages` line 152, CC 16]
- [Source: .claude/rules/sonarqube.md — CC threshold 15, S3776 dominant finding, scanner variance note]
- [Source: _bmad-output/implementation-artifacts/12-2-non-enrichment-module-cognitive-complexity-refactoring.md — previous story patterns and review findings]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Zero-debug implementation following 12.1/12.2 playbook.

### Completion Notes List

- Task 1: Extracted `_SEE_ALSO = "See Also"` constant in `enrichment.py`. Replaced 4 standalone string literal usages (lines 38, 1139, 1153, 1159). Left regex pattern on line 45 untouched. Grep confirms only the constant definition contains the literal. All 210 enrichment tests pass.
- Task 2: Extracted `_TOOL_SECTION = "[tool.docvet]"` constant in `config.py`. Replaced 4 standalone usages (lines 383, 391, 395, 398). Left error message on line 452 and all docstrings untouched. All 64 config tests pass.
- Task 3: Extracted `_collect_object_findings()` helper in `griffe_compat.py`. Moved inner record-processing loop out of `_load_and_check_packages`, flattening triple-nested structure. SonarQube `analyze_code_snippet` reports zero S3776 findings. All 40 griffe tests pass.
- Task 4: SonarQube dashboard query confirmed zero S1172 findings — already resolved by 12.1 refactoring. No action needed.
- Task 5: Full regression suite green — 731 passed, 1 skipped; ruff check clean; ruff format clean; ty check clean.
- SonarQube dashboard shows exactly 3 open issues (S1192 x2, S3776 x1) — all addressed by this story, will clear on next post-merge scan.

### Change Log

- 2026-02-22: Resolved 3 SonarQube code smell findings (S1192 x2 constant extraction, S3776 x1 CC reduction). Verified S1172 findings already absent. Full regression suite green.

### File List

| File | Action |
|------|--------|
| `src/docvet/checks/enrichment.py` | Modified — added `_SEE_ALSO` constant, replaced 4 string literal usages |
| `src/docvet/config.py` | Modified — added `_TOOL_SECTION` constant, replaced 4 string literal usages |
| `src/docvet/checks/griffe_compat.py` | Modified — added `_collect_object_findings()` helper, simplified `_load_and_check_packages` |
