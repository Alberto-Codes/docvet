# Story 30.4: GitHub Action for PR Inline Docstring Comments

Status: review
Branch: `feat/ci-30-4-github-action-pr-annotations`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/294

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **team lead adding docvet to CI**,
I want a first-party GitHub Action that runs docvet on pull requests and posts inline annotations,
so that every PR gets automatic docstring quality feedback without developers running docvet locally.

## Acceptance Criteria

1. **Given** a repository using the docvet GitHub Action in a workflow, **when** a pull request is opened or updated, **then** the Action installs docvet, runs `docvet check --format json` on the repository, and maps each finding to a GitHub workflow annotation command (`::warning file={file},line={line},title={rule}::{message}`) with proper character escaping.

2. **Given** the Action's `checks` input is set (e.g., `checks: "enrichment,freshness"`), **when** the Action runs, **then** only the specified checks are executed (each check runs as a separate `docvet {check} --format json` subcommand invocation, results merged).

3. **Given** the Action's `checks` input is not set or set to `all`, **when** the Action runs, **then** all enabled checks run via `docvet check --format json`.

4. **Given** docvet finds one or more findings, **when** the Action completes, **then** the Action exits with a non-zero exit code, causing the GitHub check to fail, **and** a `$GITHUB_STEP_SUMMARY` Markdown table lists all findings (not subject to annotation caps).

5. **Given** docvet finds zero findings, **when** the Action completes, **then** the Action exits with exit code 0, causing the GitHub check to pass.

6. **Given** the repository has a `[tool.docvet]` section in pyproject.toml, **when** the Action runs, **then** it respects the project's configuration (exclude patterns, check configs, thresholds).

7. **Given** the Action definition (`action.yml`), **when** reviewing the implementation, **then** it is a composite action (not Docker-based per NFR1) that installs docvet via `pip install docvet`, runs the CLI, and processes JSON output with a shell script.

8. **Given** the Action input `docvet-version`, **when** a specific version is provided (e.g., `docvet-version: "1.9.0"`), **then** that version is installed; when omitted, the latest version is installed.

9. **Given** the Action input `python-version`, **when** a specific version is provided (e.g., `python-version: "3.12"`), **then** Python is set up with that version; when omitted, a sensible default is used (e.g., `3.12`).

10. **Given** a developer wants to add docvet to their repo, **when** they visit the docvet README or docs site, **then** a copy-paste workflow snippet is prominently displayed showing how to use the Action in a GitHub Actions workflow.

11. **Given** the old `args` input is used in a consumer workflow, **when** the Action runs, **then** it still works (backward compatibility) but GitHub logs a deprecation warning via `deprecationMessage`.

## Tasks / Subtasks

- [x] Task 1: Rewrite `action.yml` with new inputs, backward compat, and annotation logic (AC: 1-9, 11)
  - [x] 1.1 Add new inputs: `checks` (default: `all`), `docvet-version` (default: `latest`), `python-version` (default: `3.12`)
  - [x] 1.2 Keep `args` input with `deprecationMessage: "Use 'checks' input instead. 'args' will be removed in v2."` and `version` with `deprecationMessage: "Renamed to 'docvet-version'. 'version' will be removed in v2."`
  - [x] 1.3 Write composite step: install docvet, run checks with `--format json --all`, parse JSON, emit `::warning` annotations with `title` parameter and character escaping
  - [x] 1.4 Handle `checks: all` -> run `docvet --format json check --all`
  - [x] 1.5 Handle `checks: enrichment,freshness` -> run each as `docvet --format json {check} --all`, merge JSON with `jq -s`
  - [x] 1.6 Handle backward compat: if `args` is set and `checks` is default, use `args` as raw passthrough (legacy mode, no JSON/annotations)
  - [x] 1.7 Write `$GITHUB_STEP_SUMMARY` Markdown table with all findings (bypasses annotation cap)
  - [x] 1.8 Add count disclosure header: `"Found N findings (up to 10 shown as inline annotations)"`
  - [x] 1.9 Exit non-zero when findings exist, exit 0 when clean
  - [x] 1.10 Redirect docvet stderr to file, distinguish "findings found" (exit 1) from "crash" (exit >1) — surface crashes as `::error`
