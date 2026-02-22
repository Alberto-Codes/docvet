# Story 11.3: Rule Reference Pages

Status: review
Branch: `feat/docs-11-3-rule-reference-pages`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer who received a docvet finding,
I want to look up the rule by its identifier and understand what it means, why it matters, and how to fix it,
so that I can resolve findings quickly without guessing.

## Acceptance Criteria

1. **Given** the docs site with check pages from Story 11.2, **when** 19 rule reference pages are added, **then** each of the 19 rule identifiers (`missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-other-parameters`, `missing-attributes`, `missing-typed-attributes`, `missing-examples`, `missing-cross-references`, `prefer-fenced-code-blocks`, `stale-signature`, `stale-body`, `stale-import`, `stale-drift`, `stale-age`, `griffe-missing-type`, `griffe-unknown-param`, `griffe-format-warning`, `missing-init`) has a dedicated page
2. **Given** a rule reference page, **then** each page shows: rule code, check type (enrichment/freshness/coverage/griffe), default category (required/recommended)
3. **Given** a rule reference page, **then** each page follows the What/Why/Example/Fix template: "What it detects" (1-2 sentences), "Why is this a problem?" (consequence explanation), "Example" (Python code showing the violation), "Fix" (Python code showing the corrected version)
4. **Given** 19 rule reference pages, **then** all 19 pages are linked from their parent check page (enrichment check page links to its 10 rules, freshness to its 5, coverage to its 1, griffe to its 3)
5. **Given** the docs site navigation, **then** navigation includes a "Rules" section listing all 19 rules grouped by check type
6. **Given** 19 rule reference pages, **then** all pages are structurally consistent: same H2 headings (`What it detects`, `Why is this a problem?`, `Example`, `Fix`), same code fence language markers (`python`), same metadata fields (rule code, check type, category)
7. **Given** the completed docs site, **then** `mkdocs build --strict` builds without errors and all rule pages are navigable

## Tasks / Subtasks

