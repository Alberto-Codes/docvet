# Story 22.2: Rewrite README with AI Agent Section and Competitive Positioning

Status: done
Branch: `feat/docs-22-2-readme-ai-agent-positioning`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer or AI agent evaluating docstring quality tools,
I want the README to explain how to integrate docvet with AI coding workflows and how it compares to alternatives,
so that I can immediately understand docvet's value and adopt it.

## Acceptance Criteria

1. **Given** the current README exists, **When** an "AI Agent Integration" section is added, **Then** the section includes: a CLAUDE.md snippet showing recommended docvet configuration, a `pyproject.toml` config example with `[tool.docvet]`, and a subcommand quick reference table.

2. **Given** the README is being updated, **When** a "Why docvet?" section is added, **Then** it includes a comparison table with columns for ruff, interrogate, pydoclint, and docvet, showing coverage across the six-layer quality model (presence, style, completeness, accuracy, rendering, visibility).

3. **Given** the updated README, **When** a developer or agent reads it, **Then** both sections follow existing documentation standards (NFR78) and the README renders correctly on GitHub and PyPI.

## Tasks / Subtasks

- [x] Task 1: Add "AI Agent Integration" section to README (AC: #1)
  - [x] 1.1: Add a CLAUDE.md / agent-instructions snippet showing how to configure docvet in an AI coding workflow (e.g., "After modifying Python functions, run `docvet check` and fix all findings before committing")
  - [x] 1.2: Add a `[tool.docvet]` pyproject.toml configuration example with recommended settings for agent-assisted development
  - [x] 1.3: Add a subcommand quick reference table listing all 5 commands (`check`, `enrichment`, `freshness`, `coverage`, `griffe`) with one-line descriptions and typical usage
- [x] Task 2: Enhance competitive positioning in README (AC: #2)
  - [x] 2.1: Review and strengthen the existing comparison table and surrounding narrative — ensure "Why docvet?" framing is clear and prominent
  - [x] 2.2: Strengthen pydoclint differentiation paragraph — explicitly call out what pydoclint covers (structural Args/Returns/Raises matching) vs what docvet uniquely covers (Yields, Receives, Warns, Attributes, Examples, typed attributes, cross-references, freshness, griffe, coverage)
  - [x] 2.3: Add agent-oriented narrative: "docvet catches what AI agents break" — freshness checking detects when agents modify code but leave stale docstrings
- [x] Task 3: Validate README rendering (AC: #3)
  - [x] 3.1: Run `uv run python -m readme_renderer README.md -o /dev/null` to verify PyPI rendering
  - [x] 3.2: Visual review of GitHub rendering (confirm tables, code blocks, badges all render correctly)
- [x] Task 4: Run all quality gates (AC: #3)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: README contains "## AI Agent Integration" with CLAUDE.md snippet, `[tool.docvet]` config, subcommand table (7 rows) | PASS |
| 2 | Manual: README contains "## Why docvet?" heading above comparison table with 6-layer model; pydoclint paragraph sharpened with "3 structural checks" framing | PASS |
| 3 | Manual: `uv run python -m readme_renderer README.md -o /dev/null` exits 0; all 6 quality gates pass; standard GFM only (no `<details>`, no emoji shortcodes) | PASS |

## Dev Notes

### Implementation Approach

This story **enhances** (not rewrites) the existing README by adding an "AI Agent Integration" section and strengthening the existing competitive positioning. The current README (155 lines) already has solid structure — comparison table, quickstart, configuration, pre-commit, GitHub Action, research citations, and badge sections. The work is additive: ~40-50 new lines total.

**Key design decisions (party-mode consensus):**

- **Enhance, don't rewrite**: The current README has good bones. Add two new sections and tighten existing content in-place. Do not reorganize or restructure what's already working.
- **Section placement**: "AI Agent Integration" goes AFTER integration sections (Quickstart, Configuration, Pre-commit, GitHub Action) and BEFORE "Better Docstrings, Better AI" research section. Reading flow: what it does → install → configure → use with AI agents → why it matters.
- **"Why docvet?" heading**: Add a `## Why docvet?` heading above the existing comparison table to make it a named, linkable section. The table and pydoclint paragraph already exist — just give them a section anchor.
- **Keep AI section compact**: Target 25-30 lines. Agent instructions = one sentence. Config = full-strength example. Subcommand table = 5 commands. Copy-paste-and-go design — agents scan for structure, not narrative.
- **Sharpen pydoclint differentiation with numbers**: "pydoclint covers 3 structural checks. docvet covers those plus 16 more — and adds freshness, rendering, and visibility that no other tool touches."
- **Agent narrative placement**: Weave "docvet catches what AI agents break" into the existing "Better Docstrings, Better AI" section as a connecting sentence, not a separate section. The research citations already support it.
- **Dual rendering**: README serves both GitHub and PyPI. Stick to standard GFM (tables, code blocks, headings, images) — no `<details>` tags, no emoji shortcodes. Validate with `readme-renderer`.
- **No new dependencies**: Purely a README content change.

### Current README Structure (for reference)

```
1. Badge row (6 badges)
2. # docvet heading + tagline
3. Comparison table (6-layer model vs ruff/interrogate/pydoclint)
4. pydoclint differentiation paragraph
5. Navigation links (Quickstart | GitHub Action | Pre-commit | Configuration | Docs)
6. ## What It Checks (rule listings by category)
7. ## Quickstart
8. ## Configuration
9. ## Pre-commit
10. ## GitHub Action
11. ## Better Docstrings, Better AI (research citations)
12. ## Badge
13. ## Used By
14. ## License
```

### Target README Structure

```
1. Badge row (6 badges) — unchanged
2. # docvet heading + tagline — unchanged
3. Comparison table (6-layer model) — enhanced with "Why docvet?" heading
4. pydoclint differentiation — strengthened
5. Navigation links — add AI Agent Integration link
6. ## What It Checks — unchanged
7. ## Quickstart — unchanged
8. ## Configuration — unchanged
9. ## Pre-commit — unchanged
10. ## GitHub Action — unchanged
11. ## AI Agent Integration — NEW
    - Agent instructions snippet (CLAUDE.md example)
    - pyproject.toml config example for agent workflows
    - Subcommand quick reference table
12. ## Better Docstrings, Better AI — unchanged (or minor enhancement)
13. ## Badge — unchanged
14. ## Used By — unchanged
15. ## License — unchanged
```

### AI Agent Integration Section Content Guide

The section should be ~25-30 lines, copy-paste-and-go. Three components:

**1. Agent instructions snippet** — One-sentence instruction for CLAUDE.md / `.cursorrules` / agent configs:

> After modifying Python functions, classes, or modules, run `docvet check` and fix all findings before committing.

Show this as a fenced code block labeled as a CLAUDE.md snippet. Keep it minimal — agents need one actionable sentence, not a paragraph.

**2. pyproject.toml config example** — Full-strength config (same config docvet uses on itself):

```toml
[tool.docvet]
fail-on = ["enrichment", "freshness", "coverage", "griffe"]
```

Optionally show `exclude` and `freshness` thresholds but keep it short. The Configuration section already has detail.

**3. Subcommand quick reference table** — 5 commands, one line each:

| Command | Description |
|---------|-------------|
| `docvet check` | Run all enabled checks (default: git diff files) |
| `docvet check --all` | Run all checks on entire codebase |
| `docvet check --staged` | Run all checks on staged files only |
| `docvet enrichment` | Check for missing docstring sections |
| `docvet freshness` | Detect stale docstrings via git |
| `docvet coverage` | Find files invisible to mkdocs |
| `docvet griffe` | Check mkdocs rendering compatibility |

### Competitive Positioning Enhancement Guide

The current README already has a comparison table and pydoclint paragraph. Three targeted enhancements:

1. **Add `## Why docvet?` heading** above the existing comparison table — makes it a named, linkable section. The table content stays the same. Just wrap it in a section.
2. **Sharpen pydoclint differentiation with numbers**: Replace the current descriptive paragraph with something punchier. Target framing: "pydoclint covers 3 structural checks (Args, Returns, Raises). docvet's enrichment alone has 10 rules — plus freshness, rendering, and visibility that no other tool touches. 19 rules across 4 checks."
3. **Weave agent narrative into "Better Docstrings, Better AI"**: Add one connecting sentence to the existing research section: "docvet's freshness checking catches exactly this — detecting when code changes outpace documentation updates." This ties the research citations to docvet's unique capability without creating a separate section.
4. **Do NOT remove** existing research citations — they validate the positioning and are a key differentiator

### Architecture Constraints

- README serves as both GitHub landing page AND PyPI long description — PyPI has stricter markdown support
- Must validate with `readme-renderer` (dev dependency, installed)
- Rule counts (19 rules, 4 checks) must stay synchronized with `docs/rules.yml`
- Badge row format must remain compatible with shields.io
- "Better docstrings, better AI" tagline is established branding
- All code examples must use current CLI syntax and actual command outputs

### Testing Standards

This is a documentation-only story. Testing is manual:
- `uv run python -m readme_renderer README.md -o /dev/null` must succeed (PyPI rendering validation)
- Visual review of GitHub rendering in PR preview
- Verify all links, tables, and code blocks render correctly
- Run `uv run docvet check --all` to confirm no docvet findings introduced
- All standard quality gates pass

### Project Structure Notes

- Only file modified: `README.md` at repo root
- No source code changes
- No new dependencies
- No test changes needed (README is not tested programmatically beyond readme-renderer)

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md#Story 22.2] — acceptance criteria and FRs
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 2] — README dual purpose (GitHub + PyPI)
- [Source: GitHub Issue #153] — AI Agent Integration section requirements
- [Source: GitHub Issue #162] — Competitive positioning and landscape analysis
- [Source: _bmad-output/implementation-artifacts/22-1-add-how-to-fix-guidance-to-all-19-rule-pages.md] — previous story (docs-only pattern, all quality gates passed)
- FRs: FR145, FR146
- NFR: NFR78

### Documentation Impact

- Pages: `README.md` (primary deliverable)
- Nature of update: Add "AI Agent Integration" section with agent instructions, config example, and subcommand reference; enhance competitive positioning with stronger "Why docvet?" framing and pydoclint differentiation

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 889 passed, no regressions
- [x] `uv run docvet check --all` — zero findings
- [x] `uv run interrogate -v` — 100.0% coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no debugging needed.

### Completion Notes List

- Added `## Why docvet?` heading above existing comparison table (linkable section anchor)
- Sharpened pydoclint differentiation paragraph with numbers: "3 structural checks" vs "10 rules" framing
- Added `## AI Agent Integration` section (~28 lines) with: CLAUDE.md snippet, `[tool.docvet]` config example, subcommand quick reference table (7 rows)
- Wove agent narrative into "Better Docstrings, Better AI" intro: "Agents modify code but often leave docstrings stale"
- Added "AI Agent Integration" link to navigation bar
- PyPI rendering validated with readme-renderer (exit code 0)
- All 6 quality gates pass: ruff, ty, pytest (889), docvet, interrogate (100%)

### Change Log

- 2026-02-26: Added "AI Agent Integration" section, "Why docvet?" heading, and enhanced competitive positioning in README
- 2026-02-26: Code review fixes — accurate pydoclint framing, removed false Returns coverage claim, fixed CLAUDE.md snippet heading level, eliminated AI-tell em-dashes from prose

### File List

- `README.md` — added AI Agent Integration section, Why docvet? heading, enhanced pydoclint differentiation, agent narrative in research section

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Code Review Workflow (adversarial)

### Outcome

Approve (after fixes)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | "Covering those" implies Returns checking that docvet doesn't have | Rephrased to "from Raises and parameter checking to..." — no false Returns claim |
| M1 | MEDIUM | pydoclint "3 structural checks" undercounts (pydoclint has ~15 rules across categories) | Changed to "3 structural categories" — accurate framing |
| M2 | MEDIUM | CLAUDE.md snippet uses `#` (h1) heading, conflicts with existing CLAUDE.md structure | Changed to `##` for proper section integration |
| L1 | LOW | Em-dash (`--`) in prose is an AI-generative tell; competitor READMEs avoid it | Replaced prose `--` with commas/colons per party-mode consensus; kept `--` only in table markers and license line |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
