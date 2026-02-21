# Story 10.2: README with Comparison Table, Quickstart, and Badges

Status: review

## Story

As a developer discovering docvet on PyPI or GitHub,
I want to understand what it does, how it compares to alternatives, and how to start using it in under 2 minutes,
so that I can make an informed adoption decision quickly.

## Acceptance Criteria

1. **Given** an empty `README.md`, **when** the README is written, **then** it includes a badge row: PyPI version, CI status, license, Python versions, "docs vetted | docvet".
2. **Given** an empty `README.md`, **when** the README is written, **then** it includes a one-line tagline and the six-layer quality model summary.
3. **Given** an empty `README.md`, **when** the README is written, **then** it includes a comparison table showing layer coverage for ruff, interrogate, pydoclint, and docvet.
4. **Given** an empty `README.md`, **when** the README is written, **then** it includes a single-command quickstart: `pip install docvet && docvet check --all`.
5. **Given** an empty `README.md`, **when** the README is written, **then** it includes a 3-line pre-commit configuration YAML snippet.
6. **Given** an empty `README.md`, **when** the README is written, **then** it includes a copy-paste badge snippet for adopters (`[![docs vetted | docvet]...]`).
7. **Given** an empty `README.md`, **when** the README is written, **then** it includes a "Used By" section placeholder.
8. **Given** the README is written, **when** verified via `python -m readme_renderer README.md` or `twine check dist/*`, **then** it renders correctly as PyPI long description with no rendering errors and no broken links.

## Tasks / Subtasks