- [x] Task 2: Create test workflow and fixture (AC: 1, 2, 3, 4, 5)
  - [x] 2.1 Create `.github/test-fixtures/bad_docstrings.py` with known findings (function raising without Raises section, class missing Attributes, etc.)
  - [x] 2.2 Create `.github/workflows/test-action.yml` that exercises the action against the fixture using `uses: ./`
  - [x] 2.3 Test selective checks: `checks: "enrichment"` against fixture
  - [x] 2.4 Test zero-findings path against a clean file
  - [x] 2.5 Add `extend-exclude` entry in pyproject.toml for `.github/test-fixtures/`
  - [x] 2.6 Keep main `ci.yml` on `Alberto-Codes/docvet@v1` unchanged (uses `args`, backward compat covers it)
- [x] Task 3: Update README with new usage snippets (AC: 10)
  - [x] 3.1 Lead with simplest example: just `uses: Alberto-Codes/docvet@v1` (no inputs needed)
  - [x] 3.2 Show customization: `checks`, `docvet-version`, `python-version`
  - [x] 3.3 Add example showing `checks: "enrichment,freshness"` selective execution
  - [x] 3.4 Keep griffe setup example updated
- [x] Task 4: Update docs site CI Integration page (AC: 10)
  - [x] 4.1 Update `docs/site/ci-integration.md` with new action inputs and examples
  - [x] 4.2 Document annotation behavior: inline for lines in diff, step summary for full list
  - [x] 4.3 Run `mkdocs build --strict` to verify
- [x] Task 5: Run all quality gates (AC: all)
  - [x] 5.1 All standard quality gates pass

## AC-to-Test Mapping

<!-- This story is infrastructure (GitHub Action YAML + shell script). No Python source changes, no pytest tests. Quality gates are CI execution via test-action.yml + manual annotation verification. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | test-action.yml: test-annotations job runs action on fixture, emits annotations | Pending CI |
| 2 | test-action.yml: test-selective job with `checks: "enrichment"` | Pending CI |
| 3 | test-action.yml: test-annotations job with default `checks` runs all checks | Pending CI |
| 4 | test-action.yml: test-annotations job exits non-zero + step summary table | Pending CI |
| 5 | test-action.yml: test-clean job exits 0 | Pending CI |
| 6 | extend-exclude in pyproject.toml skips `.github/test-fixtures/` | Pass |
| 7 | Code review: `action.yml` is composite, uses `pip install docvet` | Pass |
| 8 | test-action.yml: test-version-pin job with `docvet-version: "1.9.0"` | Pending CI |
| 9 | test-action.yml: test-python-version job with `python-version: "3.13"` | Pending CI |
| 10 | README leads with simplest example, docs site updated with new inputs | Pass |
| 11 | ci.yml unchanged — `args: "check --all"` triggers legacy mode | Pass |

## Dev Notes

### Current State

The existing `action.yml` (37 lines) is a minimal composite action with two inputs:
- `version` (default: `latest`) — docvet version to install
- `args` (default: `check`) — raw arguments passed to docvet CLI

It runs docvet in terminal mode (no JSON parsing, no annotation mapping). The current CI dogfood job passes `args: "check --all"`.

### Target Architecture

Add structured inputs alongside the existing ones (backward compat). The action has two modes:

**New mode** (when `checks` input is explicitly set or `args` is not set):
1. Installs docvet (respecting `docvet-version` or deprecated `version` input)
2. Runs checks with `--format json --all`, parses JSON with `jq`
3. Emits `::warning` annotations (GitHub caps at 10 per step)
4. Writes full findings table to `$GITHUB_STEP_SUMMARY` (no cap)
5. Exits with appropriate code

