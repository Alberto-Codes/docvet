# Story 30.3: License Attribution on Docs Site

Status: done
Branch: `feat/docs-30-3-license-attribution-on-docs-site`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/292

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **visitor to the docvet docs site**,
I want to see license information in the footer and a license page,
so that I can trust the project's licensing and know it's MIT-licensed.

## Acceptance Criteria

1. **Given** the `mkdocs.yml` configuration, **when** the `copyright` field is added (e.g., `Copyright &copy; 2026 Alberto-Codes — MIT License`), **then** every page of the docs site displays the copyright footer.

2. **Given** the docs site, **when** a visitor looks for license information, **then** a brief license note exists (either a standalone page or a section in an existing page) that references the MIT License and links to the LICENSE file in the repository.

3. **Given** all documentation changes, **when** `mkdocs build --strict` is run, **then** the build succeeds with zero warnings.

## Tasks / Subtasks

- [x] Task 1: Add `copyright` field to `mkdocs.yml` (AC: 1)
  - [x] 1.1 Add `copyright: "Copyright &copy; 2026 Alberto-Codes — MIT License"` at the top level of `mkdocs.yml`
  - [x] 1.2 Verify footer renders on local preview (`mkdocs serve`)
- [x] Task 2: Create license page (AC: 2)
  - [x] 2.1 Create `docs/site/license.md` with title, brief MIT summary, and link to the LICENSE file in the repo
  - [x] 2.2 Add `License: license.md` to the `nav` section in `mkdocs.yml` (place after Privacy Policy)
- [x] Task 3: Run quality gates (AC: 3)
  - [x] 3.1 `mkdocs build --strict` passes with zero warnings
  - [x] 3.2 All standard quality gates pass (ruff, ty, pytest, docvet, interrogate)

## AC-to-Test Mapping

<!-- Docs-only story — no new code, no new tests. Quality gate is mkdocs build --strict. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: `mkdocs serve` — copyright footer visible on every page | Pass |
| 2 | Manual: license page accessible from nav, links to GitHub LICENSE file | Pass |
| 3 | `uv run mkdocs build --strict` — zero warnings | Pass |

## Dev Notes

### Target Files

1. **`mkdocs.yml`** — Add `copyright` field (top-level, after `repo_name`)
2. **`docs/site/license.md`** — New file: brief license attribution page
3. No source code changes. No test changes.

### Implementation Details

**mkdocs.yml `copyright` field:**
The `copyright` field is a top-level mkdocs config key. Material theme renders it in the page footer automatically when `navigation.footer` feature is enabled (already enabled in our config). Place it after `repo_name:` for conventional ordering.

```yaml
copyright: "Copyright &copy; 2026 Alberto-Codes &mdash; MIT License"
```

**`docs/site/license.md` content:**
Keep it brief — a title, one-paragraph summary of MIT terms, and a link to the full LICENSE file in the GitHub repo. Use the existing Privacy Policy page (`docs/site/privacy.md`) as a structural reference for a standalone info page.

**Nav placement in `mkdocs.yml`:**
Add after Privacy Policy in the nav list:
```yaml
  - License: license.md
```

### Key Constraints

- **No source code changes** — purely `mkdocs.yml` config + one new markdown file
- **~15 lines changed** total across both files
- **No new tests** — `mkdocs build --strict` is the quality gate
- **Copyright symbol**: Use `&copy;` HTML entity (mkdocs renders HTML entities in the copyright field)
- **Em dash**: Use `&mdash;` for the separator between copyright holder and license name
- **Link format**: Link to `https://github.com/Alberto-Codes/docvet/blob/main/LICENSE` for the full license text
- **LICENSE file**: MIT License, Copyright 2026 Alberto-Codes (already exists at repo root)

### Anti-Patterns to Avoid

- Do NOT copy the full LICENSE text into the docs page — link to it instead
- Do NOT add a third-party dependency attribution table — this story is about the project's own license, not dependency licenses
- Do NOT modify any Python source files
- Do NOT add the `copyright` field inside the `theme:` section — it's a top-level mkdocs key

### Previous Story Intelligence

**From Story 30.2 (TypedDict refactor):**
- Quick-spec stories should be extremely straightforward with minimal AC complexity
- Quality gates must all pass — for 30.3 the critical gate is `mkdocs build --strict`
- BMAD side artifacts (sprint-status edits) are separate from core implementation
- Code review found only LOW-severity issues on 30.2 — clean execution pattern to follow

### Project Structure Notes

- Docs source: `docs/site/` (configured via `docs_dir: docs/site` in mkdocs.yml)
- Nav structure: manually maintained in `mkdocs.yml` (not auto-generated for top-level pages)
- Material theme with `navigation.footer` already enabled — copyright will render automatically
- Privacy Policy page (`docs/site/privacy.md`) is the structural reference for info pages
- Aligned with project conventions: no Python changes, no `from __future__ import annotations` needed

### References

- [Source: _bmad-output/planning-artifacts/epics-distribution-adoption.md, Story 30.3]
- [Source: mkdocs.yml, theme features and nav structure]
- [Source: LICENSE, MIT License text]
- [FR15: Copyright footer in mkdocs.yml]
- [FR16: License note/page on docs site]
- [NFR10: License attribution changes verified by mkdocs build --strict]

### Test Maturity Piggyback

- **M2**: 5 instances of weak `assert_called_once()` without argument verification in `test_cli.py` (lines 1772, 1782) and `test_lsp.py` (lines 295, 315, 348)
- Note: Commit `ed83ab4` already addressed these — verify they are resolved. If not, strengthen to `assert_called_once_with(...)`.
- Sourced from test-review.md — address alongside this story's work

### Documentation Impact

- Pages: docs/site/license.md (new), mkdocs.yml (config change for copyright footer and nav)
- Nature of update: New license attribution page; copyright footer added to all pages via mkdocs config

## Quality Gates

<!-- All gates mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — all tests pass (1201 passed), no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — N/A (no Python source changes; not in CI pipeline)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean execution, no issues encountered.

### Completion Notes List

- Added `copyright` field to `mkdocs.yml` after `repo_name` — Material theme renders it in the footer automatically via `navigation.footer` feature
- Created `docs/site/license.md` with brief MIT summary and link to GitHub LICENSE file, using Privacy Policy page as structural reference
- Added `License: license.md` to nav after Privacy Policy
- All quality gates pass: ruff, ruff format, ty, pytest (1201 passed), docvet, mkdocs build --strict

### Change Log

- 2026-03-05: Implemented license attribution — copyright footer and license page
- 2026-03-05: Code review approved — 3 LOW findings dismissed by party mode consensus

### File List

- `mkdocs.yml` — modified (added `copyright` field and `License` nav entry)
- `docs/site/license.md` — new (license attribution page)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

**Approved** — zero actionable findings. Party mode consensus: all 3 LOW findings are cosmetic and not warranted for this PR.

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| L1 | LOW | License page lacks effective date (unlike Privacy Policy) | Dismissed — privacy policies need dates (legal versioning); license pages do not |
| L2 | LOW | License page doesn't name copyright holder | Dismissed — copyright footer already displays holder on every page; duplicating creates maintenance surface |
| L3 | LOW | No `hide: [toc]` frontmatter on license page | Dismissed — consistent with Privacy Policy page; future housekeeping if desired |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