- [x] Task 1: Write badge row (AC: #1)
  - [x] 1.1 Add PyPI version badge (`shields.io/pypi/v/docvet`)
  - [x] 1.2 Add CI status badge (`shields.io/github/actions/workflow/status/...`)
  - [x] 1.3 Add license badge (`shields.io/pypi/l/docvet`)
  - [x] 1.4 Add Python versions badge (`shields.io/pypi/pyversions/docvet`)
  - [x] 1.5 Add "docs vetted | docvet" custom badge (`shields.io/badge/docs%20vetted-docvet-blue`)
- [x] Task 2: Write tagline and six-layer quality model section (AC: #2)
  - [x] 2.1 Write one-line tagline: "ruff checks how your docstrings look. interrogate checks if they exist. docvet checks if they're right."
  - [x] 2.2 Write six-layer quality model table (same as product-vision.md)
- [x] Task 3: Write comparison table (AC: #3)
  - [x] 3.1 Create markdown table: rows = 6 layers, columns = ruff, interrogate, pydoclint, docvet
  - [x] 3.2 Mark coverage with checkmarks/dashes per tool per layer
- [x] Task 4: Write Quickstart section (AC: #4)
  - [x] 4.1 Add `pip install docvet && docvet check --all` one-liner
  - [x] 4.2 Add `pip install docvet[griffe]` variant for optional griffe support
  - [x] 4.3 Add brief expected-output example
- [x] Task 5: Write pre-commit snippet (AC: #5)
  - [x] 5.1 Add 3-line YAML snippet with repo URL, rev, hook id
- [x] Task 6: Write adopter badge snippet (AC: #6)
  - [x] 6.1 Add copy-paste markdown badge for adopters: `[![docs vetted | docvet](...)](...)`
- [x] Task 7: Write "Used By" section placeholder (AC: #7)
  - [x] 7.1 Add "Used By" heading with placeholder text
- [x] Task 8: Verify PyPI rendering (AC: #8)
  - [x] 8.1 `uv add --dev readme-renderer[md]` — add as dev dependency
  - [x] 8.2 `uv run python -m readme_renderer README.md -o /tmp/readme.html` — verify clean output (exit 0, no warnings)
- [x] Task 9: Run quality gates
  - [x] 9.1 `uv run pytest` — all existing tests pass
  - [x] 9.2 `uv run ruff check .` — no lint errors
  - [x] 9.3 `uv run ruff format --check .` — no formatting issues

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | Manual: badge row present with 5 badges (PyPI, CI, license, Python, docvet) | PASS |
| #2 | Manual: tagline and six-layer table present | PASS |
| #3 | Manual: comparison table with 4 tools x 6 layers | PASS |
| #4 | Manual: quickstart section with `pip install docvet && docvet check --all` | PASS |
| #5 | Manual: pre-commit YAML snippet present | PASS |
| #6 | Manual: adopter badge snippet present | PASS |
| #7 | Manual: "Used By" section exists | PASS |
| #8 | `python -m readme_renderer README.md` — exit 0, no warnings | PASS |

## Dev Notes

### Implementation Strategy

This is a content-only story. One file created/modified: `README.md`. No source code changes. No new tests needed — verification is via rendering tools.

**README structure (top to bottom):**

1. Badge row (5 badges, left-aligned on one line)
2. `# docvet` heading
3. Tagline (one-liner from product vision)
4. Six-layer quality model table
5. `## How It Compares` — comparison table (ruff vs interrogate vs pydoclint vs docvet)
6. `## Quickstart` — single-command install + first run
7. `## Better Docstrings, Better AI` — why docstring quality matters for AI-assisted development (see AI Agent Positioning section below)
8. `## Pre-commit` — 3-line YAML snippet
9. `## Configuration` — brief `[tool.docvet]` overview with link to future docs
10. `## Badge` — adopter badge snippet
11. `## Used By` — placeholder section
12. `## License` — MIT with link to LICENSE file

### PyPI Rendering Constraints

`README.md` serves dual duty: GitHub landing page and PyPI long description. PyPI renders markdown via `readme-renderer[md]` which supports **CommonMark** (not GFM).

**Safe markdown features:**
- Standard markdown headings, bold, italic, links, images
- Fenced code blocks with language hints
- Markdown tables (supported by readme-renderer since v35+)
- Inline code

**Avoid:**
- HTML tags (some stripped by PyPI)
- GitHub-specific features (task lists `- [ ]`, `<details>`, relative image paths)
- Emoji shortcodes (`:emoji:`) — use Unicode emoji directly if needed, or avoid
- Relative links to repo files — use absolute GitHub URLs

### Comparison Table Content

Based on the six-layer quality model from `docs/product-vision.md`:

| Layer | Check | ruff | interrogate | pydoclint | **docvet** |
|-------|-------|------|-------------|-----------|------------|
| 1. Presence | "Does a docstring exist?" | — | **Yes** | — | — |
| 2. Style | "Is it formatted correctly?" | **Yes** | — | — | — |
| 3. Completeness | "Does it have all required sections?" | — | — | Partial* | **Yes** |
| 4. Accuracy | "Does it match the current code?" | — | — | — | **Yes** |
| 5. Rendering | "Will mkdocs render it correctly?" | — | — | — | **Yes** |
| 6. Visibility | "Will mkdocs even see the file?" | — | — | — | **Yes** |

*pydoclint checks Args/Returns/Raises alignment with function signatures (structural completeness). docvet's enrichment covers that plus Yields, Receives, Warns, Attributes, Examples, typed attributes, and cross-references — 19 rules total.

**Notes on competitor coverage:**
- **ruff D rules**: Style enforcement (Google/numpy/sphinx convention). Does not check completeness or accuracy. Note: ruff is actively implementing pydoclint rules (GitHub issue #12434), which may eventually subsume pydoclint's layer 3 coverage into ruff.
- **interrogate**: Presence only — "does a docstring exist?" No content analysis.
- **pydoclint**: Actively maintained (v0.8.3, November 2025, MIT license). Checks Args/Returns/Raises/Yields alignment with signatures, class attribute matching, and type hint consistency between docstrings and annotations. Strong on structural alignment but does not cover: freshness/staleness detection, rendering compatibility, mkdocs visibility, or broader enrichment rules (Receives, Warns, Other Parameters, Examples, cross-references, typed attributes). Does not check files without docstrings (use interrogate for presence).
- **docvet**: Layers 3-6 complete. 19 rules across 4 checks. Unique territory: freshness (git diff/blame), griffe rendering compatibility, mkdocs coverage.

### Badge URLs

All badges use `shields.io`. Badges will show "not found" or default values until the package is published to PyPI and CI workflows are configured on the public repo.

```markdown
[![PyPI](https://img.shields.io/pypi/v/docvet)](https://pypi.org/project/docvet/)
[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/docvet/ci.yml?branch=develop)](https://github.com/Alberto-Codes/docvet/actions)
[![License](https://img.shields.io/pypi/l/docvet)](https://github.com/Alberto-Codes/docvet/blob/develop/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/docvet)](https://pypi.org/project/docvet/)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-blue)](https://github.com/Alberto-Codes/docvet)
```

**Note on CI badge:** The workflow file name (`ci.yml`) must match the actual workflow filename in `.github/workflows/`. Verify this exists before finalizing the badge URL.

### Pre-commit Snippet

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v1.0.0
    hooks:
      - id: docvet
```

**Note:** This snippet assumes `.pre-commit-hooks.yaml` exists in the repo (Story 10.3 delivers this). The snippet is valid even before 10.3 ships — it just won't work until the hook file exists. The README can include it as a "coming soon" or as documentation for post-10.3 usage.

### Adopter Badge Snippet

```markdown
[![docs vetted | docvet](https://img.shields.io/badge/docs%20vetted-docvet-blue)](https://github.com/Alberto-Codes/docvet)
```

### AI Agent Positioning: "Better Docstrings, Better AI"

This section goes after Quickstart in the README. It positions docvet as a quality lever for AI-assisted development — not a pivot, but a factual, research-backed subsection.

**Heading:** `## Better Docstrings, Better AI`

**Content guidance (3-4 sentences, cite research, no hype):**

> AI coding agents (Claude Code, Codex CLI, GitHub Copilot, OpenClaw) rely on docstrings as context when generating and modifying code. Research shows stale or incorrect documentation degrades AI accuracy by up to 50%, while accurate documentation improves code generation quality by 40%+ — stale docs are worse than no docs at all. docvet's freshness checking catches the accuracy gap that AI-generated code produces, and its enrichment rules ensure the docstring sections that agents use as context are complete. Run `docvet check` in your CI, pre-commit hooks, or agent toolchain.

**Key research citations to include (footnotes or inline links):**

| Citation | Finding | URL |
|----------|---------|-----|
| Macke & Doyle, NAACL 2024 | Incorrect docs drop LLM task success by 22.6 percentage points; missing docs have negligible impact. Stale docs are actively harmful. | https://arxiv.org/abs/2404.03114 |
| Song et al., ACL 2024 | Comment density improves LLM code generation by 40-54% relative improvement (HumanEval pass@1: 16.46% → 23.17%). | https://arxiv.org/abs/2402.13013 |
| Google DORA 2025 | "AI doesn't fix a team; it amplifies what's already there." AI reflects and multiplies existing code quality. | https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report |
| Reyes/Factory, Stack Overflow Blog Feb 2026 | "The only signal [correlating with AI productivity] was code quality." | https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory |
| Haroon et al., 2025 | Misleading comments reduce LLM fault localization accuracy to 24.55%. LLMs extract semantic info from comments. | https://arxiv.org/abs/2504.04372 |
| Li et al., 2025 | Performance "drops substantially" without docstrings; 20%+ gains when intent is recovered from context. | https://arxiv.org/abs/2508.09537 |

**Why this positioning is defensible:**
- docvet's freshness checking (layer 4) directly addresses the NAACL 2024 finding: stale docs hurt AI more than missing docs
- docvet's enrichment (layer 3) ensures the sections AI agents use as context (Args, Returns, Raises, etc.) are present
- docvet's `file:line: rule message` output format is the convention AI agents already parse in generate-lint-fix loops
- Semantic rule IDs (`missing-raises`, `stale-signature`) are self-explanatory to LLMs — no lookup table needed
- The claim is about documentation quality improving AI performance, not about docvet being an AI tool

**What NOT to claim:**
- Do not claim specific speed improvements from using docvet (no benchmarks exist)
- Do not claim docvet was designed for AI agents (it was designed for human developers; AI compatibility is a bonus)
- Do not position this as a pivot — it's a subsection, not the hero

### Previous Story Intelligence (10.1)

- **Build backend is `uv_build`** — includes `README.md` automatically since `readme = "README.md"` is set in `pyproject.toml`
- **MIT license** already in place — README `## License` section can reference it
- **`pyproject.toml` has project URLs** — Homepage, Source, Issues all pointing to `https://github.com/Alberto-Codes/docvet`
- **Classifiers and keywords** all set — README should align with the same positioning
- **PEP 561 `py.typed`** marker added — README can mention typed package support if relevant

### Epic 9 Retro Insights (relevant)

- **Foundational principle**: "Every symbol deserves its natural language representation" — this sharpens README positioning
- **Zero dogfooding findings** achieved — the "docs vetted | docvet" badge is earned
- **Tech debt resolved**: circular import fixed, config suppressions removed, pre-commit hooks set up
- **729 tests** at Story 10.1 completion, 19 rules, 4 checks

### Git Intelligence

Last 5 commits (all on `develop`):
- `d2aa4d0` feat(cli): add LICENSE, package metadata, and PEP 561 typing marker (#62)
- `c4be928` chore: extract Finding, add Examples docstrings, and pre-commit hooks (#61)
- `b1c53bb` feat(cli): version bump to 1.0.0, --version flag, and uv_build backend (#60)
- `6b90eb4` feat(cli): add __all__ exports to all public modules (#59)
- `43c82a7` feat(cli): add unified output pipeline and resolve all docvet findings (#58)

Epic 9 and Story 10.1 fully merged. Clean starting point.

**Suggested branch:** `feat/cli-10-2-readme-with-comparison-table-quickstart-and-badges`

### Rendering Verification

Add `readme-renderer[md]` as a dev dependency, then verify:

```bash
uv add --dev readme-renderer[md]
uv run python -m readme_renderer README.md -o /tmp/readme.html
# Success: outputs HTML file, exit 0
# Failure: prints warnings/errors, exit 1
```

This stays in the dev dependency group for reproducible verification. Run during development and before PR.

### Anti-Pattern Prevention

- **Do NOT use HTML tags** in README — PyPI strips many HTML elements. Pure markdown only.
- **Do NOT use relative links** to repo files (e.g., `[LICENSE](LICENSE)`) — use absolute GitHub URLs (`https://github.com/Alberto-Codes/docvet/blob/develop/LICENSE`)
- **Do NOT use GitHub-specific markdown** (task lists, `<details>/<summary>`, GitHub alerts) — these don't render on PyPI
- **Do NOT overstate competitor limitations** — comparison table should be factual and verifiable. pydoclint is actively maintained and covers real layer 3 functionality
- **Do NOT claim docvet was designed for AI agents** — it was designed for human developers; AI agent compatibility is a factual bonus supported by research
- **Do NOT make speed claims** about AI agents using docvet — no benchmarks exist. Frame as "accuracy" and "quality," not "speed"
- **Do NOT use emoji shortcodes** (`:rocket:`) — use Unicode directly or avoid entirely
- **Do NOT reference Story 10.3 artifacts** (pre-commit hook, GitHub Action) as if they exist yet — the pre-commit snippet is informational, noting "configure after installing"
- **Do NOT modify any source code** — this is a content-only story

### Files to Modify

| File | Changes |
|------|---------|
| `README.md` | **Rewrite** — from empty to full README with all required sections |
| `pyproject.toml` | Add `readme-renderer[md]` to `[dependency-groups] dev` |

### Project Structure Notes

- `README.md` at repository root (already exists, currently empty)
- Aligned with `pyproject.toml` `readme = "README.md"` declaration
- No source tree changes
- No test changes

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.2 — Acceptance criteria]
- [Source: _bmad-output/planning-artifacts/epics.md#FR118 — Comparison table]
- [Source: _bmad-output/planning-artifacts/epics.md#FR119 — Quickstart]
- [Source: _bmad-output/planning-artifacts/epics.md#FR120 — Badge row and adopter badge]
- [Source: _bmad-output/planning-artifacts/epics.md#FR126 — "docs vetted" badge]
- [Source: docs/product-vision.md#Six-Layer Docstring Quality Model — table content]
- [Source: _bmad-output/planning-artifacts/architecture.md — README dual duty, PyPI rendering]
- [Source: _bmad-output/planning-artifacts/prd.md#README — FR118-120 details]
- [Source: _bmad-output/implementation-artifacts/10-1-license-and-package-metadata.md — previous story context]
- [Source: _bmad-output/implementation-artifacts/epic-9-retro-2026-02-21.md — foundational principle, tech debt]
- [Source: pyproject.toml — current project metadata and URLs]
- [Source: Macke & Doyle, NAACL 2024 — stale docs degrade LLM accuracy (https://arxiv.org/abs/2404.03114)]
- [Source: Song et al., ACL 2024 — comment density improves code generation (https://arxiv.org/abs/2402.13013)]
- [Source: Google DORA 2025 — AI amplifies existing code quality]
- [Source: Reyes/Factory, Stack Overflow Blog Feb 2026 — code quality is only AI productivity signal]
- [Source: pydoclint GitHub — actively maintained, v0.8.3 (https://github.com/jsh9/pydoclint)]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no issues.

### Completion Notes List

- Wrote complete README.md with all 12 sections per the story structure: badge row, heading, tagline, six-layer table, comparison table, quickstart, "Better Docstrings Better AI" (research-backed), pre-commit snippet, configuration overview, adopter badge snippet, "Used By" placeholder, and license
- Used pure CommonMark-compatible markdown — no HTML tags, no relative links, no GitHub-specific features, no emoji shortcodes
- All 6 research citations included as inline links in the AI positioning section (NAACL 2024, ACL 2024, DORA 2025, Stack Overflow Blog 2026, Haroon et al. 2025, Li et al. 2025)
- Comparison table accurately represents pydoclint as "Partial" on layer 3, with explanatory paragraph
- Added `readme-renderer[md]` as dev dependency; rendering verified clean (exit 0, no warnings)
- All 729 tests pass, ruff lint clean, ruff format clean

### File List

- `README.md` — **created** (full README with all required sections)
- `pyproject.toml` — **modified** (added `readme-renderer[md]` to dev dependencies)
