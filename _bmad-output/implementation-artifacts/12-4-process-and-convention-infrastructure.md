# Story 12.4: Process & Convention Infrastructure

Status: review
Branch: `feat/conventions-12-4-process-infrastructure`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a docvet contributor,
I want quality gates and project conventions structurally enforced in workflow templates,
so that retro carry-forward items stop regressing and every story automatically includes the right quality checks.

## Acceptance Criteria

1. **Given** the create-story workflow template **When** a new story is generated from it **Then** the story's quality gate section includes all 6 mandatory checks: `ruff check`, `ruff format`, `ty check`, `pytest`, `docvet check --all`, and `interrogate -v` **And** each gate is listed as mandatory (not optional)
2. **Given** the create-story workflow template **When** a new story is generated from it **Then** the story includes a mandatory "Code Review" section **And** the section cannot be omitted — it is part of the template structure, not a dev agent choice
3. **Given** the project needs a documented foundational principle **When** the developer creates a conventions file (`.claude/rules/conventions.md`) **Then** the file states the principle: "Every symbol deserves its natural language representation" **And** the principle is contextualized with rationale from Epic 9 retro (docstrings are the human-readable and AI-readable translation of what code does) **And** the file is discoverable by the dev agent via the `.claude/rules/` directory
4. **Given** all 3 process changes are made **When** a new story is created using the updated workflow **Then** the story output includes all 6 quality gates (including `ty check`, `docvet check --all`, `interrogate -v`), a code review section, and the conventions file is loadable as a project rule

## Tasks / Subtasks

- [x] Task 1: Add quality gates section to story template (AC: 1)
  - [x] 1.1 Open `_bmad/bmm/workflows/4-implementation/create-story/template.md`
  - [x] 1.2 Add a `## Quality Gates` section after `## Dev Notes` listing 6 mandatory checks: `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `uv run pytest`, `uv run docvet check --all`, `interrogate -v`
  - [x] 1.3 Mark all 6 gates as mandatory (not optional) with checkbox format for dev agent tracking
- [x] Task 2: Add mandatory code review section to story template (AC: 2)
  - [x] 2.1 Add a `## Code Review` section at the end of the template (after `## Dev Agent Record`)
  - [x] 2.2 Include subsections: Reviewer, Outcome, Findings Summary table, Verification checklist
  - [x] 2.3 Add HTML comment instructing dev agent that this section is mandatory and must be filled before marking story done
- [x] Task 3: Create conventions rules file (AC: 3)
  - [x] 3.1 Create `.claude/rules/conventions.md`
  - [x] 3.2 State the foundational principle: "Every symbol deserves its natural language representation"
  - [x] 3.3 Add rationale from Epic 9 retro: docstrings are the human-readable and AI-readable translation of what code does
  - [x] 3.4 Add practical implications: no config suppression to silence own rules, genuine docstrings over overrides
