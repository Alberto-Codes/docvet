# Presence Check

The presence check implements **Layer 1 (Presence)** of docvet's quality model. It detects public symbols — modules, classes, functions, and methods — that lack a docstring, and reports per-file coverage statistics. 1 rule. This is docvet's built-in replacement for interrogate, with zero extra dependencies.

```bash
docvet presence --all
```

## Rules

| Rule ID | Category | Description |
|---------|----------|-------------|
| [`missing-docstring`](../rules/missing-docstring.md) | required | Public symbol has no docstring |

The check parses each file with the standard library `ast` module, extracts all documentable symbols (modules, classes, functions, methods), applies filtering rules (init, magic, private), and reports one finding per undocumented symbol. Coverage statistics are aggregated across all files.

!!! tip "When this matters"
    Docstrings are the primary signal AI coding agents use to understand your code. Missing docstrings mean agents operate on guesswork — and research shows absent documentation degrades LLM task success significantly.

## Example Output

**Default** (with findings):

``` linenums="1"
src/myapp/utils.py:12: missing-docstring Public function has no docstring [required]
src/myapp/models.py:5: missing-docstring Public class has no docstring [required]
Vetted 10 files [presence] — 2 findings (2 required, 0 recommended), 87.0% coverage. (0.3s)
```

**Verbose** (with coverage detail):

``` linenums="1"
src/myapp/utils.py:12: missing-docstring Public function has no docstring [required]
Docstring coverage: 87/100 symbols (87.0%) — below 95.0% threshold
Vetted 10 files [presence] — 1 finding (1 required, 0 recommended), 87.0% coverage. (0.3s)
```

**Quiet** (findings only, no summary):

``` linenums="1"
src/myapp/utils.py:12: missing-docstring Public function has no docstring [required]
```

## Relationship to ruff D100–D107

ruff's pydocstyle rules (D100–D107) also detect missing docstrings. The key differences:

| Aspect | ruff D100–D107 | docvet presence |
|--------|---------------|-----------------|
| **Coverage metrics** | No | Yes — per-file and aggregate percentage |
| **Threshold enforcement** | No | Yes — `min-coverage` with CI exit code |
| **Pipeline integration** | Separate tool | Unified with enrichment, freshness, griffe, coverage |
| **Filtering** | Per-rule enable/disable | `ignore-init`, `ignore-magic`, `ignore-private` |

You can use both tools together: ruff for style enforcement (D rules), docvet for coverage tracking and threshold enforcement.

## Configuration

These keys go under `[tool.docvet.presence]`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable or disable the presence check |
| `min-coverage` | `float` | `0.0` | Minimum coverage percentage (0.0–100.0). When set above 0, the summary includes a pass/fail indicator. |
| `ignore-init` | `bool` | `true` | Skip `__init__` methods |
| `ignore-magic` | `bool` | `true` | Skip dunder methods (`__repr__`, `__str__`, etc.) |
| `ignore-private` | `bool` | `true` | Skip single-underscore-prefixed symbols (`_helper`) |

### Example

```toml
[tool.docvet.presence]
min-coverage = 95.0
ignore-init = false
```

## Usage

Run the presence check on your entire codebase:

```bash
docvet presence --all
```

Check only files with unstaged changes (default):

```bash
docvet presence
```

Check only staged files:

```bash
docvet presence --staged
```

Check specific files:

```bash
docvet presence --files src/myapp/utils.py --files src/myapp/models.py
```

Add `--verbose` for coverage detail and timing, or `-q` to suppress the summary line:

```bash
docvet presence --all --verbose
docvet presence --all -q
```

Or run presence as part of all checks:

```bash
docvet check --all
```

## Migrating from interrogate

docvet's presence check is a zero-dependency replacement for interrogate. Follow these four steps to migrate:

### Step 1: Remove interrogate

Remove interrogate from your development dependencies and CI configuration:

```bash
# If using pip
pip uninstall interrogate

# If using uv
uv remove interrogate --dev
```

Remove any `[tool.interrogate]` section from your `pyproject.toml`.

### Step 2: Add docvet presence configuration

Add the equivalent settings to `[tool.docvet.presence]` in your `pyproject.toml`:

```toml
[tool.docvet.presence]
min-coverage = 95.0      # was: --fail-under 95
ignore-init = true        # was: --ignore-init-method (default matches)
ignore-magic = true       # was: --ignore-magic (default matches)
ignore-private = true     # was: --ignore-private (default matches)
```

### Step 3: Map your interrogate options

| interrogate option | docvet equivalent | Notes |
|-------------------|-------------------|-------|
| `--fail-under N` | `min-coverage = N` | Percentage threshold |
| `--ignore-init-method` | `ignore-init = true` | Default in docvet |
| `--ignore-magic` | `ignore-magic = true` | Default in docvet |
| `--ignore-private` | `ignore-private = true` | Default in docvet |
| `--ignore-module` | No equivalent | Modules are always checked |
| `-e` / `--exclude` | `[tool.docvet] exclude = [...]` | Top-level exclude, shared across all checks |

### Step 4: Update CI

Replace your interrogate CI step with docvet:

```yaml
# Before (interrogate)
- run: interrogate -v --fail-under 95

# After (docvet)
- run: docvet presence --all
```

If you use `fail-on` to enforce presence in CI alongside other checks:

```toml
[tool.docvet]
fail-on = ["presence", "enrichment"]
```

```yaml
# Single command runs all enforced checks
- run: docvet check --all
```

!!! tip "Zero new dependencies"
    Unlike interrogate, docvet's presence check uses only the standard library `ast` module. If you already have docvet installed for enrichment or freshness checking, the presence check adds zero overhead.
