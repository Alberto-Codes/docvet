# Story 28.3: Documentation and Migration Guide

Status: done
Branch: `feat/docs-28-3-documentation-and-migration-guide`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/245

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer evaluating or adopting docvet**,
I want the docs site, README, and configuration reference to document the presence check, its rule, and a migration path from interrogate,
so that I can discover, configure, and adopt the presence check without reading source code.

## Acceptance Criteria

1. **Given** the docs site **When** a user navigates to Checks **Then** `docs/site/checks/presence.md` exists, documenting purpose (Layer 1 replacement for interrogate), configuration options (`enabled`, `min-coverage`, `ignore-init`, `ignore-magic`, `ignore-private`), example CLI output (default/verbose/quiet), and relationship to ruff D100–D107.

2. **Given** the docs site **When** a user navigates to Rules > Presence **Then** `docs/site/rules/missing-docstring.md` exists using the `{{ rule_header() }}` / `{{ rule_fix() }}` macros, with What it detects, Why is this a problem, Example (Violation/Fix tabs), and suppression via `enabled = false`.

3. **Given** the presence check page **When** a user reads the migration section **Then** a "Migrating from interrogate" section provides a 4-step guide: (1) remove interrogate, (2) add docvet presence config, (3) map interrogate options to docvet equivalents, (4) update CI.

4. **Given** `docs/site/configuration.md` **When** a user reads it **Then** the `[tool.docvet.presence]` section is documented with all fields, types, defaults, and an example TOML block. The `warn-on` default list and valid check names include `"presence"`.

5. **Given** the README **When** a user reads the comparison table **Then** the "Presence" row shows docvet covering Layer 1 alongside interrogate (marked as unmaintained). The "What It Checks" section includes a Presence line with `missing-docstring` rule.

6. **Given** `docs/site/index.md` **When** a user reads the quality model **Then** Layer 2 reflects that docvet now covers presence natively, and a Presence card links to `checks/presence.md`.

7. **Given** `docs/site/cli-reference.md` **When** a user reads it **Then** the `docvet presence` subcommand is documented with flags, output examples, and coverage percentage display.

8. **Given** `docs/site/architecture.md` **When** a user reads the pipeline **Then** the check pipeline diagram shows presence as the first check (before enrichment).

9. **Given** `docs/rules.yml` **When** the macros hook processes it **Then** a `missing-docstring` entry exists with id, name, check (`presence`), category (`required`), applies_to, summary, since (`1.7.0`), and fix guidance.

10. **Given** `mkdocs.yml` **When** `mkdocs build --strict` runs **Then** the build succeeds with zero warnings, and presence check/rule pages appear in the nav.

## Tasks / Subtasks

- [x] Task 1: Add `missing-docstring` to `docs/rules.yml` (AC: 9)
  - [x] 1.1 Add entry with id, name, check=presence, category=required, applies_to, summary, since="1.7.0", fix
- [x] Task 2: Create `docs/site/checks/presence.md` (AC: 1, 3)
  - [x] 2.1 Write check page following `checks/coverage.md` pattern (intro, rules table, example output, configuration table)
  - [x] 2.2 Add "Migrating from interrogate" section with 4-step guide
  - [x] 2.3 Document relationship to ruff D100–D107
- [x] Task 3: Create `docs/site/rules/missing-docstring.md` (AC: 2)
  - [x] 3.1 Write rule page following `rules/missing-init.md` pattern (`{{ rule_header() }}`, What it detects, Why, `{{ rule_fix() }}`, Example tabs)
- [x] Task 4: Update `docs/site/configuration.md` (AC: 4)
  - [x] 4.1 Add `[tool.docvet.presence]` section with fields table and example TOML
  - [x] 4.2 Update `warn-on` default value and valid check names to include `"presence"`
- [x] Task 5: Update `README.md` (AC: 5)
  - [x] 5.1 Update comparison table Layer 1 row to show docvet as "Yes" and mark interrogate as "(unmaintained)"
  - [x] 5.2 Add **Presence** line to "What It Checks" section with `missing-docstring` rule
  - [x] 5.3 Update quickstart example output to include a presence finding
