# Story 25.2: Audit and Configure Codecov

Status: review
Branch: `feat/ci-25-2-audit-configure-codecov`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/198

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **docvet maintainer**,
I want Codecov properly configured with reliable PR comments and badge updates,
so that coverage feedback is consistent and contributors see coverage impact on every PR.

## Acceptance Criteria

1. **Given** the Codecov GitHub App is not installed
   **When** the audit is complete
   **Then** a decision is documented on whether to install the App (yes/no with rationale)

2. **Given** no `codecov.yml` exists
   **When** the audit recommends adding one
   **Then** `codecov.yml` is committed with project/patch coverage targets and PR comment configuration

3. **Given** the README badge `[![Coverage](https://codecov.io/gh/...)]`
   **When** the badge strategy is decided
   **Then** the badge updates reliably on pushes to main

4. **Given** a PR is opened against main
   **When** CI runs and uploads coverage
   **Then** Codecov PR comments appear consistently showing coverage delta

5. **Given** all changes are applied
   **When** `uv run pytest` is executed
   **Then** all tests pass

## Tasks / Subtasks

- [x] Task 1: Document and action Codecov GitHub App decision (AC: 1)
  - [x] 1.1: Check if Codecov GitHub App is already installed on `Alberto-Codes/docvet`
  - [x] 1.2: Document decision: **INSTALL** — reliable PR comments, status checks, tokenless fork uploads
  - [x] 1.3: **MAINTAINER ACTION REQUIRED**: Install Codecov GitHub App via GitHub Settings > Integrations > Codecov. Dev agent cannot automate this step — flag clearly in Dev Notes and PR description
- [x] Task 2: Create minimal `codecov.yml` configuration file (AC: 2, 4)
  - [x] 2.1: Create `codecov.yml` at repo root with project coverage target 85% (matching CI `--cov-fail-under`)
  - [x] 2.2: Set patch coverage target 80% (new code should maintain but not require 100%)
  - [x] 2.3: Configure PR comment layout
  - [x] 2.4: Document decision: **SKIP Components and Flags** — codebase too small for per-module tracking, Flags add CI complexity for zero insight at this scale
- [x] Task 3: Badge strategy (AC: 3)
  - [x] 3.1: Decision: **KEEP Codecov native badge** — reliability issues likely caused by missing App install. Revisit only if badge remains unreliable after App installation
  - [x] 3.2: No README badge URL change needed (keep current `graph/badge.svg`)
  - [ ] 3.3: **Post-merge verification required**: Confirm badge updates reliably after Codecov App install and merge to main
- [x] Task 4: CI pipeline verification (AC: 4, 5)
  - [x] 4.1: Keep `fail_ci_if_error: false` — upload failures are informational, not a gate. The gate is `--cov-fail-under=85` in pytest
  - [x] 4.2: Decision: **Keep `--cov-fail-under=85` in CI workflow only** — single source of truth. `codecov.yml` project target is for Codecov status checks, not CI enforcement
  - [x] 4.3: Run `uv run pytest` to verify all tests pass
- [x] Task 5: Finalize and verify (AC: 1-5)
  - [x] 5.1: Document all 5 decision points with rationale in Dev Notes
  - [ ] 5.2: **On-PR verification required**: Confirm Codecov PR comment with coverage delta appears on story's own PR after CI runs

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Verified: `codecov-commenter` bot warns "install the Codecov app" on PR #196; decision documented in Dev Notes decision table | PASS |
| 2 | Verified: `codecov.yml` exists at repo root with `project: 85%`, `patch: 80%`, comment layout configured | PASS |
| 3 | **Verified post-merge**: Badge strategy decided (keep native). Badge reliability confirmed after App install + merge to main | DEFERRED |
| 4 | **Verified on-PR**: Codecov PR comment with coverage delta appears on story's own PR after CI runs | DEFERRED |
| 5 | `uv run pytest` — 971 passed in 7.96s, zero regressions | PASS |

## Dev Notes

