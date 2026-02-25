---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics-docs-publish.md'
  - '_bmad-output/planning-artifacts/epics-adoption.md'
  - 'mkdocs.yml'
  - 'src/docvet/checks/enrichment.py'
  - 'docs/site/rules/missing-cross-references.md'
  - 'party-mode-session-2026-02-24-mkdocstrings-research'
---

# docvet - Epic Breakdown (Documentation Quality & Cross-Reference Linking)

## Overview

This document provides the epic and story breakdown for docvet's **Documentation Quality & Cross-Reference Linking** phase — upgrading the mkdocstrings configuration for full-featured API reference rendering, fixing cross-reference syntax in our own docstrings to produce clickable links, and tightening the `missing-cross-references` enrichment rule to enforce linkable syntax. The docs site is live (Epic 13), all 19 rules are implemented, and the tool is published (v1.1.2 on PyPI). This phase closes the gap between "having cross-references" and "having cross-references that actually link."

## Requirements Inventory

### Functional Requirements

**mkdocstrings Configuration Enhancement:**

- FR-Q1: The mkdocstrings handler configuration must include Python stdlib inventory (`https://docs.python.org/3/objects.inv`) so that stdlib type references (`ast.AST`, `pathlib.Path`, `re.Pattern`, `subprocess.CompletedProcess`) render as clickable links to docs.python.org in the API reference
- FR-Q2: The mkdocstrings handler must enable `signature_crossrefs: true` so that type annotations in function signatures become clickable links (to stdlib docs via inventory or to internal symbols via autorefs)
- FR-Q3: The mkdocstrings handler must enable `show_signature_annotations: true` and `separate_signature: true` so that type hints are visible in rendered signatures without overflowing headings
- FR-Q4: The mkdocstrings handler must enable `show_symbol_type_heading: true` and `show_symbol_type_toc: true` so that symbol type badges (function, class, module, attribute) appear next to headings and TOC entries for scanability
- FR-Q5: The mkdocstrings handler must enable `modernize_annotations: true` so that `Union[A, B]` renders as `A | B` and `Optional[A]` as `A | None`, consistent with the project's Python 3.12+ target
- FR-Q6: The mkdocstrings handler must enable `annotations_path: brief` so that type names show short form with tooltip for full path, leveraging the `content.tooltips` feature already enabled in the theme
- FR-Q7: The mkdocstrings handler must set `members_order: source`, `group_by_category: true`, and `show_category_heading: true` so that API reference pages match code reading order and group symbols by type with headings
- FR-Q8: The mkdocstrings handler must set `merge_init_into_class: true` with `docstring_options.ignore_init_summary: true` so that `__init__` parameters fold into class documentation, eliminating redundant init sections
- FR-Q9: The mkdocstrings handler must set `line_length: 88` to match the project's ruff formatter target for consistent signature wrapping

**Cross-Reference Syntax Fix (Own Codebase):**

- FR-Q10: All See Also sections in module docstrings (~12 files) must use mkdocstrings cross-reference bracket syntax (`[`identifier`][]`) instead of plain backtick syntax (`` `identifier` ``) so that references render as clickable hyperlinks in the API reference
- FR-Q11: The rendered API reference must show See Also entries as clickable links that navigate to the referenced module's API reference page

**Cross-Reference Rule Enhancement:**

- FR-Q12: The `missing-cross-references` enrichment rule must be updated to require linkable cross-reference syntax — plain backtick identifiers (`` `module.name` ``) must no longer satisfy the rule, only bracket-style references (`[identifier][]`, `[text][identifier]`) and Sphinx roles (`:func:`, `:class:`, etc.)
- FR-Q13: The rule documentation page (`docs/site/rules/missing-cross-references.md`) must be updated to show bracket syntax in the "Fix" example and explain why bracket syntax matters for mkdocstrings rendering
- FR-Q14: All tests for the `missing-cross-references` rule must be updated to reflect the tightened syntax requirement — backtick-only See Also entries must now produce findings

### NonFunctional Requirements

