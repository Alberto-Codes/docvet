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

The action installs `docvet[griffe]`, with or without `docvet-version`, so the
rendering compatibility check needs no extra setup and is reached through the
default `checks: 'all'` along with every other check. Note that docvet releases
before 1.7.0 declare that extra without an upper bound, so pinning one installs
whatever griffe publishes at the time rather than a version docvet was released
against.

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

!!! warning "Behavior change — this can turn a passing build red"

    Earlier releases installed plain `docvet`, which has no griffe
    dependency, so the griffe check was skipped and contributed zero
    findings. It now runs.

    `determine_run_outcome` (`src/docvet/reporting.py`) returns exit
    code 1 as soon as any check listed in `fail-on` reports findings.
    So if your
    `pyproject.toml` has `griffe` in `[tool.docvet] fail-on`, your job
    goes from green to failing with no change on your side. This
    repository's own `ci.yml` docvet job is exactly such a consumer.

    These are not new problems — it is the check finally running on
    docstrings that were always broken. To get back to green, fix the
    griffe findings or remove `griffe` from `fail-on`.

The action installs `docvet[griffe]`, so the rendering compatibility check runs
on the default `checks: all` path with no extra step. Running docvet directly
rather than through the action requires the extra:

```yaml
      - run: pip install 'docvet[griffe]'
```

### Outputs

The action sets step outputs that downstream steps can consume:

| Output | Description | Example |
|--------|-------------|---------|
| `badge_message` | shields.io badge message | `"passing"`, `"3 findings"`, `"gate unavailable"`, or `"3 findings, gate unavailable"` |
| `badge_color` | shields.io badge color | `brightgreen`, `yellow`, `red`, or `orange` |
| `total_findings` | Total findings count | `0`, `3` |

A gate listed in `fail-on` that could not run and failed the build publishes `gate unavailable` / `orange` rather than `passing` / `brightgreen` — the gate produced no findings because it never executed, not because the code was clean. When such a run also has findings, the badge keeps the count and the failure colour (`3 findings, gate unavailable` / `red`), so it never hides what a findings-only badge would have shown. The badge is unchanged when a project opts out with `fail-on-unavailable = false`, where such a run still exits 0.

To consume outputs, give the docvet step an `id` and reference its outputs in later steps:

{% raw %}
```yaml
- uses: Alberto-Codes/docvet@v1
  id: docvet
  with:
    checks: "all"
- run: echo "docvet found ${{ steps.docvet.outputs.total_findings }} issues"
```
{% endraw %}

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
| **1** | A `fail-on` check produced findings, or could not run at all — CI fails. `run.status` in JSON output distinguishes the two (`findings` vs `unavailable`) |
| **2** | Usage error (invalid arguments or configuration) |

### How `fail-on` works

Checks listed in `fail-on` cause exit code 1 when they produce findings. Checks in `warn-on` are reported but never affect the exit code.

```toml
[tool.docvet]
fail-on = ["enrichment", "freshness"]  # findings here → exit 1
warn-on = ["griffe", "coverage"]       # findings here → reported only
```

Without a `[tool.docvet]` section, `fail-on` defaults to `[]` — meaning docvet always exits 0 regardless of findings. To use docvet as a CI gate, you must add at least one check to `fail-on`.

### Checks that cannot run

A check listed in `fail-on` that cannot execute never certified the gate you configured, so by default docvet exits 1 and says why on stderr:

```text
error: griffe check was configured to gate the run but could not run (griffe not installed)
  remedy: pip install 'docvet[griffe]', or drop griffe from fail-on
```

!!! warning "Behavior change"
    This run used to warn and exit 0. Any environment that lists a check in `fail-on` and cannot run it there will now fail where it previously passed. That is intended: the old exit 0 certified a gate that never executed. Install the missing extra, drop the check from `fail-on`, or opt out with `fail-on-unavailable = false`.

To restore the old warn-and-continue behavior, opt out:

```toml
[tool.docvet]
fail-on = ["griffe"]
fail-on-unavailable = false
```

or pass the flag for a single run:

```bash
docvet --no-fail-on-unavailable check --all
```

With the opt-out in place, the same situation exits 0 and the notice is a warning:

```text
warning: griffe check was configured to gate the run but could not run (griffe not installed), so that gate never executed
  remedy: pip install 'docvet[griffe]', or drop griffe from fail-on
  this did not fail the run because this project opted out with fail-on-unavailable = false; drop that setting (or pass --fail-on-unavailable) to make it an error
```

