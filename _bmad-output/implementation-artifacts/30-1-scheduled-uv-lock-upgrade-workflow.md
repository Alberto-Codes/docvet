# Story 30.1: Migrate from Dependabot to Renovate

Status: draft
Branch: `chore/renovate-migration`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/284

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **project maintainer**,
I want to replace Dependabot with Renovate for dependency automation,
so that I get full uv support (manifest + lock file updates), built-in lock file maintenance (replacing the need for a custom `uv lock --upgrade` workflow), and a config that scales to sibling projects via shared presets.

## Acceptance Criteria

1. **Given** the Renovate GitHub App is installed on `Alberto-Codes/docvet`, **when** Renovate runs its onboarding, **then** it detects `pyproject.toml` + `uv.lock` as a PEP 621/uv project and proposes an onboarding PR with the expected config.

2. **Given** `renovate.json` is committed to the repo root, **when** Renovate runs on schedule (weekly Monday before 06:00 UTC), **then** it opens grouped PRs for Python minor/patch updates, separate PRs for Python major updates, grouped PRs for GitHub Actions updates, and a lock file maintenance PR that re-resolves the full dependency tree.

3. **Given** `renovate.json` is committed, **when** reviewing the config, **then** `lockFileMaintenance` is enabled with weekly Monday schedule, replacing the need for a custom `uv lock --upgrade` workflow.

4. **Given** the migration is complete, **when** checking the repository, **then** `.github/dependabot.yml` is deleted and `.github/workflows/uv-lock-upgrade.yml` does not exist.

5. **Given** the `renovate.json` config, **when** reviewing its structure, **then** it is designed as a standalone config that can be directly extracted to a future `Alberto-Codes/renovate-config` shared preset repo without redesign.

## Tasks / Subtasks

- [ ] Task 0: Install Renovate GitHub App on `Alberto-Codes/docvet` (MANUAL — repo owner prerequisite)
  - [ ] 0.1 Install from https://github.com/apps/renovate
  - [ ] 0.2 Scope to `Alberto-Codes/docvet` repository only (not all repos yet)
  - [ ] 0.3 Verify onboarding PR is created — confirm it detects uv/PEP 621
- [ ] Task 1: Add `renovate.json` to repo root (AC: 1, 2, 3, 5)
  - [ ] 1.1 Create `renovate.json` with `config:recommended` base
  - [ ] 1.2 Enable `lockFileMaintenance` on weekly Monday schedule
  - [ ] 1.3 Add `packageRules` for grouped GitHub Actions (weekly Monday)
  - [ ] 1.4 Add `packageRules` for grouped Python minor/patch (weekly Monday)
  - [ ] 1.5 Add `packageRules` for ungrouped Python major (default schedule)
- [ ] Task 2: Delete `.github/dependabot.yml` (AC: 4)
  - [ ] 2.1 Remove the file
  - [ ] 2.2 Close any open Dependabot PRs (manual — after merge)
- [ ] Task 3: Clean up untracked uv-lock-upgrade workflow (AC: 4)
  - [ ] 3.1 Delete `.github/workflows/uv-lock-upgrade.yml` from working tree
- [ ] Task 4: Verify Renovate behavior (AC: 1, 2, 3)
  - [ ] 4.1 Merge PR to main
  - [ ] 4.2 Confirm Renovate creates dependency update PRs
  - [ ] 4.3 Confirm lock file maintenance PR appears on schedule

## AC-to-Test Mapping

<!-- Config-only story — no automated tests. Validation is manual via Renovate dashboard. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: verify onboarding PR detects uv | Pending |
| 2 | Manual: verify grouped PRs created on schedule | Pending |
| 3 | Manual: verify lockFileMaintenance PR appears | Pending |
| 4 | File inspection: dependabot.yml deleted, uv-lock-upgrade.yml absent | Pending |
| 5 | Config review: renovate.json is preset-extractable | Pending |

## Dev Notes

### Architecture & Pattern Compliance

- **Config-only story**: No Python source changes, no tests — pure CI/config swap
- **Preset-shaped config**: The `renovate.json` is written as a standalone config that doubles as a future shared preset. When `Alberto-Codes/renovate-config` is created, the config block moves there verbatim and docvet's config shrinks to `{ "extends": ["github>Alberto-Codes/renovate-config"] }`
- **No automerge yet**: Renovate docs recommend introducing automerge gradually (patch first, then minor after 1-2 weeks). Out of scope for this story — enable in a future story after validating Renovate behavior

### Why Renovate over Dependabot