- NFR-Q1: The docs site must build successfully with `mkdocs build --strict` after all configuration changes — zero warnings, zero broken cross-references
- NFR-Q2: All 729+ existing tests must continue passing after the rule behavior change
- NFR-Q3: The stdlib inventory fetch must not break offline builds — mkdocstrings caches the inventory after first fetch, and the build degrades gracefully (unresolved references render as plain text) if the inventory is unavailable
- NFR-Q4: The `docstring_section_style` option must be evaluated visually during implementation — choose `list` or `table` (default) based on which renders better for docvet's parameter documentation patterns
- NFR-Q5: The `show_source` option must remain `true` (default) — docvet is a developer tool and source visibility is a feature
- NFR-Q6: During code review for each story, run `analyze_code_snippet` (SonarQube MCP tool) against all modified `src/` files — report any HIGH or BLOCKER severity findings before merge. Update the BMAD code-review checklist (`checklist.md`) and instructions (`instructions.xml`) to include this step as a cross-cutting improvement for all future epics.
- NFR-Q7: After the final story (15.3) merges to develop, run one full SonarQube scan to baseline the dashboard — verify zero new issues introduced by the epic

### Additional Requirements

**From Party Mode Discussion (2026-02-24):**

- The `autorefs` plugin ships with mkdocstrings automatically — no new plugin needed for cross-reference resolution
- Cross-reference syntax `[`identifier`][]` requires `pymdownx.inlinehilite` for code-formatted links — already enabled in `mkdocs.yml`
- All cross-references in docstrings must use fully-qualified paths (`[docvet.checks.enrichment][]`) — relative/scoped cross-references are Insiders-only (paid feature)
- The `_XREF_BACKTICK` regex pattern in `enrichment.py` line 66 is the specific code to remove from the pass condition in the rule
- The existing `_XREF_MD_LINK` pattern (`r"\[[^\]]+\]\["`) already matches bracket cross-reference syntax — no new pattern needed

**From mkdocstrings Research:**

- Single backtick `` `identifier` `` renders as `<code>` with no hyperlink — confirmed visually on the live docs site
- Bracket syntax `[identifier][]` renders as a clickable link resolved by the autorefs plugin
- Code-formatted bracket syntax `` [`identifier`][] `` renders as a clickable code-formatted link (best of both worlds)
- Inventories enable cross-project linking — stdlib inventory is the highest-value addition
- `signature_crossrefs: true` is free (not Insiders-only) and makes type annotations in signatures clickable

**From Existing PRD (relevant FRs already delivered but enhanced here):**

- FR12: "detect See Also sections where entries lack cross-reference syntax" — DELIVERED but accepts backticks which don't link
- FR-D6: "mkdocstrings renders full API docs from source docstrings using Google-style parser" — DELIVERED with minimal config, enhanced here

### FR Coverage Map

| FR | Story | Description |
|----|-------|-------------|
| FR-Q1 | 15.1 | Python stdlib inventory for cross-project linking |
| FR-Q2 | 15.1 | Signature cross-references (`signature_crossrefs`) |
| FR-Q3 | 15.1 | Signature annotations display (`show_signature_annotations`, `separate_signature`) |
| FR-Q4 | 15.1 | Symbol type badges in headings and TOC |
| FR-Q5 | 15.1 | Modern annotation syntax (`A \| B` instead of `Union[A, B]`) |
| FR-Q6 | 15.1 | Brief annotation paths with tooltips |
| FR-Q7 | 15.1 | Source-order members with category grouping |
| FR-Q8 | 15.1 | Merge `__init__` into class docs |
| FR-Q9 | 15.1 | Line length matching ruff target |
| FR-Q10 | 15.2 | Fix own See Also syntax to bracket cross-references |
| FR-Q11 | 15.2 | Verify rendered links navigate correctly |
| FR-Q12 | 15.3 | Tighten rule to require linkable syntax |
| FR-Q13 | 15.3 | Update rule docs with bracket syntax example |
| FR-Q14 | 15.3 | Update tests for tightened rule behavior |

NFR coverage: NFR-Q1 (cross-cutting, all stories), NFR-Q2 (Story 15.3), NFR-Q3 (Story 15.1), NFR-Q4 (Story 15.1), NFR-Q5 (Story 15.1), NFR-Q6 (cross-cutting, code review for all stories + workflow update in 15.1), NFR-Q7 (post-15.3 merge).

## Epic List

### Epic 15: Documentation Quality & Cross-Reference Linking

**Goal:** The docvet API reference renders with full-featured mkdocstrings output — clickable type annotations, stdlib cross-links, symbol type badges, and navigable See Also sections — while the `missing-cross-references` rule enforces syntax that actually produces links in rendered documentation.

**User Value:** A developer browsing the docvet API reference can click type annotations to navigate to Python stdlib docs, click See Also entries to jump between modules, and see symbol types at a glance. A developer using docvet on their own project gets a rule that catches cross-references that *look* like links but don't actually link in mkdocstrings.

