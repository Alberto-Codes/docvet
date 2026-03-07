---
title: CI Integration
---

# CI Integration

Add docvet to your CI pipeline to enforce docstring quality on every push and pull request. This page covers GitHub Actions, pre-commit hooks, and how configuration controls exit codes.

## GitHub Action

The `Alberto-Codes/docvet` action installs docvet and runs it in a single step. Findings appear as inline annotations on your pull request and as a step summary table.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `checks` | No | `all` | Checks to run: `"all"` or comma-separated list (e.g., `"enrichment,freshness"`) |
| `docvet-version` | No | `latest` | docvet version to install |
| `python-version` | No | `3.12` | Python version to set up |

??? info "Deprecated inputs (v1 backward compatibility)"
    | Input | Default | Description |
    |-------|---------|-------------|
    | `version` | `latest` | Renamed to `docvet-version`. Will be removed in v2. |
    | `args` | _(empty)_ | Replaced by `checks`. When set, runs docvet in legacy mode (raw passthrough, no annotations). Will be removed in v2. |

### Usage

=== "Basic"

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: Alberto-Codes/docvet@v1
    ```

=== "Selective checks"

    Run only specific checks:

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: Alberto-Codes/docvet@v1
            with:
              checks: 'enrichment,freshness'
    ```

=== "Version-pinned"

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: Alberto-Codes/docvet@v1
            with:
              docvet-version: '1.9.0'
    ```

=== "With griffe"

    Install griffe before running docvet to enable rendering compatibility checks:

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: actions/setup-python@v6
            with:
              python-version: '3.12'
          - run: pip install griffe
          - uses: Alberto-Codes/docvet@v1
    ```

### Outputs

The action sets step outputs that downstream steps can consume:

| Output | Description | Example |
|--------|-------------|---------|
| `badge_message` | shields.io badge message | `"passing"` or `"3 findings"` |
| `badge_color` | shields.io badge color | `brightgreen`, `yellow`, or `red` |
| `total_findings` | Total findings count | `0`, `3` |

To consume outputs, give the docvet step an `id` and reference its outputs in later steps:

```yaml
- uses: Alberto-Codes/docvet@v1
  id: docvet
  with:
    checks: "all"
- run: echo "docvet found ${{ steps.docvet.outputs.total_findings }} issues"
```

Outputs are only set in new mode (`checks` input). Legacy mode (`args` input) does not produce outputs.

### Annotation behavior

Findings are reported in two places:

