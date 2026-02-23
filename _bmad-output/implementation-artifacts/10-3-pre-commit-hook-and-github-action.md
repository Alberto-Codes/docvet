# Story 10.3: Pre-commit Hook and GitHub Action

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer integrating docvet into CI,
I want a pre-commit hook and GitHub Action available with minimal configuration,
so that I can automate documentation quality gating in my workflow.

## Acceptance Criteria

1. **Given** no `.pre-commit-hooks.yaml` exists, **when** the hook definition is created, **then** `.pre-commit-hooks.yaml` exists at repo root with `id: docvet`, `language: python`, `types: [python]`, `entry: docvet check --staged`, `pass_filenames: false`, and `require_serial: true`.
2. **Given** `.pre-commit-hooks.yaml` is created, **when** the hook is tested, **then** `pre-commit try-repo . docvet --all-files` runs docvet successfully against the local repo (manual verification — not automatable in CI until published).
3. **Given** no `action.yml` exists, **when** the GitHub Action is created, **then** `action.yml` exists at repo root as a composite GitHub Action (`runs.using: composite`) with inputs: `version` (default: `latest`) and `args` (default: `check`).
4. **Given** `action.yml` is created, **when** a consumer uses the action, **then** it installs docvet via `pip install`, runs `docvet` with the provided args, and propagates the exit code (exit 0 on success, exit 1 on findings matching `fail-on`).
5. **Given** both integration files are created, **when** the README is checked, **then** the Pre-commit section no longer says "coming soon" and references the correct repo URL and hook id, and a new GitHub Action section is added with usage examples.
6. **Given** all changes applied, **when** `uv run pytest` is run, **then** all existing tests continue to pass.

## Tasks / Subtasks