- [x] Task 6: Update `docs/site/index.md` (AC: 6)
  - [x] 6.1 Update quality model table: Layer 1 now shows docvet presence (bold)
  - [x] 6.2 Add Presence card to Checks grid
- [x] Task 7: Update `docs/site/cli-reference.md` (AC: 7)
  - [x] 7.1 Add `docvet presence` subcommand section with flags and output examples
  - [x] 7.2 Document coverage percentage in default/verbose summary output
- [x] Task 8: Update `docs/site/architecture.md` (AC: 8)
  - [x] 8.1 Update pipeline diagram to show presence first
- [x] Task 9: Update `mkdocs.yml` nav (AC: 10)
  - [x] 9.1 Add `checks/presence.md` to Checks section
  - [x] 9.2 Add `rules/missing-docstring.md` under Presence in Rules section
- [x] Task 10: Verify `mkdocs build --strict` (AC: 10)
  - [x] 10.1 Run `mkdocs build --strict` and confirm zero warnings

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `mkdocs build --strict` + `docs/site/checks/presence.md` exists with config table, output examples, ruff comparison | PASS |
| 2 | `mkdocs build --strict` + `{{ rule_header() }}` / `{{ rule_fix() }}` render on `rules/missing-docstring.md` | PASS |
| 3 | "Migrating from interrogate" section in `checks/presence.md` with 4-step guide | PASS |
| 4 | `docs/site/configuration.md` has `[tool.docvet.presence]` section with fields table; `warn-on` default and valid names updated | PASS |
| 5 | `README.md` comparison table Layer 1 shows docvet "Yes" + interrogate "(unmaintained)"; What It Checks has Presence line | PASS |
| 6 | `docs/site/index.md` quality model Layer 1 bold with docvet presence; Presence card in grid | PASS |
| 7 | `docs/site/cli-reference.md` has `docvet presence` section with default/verbose output examples | PASS |
| 8 | `docs/site/architecture.md` pipeline diagram includes Presence before Enrichment | PASS |
| 9 | `docs/rules.yml` has `missing-docstring` entry with all required fields (since="1.7.0") | PASS |
| 10 | `mkdocs build --strict` passes with zero warnings, nav includes presence pages | PASS |

## Dev Notes

### Architecture Patterns and Constraints

- **Check page pattern**: Follow `docs/site/checks/coverage.md` structure (shortest, most analogous — single rule, config table, example output). NOT `enrichment.md` (too complex, 10 rules).
- **Rule page pattern**: Follow `docs/site/rules/missing-init.md` structure (uses `{{ rule_header() }}` and `{{ rule_fix() }}` Jinja2 macros from `docs/main.py` which reads `docs/rules.yml`).
- **Macro system**: `docs/main.py` defines `rule_header()` and `rule_fix()` macros that read from `docs/rules.yml`. The `missing-docstring` entry MUST exist in `rules.yml` before the rule page will render.
- **Configuration page**: Uses markdown tables. Add `[tool.docvet.presence]` section after the existing `[tool.docvet.freshness]` section. Update the `warn-on` default and valid check names.
- **mkdocs.yml nav**: Checks section lists pages directly (no subsections). Rules section groups by check name.
- **Six-layer model**: Currently positions docvet as Layers 3–6 only. This story CHANGES the positioning — docvet now covers Layer 1 natively. The model table in `index.md` and README must reflect this.

### Source Tree Components to Touch

| File | Action | Notes |
|------|--------|-------|
| `docs/rules.yml` | Add entry | `missing-docstring` with check=presence, since="1.7.0" |
| `docs/site/checks/presence.md` | **New** | Check page + migration guide |
| `docs/site/rules/missing-docstring.md` | **New** | Rule page with macros |
| `docs/site/configuration.md` | Edit | Add `[tool.docvet.presence]` section, update warn-on |
| `docs/site/index.md` | Edit | Update quality model table + add Presence card |
| `docs/site/cli-reference.md` | Edit | Add `docvet presence` subcommand |
| `docs/site/architecture.md` | Edit | Update pipeline diagram |
| `README.md` | Edit | Update comparison table + What It Checks |
| `mkdocs.yml` | Edit | Add nav entries for presence check and rule |

