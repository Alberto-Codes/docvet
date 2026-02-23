---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
inputDocuments:
  - '_bmad-output/implementation-artifacts/epic-9-retro-2026-02-21.md'
  - '_bmad-output/implementation-artifacts/epic-10-retro-2026-02-21.md'
  - '_bmad-output/implementation-artifacts/epic-8-retro-2026-02-19.md'
  - '_bmad-output/implementation-artifacts/epic-7-retro-2026-02-11.md'
  - '_bmad-output/implementation-artifacts/epic-6-retro-2026-02-11.md'
  - 'SonarQube project: docvet (18 open issues on develop)'
---

# docvet - Epic Breakdown (Housekeeping & Quality Infrastructure)

## Overview

This document provides the epic and story breakdown for the docvet Housekeeping & Quality Infrastructure epic, decomposing requirements from retrospective carry-forward items (Epics 6-10) and SonarQube static analysis findings into implementable stories.

## Requirements Inventory

### Functional Requirements

**SonarQube Findings Cleanup:**

- FR-H1: Refactor all functions exceeding cognitive complexity threshold of 15 (S3776) — 11 functions across 6 modules:
  - `enrichment.py`: 5 functions (CC 53, 21, 20, 17, 17)
  - `config.py`: 1 function (CC 29)
  - `discovery.py`: 2 functions (CC 23, 20)
  - `freshness.py`: 2 functions (CC 19, 18)
  - `griffe_compat.py`: 1 function (CC 17)
  - `coverage.py`: 1 function (CC 16)
- FR-H2: Extract duplicate string literals into named constants (S1192) — 2 instances:
  - `enrichment.py`: `"See Also"` duplicated 4 times
  - `config.py`: `"[tool.docvet]"` duplicated 4 times
- FR-H3: Remove redundant `continue` statement in `freshness.py` line 261 (S3626)
- FR-H4: Resolve `node_index` unused parameter findings (S1172) in `enrichment.py` — 3 instances, by-design for interface consistency. Accept as won't-fix in SonarQube.

**Retro Carry-Forward — Process & Documentation:**

