# Story 30.5: Concepts Page

Status: review
Branch: `feat/docs-30-5-concepts-page`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/296

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer evaluating docvet**,
I want a Concepts page that explains why each check matters and how docvet fits in the ecosystem,
so that I understand the value proposition before diving into configuration or architecture.

## Acceptance Criteria

1. **Given** a visitor navigates the docs site, **when** they look at the navigation between Getting Started and CI Integration, **then** a "Concepts" page exists at `docs/site/concepts.md` bridging the gap.

2. **Given** the Concepts page content, **when** a visitor reads the "The Problem" section, **then** it explains that docstrings lie — code changes, docstrings don't — and positions the gap between ruff (style), interrogate (presence), and actual docstring quality.

3. **Given** the Concepts page content, **when** a visitor reads the six-layer model section, **then** it provides a narrative walkthrough (not just the technical table from Getting Started) explaining what each layer catches with concrete examples.

4. **Given** the Concepts page content, **when** a visitor reads the before/after showcase, **then** it shows a realistic Python function with real docstring gaps, the docvet output, and the corrected version — the "aha moment" that converts visitors to users.

5. **Given** the Concepts page content, **when** a visitor reads the "When to Use Each Check" section, **then** each check has a one-paragraph explanation of its use case (enrichment for completeness, freshness for staleness, presence for coverage, coverage for mkdocs visibility, griffe for rendering).

6. **Given** the Concepts page content, **when** a visitor reads the ecosystem positioning, **then** docvet is positioned as complementary to ruff and interrogate, not competitive (per NFR5).

7. **Given** the `mkdocs.yml` navigation, **when** the Concepts page is added, **then** it appears between Getting Started and CI Integration in the nav.

8. **Given** all documentation changes, **when** `mkdocs build --strict` is run, **then** the build succeeds with zero warnings.

## Tasks / Subtasks

- [x] Task 1: Create `docs/site/concepts.md` (AC: 1-6)
  - [x] 1.1 Write "The Problem" section — docstrings lie, ecosystem gap narrative
  - [x] 1.2 Write "The Six-Layer Quality Model" section — narrative walkthrough of all 6 layers with examples
  - [x] 1.3 Write before/after showcase — realistic function with docstring gaps, docvet output, corrected version
  - [x] 1.4 Write "When to Use Each Check" section — scannable table per party-mode consensus
  - [x] 1.5 Write ecosystem positioning — ruff + docvet two-tool story with Further Reading admonition
- [x] Task 2: Update `mkdocs.yml` navigation (AC: 7)
  - [x] 2.1 Add "Concepts" entry between "Getting Started" and "CI Integration" in nav
- [x] Task 3: Run quality gates (AC: 8)
  - [x] 3.1 `mkdocs build --strict` passes with zero warnings
  - [x] 3.2 All standard quality gates pass

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `docs/site/concepts.md` exists; mkdocs.yml nav has "Concepts: concepts.md" | Pass |
| 2 | "The Problem" section with ecosystem gap, Paper 1 stat, DORA quote | Pass |
| 3 | "The Six-Layer Quality Model" section with 6 narrative paragraphs and research citation | Pass |
| 4 | "See It in Action" with `fetch_user` function, docvet output, corrected version | Pass |
| 5 | "When to Use Each Check" scannable table with 5 checks and "Learn more" links | Pass |
| 6 | "Where docvet Fits" — ruff + docvet two-tool story, no competitive positioning | Pass |
| 7 | mkdocs.yml: Concepts between Getting Started and CI Integration (line 90) | Pass |
| 8 | `mkdocs build --strict` — zero warnings; all other quality gates pass | Pass |

## Dev Notes

### Party-Mode Consensus: Page Structure

The team agreed on this outline (showcase before framework — concrete before abstract):

```
# Concepts

## The Problem (hook + ecosystem gap + research stats)
## See It in Action (before/after showcase)
## The Six-Layer Quality Model (narrative walkthrough)
## When to Use Each Check (scannable table, not paragraphs)
## Where docvet Fits (ecosystem positioning: ruff + docvet)
## Further Reading (admonition with research papers)
```

### Content Source

Primary content source: `docs/product-vision.md` (internal planning doc). Adapt for user-facing audience — educational and persuasive tone, not specification-oriented.

Secondary content source: `README.md` "Better Docstrings, Better AI" section (lines 166-177) — research citations and stats.

### Research Evidence (Party-Mode Consensus)

Four academic papers and two industry reports provide the evidence base. Use as follows:

