# Story 26.2: Add Editor Integration Page

Status: review
Branch: `feat/docs-26-2-editor-integration-page`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/212

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer setting up docvet in their editor**,
I want a docs page explaining LSP server configuration and Claude Code plugin installation,
so that I can get real-time docstring diagnostics without reading source code.

## Acceptance Criteria

1. **Given** the docs site **When** a user navigates to the Editor Integration page **Then** the page documents the `docvet lsp` command, which checks run (enrichment, coverage, griffe — not freshness), and how to configure in any LSP-capable editor
2. **Given** the Editor Integration page **When** a user reads the Claude Code plugin section **Then** the install command (`claude plugin install github:Alberto-Codes/docvet`), prerequisites (`pip install docvet[lsp]`), and expected diagnostics are documented
3. **Given** the Editor Integration page **When** a user reads the severity mapping section **Then** the mapping is documented: required rules -> Warning, recommended rules -> Hint
4. **Given** the Editor Integration page **When** a user looks for VS Code support **Then** a reference to issue #160 (future) is included as a planned enhancement
5. **Given** the updated docs site **When** `mkdocs build --strict` is executed **Then** the build succeeds with zero warnings

## Tasks / Subtasks

- [x] Task 1: Create `docs/site/editor-integration.md` page (AC: 1, 2, 3, 4)
  - [x] 1.1: Write LSP Server section — `docvet lsp` command, prerequisite (`pip install docvet[lsp]`), checks run (enrichment, coverage, griffe — NOT freshness), and generic LSP client configuration example
  - [x] 1.2: Write Claude Code Plugin section — install command, prerequisites, expected diagnostics behavior
  - [x] 1.3: Write Severity Mapping section — required rules -> Warning, recommended rules -> Hint, with 2-3 representative examples (link to Rules reference for full list — avoid embedding a 19-row table that goes stale)
  - [x] 1.4: Write VS Code section — reference issue #160 as planned enhancement, current workaround via generic LSP
  - [x] 1.5: Write Neovim section — example configuration using `vim.lsp.start` or `nvim-lspconfig`
- [x] Task 2: Add page to `mkdocs.yml` nav (AC: 5)
  - [x] 2.1: Add `Editor Integration: editor-integration.md` entry to nav — position after "CI Integration" and before "AI Agent Integration"
- [x] Task 3: Add cross-link from existing AI Integration page (AC: 1)
  - [x] 3.1: Add a note/link in `docs/site/ai-integration.md` pointing to the new Editor Integration page for LSP/plugin setup details
- [x] Task 4: Verify docs build (AC: 5)
  - [x] 4.1: Run `mkdocs build --strict` — zero warnings

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: page contains LSP Server section with `docvet lsp` command, checks table (enrichment/coverage/griffe, no freshness), Other Editors table with generic config | PASS |
| 2 | Manual: page contains Claude Code section with install command, prerequisites, verification example | PASS |
| 3 | Manual: page contains Severity Mapping table (required -> Warning, recommended -> Hint) with representative examples | PASS |
| 4 | Manual: page contains VS Code section referencing issue #160 as planned enhancement | PASS |
| 5 | `mkdocs build --strict` — zero warnings, build succeeds | PASS |

## Dev Notes

- **Scope:** This is a docs-only story. Create one new Markdown page, update `mkdocs.yml` nav, and add a cross-link from `ai-integration.md`. No code changes, no new tests, no new dependencies.
- **Page structure guidance (Party Mode consensus):**
  - Start with a **quick-start block** at the top ("Install `docvet[lsp]`, pick your editor below") before diving into per-editor sections — follows the pattern established in `ci-integration.md`
  - For severity mapping, show 2-3 representative examples and **link to the Rules reference** rather than embedding a full 19-row table that will go stale when rules are added
  - Neovim section (Task 1.5) is a bonus example under AC 1's "any LSP-capable editor" umbrella — if it causes friction, a generic LSP client JSON config is sufficient
  - Reference/adapt content from `.claude-plugin/README.md` rather than rewriting from scratch — keep it DRY
- **Source:** GitHub Issue #186 — Epic 24 shipped the LSP server (24.1) and Claude Code plugin (24.2) but the docs site has no page for either.
- **Quality gate:** `mkdocs build --strict` is sufficient for docs-only stories (established in Story 26.1).

### Key Technical Details for Content