- FR-H5: Add `ty check` as mandatory quality gate in story template documentation (Epic 9 retro action #1 — carried forward twice, dropped in Epics 9 and 10)
- FR-H6: Document the foundational principle "every symbol deserves its natural language representation" in project conventions (Epic 9 retro action #2 — carried forward twice, dropped in Epics 9 and 10)
- FR-H7: Ensure story template includes mandatory code review section (Epic 8 retro — Story 8.3 was missing review section)

### NonFunctional Requirements

- NFR-H1: All SonarQube findings on `develop` must be resolved — either fixed or explicitly accepted as won't-fix — zero unresolved open issues
- NFR-H2: Zero test regressions — all 729 tests must continue passing after every refactor
- NFR-H3: All refactored functions must have cognitive complexity at or below 15 (SonarQube threshold)
- NFR-H4: Refactoring must preserve identical behavior — no functional changes, only structural improvements
- NFR-H5: Process improvements (ty check, story template) must be structurally enforced, not just documented

### Additional Requirements

**From Retro Pattern Analysis (Epics 6-10):**

- Retro action items regress when they compete with feature work — documentation/process items need their own tracking epic (Epic 10 insight #2)
- "Structural enforcement over good intentions" is a proven team principle — process changes must be embedded in templates/hooks, not just written down (Epics 6-10 recurring theme)
- The create-story workflow is a leverage point — anything baked into the template gets done automatically by the dev agent (Epic 10 insight #3)

**From SonarQube Integration Notes:**

- `S1172` (unused `node_index`) findings are by design — enrichment `_check_*` functions take `node_index` for interface consistency even when unused (documented in `.claude/rules/sonarqube.md`)
- Cognitive complexity (S3776, threshold 15) is the dominant finding category — 11 of 18 open issues

### FR Coverage Map

| FR | Story | Description |
|----|-------|-------------|
| FR-H1 (enrichment) | 12.1 | Refactor 5 enrichment.py functions exceeding CC 15 (CC 53, 21, 20, 17, 17) |
| FR-H1 (non-enrichment) | 12.2 | Refactor 6 functions across config.py, discovery.py, freshness.py, griffe_compat.py, coverage.py |
| FR-H2 | 12.3 | Extract duplicate string literals into named constants |
| FR-H3 | 12.3 | Remove redundant `continue` in freshness.py |
| FR-H4 | 12.3 | Accept `node_index` unused parameter findings as won't-fix |
| FR-H5 | 12.4 | Add `ty check` to story template quality gates |
| FR-H6 | 12.4 | Document foundational principle in project conventions |
| FR-H7 | 12.4 | Add mandatory code review section to story template |

## Epic List

### Epic 12: Housekeeping & Quality Infrastructure

**Goal:** Resolve all SonarQube findings and establish structurally-enforced quality conventions so the docvet codebase exemplifies the code quality standards it enforces on others.

**User Value:** A developer contributing to docvet gets a clean SonarQube dashboard (zero open findings), structurally-enforced quality gates in every story, and documented project principles — eliminating recurring retro carry-forwards.

**Dependencies:** None — standalone epic, parallel with Epic 11 (Documentation Site).

**Recommended Story Order:** 12.1 → 12.2 → 12.3 → 12.4. Stories 12.1 and 12.2 refactor function bodies in `enrichment.py` and `config.py`; Story 12.3 extracts constants in the same files. Running 12.3 after the CC refactoring avoids merge conflicts on the same code regions. Story 12.4 is fully independent (zero source code changes) and can run in parallel with any other story.

**CC Verification Method:** During development, use `mcp__sonarqube__analyze_code_snippet` with `projectKey: "docvet"` for immediate per-function cognitive complexity feedback. The SonarQube dashboard scan on `develop` serves as the final confirmation gate (scans lag behind local changes).

| Story | Theme | FRs Covered | Scope |
|-------|-------|-------------|-------|
| 12.1 | Enrichment CC Refactoring | FR-H1 (partial) | 5 functions in `enrichment.py` (CC 53, 21, 20, 17, 17) |
| 12.2 | Non-Enrichment CC Refactoring | FR-H1 (partial) | 6 functions across 5 modules (config, discovery, freshness, griffe_compat, coverage) |
| 12.3 | SonarQube Minor Findings | FR-H2, FR-H3, FR-H4 | Constants extraction, redundant continue, by-design accepts |
| 12.4 | Process & Convention Infrastructure | FR-H5, FR-H6, FR-H7 | ty check gate, foundational principle doc, mandatory review section |

## Epic 12: Housekeeping & Quality Infrastructure — Stories

### Story 12.1: Enrichment Module Cognitive Complexity Refactoring

As a docvet contributor,
I want the enrichment module's complex functions refactored to cognitive complexity ≤ 15,
So that the codebase exemplifies the maintainability standards SonarQube enforces.

**FRs covered:** FR-H1 (enrichment portion)

**Functions to refactor:**

| Function | Line | Current CC | Target |
|----------|------|-----------|--------|
| `_check_missing_raises` | 150 | 20 | ≤ 15 |
| `_check_missing_warns` | 366 | 17 | ≤ 15 |
| `_is_dataclass` | 506 | 17 | ≤ 15 |
| `_has_self_assignments` | 652 | 21 | ≤ 15 |
| `check_enrichment` | 1163 | 53 | ≤ 15 |

**Acceptance Criteria:**

AC 1:
**Given** the function `_check_missing_raises` in `enrichment.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing enrichment tests pass without modification

AC 2:
**Given** the function `_check_missing_warns` in `enrichment.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing enrichment tests pass without modification

AC 3:
**Given** the function `_is_dataclass` in `enrichment.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing enrichment tests pass without modification

AC 4:
**Given** the function `_has_self_assignments` in `enrichment.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing enrichment tests pass without modification

AC 5:
**Given** the public orchestrator `check_enrichment` in `enrichment.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing enrichment tests pass without modification

AC 6:
**Given** all 5 refactored functions
**When** `uv run pytest` is executed
**Then** all 729 tests pass with zero failures
**And** no functional behavior has changed (identical outputs for identical inputs)

---

### Story 12.2: Non-Enrichment Module Cognitive Complexity Refactoring

As a docvet contributor,
I want the remaining complex functions across config, discovery, freshness, griffe, and coverage modules refactored to cognitive complexity ≤ 15,
So that every source module passes SonarQube's maintainability threshold.

**FRs covered:** FR-H1 (non-enrichment portion)

**Functions to refactor:**

| Module | Function | Line | Current CC | Target |
|--------|----------|------|-----------|--------|
| `config.py` | `load_config` | 426 | 29 | ≤ 15 |
| `discovery.py` | `_walk_all` | 113 | 23 | ≤ 15 |
| `discovery.py` | `discover_files` | 180 | 20 | ≤ 15 |
| `freshness.py` | `_parse_blame_timestamps` | 211 | 19 | ≤ 15 |
| `freshness.py` | `check_freshness_drift` | 319 | 18 | ≤ 15 |
| `griffe_compat.py` | `check_griffe_compat` | 152 | 17 | ≤ 15 |
| `coverage.py` | `check_coverage` | 19 | 16 | ≤ 15 |

**Acceptance Criteria:**

AC 1:
**Given** `load_config` in `config.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing config tests pass without modification

AC 2:
**Given** `_walk_all` in `discovery.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing discovery tests pass without modification

AC 3:
**Given** `discover_files` in `discovery.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing discovery tests pass without modification

AC 4:
**Given** `_parse_blame_timestamps` in `freshness.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing freshness tests pass without modification

AC 5:
**Given** `check_freshness_drift` in `freshness.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing freshness tests pass without modification

AC 6:
**Given** `check_griffe_compat` in `griffe_compat.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing griffe tests pass without modification

AC 7:
**Given** `check_coverage` in `coverage.py`
**When** analyzed by SonarQube
**Then** cognitive complexity is at or below 15
**And** all existing coverage tests pass without modification

AC 8:
**Given** all 7 refactored functions across 5 modules
**When** `uv run pytest` is executed
**Then** all 729 tests pass with zero failures
**And** no functional behavior has changed

---

### Story 12.3: SonarQube Minor Findings Resolution

As a docvet contributor,
I want all remaining SonarQube code smell findings resolved,
So that the project achieves zero open issues on the SonarQube dashboard.

**FRs covered:** FR-H2, FR-H3, FR-H4

**Findings to resolve:**

| Rule | File | Issue | Resolution |
|------|------|-------|------------|
| S1192 | `enrichment.py` | `"See Also"` duplicated 4 times | Extract to named constant |
| S1192 | `config.py` | `"[tool.docvet]"` duplicated 4 times | Extract to named constant |
| S3626 | `freshness.py` line 261 | Redundant `continue` | Remove statement |
| S1172 | `enrichment.py` line 838 | Unused `node_index` parameter | Accept as won't-fix in SonarQube |
| S1172 | `enrichment.py` line 1020 | Unused `node_index` parameter | Accept as won't-fix in SonarQube |
| S1172 | `enrichment.py` line 1107 | Unused `node_index` parameter | Accept as won't-fix in SonarQube |

**Acceptance Criteria:**

AC 1:
**Given** the string `"See Also"` is used 4 times in `enrichment.py`
**When** the developer extracts it into a module-level constant
**Then** all 4 usages reference the constant
**And** SonarQube S1192 finding for `enrichment.py` is resolved

AC 2:
**Given** the string `"[tool.docvet]"` is used 4 times in `config.py`
**When** the developer extracts it into a module-level constant
**Then** all 4 usages reference the constant
**And** SonarQube S1192 finding for `config.py` is resolved

AC 3:
**Given** the redundant `continue` at `freshness.py` line 261
**When** the developer removes the statement
**Then** control flow behavior is unchanged
**And** SonarQube S3626 finding is resolved

AC 4:
**Given** 3 S1172 findings for unused `node_index` parameters in `enrichment.py`
**When** the developer marks each as "accepted" (won't-fix) in SonarQube
**Then** all 3 findings show status `ACCEPTED`
**And** the rationale is documented (interface consistency for `_check_*` dispatch pattern)

AC 5:
**Given** all 6 findings addressed (3 fixed, 3 accepted)
**When** `uv run pytest` is executed
**Then** all 729 tests pass with zero failures

---

### Story 12.4: Process & Convention Infrastructure

As a docvet contributor,
I want quality gates and project conventions structurally enforced in workflow templates,
So that retro carry-forward items stop regressing and every story automatically includes the right quality checks.

**FRs covered:** FR-H5, FR-H6, FR-H7

**Acceptance Criteria:**

AC 1:
**Given** the create-story workflow template
**When** a new story is generated from it
**Then** the story's quality gate section includes `ty check` alongside `ruff check`, `ruff format`, and `pytest`
**And** the gate is listed as mandatory (not optional)

AC 2:
**Given** the create-story workflow template
**When** a new story is generated from it
**Then** the story includes a mandatory "Code Review" section
**And** the section cannot be omitted — it is part of the template structure, not a dev agent choice

AC 3:
**Given** the project needs a documented foundational principle
**When** the developer creates a conventions file (e.g., `.claude/rules/conventions.md`)
**Then** the file states the principle: "Every symbol deserves its natural language representation"
**And** the principle is contextualized with rationale from Epic 9 retro (docstrings are the human-readable and AI-readable translation of what code does)
**And** the file is discoverable by the dev agent via the `.claude/rules/` directory

AC 4:
**Given** all 3 process changes are made
**When** a new story is created using the updated workflow
**Then** the story output includes `ty check` in quality gates, a code review section, and the conventions file is loadable as a project rule
