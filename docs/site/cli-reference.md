# CLI Reference

docvet provides five subcommands. Global options are placed **before** the subcommand; discovery flags and check-specific options are placed **after** it.

```
docvet [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

## Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose` | flag | off | Enable verbose output (shows file count and active checks) |
| `--format` | `terminal` \| `markdown` | `terminal` | Output format |
| `--output` | `PATH` | stdout | Write report to file |
| `--config` | `PATH` | auto-detected | Path to `pyproject.toml` |
| `--version` | flag | | Show version and exit |

When `--output` is specified without `--format`, the format defaults to `markdown`.

Global options must precede the subcommand:

```bash
# Correct
docvet --verbose --format markdown check --all

# Wrong — global options after subcommand won't be recognized
docvet check --verbose --all
```

## Discovery Flags

All subcommands accept the same set of discovery flags. These are **mutually exclusive** — use only one at a time.

| Flag | Description |
|------|-------------|
| *(default)* | Files from `git diff` (unstaged changes) |
| `--staged` | Files from `git diff --cached` (staged changes) |
| `--all` | All Python files in the project |
| `--files` | Specific files (repeatable) |

The `--files` flag is repeated for each file:

```bash
docvet check --files src/app/utils.py --files src/app/models.py
```

## Commands

### `docvet check`

Run all enabled checks.

```bash
docvet check              # unstaged changes (default)
docvet check --staged     # staged files
docvet check --all        # entire codebase
```

This runs enrichment, freshness, coverage, and griffe (if installed) in sequence and produces a unified report.

### `docvet enrichment`

Check for missing docstring sections.

```bash
docvet enrichment --all
```

Analyzes Python AST to detect missing Raises, Yields, Attributes, Examples, and other sections that should be present based on the code's behavior. 10 rules covering functions, classes, modules, and format conventions.

### `docvet freshness`

Detect stale docstrings.

```bash
docvet freshness --all                # diff mode (default)
docvet freshness --all --mode drift   # drift mode
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--mode` | `diff` \| `drift` | `diff` | Freshness check strategy |

**Diff mode** maps git diff hunks to AST symbols and flags code changes without matching docstring updates. Fast, targeted feedback.

**Drift mode** uses git blame timestamps to find docstrings that haven't been updated relative to their code. Sweeps the entire codebase for long-stale documentation.

### `docvet coverage`

Find files invisible to mkdocs.

```bash
docvet coverage --all
```

Walks the directory tree from each discovered file up to the source root, checking for missing `__init__.py` files that would make packages invisible to documentation generators.

### `docvet griffe`

Check mkdocs rendering compatibility.

```bash
docvet griffe --all
```

Loads packages with the griffe parser and captures warnings that would cause broken rendering in mkdocs-material sites. Detects unknown parameters, missing type annotations, and docstring format issues.

!!! note
    Requires the optional `griffe` extra: `pip install docvet[griffe]`

## Configuration

docvet reads configuration from the `[tool.docvet]` section in `pyproject.toml`. If the section is missing, sensible defaults are used. See the Configuration guide for available options and their defaults.

Specify a custom config path with:

```bash
docvet --config path/to/pyproject.toml check --all
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | No findings (or no findings in `fail_on` checks) |
| `1` | Findings detected in `fail_on` checks |
| `2` | Usage error (invalid arguments or options) |

## Examples

Check staged files before committing:

```bash
docvet check --staged
```

Generate a markdown report for CI:

```bash
docvet --format markdown --output report.md check --all
```

Run only the freshness drift sweep with verbose output:

```bash
docvet --verbose freshness --all --mode drift
```

Check specific files:

```bash
docvet enrichment --files src/myapp/utils.py --files src/myapp/models.py
```
