# Story 15.2: Fix Own Cross-Reference Syntax

Status: done
Branch: `feat/docs-15-2-fix-own-cross-reference-syntax`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer reading docvet's API reference**,
I want **See Also entries to be clickable links that navigate to the referenced module's documentation page**,
So that **I can navigate between related modules without manually searching the sidebar**.

## Acceptance Criteria

1. **Given** module docstrings across ~12 files use plain backtick syntax in See Also sections (e.g., `` `docvet.checks` ``) **When** all See Also entries are converted to mkdocstrings bracket cross-reference syntax (e.g., `` [`docvet.checks`][] ``) **Then** every See Also entry uses the `` [`fully.qualified.name`][] `` format consistently

2. **Given** the See Also entries use bracket syntax **When** the docs site is built and a developer views a module's API reference page **Then** each See Also entry renders as a clickable code-formatted hyperlink that navigates to the referenced module's API reference page

3. **Given** the cross-references use fully-qualified module paths **When** `mkdocs build --strict` is executed **Then** all cross-references resolve successfully with zero "could not find" warnings

4. **Given** all See Also entries are updated **When** `docvet check --all` is executed against the updated codebase **Then** the `missing-cross-references` rule produces zero findings (bracket syntax satisfies the existing `_XREF_MD_LINK` pattern)

5. **Given** all changes are applied **When** `uv run pytest` is executed **Then** all existing tests pass with zero failures

## Tasks / Subtasks

- [x] Task 1: Convert See Also entries in all 12 module docstrings (AC: 1)
  - [x] `src/docvet/__init__.py` — 2 entries: `docvet.checks`, `docvet.cli`
  - [x] `src/docvet/cli.py` — 3 entries: `docvet.checks`, `docvet.config`, `docvet.discovery`
  - [x] `src/docvet/config.py` — 2 entries: `docvet.cli`, `docvet.checks`
  - [x] `src/docvet/discovery.py` — 2 entries: `docvet.cli`, `docvet.checks`
  - [x] `src/docvet/ast_utils.py` — 2 entries: `docvet.checks.enrichment`, `docvet.checks.freshness`
  - [x] `src/docvet/reporting.py` — 2 entries: `docvet.cli`, `docvet.checks`
  - [x] `src/docvet/checks/__init__.py` — 4 entries: `docvet.checks.enrichment`, `docvet.checks.freshness`, `docvet.checks.coverage`, `docvet.checks.griffe_compat`
  - [x] `src/docvet/checks/_finding.py` — 1 entry: `docvet.checks`
  - [x] `src/docvet/checks/enrichment.py` — 3 entries: `docvet.config`, `docvet.ast_utils`, `docvet.checks`
  - [x] `src/docvet/checks/freshness.py` — 2 entries: `docvet.config`, `docvet.checks`
  - [x] `src/docvet/checks/coverage.py` — 2 entries: `docvet.checks`, `docvet.config`
  - [x] `src/docvet/checks/griffe_compat.py` — 2 entries: `docvet.checks`, `docvet.config`
- [x] Task 2: Validate with `mkdocs build --strict` (AC: 3)
  - [x] Run `mkdocs build --strict`
  - [x] Verify zero "could not find" warnings for cross-references
- [x] Task 3: Validate with `docvet check --all` (AC: 4)
  - [x] Run `docvet check --all`
  - [x] Verify zero `missing-cross-references` findings
- [x] Task 4: Visual verification of rendered links (AC: 2)
  - [x] Build site and serve via `python3 -m http.server` on `site/` directory
  - [x] Verify See Also entries render as clickable code-formatted links
  - [x] Verify clicking a link navigates to the correct module's API reference page
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- NOTE: This story modifies docstrings only — testing is via mkdocs build, docvet check, and visual verification, not new pytest tests -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Manual inspection: all 12 files converted, 27 entries total | PASS |
| AC2 | Visual verification via built site (reviewer confirmed: links clickable, navigation works) | PASS |
| AC3 | `mkdocs build --strict` — zero cross-reference warnings | PASS |
| AC4 | `docvet check --all` — zero `missing-cross-references` findings | PASS |
| AC5 | `uv run pytest` — 743 tests pass, zero failures | PASS |

## Dev Notes

### Conversion Pattern

Each See Also entry follows this exact transformation:

**Before (plain backtick — renders as inline code, NOT a link):**
```
See Also:
    `docvet.checks`: Check modules and the Finding dataclass.
```

**After (bracket cross-reference — renders as clickable code-formatted link):**
```
See Also:
    [`docvet.checks`][]: Check modules and the Finding dataclass.
```

The pattern is: wrap the existing `` `module.name` `` in brackets and append `[]` → `` [`module.name`][] ``

### What to Convert vs What to Leave Alone

- **CONVERT**: The leading backtick module reference on each See Also line (e.g., `` `docvet.checks` `` → `` [`docvet.checks`][] ``)
- **DO NOT CONVERT**: Double-backtick inline code in descriptions (e.g., `` ``EnrichmentConfig`` ``, `` ``Finding`` ``, `` ``__init__.py`` ``). These are descriptive text, not cross-references.

### Why This Works

1. **autorefs v1.4.4** (installed) resolves `[identifier][]` bracket syntax into clickable links
2. **`pymdownx.inlinehilite`** (enabled at `mkdocs.yml:132`) is required for `` [`code`][] `` syntax — confirmed enabled
3. **`signature_crossrefs: true`** (added in Story 15.1) enables autorefs in signatures, but See Also resolution uses the base autorefs Markdown extension which processes all page content
4. **gen_ref_pages.py** generates `::: module.name` directives for all non-private modules — every referenced module has a page in the docs