Research findings (party mode session, 2026-03-05):

1. **Dependabot's uv limitations**: Updates `uv.lock` but [does not update `pyproject.toml`](https://github.com/dependabot/dependabot-core/issues/12788). Known sync issues with transitive deps ([#13912](https://github.com/dependabot/dependabot-core/issues/13912))
2. **uv official recommendation**: The [uv docs](https://docs.astral.sh/uv/guides/integration/dependency-bots/) give Renovate more coverage and recommend it as the more mature option
3. **`lockFileMaintenance`**: Built-in feature that re-resolves the entire dependency tree on schedule — equivalent to `uv lock --upgrade` without a custom workflow
4. **Shared presets**: Single config repo (`renovate-config`) can serve all Alberto-Codes sibling projects. Dependabot has no config inheritance
5. **PR triggers CI**: Renovate App uses its own token, so PRs trigger `on: pull_request` workflows (unlike `GITHUB_TOKEN` limitation with custom workflows)

### Renovate Config Design

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 6am on monday"]
  },
  "packageRules": [
    {
      "matchManagers": ["github-actions"],
      "groupName": "github-actions",
      "schedule": ["before 6am on monday"]
    },
    {
      "matchManagers": ["pep621"],
      "matchUpdateTypes": ["minor", "patch"],
      "groupName": "python-minor-patch",
      "schedule": ["before 6am on monday"]
    }
  ]
}
```

**Design rationale:**
- `config:recommended` base — sane defaults, Dependency Dashboard enabled
- `lockFileMaintenance` replaces the custom `uv lock --upgrade` workflow entirely
- Grouped minor/patch to reduce PR noise (matches current Dependabot grouping)
- Major updates ungrouped (default) — these need individual review
- Weekly Monday schedule matches current Dependabot cadence
- No `automerge` — introduce later after validation period
- No `platformAutomerge` — requires branch protection configuration (future story)

### Scale Path (Future Stories)

1. **Shared preset repo**: Create `Alberto-Codes/renovate-config` with `default.json` extracted from this config
2. **Sibling rollout**: Migrate docfresh, gepa-adk, adk-secure-sessions, etc. — each gets a 3-line `renovate.json`
3. **Automerge**: Enable for patch first, then minor after 1-2 weeks of stable operation
4. **Action digest pinning**: `helpers:pinGitHubActionDigests` preset for supply chain security

### Existing Dependabot Config (Being Replaced)

Current `.github/dependabot.yml` configures:
- `github-actions` ecosystem: weekly Monday, grouped, limit 5 PRs
- `uv` ecosystem: weekly Monday, grouped minor/patch, limit 5 PRs, cooldown 7 days

The Renovate config replicates this behavior with added `lockFileMaintenance` and future preset capability.

### Anti-Patterns to Avoid

- Do NOT run both Dependabot and Renovate simultaneously — conflicting PRs
- Do NOT enable automerge before validating Renovate behavior on this repo
- Do NOT scope Renovate App to all repos yet — start with docvet only

### References

- [uv docs: Using uv with dependency bots](https://docs.astral.sh/uv/guides/integration/dependency-bots/)
- [Renovate: PEP 621 / uv manager](https://docs.renovatebot.com/modules/manager/pep621/)
- [Renovate: Shareable Config Presets](https://docs.renovatebot.com/config-presets/)
- [Renovate: lockFileMaintenance](https://docs.renovatebot.com/configuration-options/)
- [Renovate: Bot comparison vs Dependabot](https://docs.renovatebot.com/bot-comparison/)

### Documentation Impact

- Pages: None — no user-facing changes
- Nature of update: N/A (internal CI/config only)

## Quality Gates

<!-- Config-only story. Subset of gates apply. -->

- [ ] `uv run ruff check .` — zero lint violations
- [ ] `uv run ruff format --check .` — zero format issues
- [ ] `uv run pytest` — no regressions (no code changes expected)
- [ ] Renovate onboarding PR validates uv detection
- [ ] No `.github/dependabot.yml` in repo
- [ ] No `.github/workflows/uv-lock-upgrade.yml` in repo

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### Change Log

- 2026-03-05: Original story (uv-lock-upgrade workflow) drafted and reviewed
- 2026-03-05: Party mode research session — team consensus to pivot to Renovate migration. Dependabot's uv limitations + lack of config inheritance + custom workflow redundancy drove the decision

### File List

- `renovate.json` (new)
- `.github/dependabot.yml` (deleted)
- `.github/workflows/uv-lock-upgrade.yml` (deleted — never committed)

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
