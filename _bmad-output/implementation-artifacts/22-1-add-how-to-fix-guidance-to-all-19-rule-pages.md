# Story 22.1: Add "How to Fix" Guidance to All 19 Rule Pages

Status: done
Branch: `feat/docs-22-1-how-to-fix-rule-pages`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer or AI agent that receives a docvet finding,
I want each rule page to include a concrete "How to Fix" section with a correct code example,
so that I can resolve findings without searching for documentation conventions elsewhere.

## Acceptance Criteria

1. **Given** the `rules.yml` data source exists with entries for all 19 rules, **When** a `fix` field is added to each rule entry containing a before/after code example, **Then** every rule in `rules.yml` has a non-empty `fix` field with Google-style docstring examples.

2. **Given** the rule page template renders rule data from `rules.yml`, **When** a rule page is generated, **Then** a "How to Fix" section appears with the `fix` content rendered as a fenced code block.

3. **Given** all 19 rule pages are regenerated, **When** a user or agent visits any rule page (e.g., `missing-raises`, `stale-signature`, `griffe-unknown-param`, `missing-init`), **Then** each page displays a "How to Fix" section with a concrete, correct docstring example following Google-style conventions (NFR77).

## Tasks / Subtasks

- [x] Task 1: Extend `rules.yml` schema with `fix` field (AC: #1)
  - [x] 1.1: Add `fix` field to all 10 enrichment rules — short pattern snippets showing the docstring section to add (not full function examples)
  - [x] 1.2: Add `fix` field to all 5 freshness rules — process guidance text (review and update docstring)
  - [x] 1.3: Add `fix` field to all 3 griffe rules — format correction snippets
  - [x] 1.4: Add `fix` field to `missing-init` coverage rule — file creation instruction
- [x] Task 2: Add `rule_fix` macro to `docs/main.py` (AC: #2)
  - [x] 2.1: Create `rule_fix()` macro that reads the `fix` field for the current page's rule
  - [x] 2.2: Return markdown rendering with "## How to Fix" heading and the fix content
- [x] Task 3: Add `{{ rule_fix() }}` call to all 19 rule pages (AC: #2, #3)
  - [x] 3.1: Add macro call **before** the `## Example` section in all 19 rule .md files (reading flow: detect → why → fix → example)
- [x] Task 4: Verify docs build and rendering (AC: #3)
  - [x] 4.1: Run `mkdocs build --strict` to verify zero build errors
  - [x] 4.2: Spot-check representative pages from each check type (enrichment, freshness, griffe, coverage)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: `python -c "import yaml; ..."` verified all 19 rules have non-empty `fix` field | PASS |
| 2 | Manual: `mkdocs build --strict` succeeds; `rule_fix` macro registered; "How to Fix" in built HTML | PASS |
| 3 | Manual: spot-checked `missing-raises`, `stale-signature`, `griffe-unknown-param`, `missing-init` — all render "How to Fix" | PASS |

## Dev Notes

### Implementation Approach

This story adds a data-driven "How to Fix" section to all 19 rule pages. The new section is placed **before** the existing "Example" section, creating a natural reading flow: What it detects → Why is this a problem? → **How to Fix** → Example.

**Key design decisions (party-mode consensus):**

- **No duplication**: The `fix` field contains a *short pattern snippet* (5-10 lines), not a full before/after example. The existing "Example" section with violation/fix tabs stays unchanged and provides full context.
- **Polymorphic content**: Enrichment rules get code snippets showing the docstring section to add. Freshness rules get process guidance. Griffe rules get format corrections. Coverage gets a file creation instruction.
- **Minimal YAML**: Short block scalars avoid the fragility of embedding large code blocks in YAML.

### Key Files to Modify

| File | Change |
|------|--------|
| `docs/rules.yml` | Add `fix` field (YAML block scalar) to all 19 rule entries |
| `docs/main.py` | Add `rule_fix()` macro alongside existing `rule_header()` |
| `docs/site/rules/*.md` (19 files) | Add `{{ rule_fix() }}` call **before** the `## Example` section |

### `rules.yml` Schema Extension

Current 7-field schema becomes 8 fields. The `fix` field stores **short markdown content** — a brief explanation + minimal code pattern (not a full function example). Examples by check type:

**Enrichment rule (code pattern):**
```yaml
- id: missing-raises
  name: Missing Raises Section
  check: enrichment
  # ... existing fields ...
  fix: |
    Add a `Raises:` section listing each exception type and the condition that triggers it:

    ```python
    Raises:
        ValueError: If the input path is not a .toml file.
        FileNotFoundError: If the config file does not exist.
    ```
```

**Freshness rule (process guidance):**
```yaml
- id: stale-signature
  name: Stale Signature
  check: freshness
  # ... existing fields ...
  fix: |
    The function signature changed but the docstring was not updated.
    Review the current signature (parameters, defaults, return type) and
    update the docstring `Args:`, `Returns:`, and summary to match.
```

**Coverage rule (file creation):**
```yaml
- id: missing-init
  name: Missing __init__.py
  check: coverage
  # ... existing fields ...
  fix: |
    Create an `__init__.py` file in the directory with a module docstring:

    ```python
    """Subpackage for handling configuration parsing."""
    ```
```

### `docs/main.py` Macro Design

Add a new `rule_fix()` macro registered alongside `rule_header()` inside `define_env()`. It reuses the same `rules_by_id` dict:

```python
@env.macro
def rule_fix() -> str:
    rule_id = env.page.file.name.removesuffix(".md")
    rule = rules_by_id[rule_id]
    fix_content = rule.get("fix", "")
    if not fix_content:
        return ""
    return f"## How to Fix\n\n{fix_content}\n"
```

The macro is intentionally minimal — it reads the `fix` field and wraps it with the heading. The markdown content in the YAML field handles all formatting (text, code blocks, or both). This means enrichment rules render with code snippets, freshness rules render as plain guidance text, and the macro doesn't need to know the difference.

### Rule Page Update Pattern

Each of the 19 rule `.md` files gets one line added **before** the `## Example` section. The reading flow becomes: detect → why → **fix** → example.

```markdown
## Why is this a problem?
...existing content...

{{ rule_fix() }}

## Example
...existing content (unchanged)...
```

### Fix Content Guidelines Per Check Type

Each `fix` field should be 5-10 lines: a one-sentence explanation + a minimal code pattern where applicable. Do NOT duplicate the full before/after from the existing Example section.

**Enrichment rules (10):** One sentence explaining what to add, then a minimal code snippet showing *just the docstring section* (e.g., `Raises:`, `Yields:`, `Attributes:` block) — not a full function. Example: 3-4 lines of the section header + 1-2 entries.

**Freshness rules (5):** Process guidance only, no code. Explain what to review and update (e.g., "Review the current signature and update `Args:` and `Returns:` to match"). Different for each severity level: `stale-signature` → check params/returns, `stale-body` → check behavioral description, `stale-import` → check referenced types/modules, `stale-drift`/`stale-age` → full docstring review.

**Griffe rules (3):** Format correction snippet. `griffe-unknown-param` → remove/rename the param entry. `griffe-missing-type` → add type annotation in `name (type):` format. `griffe-format-warning` → fix the specific format issue (indentation, section header).

**Coverage rule (1 — `missing-init`):** File creation instruction + minimal `__init__.py` with module docstring (3 lines).

### Architecture Constraints

- `rules.yml` is the single source of truth — the `fix` field extends the schema from 7 to 8 fields per rule [Source: architecture.md#Decision 3]
- `docs/main.py` is the only location for macros — no separate Jinja partials [Source: architecture.md#Decision 3]
- macros plugin must remain last in `mkdocs.yml` plugin order [Source: architecture.md#Pattern 6]
- Rule page filenames match Finding `rule` field values (kebab-case) [Source: architecture.md#Enforcement Rules]

### Testing Standards

This is a documentation-only story. Testing is manual:
- `mkdocs build --strict` must pass with zero warnings/errors
- Spot-check built HTML for correct rendering of "How to Fix" sections
- Verify YAML is valid (no syntax errors from block scalars)

No pytest tests needed — this story touches only `docs/` files and `docs/main.py` (which is a mkdocs plugin, not part of the docvet package).

### Project Structure Notes

- All changes are within the `docs/` boundary — no source code changes
- `docs/rules.yml` schema extension is authorized by FR144
- `docs/main.py` macro addition follows the established pattern
- No new dependencies required

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md#Story 22.1] — acceptance criteria and FRs
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 3] — rule reference page structure
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern 6] — mkdocs.yml plugin ordering
- [Source: docs/rules.yml] — current 7-field rule schema (19 entries)
- [Source: docs/main.py] — current `rule_header()` macro implementation
- [Source: docs/site/rules/missing-raises.md] — representative rule page structure
- FRs: FR143, FR144
- Issue: #155

### Documentation Impact

- Pages: All 19 `docs/site/rules/*.md` pages (content addition), `docs/rules.yml` (schema extension), `docs/main.py` (macro addition)
- Nature of update: Add "How to Fix" sections to every rule page via data-driven macro

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 879 passed, no regressions
- [x] `uv run docvet check --all` — zero findings
- [x] `uv run interrogate -v` — 100.0% coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no debugging needed.

### Completion Notes List

- Extended `docs/rules.yml` schema from 7 to 8 fields by adding `fix` block scalar to all 19 rules
- Enrichment rules (10): short pattern snippets showing the docstring section to add
- Freshness rules (5): process guidance text explaining what to review and update
- Griffe rules (3): format correction snippets with concrete examples
- Coverage rule (1): file creation instruction with minimal `__init__.py` example
- Added `rule_fix()` macro in `docs/main.py` alongside existing `rule_header()`, reusing `rules_by_id` dict
- Added `{{ rule_fix() }}` call before `## Example` in all 19 rule `.md` files
- `mkdocs build --strict` passes with zero errors; "How to Fix" renders on all 19 pages
- All quality gates pass: ruff, ty, pytest (879), docvet, interrogate (100%)

### Change Log

- 2026-02-26: Added "How to Fix" guidance sections to all 19 rule pages via data-driven `rule_fix()` macro
- 2026-02-26: Code review — 1 LOW fixed (schema comment in `rules.yml`), 3 dismissed after party-mode consensus

### File List

- `docs/rules.yml` — added `fix` field to all 19 rule entries
- `docs/main.py` — added `rule_fix()` macro
- `docs/site/rules/missing-raises.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-yields.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-receives.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-warns.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-other-parameters.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-attributes.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-typed-attributes.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-examples.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-cross-references.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/prefer-fenced-code-blocks.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/stale-signature.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/stale-body.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/stale-import.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/stale-drift.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/stale-age.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/missing-init.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/griffe-unknown-param.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/griffe-missing-type.md` — added `{{ rule_fix() }}` call
- `docs/site/rules/griffe-format-warning.md` — added `{{ rule_fix() }}` call

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approve — 1 LOW finding fixed, 3 findings dismissed after party-mode debate.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| R1 | MEDIUM | `rule_fix()` silently swallows unknown rule IDs (asymmetry with `rule_header()`) | Dismissed — `rule_header()` guards the runtime path; `rule_fix()` can never encounter an unknown rule. Merged into R2. |
| R2 | LOW | No regression guard for `fix` field presence in `rules.yml` | Fixed — added schema comment to `rules.yml` header documenting `fix` as required. |
| R3 | LOW | Module docstring uses RST `::` directive in Examples section | Dismissed — pre-existing in a file not rendered by mkdocstrings; zero user impact. |
| R4 | LOW | Untracked `rule_header()` docstring enhancement | Dismissed — improving adjacent docstrings when editing a file is expected practice. |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