The warning is always printed, including under `--quiet`. It speaks only for that check — it is written mid-run, so another `fail-on` check with findings or a `min-coverage` shortfall can still fail the run.

The griffe check cannot run when `griffe` is not importable, or when `docstring-style` is `"sphinx"` (griffe's Google parser cannot read RST field lists). The presence check cannot run when it is switched off with `[tool.docvet.presence] enabled = false` while something still gates on it — `presence` listed in `fail-on`, or a `min-coverage` floor, which `determine_run_outcome` enforces without consulting `fail-on` at all. Either way the gate was configured never to execute, and the reason names the floor that went unmeasured. A check disabled with nothing gating on it is an ordinary opt-out and is not reported. A check that is unavailable but **not** listed in `fail-on` never fails the run either way: it exits 0. `docvet check` mentions the skip only under `--verbose`, since the check was one of many it ran; the `docvet griffe` subcommand always reports it, because you asked for that check by name and it did not run.

JSON output carries the same information in a `run` object, so an agent or a script can tell an incomplete run from one whose gates found problems — the exit code is 1 for both:

```json
{
  "run": {
    "status": "unavailable",
    "exit_code": 1,
    "exit_reason": "checks configured in fail-on could not run: griffe (griffe not installed)",
    "unavailable_checks": [
      {
        "check": "griffe",
        "reason": "griffe not installed",
        "remedy": "pip install 'docvet[griffe]', or drop griffe from fail-on",
        "blocking": true,
        "configured_gate": true
      }
    ]
  }
}
```

`status` is `"passed"`, `"findings"`, or `"unavailable"`. `unavailable_checks` lists every check that could not run and is empty when every check executed. `configured_gate` says the config asked that check to gate the run — listed in `fail-on`, or, for presence, enforcing a `min-coverage` floor, which gates without appearing in `fail-on`, so the field is named for the gate rather than for membership of that list; `blocking` says that fact actually failed the run, which is the default unless the project set `fail-on-unavailable = false`. `status` names which condition blocked the run rather than everything that happened, so read `summary.total` for findings regardless of `status`. With `fail-on-unavailable = false`, a configured gate that never ran reports `status: "passed"`, `exit_code: 0`, and an entry with `"configured_gate": true, "blocking": false` — read `unavailable_checks`, not the exit code, to detect it. `exit_reason` names that gate too, so it never contradicts `unavailable_checks`:

```text
no check in fail-on reported findings, but these checks in fail-on could not run and this project opted out with fail-on-unavailable = false: griffe (griffe not installed)
```

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

!!! tip "Machine-readable quality metrics"
    Use `--summary --format json` to include per-check quality percentages in the JSON output. The `quality` object is additive — it appears alongside the existing `summary` object only when `--summary` is active:

    ```bash
    docvet check --all --summary --format json
    ```

See [Configuration](configuration.md) for the full list of options including freshness thresholds, enrichment toggles, and exclusion patterns.

## Advanced: Dynamic Badge

For teams that want a live badge showing pass/fail status from the latest CI run, you can use the action's outputs with [schneegans/dynamic-badges-action](https://github.com/Schneegans/dynamic-badges-action) to write shields.io-compatible JSON to a GitHub Gist.

### Setup

1. **Create a GitHub Gist** — create a new public Gist (any filename). Copy the Gist ID from the URL.

2. **Add repository secrets and variables** — in your repo's Settings > Secrets and variables > Actions:
    - Add a **secret** named `GIST_SECRET` containing a [personal access token](https://github.com/settings/tokens) with the `gist` scope.
    - Add a **variable** named `BADGE_GIST_ID` containing the Gist ID from step 1.

3. **Add the badge step** to your workflow after the docvet action:

    {% raw %}
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
    {% endraw %}

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
| A gate in `fail-on` could not run and failed the build | `gate unavailable` | ![orange](https://img.shields.io/badge/-orange-orange) |
| That gate plus findings | `N findings, gate unavailable` | ![red](https://img.shields.io/badge/-red-red) |

!!! tip "Freshness checks need git history"
    If your workflow includes the `freshness` check (or `checks: "all"`), add `fetch-depth: 0` to your checkout step for full `git blame` support. See [Annotation behavior](#annotation-behavior) above for details.

!!! note "Branch guard and fork safety"
    The `if: always() && github.ref == 'refs/heads/main'` condition ensures the badge only updates on pushes to `main`, not on pull request branches. The `continue-on-error: true` prevents badge failures (e.g., from forks without Gist access) from failing the overall workflow.
