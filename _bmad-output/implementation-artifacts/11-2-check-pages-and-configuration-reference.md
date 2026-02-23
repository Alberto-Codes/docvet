# Story 11.2: Check Pages and Configuration Reference

Status: done
Branch: `feat/docs-11-2-check-pages-config-ref`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer configuring docvet for their team,
I want dedicated pages for each check type and a configuration reference,
so that I understand what each check does and how to customize it.

## Acceptance Criteria

1. **Given** the docs site scaffold from Story 11.1, **when** check pages and config reference are added, **then** an Enrichment Check page exists explaining the 10 enrichment rules, required vs recommended categories, and `[tool.docvet.enrichment]` config options
2. **Given** the docs site scaffold, **then** a Freshness Check page exists explaining diff mode vs drift mode, the 5 freshness rules, severity levels, and `[tool.docvet.freshness]` config options
3. **Given** the docs site scaffold, **then** a Coverage Check page exists explaining `missing-init` detection and `src-root` behavior
4. **Given** the docs site scaffold, **then** a Griffe Check page exists explaining the 3 griffe rules, optional dependency, and graceful skip behavior
5. **Given** the docs site scaffold, **then** a Configuration page exists documenting every `[tool.docvet]` key with its type, default value, and an example
6. **Given** the docs site scaffold, **then** CLI usage examples shown on check pages and the Configuration page match the actual `docvet --help` output (NFR58)
7. **Given** the docs site scaffold, **then** `mkdocs serve` builds without errors and all pages are navigable

## Tasks / Subtasks

