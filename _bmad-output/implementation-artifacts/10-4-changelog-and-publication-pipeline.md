# Story 10.4: CHANGELOG and Publication Pipeline

Status: review

## Story

As a package maintainer,
I want a CHANGELOG documenting v1.0.0 and a validated publish pipeline,
so that the package is professionally released with an auditable history.

## Acceptance Criteria

1. **Given** no CHANGELOG exists, **when** the v1.0.0 release entry is hand-authored, **then** `CHANGELOG.md` exists at repo root with a curated v1.0.0 entry summarizing: 4 check modules (enrichment, freshness, coverage, griffe), 19 rules, reporting module, CLI with 5 subcommands, pre-commit hook, and GitHub Action.
2. **Given** release-please config is in place, **when** `release-please-config.json` and `.release-please-manifest.json` are created, **then** release-please can read conventional commits from `main` and generate release PRs that bump `pyproject.toml` version and update `CHANGELOG.md` — with `bootstrap-sha` set to prevent genesis commit flood.
3. **Given** no release workflows exist, **when** `.github/workflows/release-please.yml` is created, **then** it triggers on pushes to `main`, runs `googleapis/release-please-action@v4`, and outputs release metadata (tag, upload_url, release_created).
4. **Given** no publish workflow exists, **when** `.github/workflows/publish.yml` is created, **then** it triggers on `release: [published]`, builds with `uv build --no-sources`, smoke-tests the wheel (size <500KB, no test data), publishes to PyPI via OIDC trusted publishing (`uv publish`), and updates the floating `v1` tag.
5. **Given** no TestPyPI workflow exists, **when** `.github/workflows/test-publish.yml` is created, **then** it triggers on `workflow_dispatch`, builds with `uv build --no-sources`, and publishes to TestPyPI via OIDC trusted publishing — independent of release-please.
6. **Given** all pipeline files are in place, **when** `uv build` is run (after `rm -rf dist/`), **then** both wheel and sdist are produced, the wheel installs cleanly in a fresh virtual environment, `docvet check --help` works after install, and `import docvet` works after install.
7. **Given** all changes applied, **when** `uv run pytest` is run, **then** all existing tests continue to pass (729+).

## Tasks / Subtasks

