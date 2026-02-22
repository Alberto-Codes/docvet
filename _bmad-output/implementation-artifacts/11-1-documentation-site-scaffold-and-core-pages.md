# Story 11.1: Documentation Site Scaffold and Core Pages

Status: review
Branch: `feat/docs-11-1-scaffold-core-pages`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer who just installed docvet,
I want a documentation site with Getting Started and CLI Reference pages,
so that I can learn how to use the tool without reading source code.

## Acceptance Criteria

1. **Given** no `mkdocs.yml` or documentation site exists, **when** the docs site is scaffolded, **then** `mkdocs.yml` exists with mkdocs-material theme, navigation, and search plugin enabled
2. **Given** the scaffolded site, **then** a Getting Started page exists with installation instructions (`pip install docvet`, `pip install docvet[griffe]`), quickstart command, and brief overview of the four checks
3. **Given** the scaffolded site, **then** a CLI Reference page exists documenting all 5 subcommands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) and all global options (`--format`, `--output`, `--verbose`, `--staged`, `--all`, `--files`)
4. **Given** the scaffolded site, **then** `mkdocs serve` builds the site without errors
5. **Given** the scaffolded site, **then** client-side search returns results for "enrichment", "freshness", "coverage", "griffe"

## Tasks / Subtasks

- [x] Task 1: Add mkdocs dependencies to pyproject.toml (AC: #1)
  - [x] 1.1 Add `docs` optional dependency group: `mkdocs>=1.6`, `mkdocs-material>=9.6`
  - [x] 1.2 Run `uv sync --extra docs` to install
- [x] Task 2: Create mkdocs.yml configuration (AC: #1, #4, #5)
  - [x] 2.1 Create `mkdocs.yml` at project root with site_name, theme (material), plugins (search), nav structure
  - [x] 2.2 Configure material theme palette, font, features (navigation.tabs, navigation.sections, search.highlight)
  - [x] 2.3 Nav must only list pages that exist — `mkdocs build --strict` fails on missing page refs. Stories 11.2/11.3 extend nav when they add pages.
  - [x] 2.4 Verify `mkdocs serve` runs cleanly
- [x] Task 3: Create Getting Started page (AC: #2)
  - [x] 3.1 Create `docs/site/index.md` (serves as home page / Getting Started)
  - [x] 3.2 Write installation section: `pip install docvet` and `pip install docvet[griffe]`
  - [x] 3.3 Write quickstart: `docvet check --all` with realistic terminal output example showing what the user will actually see (findings format, summary line). Show, don't tell.
  - [x] 3.4 Write brief overview of 4 checks (enrichment, freshness, coverage, griffe) with 1-2 sentence descriptions
- [x] Task 4: Create CLI Reference page (AC: #3)
  - [x] 4.1 Create `docs/site/cli-reference.md`
  - [x] 4.2 Document 5 subcommands: `check`, `enrichment`, `freshness`, `coverage`, `griffe`
  - [x] 4.3 Document global options: `--format`, `--output`, `--verbose`
  - [x] 4.4 Document discovery flags: `--staged`, `--all`, `--files` (mutually exclusive, default is git diff)
  - [x] 4.5 Document check-specific options: `freshness --mode drift`
  - [x] 4.6 Cross-check every flag against actual `docvet --help` output (NFR58)
- [x] Task 5: Verify build and search (AC: #4, #5)
  - [x] 5.1 Run `mkdocs build --strict` and confirm zero warnings
  - [x] 5.2 Run `mkdocs serve` and manually verify all pages render
  - [x] 5.3 Verify search: inspect `search_index.json` in build output for "enrichment", "freshness", "coverage", "griffe" entries

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | `mkdocs.yml` exists with `theme: material`, `plugins: [search]`, nav; `mkdocs build --strict` passes | PASS |
| #2 | `docs/site/index.md` contains `pip install docvet`, `pip install docvet[griffe]`, quickstart commands, 4-check overview sections | PASS |
| #3 | `docs/site/cli-reference.md` lists 5 subcommands (check, enrichment, freshness, coverage, griffe), global options (--format, --output, --verbose, --config, --version), discovery flags (--staged, --all, --files), check-specific (--mode) | PASS |
| #4 | `mkdocs build --strict` exits 0 with zero build warnings | PASS |
| #5 | `search_index.json` contains entries for "enrichment" (5 pages), "freshness" (5 pages), "coverage" (4 pages), "griffe" (4 pages) | PASS |

## Dev Notes

### Architecture Decisions

- **mkdocs-material (free tier)** — architecture decision from v1.0 Polish phase. No paid features needed.
- **Separate docs directory (recommended):** Consider using a subdirectory (e.g. `docs/site/`) as `docs_dir` to keep user-facing pages separate from existing internal design docs in `docs/` (product-vision.md, development-guide.md, architecture.md, etc. are NOT part of the public site). The dev may choose any directory structure as long as internal docs are not served.
- **No mkdocstrings yet** — API reference auto-generation (mkdocstrings + mkdocs-gen-files) is NOT in scope for this story. That can be added later if desired.
- **No Jinja macros yet** — `mkdocs-macros` and `docs/rules.yml` catalog are for Story 11.3 (rule reference pages), not this story.

### Technical Stack for Docs

| Tool | Version | Purpose |
|------|---------|---------|
| mkdocs | >=1.6 | Static site generator |
| mkdocs-material | >=9.6 | Theme (search, navigation, responsive) |

Both added as optional `[docs]` dependency group — NOT runtime dependencies.

### File Structure

```
docvet/
├── mkdocs.yml                    # NEW - site configuration
├── docs/
│   ├── site/                     # NEW - user-facing docs (mkdocs docs_dir)
│   │   ├── index.md              # NEW - Getting Started (home page)
│   │   └── cli-reference.md      # NEW - CLI Reference
│   ├── product-vision.md         # EXISTING - internal (not served)
│   ├── development-guide.md      # EXISTING - internal (not served)
│   ├── architecture.md           # EXISTING - internal (not served)
│   └── ...                       # EXISTING - other internal docs
├── pyproject.toml                # MODIFIED - add [docs] optional deps
└── ...
```

### CLI Reference Data (Source of Truth)

Extract flags from actual `docvet --help` output. Do NOT copy from docs — always verify against CLI.

**5 Subcommands:**
| Command | Description |
|---------|-------------|
| `docvet check` | Run all checks on discovered files |
| `docvet enrichment` | Run enrichment (completeness) check only |
| `docvet freshness` | Run freshness (accuracy) check only |
| `docvet coverage` | Run coverage (visibility) check only |
| `docvet griffe` | Run griffe (rendering) check only |

**Global Options (precede subcommand):**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `terminal\|markdown` | `terminal` | Output format |
| `--output` | path | stdout | Write report to file |
| `--verbose` | flag | off | Verbose output with file count |

**Discovery Flags (mutually exclusive, follow subcommand):**
| Flag | Description |
|------|-------------|
| (default) | Files from `git diff` (unstaged changes) |
| `--staged` | Files from `git diff --cached` (staged changes) |
| `--all` | All Python files in project |
| `--files` | Specific files (repeatable: `--files a.py --files b.py`) |

**Check-Specific Options:**
| Flag | Command | Description |
|------|---------|-------------|
| `--mode drift` | `freshness` | Use git-blame drift mode (default: diff) |

### Getting Started Content Guide

**Installation section:**
```bash
pip install docvet           # Core (enrichment, freshness, coverage)
pip install docvet[griffe]   # With optional griffe rendering check
```

**Quickstart section:**
```bash
docvet check --all           # Check entire codebase
docvet check                 # Check only files with uncommitted changes
docvet check --staged        # Check only staged files (pre-commit)
```

Include a realistic terminal output block showing what the user will see, e.g.:
```
src/myapp/utils.py:42: missing-raises Function 'parse_config' raises ValueError but Raises section is missing [required]
src/myapp/models.py:15: missing-attributes Class 'User' has 3 undocumented attributes [required]

2 findings (2 required, 0 recommended)
```
Run `docvet check --all` against the docvet codebase itself (or craft a representative example) to get real output format.

**Four checks overview (1-2 sentences each):**
1. **Enrichment** (Layer 3: Completeness) — Detects missing docstring sections like Raises, Yields, Attributes, and Examples. 10 rules, AST-based.
2. **Freshness** (Layer 4: Accuracy) — Flags code changes without matching docstring updates. Diff mode (fast) and drift mode (git blame sweep). 5 rules.
3. **Coverage** (Layer 6: Visibility) — Finds missing `__init__.py` files that would make packages invisible to mkdocs. 1 rule.
4. **Griffe** (Layer 5: Rendering) — Captures griffe parser warnings that would break mkdocs-material rendering. 3 rules, optional dependency.

### Navigation Strategy

- **Minimal nav now, extend later.** Only list pages that exist in `mkdocs.yml` nav — `mkdocs build --strict` will fail on missing page references.
- Stories 11.2 and 11.3 will add Check pages, Configuration, and Rule Reference pages. They will extend the nav when those files are created.
- Do NOT create stub/placeholder files for future pages. Keep this story's scope to Getting Started + CLI Reference only.

### Project Structure Notes

- `mkdocs.yml` goes at project root (standard mkdocs convention)
- User-facing docs directory must be separate from existing internal design docs (`docs/product-vision.md`, `docs/architecture.md`, etc.)
- The `site/` build output directory should not be committed (add to `.gitignore` if not already)

### Quickstart UX

- The Getting Started page is the landing page — developers want to get running, not read a mission statement.
- **Show, don't tell:** Include a realistic terminal output example after `docvet check --all` so users see exactly what to expect (file:line format, findings, summary line with counts).
- Keep the "why docvet" pitch to one sentence max, then straight into install + run + see results. PRD validated: 73% of developers demand hands-on value in under 2 minutes.

### NFR Compliance

- **NFR57:** mkdocs-material handles responsive design (>=320px to 1920px) and fast loads natively
- **NFR58:** CLI Reference must match actual `docvet --help` output — run the CLI to verify, do not copy from documentation

### Previous Epic Learnings (Epic 10)

- Fifth consecutive zero-debug epic when spec quality is high
- GitHub Pages deployment infra is ready (GitHub Actions source)
- `uv_build` is the build system — docs deps go in optional group, NOT runtime
- Floating `v1` tag pattern established for versioned references

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 11, Story 11.1 lines 339-353]
- [Source: _bmad-output/planning-artifacts/architecture.md — v1.0 Polish & Publish, Docs Architecture section]
- [Source: _bmad-output/planning-artifacts/prd.md — FR121, FR122, NFR57, NFR58]
- [Source: CLAUDE.md — CLI commands, build system, dependencies]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered — zero-debug implementation.

### Completion Notes List

- Added `docs` optional dependency group (`mkdocs>=1.6`, `mkdocs-material>=9.6`) to `pyproject.toml`
- Created `mkdocs.yml` at project root with material theme (light/dark palette toggle), search plugin, tabbed navigation, code copy feature, and minimal nav (Getting Started + CLI Reference only)
- Used `docs/site/` as `docs_dir` to separate user-facing docs from internal design docs in `docs/`
- Created `docs/site/index.md` (Getting Started) with installation (tabbed pip commands), quickstart with three modes, realistic terminal output example, and 1-2 sentence overview of all 4 checks
- Created `docs/site/cli-reference.md` with all 5 subcommands, all global options (--verbose, --format, --output, --config, --version), mutually exclusive discovery flags, check-specific --mode option, exit codes, and usage examples
- Cross-checked all flags against actual `docvet --help` output per NFR58 — also discovered and documented `--config` and `--version` flags not listed in story spec
- Added `site/` to `.gitignore` to exclude mkdocs build output
- `mkdocs build --strict` passes with zero warnings; search index contains all 4 check terms across multiple pages
- 729 tests pass, 0 regressions; ruff lint and format checks clean

### File List

- `pyproject.toml` — MODIFIED (added `docs` optional dependency group)
- `mkdocs.yml` — NEW (site configuration)
- `docs/site/index.md` — NEW (Getting Started page)
- `docs/site/cli-reference.md` — NEW (CLI Reference page)
- `.gitignore` — MODIFIED (added `site/` exclusion)

### Change Log

- 2026-02-21: Scaffolded documentation site with mkdocs-material theme, Getting Started page, and CLI Reference page (Story 11.1)
