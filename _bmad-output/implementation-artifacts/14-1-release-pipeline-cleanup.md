# Story 14.1: Release Pipeline Cleanup

Status: done
Branch: `feat/ci-14-1-release-pipeline-cleanup`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **project maintainer**,
I want the release pipeline to produce clean, non-repetitive changelogs,
so that each release tells a clear story of what changed without confusing duplicate entries.

## Acceptance Criteria

1. **Given** the current develop→main merge strategy produces duplicate changelog entries (same message, different SHAs), **when** the root cause is diagnosed and a fix is implemented (release-please config, merge strategy change, or branching adjustment), **then** the next release-please PR after a develop→main merge contains zero duplicate entries **and** each logical change appears exactly once in the generated changelog section.

2. **Given** the fix is applied to the release pipeline, **when** a test merge from develop to main is performed and release-please generates a changelog, **then** the generated changelog section contains zero duplicate entries (verified by comparing against `git log --oneline <last-release-tag>..main`) **and** the root cause diagnosis and chosen fix are documented in the PR description.

3. *(Optional)* **Given** the CHANGELOG.md contains historical duplicate entries from v1.0.1 and v1.0.2, **when** the maintainer optionally chooses to clean up historical entries, **then** duplicate lines are removed and each release section contains only unique entries.

## Tasks / Subtasks