- [x] Task 1: Create `CHANGELOG.md` with hand-curated v1.0.0 entry (AC: #1)
  - [x] 1.1 Write `CHANGELOG.md` at repo root using release-please heading format: `## [1.0.0](url) (date)`
  - [x] 1.2 Include curated summary: 4 check modules, 19 rules, reporting module, 5 CLI subcommands, pre-commit hook, GitHub Action
  - [x] 1.3 Group under Features section only — this is a product announcement, not a commit log
- [x] Task 2: Create release-please configuration (AC: #2)
  - [x] 2.1 Create `release-please-config.json` with `release-type: python`, `package-name: docvet`, `include-component-in-tag: false`, `bootstrap-sha` set to the merge commit SHA, and `changelog-sections` hiding chore/test/ci/refactor
  - [x] 2.2 Create `.release-please-manifest.json` with `{".": "1.0.0"}`
- [x] Task 3: Create `.github/workflows/release-please.yml` (AC: #3)
  - [x] 3.1 Trigger on `push: branches: [main]`
  - [x] 3.2 Use `googleapis/release-please-action@v4` with `config-file` and `manifest-file` inputs
  - [x] 3.3 Output `release_created`, `tag_name`, `upload_url` for downstream consumption
- [x] Task 4: Create `.github/workflows/publish.yml` (AC: #4)
  - [x] 4.1 Trigger on `release: types: [published]`
  - [x] 4.2 Build step: `uv build --no-sources` (produces wheel + sdist)
  - [x] 4.3 Smoke test step: verify wheel <500KB, no `tests/` or `_bmad` in wheel contents
  - [x] 4.4 Publish step: `uv publish` with OIDC trusted publishing (PyPI)
  - [x] 4.5 Attestation step: `astral-sh/attest-action` for supply chain security
  - [x] 4.6 Floating tag step: update `v1` tag via `git tag -f v1 && git push origin v1 --force` (intentional force push for floating tag — requires `contents: write` permission)
- [x] Task 5: Create `.github/workflows/test-publish.yml` (AC: #5)
  - [x] 5.1 Trigger on `workflow_dispatch` (manual button in GitHub Actions UI)
  - [x] 5.2 Build step: `uv build --no-sources`
  - [x] 5.3 Publish step: `uv publish` targeting TestPyPI via OIDC trusted publishing
- [x] Task 6: Verify build and install (AC: #6)
  - [x] 6.1 `rm -rf dist/ && uv build` — clean build produces wheel and sdist
  - [x] 6.2 Wheel installs in fresh venv: `pip install dist/docvet-1.0.0-py3-none-any.whl`
  - [x] 6.3 `docvet check --help` works after install
  - [x] 6.4 `import docvet` works after install
  - [x] 6.5 Wheel size <500KB (NFR56)
- [x] Task 7: Run quality gates (AC: #7)
  - [x] 7.1 `uv run pytest` — all existing tests pass
  - [x] 7.2 `uv run ruff check .` — no lint errors
  - [x] 7.3 `uv run ruff format --check .` — no formatting issues

## AC-to-Test Mapping

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `CHANGELOG.md` exists; contains "1.0.0", "enrichment", "freshness", "coverage", "griffe"; heading matches release-please format `## [1.0.0](...) (2026-02-21)` | PASS |
| AC2 | `release-please-config.json` is valid JSON; has `release-type: python`, `bootstrap-sha: 0924228...`, `include-component-in-tag: false`; `changelog-sections` hides chore/test/ci/refactor; `.release-please-manifest.json` contains `{".": "1.0.0"}` | PASS |
| AC3 | `release-please.yml` triggers on `push: branches: [main]`; uses `googleapis/release-please-action@v4`; outputs `release_created`, `tag_name`, `upload_url` | PASS |
| AC4 | `publish.yml` triggers on `release: [published]`; has build/smoke/publish/attest/tag steps; declares `id-token: write`, `contents: write`, `attestations: write` permissions | PASS |
| AC5 | `test-publish.yml` triggers on `workflow_dispatch`; builds and publishes to TestPyPI via OIDC | PASS |
| AC6 | `rm -rf dist/ && uv build` succeeds; wheel (38KB) installs in fresh venv; `docvet check --help` exits 0; `import docvet` succeeds; wheel <500KB | PASS |
| AC7 | `uv run pytest` — 729 passed, 1 skipped; `ruff check` all passed; `ruff format --check` all formatted | PASS |

## Dev Notes

### Implementation Strategy

This is an **infrastructure/content story** — no source code changes to `src/docvet/`. Six new files created. The main deliverables are the release-please configuration, three GitHub Actions workflows (release-please, publish, test-publish), and a hand-curated CHANGELOG.

**Files to create:**

| File | Purpose | Lines |
|------|---------|-------|
| `CHANGELOG.md` | Hand-curated v1.0.0 entry (release-please manages future entries) | ~40 |
| `release-please-config.json` | Release-please behavior config with polished settings | ~25 |
| `.release-please-manifest.json` | Current version tracker | 1 |
| `.github/workflows/release-please.yml` | Opens release PRs on push to `main` | ~30 |
| `.github/workflows/publish.yml` | Build, smoke-test, publish to PyPI on GitHub Release | ~80 |
| `.github/workflows/test-publish.yml` | Manual TestPyPI publish from any branch | ~40 |

### Branching Strategy

```
feature branch → PR to develop → merge
                                   ↓
                          develop (integration)
                                   ↓ (regular merge via PR, NOT squash)
                          main (release branch)
                                   ↓ (release-please opens release PR)
                          merge release PR → GitHub Release → publish.yml → PyPI
```

**Key rules:**
- `develop` is the integration branch — all feature PRs merge here
- `main` is the release branch — release-please watches here, publishes trigger from here
- **Regular merge (NOT squash) from develop to main** — preserves individual conventional commits so release-please can generate proper changelogs
- `main` does NOT exist yet — the maintainer creates it as part of the launch sequence (not this story's dev tasks — see Launch Sequence below)
- CI (`ci.yml`) already triggers on both `develop` and `main`

### v1.0.0 Release Strategy: "First Release is Sacred"

v1.0.0 is hand-curated, not auto-generated. This is the standard pattern for mature projects (ruff, uv, etc.). The dev agent creates the CHANGELOG and pipeline files. The maintainer executes the actual release.

**Why not let release-please generate v1.0.0?** Because it would dump every commit since repo creation into the changelog (the "genesis commit flood"). Even with `bootstrap-sha`, the first release entry should tell the product story, not list commits.

**After v1.0.0**, release-please takes over:
- `bootstrap-sha` in config tells release-please "v1.0.0 already happened, start tracking from here"
- Future conventional commits on `main` generate clean, grouped changelogs
- Only Features, Bug Fixes, Performance, and Documentation show — noise types (chore, test, ci, refactor) are hidden

### release-please Configuration (Polished)

**`release-please-config.json`:**
```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "bootstrap-sha": "<full 40-char SHA — set to develop HEAD at time of PR merge>",
  "packages": {
    ".": {
      "release-type": "python",
      "package-name": "docvet",
      "include-component-in-tag": false,
      "changelog-sections": [
        { "type": "feat",     "section": "Features" },
        { "type": "fix",      "section": "Bug Fixes" },
        { "type": "perf",     "section": "Performance Improvements" },
        { "type": "docs",     "section": "Documentation" },
        { "type": "refactor", "section": "Refactoring",    "hidden": true },
        { "type": "chore",    "section": "Miscellaneous",  "hidden": true },
        { "type": "test",     "section": "Tests",           "hidden": true },
        { "type": "ci",       "section": "CI",              "hidden": true }
      ]
    }
  }
}
```

**Key settings explained:**
- `$schema` — enables IDE validation and autocomplete
- `bootstrap-sha` — prevents genesis commit flood. Set to the merge commit SHA of THIS story's PR. **Remove this field after the first release-please PR is merged** (it's only consulted on the first run).
- `release-type: "python"` — automatically handles `pyproject.toml` version bumping natively. **No `extra-files` needed** — the Python strategy finds and updates `pyproject.toml` automatically.
- `package-name: "docvet"` — identifies the package for release notes
- `include-component-in-tag: false` — produces clean tags like `v1.1.0` instead of `docvet-v1.1.0` (monorepo tags are unnecessary for a single-package repo)
- `changelog-sections` — hides refactor, chore, test, ci from changelogs. Users see Features, Bug Fixes, Performance, Documentation only. Hidden types still contribute to version bumping (a `feat` always bumps minor).

**`.release-please-manifest.json`:**
```json
{ ".": "1.0.0" }
```

### Publish Workflow Design

**Trigger:** `release: types: [published]`

**Required workflow permissions:**
```yaml
permissions:
  id-token: write       # OIDC trusted publishing to PyPI
  contents: write       # Update floating v1 tag
  attestations: write   # Supply chain attestations
```

**Jobs:**
1. **build-and-publish:**
   - Checkout + `astral-sh/setup-uv@v7`
   - `uv build --no-sources` (produces wheel + sdist in `dist/`)
   - Smoke test: `unzip -l dist/*.whl` — verify <500KB, no `tests/`, `_bmad/`, `_bmad-output/`
   - Version assertion: extract version from tag, compare to `pyproject.toml`
   - `uv publish` with OIDC trusted publishing (no API tokens)
   - `astral-sh/attest-action` for supply chain attestations
2. **update-tags:**
   - `git tag -f v1 && git push origin v1 --force` — floating tag for GitHub Action consumers
   - This force push is **intentional** for floating major-version tags (standard GitHub Actions convention)

### TestPyPI Workflow Design

**Trigger:** `workflow_dispatch` (manual button in GitHub Actions UI)

**Purpose:** Validate the package builds and publishes correctly without touching production PyPI. Completely independent of release-please — no release PR needed.

**Required workflow permissions:**
```yaml
permissions:
  id-token: write   # OIDC trusted publishing to TestPyPI
```

**Steps:**
1. Checkout + setup-uv
2. `uv build --no-sources`
3. `uv publish --index-url https://test.pypi.org/simple/` with OIDC

### CHANGELOG.md Format

Hand-authored v1.0.0 entry using release-please's exact heading format (so future auto-generated entries are compatible):

```markdown
# Changelog

## [1.0.0](https://github.com/Alberto-Codes/docvet/releases/tag/v1.0.0) (2026-02-XX)

### Features

* **enrichment:** 10 rules detecting missing docstring sections — Raises, Yields, Receives, Warns, Other Parameters, Attributes, Typed Attributes, Examples, Cross-references, and fenced code blocks
* **freshness:** 5 rules detecting stale docstrings — signature changes (HIGH), body changes (MEDIUM), import changes (LOW), git-blame drift, and age-based staleness
* **coverage:** missing `__init__.py` detection for mkdocs discoverability
* **griffe:** 3 rules capturing griffe parser warnings for mkdocs rendering compatibility
* **reporting:** markdown and terminal output with configurable formats
* **cli:** 5 subcommands (check, enrichment, freshness, coverage, griffe) with `--staged`, `--all`, `--files`, `--format`, and `--output` options
* **integrations:** pre-commit hook and GitHub Action for CI/CD pipelines
* **config:** `[tool.docvet]` section in pyproject.toml with per-check configuration
```

**Date:** Set to the actual release date when the maintainer creates the GitHub Release.

### Launch Sequence (Maintainer Executes Post-Merge)

After this story's PR merges to `develop`, the maintainer executes these steps:

1. **Create `main` branch:** `git checkout develop && git pull && git checkout -b main && git push -u origin main`
2. **Configure repository settings** (see Pre-flight Checklist below)
3. **Test the pipeline:** Go to Actions tab > "Test Publish" workflow > "Run workflow" on `develop` — verify TestPyPI install: `pip install -i https://test.pypi.org/simple/ docvet && docvet --version`
4. **Update `bootstrap-sha`** in `release-please-config.json` to the actual merge commit SHA on `main` (if different from develop HEAD at PR time)
5. **Tag v1.0.0:** `git tag v1.0.0 && git push origin v1.0.0`
6. **Create GitHub Release** manually from the `v1.0.0` tag — paste curated release notes (can mirror the CHANGELOG entry)
7. **`publish.yml` triggers automatically** → builds → publishes to PyPI
8. **Verify:** `pip install docvet && docvet --version` shows `1.0.0`

### Pre-flight Infrastructure Checklist (Maintainer)

These are web UI configuration tasks — not code changes:

- [ ] **PyPI** (pypi.org): Create project `docvet` > Manage > Publishing > Add trusted publisher: owner=`Alberto-Codes`, repo=`docvet`, workflow=`publish.yml`, environment=`pypi`
- [ ] **TestPyPI** (test.pypi.org): Same as above but workflow=`test-publish.yml`, environment=`testpypi`
- [ ] **GitHub repo > Settings > Environments**: Create `pypi` environment (optional — adds deploy protection rules, approval gates)
- [ ] **GitHub repo > Settings > Environments**: Create `testpypi` environment (optional)
- [ ] **GitHub repo > Settings > Branches**: Add branch protection rule for `main` — require PR reviews, require CI to pass, no direct pushes
- [ ] **GitHub repo > Settings > Actions > General**: Ensure "Allow GitHub Actions to create and approve pull requests" is enabled (needed for release-please PRs)
- [ ] **GitHub repo > Settings > Pages**: Source = GitHub Actions (for future docs deployment in Epic 11)

### Previous Story Intelligence

**From 10.3 (Pre-commit Hook and GitHub Action):**
- Build backend is `uv_build` (migrated in Epic 9)
- `action.yml` exists at repo root — publish workflow updates floating `v1` tag for it
- `.pre-commit-hooks.yaml` exists — version pinning via `rev:` depends on release tags
- 729 tests as baseline

**From 10.1 (LICENSE and Package Metadata):**
- MIT license in place
- All PyPI classifiers configured
- `pyproject.toml` version is `1.0.0`

**From 10.2 (README):**
- Badge row references PyPI version — will resolve after first publish
- CI status badge references GitHub Actions — will work with new workflows

### Git Intelligence

Recent commits (all Epic 10):
- `0924228` feat(cli): add pre-commit hook and GitHub Action for CI integration (#65)
- `7bc1f24` docs(cli): add README with comparison table, quickstart, and badges (#64)
- `d2aa4d0` feat(cli): add LICENSE, package metadata, and PEP 561 typing marker (#62)

Existing CI at `.github/workflows/ci.yml` already references `main` branch. No CI changes needed.

Current wheel is ~132KB compressed — well under 500KB limit.

### NFR Compliance Notes

- **NFR55:** Pure Python wheel, no compilation step — already verified
- **NFR56:** Wheel <500KB — current wheel is ~132KB
- **NFR63:** Zero findings from `docvet check --all` as CI gate — achieved in Epic 9
- **NFR64-66:** API stability — `__all__` exports on all modules, `Finding` shape frozen

### Anti-Pattern Prevention

- **Do NOT hand-edit CHANGELOG.md after initial v1.0.0 entry** — release-please manages all future entries from conventional commits
- **Do NOT use API tokens for PyPI publishing** — use OIDC trusted publishing (more secure, no secret rotation)
- **Do NOT use `hatch-vcs` or dynamic versioning** — version is a static string in `pyproject.toml`, bumped by release-please's Python strategy
- **Do NOT trigger release-please on `develop`** — it watches `main` only. Develop is for integration, main is for releases.
- **Do NOT squash merge from develop to main** — release-please needs individual conventional commits to generate proper changelogs
- **Do NOT skip the smoke test step in publish.yml** — verify wheel contents before publishing to catch build config regressions
- **Do NOT add `extra-files` for `pyproject.toml` version** — `release-type: python` handles this natively
- **Do NOT modify any source code in `src/docvet/`** — this is an infrastructure-only story
- **Do NOT create the `main` branch in this story** — that's a maintainer launch task (see Launch Sequence)
- **Do NOT reuse stale `dist/` artifacts** — always `rm -rf dist/` before `uv build` for clean verification
- **Force push for floating `v1` tag is intentional** — this is the standard GitHub Actions convention for major-version tags, not a violation

### Project Structure Notes

- All new files are at repo root or under `.github/workflows/`
- No source tree changes
- No new test files (verification is structural and manual)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.4 — Acceptance criteria]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-G3 — CHANGELOG.md]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-G4 — TestPyPI validation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1 — Build System & Version Strategy]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5 — GitHub Action (floating v1 tag)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern 3 — GitHub Actions Workflow Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Boundary 3 — CI/CD Infrastructure]
- [Source: _bmad-output/implementation-artifacts/10-3-pre-commit-hook-and-github-action.md — previous story context]
- [Source: .github/workflows/ci.yml — existing CI referencing main branch]
- [Source: pyproject.toml — version 1.0.0, uv_build backend]
- [Source: release-please docs — manifest-releaser.md, customizing.md, config schema]
- [Source: gepa-adk releases — lessons learned on genesis commit flood and default formatting]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug issues encountered — infrastructure-only story with no source code changes.

### Completion Notes List

- Created `CHANGELOG.md` with hand-curated v1.0.0 entry using release-please heading format, summarizing all 4 check modules, 19 rules, reporting, 5 CLI subcommands, pre-commit hook, and GitHub Action
- Created `release-please-config.json` with `release-type: python`, `bootstrap-sha` (current HEAD), `include-component-in-tag: false`, and `changelog-sections` hiding chore/test/ci/refactor noise types
- Created `.release-please-manifest.json` with `{".": "1.0.0"}`
- Created `release-please.yml` workflow: triggers on push to `main`, uses `googleapis/release-please-action@v4`, outputs release metadata
- Created `publish.yml` workflow: triggers on `release: [published]`, builds with `uv build --no-sources`, smoke-tests wheel (size + contents), publishes via OIDC, attests provenance, updates floating `v1` tag
- Created `test-publish.yml` workflow: triggers on `workflow_dispatch`, builds and publishes to TestPyPI via OIDC
- Verified clean build: wheel (38KB) + sdist, installs in fresh venv, `docvet check --help` and `import docvet` both work
- All 729 tests pass, ruff lint clean, ruff format clean

### Change Log

- 2026-02-21: Created CHANGELOG.md and publication pipeline (6 new files)

### File List

- `CHANGELOG.md` (new)
- `release-please-config.json` (new)
- `.release-please-manifest.json` (new)
- `.github/workflows/release-please.yml` (new)
- `.github/workflows/publish.yml` (new)
- `.github/workflows/test-publish.yml` (new)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified)
- `_bmad-output/implementation-artifacts/10-4-changelog-and-publication-pipeline.md` (modified)
