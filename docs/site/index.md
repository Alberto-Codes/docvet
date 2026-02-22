# Getting Started

docvet is a CLI tool that vets your Python docstrings for completeness, accuracy, and rendering compatibility — the checks that linters and presence tools miss.

## Installation

=== "Core"

    ```bash
    pip install docvet
    ```

    Includes enrichment, freshness, and coverage checks.

=== "With griffe"

    ```bash
    pip install docvet[griffe]
    ```

    Adds the optional griffe rendering compatibility check for mkdocs projects.

## Quickstart

Run docvet against your entire codebase:

```bash
docvet check --all
```

Or check only files with uncommitted changes (the default):

```bash
docvet check
```

Or check only staged files, ideal for pre-commit hooks:

```bash
docvet check --staged
```

Here's what the output looks like:

```
src/myapp/utils.py:42: missing-raises Function 'parse_config' raises ValueError but Raises section is missing [required]
src/myapp/utils.py:87: stale-diff-sig Function 'validate_input' signature changed without docstring update [required]
src/myapp/models.py:15: missing-attributes Class 'User' has 3 undocumented attributes [required]

3 findings (3 required, 0 recommended)
```

Each finding shows the file, line number, rule name, a human-readable message, and severity.

## The Four Checks

docvet fills the gap between style linting (ruff D rules) and presence checking (interrogate) with four layers of deeper analysis:

### Enrichment — Completeness (Layer 3)

Detects missing docstring sections like Raises, Yields, Attributes, and Examples by analyzing your code's AST. 10 rules cover functions, classes, modules, and format conventions.

```bash
docvet enrichment --all
```

### Freshness — Accuracy (Layer 4)

Flags code changes that weren't accompanied by docstring updates. **Diff mode** (default) maps git diff hunks to symbols for fast feedback. **Drift mode** uses git blame to find long-stale docstrings across the codebase. 5 rules across two modes.

```bash
docvet freshness --all              # diff mode (default)
docvet freshness --all --mode drift # drift mode (git blame sweep)
```

### Coverage — Visibility (Layer 6)

Finds missing `__init__.py` files that would make Python packages invisible to mkdocs and other documentation generators. 1 rule.

```bash
docvet coverage --all
```

### Griffe — Rendering (Layer 5)

Captures griffe parser warnings that would cause broken rendering in mkdocs-material sites. Catches unknown parameters, missing type annotations, and format issues. 3 rules, requires the optional `griffe` extra.

```bash
docvet griffe --all
```

## What's Next

- See the [CLI Reference](cli-reference.md) for full command and option documentation.