### Key Technical Details

**PresenceConfig fields** (from `src/docvet/config.py`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable/disable the presence check |
| `min-coverage` | `float` | `0.0` | Minimum coverage threshold (0.0 = no enforcement) |
| `ignore-init` | `bool` | `true` | Skip `__init__` methods |
| `ignore-magic` | `bool` | `true` | Skip magic methods (`__repr__`, etc.) |
| `ignore-private` | `bool` | `true` | Skip private symbols (`_name`) |

**CLI output formats** (from Story 28.2):
- Default: `"Vetted N files [presence, ...] — X findings, 87.0% coverage. (0.3s)"`
- Verbose: `"Docstring coverage: 87/100 symbols (87.0%) — below 95.0% threshold"`
- JSON: `"presence_coverage": {"documented": 87, "total": 100, "percentage": 87.0, "threshold": 95.0, "passed": false}`

**Pipeline order**: `presence → enrichment → freshness → coverage → griffe`

**Interrogate mapping** (for migration guide):

| interrogate option | docvet equivalent |
|-------------------|-------------------|
| `--fail-under N` | `min-coverage = N` |
| `--ignore-init-method` | `ignore-init = true` (default) |
| `--ignore-magic` | `ignore-magic = true` (default) |
| `--ignore-private` | `ignore-private = true` (default) |
| `--ignore-module` | No equivalent (modules always checked) |
| `-e/--exclude` | `[tool.docvet] exclude = [...]` |

### Testing Standards

This is a docs-only story. Verification is:
1. `mkdocs build --strict` passes with zero warnings
2. All new pages render correctly (check page, rule page)
3. Macro expansion works (`{{ rule_header() }}`, `{{ rule_fix() }}`)
4. All internal links resolve (no broken cross-references)
5. `uv run docvet check --all` still passes (docstrings unchanged)

### Previous Story Intelligence (28.2)

- **SonarQube CC refactoring done**: Three helpers extracted (`_write_timing`, `_format_coverage_line`, `_resolve_format`). No source code changes needed in this story.
- **`PresenceStats.percentage` property**: Added during 28.2 code review — use this in any docs examples showing the Python API.
- **Config default changed**: `warn_on` default now starts with `"presence"`. Configuration docs must reflect this.
- **Documentation Impact was explicitly "None" in 28.2**: This story IS the deferred documentation work.
- **Coverage percentage in summary**: New feature from 28.2 — verbose output shows `Docstring coverage: N/M symbols (X.X%)`. Document in CLI reference.

### Git Intelligence

Recent commits:
- `067fbbd` feat(presence): wire presence check into CLI pipeline and reporting (#244)
- `a48edd3` feat(presence): add core presence detection and configuration (#240)
- `83575c5` chore(deps): add dependency health gates and drop interrogate (#235)

Key insight: PR #235 dropped interrogate from CI. The migration guide should reference this as context — docvet presence is the zero-dependency replacement.

### Project Structure Notes

- Docs pages live in `docs/site/` (mkdocs `docs_dir` setting)
- Rule metadata lives in `docs/rules.yml` at project root's `docs/` dir
- Macros hook is `docs/main.py`
- No test files needed — this is pure documentation

### References

- [Source: docs/site/checks/coverage.md] — Check page template (single-rule check, config table)
- [Source: docs/site/rules/missing-init.md] — Rule page template (macros, example tabs)
- [Source: docs/rules.yml] — Rule metadata catalog
- [Source: docs/main.py] — Macros hook defining `rule_header()` and `rule_fix()`
- [Source: mkdocs.yml lines 87-125] — Nav structure
- [Source: src/docvet/config.py] — PresenceConfig field definitions
- [Source: src/docvet/checks/presence.py] — check_presence implementation
- [Source: _bmad-output/implementation-artifacts/28-2-cli-wiring-and-pipeline-integration.md] — Previous story learnings

### Documentation Impact

- Pages: docs/site/checks/presence.md (NEW), docs/site/rules/missing-docstring.md (NEW), docs/site/configuration.md, docs/site/index.md, docs/site/cli-reference.md, docs/site/architecture.md, README.md, mkdocs.yml, docs/rules.yml
- Nature of update: This IS the documentation story — all pages listed above are the primary deliverable.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1093 passed, no regressions
- [x] `uv run docvet check --all` — zero findings, 100.0% coverage
- [x] `mkdocs build --strict` — zero warnings (replaces interrogate gate for docs-only story)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Verified LSP does NOT include presence check before documenting architecture — reverted incorrect claim.
- `interrogate -v` quality gate N/A — interrogate was dropped in PR #235. Replaced with `mkdocs build --strict` for this docs-only story.

### Completion Notes List

- Added `missing-docstring` rule entry to `docs/rules.yml` (20 total rules now)
- Created `docs/site/checks/presence.md` with check page, config table, output examples, ruff comparison, and 4-step interrogate migration guide
- Created `docs/site/rules/missing-docstring.md` with `{{ rule_header() }}` / `{{ rule_fix() }}` macros, violation/fix tabs, suppression docs
- Updated `docs/site/configuration.md` with `[tool.docvet.presence]` section and updated `warn-on` defaults to include `"presence"` (5 checks)
- Updated `README.md`: Layer 1 row now shows docvet "Yes" + interrogate "(unmaintained)", added Presence line to What It Checks, updated rule count to 20, added presence finding to example output, added `docvet presence` to subcommand table
- Updated `docs/site/index.md`: quality model table Layer 1 now bold (docvet presence), added Presence card to grid
- Updated `docs/site/cli-reference.md`: added `docvet presence` subcommand section with default/verbose output examples, updated command count to 6
- Updated `docs/site/architecture.md`: pipeline diagram includes Presence as first check, modules table includes `checks/presence.py`
- Updated `mkdocs.yml` nav: added `checks/presence.md` and `rules/missing-docstring.md` under new Presence group
- **Cross-cutting**: Added `tests/unit/test_docs_infrastructure.py` — 13 tests validating `docs/rules.yml` schema integrity, bidirectional rule-page consistency, and mkdocs.yml nav file existence (TEA-identified P1 risk gap)

### Change Log

- 2026-03-02: Story 28.3 implementation — documented presence check across docs site, README, configuration reference, and mkdocs nav. Added interrogate migration guide.
- 2026-03-02: Cross-cutting improvement — added docs infrastructure tests (rules.yml schema, macro compat, nav consistency). 13 new tests, 1106 total.
- 2026-03-02: Code review — fixed 3 findings (H1: wrong check list in presence.md examples, M1: inconsistent [required] suffix in README, M2: config section ordering). L1 (architecture diagram) skipped by consensus.

### File List

- `docs/rules.yml` (modified)
- `tests/unit/test_docs_infrastructure.py` (new — cross-cutting)
- `docs/site/checks/presence.md` (new)
- `docs/site/rules/missing-docstring.md` (new)
- `docs/site/configuration.md` (modified)
- `docs/site/index.md` (modified)
- `docs/site/cli-reference.md` (modified)
- `docs/site/architecture.md` (modified)
- `README.md` (modified)
- `mkdocs.yml` (modified)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified)
- `_bmad-output/implementation-artifacts/28-3-documentation-and-migration-guide.md` (modified)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow + party mode consensus)

### Outcome

Approved with fixes applied (3 findings fixed, 1 skipped by consensus)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | `checks/presence.md` example output showed `[presence, enrichment, freshness, coverage]` instead of `[presence]` — wrong check list for single-check subcommand | Fixed: changed both Default and Verbose summary lines to `[presence]` |
| M1 | MEDIUM | README example output inconsistent — new `missing-docstring` line had `[required]` suffix but pre-existing lines did not | Fixed: added `[required]` suffix to all three pre-existing example lines |
| M2 | MEDIUM | Configuration section ordering (Freshness → Enrichment → Presence) didn't match pipeline order or Complete Example TOML | Fixed: moved Presence Options section before Freshness Options |
| L1 | LOW | Architecture pipeline diagram shows checks as flat subgraph without sequential ordering arrows | Skipped: party mode consensus — diagram accurately reflects architectural independence; CLI order is implementation detail, not architecture |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
