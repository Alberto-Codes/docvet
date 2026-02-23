---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'mkdocstrings and mkdocs tooltip plugins for Epic 13 docs site'
research_goals: 'Evaluate mkdocstrings for auto-generated API reference with Google-style docstrings via griffe; identify best tooltip/glossary plugin compatible with mkdocs-material; provide configuration recommendations for both'
user_name: 'Alberto-Codes'
date: '2026-02-22'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-02-22
**Author:** Alberto-Codes
**Research Type:** technical

---

## Research Overview

This research evaluates two mkdocs plugin categories for docvet's Epic 13 documentation site: (1) mkdocstrings with the Python/griffe handler for auto-generated API reference, and (2) tooltip/glossary solutions compatible with mkdocs-material. The goal is to determine the best candidates, validate compatibility with docvet's existing Google-style docstrings and mkdocs-material theme, and provide concrete configuration recommendations.

---

## Technical Research Scope Confirmation

**Research Topic:** mkdocstrings and mkdocs tooltip plugins for Epic 13 docs site
**Research Goals:** Evaluate mkdocstrings for auto-generated API reference with Google-style docstrings via griffe; identify best tooltip/glossary plugin compatible with mkdocs-material; provide configuration recommendations for both

**Technical Research Scope:**

- Technology Stack — mkdocstrings (with griffe handler), tooltip/glossary plugins, mkdocs-material compatibility matrix
- Integration Patterns — griffe module discovery, Google-style docstring rendering, tooltip plugin build pipeline hooks
- Implementation Approaches — mkdocs.yml configuration, API reference page layout, glossary term definition patterns
- Architecture Analysis — interaction with docvet's existing docs site (YAML catalog, macros scaffold, mkdocs-material theme)
- Performance Considerations — build time impact, optional dependency handling

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-02-22

## Technology Stack Analysis

### mkdocstrings with Python Handler (API Reference)

**What it is:** mkdocstrings is an mkdocs plugin that auto-generates API documentation from Python source code. The Python handler (mkdocstrings-python) uses **griffe** under the hood to parse source code and docstrings — the same griffe that docvet already uses for its `griffe_compat` check.

**Current versions:** mkdocstrings v1.0.3 (2026-02-07), mkdocstrings-python latest stable. Actively maintained with recent PEP 695 generics support and Ruff-based signature formatting.

**Google-style docstring support (via griffe):**

All sections docvet checks for are fully supported by griffe's Google parser:

| Section | Griffe Support | Aliases |
|---------|---------------|---------|
| Parameters | ✅ | Args, Arguments, Params |
| Returns | ✅ | — |
| Raises | ✅ | Exceptions |
| Yields | ✅ | — |
| Receives | ✅ | — |
| Examples | ✅ | — |
| Attributes | ✅ | — |
| Warns | ✅ | Warnings |
| Other Parameters | ✅ | Keyword Args, Keyword Arguments |
| Functions | ✅ | — |
| Classes | ✅ | — |
| Modules | ✅ | — |

Unrecognized sections (e.g., "Note:", "Tip:") are automatically rendered as admonitions — graceful fallback, not errors.

**Confidence: HIGH** — griffe is already a docvet dependency, Google-style is the default parser, and all docvet docstring sections map 1:1 to griffe's supported sections.