- **Inline annotations** — up to 10 findings appear as `::warning` annotations directly on the pull request diff (GitHub's per-step limit). Annotations on lines outside the diff appear in the Checks tab instead.
- **Step summary** — all findings appear in a Markdown table in the step summary, with no cap. This is the authoritative complete list.

The step summary always includes a count disclosure: `"Found N findings (up to 10 shown as inline annotations)."` so reviewers know when findings exceed the annotation cap.

!!! tip "Freshness checks need git history"
    The freshness check uses `git blame` to detect stale docstrings. If your checkout step uses a shallow clone (the default), add `fetch-depth: 0` for full blame support:

    ```yaml
    - uses: actions/checkout@v6
      with:
        fetch-depth: 0
    ```

## Badge

Add a docvet badge to your README to signal that your project uses docvet for docstring quality:

```markdown
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)
```

This renders as: [![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

For a dynamic badge that updates with your CI results, see [Advanced: Dynamic Badge](#advanced-dynamic-badge) below.

## Pre-commit

docvet ships a [pre-commit](https://pre-commit.com/) hook that checks Python files before each commit.

=== "Basic"

    ```yaml
    repos:
      - repo: https://github.com/Alberto-Codes/docvet
        rev: v1.2.0
        hooks:
          - id: docvet
    ```

=== "With griffe"

    ```yaml
    repos:
      - repo: https://github.com/Alberto-Codes/docvet
        rev: v1.2.0
        hooks:
          - id: docvet
            additional_dependencies: [griffe]
    ```

=== "With exclude"

    ```yaml
    repos:
      - repo: https://github.com/Alberto-Codes/docvet
        rev: v1.2.0
        hooks:
          - id: docvet
            exclude: ^tests/
    ```

Pre-commit passes staged Python filenames as positional arguments to `docvet check`. The hook uses `require_serial: true` to prevent parallel invocations that could race on git state. Progress output is automatically suppressed because pre-commit pipes stderr.

!!! note "Exclude patterns in pre-commit mode"
    When run as a pre-commit hook, docvet checks only the files pre-commit passes — your `[tool.docvet].exclude` patterns do not apply. Use pre-commit's own `exclude` key to filter files, as shown in the "With exclude" tab above.

!!! info "Pin `rev` to a release tag"
    Replace `v1.2.0` with the [latest release tag](https://github.com/Alberto-Codes/docvet/releases). Pre-commit caches the hook environment per `rev`, so pinning to a tag avoids unnecessary reinstalls.

## Exit Codes and CI Behavior

docvet uses `fail-on` and `warn-on` to control whether findings cause a non-zero exit code:

| Exit Code | Meaning |
|-----------|---------|
| **0** | No findings in `fail-on` checks — CI passes |
| **1** | One or more findings in a `fail-on` check — CI fails |
| **2** | Usage error (invalid arguments or configuration) |

### How `fail-on` works

Checks listed in `fail-on` cause exit code 1 when they produce findings. Checks in `warn-on` are reported but never affect the exit code.

```toml
[tool.docvet]
fail-on = ["enrichment", "freshness"]  # findings here → exit 1
warn-on = ["griffe", "coverage"]       # findings here → reported only
```

Without a `[tool.docvet]` section, `fail-on` defaults to `[]` — meaning docvet always exits 0 regardless of findings. To use docvet as a CI gate, you must add at least one check to `fail-on`.

!!! tip "Default `warn-on` overlap"
    The default `warn-on` list includes all four checks. If you add a check to `fail-on`, docvet silently removes it from the default `warn-on` — no warnings, no findings lost. Warnings only appear when you explicitly set both `fail-on` and `warn-on` with overlapping checks.

!!! tip "Suppress summary output in scripts"
    Use `-q` (quiet mode) when you only need the exit code and don't want summary or timing output:

    ```yaml
    - uses: Alberto-Codes/docvet@v1
      with:
        checks: 'enrichment'
    ```

    The action uses `--format json` internally, so terminal output is already suppressed.

See [Configuration](configuration.md) for the full list of options including freshness thresholds, enrichment toggles, and exclusion patterns.

## Advanced: Dynamic Badge

For teams that want a live badge showing pass/fail status from the latest CI run, you can use the action's outputs with [schneegans/dynamic-badges-action](https://github.com/Schneegans/dynamic-badges-action) to write shields.io-compatible JSON to a GitHub Gist.

### Setup

1. **Create a GitHub Gist** — create a new public Gist (any filename). Copy the Gist ID from the URL.

2. **Add repository secrets and variables** — in your repo's Settings > Secrets and variables > Actions:
    - Add a **secret** named `GIST_SECRET` containing a [personal access token](https://github.com/settings/tokens) with the `gist` scope.
    - Add a **variable** named `BADGE_GIST_ID` containing the Gist ID from step 1.

3. **Add the badge step** to your workflow after the docvet action:

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: Alberto-Codes/docvet@v1
            id: docvet
            with:
              checks: "all"
          - name: Update docvet badge
            if: always() && github.ref == 'refs/heads/main'
            continue-on-error: true
            uses: schneegans/dynamic-badges-action@v1.7.0
            with:
              auth: ${{ secrets.GIST_SECRET }}
              gistID: ${{ vars.BADGE_GIST_ID }}
              filename: docvet-badge.json
              label: docvet
              message: ${{ steps.docvet.outputs.badge_message || 'error' }}
              color: ${{ steps.docvet.outputs.badge_color || 'lightgrey' }}
    ```

4. **Add the badge to your README**:

    ```markdown
    [![docvet](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<USER>/<GIST_ID>/raw/docvet-badge.json)](https://github.com/Alberto-Codes/docvet)
    ```

    Replace `<USER>` with your GitHub username and `<GIST_ID>` with the Gist ID.

### Badge states

| State | Message | Color |
|-------|---------|-------|
| All checks pass | `passing` | ![brightgreen](https://img.shields.io/badge/-brightgreen-brightgreen) |
| Only recommended findings | `N findings` | ![yellow](https://img.shields.io/badge/-yellow-yellow) |
| Required findings present | `N findings` | ![red](https://img.shields.io/badge/-red-red) |

!!! tip "Freshness checks need git history"
    If your workflow includes the `freshness` check (or `checks: "all"`), add `fetch-depth: 0` to your checkout step for full `git blame` support. See [Annotation behavior](#annotation-behavior) above for details.

!!! note "Branch guard and fork safety"
    The `if: always() && github.ref == 'refs/heads/main'` condition ensures the badge only updates on pushes to `main`, not on pull request branches. The `continue-on-error: true` prevents badge failures (e.g., from forks without Gist access) from failing the overall workflow.
