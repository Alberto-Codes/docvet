---
title: CI Integration
---

# CI Integration

Add docvet to your CI pipeline to enforce docstring quality on every push and pull request. This page covers GitHub Actions, pre-commit hooks, and how configuration controls exit codes.

## GitHub Action

The `Alberto-Codes/docvet` action installs docvet and runs it in a single step.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `version` | No | `latest` | docvet version to install |
| `args` | No | `check` | Arguments passed to the `docvet` CLI |

### Usage

=== "Basic"

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: Alberto-Codes/docvet@v1
            with:
              args: 'check --all'
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
              version: '1.2.0'
              args: 'check --all'
    ```

=== "With griffe"

    Install griffe before running docvet to enable rendering compatibility checks:

    ```yaml
    jobs:
      docvet:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v6
          - uses: actions/setup-python@v5
            with:
              python-version: '3.12'
          - run: pip install griffe
          - uses: Alberto-Codes/docvet@v1
            with:
              args: 'check --all'
    ```

!!! tip "Freshness checks need git history"
    The freshness check uses `git blame` to detect stale docstrings. If your checkout step uses a shallow clone (the default), add `fetch-depth: 0` for full blame support:

    ```yaml
    - uses: actions/checkout@v6
      with:
        fetch-depth: 0
    ```

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
        args: 'check --all -q'
    ```

See [Configuration](configuration.md) for the full list of options including freshness thresholds, enrichment toggles, and exclusion patterns.