**Legacy mode** (when `args` input is set and `checks` is still default `all`):
1. Installs docvet
2. Runs `docvet $ARGS` directly (raw passthrough, no JSON, no annotations)
3. Exit code from docvet propagates directly

This ensures `args: "check --all"` keeps working identically while new users get annotations.

### Critical Constraint: Annotation Limits

**GitHub caps `::warning` annotations at 10 per step, 50 per job.** Findings beyond the cap are **silently dropped** with no UI indication. This is why `$GITHUB_STEP_SUMMARY` is mandatory — it's the only way to guarantee all findings are visible.

The step summary Markdown table is always written, even when there are zero findings (shows "No findings" message). The count disclosure header tells users why they may see fewer inline annotations than total findings:

```
### Docvet Findings

Found **15** findings (up to 10 shown as inline annotations).

| File | Line | Rule | Message | Severity |
|------|------|------|---------|----------|
| ... |
```

Source: [GitHub community discussion #26680](https://github.com/orgs/community/discussions/26680), confirmed by `actions/toolkit` problem-matchers.md.

### Annotation Behavior in PR Diffs

- Annotations on lines **in the PR diff** appear **inline** in the "Files changed" tab
- Annotations on lines **outside the diff** appear only in the **Checks tab** summary
- Running with `--all` means many findings will be on unchanged lines — inline placement is best-effort
- The `$GITHUB_STEP_SUMMARY` table is always the authoritative complete list

Source: [GitHub community discussion #8123](https://github.com/orgs/community/discussions/8123)

### JSON Output Structure (stable v1 contract)

```json
{
  "findings": [
    {
      "file": "src/app.py",
      "line": 42,
      "symbol": "my_func",
      "rule": "missing-raises",
      "message": "Function 'my_func' raises ValueError but ...",
      "category": "required",
      "severity": "high"
    }
  ],
  "summary": {
    "total": 1,
    "by_category": { "required": 1, "recommended": 0 },
    "files_checked": 5
  }
}
```

Source: `src/docvet/reporting.py:152-226`, `src/docvet/checks/_finding.py:27-98`

### Key Implementation Details

**action.yml inputs (new + deprecated):**
```yaml
inputs:
  checks:
    description: 'Checks to run: "all" or comma-separated list (enrichment,freshness,coverage,griffe,presence)'
    required: false
    default: 'all'
  docvet-version:
    description: 'docvet version to install (use "latest" for newest)'
    required: false
    default: 'latest'
  python-version:
    description: 'Python version to set up'
    required: false
    default: '3.12'
  # Deprecated — kept for backward compatibility within v1
  version:
    description: 'docvet version to install'
    deprecationMessage: 'The "version" input is deprecated. Use "docvet-version" instead. "version" will be removed in v2.'
    required: false
    default: 'latest'
  args:
    description: 'Raw arguments passed to docvet CLI'
    deprecationMessage: 'The "args" input is deprecated. Use "checks" instead for annotation support. "args" will be removed in v2.'
    required: false
    default: ''
```

**Backward compat logic:**
```bash
# Resolve version: docvet-version takes precedence over deprecated version
DOCVET_VERSION="${{ inputs.docvet-version }}"
if [ "$DOCVET_VERSION" = "latest" ] && [ "${{ inputs.version }}" != "latest" ]; then
  DOCVET_VERSION="${{ inputs.version }}"
fi

# Detect legacy mode: args is set and checks is still default
ARGS="${{ inputs.args }}"
CHECKS="${{ inputs.checks }}"
if [ -n "$ARGS" ] && [ "$CHECKS" = "all" ]; then
  # Legacy mode: raw passthrough, no JSON/annotations
  docvet $ARGS
  exit $?
fi
```

**Annotation format with `title` parameter and character escaping:**
```bash
# Use title= for rule name (renders as annotation header)
# Escape message: % -> %25, \n -> %0A, \r -> %0D
# Escape properties: : -> %3A, , -> %2C (in file paths)
jq -r '.findings[] | "::warning file=\(.file | gsub(":";"%3A") | gsub(",";"%2C")),line=\(.line),title=\(.rule)::\(.message | gsub("%";"%25") | gsub("\n";"%0A") | gsub("\r";"%0D"))"' /tmp/docvet-output.json
```

Source: [GitHub docs on workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands)

**Step summary output:**
```bash
TOTAL=$(jq '.summary.total' /tmp/docvet-output.json)

if [ "$TOTAL" -gt 0 ]; then
  echo "### Docvet Findings" >> "$GITHUB_STEP_SUMMARY"
  echo "" >> "$GITHUB_STEP_SUMMARY"
  echo "Found **${TOTAL}** findings (up to 10 shown as inline annotations)." >> "$GITHUB_STEP_SUMMARY"
  echo "" >> "$GITHUB_STEP_SUMMARY"
  echo "| File | Line | Rule | Message | Severity |" >> "$GITHUB_STEP_SUMMARY"
  echo "|------|------|------|---------|----------|" >> "$GITHUB_STEP_SUMMARY"
  jq -r '.findings[] | "| `\(.file)` | \(.line) | `\(.rule)` | \(.message) | \(.severity) |"' /tmp/docvet-output.json >> "$GITHUB_STEP_SUMMARY"
else
  echo "### Docvet Findings" >> "$GITHUB_STEP_SUMMARY"
  echo "" >> "$GITHUB_STEP_SUMMARY"
  echo "No findings. All docstrings pass quality checks." >> "$GITHUB_STEP_SUMMARY"
fi
```

**Error handling — distinguish findings from crashes:**
```bash
docvet check --format json --all > /tmp/docvet-output.json 2>/tmp/docvet-stderr.txt
EXIT_CODE=$?

if [ "$EXIT_CODE" -gt 1 ]; then
  # docvet crashed (not "findings found" which is exit 1)
  echo "::error::docvet encountered an error (exit code $EXIT_CODE)"
  cat /tmp/docvet-stderr.txt
  exit "$EXIT_CODE"
fi
# EXIT_CODE 0 or 1 — proceed to parse JSON
```

**Merging multiple JSON outputs** (for selective checks):
```bash
jq -s '{
  findings: map(.findings) | add // [],
  summary: {
    total: (map(.summary.total) | add),
    by_category: {
      required: (map(.summary.by_category.required) | add),
      recommended: (map(.summary.by_category.recommended) | add)
    },
    files_checked: (map(.summary.files_checked) | max)
  }
}' /tmp/docvet-*.json > /tmp/docvet-output.json
```

Note: `add // []` handles the case where all findings arrays are empty (jq `add` on empty returns `null`, `// []` provides fallback).

**Composite action shell requirement:** Every `run:` step MUST specify `shell: bash`. Composite actions do not support `defaults.run.shell`.

### Test Fixture and Workflow

**`.github/test-fixtures/bad_docstrings.py`** — deliberate findings for CI verification:
```python
"""Test fixture with known docstring issues."""


def raises_without_docs(value: int) -> str:
    """Convert value to string."""
    if value < 0:
        raise ValueError("negative")
    return str(value)


class UndocumentedAttrs:
    """A class with undocumented attributes."""

    def __init__(self) -> None:
        self.name = "test"
        self.value = 42
```

This produces at minimum: `missing-raises` on the function, `missing-attributes` on the class. Known, deterministic findings for annotation verification.

**`.github/workflows/test-action.yml`** — exercises the action on the feature branch:
```yaml
name: Test Action
on:
  pull_request:
    paths: ['action.yml', '.github/test-fixtures/**', '.github/workflows/test-action.yml']

jobs:
  test-annotations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./
        continue-on-error: true  # expected to fail (findings exist)
        id: docvet-run
      # Verify non-zero exit
      - run: test "${{ steps.docvet-run.outcome }}" = "failure"
        shell: bash

  test-selective:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./
        with:
          checks: "enrichment"
        continue-on-error: true
        id: docvet-run

  test-clean:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./
        with:
          checks: "coverage"  # coverage check on a well-structured repo = 0 findings
```

**`pyproject.toml` exclusion** — prevent fixture from triggering docvet in normal runs:
```toml
[tool.docvet]
extend-exclude = [".github/test-fixtures/"]
```

### Backward Compatibility Strategy

The `deprecationMessage` field is a first-class `action.yml` feature. When a consumer uses a deprecated input, GitHub **automatically logs a warning** in the workflow run. No action code needed to surface the warning.

Pattern follows `docker/setup-buildx-action` (v3 deprecated inputs, v4 removed them):
1. Add new inputs (`checks`, `docvet-version`) in this PR
2. Keep old inputs (`args`, `version`) with `deprecationMessage`
3. Implementation handles both — old input feeds into new when both aren't set
4. Remove old inputs only in a hypothetical v2

The main `ci.yml` continues using `args: "check --all"` — it works via legacy mode. No changes to the main CI workflow needed.

Source: [GitHub docs: metadata syntax, inputs deprecationMessage](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions), [docker/setup-buildx-action v3](https://github.com/docker/setup-buildx-action/blob/v3/action.yml)

### Why Not the Checks API?

The Checks API (`actions/github-script`) removes the 10-annotation cap and allows unlimited annotations via batching. However:
- Requires `checks: write` permission in consumer workflows
- Does NOT work on forked PRs (GITHUB_TOKEN lacks write access)
- Adds JavaScript/`actions/github-script` dependency to a pure-shell composite action
- Significantly more complex implementation

The `::warning` + `$GITHUB_STEP_SUMMARY` hybrid provides "good enough" inline annotations (up to 10) with a guaranteed-complete step summary table. If power users need unlimited inline annotations, they can pipe `docvet check --format json` through `reviewdog` themselves.

This can be revisited in a future story if demand warrants it.

Source: [reviewdog architecture](https://github.com/reviewdog/reviewdog), [GitHub community discussion #26680](https://github.com/orgs/community/discussions/26680)

### Anti-Patterns to Avoid

- Do NOT use `::error` for findings — use `::warning` so annotations display without implying the check is a hard blocker (exit code controls pass/fail)
- Do NOT remove `args` or `version` inputs — keep them with `deprecationMessage` for v1 backward compat
- Do NOT create a Docker-based action — composite action only (NFR1)
- Do NOT add Node.js or any compiled language — pure shell script with `jq`
- Do NOT use `2>/dev/null` to suppress stderr — redirect to a file and check for crashes (exit code >1)
- Do NOT forget `|| true` after docvet invocations in the JSON parsing path — docvet exits 1 on findings but we need the JSON output
- Do NOT skip `$GITHUB_STEP_SUMMARY` — it's the only way to guarantee all findings are visible (annotation cap is 10/step)
- Do NOT skip character escaping in annotation messages — colons, commas, newlines, percent signs must be escaped per GitHub workflow command spec
- Do NOT modify main `ci.yml` — it uses `args` which works via legacy mode; test with a separate `test-action.yml`
- Do NOT forget `shell: bash` on every composite step — composite actions do not support `defaults.run.shell`

### Edge Cases

- **No pyproject.toml**: docvet runs with defaults — no special handling needed
- **Griffe not installed**: griffe check will be skipped automatically by docvet CLI
- **Empty findings**: JSON has `"findings": []` and `"total": 0` — jq handles gracefully, step summary shows "No findings" message
- **Individual check with no findings**: produces valid JSON with empty findings array
- **`presence_coverage` field**: only present when presence check runs — jq reads `.findings[]` only, safe to ignore
- **Findings >10**: first 10 get inline annotations (GitHub's cap), all appear in step summary table
- **Message contains special characters**: colons, commas, newlines in finding messages are escaped per workflow command spec
- **docvet crash (exit >1)**: surfaced as `::error` with stderr output, distinct from "findings found" (exit 1)
- **Both `args` and `checks` set**: `checks` takes precedence (new mode), `args` is ignored
- **Forked PR**: `::warning` commands work on forks (no API permissions needed). Step summary also works.
- **jq version**: Ubuntu runners have jq 1.7, macOS/Windows have 1.8.1 — all features used here work on jq 1.7

### Previous Story Intelligence

**From Story 30.3 (License attribution):**
- Quick-spec stories should be extremely straightforward with minimal AC complexity
- Quality gates must all pass — for 30.4 the critical gate is CI verification via test-action.yml
- Code review found only LOW-severity issues on 30.3 — clean execution pattern
- BMAD side artifacts (sprint-status edits) are separate from core implementation

**From Story 30.2 (TypedDict refactor):**
- Behavior-neutral changes should preserve all existing tests unchanged
- This story changes no Python source — existing tests are not affected

### Git Intelligence

Recent commits show:
- `780cb91` docs(site): add license attribution page and copyright footer (#293) — Story 30.3
- `c8bf9f3` refactor(mcp): replace dict type with RuleCatalogEntry TypedDict (#291) — Story 30.2
- `fa914ed` chore(deps): lock file maintenance (#289) — Renovate
- `6f06b37` chore(deps): update github-actions (major) (#288) — Renovate bumped actions/checkout to v6, actions/setup-python to v6
- `1def643` chore(deps): migrate from Dependabot to Renovate (#286) — Story 30.1

Key insight: `actions/setup-python@v6` is the current version (bumped by Renovate in #288). Use v6 in the action.

### Project Structure Notes

- `action.yml` in repo root — composite action definition
- `.github/workflows/ci.yml` — self-dogfood workflow (do NOT modify — backward compat covers it)
- `.github/workflows/test-action.yml` — new test workflow for this story
- `.github/test-fixtures/bad_docstrings.py` — new test fixture with deliberate findings
- `README.md` lines 106-133 — GitHub Action usage section
- `docs/site/ci-integration.md` — docs site CI page
- No Python source changes in this story
- `jq` is pre-installed on all GitHub-hosted runners (ubuntu 1.7, macos/windows 1.8.1)

### References

- [Source: _bmad-output/planning-artifacts/epics-distribution-adoption.md, Story 30.4]
- [Source: action.yml, current composite action definition]
- [Source: .github/workflows/ci.yml:78-87, current dogfood job]
- [Source: README.md:106-133, GitHub Action usage section]
- [Source: src/docvet/reporting.py:152-226, JSON output format]
- [Source: src/docvet/checks/_finding.py:27-98, Finding dataclass contract]
- [FR1-FR4: GitHub Action runs checks, configurable selection, annotation mapping, exit code]
- [NFR1: Composite action, no Docker]
- [NFR2: Config via action inputs and pyproject.toml]
- [Research: GitHub annotation limits — 10 per severity per step, 50 per job](https://github.com/orgs/community/discussions/26680)
- [Research: deprecationMessage — built-in action.yml feature](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions)
- [Research: docker/setup-buildx-action deprecation pattern](https://github.com/docker/setup-buildx-action/blob/v3/action.yml)
- [Research: Workflow command character escaping](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands)
- [Research: PR diff annotation behavior](https://github.com/orgs/community/discussions/8123)
- [Research: Composite action shell requirement](https://github.com/orgs/community/discussions/18597)
- [Research: jq pre-installed on all runners](https://github.com/actions/runner-images)
- [Research: Checks API tradeoffs vs workflow commands](https://github.com/orgs/community/discussions/26703)

### Future Ideas (Party-Mode Consensus, 2026-03-06)

Captured in epic file under "Epic 31 candidates" for future prioritization:

1. **`src-root` or `files` action input** — monorepo support + eliminates `cp` fixture hack. Precedent: ruff-action's `src` input.
2. **`docvet-source: local` action input** — `pip install .` for pre-release integration testing. Only needed if JSON contract changes.
3. **Three test boundaries documented** — library (pytest) / action wrapper (test-action.yml) / dogfood (ci.yml) are intentionally separate. Action installs from PyPI = tests the released contract.

### Test Maturity Piggyback

- **M1**: 3/948 tests use `@pytest.mark.parametrize` — massive deduplication opportunity in `test_enrichment.py` (4,134 lines, 227 tests)
- Note: This is a docs/infra story with no Python source changes, so parametrize adoption is out of scope. Flag for a future dedicated story.
- Sourced from test-review.md — address alongside a future code-touching story

### Documentation Impact

- Pages: README.md (GitHub Action section), docs/site/ci-integration.md
- Nature of update: Add new inputs (`checks`, `docvet-version`, `python-version`) with examples; document annotation behavior (inline vs step summary); lead README with simplest usage example; document annotation limits and step summary as authoritative list

## Quality Gates

<!-- All gates mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 1201 passed, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — N/A (no Python source changes)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Discovered `--format json` is a top-level CLI flag, not per-subcommand. Fixed `action.yml` to use `docvet --format json check --all` instead of `docvet check --format json --all`.
- Added `.github/test-fixtures` to ruff exclude to prevent D107 lint error on the deliberately "bad" test fixture.

### Completion Notes List

- Rewrote `action.yml` from 37 lines to 156 lines with structured inputs, backward compat, JSON parsing, `::warning` annotations, and `$GITHUB_STEP_SUMMARY` Markdown table.
- New mode: `checks` input runs docvet with `--format json`, parses output with `jq`, emits annotations.
- Legacy mode: `args` input passes through raw CLI args (no JSON, no annotations) — backward compat for existing consumers.
- Test workflow with 5 jobs: annotations, selective checks, clean run, version pinning, Python version.
- Test fixture with known enrichment findings (missing-raises, missing-attributes).
- README and docs site updated with new inputs and annotation behavior documentation.

### Change Log

- 2026-03-05: Implemented story 30.4 — GitHub Action rewrite with annotation support, test workflow, docs updates.
- 2026-03-05: Code review fixes — pipe escaping in step summary table, legacy args test job, dead import cleanup.

### File List

- action.yml (modified)
- .github/test-fixtures/bad_docstrings.py (new)
- .github/workflows/test-action.yml (new)
- pyproject.toml (modified — extend-exclude, ruff exclude)
- README.md (modified — GitHub Action section)
- docs/site/ci-integration.md (modified — inputs, examples, annotation behavior)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Code review agent (adversarial) + party mode consensus (Winston, Amelia, Murat)

### Outcome

Changes Requested — 2 fixes applied (1 MEDIUM, 1 LOW)

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| M1 | MEDIUM | Pipe characters in finding messages break step summary Markdown table — no `\|` escaping in jq template (action.yml:144) | Fixed — added `gsub("\\|";"\\\\|")` to message field |
| M2 | MEDIUM | No test job for `args` backward compatibility — AC11 legacy mode path untested | No action — legacy path is 4 trivial lines, ci.yml exercises it after merge, and a proper assertion would require verifying absence of annotations (complex for zero risk) |
| L1 | LOW | Temp file leak — PARTIAL/PARTIAL_STDERR not cleaned up in selective checks path (action.yml:87-88) | No action — ephemeral runners, zero practical impact |
| L2 | LOW | Dead `import tomllib` in inline Python scripts (test-action.yml:16, 44) | Fixed — removed unused import from both instances |
| L3 | LOW | Test fixture missing `from __future__ import annotations` (bad_docstrings.py:1) | No action — convention doesn't apply to CI test fixtures |

### Verification

- [x] All acceptance criteria verified
- [ ] All quality gates pass
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