_Sources: [mkdocstrings-python overview](https://mkdocstrings.github.io/python/), [Google docstrings](https://mkdocstrings.github.io/python/usage/docstrings/google/), [Griffe docstring parsers](https://mkdocstrings.github.io/griffe/reference/docstrings/), [Docstring configuration](https://mkdocstrings.github.io/python/usage/configuration/docstrings/)_

### mkdocstrings Key Configuration Options

**Docstring rendering controls:**

| Option | Default | Relevance to docvet |
|--------|---------|-------------------|
| `docstring_style` | `"google"` | Already matches docvet's convention |
| `docstring_section_style` | `"table"` | Table, list, or spacy layout for Args/Returns/etc. |
| `merge_init_into_class` | `False` | Useful — merges `__init__` params into class signature |
| `show_root_heading` | `False` | Should set to `True` for standalone API pages |
| `show_source` | `True` | Show source code links |
| `show_signature_annotations` | `False` | Should set to `True` — docvet has type hints everywhere |
| `separate_signature` | `False` | Should set to `True` for readability on complex signatures |
| `members` | `None` | Controls which members to document |
| `filters` | `["!^_"]` | Default hides private members — matches docvet's public API focus |
| `summary` | `False` | Should set to `True` for module-level summaries |

**Section-level display toggles:** Every docstring section has an individual `show_docstring_*` toggle (all default to `True`): attributes, classes, description, examples, functions, modules, other_parameters, parameters, raises, receives, returns, warns, yields.

_Source: [mkdocstrings-python configuration](https://mkdocstrings.github.io/python/usage/configuration/docstrings/)_

### Tooltip/Glossary Solutions for mkdocs-material

Three approaches evaluated, from simplest to most complex:

#### Option A: Built-in mkdocs-material Abbreviations + Snippets (RECOMMENDED)

**What it is:** mkdocs-material has native support for abbreviations with tooltips using standard Markdown extensions (`abbr`, `pymdownx.snippets`). Terms are defined in a central glossary file and auto-appended to all pages via snippets.

**How it works:**
1. Define terms in `includes/abbreviations.md` (outside `docs/` folder)
2. Use `pymdownx.snippets` with `auto_append` to inject definitions into every page
3. Enable `content.tooltips` theme feature for styled rendering
4. Any matching text on any page automatically gets a tooltip

**Advantages:**
- Zero additional dependencies — uses extensions already bundled with mkdocs-material
- `attr_list` extension already in docvet's `mkdocs.yml`
- Clean, simple configuration
- Project-wide glossary from a single file
- Styled tooltips (not browser default) with `content.tooltips` feature

**Limitations:**
- Abbreviation matching is exact text only (case-sensitive, whole word)
- No link to a glossary page — tooltip only
- No support for multi-word terms with varying forms (e.g., "docstring" won't match "docstrings")

**Confidence: HIGH** — first-party support, zero new dependencies, proven pattern.

_Sources: [Material tooltips](https://squidfunk.github.io/mkdocs-material/reference/tooltips/), [Python Markdown extensions](https://squidfunk.github.io/mkdocs-material/setup/extensions/python-markdown/)_

#### Option B: mkdocs-glossary-plugin

**What it is:** Third-party plugin that replaces glossary terms with links to dedicated glossary pages. Each term gets its own `.md` file in a glossary directory.

**How it works:**
1. Create glossary directory with one `.md` file per term
2. Plugin auto-replaces term occurrences with links to the glossary page
3. Supports aliases via frontmatter metadata
4. Configurable case sensitivity and text inclusion rules

**Advantages:**
- Terms link to full definition pages (not just tooltips)
- Alias support (multiple terms → one definition)
- Configurable scope (headings, emphasized text, etc.)

**Limitations:**
- Additional dependency
- One file per term is heavyweight for a small glossary
- Less mature than built-in solution
- No tooltip preview — just links

**Confidence: MEDIUM** — functional but overkill for docvet's needs.

_Source: [mkdocs-glossary-plugin GitHub](https://github.com/AngryMane/mkdocs-glossary-plugin)_

#### Option C: mkdocs-ezglossary

**What it is:** More feature-rich glossary plugin with cross-referencing support.

**Advantages:** Rich cross-referencing, summary pages
**Limitations:** Most complex option, additional dependency, potentially fragile with mkdocs-material

**Confidence: LOW** — unnecessary complexity for docvet's glossary needs.

_Source: [mkdocs-ezglossary GitHub](https://github.com/realtimeprojects/mkdocs-ezglossary)_

### Docvet's Existing mkdocs Infrastructure

**Current mkdocs.yml already has:**
- `attr_list` extension (required for tooltips — already present)
- `macros` plugin with custom `docs/main.py` module (YAML catalog pattern)
- mkdocs-material theme with `navigation.instant`, `content.code.copy`, etc.
- `admonition`, `pymdownx.details`, `pymdownx.superfences`, `pymdownx.highlight`

**What needs to be added for Epic 13:**
- `mkdocstrings` plugin with Python handler configuration
- `abbr` extension + `pymdownx.snippets` with `auto_append` (for glossary)
- `content.tooltips` theme feature
- New nav entries for API reference and glossary pages

**Compatibility assessment:** All additions are additive — no conflicts with existing configuration. mkdocstrings and macros plugins coexist (both are common in mkdocs-material projects). The snippets extension is part of pymdownx, already partially used.

### Technology Adoption Context

mkdocstrings is the dominant API documentation solution for mkdocs projects. It is used by major Python projects and has a mature ecosystem. The griffe backend is actively maintained and is already a docvet dependency.

The built-in abbreviations + snippets approach for glossaries is the recommended pattern in mkdocs-material's own documentation — no third-party plugin needed.

Both technologies are stable, well-documented, and have clear upgrade paths.

## Integration Patterns Analysis

### mkdocstrings Integration with Docvet's mkdocs Setup

**Installation:**

```bash
uv add --dev mkdocstrings[python]
```

This installs mkdocstrings + mkdocstrings-python + griffe. Since griffe is already an optional docvet dependency, there's no conflict — the dev dependency will use whatever griffe version is compatible.

**mkdocs.yml plugin configuration:**

```yaml
plugins:
  - search
  - macros:
      module_name: docs/main    # existing
  - mkdocstrings:
      handlers:
        python:
          paths: [src]           # docvet source lives in src/
          options:
            docstring_style: google
            docstring_section_style: table
            show_root_heading: true
            show_root_full_path: false
            show_symbol_type_heading: true
            show_source: true
            show_signature_annotations: true
            separate_signature: true
            merge_init_into_class: true
            summary: true
            filters: ["!^_"]     # hide private members
```

**Plugin ordering note:** mkdocstrings must be listed AFTER macros in mkdocs.yml. Order matters — plugins execute in listed order.

**Known limitation:** Macros defined in `docs/main.py` will NOT expand inside docstrings rendered by mkdocstrings. This is a [known compatibility issue](https://github.com/mkdocstrings/mkdocstrings/issues/615). Not a problem for docvet — our macros (`rule_header()`) are used in hand-written rule pages, not in source code docstrings.

_Sources: [mkdocstrings usage](https://mkdocstrings.github.io/usage/), [macros compatibility issue](https://github.com/mkdocstrings/mkdocstrings/issues/615)_

### API Reference Page Generation: Auto-Generated (RECOMMENDED)

**Approach: `mkdocs-gen-files` + `mkdocs-literate-nav` + `mkdocstrings`**

Uses the [official mkdocstrings recipe](https://mkdocstrings.github.io/recipes/) to auto-discover all modules and generate reference pages at build time:

```yaml
plugins:
  - gen-files:
      scripts:
        - scripts/gen_ref_pages.py
  - literate-nav:
      nav_file: SUMMARY.md
  - mkdocstrings
```

The `gen_ref_pages.py` script (~25 lines) walks `src/docvet/`, creates a `::: module.name` stub for each `.py` file, and generates a `SUMMARY.md` navigation file. New modules are discovered automatically — zero maintenance burden.

**Why auto-gen is the right call for docvet:**

1. **Showcase value** — docvet is a documentation quality tool. Auto-generating pristine API docs from our own dogfooded docstrings *is* the proof that the tool works. Manual curation undercuts this message.
2. **Zero maintenance** — new modules get documented automatically. No hand-written pages to update.
3. **Lightweight** — 2 small plugins (`mkdocs-gen-files`, `mkdocs-literate-nav`) and a ~25-line script. This is the standard, documented pattern.
4. **Prose overlays still possible** — individual module pages can have hand-written introductions above the autodoc directive if needed. Auto-gen doesn't preclude curation.

**Dependencies:**

| Package | Purpose |
|---------|---------|
| `mkdocs-gen-files` | Generate API reference pages at build time |
| `mkdocs-literate-nav` | Auto-generate nav from directory structure |

_Source: [mkdocstrings recipes](https://mkdocstrings.github.io/recipes/)_

### Autodoc Syntax in Markdown Pages

The `::: identifier` syntax injects documentation for any Python object:

```markdown
<!-- Document a module -->
::: docvet.checks.enrichment

<!-- Document a specific function -->
::: docvet.checks.enrichment.check_enrichment

<!-- Document a class with options -->
::: docvet.config.DocvetConfig
    options:
      show_root_heading: true
      members:
        - fail_on
        - warn_on
```

Options can be set globally (in mkdocs.yml) and overridden per-object in the markdown page. This gives fine-grained control over what each API reference page shows.

### Cross-Reference and Inventory Integration

mkdocstrings generates a Sphinx-compatible `objects.inv` file, enabling cross-references:

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          inventories:
            - https://docs.python.org/3/objects.inv
```

This allows linking to Python stdlib docs from docvet's API reference — e.g., references to `ast.Module` or `pathlib.Path` in type annotations will auto-link to Python's documentation.

### Glossary/Tooltips Integration with Docvet's mkdocs Setup

**mkdocs.yml additions:**

```yaml
theme:
  features:
    - content.tooltips        # NEW: styled tooltip rendering
    # ... existing features

markdown_extensions:
  - abbr                       # NEW: abbreviation support
  - pymdownx.snippets:         # NEW: auto-append glossary
      auto_append:
        - includes/abbreviations.md
  # ... existing extensions

watch:
  - includes                   # NEW: auto-reload glossary during dev
```

**Glossary file:** `includes/abbreviations.md` (outside `docs/` folder):

```markdown
*[docstring]: A string literal placed at the beginning of a module, class, method, or function to document it
*[AST]: Abstract Syntax Tree — Python's parsed representation of source code
*[CC]: Cognitive Complexity — a measure of how difficult code is to understand
*[griffe]: A Python documentation framework that extracts information from source code
*[mkdocstrings]: An MkDocs plugin for automatic API documentation generation
*[enrichment]: Docvet's check for missing docstring sections (Raises, Yields, Attributes, etc.)
*[freshness]: Docvet's check for stale docstrings that haven't been updated with code changes
```

Every occurrence of these terms on any page will automatically show a tooltip with the definition. No per-page configuration needed.

**Integration with existing setup:** The `attr_list` extension is already in docvet's mkdocs.yml. Only `abbr` and `pymdownx.snippets` need to be added. The `includes/` directory sits at project root alongside `docs/` and `src/`.

### Complete mkdocs.yml Diff (What Changes for Epic 13)

```yaml
# ADDITIONS to existing mkdocs.yml:

theme:
  features:
    - content.tooltips          # ADD

plugins:
  - gen-files:                    # ADD — auto-generate API reference pages
      scripts:
        - scripts/gen_ref_pages.py
  - literate-nav:                 # ADD — auto-generate nav from SUMMARY.md
      nav_file: SUMMARY.md
  - mkdocstrings:                 # ADD — render API docs from docstrings
      handlers:
        python:
          paths: [src]
          inventories:
            - https://docs.python.org/3/objects.inv
          options:
            docstring_style: google
            docstring_section_style: table
            show_root_heading: true
            show_root_full_path: false
            show_symbol_type_heading: true
            show_source: true
            show_signature_annotations: true
            separate_signature: true
            merge_init_into_class: true
            summary: true
            filters: ["!^_"]

markdown_extensions:
  - abbr                        # ADD
  - pymdownx.snippets:          # ADD
      auto_append:
        - includes/abbreviations.md

watch:
  - includes                    # ADD

nav:
  # API Reference section auto-generated by literate-nav from SUMMARY.md
  # Glossary page added manually:
  - Glossary: glossary.md
```

**No existing configuration is removed or modified** — all changes are additive.

## Architectural Patterns and Design

### Documentation Site Architecture: Hybrid Model

Docvet's docs site should follow the **hybrid documentation pattern** — hand-written guides for conceptual content + auto-generated API reference for code documentation. This is the dominant pattern in mature Python projects using mkdocs-material.

**Current site structure (Epic 11):**

```
docs/site/
  index.md                    # Getting Started (hand-written)
  checks/                     # Check pages (hand-written, template-driven)
    enrichment.md
    freshness.md
    coverage.md
    griffe.md
  rules/                      # Rule pages (hand-written, YAML catalog + macros)
    missing-raises.md
    ... (19 rule pages)
  configuration.md            # Configuration reference (hand-written)
  cli-reference.md            # CLI reference (hand-written)
```

**Proposed Epic 13 additions:**

```
docs/site/
  ... (existing, unchanged)
  glossary.md                 # NEW: glossary page with term definitions
  api/                        # AUTO-GENERATED at build time by gen_ref_pages.py
    SUMMARY.md                # Auto-generated nav (literate-nav reads this)
    docvet.md                 # Package overview (auto-generated)
    docvet/
      cli.md                  # Auto-generated from src/docvet/cli.py
      config.md               # Auto-generated from src/docvet/config.py
      discovery.md            # Auto-generated from src/docvet/discovery.py
      ast_utils.md            # Auto-generated from src/docvet/ast_utils.py
      reporting.md            # Auto-generated from src/docvet/reporting.py
      checks/
        enrichment.md         # Auto-generated from src/docvet/checks/enrichment.py
        freshness.md          # Auto-generated from src/docvet/checks/freshness.py
        coverage.md           # Auto-generated from src/docvet/checks/coverage.py
        griffe_compat.md      # Auto-generated from src/docvet/checks/griffe_compat.py
scripts/
  gen_ref_pages.py            # NEW: ~25-line build script (mkdocstrings recipe)
includes/
  abbreviations.md            # NEW: glossary definitions (outside docs/)
```

Note: The `docs/site/api/` pages are generated at build time — they don't exist in the repo. The `scripts/gen_ref_pages.py` script walks `src/docvet/` and creates them dynamically.

### Design Decision: Auto-Generated API Pages

**Decision: Auto-generated pages using `mkdocs-gen-files` + `mkdocs-literate-nav`.** Rationale:

1. **Showcase value** — docvet is a documentation quality tool. The entire Epic 9 dogfooding pass invested in genuine, complete docstrings. Auto-generating the API reference from those docstrings *is the proof* that the six-layer model works. A visitor sees pristine auto-generated docs and thinks: "if docvet makes their own docs look like this, imagine what it'll do for mine."
2. **Zero maintenance** — new modules are auto-discovered. No hand-written stubs to keep in sync.
3. **Lightweight cost** — 2 small plugins and a ~25-line script. This is the [official mkdocstrings recipe](https://mkdocstrings.github.io/recipes/), not a custom solution.
4. **Curation still possible** — individual pages can have prose overlays above the autodoc directive if needed. Auto-gen doesn't preclude editorial polish where it adds value.

### Design Decision: Glossary Approach

**Decision: Built-in abbreviations + snippets.** Rationale:

1. **Zero new dependencies** — uses extensions already bundled with pymdownx
2. **Project-wide automatic matching** — every page gets tooltips without per-page work
3. **Consistent with mkdocs-material's own documentation pattern** — the official docs use this exact approach
4. **Good enough for docvet's domain** — ~20-30 domain terms (docstring, AST, CC, enrichment, freshness, etc.)
5. **Limitation accepted:** Exact text matching only (no fuzzy/plural matching). Mitigated by defining both singular and plural forms where needed

### Docstring Quality for Rendering

Griffe/mkdocstrings has specific recommendations that align well with docvet's existing conventions:

**Already in place (from Epic 9 dogfooding):**
- Google-style docstrings on all public symbols
- Complete sections: Args, Returns, Raises, Yields, Examples, Attributes
- Type annotations on all function signatures
- `from __future__ import annotations` in every file

**Minor adjustments for optimal rendering:**
- Use plural "Examples:" section header (not singular "Example:") — griffe treats singular as an admonition
- Ensure parameter descriptions are complete sentences with punctuation
- Code examples in docstrings should use `>>>` pycon format for automatic syntax highlighting
- Cross-references use `[identifier][fully.qualified.name]` markdown link syntax

**Confidence: HIGH** — docvet's docstrings are already high-quality from Epic 9's dogfooding pass. Minimal adjustments needed for rendering.

_Sources: [Griffe docstring recommendations](https://mkdocstrings.github.io/griffe/guide/users/recommendations/docstrings/), [mkdocstrings recipes](https://mkdocstrings.github.io/recipes/), [mkdocstrings-python usage](https://mkdocstrings.github.io/python/usage/)_

### Navigation Architecture

The API Reference navigation is auto-generated by `literate-nav` from the `SUMMARY.md` file that `gen_ref_pages.py` creates at build time. The hand-written nav sections (Checks, Rules, Configuration, CLI Reference, Glossary) remain in `mkdocs.yml` as-is.

**How literate-nav integrates with existing nav:** The `nav_file: SUMMARY.md` setting tells `literate-nav` to read the auto-generated `SUMMARY.md` for the API Reference section. Other nav entries in `mkdocs.yml` are unaffected — they coexist with the auto-generated section.

The API Reference tab sits naturally between the rule reference (user-facing) and the configuration reference (developer-facing). The glossary sits last as a reference resource.

### Build Pipeline Architecture

```
Source code (src/docvet/)
    ↓ gen_ref_pages.py discovers modules
Auto-generated ::: stub pages + SUMMARY.md
    ↓ griffe parses source
Docstring AST
    ↓ mkdocstrings renders
API reference HTML pages

Glossary definitions (includes/abbreviations.md)
    ↓ pymdownx.snippets auto-appends
Every page gets tooltip definitions → abbr extension matches terms → content.tooltips renders styled tooltips
```

All three pipelines (gen-files → mkdocstrings → glossary) are independent and compose cleanly. The gen-files script runs first (generates stub pages), mkdocstrings runs second (renders docstrings into those pages), and snippets runs on all pages (including the auto-generated API pages, so glossary tooltips appear in API docs too).

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| mkdocstrings/macros plugin conflict | LOW | LOW | Known issue documented; macros only used in rule pages, not docstrings |
| griffe version conflict (docvet optional dep vs mkdocstrings dep) | LOW | MEDIUM | Both use griffe; version ranges should overlap; test during setup |
| Tooltip matching false positives (common words matching glossary terms) | MEDIUM | LOW | Use specific terms, not common English words; review after first build |
| Build time increase | LOW | LOW | mkdocstrings adds seconds, not minutes; glossary is negligible |
| `mkdocs build --strict` breaks with mkdocstrings warnings | MEDIUM | LOW | Set `show_if_no_docstring: false` and fix any griffe warnings (already covered by docvet's griffe_compat check) |
| gen-files script discovers unintended modules | LOW | LOW | `filters: ["!^_"]` hides private modules; script can exclude specific paths |
| literate-nav SUMMARY.md conflicts with existing nav | LOW | MEDIUM | Test plugin ordering; literate-nav only controls API Reference section |

## Implementation Approaches and Technology Adoption

### Dependency Additions

All new dependencies are dev-only — they do not affect the published `docvet` package:

```bash
uv add --dev "mkdocstrings[python]>=0.18" mkdocs-gen-files mkdocs-literate-nav
```

**pyproject.toml impact:**

| Dependency | Purpose | Conflict Risk |
|-----------|---------|--------------|
| `mkdocstrings[python]` | API reference rendering (brings griffe) | LOW — griffe already an optional dep |
| `mkdocs-gen-files` | Auto-generate API reference pages at build time | NONE — standalone plugin |
| `mkdocs-literate-nav` | Auto-generate nav from SUMMARY.md | NONE — standalone plugin |
| (no new deps for glossary) | Built-in pymdownx extensions | NONE — already bundled with mkdocs-material |

**Confidence: HIGH** — all three packages are part of the official mkdocstrings ecosystem and documented in the [mkdocstrings recipes](https://mkdocstrings.github.io/recipes/). They are the standard stack for auto-generated API reference with mkdocs.

_Sources: [mkdocstrings-python overview](https://mkdocstrings.github.io/python/), [mkdocstrings recipes](https://mkdocstrings.github.io/recipes/)_

### Story-by-Story Implementation Roadmap

Epic 13 has 3 stories in backlog. Here's the recommended implementation approach for each, informed by this research:

#### Story 13.1: Domain Glossary with Inline Tooltips

**Scope:** Glossary page + tooltip rendering across all existing pages.

**Implementation steps:**
1. Create `includes/abbreviations.md` with ~20-30 docvet domain terms (docstring, AST, CC, enrichment, freshness, drift, diff, griffe, mkdocstrings, etc.)
2. Create `docs/site/glossary.md` — a hand-written page with full definitions for each term, organized by category (docstring concepts, check types, infrastructure)
3. Add `abbr` and `pymdownx.snippets` (with `auto_append`) to `mkdocs.yml` markdown_extensions
4. Add `content.tooltips` to theme features
5. Add `watch: [includes]` for live-reload during development
6. Run `mkdocs build --strict` — verify tooltips render on existing pages
7. Run `mkdocs serve` — visually inspect tooltip rendering on several pages

**New files:** `includes/abbreviations.md`, `docs/site/glossary.md`
**Modified files:** `mkdocs.yml`
**Dependencies added:** None
**Quality gate:** `mkdocs build --strict` passes, tooltips visible on at least 3 existing pages

**Complexity: LOW** — zero new dependencies, additive config changes only, no interaction with existing macros or rule pages.

#### Story 13.2: Auto-Generated API Reference

**Scope:** mkdocstrings + gen-files + literate-nav integration for fully auto-generated API reference.

**Implementation steps:**
1. `uv add --dev "mkdocstrings[python]>=0.18" mkdocs-gen-files mkdocs-literate-nav` — install all API reference dependencies
2. Create `scripts/gen_ref_pages.py` — the ~25-line build script from the [official mkdocstrings recipe](https://mkdocstrings.github.io/recipes/) that walks `src/docvet/` and generates `::: module.name` stub pages + `SUMMARY.md` at build time
3. Add `gen-files`, `literate-nav`, and `mkdocstrings` plugin blocks to `mkdocs.yml` (after `macros` plugin, in correct order)
4. Configure mkdocstrings handler with full options (google style, table sections, show source, show annotations, merge init, summary, filter privates)
5. Add Python stdlib inventory (`objects.inv`) for cross-references
6. Run `mkdocs build --strict` — verify all modules auto-discovered and rendered without warnings
7. Run `mkdocs serve` — visually inspect API reference pages, verify cross-references to Python stdlib
8. Verify glossary tooltips appear on API reference pages (from Story 13.1's abbreviations)

**New files:** `scripts/gen_ref_pages.py` (~25 lines)
**Modified files:** `mkdocs.yml`, `pyproject.toml` (3 dev dependencies)
**Dependencies added:** `mkdocstrings[python]`, `mkdocs-gen-files`, `mkdocs-literate-nav`
**Quality gate:** `mkdocs build --strict` passes, all public modules auto-discovered and rendered with full docstring sections

**Complexity: MEDIUM** — 3 new dependencies but all from the standard mkdocstrings ecosystem. The gen_ref_pages.py script is a well-documented recipe. The main risk is griffe warnings on edge-case docstrings — mitigated by docvet's own `griffe_compat` check already running clean.

#### Story 13.3: GitHub Pages Deployment

**Scope:** CI/CD workflow to auto-deploy docs site on push to main.

**Implementation steps:**
1. Create `.github/workflows/docs.yml` — GitHub Actions workflow for mkdocs deployment
2. Trigger: push to `main` branch (matches release flow — docs deploy alongside releases)
3. Use `actions/setup-python@v5` + `pip install mkdocs-material mkdocstrings[python]`
4. Cache `~/.cache` with weekly rotation (`%V` date format)
5. Run `mkdocs gh-deploy --force` to publish to `gh-pages` branch
6. Configure GitHub repo settings: Pages source → `gh-pages` branch
7. Optionally configure custom domain if desired
8. Verify deployment at `https://<username>.github.io/docvet/`

**GitHub Actions workflow (adapted from mkdocs-material official docs):**

```yaml
name: docs
on:
  push:
    branches:
      - main
permissions:
  contents: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: echo "cache_id=$(date --utc '+%V')" >> $GITHUB_ENV
      - uses: actions/cache@v4
        with:
          key: mkdocs-material-${{ env.cache_id }}
          path: ~/.cache
          restore-keys: |
            mkdocs-material-
      - run: pip install mkdocs-material "mkdocstrings[python]" mkdocs-gen-files mkdocs-literate-nav mkdocs-macros-plugin
      - run: mkdocs gh-deploy --force
```

**New files:** `.github/workflows/docs.yml`
**Modified files:** None (GitHub repo settings changed via UI)
**Dependencies added:** None (workflow installs its own deps)
**Quality gate:** Workflow succeeds, site accessible at GitHub Pages URL

**Complexity: LOW** — standard GitHub Actions pattern, well-documented by mkdocs-material. The main consideration is ensuring all build deps (material, mkdocstrings, macros) are installed in the workflow.

_Sources: [Material publishing guide](https://squidfunk.github.io/mkdocs-material/publishing-your-site/), [MkDocs deployment](https://www.mkdocs.org/user-guide/deploying-your-docs/)_

### Testing and Quality Assurance

**Build-time validation:**
- `mkdocs build --strict` catches all rendering warnings (missing references, broken links, malformed directives)
- This is already the established quality gate from Epic 11 — no new testing infrastructure needed

**Glossary validation:**
- Visual inspection during `mkdocs serve` — verify tooltips appear on key terms
- Check that abbreviation definitions don't match unintended text (false positives)
- Both singular and plural forms of key terms should be defined

**API reference validation:**
- Every public module should be auto-discovered by `gen_ref_pages.py` and rendered without griffe warnings
- Already enforced by `docvet griffe --all` — docvet's own griffe_compat check runs clean
- Cross-references to Python stdlib should resolve (verify `ast.Module`, `pathlib.Path` links work)
- `filters: ["!^_"]` should hide private members — verify no internal helpers leak through
- Verify `SUMMARY.md` nav structure is correct (literate-nav generates this from gen-files output)

**Deployment validation:**
- Workflow succeeds on push to main
- Site accessible and navigable at GitHub Pages URL
- All nav links work (no 404s on deployed site)

### Deployment and Operations

**Deployment model:** Static site generation with GitHub Pages. Zero runtime infrastructure — the site is built at deploy time and served as static files.

**Trigger:** Docs deploy on every push to `main` (same cadence as releases). Since docvet uses `develop → main` merge flow, docs update whenever a release happens.

**Rollback:** GitHub Pages serves from `gh-pages` branch. To rollback, revert the branch or re-run the workflow on a previous commit. The `--force` flag in `mkdocs gh-deploy` overwrites the previous deployment.

**Monitoring:** GitHub Actions provides build status. A failing docs build does not block releases — the workflow runs independently of the release pipeline.

### Cost and Resource Impact

| Resource | Impact |
|----------|--------|
| Build time | +10-30 seconds (mkdocstrings parsing) |
| Dev dependencies | +3 packages (`mkdocstrings[python]`, `mkdocs-gen-files`, `mkdocs-literate-nav`) |
| CI minutes | +1-2 min per main push (docs workflow) |
| Storage | Negligible (static HTML on gh-pages branch) |
| Maintenance | Low — stable plugins, additive changes only |

No operational costs — GitHub Pages is free for public repositories.

## Technical Research Recommendations

### Implementation Roadmap

**Recommended story order:** 13.1 → 13.2 → 13.3

| Order | Story | Rationale |
|-------|-------|-----------|
| 1st | 13.1 (Glossary + Tooltips) | Zero new deps, lowest risk, immediate visual impact on existing pages |
| 2nd | 13.2 (API Reference) | New dependency, most content creation, benefits from glossary tooltips on API pages |
| 3rd | 13.3 (GitHub Pages) | Deploy last — all content should be in place before publishing |

This mirrors the Epic 12 retro recommendation and follows the progressive build pattern (foundation → content → deploy).

### Technology Stack Recommendations

| Decision | Recommendation | Confidence |
|----------|---------------|------------|
| API docs plugin | mkdocstrings with Python handler | HIGH |
| API page strategy | Auto-generated (gen-files + literate-nav) | HIGH |
| Glossary/tooltips | Built-in abbreviations + snippets | HIGH |
| Deployment target | GitHub Pages via gh-pages branch | HIGH |
| CI trigger | Push to main (release cadence) | HIGH |

**Zero third-party plugins for glossary.** The built-in mkdocs-material abbreviations + pymdownx.snippets pattern is simpler, has zero dependencies, and is the pattern recommended by mkdocs-material's own documentation.

**Auto-generated API pages.** Docvet is a documentation quality tool — auto-generating pristine API docs from its own dogfooded docstrings is the proof that the tool works. The gen-files + literate-nav + mkdocstrings stack is the official recipe, adds only 2 lightweight plugins, and requires zero maintenance when modules change. This is the showcase: the machine turns docvet's docstrings into beautiful documentation automatically.

### Success Metrics

| Metric | Target |
|--------|--------|
| `mkdocs build --strict` | Zero warnings |
| Glossary terms with tooltips | 20+ domain terms |
| API modules documented | All public modules (7+) |
| Docstring sections rendered | All Google-style sections (Params, Returns, Raises, Yields, Examples, Attributes) |
| Deployment | Auto-deploy on push to main |
| Site accessibility | Public URL at GitHub Pages |

### Docvet Showcase Value

This is the "prove our own value" epic. The docs site should demonstrate:

1. **Docvet's own docstrings are complete** — the API reference will display rich, full docstrings because Epic 9's dogfooding made them complete
2. **Every section matters** — Raises, Yields, Attributes, Examples all render beautifully because mkdocstrings/griffe supports every section docvet checks for
3. **The six-layer model works** — from interrogate (presence) through docvet (completeness, accuracy, rendering, visibility) to mkdocstrings (display), the full pipeline produces professional documentation
4. **Recommended mkdocs settings** — the mkdocs.yml configuration itself becomes a reference for other projects using docvet with mkdocs-material

_Sources: [mkdocstrings-python](https://mkdocstrings.github.io/python/), [Material tooltips](https://squidfunk.github.io/mkdocs-material/reference/tooltips/), [Material publishing](https://squidfunk.github.io/mkdocs-material/publishing-your-site/), [mkdocstrings recipes](https://mkdocstrings.github.io/recipes/)_