- [x] Task 4: Verify integration (AC: 4)
  - [x] 4.1 Confirm `.claude/rules/conventions.md` is auto-discovered (it's in the `.claude/rules/` directory which CLAUDE.md already references)
  - [x] 4.2 Visually inspect updated template to confirm quality gates and code review sections are present and correctly formatted
  - [x] 4.3 Run `uv run ruff check .` and `uv run ruff format --check .` to confirm no format issues in non-Python files (N/A — these are .md files, so just verify no regressions)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- Note: This story has zero source code changes — no automated tests. Verification is manual/structural. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: inspect template.md for `## Quality Gates` section with 6 mandatory checks | PASS |
| 2 | Manual: inspect template.md for `## Code Review` section with required subsections | PASS |
| 3 | Manual: inspect `.claude/rules/conventions.md` exists, contains principle and rationale | PASS |
| 4 | Manual: create-story workflow produces output with all 3 additions; conventions file in `.claude/rules/` | PASS |

## Dev Notes

### Story Context

This is the final story in Epic 12 (Housekeeping & Quality Infrastructure). It addresses three retro carry-forward items that were identified across Epics 8-10 and repeatedly dropped because they competed with feature work. The solution: structurally enforce them in templates and rules files so they happen automatically.

**Zero source code changes.** Only workflow template modifications and a new rules file.

### FR-to-Source Traceability

| FR | Source | What to do |
|----|--------|------------|
| FR-H5 | Epic 9 retro action #1: "Enforce `ty check` as mandatory quality gate" | Add all 6 quality gates to story template (`ty check` + `docvet check --all` + `interrogate -v` alongside existing `ruff check`, `ruff format`, `pytest`) |
| FR-H6 | Epic 9 retro insight #1: "every symbol deserves its natural language representation" | Create `.claude/rules/conventions.md` with principle and rationale |
| FR-H7 | Epic 8 retro challenge #1: "Story 8.3 missing code review section" | Add mandatory `## Code Review` section to story template |

### File Scope

| File | Action |
|------|--------|
| `_bmad/bmm/workflows/4-implementation/create-story/template.md` | Modified — add `## Quality Gates` section, add `## Code Review` section |
| `.claude/rules/conventions.md` | New — foundational principle with rationale |

**No other files should be modified.** No source code, no tests, no CLI, no config.

### Template Modification Detail

**Current template structure** (`template.md`):
1. Story header (title, status, branch)
2. `## Story` (user story format)
3. `## Acceptance Criteria`
4. `## Tasks / Subtasks`
5. `## AC-to-Test Mapping`
6. `## Dev Notes` (with `### Project Structure Notes` and `### References`)
7. `## Dev Agent Record` (model, debug log, completion notes, file list)

**After modification:**
1. Story header (title, status, branch) — unchanged
2. `## Story` — unchanged
3. `## Acceptance Criteria` — unchanged
4. `## Tasks / Subtasks` — unchanged
5. `## AC-to-Test Mapping` — unchanged
6. `## Dev Notes` — unchanged
7. **`## Quality Gates`** — NEW: mandatory checks with checkbox format
8. `## Dev Agent Record` — unchanged
9. **`## Code Review`** — NEW: mandatory review section with structure

### Quality Gates Content

The quality gates section lists 6 mandatory checks that must all pass before a story can be marked done:

- `uv run ruff check .` — lint
- `uv run ruff format --check .` — format
- `uv run ty check` — type check
- `uv run pytest` — tests
- `uv run docvet check --all` — full-strength dogfooding (zero docvet findings on own codebase)
- `interrogate -v` — docstring coverage ≥ 95%

The first 5 use `uv run` prefix. `interrogate` also uses `uv run` if installed as a dev dependency (check `pyproject.toml`). These are already documented in `project-context.md` as CI gates. The template addition ensures the dev agent runs them explicitly and tracks them per-story. Adding `docvet check --all` structurally enforces full-strength dogfooding per Epic 9 retro insight #1.

### Conventions File Content

The foundational principle from Epic 9 retro:

> "Every symbol deserves its natural language representation."

Rationale: Docstrings are the human-readable and AI-readable translation of what code does. Examples, attributes, raises, yields — all sections serve as the natural language bridge between code and understanding. The tool should not suppress its own rules to make itself quiet; it should write the docstrings to make the code understood.

Practical implications:
- No config suppression to silence own rules on own codebase
- Genuine docstrings over `[tool.docvet.enrichment]` overrides
- Full-strength dogfooding: the tool runs on itself with zero config exemptions

### Previous Story Intelligence (12.3)

**What worked:**
- Same zero-debug pattern as 12.1/12.2 — clean, focused changes
- Module-specific verification before full suite
- `analyze_code_snippet` for CC verification (not applicable here — no code changes)

**Key lesson for 12.4:**
- This story is documentation/template only — no SonarQube, no tests, no code analysis needed
- Focus on structural correctness of the template modifications
- Ensure the conventions file follows existing `.claude/rules/` patterns (see `dev-quality-checklist.md`, `sonarqube.md` for style reference)

### Git Intelligence

Latest commits on develop:
- `b82da45` refactor: resolve remaining SonarQube minor findings (#76) — Story 12.3
- `3bccab1` chore: replace hardcoded LAN IP with env vars in sonarqube rule
- `2a191d3` refactor: reduce cognitive complexity of 7 functions across 5 non-enrichment modules (#74) — Story 12.2
- `64f0945` refactor(enrichment): reduce cognitive complexity of 5 functions below SonarQube threshold (#73) — Story 12.1

Codebase is clean. No pending changes. Story 12.3 PR is in review.

### Critical Constraints

- **Zero source code changes** — only `.md` files in `_bmad/` and `.claude/rules/`
- **Template changes must be additive** — do not remove or modify existing template sections
- **Conventions file must follow existing `.claude/rules/` style** — concise, actionable, developer-focused
- **No test changes** — this story produces no testable source code
- **Template quality gates must match project-context.md CI gates** — consistency matters. All 6 gates: ruff check, ruff format, ty check, pytest, docvet check --all, interrogate -v

### Project Structure Notes

- `.claude/rules/` already has 7 files — new `conventions.md` follows the same pattern
- Template at `_bmad/bmm/workflows/4-implementation/create-story/template.md` is used by the BMad workflow to generate story files
- The create-story workflow reads the template and populates placeholders — new sections with static content (no placeholders) will be included verbatim

### References

- [Source: _bmad-output/planning-artifacts/epics-housekeeping.md#Story 12.4]
- [Source: _bmad-output/implementation-artifacts/epic-9-retro-2026-02-21.md#Action Items — FR-H5 (#1), FR-H6 (#2)]
- [Source: _bmad-output/implementation-artifacts/epic-8-retro-2026-02-19.md#Challenges — FR-H7 (#1)]
- [Source: _bmad-output/project-context.md#CI gates — ruff check, ruff format, ty check, pytest, interrogate -v]
- [Source: _bmad-output/implementation-artifacts/epic-9-retro-2026-02-21.md#Action Item #6 — docvet check --staged for pre-commit, docvet check --all for quality gates]
- [Source: _bmad/bmm/workflows/4-implementation/create-story/template.md — current template structure]
- [Source: .claude/rules/ — existing rules files for style reference]

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. -->

- [x] `uv run ruff check .` — zero violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 731 passed, 1 skipped, no regressions
- [x] `uv run docvet check --all` — N/A (no source code changes)
- [x] `uv run interrogate -v` — N/A (no source code changes)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero-debug story (template/rules only, no source code changes).

### Completion Notes List

- Task 1: Added `## Quality Gates` section to `template.md` after `## Dev Notes` with 6 mandatory checks in checkbox format. Each check includes the full command and a description of the expected result. HTML comment marks all gates as mandatory.
- Task 2: Added `## Code Review` section at end of `template.md` (after `## Dev Agent Record`) with subsections: Reviewer, Outcome, Findings Summary table, and Verification checklist. HTML comment marks section as mandatory per Epic 8 retro.
- Task 3: Created `.claude/rules/conventions.md` with foundational principle ("Every symbol deserves its natural language representation"), Epic 9 retro rationale, and practical implications (no config suppression, genuine docstrings, full-strength dogfooding).
- Task 4: Verified integration — conventions file is 8th file in `.claude/rules/` (auto-discovered), template structure matches specification, all quality gates pass with zero regressions (731 tests pass).

### Change Log

- 2026-02-22: Implemented all 4 tasks — added Quality Gates and Code Review sections to story template, created conventions rules file

### File List

- `_bmad/bmm/workflows/4-implementation/create-story/template.md` — Modified (added `## Quality Gates` and `## Code Review` sections)
- `.claude/rules/conventions.md` — New (foundational principle with rationale)

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
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, File List all filled)
