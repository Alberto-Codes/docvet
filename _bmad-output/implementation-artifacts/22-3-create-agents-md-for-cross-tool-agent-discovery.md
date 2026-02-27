# Story 22.3: Create AGENTS.md for Cross-Tool Agent Discovery

Status: review
Branch: `feat/docs-22-3-agents-md`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an AI coding agent (Codex, Cursor, Copilot, Cline, Claude Code),
I want an `AGENTS.md` file at the docvet repo root and a docs site page with copy-paste integration snippets,
so that I can discover docvet, understand its value, and integrate it into any Python project's workflow.

## Acceptance Criteria

1. **Given** no `AGENTS.md` exists at the repo root, **When** `AGENTS.md` is created, **Then** it is purely tool-usage focused: what docvet is, how to install it, how to configure it, how to run it, how to fix findings, and the six-layer quality model. It does NOT contain development conventions, contributor guidance, or internal architecture details.

2. **Given** the docs site exists at `docs/site/`, **When** a new AI Agent Integration page is created, **Then** it includes copy-paste snippets for 5 agent tool formats: AGENTS.md, CLAUDE.md, `.cursorrules`, `.github/copilot-instructions.md`, and `.windsurfrules`. Each snippet is 10-15 lines, uses the same canonical content adapted to each tool's conventions, and is enclosed in a fenced code block for easy copying.

3. **Given** `AGENTS.md` is created at the repository root, **When** the file is inspected, **Then** it is valid standard markdown, located at the root level (not in a subdirectory), and follows the AGENTS.md naming convention used by Codex, Cursor, Copilot, Windsurf, and Kilo Code for automatic discovery.

4. **Given** the README already has an "AI Agent Integration" section (story 22-2), **When** the new docs site page is published, **Then** the README section links to the docs page for the full snippet library ("See the [AI Agent Integration guide](https://alberto-codes.github.io/docvet/ai-integration/) for tool-specific snippets").

## Tasks / Subtasks