- **This is a CI/config story** — no new Python source code, no new tests. Deliverables are `codecov.yml`, possible CI workflow tweaks, badge update, and decision documentation.
- **Maintainer-dependent step**: Installing the Codecov GitHub App requires manual action in GitHub Settings > Integrations. The dev agent can document the recommendation but cannot install it.
- **Current Codecov state** (verified 2026-02-28):
  - `codecov/codecov-action@v5` uploads from Ubuntu + Python 3.12 matrix cell only
  - No `codecov.yml` — all Codecov defaults
  - `CODECOV_TOKEN` in GitHub Secrets
  - `fail_ci_if_error: false` (upload failures don't break CI)
  - `--cov-fail-under=85` in CI workflow `.github/workflows/ci.yml:63`, NOT in `pyproject.toml`
  - README badge: `[![Coverage](https://codecov.io/gh/Alberto-Codes/docvet/graph/badge.svg)]`
  - CI matrix: 3 OS (ubuntu, macos, windows) x 2 Python (3.12, 3.13) — upload only from ubuntu/3.12

### Five Decision Points (from Issue #182) — RESOLVED via Party Mode

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| 1 | Install Codecov GitHub App | **YES** (maintainer action) | Reliable PR comments, status checks, tokenless fork uploads. No downside. |
| 2 | Add `codecov.yml` | **YES** — minimal config | Project 85%, patch 80%, PR comment layout. Don't over-engineer. |
| 3 | Components vs Flags | **SKIP BOTH** | Codebase too small (~5 modules, ~970 tests). Global coverage tells full story. Components add config to maintain for zero insight. Flags require splitting CI uploads. |
| 4 | Badge strategy | **KEEP native, revisit post-App** | Unreliability likely caused by missing App. Install first, give it a week. Switch to Shields.io only if still broken. |
| 5 | `--cov-fail-under` location | **CI workflow only** | Single source of truth for CI gate. `codecov.yml` targets serve Codecov status checks, not CI enforcement. Dual enforcement creates confusion. |

### AC Verification Notes

- **AC 1**: Verified via documented decision in Dev Notes
- **AC 2**: Verified via `codecov.yml` file existence and content
- **AC 3**: **Verified post-merge** — badge update confirmed on next push to main after PR merges. Cannot be verified locally
- **AC 4**: **Verified on-PR** — the story's own PR is the integration test. If Codecov comment appears, AC passes
- **AC 5**: Verified via `uv run pytest`

### Previous Story Intelligence (25.1)

- Story 25.1 was a convention/cleanup story (pytestmark standardization) — no runtime changes
- All 971 tests pass after 25.1 changes
- Code review found 1 follow-up (M1: no automated enforcement of pytestmark convention) — not relevant to this story
- Code review found pre-existing gap (L1: `test_exports.py` missing `docvet.lsp`) — not relevant to this story
- Pattern: cleanup/config stories need clear decision documentation in Dev Notes

### Git Intelligence

- Most recent commit: `a32582a chore(test): standardize pytestmark usage across all test files (#196)` — Story 25.1
- CI workflow last modified in Epic 23 (cross-platform matrix, positional args, JSON output, pre-commit hook)
- No recent changes to coverage infrastructure

### Project Structure Notes

- `codecov.yml` goes at repo root (standard Codecov convention)
- CI workflow at `.github/workflows/ci.yml`
- README badge section at line 3 of `README.md`
- No conflicts with existing structure

### References

- [Source: GitHub Issue #182] — 5 decision points, current state audit, acceptance criteria
- [Source: .github/workflows/ci.yml:63-71] — current Codecov upload configuration
- [Source: README.md:3] — current Coverage badge
- [Source: _bmad-output/planning-artifacts/epics.md#Story 25.2] — epic acceptance criteria and implementation notes
- [Source: pyproject.toml:145-157] — pytest configuration (no `--cov-fail-under` in addopts)

### Post-Merge Maintainer Actions

After this PR merges to main, the maintainer should complete these in a single pass:

- [ ] Install Codecov GitHub App via GitHub Settings > Integrations > Codecov
- [ ] Verify badge updates on next push to main (AC 3 / Task 3.3)
- [ ] Verify Codecov PR comment appears on next PR (AC 4 / Task 5.2)
- [ ] Flip `codecov.yml` `require_changes: false` → `true` (bootstrap period complete)

### Documentation Impact

- Pages: None — this story changes CI configuration and adds `codecov.yml`, no docs-site pages affected
- Nature of update: N/A — no user-facing docvet behavior changes

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 971 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% (>= 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug sessions required. CI/config story with zero implementation issues.

### Completion Notes List

- Verified Codecov GitHub App is NOT installed — `codecov-commenter` bot warns on PR #196
- Decision: Install App (maintainer action required, cannot be automated)
- Created `codecov.yml` at repo root with project target 85%, patch target 80%, comment layout
- Decided to SKIP Components and Flags (codebase too small)
- Decided to KEEP Codecov native badge (revisit post-App-install)
- Decided to KEEP `--cov-fail-under=85` in CI workflow only (single source of truth)
- Decided to KEEP `fail_ci_if_error: false` (upload failures are informational)
- No CI workflow changes needed — existing configuration is correct
- No README badge changes needed
- All 6 quality gates pass: ruff, format, ty, pytest (971 passed), docvet, interrogate (100%)
- ACs 3 and 4 are deferred to post-merge/on-PR verification (cannot be validated locally)

### Change Log

- 2026-02-28: Created `codecov.yml` with minimal configuration (project 85%, patch 80%, comment layout)
- 2026-02-28: Documented all 5 decision points from Issue #182 with rationale
- 2026-02-28: Code review — unchecked deferred tasks 3.3/5.2, added Post-Merge Maintainer Actions checklist, kept `require_changes: false` as intentional bootstrap

### File List

- `codecov.yml` — **NEW**: Codecov configuration with project/patch targets and PR comment layout
- `_bmad-output/implementation-artifacts/25-2-audit-and-configure-codecov.md` — story file updates
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status update

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow + party mode consensus)

### Outcome

Changes Requested → Fixed (3 of 5 findings addressed, 2 accepted as-is)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Task 3.3 marked [x] but post-merge verification not yet done | Fixed: unchecked task, reworded as pending verification |
| H2 | HIGH | Task 5.2 marked [x] but on-PR verification not yet done | Fixed: unchecked task, reworded as pending verification |
| M1 | MEDIUM | `require_changes: false` adds noise to non-code PRs | Intentional bootstrap — flip to `true` after Codecov App confirmed working (noted in Post-Merge Maintainer Actions) |
| L1 | LOW | Non-story commit (Epic 23 retro) on feature branch | Accepted: squash merge will consolidate; awareness for future workflow |
| L2 | LOW | Deferred ACs lack follow-up tracking mechanism | Fixed: added Post-Merge Maintainer Actions checklist to Dev Notes |

### Verification

- [x] All acceptance criteria verified (3 PASS, 2 DEFERRED with tracking mechanism)
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
