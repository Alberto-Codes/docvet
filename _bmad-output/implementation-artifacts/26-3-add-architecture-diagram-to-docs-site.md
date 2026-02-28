# Story 26.3: Add Architecture Diagram to Docs Site

Status: done
Branch: `feat/docs-26-3-architecture-diagram`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/214

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **docvet contributor or evaluator**,
I want a Mermaid architecture diagram on the docs site showing the system structure,
so that I can quickly understand how the modules, checks, and CLI fit together.

## Acceptance Criteria

1. **Given** the docs site **When** a user navigates to the Architecture page **Then** one Mermaid flowchart is rendered showing both entry points (CLI and LSP) converging on the shared checks layer, with the CLI path continuing through reporting to output
2. **Given** the Mermaid diagram source **When** inspected in the repository **Then** it lives in `docs/site/architecture.md` (not generated externally)
3. **Given** the diagram **When** rendered on the published docs site **Then** it renders correctly as an SVG via mkdocs-material's built-in Mermaid support (not as a code block)
4. **Given** the updated docs site **When** `mkdocs build --strict` is executed **Then** the build succeeds with zero warnings
5. **Given** the project's Mermaid guidelines (`.claude/rules/mermaid.md`) **When** the diagram is reviewed **Then** it follows the guidelines: standard flowchart syntax (no C4 native syntax), `<br>` for line breaks, under 20 nodes, meaningful shapes

## Tasks / Subtasks

- [x] Task 1: Enable Mermaid rendering in mkdocs.yml (AC: 3)
  - [x] 1.1: Replace the bare `- pymdownx.superfences` entry with the version including `custom_fences` — name `mermaid`, class `mermaid`, format `pymdownx.superfences.fence_code_format`
- [x] Task 2: Create architecture docs page with Mermaid diagram (AC: 1, 2, 5)
  - [x] 2.1: Create `docs/site/architecture.md` with a `flowchart TD` diagram showing: two entry points (CLI, LSP) converging on a checks subgraph (enrichment, freshness, coverage, griffe), CLI path flowing through config → discovery before checks and through reporting → output after checks, LSP path going directly to checks and returning diagnostics
  - [x] 2.2: Add an intro paragraph framing the dual-entry-point design: "Whether you run docvet from the command line or your editor, the same checks analyze your code"
  - [x] 2.3: Add a module-purpose table below the diagram mapping each source module to its role (see Prescribed Diagram Content below)
  - [x] 2.4: Add a contributor callout: "To add a new check, create a module in `src/docvet/checks/` and register it in `cli.py`"
- [x] Task 3: Add page to mkdocs.yml nav (AC: 4)
  - [x] 3.1: Add `Architecture: architecture.md` entry to nav — position after Configuration, before CLI Reference
- [x] Task 4: Verify docs build and rendering (AC: 3, 4)
  - [x] 4.1: Run `mkdocs build --strict` — zero warnings (note: this validates markdown, NOT Mermaid rendering)
  - [x] 4.2: Run `mkdocs serve`, open in browser, confirm diagram renders as SVG in both light and dark modes (not a code block or Mermaid error box). Document confirmation in Completion Notes.

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: architecture page contains flowchart TD diagram with CLI + LSP entry points, checks subgraph (4 checks), reporting + diagnostics outputs | PASS |
| 2 | Manual: diagram source lives in `docs/site/architecture.md` — committed to repo, not generated | PASS |
| 3 | Manual: built HTML contains `<pre class="mermaid">` element; browser renders SVG diagram in both dark and light modes | PASS |
| 4 | `mkdocs build --strict` — zero warnings, build succeeds | PASS |
| 5 | Manual: `flowchart TD` syntax, no C4, `<br>` not used (no multi-line labels needed), 12 nodes (under 20), rounded rectangles for I/O, rectangles for processing, subgraph for checks | PASS |

## Dev Notes