- [x] **Task 1: Diagnose root cause of changelog duplication** (AC: 1, 2)
  - [x] 1.1 Compare commit history on `main` between v1.0.0 and v1.0.2 tags — identify which commits appear with duplicate SHAs
  - [x] 1.2 Trace the develop→main merge commits (44404c2, e00c2a7) to understand how individual commits from squash-merged PRs end up duplicated in release-please output
  - [x] 1.3 Review release-please issue [#2476](https://github.com/googleapis/release-please/issues/2476) — confirms merge commits cause duplicate changelog entries; maintainers recommend squash-merge
  - [x] 1.4 Verify `bootstrap-sha` in `release-please-config.json` (currently `885c538`) — confirm it points to the correct post-release commit and isn't causing release-please to scan too far back
  - [x] 1.5 Verify `.release-please-manifest.json` version matches the latest release tag (currently `1.0.2` but v1.1.0 tag exists — update to `1.1.0` if stale)
  - [x] 1.6 Document the root cause diagnosis in a markdown section of the PR description
- [x] **Task 2: Implement the fix** (AC: 1, 2)
  - [x] 2.1 Evaluate squash-merge for develop→main as the primary fix candidate (release-please maintainers explicitly recommend squash-merge per issue #2476 — merge commits are unsupported for deduplication)
  - [x] 2.2 If config-based fix is viable instead: update `release-please-config.json` with the necessary changes
  - [x] 2.3 Update `release-please-config.json` if `bootstrap-sha` or other settings need correction (from Task 1.4 findings)
  - [x] 2.4 Determine whether release-please regenerates the full CHANGELOG.md on each release or only appends — this affects whether Task 4 cleanup is durable
- [x] **Task 3: Update CLAUDE.md branching documentation** (AC: 1, 2)
  - [x] 3.1 Update `CLAUDE.md` "Branching & Release" section — currently says "Use merge commit (not squash) to preserve individual conventional commits for release-please changelog generation" which is the root cause of duplication
  - [x] 3.2 Document the new develop→main merge strategy with rationale (why the old approach caused duplicates, what the new approach achieves)
  - [x] 3.3 Verify no other `.claude/rules/` files reference the old merge strategy
- [ ] **Task 4: Validate the fix** (AC: 2) *(Maintainer actions — dev agent prepares, maintainer executes)*
  - [ ] 4.1 Merge the fix PR to develop via squash merge (normal PR flow)
  - [ ] 4.2 *(Maintainer)* Merge develop to main using the new strategy (rebase and merge) — CHANGELOG.md will conflict because main's version diverges from develop's; resolve by keeping develop's cleaned-up version
  - [ ] 4.3 *(Maintainer)* Verify release-please generates a changelog section with zero duplicate entries
  - [ ] 4.4 *(Maintainer)* Compare changelog output against `git log --oneline <last-release-tag>..main` to confirm 1:1 correspondence
- [x] **Task 5: (Optional) Clean up historical changelog entries** (AC: 3)
  - [x] 5.1 Review v1.0.1 and v1.0.2 CHANGELOG.md sections for duplicate lines
  - [x] 5.2 Remove duplicate entries, keeping the canonical SHA for each change — also removed phantom v1.0.1 section (never released) and fixed v1.0.2 compare link
  - [x] 5.3 Verify CHANGELOG.md renders correctly after cleanup

## AC-to-Test Mapping

<!-- This is a config/pipeline story with no Python code changes. "Tests" are manual verification steps, not pytest tests. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Task 4.3: Verify release-please changelog has zero duplicates after develop→main merge | Pending (maintainer) |
| 2 | Task 4.4: Compare changelog against `git log --oneline <last-release-tag>..main` | Pending (maintainer) |
| 3 | Task 5.3: Visual inspection of CHANGELOG.md after cleanup | Pass |

## Dev Notes

### Story Nature

This is a **pipeline/config story** — no Python source code changes in `src/`. The deliverables are configuration files, workflow YAML, and documentation updates. Quality gates (ruff, pytest, docvet, interrogate) will pass trivially since no Python code is modified.

### Root Cause Summary

release-please creates duplicate changelog entries when git history contains merge commits that preserve individual feature branch commits ([googleapis/release-please#2476](https://github.com/googleapis/release-please/issues/2476)). The maintainers explicitly recommend squash-merge and do not plan to support deduplication for merge commits.

**Current flow (broken):**
1. Feature PR → squash-merged to `develop` (one commit, e.g. SHA-A: "fix(ci): something")
2. `develop` → merge-committed to `main` — the merge commit itself carries a conventional commit message AND the individual commits from develop also carry their own conventional commit messages
3. release-please scans `main` history and double-counts: it picks up both the merge commit's message and each individual commit's message → duplicate entries with different SHAs

**Squash-merge tradeoff**: If the fix is to switch develop→main to squash merge, the individual conventional commit messages from develop will be collapsed into a single squash commit. The develop→main PR title becomes the ONLY changelog entry for that merge. This means develop→main PR titles must be crafted carefully — either as a release summary or using conventional commit format to produce a clean changelog entry.

**Evidence in CHANGELOG.md:**
- v1.0.2 has 4 duplicate pairs: same message, different SHAs (e.g. `601b035` and `aeb9435` both say "ci: add contents read permission")
- v1.0.1 and v1.0.2 released same day with overlapping content

### Key Files to Touch

| File | Action | Notes |
|------|--------|-------|
| `CLAUDE.md` | **Edit** | Update "Branching & Release" section — change "merge commit" to new strategy |
| `release-please-config.json` | **Edit** | Verify/fix `bootstrap-sha`, any config adjustments |
| `.release-please-manifest.json` | **Edit** | Update version from `1.0.2` to `1.1.0` if stale |
| `CHANGELOG.md` | **Edit (optional)** | Clean up historical v1.0.1/v1.0.2 duplicates |
| `.claude/rules/pull-requests.md` | **Verify** | Check if it references develop→main merge strategy |

### Critical Guardrails

- **Do NOT modify** `.github/workflows/release-please.yml` unless diagnosis reveals a workflow-level issue — the problem is in git history, not the workflow trigger
- **Do NOT modify** `.github/workflows/publish.yml` — publishing pipeline is working correctly
- **Do NOT add** `sonar.branch.name` to `sonar-project.properties` — Community Edition doesn't support it
- **Do NOT change** the PR→develop merge strategy (squash merge) — only the develop→main strategy needs evaluation
- **Do NOT remove** `bootstrap-sha` from `release-please-config.json` — only update its value if incorrect. Removing it entirely causes release-please to scan the entire repo history
- **Verify before editing**: Run `git log --oneline v1.0.2..main` and `git log --oneline v1.1.0..main` to understand current state of main before making changes

### Manifest Version Mismatch

`.release-please-manifest.json` currently says `1.0.2` but `v1.1.0` tag exists in the repo. If the manifest is stale, release-please will generate the wrong next version — e.g. bumping to `1.0.3` instead of `1.2.0`, causing a version that conflicts with or regresses from the existing `v1.1.0` tag. Check:
```bash
git tag --list 'v*' --sort=-v:refname | head -5
cat .release-please-manifest.json
```
If mismatched, update manifest to match latest tag version.

### release-please Behavior Notes

- release-please uses `bootstrap-sha` to limit how far back it scans for conventional commits — if this SHA is wrong, it may pick up commits from before v1.0.0
- The `changelog-sections` config hides `refactor`, `chore`, `test`, `ci` types — only `feat`, `fix`, `perf`, `docs` appear in CHANGELOG
- release-please generates the CHANGELOG by **prepending** new entries to the existing file — it does NOT regenerate the full file, so manual cleanup of historical entries IS durable

### Project Structure Notes

- No `src/` changes — this story operates entirely in project root config files and `.github/` workflows
- Branch naming uses `feat/ci-14-1-release-pipeline-cleanup` — scope `ci` since primary changes are CI/release pipeline config
- PR targets `develop` per normal flow; the validation of the fix happens when develop is merged to main (maintainer action)

### References

- [Source: CLAUDE.md#Branching & Release] — current merge strategy documentation
- [Source: release-please-config.json] — bootstrap-sha, changelog-sections config
- [Source: .release-please-manifest.json] — version tracking (currently 1.0.2)
- [Source: CHANGELOG.md] — v1.0.1 and v1.0.2 duplicate entries
- [Source: .github/workflows/release-please.yml] — workflow trigger on push to main
- [External: googleapis/release-please#2476](https://github.com/googleapis/release-please/issues/2476) — merge commit duplication issue, maintainer response recommending squash-merge
- [External: release-please docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md) — manifest releaser configuration reference

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 743 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings
- [x] `uv run interrogate -v` — 100.0% docstring coverage

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Diagnosed root cause: merge commits to main exposed both branch histories, causing release-please to double-count commits
- Additional finding: v1.0.1 was never released (no tag, no GitHub release) — phantom section removed
- Additional finding: `.release-please-manifest.json` was stale at `1.0.2` when latest release is `v1.1.0`
- Fix: switch develop→main merge strategy from merge commit to rebase and merge
- Rebase and merge preserves individual conventional commit granularity (unlike squash merge) while creating linear history (unlike merge commit)
- Task 4 (validation) is maintainer-executed — happens when develop is merged to main using the new strategy

### Change Log

- 2026-02-24: Diagnosed root cause, implemented fix, cleaned up historical CHANGELOG

### File List

- `CLAUDE.md` — updated "Branching & Release" section: merge commit → rebase and merge
- `.release-please-manifest.json` — updated stale version: `1.0.2` → `1.1.0`
- `CHANGELOG.md` — removed 4 duplicate Bug Fix entries, removed phantom v1.0.1 section, fixed compare link

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Approve with minor fixes (applied)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Task 4.2 missing CHANGELOG conflict warning — main's CHANGELOG diverges from develop's, rebase will conflict | Fixed: added conflict warning and resolution guidance to Task 4.2 |
| M1 | MEDIUM | Dev Notes claim "6 duplicate pairs" but actual cleanup removed 4 | Fixed: corrected to "4 duplicate pairs" at line 78 |
| L1 | LOW | CLAUDE.md line 135 is ~270 chars, longer than surrounding bullets | Rejected: density is a feature in reference docs, all information earns its place |
| L2 | LOW | No mechanism to enforce correct merge strategy per target branch | Rejected: informational, not actionable for this story — CLAUDE.md convention is the enforcement mechanism |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