- [x] Task 1: Create Enrichment Check page (AC: #1)
  - [x] 1.1 Create `docs/site/checks/enrichment.md` following the Check Page Template (see Dev Notes)
  - [x] 1.2 Write overview: Layer 3 completeness, AST-based, 10 rules across required/recommended categories
  - [x] 1.3 Document all 10 rules in a table: rule ID, category, applies-to, description
  - [x] 1.4 Include example terminal output showing a realistic enrichment finding
  - [x] 1.5 Document `[tool.docvet.enrichment]` config options: 9 booleans + 1 list, with defaults and examples
  - [x] 1.6 Include a TOML config example showing how to disable specific rules
- [x] Task 2: Create Freshness Check page (AC: #2)
  - [x] 2.1 Create `docs/site/checks/freshness.md` following the Check Page Template (see Dev Notes)
  - [x] 2.2 Write overview: Layer 4 accuracy, detects stale docstrings via git analysis
  - [x] 2.3 Explain diff mode (default, fast, maps git diff hunks to symbols) vs drift mode (git blame sweep, historical)
  - [x] 2.4 Document all 5 rules in a table: 3 diff-mode rules + 2 drift-mode rules with categories and severity mapping
  - [x] 2.5 Include example terminal output showing a realistic freshness finding (one per mode)
  - [x] 2.6 Document `[tool.docvet.freshness]` config: `drift-threshold` (int, default 30) and `age-threshold` (int, default 90)
  - [x] 2.7 Include example showing CLI usage for each mode: `docvet freshness --all` vs `docvet freshness --all --mode drift`
- [x] Task 3: Create Coverage Check page (AC: #3)
  - [x] 3.1 Create `docs/site/checks/coverage.md` following the Check Page Template (see Dev Notes)
  - [x] 3.2 Write overview: Layer 6 visibility, detects missing `__init__.py` files that make packages invisible to mkdocs
  - [x] 3.3 Document the single `missing-init` rule: required category, directory-level deduplication, affected file count
  - [x] 3.4 Include example terminal output showing a realistic coverage finding
  - [x] 3.5 Explain `src-root` behavior: auto-detects `src/` layout, configurable via `[tool.docvet]` `src-root` key (see `src-root` auto-detection note in Dev Notes)
  - [x] 3.6 Note: no check-specific configuration — this check has no `[tool.docvet.coverage]` section
- [x] Task 4: Create Griffe Check page (AC: #4)
  - [x] 4.1 Create `docs/site/checks/griffe.md` following the Check Page Template (see Dev Notes)
  - [x] 4.2 Write overview: Layer 5 rendering, captures griffe parser warnings that break mkdocs-material
  - [x] 4.3 Document all 3 rules: `griffe-unknown-param` (required), `griffe-missing-type` (recommended), `griffe-format-warning` (recommended)
  - [x] 4.4 Include example terminal output showing a realistic griffe finding
  - [x] 4.5 Explain optional dependency: `pip install docvet[griffe]`, graceful skip when not installed
  - [x] 4.6 Note: no check-specific configuration — this check has no `[tool.docvet.griffe]` section
- [x] Task 5: Create Configuration Reference page (AC: #5)
  - [x] 5.1 Create `docs/site/configuration.md`
  - [x] 5.2 Document top-level `[tool.docvet]` keys: `src-root`, `package-name`, `exclude`, `fail-on`, `warn-on` — include `fail-on`/`warn-on` precedence behavior (see Dev Notes)
  - [x] 5.3 Document `[tool.docvet.freshness]` subsection: `drift-threshold`, `age-threshold`
  - [x] 5.4 Document `[tool.docvet.enrichment]` subsection: all 10 keys
  - [x] 5.5 For each key: show type, default value, and a TOML example snippet
  - [x] 5.6 Include a complete `pyproject.toml` example showing all sections together
  - [x] 5.7 Note that `[tool.docvet]` is optional — missing section uses defaults, not error
- [x] Task 6: Update mkdocs.yml navigation and verify build (AC: #6, #7)
  - [x] 6.1 Add Checks section to `mkdocs.yml` nav with 4 check pages
  - [x] 6.2 Add Configuration page to nav
  - [x] 6.3 Run `mkdocs build --strict` and confirm zero warnings
  - [x] 6.4 Cross-check all CLI flags and options against actual `docvet --help` output (NFR58)
  - [x] 6.5 Verify all pages are navigable and search returns results for check names

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- All verifications are manual (docs-only story — no automated tests). -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Manual: enrichment.md has 10 rules table, required/recommended categories, config options | Pass |
| AC2 | Manual: freshness.md has diff/drift modes, 5 rules table, severity levels, config options | Pass |
| AC3 | Manual: coverage.md has missing-init rule, src-root behavior | Pass |
| AC4 | Manual: griffe.md has 3 rules, optional dependency admonition, graceful skip note | Pass |
| AC5 | Manual: configuration.md has all [tool.docvet] keys with type, default, example | Pass |
| AC6 | Manual: CLI flags cross-checked against `docvet --help` and all subcommand `--help` output | Pass |
| AC7 | Manual: `mkdocs build --strict` completes with zero errors, all pages navigable | Pass |

## Dev Notes

### Architecture Decisions

- **Docs directory structure**: Story 11.1 established `docs/site/` as `docs_dir`. Check pages go in `docs/site/checks/` subdirectory for clean organization.
- **mkdocs-material (free tier)** — no paid features (e.g., no `tags` plugin). All navigation is manual in `mkdocs.yml`.
- **No mkdocstrings** — pages are manually authored markdown, not auto-generated from source. This is intentional per story 11.1.
- **No Jinja macros** — `mkdocs-macros` and `docs/rules.yml` catalog are for Story 11.3 (rule reference pages), not this story.
- **Cross-referencing forward**: Check pages should mention rule IDs but do NOT need to link to individual rule reference pages yet — those are created in Story 11.3. Use inline code formatting (backticks) for rule IDs.

### Check Page Template (Mandatory)

All four check pages MUST follow this consistent H2 structure. Do not invent per-page layouts.

```markdown
# <Check Name> Check

Brief overview paragraph: which quality layer, what it detects, how it works (AST/git/griffe).

## Rules

Table of all rules for this check: rule ID, category (required/recommended), applies-to, one-line description.

## Example Output

A realistic terminal output block showing what a finding from this check looks like. Use the `file:line: rule-id message [category]` format established in the Getting Started page. Generate by running `docvet <check> --all` against the docvet codebase or craft a representative example.

## Configuration

The `[tool.docvet.<check>]` config options with types, defaults, and a TOML example. If the check has no config section, use an admonition:

!!! info
    This check has no check-specific configuration.

## Usage

CLI usage examples for running this specific check (e.g., `docvet enrichment --all`). Include mode variants if applicable (freshness diff vs drift).
```

Each check page must be **independently useful** without the rule reference pages from Story 11.3. The rules table in each page is the user's primary reference until those pages exist.

### `fail-on` / `warn-on` Precedence Behavior

The Configuration page must document this interaction (source: `config.py` lines 499-506):

- If a check name appears in **both** `fail-on` and `warn-on`, docvet prints a warning to stderr and **`fail-on` wins** — the check is removed from `warn-on`.
- Example: setting `fail-on = ["enrichment"]` with the default `warn-on = ["freshness", "enrichment", "griffe", "coverage"]` results in `enrichment` being silently removed from `warn-on`.
- This is not an error — it's graceful deduplication with a diagnostic message.

### `src-root` Auto-Detection Heuristic

The Coverage Check page and Configuration page must both explain this behavior (source: `config.py:_resolve_src_root` lines 306-323):

- If `src-root` is **not set** in config and a `src/` directory exists at the project root, `src-root` defaults to `"src"`.
- If `src-root` is **not set** and no `src/` directory exists, it defaults to `"."` (project root).
- If `src-root` is **explicitly set**, the configured value is used as-is, no heuristic applied.

### Technical Requirements

**Source of truth for all documentation content:**

1. **Rule details** — extract from source code (`src/docvet/checks/*.py`), NOT from memory or prior docs
2. **Config keys** — extract from `src/docvet/config.py` (`_VALID_TOP_KEYS`, `_VALID_FRESHNESS_KEYS`, `_VALID_ENRICHMENT_KEYS`, dataclass defaults)
3. **CLI flags** — verify against actual `docvet --help` output (NFR58)
4. **DO NOT copy-paste** from the Getting Started page or CLI Reference — each page serves a different audience depth

**Config key naming**: TOML uses kebab-case (`require-raises`), Python uses snake_case (`require_raises`). Documentation should show the TOML kebab-case form since that's what users write.

### Rule Reference by Check Module

#### Enrichment (10 rules)

| Rule ID | Category | Applies To | What It Detects |
|---------|----------|-----------|-----------------|
| `missing-raises` | required | functions, methods | Function raises exceptions but has no Raises: section |
| `missing-yields` | required | functions, methods | Generator yields but has no Yields: section |
| `missing-receives` | required | functions, methods | Generator uses `.send()` but has no Receives: section |
| `missing-warns` | required | functions, methods | Function calls `warnings.warn()` but has no Warns: section |
| `missing-other-parameters` | recommended | functions, methods | Function accepts `**kwargs` but has no Other Parameters: section |
| `missing-attributes` | required | classes, modules | Class or `__init__.py` module has undocumented attributes |
| `missing-typed-attributes` | recommended | classes | Attributes: section entries lack typed format |
| `missing-examples` | recommended | classes, modules | Symbol kind in `require-examples` list lacks Examples: section |
| `missing-cross-references` | recommended | modules | `__init__.py` module missing See Also: section |
| `prefer-fenced-code-blocks` | recommended | any symbol | Examples: section uses doctest `>>>` instead of fenced code blocks |

#### Freshness (5 rules)

**Diff Mode (default):**

| Rule ID | Category | Severity | What It Detects |
|---------|----------|----------|-----------------|
| `stale-signature` | required | HIGH | Function signature changed, docstring not updated |
| `stale-body` | recommended | MEDIUM | Function body changed, docstring not updated |
| `stale-import` | recommended | LOW | Import changed, docstring not updated |

**Drift Mode (`--mode drift`):**

| Rule ID | Category | What It Detects |
|---------|----------|-----------------|
| `stale-drift` | recommended | Code modified more recently than docstring (exceeds `drift-threshold` days) |
| `stale-age` | recommended | Docstring untouched beyond `age-threshold` days |

#### Coverage (1 rule)

| Rule ID | Category | What It Detects |
|---------|----------|-----------------|
| `missing-init` | required | Directory in source tree lacks `__init__.py` — invisible to mkdocs |

#### Griffe (3 rules)

| Rule ID | Category | What It Detects |
|---------|----------|-----------------|
| `griffe-unknown-param` | required | Docstring documents parameter not in function signature |
| `griffe-missing-type` | recommended | Parameter/return lacks type annotation in docstring |
| `griffe-format-warning` | recommended | Docstring format issue that would break mkdocs rendering |

### Configuration Reference Data (Source of Truth)

**Top-level `[tool.docvet]` keys** (from `config.py:_VALID_TOP_KEYS`):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `src-root` | `str` | `"."` (auto-detects `src/`) | Source directory relative to project root |
| `package-name` | `str` | `null` (auto-detected) | Explicit package name override |
| `exclude` | `list[str]` | `["tests", "scripts"]` | Directory names to exclude from checks |
| `fail-on` | `list[str]` | `[]` | Check names that cause exit code 1 |
| `warn-on` | `list[str]` | `["freshness", "enrichment", "griffe", "coverage"]` | Check names reported without failing |

**`[tool.docvet.freshness]` keys** (from `config.py:_VALID_FRESHNESS_KEYS`):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `drift-threshold` | `int` | `30` | Max days code can be ahead of docstring before flagging drift |
| `age-threshold` | `int` | `90` | Max days docstring can go without any update |

**`[tool.docvet.enrichment]` keys** (from `config.py:_VALID_ENRICHMENT_KEYS`):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `require-raises` | `bool` | `true` | Require Raises: sections |
| `require-yields` | `bool` | `true` | Require Yields: sections |
| `require-receives` | `bool` | `true` | Require Receives: sections |
| `require-warns` | `bool` | `true` | Require Warns: sections |
| `require-other-parameters` | `bool` | `true` | Require Other Parameters: sections |
| `require-attributes` | `bool` | `true` | Require Attributes: sections |
| `require-typed-attributes` | `bool` | `true` | Require typed attribute format |
| `require-cross-references` | `bool` | `true` | Require See Also: in `__init__.py` modules |
| `prefer-fenced-code-blocks` | `bool` | `true` | Prefer fenced code blocks over doctest format |
| `require-examples` | `list[str]` | `["class", "protocol", "dataclass", "enum"]` | Symbol kinds requiring Examples: section |

**Valid check names** (for `fail-on` and `warn-on`): `enrichment`, `freshness`, `coverage`, `griffe`

**`[tool.docvet]` is optional** — if the section is missing entirely, all defaults apply. Invalid keys cause an error on stderr and exit code 1.

### File Structure

```
docs/site/
├── index.md              # EXISTING - Getting Started
├── cli-reference.md      # EXISTING - CLI Reference
├── configuration.md      # NEW - Configuration Reference
└── checks/
    ├── enrichment.md      # NEW - Enrichment Check page
    ├── freshness.md       # NEW - Freshness Check page
    ├── coverage.md        # NEW - Coverage Check page
    └── griffe.md          # NEW - Griffe Check page
```

### mkdocs.yml Navigation Update

The nav must be extended to include the new pages. Recommended structure:

```yaml
nav:
  - Getting Started: index.md
  - Checks:
    - Enrichment: checks/enrichment.md
    - Freshness: checks/freshness.md
    - Coverage: checks/coverage.md
    - Griffe: checks/griffe.md
  - Configuration: configuration.md
  - CLI Reference: cli-reference.md
```

Only list pages that exist — `mkdocs build --strict` fails on missing page refs. Story 11.3 will add a "Rules" nav section when rule reference pages are created.

### Previous Story Intelligence (11.1)

**Key learnings from story 11.1:**
- Zero-debug implementation — story spec quality was high
- Used `docs/site/` as `docs_dir` to separate from internal docs — this is established convention
- Cross-checked all CLI flags against actual `docvet --help` (NFR58) — discovered `--config` and `--version` flags not in original spec
- `mkdocs build --strict` catches missing page refs and broken nav — always run before declaring done
- Added `site/` to `.gitignore` — already handled
- mkdocs-material handles responsive design natively (NFR57)
- `mkdocs<2` pinned to avoid incompatible MkDocs 2.0 — this is already in pyproject.toml

**Files created by 11.1:**
- `mkdocs.yml` — site configuration (MODIFY nav in this story)
- `docs/site/index.md` — Getting Started page (DO NOT modify)
- `docs/site/cli-reference.md` — CLI Reference (DO NOT modify)
- `pyproject.toml` — added `docs` optional deps (DO NOT modify)

### NFR Compliance

- **NFR57:** mkdocs-material handles responsive design natively — no extra work needed
- **NFR58:** Every CLI flag in the docs site must match actual `docvet --help` output. Run the CLI and verify, do not copy from documentation or memory.

### Git Intelligence

Recent commits show:
- `f023955` — PR review fixes for accuracy (doc accuracy is critical)
- `5036891` — pinned `mkdocs<2` to avoid MkDocs 2.0 incompatibility
- `42d43d6` — the 11.1 scaffold commit (#67)

### Markdown Extensions Available

From `mkdocs.yml`, these extensions are available for use in check pages:
- `admonition` — for tip/warning/note callout boxes
- `pymdownx.details` — collapsible sections
- `pymdownx.superfences` — fenced code blocks
- `pymdownx.highlight` — syntax highlighting with line numbers
- `pymdownx.tabbed` — tabbed content (alternate_style)
- `toc` — table of contents with permalink anchors

Use admonitions for important notes (e.g., "Griffe is optional — install with `pip install docvet[griffe]`"). Use tabbed content if showing multiple config examples (e.g., "Minimal Config" vs "Full Config" tabs on the Configuration page using `pymdownx.tabbed`).

### Example Terminal Output Per Check

Each check page must include a realistic terminal output block showing what a finding looks like. Use the format established in the Getting Started page (`file:line: rule-id message [category]`). Either run the actual check against docvet's codebase or craft a representative example. Sample patterns:

**Enrichment:**
```
src/myapp/utils.py:42: missing-raises Function 'parse_config' raises ValueError but Raises section is missing [required]
```

**Freshness (diff mode):**
```
src/myapp/utils.py:42: stale-signature Function 'parse_config' signature changed but docstring not updated [required]
```

**Freshness (drift mode):**
```
src/myapp/utils.py:42: stale-drift Function 'parse_config' code modified 2026-01-15, docstring last modified 2025-11-02 (74 days drift) [recommended]
```

**Coverage:**
```
src/myapp/helpers:0: missing-init Directory 'helpers' lacks __init__.py (3 file(s) affected) [required]
```

**Griffe:**
```
src/myapp/utils.py:42: griffe-unknown-param Function 'parse_config' 'timeout' does not appear in the function signature [required]
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 11, Story 11.2 lines 355-371]
- [Source: src/docvet/config.py — DocvetConfig, EnrichmentConfig, FreshnessConfig dataclasses]
- [Source: src/docvet/checks/enrichment.py — 10 rule identifiers and categories]
- [Source: src/docvet/checks/freshness.py — 5 rule identifiers, diff/drift modes]
- [Source: src/docvet/checks/coverage.py — missing-init rule]
- [Source: src/docvet/checks/griffe_compat.py — 3 griffe rules]
- [Source: _bmad-output/implementation-artifacts/11-1-documentation-site-scaffold-and-core-pages.md — previous story learnings]
- [Source: CLAUDE.md — CLI commands, architecture overview]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered — zero-debug implementation.

### Completion Notes List

- Created 4 check pages following mandatory Check Page Template (H2 structure: Rules, Example Output, Configuration, Usage)
- Created Configuration Reference page with all [tool.docvet] keys, types, defaults, and examples
- All rule details extracted from source code (enrichment.py, freshness.py, coverage.py, griffe_compat.py)
- All config keys extracted from config.py (_VALID_TOP_KEYS, _VALID_FRESHNESS_KEYS, _VALID_ENRICHMENT_KEYS)
- CLI flags cross-checked against actual `docvet --help` and all subcommand help output (NFR58)
- Documented fail-on/warn-on precedence behavior from config.py lines 499-506
- Documented src-root auto-detection heuristic from config.py:_resolve_src_root lines 306-323
- Used admonitions for griffe optional dependency and checks with no config section
- Used tabbed content for Full/Minimal config examples on Configuration page
- mkdocs build --strict passes with zero errors
- Navigation updated with Checks section (4 pages) and Configuration page

### Change Log

- 2026-02-21: Created 4 check pages and configuration reference, updated mkdocs.yml navigation

### File List

- docs/site/checks/enrichment.md (new)
- docs/site/checks/freshness.md (new)
- docs/site/checks/coverage.md (new)
- docs/site/checks/griffe.md (new)
- docs/site/configuration.md (new)
- mkdocs.yml (modified — nav section)