**Inline in "The Problem" section (two stats + one quote):**
- Paper 1 (arxiv 2404.03114): "Incorrect documentation degrades LLM task success by 22.6pp — but missing docs have *no significant impact*." Key nuance: wrong is worse than absent. This directly supports freshness checking as the highest-value layer.
- DORA 2025: "AI doesn't fix a team; it amplifies what's already there."
- Paper 4 opener quote (arxiv 2508.09537): "In practice, developers frequently expect models to complete code without explicit guidance, as writing comprehensive docstrings is time-consuming and often neglected."

**Brief reference in Six-Layer Model section:**
- Connect Layer 4 (Accuracy) to Paper 1's finding — "This is why accuracy checking exists. Research shows stale docstrings actively harm AI tools."

**Further Reading `!!! info` admonition at page bottom:**

| Paper | Key Finding | Scale/Credibility |
|-------|------------|-------------------|
| [Testing the Effect of Code Documentation on LLM Code Understanding](https://arxiv.org/abs/2404.03114) (NAACL 2024) | Wrong docs degrade success by 22.6pp; missing docs have no significant effect | 164 HumanEval tasks, GPT-3.5 + GPT-4 |
| [Code Needs Comments](https://arxiv.org/abs/2402.13013) | Comment density improves code generation by 40-54%; existing corpora are comment-starved (16.7% density) | 40B tokens, 32 A100 GPUs, 3 models |
| [Impact of Code Changes on Fault Localizability](https://arxiv.org/abs/2504.04372) | Misleading comments drop fault localization to 25.63%; cosmetic changes broke LLM reasoning in 78% of cases | 750K tasks, 10 frontier LLMs, 245M lines |
| [Your Coding Intent is Secretly in the Context](https://arxiv.org/abs/2508.09537) | Docstrings unlock 44-84% relative performance gains; CodeLlama-7B Pass@1 nearly doubles with docstrings | DevEval + ComplexCodeEval, 6 models |
| [2025 DORA Report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report) | AI amplifies quality: 98% more PRs but 9% more bugs; code quality is prerequisite | Google DORA team |
| [Code Smells for AI Agents](https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory) | "The only signal was code quality. The higher-quality the codebase, the more AI accelerated the organization." | Stanford research via Factory |

**Cross-cutting narrative themes:**
1. Wrong docs are worse than no docs (Papers 1 + 3) — freshness checking prevents active harm
2. Docstrings unlock 44-84% relative AI performance gains (Paper 4) — presence + completeness matter
3. AI amplifies existing quality (DORA + Factory) — without quality foundations, throughput is a liability
4. Documentation quality must be checked programmatically at AI scale (Factory) — can't manually review 100 agents' output

### Current Docs Site Structure

Navigation in `mkdocs.yml` currently goes:
```
- Getting Started: index.md
- CI Integration: ci-integration.md
- Editor Integration: editor-integration.md
- AI Agent Integration: ai-integration.md
- Checks: (5 pages)
- Rules: (18 pages)
- Configuration, Architecture, CLI Reference, Glossary, etc.
```

Concepts page slots in at position 2, pushing CI Integration to position 3.

### Getting Started Page Content (Avoid Duplication)

`docs/site/index.md` already contains:
- A quality model table showing all 6 layers with tool ownership
- Quick start commands
- A "Checks" card grid linking to individual check pages

The Concepts page should **deepen** the quality model explanation (narrative walkthrough, not duplicate the table) and **add** the before/after showcase and ecosystem positioning that index.md lacks.

### Six-Layer Model — Current Accurate Definition

docvet implements layers 1 and 3-6 (Epic 28 added presence check for layer 1):

| Layer | Name | Tool |
|-------|------|------|
| 1 | Presence | docvet (`presence` check) |
| 2 | Style | ruff (D rules) |
| 3 | Completeness | docvet (`enrichment` check) |
| 4 | Accuracy | docvet (`freshness` check) |
| 5 | Rendering | docvet (`griffe` check) |
| 6 | Visibility | docvet (`coverage` check) |

One transitional sentence in the six-layer model section: "Layer 1 was historically handled by tools like interrogate; docvet's `presence` check now covers this natively." Do NOT give interrogate a peer positioning section — it is unmaintained.

### Before/After Showcase Guidelines (Party-Mode Consensus)

Use a **realistic, multi-issue** function — at least 2-3 different findings in one example. Good candidate:
- A function that raises exceptions without documenting them (missing-raises)
- Same function missing an Examples section (missing-examples)
- Possibly stale parameter docs (freshness)

Show three code blocks:
1. The problematic code (`python` syntax highlighting)
2. The docvet output (`console` or `text` block — NOT `bash`)
3. The fixed code (`python` syntax highlighting)

### When to Use Each Check (Party-Mode Consensus)

Use Winston's scannable table format, NOT full paragraphs:

| Check | Use When... | Learn More |
|-------|------------|------------|
| `presence` | You want to ensure every public symbol has a docstring | [Presence](checks/presence.md) |
| `enrichment` | You want complete docstrings (Raises, Attributes, Examples) | [Enrichment](checks/enrichment.md) |
| `freshness` | Code changed but docstrings didn't get updated | [Freshness](checks/freshness.md) |
| `coverage` | Your mkdocs site is missing modules (no `__init__.py`) | [Coverage](checks/coverage.md) |
| `griffe` | mkdocstrings can't parse your docstrings | [Griffe](checks/griffe.md) |

One short paragraph after the table for context is acceptable. The table is what people read.

### Ecosystem Positioning (Party-Mode Consensus)

Simplified to a two-tool story: **ruff + docvet = complete docstring quality**.
- **ruff** handles style (D rules) — complementary, use together
- **docvet** handles everything else: presence, completeness, accuracy, rendering, visibility
- Do NOT give interrogate peer positioning — it is unmaintained and docvet supersedes it
- One transitional sentence for migration SEO is sufficient (in six-layer model section)

### Anti-Patterns to Avoid

- Do NOT duplicate the quality model table from `index.md` — reference it and expand with narrative
- Do NOT write a dry specification — this is a persuasion/education page for evaluating developers
- Do NOT use toy examples — realistic multi-issue Python patterns only
- Do NOT give interrogate a peer positioning section — one transitional sentence only
- Do NOT forget to update `mkdocs.yml` nav
- Do NOT include internal references to product-vision.md or planning artifacts
- Do NOT use `bash` syntax highlighting for docvet output — use `console` or `text`
- Do NOT overload inline citations — two stats inline, rest in Further Reading admonition

### Project Structure Notes

- New file: `docs/site/concepts.md` (~200 lines of markdown)
- Modified file: `mkdocs.yml` (add nav entry)
- No Python source changes
- No test changes
- Use relative paths for cross-references (`checks/enrichment.md`, not `/checks/enrichment.md`)

### References

- [Source: _bmad-output/planning-artifacts/epics-distribution-adoption.md, Story 30.5]
- [Source: docs/product-vision.md — primary content source for narrative]
- [Source: README.md:166-177 — research citations and stats]
- [Source: docs/site/index.md — existing quality model table, avoid duplication]
- [Source: mkdocs.yml — current nav structure]
- [FR8: Concepts page with six-layer model narrative]
- [FR9: Before/after showcase]
- [NFR5: Complementary positioning to ruff and interrogate]
- [Research: arxiv 2404.03114 — wrong docs degrade LLM success by 22.6pp]
- [Research: arxiv 2402.13013 — comment density improves generation by 40-54%]
- [Research: arxiv 2504.04372 — misleading comments drop fault localization to 25.63%]
- [Research: arxiv 2508.09537 — docstrings unlock 44-84% relative performance gains]
- [Research: 2025 DORA Report — AI amplifies existing quality]
- [Research: Stack Overflow/Factory — code quality is only AI acceleration signal]

### Test Maturity Piggyback

No test-review.md found — run `/bmad-tea-testarch-test-review` to establish baseline.

### Documentation Impact

- Pages: docs/site/concepts.md (new), mkdocs.yml (nav update)
- Nature of update: New Concepts page bridging Getting Started and CI Integration; nav entry addition

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1201 passed, no regressions
- [x] `uv run docvet check --all` — no findings, 100% coverage
- [x] `uv run interrogate -v` — N/A (no Python source changes)
- [x] `mkdocs build --strict` — zero warnings

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- No issues encountered. Docs-only story with straightforward implementation.

### Completion Notes List

- Created `docs/site/concepts.md` (~130 lines) with party-mode consensus structure: The Problem → See It in Action → Six-Layer Quality Model → When to Use Each Check → Where docvet Fits → Further Reading
- "The Problem" section weaves in Paper 1 stat (22.6pp degradation) and DORA quote inline
- Before/after showcase uses realistic `fetch_user` function with missing-raises and missing-examples findings
- Six-layer model is narrative paragraphs (not table duplication from index.md), with Paper 3 citation at Layer 4
- "When to Use Each Check" uses scannable table format per party-mode consensus
- Ecosystem positioning simplified to ruff + docvet two-tool story; interrogate mentioned in one transitional sentence only
- Further Reading admonition includes all 4 academic papers and 2 industry reports with key findings and scale
- mkdocs.yml updated with Concepts nav entry between Getting Started and CI Integration

### Change Log

- 2026-03-05: Implemented story 30.5 — Concepts page with research-backed narrative and party-mode consensus structure.

### File List

- docs/site/concepts.md (new)
- mkdocs.yml (modified — nav entry added)

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