**LSP Server (`src/docvet/lsp.py`):**
- Command: `docvet lsp` — starts stdio-based LSP server
- Prerequisite: `pip install docvet[lsp]` (installs `pygls`)
- Checks run: enrichment (10 rules), coverage (1 rule), griffe (3 rules) — **freshness excluded** because it requires git context unavailable in single-file LSP mode
- Severity mapping:
  - `"required"` category rules -> `DiagnosticSeverity.Warning`
  - `"recommended"` category rules -> `DiagnosticSeverity.Hint`
- Events: `textDocument/didOpen` and `textDocument/didSave` trigger diagnostics
- Text document sync: `TextDocumentSyncKind.Full`
- Each diagnostic includes `codeDescription.href` linking to `https://alberto-codes.github.io/docvet/rules/{rule-id}/`
- Configuration loaded from `[tool.docvet]` in `pyproject.toml` on startup
- Graceful error if pygls not installed: `"LSP server requires pygls. Install with: pip install docvet[lsp]"`

**Claude Code Plugin (`.claude-plugin/`):**
- Plugin name: `docvet-lsp`
- Install: `claude plugin install github:Alberto-Codes/docvet`
- Prerequisites: `pip install docvet[lsp]`
- LSP config in `.lsp.json`: command `docvet`, args `["lsp"]`, file extension `.py` -> language `python`, max restarts 3
- Plugin manifest in `.claude-plugin/plugin.json`
- Plugin docs in `.claude-plugin/README.md` (can reference/adapt content from here)

**VS Code (Issue #160):**
- Future enhancement — VS Code extension with diagnostics in Problems panel + Language Model Tools API for Copilot agent mode
- Options discussed: thin LSP wrapper (Option A), subprocess-based (Option B), or both (Option C)
- For now, VS Code users can use the generic LSP client approach

**Current mkdocs.yml nav structure (relevant section):**
```
nav:
  - Getting Started: index.md
  - CI Integration: ci-integration.md
  - AI Agent Integration: ai-integration.md   # <-- Editor Integration goes BEFORE this
  - Checks: ...
```

**New nav entry position:** After "CI Integration", before "AI Agent Integration":
```
  - CI Integration: ci-integration.md
  - Editor Integration: editor-integration.md   # NEW
  - AI Agent Integration: ai-integration.md
```

### Project Structure Notes

- New file: `docs/site/editor-integration.md`
- Modified: `mkdocs.yml` (nav entry)
- Modified: `docs/site/ai-integration.md` (cross-link)
- No structural conflicts — standard docs site addition pattern

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 26.2]
- [Source: GitHub Issue #186 — Add Editor Integration page]
- [Source: GitHub Issue #160 — VS Code extension (future)]
- [Source: src/docvet/lsp.py — LSP server implementation]
- [Source: .claude-plugin/plugin.json — Claude Code plugin manifest]
- [Source: .claude-plugin/README.md — Plugin documentation]
- [Source: .lsp.json — LSP server configuration]
- [Source: docs/rules.yml — Rule catalog with categories for severity mapping]

### Documentation Impact

- Pages: docs/site/editor-integration.md (NEW), docs/site/ai-integration.md (cross-link update)
- Nature of update: Create new Editor Integration page documenting LSP server setup, Claude Code plugin installation, severity mapping, and VS Code future plans. Add cross-link from AI Agent Integration page.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
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

- Created `docs/site/editor-integration.md` with 7 sections: Quick Start, LSP Server (checks table, severity mapping, configuration, documentation links), Claude Code (install, verify, uninstall), Neovim (nvim-lspconfig + manual vim.lsp.start), Other Editors (generic settings table), VS Code (issue #160 reference)
- Added nav entry to `mkdocs.yml` between CI Integration and AI Agent Integration
- Added admonition cross-link in `ai-integration.md` pointing to the new page
- All 7 quality gates pass: ruff, format, ty, pytest (971), docvet, interrogate (100%), mkdocs build --strict

### Change Log

- 2026-02-28: Created Editor Integration docs page with LSP server, Claude Code plugin, Neovim, generic editor, and VS Code sections. Updated mkdocs.yml nav and ai-integration.md cross-link.

### File List

- docs/site/editor-integration.md (NEW — Editor Integration docs page)
- mkdocs.yml (modified — added nav entry)
- docs/site/ai-integration.md (modified — added cross-link admonition)

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
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