- [x] Task 1: Set up rules scaffold infrastructure (AC: #2, #6)
  - [x] 1.1 Add `mkdocs-macros-plugin` to `[project.optional-dependencies] docs` in `pyproject.toml` and run `uv sync --extra docs`
  - [x] 1.2 Create `docs/rules.yml` — YAML catalog with all 19 rules (schema: id, name, check, category, applies_to, summary, since)
  - [x] 1.3 Create `docs/main.py` — macros hook defining `define_env()` that loads `rules.yml` and provides `rule_header(env)` macro
  - [x] 1.4 Add `macros` plugin to `mkdocs.yml` plugins list (must be last plugin) with `module_name: docs/main`
  - [x] 1.5 Create `docs/site/rules/` directory
  - [x] 1.6 Verify scaffold: create one test rule page using `{{ rule_header() }}`, confirm `mkdocs build --strict` renders the macro-generated metadata header correctly, then proceed to remaining pages
- [x] Task 2: Create 10 enrichment rule pages (AC: #1, #3, #6)
  - [x] 2.1 `docs/site/rules/missing-raises.md`
  - [x] 2.2 `docs/site/rules/missing-yields.md`
  - [x] 2.3 `docs/site/rules/missing-receives.md`
  - [x] 2.4 `docs/site/rules/missing-warns.md`
  - [x] 2.5 `docs/site/rules/missing-other-parameters.md`
  - [x] 2.6 `docs/site/rules/missing-attributes.md`
  - [x] 2.7 `docs/site/rules/missing-typed-attributes.md`
  - [x] 2.8 `docs/site/rules/missing-examples.md`
  - [x] 2.9 `docs/site/rules/missing-cross-references.md`
  - [x] 2.10 `docs/site/rules/prefer-fenced-code-blocks.md`
- [x] Task 3: Create 5 freshness rule pages (AC: #1, #3, #6)
  - [x] 3.1 `docs/site/rules/stale-signature.md`
  - [x] 3.2 `docs/site/rules/stale-body.md`
  - [x] 3.3 `docs/site/rules/stale-import.md`
  - [x] 3.4 `docs/site/rules/stale-drift.md`
  - [x] 3.5 `docs/site/rules/stale-age.md`
- [x] Task 4: Create 1 coverage rule page (AC: #1, #3, #6)
  - [x] 4.1 `docs/site/rules/missing-init.md`
- [x] Task 5: Create 3 griffe rule pages (AC: #1, #3, #6)
  - [x] 5.1 `docs/site/rules/griffe-unknown-param.md`
  - [x] 5.2 `docs/site/rules/griffe-missing-type.md`
  - [x] 5.3 `docs/site/rules/griffe-format-warning.md`
- [x] Task 6: Add rule links to parent check pages (AC: #4)
  - [x] 6.1 Update `docs/site/checks/enrichment.md` — add links from Rules table to individual rule pages
  - [x] 6.2 Update `docs/site/checks/freshness.md` — add links from Rules table to individual rule pages
  - [x] 6.3 Update `docs/site/checks/coverage.md` — add link from Rules table to rule page
  - [x] 6.4 Update `docs/site/checks/griffe.md` — add links from Rules table to individual rule pages
- [x] Task 7: Update mkdocs.yml navigation and verify build (AC: #5, #7)
  - [x] 7.1 Add "Rules" nav section with all 19 rules grouped by check type
  - [x] 7.2 Run `mkdocs build --strict` and confirm zero errors
  - [x] 7.3 Verify all rule pages are navigable and search returns results for rule IDs

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- All verifications are manual (docs-only story — no automated tests). -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Manual: 19 rule page files exist in `docs/site/rules/`, confirmed by `ls docs/site/rules/ \| wc -l` = 19 | Pass |
| AC2 | Manual: Each rule page uses `{{ rule_header() }}` macro rendering check type, category, applies_to, since from `rules.yml` | Pass |
| AC3 | Manual: Each page follows What/Why/Example/Fix template with `=== "Violation"` and `=== "Fix"` content tabs using `python` code fences | Pass |
| AC4 | Manual: All 4 check pages updated — enrichment (10 links), freshness (5 links), coverage (1 link), griffe (3 links) | Pass |
| AC5 | Manual: `mkdocs.yml` nav includes "Rules" section with Enrichment (10), Freshness (5), Coverage (1), Griffe (3) subsections | Pass |
| AC6 | Manual: All 19 pages use identical H2 structure (`What it detects`, `Why is this a problem?`, `Example`), same code fence language, same macro-generated metadata | Pass |
| AC7 | Manual: `mkdocs build --strict` exits 0, all 19 rules in search index confirmed by parsing `search_index.json` | Pass |

## Dev Notes

### Rule Page Template (Mandatory)

All 19 rule pages MUST follow this exact structure. The metadata header is rendered by the `rule_header()` Jinja macro from `docs/main.py`, reading data from `docs/rules.yml`. Narrative sections are handwritten. Do not vary headings, order, or section names between pages.

```markdown
# `rule-id`

{{ rule_header() }}

## What it detects

1-2 sentences explaining what this rule flags. Plain language, no jargon.

## Why is this a problem?

2-3 sentences explaining the real-world consequence of ignoring this issue.
Focus on the downstream impact: broken docs, confused users, stale information.

## Example

=== "Violation"

    ```python
    # Code that triggers this rule
    ```

=== "Fix"

    ```python
    # Corrected code
    ```
```

**Template details:**
- `{{ rule_header() }}` renders a metadata table from `rules.yml` (check type, category, applies-to, summary). The macro infers the rule ID from the page filename (e.g., `missing-raises.md` → `missing-raises`).
- Content tabs (`=== "Violation"` / `=== "Fix"`) use `pymdownx.tabbed` (already enabled in `mkdocs.yml`) to show violation and fix side-by-side, following the ruff/ty documentation pattern.
- All code fences use `python` language marker for syntax highlighting.

### Rule Content Reference (Source of Truth)

Extract all rule behavior and examples from source code, NOT from memory. The definitive sources are:

| Check Module | Source File | Key Function |
|---|---|---|
| enrichment | `src/docvet/checks/enrichment.py` | `check_enrichment()` + `_check_*` helpers |
| freshness | `src/docvet/checks/freshness.py` | `check_freshness_diff()`, `check_freshness_drift()` |
| coverage | `src/docvet/checks/coverage.py` | `check_coverage()` |
| griffe | `src/docvet/checks/griffe_compat.py` | `check_griffe_compat()` |

### All 19 Rules — Content Guide

#### Enrichment Rules (10)

**`missing-raises`** (required, functions/methods)
- Detects: Function body contains `raise` statements but docstring has no `Raises:` section
- Why bad: Callers don't know which exceptions to catch; leads to unhandled errors in production
- Example: function with `raise ValueError(...)` but no Raises section
- Fix: Add `Raises:` section listing `ValueError` with description

**`missing-yields`** (required, functions/methods)
- Detects: Generator function contains `yield` or `yield from` but docstring has no `Yields:` section
- Why bad: Consumers don't know what the generator produces; can't write correct iteration code
- Example: function with `yield item` but no Yields section
- Fix: Add `Yields:` section describing yielded values

**`missing-receives`** (required, functions/methods)
- Detects: Generator uses send pattern (`value = yield`) but docstring has no `Receives:` section
- Why bad: Callers using `.send()` don't know what values the generator accepts
- Example: `data = yield` assignment with no Receives section
- Fix: Add `Receives:` section describing accepted values

**`missing-warns`** (required, functions/methods)
- Detects: Function calls `warnings.warn()` but docstring has no `Warns:` section
- Why bad: Users don't know which warnings to expect or suppress; noisy logs in production
- Example: `warnings.warn("deprecated", DeprecationWarning)` with no Warns section
- Fix: Add `Warns:` section listing warning type and condition

**`missing-other-parameters`** (recommended, functions/methods)
- Detects: Function accepts `**kwargs` but docstring has no `Other Parameters:` section
- Why bad: Callers must read source code to discover available keyword arguments
- Example: `def create(name, **kwargs):` with no Other Parameters section
- Fix: Add `Other Parameters:` section documenting accepted keyword arguments

**`missing-attributes`** (required, classes/modules)
- Detects: Dataclass, NamedTuple, TypedDict, class with `__init__` self-assignments, or `__init__.py` module with no `Attributes:` section
- Why bad: Users can't discover object properties without reading source; mkdocs renders empty attribute tables
- Example: `@dataclass` class with fields but no Attributes section
- Fix: Add `Attributes:` section listing each field with type and description

**`missing-typed-attributes`** (recommended, classes)
- Detects: `Attributes:` section entries lack typed format `name (type): description`
- Why bad: mkdocstrings can't render attribute types in API docs; users lose type information
- Example: `Attributes:` with `name: The user name` instead of `name (str): The user name`
- Fix: Add parenthesized type: `name (str): The user name`

**`missing-examples`** (recommended, classes/modules)
- Detects: Symbol kind in `require-examples` config list (default: class, protocol, dataclass, enum) lacks `Examples:` section
- Why bad: Complex types without usage examples force users to reverse-engineer behavior from source
- Example: `@dataclass` class with no Examples section when `require-examples` includes "dataclass"
- Fix: Add `Examples:` section with a fenced code block showing instantiation/usage

**`missing-cross-references`** (recommended, modules)
- Detects: `__init__.py` module docstring missing `See Also:` section, or `See Also:` section lacking cross-reference syntax
- Why bad: Package modules are navigation entry points; missing cross-refs break mkdocs discoverability
- Example: `__init__.py` module docstring with no See Also section
- Fix: Add `See Also:` section with backtick-quoted identifiers or Markdown links

**`prefer-fenced-code-blocks`** (recommended, any symbol)
- Detects: `Examples:` section uses doctest `>>>` format instead of fenced code blocks
- Why bad: mkdocs-material renders fenced blocks with syntax highlighting; doctest `>>>` renders as plain text
- Example: Examples section with `>>> foo(1)` / `2`
- Fix: Replace with triple-backtick fenced code block with `python` language marker

#### Freshness Rules (5)

**`stale-signature`** (required, diff mode)
- Detects: Function signature changed in git diff but docstring was not updated
- Why bad: Callers relying on documented parameters get wrong information; highest-impact staleness
- Example: Parameter renamed/added/removed but docstring still describes old signature
- Fix: Update docstring Args/Returns to match new signature

**`stale-body`** (recommended, diff mode)
- Detects: Function body changed in git diff but docstring was not updated
- Why bad: Docstring may describe outdated behavior; medium-impact staleness
- Example: Function logic changed (new branch, different return) but docstring unchanged
- Fix: Review and update docstring to reflect new behavior

**`stale-import`** (recommended, diff mode)
- Detects: Import or formatting changed in git diff but docstring not updated
- Why bad: Low-impact but may indicate dependency changes not reflected in docs
- Example: Import added/removed near a function but docstring unchanged
- Fix: Review if import change affects documented behavior

**`stale-drift`** (recommended, drift mode)
- Detects: Code modified more recently than docstring by more than `drift-threshold` days (default: 30)
- Why bad: Docstring is falling behind active code changes; gradually becoming unreliable
- Example: Function body last modified 2026-01-15, docstring last modified 2025-11-02 (74 days drift)
- Fix: Review and update docstring to reflect current implementation

**`stale-age`** (recommended, drift mode)
- Detects: Docstring untouched for more than `age-threshold` days (default: 90)
- Why bad: Very old docstrings may describe obsolete behavior even if code hasn't changed much
- Example: Docstring last modified 180 days ago
- Fix: Review docstring for accuracy and touch it to reset the age counter

#### Coverage Rule (1)

**`missing-init`** (required)
- Detects: Directory in source tree lacks `__init__.py` file
- Why bad: Python files in that directory are invisible to mkdocstrings and won't appear in generated API docs
- Example: `src/myapp/helpers/` directory with `.py` files but no `__init__.py`
- Fix: Create an `__init__.py` file (can be empty or with module docstring)

#### Griffe Rules (3)

**`griffe-unknown-param`** (required)
- Detects: Docstring documents a parameter that doesn't exist in the function signature
- Why bad: Misleading documentation; parameter may have been renamed or removed
- Example: Docstring has `Args: timeout (int):` but function signature has no `timeout` parameter
- Fix: Remove the stale parameter from the docstring or add it to the function signature

**`griffe-missing-type`** (recommended)
- Detects: Parameter or return value in docstring lacks type annotation
- Why bad: mkdocstrings can't render type information; users lose type context in API docs
- Example: `Args: name: The user name` instead of `Args: name (str): The user name`
- Fix: Add type annotation in parentheses: `name (str): The user name`

**`griffe-format-warning`** (recommended)
- Detects: Docstring has formatting issues that would break mkdocs rendering (caught by griffe parser)
- Why bad: Malformed docstrings render incorrectly or cause griffe parser warnings in build output
- Example: Incorrectly indented section, malformed section header
- Fix: Correct the formatting per Google-style docstring conventions

### Architecture Compliance

Per Architecture Decision 3 (Rule Reference Page Structure), this story uses the **YAML catalog + macros scaffold**:

- **`docs/rules.yml`** — single source of truth for rule metadata. Adding a rule = one YAML entry + one markdown file.
- **`mkdocs-macros-plugin`** — Jinja macros for consistent page headers rendered from YAML data. Added as a `docs` optional dependency (NOT a runtime dependency).
- **`docs/main.py`** — macros hook module defining `define_env()` and `rule_header()`. Lives outside `docs_dir` so it's not served as a page.
- **No mkdocstrings** — pages are manually authored markdown, not auto-generated from source. This is intentional per Story 11.1.
- **mkdocs-material free tier only** — no paid features (e.g., no `tags` plugin). All navigation is manual in `mkdocs.yml`.
- **docs_dir is `docs/site/`** — all content pages live under this directory. Rule pages go in `docs/site/rules/` subdirectory.
- **No new runtime dependencies** — `mkdocs-macros-plugin` is a docs-only dev dependency. No changes to `src/docvet/`.
- **Content tabs** — `pymdownx.tabbed` (already enabled) for side-by-side violation/fix examples, following the ruff/ty pattern.

### File Structure

```
docs/
├── main.py                     # NEW — macros hook (define_env, rule_header)
├── rules.yml                   # NEW — 19-rule YAML metadata catalog
└── site/                       # docs_dir
    ├── index.md                # EXISTING — Getting Started (DO NOT modify)
    ├── cli-reference.md        # EXISTING — CLI Reference (DO NOT modify)
    ├── configuration.md        # EXISTING — Configuration Reference (DO NOT modify)
    ├── checks/
    │   ├── enrichment.md       # EXISTING — modify to add rule page links (Task 6)
    │   ├── freshness.md        # EXISTING — modify to add rule page links (Task 6)
    │   ├── coverage.md         # EXISTING — modify to add rule page links (Task 6)
    │   └── griffe.md           # EXISTING — modify to add rule page links (Task 6)
    └── rules/                  # NEW directory
        ├── missing-raises.md   # NEW — 10 enrichment rule pages
        ├── missing-yields.md
        ├── missing-receives.md
        ├── missing-warns.md
        ├── missing-other-parameters.md
        ├── missing-attributes.md
        ├── missing-typed-attributes.md
        ├── missing-examples.md
        ├── missing-cross-references.md
        ├── prefer-fenced-code-blocks.md
        ├── stale-signature.md  # NEW — 5 freshness rule pages
        ├── stale-body.md
        ├── stale-import.md
        ├── stale-drift.md
        ├── stale-age.md
        ├── missing-init.md     # NEW — 1 coverage rule page
        ├── griffe-unknown-param.md # NEW — 3 griffe rule pages
        ├── griffe-missing-type.md
        └── griffe-format-warning.md
```

### mkdocs.yml Changes

**Plugin addition** — add `macros` as the LAST plugin (per architecture Pattern 6 ordering):

```yaml
plugins:
  - search
  - macros:
      module_name: docs/main
```

**Navigation update** — add a "Rules" section grouping rules by check type:

```yaml
nav:
  - Getting Started: index.md
  - Checks:
    - checks/enrichment.md
    - checks/freshness.md
    - checks/coverage.md
    - checks/griffe.md
  - Rules:
    - Enrichment:
      - missing-raises: rules/missing-raises.md
      - missing-yields: rules/missing-yields.md
      - missing-receives: rules/missing-receives.md
      - missing-warns: rules/missing-warns.md
      - missing-other-parameters: rules/missing-other-parameters.md
      - missing-attributes: rules/missing-attributes.md
      - missing-typed-attributes: rules/missing-typed-attributes.md
      - missing-examples: rules/missing-examples.md
      - missing-cross-references: rules/missing-cross-references.md
      - prefer-fenced-code-blocks: rules/prefer-fenced-code-blocks.md
    - Freshness:
      - stale-signature: rules/stale-signature.md
      - stale-body: rules/stale-body.md
      - stale-import: rules/stale-import.md
      - stale-drift: rules/stale-drift.md
      - stale-age: rules/stale-age.md
    - Coverage:
      - missing-init: rules/missing-init.md
    - Griffe:
      - griffe-unknown-param: rules/griffe-unknown-param.md
      - griffe-missing-type: rules/griffe-missing-type.md
      - griffe-format-warning: rules/griffe-format-warning.md
  - Configuration: configuration.md
  - CLI Reference: cli-reference.md
```

### Scaffold Implementation Details

#### `docs/rules.yml` Schema

Single source of truth for all 19 rules. Each entry has exactly these fields:

```yaml
- id: missing-raises            # kebab-case, matches filename and Finding.rule field
  name: Missing Raises Section  # human-readable display name
  check: enrichment             # enrichment | freshness | coverage | griffe
  category: required            # required | recommended
  applies_to: functions, methods  # what symbol kinds this rule applies to
  summary: Function raises exceptions but has no Raises: section
  since: "1.0.0"                # version introduced
```

All 19 entries must be present. The `id` field must exactly match the rule page filename (minus `.md`). Do NOT add ad-hoc fields — the 7-field schema is the contract.

**Future consumers of `rules.yml`** (beyond this story):
- Rules index page (potential future auto-generation)
- CLI `--explain <rule-id>` feature (growth phase)
- Rule documentation URLs in findings (growth phase)

#### `docs/main.py` Macros Hook

Defines `define_env(env)` which:
1. Loads `docs/rules.yml` using `yaml.safe_load()`
2. Builds a lookup dict keyed by rule `id`
3. Registers a `rule_header` Jinja macro that:
   - Infers the rule ID from the current page's filename (via `env.page.file.name` → strip `.md`)
   - Looks up the rule in the YAML data
   - Renders a metadata table:

```
| | |
|---|---|
| **Check** | enrichment |
| **Category** | required |
| **Applies to** | functions, methods |
| **Since** | v1.0.0 |

> Function raises exceptions but has no Raises: section
```

The macro renders markdown (not HTML) so it integrates naturally with the rest of the page. If a rule ID is not found in `rules.yml`, the macro should raise a clear build error so missing catalog entries are caught by `mkdocs build --strict`.

#### `pyproject.toml` Dependency Addition

Add `mkdocs-macros-plugin` to the existing `docs` optional dependency group:

```toml
[project.optional-dependencies]
docs = [
    "mkdocs-material>=9.5,<10",
    "mkdocs<2",
    "mkdocs-macros-plugin>=1.0",  # NEW — Jinja macros for rule page headers
]
```

Then run `uv sync --extra docs` to install.

### Check Page Cross-Linking (Task 6)

Each check page has a Rules table (created in Story 11.2). Convert rule IDs in the first column from inline code to markdown links pointing to the rule reference page:

**Before** (current):
```markdown
| `missing-raises` | required | functions, methods | ... |
```

**After** (updated):
```markdown
| [`missing-raises`](../rules/missing-raises.md) | required | functions, methods | ... |
```

Apply this pattern to all rule IDs in all 4 check pages. The relative path from `checks/` to `rules/` is `../rules/`.

### Markdown Extensions Available

From `mkdocs.yml`, these extensions are available for rule pages:
- `admonition` — for tip/warning/note callout boxes
- `pymdownx.superfences` — fenced code blocks with syntax highlighting
- `pymdownx.highlight` — syntax highlighting with line numbers via `anchor_linenums: true`
- `toc` — table of contents with permalink anchors
- `content.code.copy` — copy button on code blocks (enabled in theme features)

### Previous Story Intelligence (11.2)

**Key learnings from Story 11.2:**
- Zero-debug implementation — story spec quality was high
- Check Page Template with mandatory H2 structure worked well — apply same rigor to rule page template
- All rule details extracted from source code, NOT from memory — critical pattern to follow
- All config keys extracted from `config.py` — verified against actual implementation
- CLI flags cross-checked against actual `docvet --help` (NFR58)
- `mkdocs build --strict` catches missing page refs and broken nav — always run before declaring done
- Story 11.2 notes: "Cross-referencing forward: Check pages should mention rule IDs but do NOT need to link to individual rule reference pages yet — those are created in Story 11.3." Now is the time to add those links.
- Story 11.2 deferred macros to this story: "`mkdocs-macros` and `docs/rules.yml` catalog are for Story 11.3 (rule reference pages), not this story." This story now implements that scaffold per Architecture Decision 3.

**Files created by 11.2 (and their modification scope in this story):**
- `docs/site/checks/enrichment.md` — MODIFY: add rule page links in Rules table (Task 6.1)
- `docs/site/checks/freshness.md` — MODIFY: add rule page links in Rules table (Task 6.2)
- `docs/site/checks/coverage.md` — MODIFY: add rule page links in Rules table (Task 6.3)
- `docs/site/checks/griffe.md` — MODIFY: add rule page links in Rules table (Task 6.4)
- `docs/site/configuration.md` — DO NOT MODIFY
- `mkdocs.yml` — MODIFY: add Rules nav section (Task 7.1)

### Git Intelligence

Recent commits (relevant to this story):
- `a67b718` — marked story 11.2 as done
- `2408d1c` — PR #68 that added check pages and configuration reference
- `42d43d6` — PR #67 that scaffolded the docs site with Getting Started and CLI Reference

All docs work has been zero-debug so far. Pattern: well-specified stories produce clean implementations.

### NFR Compliance

- **NFR57:** mkdocs-material handles responsive design natively — no extra work needed for rule pages
- **NFR58:** Rule pages document rule behavior, not CLI flags — NFR58 (CLI/docs drift) is less relevant here but ensure rule descriptions match actual check behavior from source code

### Project Context Reference

See `_bmad-output/project-context.md` for full project conventions. Key points for this story:
- This is a docs-only story — no changes to `src/docvet/` or `tests/`
- No automated tests — all verification is manual (`mkdocs build --strict`, visual inspection)
- Google-style docstrings assumed throughout — all examples in rule pages must use Google-style format

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 11, Story 11.3]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 3: Rule Reference Page Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md — Pattern 2: Rule Page Authoring]
- [Source: _bmad-output/planning-artifacts/architecture.md — Pattern 6: mkdocs.yml Plugin Ordering]
- [Source: src/docvet/checks/enrichment.py — 10 rule identifiers and detection logic]
- [Source: src/docvet/checks/freshness.py — 5 rule identifiers, diff/drift modes]
- [Source: src/docvet/checks/coverage.py — missing-init rule]
- [Source: src/docvet/checks/griffe_compat.py — 3 griffe rules and warning classification]
- [Source: _bmad-output/implementation-artifacts/11-2-check-pages-and-configuration-reference.md — previous story learnings]
- [Source: CLAUDE.md — CLI commands, architecture overview]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues — zero-debug implementation (third consecutive docs story).

### Completion Notes List

- Scaffold built with `mkdocs-macros-plugin` + `docs/rules.yml` YAML catalog + `docs/main.py` macros hook
- `rule_header()` macro infers rule ID from page filename and renders metadata table from YAML
- Macro raises `ValueError` on unknown rule ID, caught by `mkdocs build --strict`
- All 19 rule pages follow identical template: H1 with rule ID, macro-generated metadata, What/Why/Example sections
- Content tabs (`pymdownx.tabbed`) used for side-by-side Violation/Fix examples
- `hl_lines` added to all 19 Fix code blocks to visually highlight the fix (works in built output; `mkdocs serve` live-reload strips them — known dev-server limitation)
- Bumped `--md-code-hl-color` opacity and added explicit `.hll` CSS rules in `theme.css` for both dark and light modes
- All 4 check pages updated with cross-links from Rules tables to individual rule pages
- Nav updated with "Rules" section grouping 19 rules by check type (Enrichment/Freshness/Coverage/Griffe)
- `mkdocs build --strict` passes, all 19 rules appear in search index
- 729 existing tests pass — no regressions (docs-only story, no src/tests changes)

### Change Log

- 2026-02-22: Implemented Story 11.3 — 19 rule reference pages with YAML catalog + macros scaffold, check page cross-links, nav updates, and hl_lines fix highlighting

### File List

- `pyproject.toml` — modified (added `mkdocs-macros-plugin` to docs optional deps)
- `mkdocs.yml` — modified (added macros plugin, Rules nav section with 19 entries)
- `docs/main.py` — new (macros hook with `define_env()` and `rule_header()`)
- `docs/rules.yml` — new (19-rule YAML metadata catalog)
- `docs/site/rules/missing-raises.md` — new
- `docs/site/rules/missing-yields.md` — new
- `docs/site/rules/missing-receives.md` — new
- `docs/site/rules/missing-warns.md` — new
- `docs/site/rules/missing-other-parameters.md` — new
- `docs/site/rules/missing-attributes.md` — new
- `docs/site/rules/missing-typed-attributes.md` — new
- `docs/site/rules/missing-examples.md` — new
- `docs/site/rules/missing-cross-references.md` — new
- `docs/site/rules/prefer-fenced-code-blocks.md` — new
- `docs/site/rules/stale-signature.md` — new
- `docs/site/rules/stale-body.md` — new
- `docs/site/rules/stale-import.md` — new
- `docs/site/rules/stale-drift.md` — new
- `docs/site/rules/stale-age.md` — new
- `docs/site/rules/missing-init.md` — new
- `docs/site/rules/griffe-unknown-param.md` — new
- `docs/site/rules/griffe-missing-type.md` — new
- `docs/site/rules/griffe-format-warning.md` — new
- `docs/site/checks/enrichment.md` — modified (rule IDs linked to rule pages)
- `docs/site/checks/freshness.md` — modified (rule IDs linked to rule pages)
- `docs/site/checks/coverage.md` — modified (rule ID linked to rule page)
- `docs/site/checks/griffe.md` — modified (rule IDs linked to rule pages)
- `docs/site/stylesheets/theme.css` — modified (increased hl_lines highlight visibility for both themes)