### Cross-Reference Resolution Verification

All 27 See Also references target these modules — all are generated by gen_ref_pages.py:

| Target Module | Generated Page | Referenced By |
|---------------|---------------|---------------|
| `docvet.checks` | `reference/docvet/checks/index.md` | `__init__`, cli, config, discovery, reporting, _finding, enrichment, freshness, coverage, griffe_compat |
| `docvet.cli` | `reference/docvet/cli.md` | `__init__`, config, discovery, reporting |
| `docvet.config` | `reference/docvet/config.md` | cli, enrichment, freshness, coverage, griffe_compat |
| `docvet.discovery` | `reference/docvet/discovery.md` | cli |
| `docvet.ast_utils` | `reference/docvet/ast_utils.md` | enrichment |
| `docvet.checks.enrichment` | `reference/docvet/checks/enrichment.md` | ast_utils, checks/__init__ |
| `docvet.checks.freshness` | `reference/docvet/checks/freshness.md` | ast_utils, checks/__init__ |
| `docvet.checks.coverage` | `reference/docvet/checks/coverage.md` | checks/__init__ |
| `docvet.checks.griffe_compat` | `reference/docvet/checks/griffe_compat.md` | checks/__init__ |

### Enrichment Rule Compatibility

The `_XREF_MD_LINK` pattern at `enrichment.py:67` is `r"\[[^\]]+\]\["` — this matches the `[...][ ` portion of `` [`docvet.checks`][] ``, so bracket syntax satisfies the existing `missing-cross-references` rule (AC4). No rule changes needed in this story.

### Private Module Note

`_finding.py` starts with `_` and is skipped by gen_ref_pages.py (line 49-50). Its See Also references `docvet.checks` which IS a generated page. Cross-references FROM `_finding.py` still appear in the rendered docs IF the module is somehow included, but since it's private, its API reference page is not generated. Update it anyway for consistency — the `Finding` class is re-exported via `docvet.checks.__init__`.

### Previous Story Intelligence (15.1)

- Story 15.1 added the mkdocstrings handler configuration that enables cross-reference resolution (inventories, signature_crossrefs, etc.)
- `mkdocs build --strict` passes with zero warnings on the current codebase
- Visual verification was done via `python3 -m http.server` serving the built `site/` directory (dev server has issues with gen-files plugin)
- All quality gates pass: ruff, format, ty, pytest (743), docvet, interrogate (100%)

### Project Structure Notes

- All 12 files are in `src/docvet/` — no files outside this directory
- All files use `from __future__ import annotations` at top
- Module docstrings are at the very top of each file (lines 1-N), before imports
- See Also is the last section in each module docstring

### References

- [Source: _bmad-output/planning-artifacts/epics-docs-quality.md — Story 15.2]
- [Source: mkdocs.yml — mkdocstrings handler config (Story 15.1)]
- [Source: scripts/gen_ref_pages.py — API reference page generation]
- [Source: src/docvet/checks/enrichment.py:66-67 — _XREF_BACKTICK and _XREF_MD_LINK patterns]
- [Source: src/docvet/checks/enrichment.py:1178-1179 — cross-reference pass condition]
- [Source: CLAUDE.md — code style, build commands, project structure]

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 743 passed, zero failures
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100% (no new symbols added)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — zero errors encountered.

### Completion Notes List

- All 27 See Also entries across 12 files converted from plain backtick to bracket cross-reference syntax
- `mkdocs build --strict` passes with zero cross-reference warnings
- `docvet check --all` produces zero findings
- All quality gates pass (ruff, format, ty, pytest 743/743)
- Visual verification (AC2/Task 4) deferred to code review

### Change Log

| File | Change |
|------|--------|
| `src/docvet/__init__.py` | 2 See Also entries converted |
| `src/docvet/cli.py` | 3 See Also entries converted |
| `src/docvet/config.py` | 2 See Also entries converted |
| `src/docvet/discovery.py` | 2 See Also entries converted |
| `src/docvet/ast_utils.py` | 2 See Also entries converted |
| `src/docvet/reporting.py` | 2 See Also entries converted |
| `src/docvet/checks/__init__.py` | 4 See Also entries converted |
| `src/docvet/checks/_finding.py` | 1 See Also entry converted |
| `src/docvet/checks/enrichment.py` | 3 See Also entries converted |
| `src/docvet/checks/freshness.py` | 2 See Also entries converted |
| `src/docvet/checks/coverage.py` | 2 See Also entries converted |
| `src/docvet/checks/griffe_compat.py` | 2 See Also entries converted |

### File List

- `src/docvet/__init__.py`
- `src/docvet/cli.py`
- `src/docvet/config.py`
- `src/docvet/discovery.py`
- `src/docvet/ast_utils.py`
- `src/docvet/reporting.py`
- `src/docvet/checks/__init__.py`
- `src/docvet/checks/_finding.py`
- `src/docvet/checks/enrichment.py`
- `src/docvet/checks/freshness.py`
- `src/docvet/checks/coverage.py`
- `src/docvet/checks/griffe_compat.py`

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review)

### Outcome

PASS — all ACs implemented, all quality gates green, visual verification confirmed during review.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| R1 | MEDIUM | Interrogate gate marked skip but passes 100% | Fixed: marked `[x]` with result |
| R2 | LOW | AC2 still PENDING in AC-to-Test table | Fixed: updated to PASS |
| R3 | LOW | Task 4 subtasks unchecked after reviewer verified | Fixed: marked `[x]` |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
