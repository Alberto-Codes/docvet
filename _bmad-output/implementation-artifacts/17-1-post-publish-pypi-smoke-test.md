# Story 17.1: Post-Publish PyPI Smoke Test

Status: review
Branch: `feat/ci-17-1-post-publish-smoke-test`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **maintainer**,
I want a CI job that installs docvet from PyPI after each release and verifies it works,
so that I can trust published releases are functional without manual verification.

## Acceptance Criteria

1. **Given** the publish workflow completes successfully, **when** the smoke-test job runs, **then** it waits for PyPI propagation (~60s) before attempting install.
2. **Given** the smoke-test job runs after propagation wait, **when** it installs docvet, **then** it uses `pip install --no-cache-dir docvet==$VERSION` where `$VERSION` is extracted from the release tag (strip leading `v`).
3. **Given** docvet is installed from PyPI, **when** the smoke-test job runs `docvet --version`, **then** exit code is 0.
4. **Given** docvet is installed from PyPI, **when** the smoke-test job runs `docvet check --help`, **then** exit code is 0.
5. **Given** the `build-and-publish` job fails, **when** the workflow evaluates job dependencies, **then** the smoke-test job is skipped (via `needs: [build-and-publish]`).
6. **Given** the smoke-test job is added, **when** the `update-tags` job runs, **then** it still depends only on `build-and-publish` (not on smoke-test) to preserve existing behavior.

## Tasks / Subtasks

- [x] Task 1: Add `smoke-test` job to `publish.yml` (AC: #1, #2, #3, #4, #5)
  - [x] 1.1: Define job with `needs: [build-and-publish]` and `runs-on: ubuntu-latest`
  - [x] 1.2: Add step to extract version from `GITHUB_REF_NAME` (strip `v` prefix)
  - [x] 1.3: Add step to wait ~60s for PyPI propagation
  - [x] 1.4: Add step to install docvet from PyPI: `pip install --no-cache-dir docvet==$VERSION`
  - [x] 1.5: Add step to verify `docvet --version` (exit code 0)
  - [x] 1.6: Add step to verify `docvet check --help` (exit code 0)
- [x] Task 2: Verify `update-tags` job dependency unchanged (AC: #6)
  - [x] 2.1: Confirm `update-tags` still has `needs: [build-and-publish]` only

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->
<!-- NOTE: This story modifies a GitHub Actions workflow — acceptance criteria are verified by workflow structure inspection, not pytest tests. Manual verification via workflow YAML review. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | Workflow YAML: `sleep 60` step present in smoke-test job (line 71) | PASS |
| AC2 | Workflow YAML: `pip install --no-cache-dir docvet==$VERSION` with version extraction (lines 66-68, 74) | PASS |
| AC3 | Workflow YAML: `docvet --version` step present (line 77) | PASS |
| AC4 | Workflow YAML: `docvet check --help` step present (line 80) | PASS |
| AC5 | Workflow YAML: `needs: [build-and-publish]` on smoke-test job (line 64) | PASS |
| AC6 | Workflow YAML: `update-tags` still has `needs: [build-and-publish]` only (line 84) | PASS |

## Dev Notes

### Architecture & Implementation Guide

**File to modify:** `.github/workflows/publish.yml`

**Current workflow structure:**
```
jobs:
  build-and-publish:    # Build, smoke-test wheel, verify version, publish, attest
    ...
  update-tags:          # Update floating v1 tag
    needs: build-and-publish
    ...
```

**Target workflow structure:**
```
jobs:
  build-and-publish:    # (unchanged)
    ...
  smoke-test:           # NEW — install from PyPI and verify
    needs: [build-and-publish]
    ...
  update-tags:          # (unchanged — still needs: build-and-publish only)
    needs: build-and-publish
    ...
```

**Version extraction pattern** (already used in `build-and-publish` job):
```yaml
TAG_VERSION="${GITHUB_REF_NAME#v}"
```

**Permissions:** The smoke-test job only needs to install from PyPI and run CLI commands. No special permissions required beyond the default `contents: read`. Since `publish.yml` does not declare top-level `permissions:`, each job that needs elevated permissions declares its own. The smoke-test job can omit `permissions:` entirely (defaults are sufficient).

**PyPI propagation:** NFR1 requires ~60s wait. A simple `sleep 60` is the most reliable approach — no need for retry loops or polling. The publish step in `build-and-publish` already succeeds before the smoke-test job starts, so the package upload is complete; we're just waiting for CDN propagation.

**Install command:** Use `pip install --no-cache-dir docvet==$VERSION` (not `uv pip install`) to match what end users do. `--no-cache-dir` ensures a fresh download from PyPI, not a cached wheel.

**CI lessons from CLAUDE.md:** When declaring `permissions:` in a job, all unmentioned permissions default to `none`. Always include `contents: read` if checkout is needed. However, the smoke-test job doesn't need checkout — it installs from PyPI directly.

### Project Structure Notes

- Only `.github/workflows/publish.yml` is modified — no source code changes
- No new files created
- Aligns with existing workflow patterns (job dependency chaining, version extraction from tag)
- No impact on `ci.yml`, `release-please.yml`, or `docs.yml`

### References

- [Source: .github/workflows/publish.yml] — current publish workflow with build-and-publish + update-tags jobs
- [Source: _bmad-output/planning-artifacts/epics-next.md#Epic 1] — Epic 17 requirements (FR1, FR2, NFR1, NFR2)
- [Source: CLAUDE.md#CI/CD Pipeline Lessons] — OIDC and permissions lessons
- [Source: .release-please-manifest.json] — current version 1.3.0
- [Source: release-please-config.json] — release configuration

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 762 passed, zero regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% (threshold 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no debug issues.

### Completion Notes List

- Added `smoke-test` job to `.github/workflows/publish.yml` between `build-and-publish` and `update-tags`
- Job depends on `build-and-publish` via `needs:` — skipped if publish fails (AC5)
- Version extracted from release tag using `${GITHUB_REF_NAME#v}` via `GITHUB_OUTPUT` (AC2)
- 60-second sleep for PyPI CDN propagation (AC1)
- Fresh install via `pip install --no-cache-dir` to match end-user experience (AC2)
- Two verification steps: `docvet --version` (AC3) and `docvet check --help` (AC4)
- `update-tags` dependency unchanged — still only `needs: build-and-publish` (AC6)
- No source code changes, no new tests needed (CI-only story)
- All 6 quality gates pass with zero issues

### Change Log

- 2026-02-25: Added post-publish PyPI smoke test job to publish workflow

### File List

- `.github/workflows/publish.yml` (modified — added `smoke-test` job)

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