- [x] Task 1: Create `AGENTS.md` at repo root (AC: #1, #3)
  - [x] 1.1: Write project overview (what docvet is, the six-layer quality model table)
  - [x] 1.2: Write install section (`pip install docvet`, optional `docvet[griffe]`)
  - [x] 1.3: Write run section (key commands: `docvet check`, `docvet check --all`, `docvet check --staged`, individual subcommands)
  - [x] 1.4: Write configuration section (`[tool.docvet]` in pyproject.toml, key options)
  - [x] 1.5: Write "What each check does" section (enrichment, freshness, coverage, griffe one-liners)
  - [x] 1.6: Write "Fixing findings" section (rule pages link, general approach per category)
  - [x] 1.7: Verify file is ~60-80 lines, scannable, no contributor/development content
- [x] Task 2: Create docs site page `docs/site/ai-integration.md` (AC: #2)
  - [x] 2.1: Write page intro ("Add docvet to your AI coding workflow")
  - [x] 2.2: Write brief explanation of what each agent instruction file is and which tools read it
  - [x] 2.3: Write canonical docvet snippet (the core content all tools share)
  - [x] 2.4: Create AGENTS.md snippet (standard markdown format)
  - [x] 2.5: Create CLAUDE.md snippet (Claude Code format)
  - [x] 2.6: Create `.cursorrules` snippet (Cursor format)
  - [x] 2.7: Create `.github/copilot-instructions.md` snippet (GitHub Copilot format)
  - [x] 2.8: Create `.windsurfrules` snippet (Windsurf format)
- [x] Task 3: Wire up navigation and cross-links (AC: #4)
  - [x] 3.1: Add `ai-integration.md` to mkdocs.yml nav (after "CI Integration", label: "AI Agent Integration")
  - [x] 3.2: Update README "AI Agent Integration" section: add a link to the docs page as the FIRST line of the section, before the existing "Add docvet to your AI coding workflow" text. Format: "For tool-specific integration snippets, see the [full AI Agent Integration guide](https://alberto-codes.github.io/docvet/ai-integration/)."
- [x] Task 4: Validate and run quality gates (AC: all)
  - [x] 4.1: `mkdocs build --strict` passes
  - [x] 4.2: Verify AGENTS.md renders correctly on GitHub
  - [x] 4.3: Verify docs page renders correctly locally
  - [x] 4.4: Run all 6 standard quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- Pre-populated with expected test approaches — dev agent updates Status column. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: `AGENTS.md` exists at repo root, contains tool-usage sections only (install, configure, run, fix), no development conventions or internal architecture | PASS |
| 2 | Manual: `docs/site/ai-integration.md` contains decision guide table + 5 fenced code blocks (one per tool), each 10-15 lines | PASS |
| 3 | Manual: `AGENTS.md` is at repo root (not subdirectory), valid markdown, standard naming convention | PASS |
| 4 | Manual: README "AI Agent Integration" section contains link to `https://alberto-codes.github.io/docvet/ai-integration/` | PASS |

## Dev Notes

### Implementation Approach

This story creates two files and updates two existing files. It is documentation-only with no source code changes.

**Key design decisions from party-mode consensus:**

- **Pure tool-usage AGENTS.md**: The AGENTS.md at docvet's repo root is for agents discovering/evaluating docvet as a tool to USE. It does NOT document docvet's internal development conventions. CLAUDE.md and project-context.md serve that purpose. This avoids confusing "how to use docvet" with "how to develop docvet."
- **New docs site page, not README extension**: The README's "AI Agent Integration" section (added in story 22-2) is the teaser. The docs page is the full guide with tool-specific snippets. This keeps the README concise and gives the docs site the detailed content.
- **User authors their own files**: Snippets are copy-paste, not scaffolded. This avoids the supply chain trust escalation documented in the research (see issue #161 comment). The user decides what goes in their project's agent instruction files.
- **Same canonical content, adapted per tool**: The core message is identical across all 5 snippets ("after modifying Python code, run `docvet check` and fix all findings"). The wrapping and format differ per tool's conventions.
- **Short and specialist**: The GitHub Blog research (2500+ repos) found that effective AGENTS.md files are specialists, not generalists. One code snippet beats three paragraphs. Target ~60-80 lines for AGENTS.md, ~10-15 lines per snippet.

### AGENTS.md Content Outline

```
# AGENTS.md (repo root, ~60-80 lines)

1. One-line description: "docvet is a Python CLI tool for docstring quality"
2. Six-layer quality model table (the mental model)
3. Install: pip install docvet / pip install docvet[griffe]
4. Run: key commands table (check, check --all, check --staged, enrichment, freshness, coverage, griffe)
5. Configure: [tool.docvet] in pyproject.toml, key options (exclude, fail-on)
6. Fix findings: link to rule reference, brief per-category guidance
```

No architecture, no module layout, no coding conventions, no commit format.

### Docs Page Content Outline

```
# AI Agent Integration (docs/site/ai-integration.md)

1. Intro: "Add docvet to your AI coding workflow"
2. "Which file should I use?" decision guide table:
   | Your AI Tool     | Add This File                        |
   |------------------|--------------------------------------|
   | OpenAI Codex     | AGENTS.md                            |
   | Cursor           | .cursorrules (also reads AGENTS.md)  |
   | GitHub Copilot   | .github/copilot-instructions.md (also reads AGENTS.md) |
   | Claude Code      | CLAUDE.md                            |
   | Windsurf         | .windsurfrules                       |
3. Universal snippet (the core content)
4. Tool-specific sections:
   a. AGENTS.md — standard markdown (Codex, Cursor, Copilot, Windsurf, Kilo Code)
   b. CLAUDE.md — standard markdown (Claude Code)
   c. .cursorrules — plain text, not markdown (Cursor)
   d. .github/copilot-instructions.md — standard markdown (GitHub Copilot)
   e. .windsurfrules — plain text, not markdown (Windsurf)
5. Configuration reference (link to configuration.md)
6. Rule reference (link to rules index)
```

**Snippet format note:** AGENTS.md, CLAUDE.md, and `.github/copilot-instructions.md` are standard markdown. `.cursorrules` and `.windsurfrules` are plain text files (no markdown rendering). The snippets for plain text formats should omit markdown-specific syntax (links, headers) and use plain text equivalents.

### Canonical Snippet Content

The core content shared across all tool-specific snippets (~10-15 lines):

```
## Docstring Quality

This project uses [docvet](https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- `docvet check --all` — run all checks on entire codebase (recommended for agent workflows)
- `docvet check` — run all checks on files changed since last commit
- `docvet check --staged` — run checks on staged files only
- `docvet enrichment` — check for missing docstring sections
- `docvet freshness` — detect stale docstrings via git

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
```

Note: `docvet check --all` is the recommended default for agent workflows since agents typically work across broader scope than a single git diff. Adapted per tool: heading levels, file format conventions (markdown vs plain text), additional context where appropriate.

### Security Research Context

Research (documented in issue #161 comment) found that AGENTS.md files are confirmed prompt injection vectors with CVEs assigned. The decision to use copy-paste snippets rather than `docvet init` scaffolding avoids the supply chain trust escalation risk. The user is always the author of their own agent instruction files.

Long-term, the MCP server approach (issue #149) is preferred for tool-native agent instructions.

### Previous Story Intelligence

Stories 22-1 and 22-2 were both clean docs-only implementations:
- 22-2 added the README "AI Agent Integration" section (~28 lines) — this story links to the new docs page from there
- 22-1 added "How to Fix" guidance to all 19 rule pages — the snippets can link to these
- Code review on 22-2 found: em-dashes are an AI-generative tell (avoid in prose), inaccurate competitor claims need careful framing
- All quality gates pass trivially for docs-only stories

### Git Intelligence

Last 2 commits are both Epic 22 docs work:
- `df51114` feat(docs): add AI Agent Integration section and enhance competitive positioning (#170)
- `817f43c` feat(docs): add "How to Fix" guidance to all 19 rule pages (#166)

### Architecture Constraints

- `docs/site/` is the docs_dir for mkdocs — new page goes here
- mkdocs.yml has explicit nav entries — must add the new page
- Theme: material with macros plugin (docs/main.py) — no macros needed for this page
- `mkdocs build --strict` is the quality gate for docs changes
- AGENTS.md at repo root is outside the docs site — it's a standalone GitHub-rendered file

### Relationship to Other Issues

| Issue | Relationship | Impact |
|---|---|---|
| #161 | Primary issue for this story | Research findings documented in issue comment |
| #150 | `docvet init` scaffolding (deferred) | Security concerns documented in issue comment; this story's snippets are the safe alternative |
| #149 | MCP server (future) | Preferred long-term mechanism; documented in issue comment |
| #153 | README AI section (done, story 22-2) | This story links from that section to new docs page |
| #104 | CONTRIBUTING.md (story 22-4) | Separate concern; AGENTS.md is tool-usage, CONTRIBUTING.md is contributor-facing |

### Project Structure Notes

- Files created: `AGENTS.md` (repo root), `docs/site/ai-integration.md`
- Files updated: `mkdocs.yml` (nav entry), `README.md` (link to docs page)
- No source code changes
- No new dependencies
- No test changes needed

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md#Story 22.3] — original acceptance criteria (revised for tool-usage focus)
- [Source: GitHub Issue #161] — AGENTS.md scaffolding and cross-tool agent instructions + research findings
- [Source: AGENTS.md Specification](https://agents.md/) — cross-tool standard
- [Source: GitHub Blog](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) — best practices from 2500+ repos
- [Source: OpenAI Codex Guide](https://developers.openai.com/codex/guides/agents-md/) — Codex AGENTS.md guide
- [Source: _bmad-output/implementation-artifacts/22-2-rewrite-readme-with-ai-agent-section-and-competitive-positioning.md] — previous story
- FR: FR147
- NFR: NFR78
- Issue: #161

### Documentation Impact

- Pages: `docs/site/ai-integration.md` (new), `README.md` (link update)
- Nature of update: New docs page with agent integration snippets; README cross-link to docs page

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (889 passed), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0% (>= 95%)
- [x] `uv run mkdocs build --strict` — zero warnings (docs quality gate)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging required.

### Completion Notes List

- Created `AGENTS.md` (76 lines) at repo root: pure tool-usage content covering the six-layer quality model, install, run commands, configuration, check descriptions, and fix guidance. No contributor/development content.
- Created `docs/site/ai-integration.md`: docs site page with decision guide table (6 tools) and 5 copy-paste snippets (AGENTS.md, CLAUDE.md, .cursorrules, .github/copilot-instructions.md, .windsurfrules). Markdown snippets use links/headers; plain text snippets (.cursorrules, .windsurfrules) omit markdown syntax.
- Added nav entry in mkdocs.yml after "CI Integration".
- Added link to docs page as first line of README "AI Agent Integration" section.
- All 7 quality gates pass. 889 tests, zero regressions.

### Change Log

- 2026-02-26: Created AGENTS.md and AI Agent Integration docs page; wired navigation and cross-links; all quality gates pass.

### File List

- `AGENTS.md` (new) — repo-root agent discovery file
- `docs/site/ai-integration.md` (new) — docs site AI Agent Integration page
- `mkdocs.yml` (modified) — added nav entry for ai-integration.md
- `README.md` (modified) — added docs page link to AI Agent Integration section

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