**Dependencies:** Epic 13 (docs site deployed), Epic 14 (marketplace published). All prerequisites satisfied.

**Recommended Story Order:** 15.1 → 15.2 → 15.3

- **15.1 first**: Configuration changes that enable all the rendering features — no source code changes to `src/`
- **15.2 after config**: Fix our own See Also syntax to use bracket references — depends on 15.1's config for the links to actually resolve
- **15.3 last**: Tighten the rule only after our own codebase passes with bracket syntax — avoids `docvet check --all` failing on itself

| Story | Theme | FRs Covered | Scope |
|-------|-------|-------------|-------|
| 15.1 | mkdocstrings Config Overhaul | FR-Q1 through FR-Q9 | `mkdocs.yml` handler options, stdlib inventory, visual verification |
| 15.2 | Fix Own Cross-Reference Syntax | FR-Q10, FR-Q11 | ~12 module docstrings, See Also bracket syntax |
| 15.3 | Tighten Cross-Reference Rule | FR-Q12, FR-Q13, FR-Q14 | `enrichment.py` rule logic, rule docs, test updates |

## Epic 15: Documentation Quality & Cross-Reference Linking

### Story 15.1: mkdocstrings Configuration Overhaul

As a **developer browsing the docvet API reference**,
I want **type annotations rendered as clickable links, symbol type badges on headings, and stdlib types linking to Python docs**,
So that **the API reference is a navigable, information-rich resource rather than a flat text dump**.

**Acceptance Criteria:**

AC 1:
**Given** the `mkdocs.yml` mkdocstrings handler has minimal options (`docstring_style`, `show_root_heading`, `show_root_full_path`)
**When** the Python stdlib inventory is added (`https://docs.python.org/3/objects.inv`)
**Then** stdlib types referenced in docstrings and signatures (e.g., `ast.Module`, `pathlib.Path`, `re.Pattern`) render as clickable links to docs.python.org in the built site

AC 2:
**Given** the mkdocstrings handler options are updated
**When** `signature_crossrefs: true` and `show_signature_annotations: true` are enabled
**Then** function signatures in the API reference show type annotations as clickable links — internal types link to their API reference page, stdlib types link to docs.python.org via the inventory

AC 3:
**Given** the mkdocstrings handler options are updated
**When** `separate_signature: true` is enabled
**Then** long function signatures render in their own code block below the heading, preventing heading overflow on narrow viewports

AC 4:
**Given** the mkdocstrings handler options are updated
**When** `show_symbol_type_heading: true` and `show_symbol_type_toc: true` are enabled
**Then** API reference headings and TOC entries show type badges (function, class, module, attribute) for visual scanning

AC 5:
**Given** the mkdocstrings handler options are updated
**When** `modernize_annotations: true` and `annotations_path: brief` are enabled
**Then** type annotations render in modern syntax (`A | B` instead of `Union[A, B]`) with short names and full-path tooltips on hover

AC 6:
**Given** the mkdocstrings handler options are updated
**When** `members_order: source`, `group_by_category: true`, and `show_category_heading: true` are enabled
**Then** API reference pages list members in source-code order, grouped by type (attributes, classes, functions) with headings for each group

AC 7:
**Given** the mkdocstrings handler options are updated
**When** `merge_init_into_class: true` with `docstring_options.ignore_init_summary: true` is enabled
**Then** class pages show `__init__` parameters as part of the class documentation, not as a separate `__init__` method section

AC 8:
**Given** the mkdocstrings handler sets `line_length: 88`
**When** function signatures are rendered
**Then** signature wrapping matches the project's ruff formatter target for visual consistency

AC 9:
**Given** all configuration changes are applied
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings and zero broken cross-references (NFR-Q1)

AC 10:
**Given** the `docstring_section_style` option
**When** the developer evaluates `list` vs `table` rendering visually
**Then** the option that produces better readability for docvet's parameter documentation is selected and documented in the commit message (NFR-Q4)

**FRs covered:** FR-Q1, FR-Q2, FR-Q3, FR-Q4, FR-Q5, FR-Q6, FR-Q7, FR-Q8, FR-Q9
**NFRs covered:** NFR-Q1, NFR-Q3, NFR-Q4, NFR-Q5, NFR-Q6 (code-review workflow update)

---

### Story 15.2: Fix Own Cross-Reference Syntax

As a **developer reading docvet's API reference**,
I want **See Also entries to be clickable links that navigate to the referenced module's documentation page**,
So that **I can navigate between related modules without manually searching the sidebar**.

