# Story 22.5: Audit and Expand Discoverability Metadata

Status: done
Branch: `feat/chore-22-5-discoverability-metadata`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer searching for docstring quality tools on GitHub or PyPI,
I want docvet to appear in relevant searches through optimized topics, classifiers, and keywords,
so that I can discover docvet when looking for tools in this space.

## Acceptance Criteria

1. **Given** the current GitHub repository topics (12 topics), **when** topics are audited and expanded, **then** agent/AI-oriented terms are added (e.g., `ai-coding`, `llm-tools`, `code-quality`, `docstring-linter`) alongside existing topics.

2. **Given** the current PyPI classifiers in `pyproject.toml` (8 classifiers), **when** classifiers are audited, **then** relevant classifiers are added or confirmed present (e.g., `Topic :: Software Development :: Documentation`, `Topic :: Software Development :: Testing`).

3. **Given** the current PyPI keywords in `pyproject.toml` (8 keywords), **when** keywords are audited and expanded, **then** agent/AI-oriented keywords are added (e.g., `ai-agent`, `code-review`, `static-analysis`, `pre-commit`) to improve search ranking.

## Tasks / Subtasks

- [x] Task 1: Add 8 GitHub topics (AC: #1)
  - [x] 1.1: Run `gh repo edit --add-topic` for all 8 agreed topics: `ai-agent`, `ai-coding`, `ai-tools`, `llm-tools`, `google-style-docstrings`, `mkdocstrings`, `docstring-linter`, `developer-tools`
  - [x] 1.2: Verify final 20-topic list with `gh repo view --json repositoryTopics`
- [x] Task 2: Add 2 PyPI classifiers (AC: #2)
  - [x] 2.1: Add `Topic :: Software Development :: Documentation` and `Topic :: Software Development :: Testing` to `pyproject.toml` `[project]` classifiers list
  - [x] 2.2: Verify classifiers are valid with `uv build` (invalid classifiers cause build warnings)
- [x] Task 3: Add 12 PyPI keywords (AC: #3)
  - [x] 3.1: Add all 12 agreed keywords to `pyproject.toml` `[project]` keywords list: `ai-agent`, `ai-coding`, `llm-tools`, `static-analysis`, `code-review`, `pre-commit`, `github-actions`, `mkdocstrings`, `google-style`, `docstring-linter`, `docstring-checker`, `python-linter`
  - [x] 3.2: Verify no duplicates within keywords list

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- NOTE: This story modifies metadata only — acceptance criteria are verified by inspection of GitHub topics and pyproject.toml content. No pytest tests needed. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `gh repo view --json repositoryTopics`: 20 topics present, all 8 new AI/ecosystem topics confirmed | PASS |
| AC2 | `uv build`: zero warnings, classifiers `Documentation` and `Quality Assurance` present in pyproject.toml (11 total after review: +2 original, -1 Testing, +2 OS Independent/Python 3 Only) | PASS |
| AC3 | pyproject.toml inspection: all 12 new keywords present, zero duplicates, 20 total keywords | PASS |

## Dev Notes

### Architecture & Implementation Guide

**This is a metadata-only story.** No source code changes, no new tests. Two surfaces to update:

1. **GitHub topics** — via `gh repo edit --add-topic <topic>` (and `--remove-topic` if needed)
2. **PyPI metadata** — edit `pyproject.toml` `[project]` section: `classifiers` and `keywords` arrays

### Agreed Additions (Party Mode Consensus)

**GitHub Topics — add 8 topics (12 → 20/20):**

| Topic to Add | Rationale |
|--------------|-----------|
| `ai-agent` | AGENTS.md exists, AI agent integration documented |
| `ai-coding` | Active search category, README targets this audience |
| `ai-tools` | Broader discovery net for AI tool searches |
| `llm-tools` | Catches LLM-specific searches (Copilot, Claude, Codex users) |
| `google-style-docstrings` | Core assumption of the tool, highly specific differentiator |
| `mkdocstrings` | Direct integration target, specific ecosystem term |
| `docstring-linter` | Compound search term developers actually type |
| `developer-tools` | Broad category catch for general tool discovery |

Commands:
```bash
gh repo edit --add-topic ai-agent --add-topic ai-coding --add-topic ai-tools --add-topic llm-tools --add-topic google-style-docstrings --add-topic mkdocstrings --add-topic docstring-linter --add-topic developer-tools
```

Keep all 12 existing topics unchanged. Verify with:
```bash
gh repo view --json repositoryTopics --jq '.repositoryTopics[].name' | sort
```

**PyPI Classifiers — add 2 classifiers (8 → 10):**

| Classifier to Add | Rationale |
|--------------------|-----------|
| `Topic :: Software Development :: Documentation` | Primary function — we vet documentation quality |
| `Topic :: Software Development :: Testing` | Quality assurance adjacent, catches testing tool searches |

No AI-specific category exists in PyPI's taxonomy. Only add classifiers from the official list: https://pypi.org/classifiers/

**PyPI Keywords — add 12 keywords (8 → 20):**

| Keyword to Add | Rationale |
|----------------|-----------|
| `ai-agent` | Primary agent discovery term |
| `ai-coding` | Active search category |
| `llm-tools` | LLM-specific searches |
| `static-analysis` | Core category, missing from keywords |
| `code-review` | Adjacent category, agents use this term |
| `pre-commit` | Integration surface, real search term |
| `github-actions` | Integration surface, matches our action |
| `mkdocstrings` | Specific ecosystem integration |
| `google-style` | Docstring style specifier |
| `docstring-linter` | Compound search term |
| `docstring-checker` | Alternate compound search term |
| `python-linter` | General category catch |

Keep all 8 existing keywords unchanged (including competitor names `interrogate`, `pydocstyle`, `darglint` — deliberate competitive positioning for "alternative to X" searches).

### Current State (Before)

**GitHub topics (12):**
```
code-quality, docstring-checker, docstrings, documentation, github-actions,
linter, mkdocs, pre-commit-hook, python, python3, static-analysis, docvet
```

**PyPI classifiers (8):**
```python
"Development Status :: 5 - Production/Stable",
"Environment :: Console",
"Intended Audience :: Developers",
"License :: OSI Approved :: MIT License",
"Programming Language :: Python :: 3.12",
"Programming Language :: Python :: 3.13",
"Topic :: Software Development :: Quality Assurance",
"Typing :: Typed",
```

**PyPI keywords (8):**
```python
"docstring", "linter", "mkdocs", "interrogate", "pydocstyle",
"darglint", "documentation", "quality",
```

### Scope Boundaries

**In scope:**
- GitHub topics (add via `gh` CLI)
- PyPI classifiers and keywords (edit `pyproject.toml`)

**Out of scope (issue #156 includes but not in epic ACs):**
- Community list submissions (awesome-python, etc.) — requires external PRs, not automatable
- Repo description changes — current description is fine: "Comprehensive docstring quality vetting for Python projects"

### Carry-Forward from 22-4

Story 22-4 code review finding M3 deferred adding `docs` scope to commit conventions (CLAUDE.md + CONTRIBUTING.md). This is NOT in scope for 22-5 — handle as a separate chore if desired.

### Anti-Patterns to Avoid

- **Do NOT add `mcp` topic or keyword** — MCP/LSP integration doesn't exist yet (Epic 24 backlog). Every term must be truthful today, not aspirational.
- **Do NOT add `Framework :: Pytest` classifier** — docvet is not a pytest plugin
- **Do NOT add `cli` topic** — too generic, invisible in a sea of 50k+ repos with that topic
- **Do NOT remove existing competitor-name keywords** (`interrogate`, `pydocstyle`, `darglint`) — deliberate competitive positioning for "alternative to X" searches
- **Do NOT modify repo description** — out of scope, current description is effective
- **Do NOT submit to community lists** — external action, not in AC scope
- **Do NOT remove any existing GitHub topics** — all 12 current topics are pulling their weight

### Previous Story Intelligence (22-4)

- Clean docs-only implementation, zero debugging
- All quality gates pass trivially (no source changes)
- Code review: 4 of 5 findings fixed, M3 deferred (docs scope in commit conventions)
- Pattern: `feat(docs):` prefix, issue number in PR title, single-file or few-file changes

### Git Intelligence

Recent commits are all docs-related (Epic 22):
- `4ff286f` feat(docs): add CONTRIBUTING.md contributor guide (#172)
- `bc662a2` feat(docs): add AGENTS.md and AI Agent Integration docs page (#171)
- `df51114` feat(docs): add AI Agent Integration section and enhance competitive positioning (#170)

Pattern: `feat(docs):` or `chore(...)` prefix, issue number in title, clean single-file PRs.

### Project Structure Notes

- `pyproject.toml` at repo root — primary deliverable (classifiers + keywords)
- GitHub topics managed via `gh repo edit` — no file changes needed for topics
- `_bmad-output/implementation-artifacts/` — story file, sprint-status, and retro committed alongside
- No conflicts with existing files

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Story 22.5 definition, FR149, FR150]
- [Source: GitHub Issue #156 — chore: audit and expand GitHub/PyPI discoverability metadata]
- [Source: pyproject.toml — current classifiers, keywords, URLs]
- [Source: gh repo view — current 12 GitHub topics]

### Documentation Impact

- Pages: None
- Nature of update: N/A (metadata-only changes to pyproject.toml and GitHub topics)

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (889 passed), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging required.

### Completion Notes List

- Added 8 GitHub topics via `gh repo edit --add-topic` (12 → 20/20): `ai-agent`, `ai-coding`, `ai-tools`, `llm-tools`, `google-style-docstrings`, `mkdocstrings`, `docstring-linter`, `developer-tools`
- Added 2 PyPI classifiers to `pyproject.toml`: `Topic :: Software Development :: Documentation`, `Topic :: Software Development :: Testing` (8 → 10); post-review: removed `Testing`, added `Operating System :: OS Independent` and `Programming Language :: Python :: 3 :: Only` (final: 11)
- Added 12 PyPI keywords to `pyproject.toml`: `ai-agent`, `ai-coding`, `llm-tools`, `static-analysis`, `code-review`, `pre-commit`, `github-actions`, `mkdocstrings`, `google-style`, `docstring-linter`, `docstring-checker`, `python-linter` (8 → 20)
- All existing topics, classifiers, and keywords preserved unchanged
- `uv build` succeeds with zero warnings — all classifiers valid
- All 6 quality gates pass: 889 tests, zero regressions, zero findings, 100% docstring coverage
- Discoverability surface area approximately doubled across all three metadata surfaces

### Change Log

- 2026-02-27: Added 8 GitHub topics, 2 PyPI classifiers, 12 PyPI keywords for discoverability
- 2026-02-27: Code review fixes — removed `Testing` classifier, added `OS Independent` + `Python :: 3 :: Only`, sorted keywords alphabetically

### File List

- `pyproject.toml` (modified — added classifiers and keywords)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial review + party mode consensus)

### Outcome

Approved with fixes — 3 findings, all accepted and resolved.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | `Topic :: Software Development :: Testing` classifier misleading — linters use `Quality Assurance`, not `Testing` (competitive set confirms: ruff, flake8, pylint, interrogate all omit it) | Fixed: removed `Testing`, added `Operating System :: OS Independent` and `Programming Language :: Python :: 3 :: Only` (L2 merged) |
| L1 | LOW | Keywords list not alphabetically sorted — 20 entries hard to scan | Fixed: sorted all 20 keywords alphabetically |
| L2 | LOW | Missing standard classifiers: `Operating System :: OS Independent` and `Programming Language :: Python :: 3 :: Only` | Fixed: added both (merged into M1 resolution) |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
