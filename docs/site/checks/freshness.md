# Freshness Check

The freshness check implements **Layer 4 (Accuracy)** of docvet's quality model. It detects stale docstrings — code that changed without a corresponding docstring update — using git history analysis. Two modes offer different trade-offs: **diff mode** for fast feedback on recent changes, and **drift mode** for a comprehensive sweep of historical staleness. 5 rules across two modes.

```bash
docvet freshness --all
```

## Modes

### Diff Mode (Default)

Diff mode parses `git diff` output and maps changed hunks to AST symbols. It flags symbols whose code was modified but whose docstring was not updated in the same diff. This is fast and ideal for pre-commit hooks or CI on pull requests.

Changes are classified by severity based on *what* changed:

- **HIGH** (`stale-signature`): The function signature changed — parameters, return type, or decorators
- **MEDIUM** (`stale-body`): The function body changed — logic, control flow, or internal behavior
- **LOW** (`stale-import`): Only imports or formatting changed outside the function body

If the docstring *was* updated in the same diff, the finding is suppressed entirely.

!!! tip "Pre-commit integration"
    Diff mode with `--staged` is ideal for pre-commit hooks — it only checks files you're about to commit and runs in under a second.

### Drift Mode

Drift mode uses `git blame --line-porcelain` to extract per-line timestamps, then compares when code was last modified versus when the docstring was last touched. It finds docstrings that have gradually fallen behind over time.

Two thresholds control sensitivity:

- **`drift-threshold`**: Maximum days the code can be ahead of its docstring before flagging `stale-drift`
- **`age-threshold`**: Maximum days a docstring can go without *any* update before flagging `stale-age`

!!! warning "Performance"
    Drift mode runs `git blame` on every file — it's thorough but slower than diff mode. Best suited for scheduled CI runs or periodic sweeps, not pre-commit hooks.

## Rules

**Diff Mode:**

| Rule ID | Category | Severity | Description |
|---------|----------|----------|-------------|
| [`stale-signature`](../rules/stale-signature.md) | required | HIGH | Function signature changed but docstring not updated |
| [`stale-body`](../rules/stale-body.md) | recommended | MEDIUM | Function body changed but docstring not updated |
| [`stale-import`](../rules/stale-import.md) | recommended | LOW | Import changed but docstring not updated |

**Drift Mode:**

| Rule ID | Category | Description |
|---------|----------|-------------|
| [`stale-drift`](../rules/stale-drift.md) | recommended | Code modified more recently than docstring (exceeds `drift-threshold` days) |
| [`stale-age`](../rules/stale-age.md) | recommended | Docstring untouched beyond `age-threshold` days |

## Example Output

**Diff mode finding:**

``` linenums="1"
src/myapp/utils.py:42: stale-signature Function 'parse_config' signature changed but docstring not updated [required]
src/myapp/utils.py:87: stale-body Function 'validate_input' body changed but docstring not updated [recommended]

2 findings (1 required, 1 recommended)
```

**Drift mode finding:**

``` linenums="1"
src/myapp/utils.py:42: stale-drift Function 'parse_config' code modified 2026-01-15, docstring last modified 2025-11-02 (74 days drift) [recommended]
src/myapp/models.py:10: stale-age Class 'User' docstring untouched since 2025-08-20 (185 days) [recommended]

2 findings (0 required, 2 recommended)
```

## Configuration

The freshness check is configured under `[tool.docvet.freshness]` in your `pyproject.toml`.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `drift-threshold` | `int` | `30` | Maximum days code can be ahead of its docstring before flagging drift |
| `age-threshold` | `int` | `90` | Maximum days a docstring can go without any update |

Example configuration:

```toml
[tool.docvet.freshness]
drift-threshold = 14
age-threshold = 60
```

## Usage

Run diff mode (default) on your entire codebase:

```bash
docvet freshness --all
```

Run drift mode for a comprehensive git blame sweep:

```bash
docvet freshness --all --mode drift
```

Check only files with unstaged changes (diff mode):

```bash
docvet freshness
```

Check only staged files:

```bash
docvet freshness --staged
```

Check specific files in drift mode:

```bash
docvet freshness --files src/myapp/utils.py --mode drift
```

Add `--verbose` for file count and timing, or `-q` to suppress the summary line:

```bash
docvet freshness --all --verbose
docvet freshness --all -q
```

Or run freshness as part of all checks (diff mode only):

```bash
docvet check --all
```