- [x] Task 1: Create `.pre-commit-hooks.yaml` at repo root (AC: #1)
  - [x] 1.1 Create file with hook definition: `id: docvet`, `name: docvet`, `entry: docvet check --staged`, `language: python`, `types: [python]`, `pass_filenames: false`, `require_serial: true`
- [x] Task 2: Manual verification of pre-commit hook (AC: #2)
  - [x] 2.1 Run `pre-commit try-repo . docvet --all-files` and verify docvet executes
- [x] Task 3: Create `action.yml` at repo root (AC: #3)
  - [x] 3.1 Create composite action with `actions/setup-python@v5`, two inputs (`version`, `args`)
  - [x] 3.2 Add install step: `pip install docvet` (with version pinning when not `latest`)
  - [x] 3.3 Add run step: `docvet ${{ inputs.args }}` with `shell: bash`
- [x] Task 4: Update README.md pre-commit section (AC: #5)
  - [x] 4.1 Remove "coming in a future release" language from Pre-commit section
  - [x] 4.2 Add GitHub Action usage section with basic and advanced examples
  - [x] 4.3 Verify pre-commit section shows direct usage instructions without provisional language
- [x] Task 5: Run quality gates (AC: #6)
  - [x] 5.1 `uv run pytest` — all existing tests pass
  - [x] 5.2 `uv run ruff check .` — no lint errors
  - [x] 5.3 `uv run ruff format --check .` — no formatting issues
  - [x] 5.4 `uv run python -m readme_renderer README.md -o /tmp/readme.html` — PyPI rendering clean (exit 0, no warnings)

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | YAML validation: `python -c "import yaml; yaml.safe_load(open('.pre-commit-hooks.yaml'))"` — all 7 fields present | Pass |
| AC2 | `pre-commit try-repo . docvet --all-files` — hook executes and passes | Pass |
| AC3 | YAML validation: `action.yml` has `runs.using: composite`, inputs `version` and `args` | Pass |
| AC4 | `action.yml` install step uses `pip install docvet`, run step uses `docvet ${{ inputs.args }}`, `shell: bash` | Pass |
| AC5 | README Pre-commit section has no "coming soon" language; GitHub Action section added with usage examples | Pass |
| AC6 | `uv run pytest` (729 passed), `ruff check` (passed), `ruff format --check` (passed), `readme_renderer` (exit 0) | Pass |

## Dev Notes

### Implementation Strategy

This is an integration/content story. Three files created, one file updated. No source code changes. No new tests needed — verification is manual (pre-commit try-repo) and structural (file existence, YAML validity).

**Files:**

1. **`.pre-commit-hooks.yaml`** (new) — Consumer-facing hook definition. ~10 lines YAML. This is different from `.pre-commit-config.yaml` (docvet's own pre-commit config for internal development).
2. **`action.yml`** (new) — Composite GitHub Action. ~25 lines YAML.
3. **`README.md`** (modify) — Update Pre-commit section, add GitHub Action section.

### Pre-commit Hook Design (Architecture Decision 4)

The architecture specifies a single hook with `pass_filenames: false`, delegating file discovery to docvet's `--staged` mode:

```yaml
- id: docvet
  name: docvet
  entry: docvet check --staged
  language: python
  types: [python]
  require_serial: true
  pass_filenames: false
```

**Key design points:**

- **`pass_filenames: false`** — docvet's `--staged` mode uses `git diff --cached` internally for file discovery. Accepting filenames from pre-commit would bypass this and break the git-aware discovery pipeline.
- **`require_serial: true`** — prevents parallel invocations that would race on `git diff --cached` state.
- **`types: [python]`** — ensures pre-commit only triggers on Python file changes (skip early if only markdown/config changed).
- **Single hook** — one `id: docvet` covers all checks. Users customize via `args:` in their `.pre-commit-config.yaml` (e.g., `args: [enrichment]` to run only enrichment).
- **Griffe opt-in** — users who want griffe checking add `additional_dependencies: [griffe]` in their `.pre-commit-config.yaml`. The hook itself does not declare griffe as a dependency.

**Consumer usage example (in their `.pre-commit-config.yaml`):**

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v1.0.0
    hooks:
      - id: docvet
```

**With griffe:**

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v1.0.0
    hooks:
      - id: docvet
        additional_dependencies: [griffe]
```

### GitHub Action Design (Architecture Decision 5)

The architecture specifies a composite action with `actions/setup-python@v5`, `shell: bash` on all steps, and two inputs:

```yaml
name: 'docvet'
description: 'Run docvet docstring quality checks'
inputs:
  version:
    description: 'docvet version to install (use "latest" for newest)'
    required: false
    default: 'latest'
  args:
    description: 'Arguments to pass to docvet (e.g., "check --all")'
    required: false
    default: 'check'
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: |
        if [ "${{ inputs.version }}" = "latest" ]; then
          pip install docvet
        else
          pip install docvet==${{ inputs.version }}
        fi
      shell: bash
    - run: docvet ${{ inputs.args }}
      shell: bash
```

**Key design points:**

- **Composite action** — no Node.js runtime needed, simpler maintenance than JavaScript actions.
- **`actions/setup-python@v5`** — ensures Python 3.12+ is available regardless of runner image.
- **`shell: bash`** on every step — required for composite actions (no default shell inheritance).
- **Two inputs only** — `args` (what to run) and `version` (which version). Minimal surface area. The `src` input from FR116 was intentionally collapsed into `args` by the architecture for simplicity — users pass `args: "check --all"` instead.
- **`pip install`** — standard Python package install. No uv dependency in the action itself (runners may not have uv).
- **Version handling** — `latest` installs without pinning; specific versions use `==X.Y.Z`.

**Consumer usage examples:**

Basic:
```yaml
- uses: Alberto-Codes/docvet@v1
```

With version pinning:
```yaml
- uses: Alberto-Codes/docvet@v1
  with:
    version: '1.0.0'
    args: 'check --all'
```

### README Updates

**Pre-commit section:** Remove "Pre-commit hook support is coming in a future release." Replace with direct instructions (no "coming soon" language).

**GitHub Action section:** Add a new `## GitHub Action` section after Pre-commit with basic and advanced usage examples. Place before "Better Docstrings, Better AI" section.

**Verification:** Run `uv run python -m readme_renderer README.md -o /tmp/readme.html` to confirm PyPI rendering is clean after changes.

### Disambiguation: `.pre-commit-hooks.yaml` vs `.pre-commit-config.yaml`

These are **two different files** with different purposes:

| File | Purpose | Audience |
|------|---------|----------|
| `.pre-commit-hooks.yaml` | **Hook definition** — tells the pre-commit framework what hooks this repo provides | **Consumers** of docvet |
| `.pre-commit-config.yaml` | **Hook configuration** — tells pre-commit what hooks to run on this repo | **Developers** of docvet |

The `.pre-commit-config.yaml` already exists (added in commit `c4be928`) with ruff, ty, pytest, and a local docvet hook. Story 10.3 creates the **hook definition** file (`.pre-commit-hooks.yaml`) that lets external projects use docvet as a pre-commit hook.

### Previous Story Intelligence (10.1 and 10.2)

**From 10.1 (LICENSE and Package Metadata):**
- Build backend is `uv_build` (not hatchling) — no special build config needed for new root files
- MIT license in place
- `pyproject.toml` has `[project.urls]` with Homepage, Source, Issues
- 729 tests as baseline

**From 10.2 (README):**
- README has a Pre-commit section (line 72-82) with "coming in a future release" placeholder — must be updated
- README currently references `https://github.com/Alberto-Codes/docvet` as repo URL and `v1.0.0` as rev
- `readme-renderer[md]` is a dev dependency for rendering verification
- No GitHub Action section exists yet — must be added

### Git Intelligence

Last 5 commits (all on `develop`):
- `7bc1f24` docs(cli): add README with comparison table, quickstart, and badges (#64)
- `d2aa4d0` feat(cli): add LICENSE, package metadata, and PEP 561 typing marker (#62)
- `c4be928` chore: extract Finding, add Examples docstrings, and pre-commit hooks (#61)
- `b1c53bb` feat(cli): version bump to 1.0.0, --version flag, and uv_build backend (#60)
- `6b90eb4` feat(cli): add __all__ exports to all public modules (#59)

Epic 9 fully done, Stories 10.1 done, 10.2 in review. Clean `develop` branch.

**Suggested branch:** `feat/cli-10-3-pre-commit-hook-and-github-action`

### NFR Compliance Notes

- **NFR59:** Pre-commit hook executes in under 10 seconds for 50 staged Python files — aspirational benchmark. docvet's current performance is sub-50ms per file (NFR1-4), so 50 files = ~2.5s max.
- **NFR61:** Pre-commit hook works with pre-commit framework v3.x and v4.x — `language: python` is stable across both versions. No version-specific workarounds needed.
- **NFR62:** GitHub Action works with `ubuntu-latest`, `macos-latest`, and `windows-latest` — composite action with `shell: bash` works on all three. `pip install` is universal.

### Anti-Pattern Prevention

- **Do NOT add `pass_filenames: true`** — docvet uses `git diff --cached` internally. Passing filenames would bypass the git-aware discovery pipeline.
- **Do NOT add multiple hooks** — one `id: docvet` with `args:` customization is simpler and matches how ruff's pre-commit works.
- **Do NOT declare griffe in the hook's dependencies** — griffe is optional. Users opt in via `additional_dependencies: [griffe]` in their own config.
- **Do NOT use `uv` or `uvx` in the GitHub Action** — runners may not have uv. Use `pip install` for universal compatibility.
- **Do NOT add a `src` input to the action** — architecture Decision 5 intentionally collapsed this into `args` for simplicity.
- **Do NOT use Node.js action** — composite is the standard for Python tool actions (ruff, mypy follow the same pattern).
- **Do NOT modify any source code** — this is an integration/content-only story.
- **Do NOT confuse `.pre-commit-hooks.yaml` (hook definition for consumers) with `.pre-commit-config.yaml` (hook config for docvet development)**.
- **Do NOT remove the existing `.pre-commit-config.yaml`** — it's docvet's own pre-commit config and is unrelated to this story.

### Project Structure Notes

- `.pre-commit-hooks.yaml` goes at repository root (same level as `pyproject.toml`)
- `action.yml` goes at repository root (same level as `pyproject.toml`)
- No source tree changes
- No new test files

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.3 — Acceptance criteria]
- [Source: _bmad-output/planning-artifacts/epics.md#FR114 — .pre-commit-hooks.yaml]
- [Source: _bmad-output/planning-artifacts/epics.md#FR116 — GitHub Action composite]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 4 — Pre-commit Hook Design]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5 — GitHub Action Design]
- [Source: _bmad-output/planning-artifacts/architecture.md#NFR59-NFR62 — CI integration quality]
- [Source: _bmad-output/project-context.md — technology stack and testing rules]
- [Source: _bmad-output/implementation-artifacts/10-1-license-and-package-metadata.md — previous story context]
- [Source: _bmad-output/implementation-artifacts/10-2-readme-with-comparison-table-quickstart-and-badges.md — README current state]
- [Source: README.md — current pre-commit section (lines 72-82)]
- [Source: .pre-commit-config.yaml — docvet's own pre-commit config (not to be confused with hooks file)]
- [Source: pyproject.toml — entry point: docvet.cli:app, build system: uv_build]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- `pre-commit try-repo` required staging `.pre-commit-hooks.yaml` first — untracked files aren't included in shadow repo

### Completion Notes List

- Created `.pre-commit-hooks.yaml` with all 7 required fields matching architecture Decision 4
- Verified hook via `pre-commit try-repo . docvet --all-files` — passed on all files
- Created `action.yml` as composite GitHub Action with `actions/setup-python@v5`, version-aware `pip install`, and `shell: bash` on all steps
- Updated README: removed "coming in a future release" from Pre-commit section, added griffe opt-in example, added GitHub Action section with basic and pinned-version examples
- All quality gates pass: 729 tests, ruff clean, PyPI rendering clean

### Change Log

- 2026-02-21: Story implemented — `.pre-commit-hooks.yaml`, `action.yml` created; README updated with CI integration docs

### File List

- `.pre-commit-hooks.yaml` (new)
- `action.yml` (new)
- `README.md` (modified)
- `_bmad-output/implementation-artifacts/10-3-pre-commit-hook-and-github-action.md` (modified)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified)
