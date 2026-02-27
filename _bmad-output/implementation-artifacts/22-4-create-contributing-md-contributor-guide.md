# Story 22.4: Create CONTRIBUTING.md Contributor Guide

Status: done
Branch: `feat/docs-22-4-contributing-md`

## Story

As a human contributor or AI agent submitting a pull request,
I want a `CONTRIBUTING.md` file at the repo root with clear development setup and process documentation,
so that I can contribute effectively without trial-and-error.

## Acceptance Criteria

1. **Given** no `CONTRIBUTING.md` exists at the repo root, **when** `CONTRIBUTING.md` is created, **then** it covers: fork-and-clone workflow, dev setup (`uv sync --dev`), pre-commit hooks setup, coding standards (ruff, ty, Google-style docstrings), PR process (draft PRs, squash-merge, no Co-Authored-By), commit conventions (conventional commits), testing expectations (unit + integration, pytest markers), and issue reporting (templates available).

2. **Given** `CONTRIBUTING.md` exists, **when** a new contributor follows its instructions, **then** they can set up a working dev environment, run all checks, and submit a properly formatted PR.

3. **Given** GitHub's contribution guidelines convention, **when** a user clicks "Contributing" in the GitHub UI or an agent looks for contribution instructions, **then** GitHub surfaces `CONTRIBUTING.md` automatically (standard root-level file convention).

## Tasks / Subtasks

- [x] Create `CONTRIBUTING.md` at repo root (AC: 1, 2, 3)
  - [x] Write Prerequisites section (Python 3.12+, uv, git)
  - [x] Write Fork & Clone section (fork on GitHub, clone fork, add upstream remote, create feature branch)
  - [x] Write Development Setup section (`uv sync --dev`, verify with `uv run docvet --help`)
  - [x] Write Pre-Commit Hooks section (`pre-commit install` + what hooks run: yamllint, actionlint, ruff-check, ruff-format, ty, pytest, docvet --staged)
  - [x] Write Quality Gates section (6 mandatory gates: ruff, ruff format, ty, pytest, docvet, interrogate)
  - [x] Write Coding Standards summary (future-annotations, Google-style docstrings, type hints, line lengths) with pointer to `docs/development-guide.md`
  - [x] Write Testing section (test org, naming convention, run commands) with pointer to development guide
  - [x] Write Commit Conventions section (conventional commits format, types, scopes, no Co-Authored-By)
  - [x] Write Pull Request Process section (fork workflow, draft PRs, target upstream main, squash-merge, PR template)
  - [x] Write Reporting Issues section (3 issue templates: bug report, feature request, enhancement)
  - [x] Write CI Pipeline summary (what CI checks, link to development guide for details)
  - [x] Write Key Constraints section (no runtime deps, no relative imports, no `__main__.py`)
- [x] Verify GitHub surfaces CONTRIBUTING.md in UI (AC: 3) -- standard root-level convention, verified by file placement
- [x] Run all quality gates (AC: 2)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: CONTRIBUTING.md exists at repo root with all 13 sections (fork-and-clone, dev setup, pre-commit, coding standards, PR process, commit conventions, testing, issue templates, CI pipeline, key constraints) | PASS |
| 2 | Manual: Quality gates all pass (ruff check, ruff format, ty, pytest 889 passed, docvet zero findings, interrogate 100%) | PASS |
| 3 | Manual: CONTRIBUTING.md at repo root, standard naming convention, GitHub auto-discovers | PASS |

## Dev Notes

### Implementation Strategy

This is a **docs-only story** — no source code changes, no automated tests needed. The pattern is identical to story 22-3 (AGENTS.md).

**Key design decision: Reference, don't duplicate.** `docs/development-guide.md` already contains comprehensive dev setup, quality gates, testing, code style, and git workflow documentation (~222 lines). CONTRIBUTING.md should be a concise (~100-150 lines) entry point that:
1. Covers the essentials inline (setup, quality gates, commit format, PR process)
2. Points to `docs/development-guide.md` for detailed testing standards, fixture patterns, and code style rules
3. Points to `.github/PULL_REQUEST_TEMPLATE.md` for PR body format

**Content complement (no overlap with AGENTS.md):**
- `AGENTS.md` = tool-usage focus (how to USE docvet)
- `CONTRIBUTING.md` = contribution focus (how to DEVELOP docvet)
- `docs/development-guide.md` = comprehensive reference (detailed conventions)

### Content Outline

**CONTRIBUTING.md** sections (in order):
1. **One-liner intro** — "Thanks for contributing" + link to GitHub issues
2. **Reporting Issues** — 3 issue templates available (bug report, feature request, enhancement), link to issues page
3. **Prerequisites** — Python 3.12+, uv, git (3 lines)
4. **Fork & Clone** — fork on GitHub, clone fork, add upstream remote, create feature branch (standard open-source workflow — external contributors cannot push to `Alberto-Codes/docvet`)
5. **Development Setup** — `uv sync --dev`, verify with `uv run docvet --help` (code block)
6. **Pre-Commit Hooks** — `pre-commit install` to activate; 7 hooks run automatically before each commit (yamllint, actionlint, ruff-check, ruff-format, ty, pytest, docvet --staged). All hooks must pass before commit succeeds. Note: docvet self-dogfoods via pre-commit (fail-on all 4 checks, zero exemptions).
7. **Quality Gates** — the 6 mandatory gates as a code block (ruff check, ruff format, ty, pytest, docvet check --all, interrogate). These mirror CI — run locally before pushing.
8. **Coding Standards** — brief summary (future-annotations, Google-style docstrings, type hints, 88/100 line lengths) + "See [Development Guide](docs/development-guide.md) for full details"
9. **Testing** — run commands (`uv run pytest`, `uv run pytest tests/unit`), naming convention, "See [Development Guide](docs/development-guide.md#testing) for fixtures, markers, and patterns"
10. **Commit Conventions** — conventional commits format with types/scopes table, no Co-Authored-By trailers
11. **Pull Request Process** — fork workflow: push to your fork, open draft PR against `upstream/main`, squash-merge, conventional commit title, reference PR template. Branch conventions (`feat/<scope>-<description>`) still apply on the fork. Always draft (non-draft triggers automated review).
12. **CI Pipeline** — brief table of what CI checks (lint, type-check, test, interrogate, docvet, CodeQL)
13. **Key Constraints** — the "never" rules (no runtime deps, no relative imports, no `__main__.py`, no mock AST nodes)

### Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `CONTRIBUTING.md` | CREATE | ~100-150 lines, repo root |

No other files need modification. Unlike story 22-3 (which added a docs site page + mkdocs nav entry), this is a single-file story. GitHub auto-discovers `CONTRIBUTING.md` at repo root — no nav entries or links needed.

### Anti-Patterns to Avoid

- **Do NOT duplicate `docs/development-guide.md`** — reference it. CONTRIBUTING.md is the concise entry point, not the encyclopedia.
- **Do NOT include AI agent workflow content** — that's AGENTS.md's territory (story 22-3).
- **Do NOT add sections about docvet's quality model or rules** — that's user-facing docs, not contributor guide.
- **Do NOT add a docs site page for CONTRIBUTING.md** — GitHub convention is repo-root only.
- **Do NOT link to `CONTRIBUTING.md` from README** — GitHub auto-surfaces it in the "Contributing" sidebar link and in issue/PR templates.

### Previous Story Intelligence (22-3)

- Clean docs-only implementation, zero debugging required
- All quality gates pass trivially (no source changes)
- Code review found: avoid em-dashes (AI-generative tell), be careful with competitor claims
- HTML tags in markdown (like `<rule-id>`) render as invisible HTML on GitHub — use backtick-wrapping
- Story 22-3 created AGENTS.md (76 lines) as a concise, scannable reference — same energy for CONTRIBUTING.md

### Git Intelligence

Recent commits are all docs-related (Epic 22):
- `bc662a2` feat(docs): add AGENTS.md and AI Agent Integration docs page (#171)
- `df51114` feat(docs): add AI Agent Integration section and enhance competitive positioning (#170)
- `817f43c` feat(docs): add "How to Fix" guidance to all 19 rule pages (#166)

Pattern: `feat(docs):` prefix, issue number in title, clean single-file or few-file PRs.

### Project Structure Notes

- `CONTRIBUTING.md` at repo root — standard GitHub convention, auto-discovered by GitHub UI
- No conflicts with existing files (confirmed: no CONTRIBUTING.md exists)
- Complements `AGENTS.md` (repo root, tool-usage) and `CLAUDE.md` (repo root, AI dev agent conventions)

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Story 22.4 definition, FR148, Issue #104]
- [Source: docs/development-guide.md — Comprehensive dev setup, testing, code style, git workflow]
- [Source: .github/PULL_REQUEST_TEMPLATE.md — PR body format and checklist]
- [Source: AGENTS.md — Tool-usage focus, content boundary]
- [Source: CLAUDE.md — Project conventions, architecture summary]
- [Source: .github/instructions/python.instructions.md — Detailed Google-style docstring guide]
- [Source: .github/instructions/pytest.instructions.md — Detailed pytest conventions]

### Documentation Impact

- Pages: None
- Nature of update: N/A (CONTRIBUTING.md is a standalone repo-root file, not a docs site page)

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

None -- clean implementation, no debugging required.

### Completion Notes List

- Created `CONTRIBUTING.md` (163 lines) at repo root: 13-section contributor guide covering fork-and-clone, dev setup, pre-commit hooks, quality gates, coding standards, testing, commit conventions, PR process, issue reporting, CI pipeline, and key constraints
- References `docs/development-guide.md` for detailed conventions (no duplication)
- References `.github/PULL_REQUEST_TEMPLATE.md` for PR body format
- Pre-commit hooks documented for the first time (not in development-guide.md or pyproject.toml dev deps)
- All 6 quality gates pass: 889 tests, zero regressions, zero findings, 100% docstring coverage
- 2026-02-27: Implementation complete

### Change Log

- 2026-02-27: Created CONTRIBUTING.md at repo root (163 lines, 13 sections)
- 2026-02-27: Code review fixes applied (4 findings resolved)

### File List

- `CONTRIBUTING.md` (CREATED) -- repo-root contributor guide

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approve with fixes (4 of 5 findings fixed, 1 deferred)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | Coverage command misleading -- `uv run pytest` comment said "85% coverage minimum" but command doesn't enforce it | Fixed: changed to "CI enforces 85% coverage" |
| M2 | MEDIUM | Pre-commit install gap -- contributor flow breaks if pre-commit not installed separately | Fixed: added explicit note with install link in Pre-Commit Hooks section |
| M3 | MEDIUM | Missing `docs` scope in Commit Conventions -- used in practice but omitted | Deferred: canonical source (CLAUDE.md) also omits it; fix all three files together in 22-5 or chore |
| L1 | LOW | ruff-check hook description overspecifies (E501, isort, docstrings) | Fixed: simplified to "Python linting" |
| L2 | LOW | No link to live documentation site | Fixed: added docs site link to intro paragraph |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