- **Scope:** Docs-only story. One new Markdown page, one `mkdocs.yml` update (nav + superfences config). No code changes, no new tests, no new dependencies.
- **Quality gate:** `mkdocs build --strict` is the required build gate for docs-only stories (established in Story 26.1). Note: `mkdocs build --strict` does NOT validate that Mermaid renders correctly — a syntax error in the Mermaid block produces an error box in the browser while the build still passes. Manual browser verification (Task 4.2) is required.
- **Proof-of-concept scope** (Issue #190) — one diagram. Not exhaustive.

### Critical: Mermaid Rendering Requires Config Change

The current `mkdocs.yml` has `pymdownx.superfences` as a bare entry without `custom_fences`. Without `custom_fences`, ` ```mermaid ` blocks render as syntax-highlighted code, not diagrams.

**Required change** — replace `- pymdownx.superfences` with:

```yaml
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

No additional JS, CSS, or plugins needed — the material theme includes Mermaid.js natively.

### Prescribed Diagram Content

The diagram must show the **dual-entry-point architecture** — this is the most architecturally significant thing to communicate:

```
CLI (cli.py) ──→ Config ──→ Discovery ──→ ┐
                                           ├──→ Checks (shared) ──→ Reporting ──→ Output
LSP (lsp.py) ─────────────────────────────→ ┘                  └──→ Diagnostics (LSP)
```

**Prescribed nodes** (target ~12-15 nodes, under 20 max):

| Node | Shape | Label |
|------|-------|-------|
| CLI entry | Rounded rectangle | CLI |
| LSP entry | Rounded rectangle | LSP Server |
| Config | Rectangle | Configuration |
| Discovery | Rectangle | File Discovery |
| Checks subgraph | Subgraph box | Checks |
| Enrichment | Rectangle (inside subgraph) | Enrichment |
| Freshness | Rectangle (inside subgraph) | Freshness |
| Coverage | Rectangle (inside subgraph) | Coverage |
| Griffe | Rectangle (inside subgraph) | Griffe |
| Reporting | Rectangle | Reporting |
| CLI output | Rounded rectangle | Terminal / File |
| LSP output | Rounded rectangle | Editor Diagnostics |

**Visual direction:**
- Use `flowchart TD` — vertical flow reads naturally as "input in, output out"
- Use a `subgraph` to visually group the four checks — creates a clear "check layer"
- **Label economy**: use concept names ("CLI", "Enrichment"), NOT filenames ("cli.py", "enrichment.py") — filenames belong in the module table below the diagram
- Do NOT use diamonds — there are no user-facing decisions in this pipeline; check selection is config-driven

**Module-purpose table** (place below the diagram):

| Module | Purpose |
|--------|---------|
| `cli.py` | Typer CLI — config loading, file discovery, check dispatch, output |
| `config.py` | Reads `[tool.docvet]` from pyproject.toml |
| `discovery.py` | Finds target files via git diff, staged, --all, or positional args |
| `checks/enrichment.py` | Missing sections detection — 10 rules (AST analysis) |
| `checks/freshness.py` | Stale docstring detection — 5 rules (git diff + git blame) |
| `checks/coverage.py` | Missing `__init__.py` detection — 1 rule (directory scan) |
| `checks/griffe_compat.py` | Griffe parser warning capture — 3 rules |
| `reporting.py` | Formats findings as terminal, markdown, or JSON output |
| `lsp.py` | LSP server — reuses checks for real-time editor diagnostics |

### Anti-Patterns (Do NOT)

- Do NOT include `ast_utils.py`, `_finding.py`, or `config.py` as pipeline nodes in the diagram — they are internal utilities, not pipeline stages
- Do NOT install `mkdocs-mermaid2` or add any `extra_javascript` for Mermaid — the material theme handles this natively via `custom_fences`
- Do NOT use C4 native syntax (`C4Context`, `C4Container`) — hardcoded CSS doesn't respond to theme colors
- Do NOT put filenames in diagram node labels — use concept names; filenames go in the module table

### Diagram Placement

The nav entry goes after "Configuration" and before "CLI Reference" — users get all "how to use it" content first, Architecture sits in the "how it works" section:

```
nav:
  ...
  - Configuration: configuration.md
  - Architecture: architecture.md      # NEW
  - CLI Reference: cli-reference.md
  ...
```

### Mermaid Guidelines

Source of truth: `.claude/rules/mermaid.md` (has `paths:` frontmatter that auto-triggers on `*architecture*` files). The `.github/instructions/mermaid.instructions.md` file is for GitHub Copilot — ignore it.

- `flowchart TD` — standard syntax only
- `<br>` for line breaks in double-quoted labels, never `\n`
- Under 20 nodes
- Clarity over completeness

### Previous Story Intelligence (26.2)

- Docs-only stories follow the same pattern: create `.md` file, update `mkdocs.yml` nav
- Story 26.2 party-mode review caught misleading link text (M1) and overclaiming "zero configuration" (M2) — review diagram labels and surrounding prose for accuracy
- No code changes means quality gates (ruff, ty, pytest, docvet, interrogate) pass unchanged — run them to confirm no regressions

### Project Structure Notes

- New file: `docs/site/architecture.md`
- Modified: `mkdocs.yml` (nav entry + superfences custom_fences config)
- No structural conflicts — standard docs site addition pattern

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 26.3]
- [Source: GitHub Issue #190 — Mermaid architecture diagram]
- [Source: .claude/rules/mermaid.md — Diagram guidelines (source of truth)]
- [Source: mkdocs.yml — Current site config (missing custom_fences)]
- [Source: src/docvet/ — Module layout for diagram content]
- [Source: squidfunk.github.io/mkdocs-material/reference/diagrams/ — Official Mermaid setup docs]

### Documentation Impact

- Pages: docs/site/architecture.md (NEW)
- Nature of update: Create new Architecture page with Mermaid diagram showing dual-entry-point architecture (CLI + LSP converging on shared checks). Update mkdocs.yml superfences config to enable Mermaid rendering and add nav entry.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues (44 files already formatted)
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all 971 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100% (minimum 95%)
- [x] `mkdocs build --strict` — docs site builds cleanly (docs-only story gate)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — docs-only story, no debugging needed.

### Completion Notes List

- Replaced bare `pymdownx.superfences` with `custom_fences` config for Mermaid rendering in `mkdocs.yml`
- Created `docs/site/architecture.md` with `flowchart TD` Mermaid diagram showing dual-entry-point architecture: CLI path (CLI → Configuration → File Discovery → Checks → Reporting → Terminal/File) and LSP path (LSP Server → Checks → Editor Diagnostics)
- Diagram uses 12 nodes (under 20 limit), subgraph for 4 checks, rounded rectangles for entry/output, standard rectangles for processing
- Added prose: intro paragraph, CLI/LSP path descriptions, coverage directory-level admonition, module-purpose table (9 modules), contributor callout
- Added nav entry after Configuration, before CLI Reference
- `mkdocs build --strict` passes with zero warnings
- Verified Mermaid renders as SVG in browser — confirmed in both dark mode (slate scheme) and light mode (default scheme)
- All 7 quality gates pass: ruff, format, ty, 971 tests, docvet, interrogate 100%, mkdocs build

### Change Log

- 2026-02-28: Created Architecture docs page with Mermaid check pipeline diagram showing dual-entry-point design (CLI + LSP). Enabled Mermaid rendering via superfences custom_fences config. Added nav entry.
- 2026-02-28: Code review — fixed LSP paragraph accuracy (M1: listed 3 checks explicitly, explained freshness exclusion) and added LSP registration to contributor callout (L1). Dismissed L2 (edge labels) via party-mode consensus.

### File List

- docs/site/architecture.md (NEW — Architecture page with Mermaid diagram)
- mkdocs.yml (modified — added superfences custom_fences for Mermaid + Architecture nav entry)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review + party-mode consensus)

### Outcome

Approved with fixes applied

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | LSP paragraph says "runs the same checks" — LSP excludes freshness (requires git context) | Fixed: rewrote LSP paragraph to list 3 checks explicitly and explain freshness exclusion |
| L1 | LOW | Contributing callout omits LSP `_check_file` registration | Fixed: added sentence about `lsp.py` registration |
| L2 | LOW | Diagram output branches lack edge labels | Dismissed: intentional "clarity over completeness" per Mermaid guidelines (party-mode consensus) |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