**Dependencies:** Story 15.1 (mkdocstrings config must be in place for bracket references to resolve as links)

**Acceptance Criteria:**

AC 1:
**Given** module docstrings across ~12 files use plain backtick syntax in See Also sections (e.g., `` `docvet.checks` ``)
**When** all See Also entries are converted to mkdocstrings bracket cross-reference syntax (e.g., `` [`docvet.checks`][] ``)
**Then** every See Also entry uses the `` [`fully.qualified.name`][] `` format consistently

AC 2:
**Given** the See Also entries use bracket syntax
**When** the docs site is built and a developer views a module's API reference page
**Then** each See Also entry renders as a clickable code-formatted hyperlink that navigates to the referenced module's API reference page

AC 3:
**Given** the cross-references use fully-qualified module paths
**When** `mkdocs build --strict` is executed
**Then** all cross-references resolve successfully with zero "could not find" warnings

AC 4:
**Given** all See Also entries are updated
**When** `docvet check --all` is executed against the updated codebase
**Then** the `missing-cross-references` rule produces zero findings (bracket syntax satisfies the existing `_XREF_MD_LINK` pattern)

AC 5:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all existing tests pass with zero failures

**Files to update (See Also sections):**
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

**FRs covered:** FR-Q10, FR-Q11
**NFRs covered:** NFR-Q1

---

### Story 15.3: Tighten Cross-Reference Rule to Require Linkable Syntax

As a **Python developer using docvet to enforce docstring quality**,
I want **the `missing-cross-references` rule to flag See Also entries that use plain backtick syntax (which doesn't produce clickable links in mkdocstrings)**,
So that **my documentation cross-references actually navigate when rendered, not just look like code**.

**Dependencies:** Story 15.2 (own codebase must pass with bracket syntax before tightening the rule)

**Acceptance Criteria:**

AC 1:
**Given** the `_check_missing_cross_references` function in `enrichment.py` currently accepts `_XREF_BACKTICK` (`` r"`[^`]+`" ``) as valid cross-reference syntax
**When** the `_XREF_BACKTICK` pattern is removed from the pass condition (line 1178)
**Then** See Also sections containing only plain backtick references (e.g., `` `docvet.checks` ``) produce a `missing-cross-references` finding
**And** See Also sections containing bracket references (`[docvet.checks][]`) or Sphinx roles (`:func:`docvet.checks``) continue to pass

AC 2:
**Given** the rule logic is updated
**When** a See Also section contains `` [`docvet.checks`][] `` (backtick content inside bracket reference)
**Then** the rule passes — the `_XREF_MD_LINK` pattern matches the bracket syntax regardless of backtick content inside

AC 3:
**Given** the rule documentation at `docs/site/rules/missing-cross-references.md`
**When** the "Fix" example is updated
**Then** it shows bracket cross-reference syntax (`` [`myapp.utils.parsing`][] ``) instead of plain backtick syntax
**And** the "What it detects" section explains that plain backtick syntax doesn't produce clickable links in mkdocstrings

AC 4:
**Given** the existing test `test_cross_refs_when_see_also_with_backtick_xrefs_returns_none`
**When** the test is updated to reflect the tightened rule
**Then** the test is renamed to `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding` (name must match new behavior)
**And** it asserts that backtick-only See Also entries now produce a finding (not `None`)
**And** a new test verifies that bracket syntax See Also entries return `None` (pass)

AC 5:
**Given** all rule changes are applied
**When** `docvet check --all` is executed against the docvet codebase
**Then** zero findings are produced (own codebase was already fixed in Story 15.2)

AC 6:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass with zero failures (NFR-Q2)

**Implementation notes:**
- Remove `_XREF_BACKTICK.search(line)` from the `or` chain at line 1178 of `enrichment.py`
- The `_XREF_BACKTICK` constant itself can remain (or be removed) — it's only used in one place
- Rename `test_cross_refs_when_see_also_with_backtick_xrefs_returns_none` → `test_cross_refs_when_see_also_with_backtick_xrefs_returns_finding` and update assertion to expect a finding
- Add `test_cross_refs_when_see_also_with_bracket_xrefs_returns_none` for bracket syntax
- Add `test_cross_refs_when_see_also_with_code_bracket_xrefs_returns_none` for `` [`id`][] `` syntax

**FRs covered:** FR-Q12, FR-Q13, FR-Q14
**NFRs covered:** NFR-Q1, NFR-Q2
