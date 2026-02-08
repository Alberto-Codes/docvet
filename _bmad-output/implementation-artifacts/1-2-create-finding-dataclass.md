# Story 1.2: Create Finding Dataclass

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a shared, immutable `Finding` dataclass in `checks/__init__.py`,
so that all check modules produce findings with a consistent, stable structure.

## Acceptance Criteria

1. **Given** the `checks/__init__.py` module, **when** imported, **then** it exports `Finding` as the only public name (AC: #1)

2. **Given** a `Finding` instance, **when** constructed with `file`, `line`, `symbol`, `rule`, `message`, `category`, **then** all 6 fields are accessible and the instance is frozen (immutable) (AC: #2)

3. **Given** a `Finding` instance, **when** any field assignment is attempted (e.g., `finding.rule = "new"`), **then** a `FrozenInstanceError` is raised (AC: #3)

4. **Given** the `category` field, **when** a `Finding` is constructed, **then** it accepts `"required"` or `"recommended"` as valid values (AC: #4)

5. **Given** the `rule` field, **when** a `Finding` is constructed, **then** it accepts any string (kebab-case rule identifiers like `"missing-raises"`) (AC: #5)

## Tasks / Subtasks

- [x] Task 1: Create `src/docvet/checks/__init__.py` with Finding dataclass (AC: #1, #2, #3, #4, #5)
  - [x] 1.1: Add module docstring explaining checks package purpose
  - [x] 1.2: Import required stdlib dependencies (`dataclasses`, `typing.Literal`)
  - [x] 1.3: Define Finding frozen dataclass with 6 fields (file, line, symbol, rule, message, category)
  - [x] 1.4: Add comprehensive docstring to Finding with field descriptions
  - [x] 1.5: Add `__all__ = ["Finding"]` export
- [x] Task 2: Write unit tests for Finding dataclass (AC: #1, #2, #3, #4, #5)
  - [x] 2.1: Create `tests/unit/checks/test_finding.py` test file
  - [x] 2.2: `test_finding_can_be_constructed_with_all_fields` — verify all fields accessible
  - [x] 2.3: `test_finding_is_frozen_raises_on_mutation` — verify frozen behavior
  - [x] 2.4: `test_finding_is_hashable` — verify can be added to sets/dicts
  - [x] 2.5: `test_finding_equality_works_correctly` — verify instances are comparable
  - [x] 2.6: `test_finding_exports_only_finding_class` — verify `__all__` export
- [x] Task 3: Run quality gates and verify all pass
  - [x] 3.1: `uv run ruff check .`
  - [x] 3.2: `uv run ruff format --check .`
  - [x] 3.3: `uv run ty check`
  - [x] 3.4: `uv run pytest tests/unit/checks/test_finding.py -v`

## Dev Notes

### Scope

This is **Prerequisite PR 2** of the enrichment module. It creates the shared `Finding` dataclass that all check modules (enrichment, freshness, griffe, coverage) will import and use. This is the foundational API contract between check modules and the CLI layer.

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/docvet/checks/__init__.py` | NEW — Create Finding frozen dataclass with 6 fields |
| `tests/unit/checks/__init__.py` | NEW — Empty file to make tests/unit/checks a package |
| `tests/unit/checks/test_finding.py` | NEW — Unit tests for Finding dataclass |

### Architecture Constraints

- **Finding is frozen** (`@dataclass(frozen=True)`) — immutability is a v1 API contract (NFR17)
- **6-field shape is stable** — no fields added, removed, or renamed within v1 lifecycle
- **Category is literal type** — `Literal["required", "recommended"]` enforced at type-check time
- **No default values** — all 6 fields are required; no ambiguity about what a Finding represents
- **No cross-check dependencies** — Finding is the ONLY type shared between check modules
- **Exported as sole public API** — `__all__ = ["Finding"]` makes the export explicit

### The 6 Fields Explained

| Field | Type | Purpose | Source |
|-------|------|---------|--------|
| `file` | `str` | Source file path | Always `file_path` parameter passed to check functions |
| `line` | `int` | Line number where symbol is defined | Always `symbol.line` from Symbol object (the `def`/`class` keyword line) |
| `symbol` | `str` | Name of the symbol with the issue | Always `symbol.name` from Symbol object (e.g., `"validate_input"`, `"ValidationResult"`, `"<module>"`) |
| `rule` | `str` | Kebab-case stable rule identifier | Literal string from rule taxonomy (one of 10 values: `"missing-raises"`, `"missing-yields"`, etc.) |
| `message` | `str` | Human-readable finding description | f-string composed by each `_check_*` function explaining what's missing |
| `category` | `Literal["required", "recommended"]` | Severity classification | `"required"` = misleading omission, `"recommended"` = improvement opportunity |

### Category Values & Semantic Meaning

**`"required"` (6 rules):**
- Semantics: Missing this section actively misleads developers
- Examples: `missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-attributes`
- CI usage: Often mapped to `fail-on` — teams enforce these in CI pipelines
- Triage: High priority — fix these first

**`"recommended"` (4 rules):**
- Semantics: Missing this section is a nice-to-have improvement
- Examples: `missing-examples`, `missing-other-parameters`, `missing-typed-attributes`, `prefer-fenced-code-blocks`
- CI usage: Often mapped to `warn-on` — informational but don't fail builds
- Triage: Lower priority — address gradually

### Rule Identifiers (All 10)

From the rule taxonomy table in architecture.md:

1. `missing-raises` (required)
2. `missing-yields` (required)
3. `missing-receives` (required)
4. `missing-warns` (required)
5. `missing-other-parameters` (recommended)
6. `missing-attributes` (required)
7. `missing-typed-attributes` (recommended)
8. `missing-examples` (recommended)
9. `missing-cross-references` (recommended)
10. `prefer-fenced-code-blocks` (recommended)

All kebab-case, stable across tool lifetime, used in config/CLI output/issue tracking.

### Implementation Pattern

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Finding:
    """A docstring quality finding.

    Findings are immutable records produced by check modules to report
    missing or incomplete docstring sections. All check modules (enrichment,
    freshness, griffe, coverage) return list[Finding] to the CLI layer.

    Attributes:
        file: Source file path where the finding was detected.
        line: Line number of the symbol definition (def/class keyword line).
        symbol: Name of the symbol with the issue (function/class/module name).
        rule: Kebab-case rule identifier (e.g., "missing-raises").
        message: Human-readable description of the issue.
        category: Severity classification ("required" or "recommended").
    """

    file: str
    line: int
    symbol: str
    rule: str
    message: str
    category: Literal["required", "recommended"]

__all__ = ["Finding"]
```

### Why Frozen/Immutable

From architecture.md NFR17 and design rationale:

1. **API stability** — NFR17: "Finding's 6-field shape is stable for v1 — no fields added, removed, or renamed"
2. **Cross-check consistency** — All future check modules import and return Finding; freezing prevents accidental mutation
3. **Thread-safety ready** — Frozen dataclasses are naturally hashable and safe for concurrent access
4. **Defensive design** — Aligns with NFR8: "The enrichment check never modifies input data" — output is equally immutable
5. **Hashability** — Frozen dataclasses can be added to sets/dicts for deduplication and grouping

### Integration with Check Modules

**Data flow pattern:**
```
CLI (_run_enrichment)
  │
  ├─ reads file → source: str
  ├─ ast.parse(source) → tree: ast.Module
  ├─ loads config → config.enrichment: EnrichmentConfig
  │
  ▼
check_enrichment(source, tree, config, file_path) → list[Finding]
  │
  ├─ for each symbol:
  │    _check_*(symbol, sections, node_index, config, file_path)
  │      → Finding | None
  │
  ▼
list[Finding] returned to CLI → formatted for output
```

**Import paths:**
```python
# In cli.py
from docvet.checks import Finding
from docvet.checks.enrichment import check_enrichment

# In checks/enrichment.py
from docvet.checks import Finding
from docvet.ast_utils import Symbol

# In tests
from docvet.checks import Finding
```

### What NOT to Do

- Do NOT add methods to Finding — it's a pure data container
- Do NOT make Finding mutable — frozen=True is required
- Do NOT add default values to fields — all 6 are required
- Do NOT use dynamic category values — only `"required"` or `"recommended"` literals
- Do NOT add additional fields in this story — 6 fields only per v1 API contract
- Do NOT create Finding instances in tests yet — this story only defines the dataclass

### Testing Strategy

**Unit tests only** — no integration tests needed for a dataclass definition

Test coverage requirements:
1. Construction with all 6 fields works
2. Frozen behavior prevents mutation
3. Instances are hashable (can be in sets/dicts)
4. Equality comparison works correctly
5. `__all__` export is correct

**No need to test:**
- Type checking enforcement of Literal["required", "recommended"] — that's ty's job
- Field validation beyond construction — dataclasses don't validate, type checkers do

### FRs Covered

- FR16: Finding dataclass with 6 fields (file, line, symbol, rule, message, category)
- FR17: Finding category (required/recommended)
- FR22: Finding is frozen/immutable
- FR23: Kebab-case rule identifiers
- FR41: Finding as shared type for all check modules
- NFR17: Finding's 6-field shape is stable for v1

### Project Structure Notes

New directory created: `src/docvet/checks/` — the checks package
New test directory created: `tests/unit/checks/` — mirrors checks package structure

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Prerequisite PRs] — "Prereq PR 2: Create `src/docvet/checks/__init__.py` with Finding frozen dataclass (6 fields)"
- [Source: _bmad-output/planning-artifacts/architecture.md#Finding Dataclass] — Complete Finding specification with field types and semantics
- [Source: _bmad-output/planning-artifacts/architecture.md#Rule Taxonomy] — All 10 rule identifiers and their categories
- [Source: _bmad-output/planning-artifacts/prd.md#FR16-FR22] — Finding requirements
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2] — BDD acceptance criteria
- [Source: _bmad-output/project-context.md#Python Language Rules] — "Every file starts with `from __future__ import annotations`"
- [Source: _bmad-output/project-context.md#Testing Rules] — Test naming conventions and self-contained test requirements

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

No issues encountered. All tasks completed successfully in a single pass following TDD red-green-refactor cycle.

### Completion Notes List

- ✅ Created `src/docvet/checks/__init__.py` with Finding frozen dataclass
  - Module docstring explains checks package purpose and Finding's role as shared API contract
  - Imported `dataclasses.dataclass` and `typing.Literal` as private (_dataclass, _Literal) to prevent import leakage
  - Defined Finding with all 6 required fields: file, line, symbol, rule, message, category
  - Added `__post_init__` validation to reject empty strings and line numbers < 1
  - Comprehensive docstring on Finding explaining immutability contract and field semantics
  - Explicit `__all__ = ["Finding"]` export for clean public API
- ✅ Created comprehensive unit tests in `tests/unit/checks/test_finding.py`
  - All 11 tests pass validating construction, immutability, hashability, equality, exports, and input validation
  - Test naming follows project conventions: `test_{what}_{condition}_{expected}`
  - Tests use multiple category values ("required" and "recommended") to validate Literal type
  - Frozen behavior test explicitly checks for FrozenInstanceError (not generic AttributeError)
  - Validation tests cover empty strings, negative line numbers, and zero line numbers
- ✅ All quality gates pass
  - ruff check: All checks passed ✓
  - ruff format: All files formatted correctly ✓
  - ty check: All type checks passed ✓
  - pytest: 201 tests pass (11 new + 190 existing, 0 regressions) ✓
  - coverage: 100% coverage on checks module ✓
- ✅ All 5 acceptance criteria satisfied
  - AC#1: checks/__init__.py exports only Finding (import leakage fixed) ✓
  - AC#2: Finding constructed with all 6 fields, frozen and accessible ✓
  - AC#3: Mutation attempts raise FrozenInstanceError (test tightened) ✓
  - AC#4: category accepts "required" and "recommended" ✓
  - AC#5: rule accepts any string (kebab-case identifiers) ✓
- ✅ Code review fixes applied (2026-02-08)
  - Fixed: Module import leakage (dataclass, Literal now private)
  - Fixed: AC#3 test now specifically checks FrozenInstanceError
  - Fixed: Added input validation via __post_init__ (rejects empty strings, line < 1)
  - Added: 6 new validation tests (empty file, negative/zero line, empty symbol/rule/message)
  - Updated: File List to include sprint-status.yaml modification

### Change Log

- 2026-02-08: Implemented Story 1.2 — Created Finding frozen dataclass as shared API contract for all check modules with comprehensive unit tests (11 tests, 100% coverage)
- 2026-02-08: Applied code review fixes — Fixed import leakage, tightened AC#3 test, added input validation with 6 validation tests

### File List

- `src/docvet/checks/__init__.py` (NEW) — Finding frozen dataclass with 6 fields, input validation, and module docstring
- `tests/unit/checks/__init__.py` (NEW) — Empty init file for tests/unit/checks package
- `tests/unit/checks/test_finding.py` (NEW) — 11 unit tests validating Finding construction, immutability, hashability, equality, exports, and input validation
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED) — Updated story status from ready-for-dev to review
