# docvet

docvet is a Python CLI tool that checks whether docstrings are complete, accurate, and renderable. It fills the gap between style linting (ruff) and presence checking (interrogate).

## Quality Model

| Layer | Check | What it catches |
|-------|-------|-----------------|
| 3. Completeness | `enrichment` | Missing Raises, Yields, Attributes, Examples, and 6 more sections |
| 4. Accuracy | `freshness` | Docstrings that fell out of sync with code (git diff + blame) |
| 5. Rendering | `griffe` | Warnings that break mkdocs-material + mkdocstrings output |
| 6. Visibility | `coverage` | Packages missing `__init__.py` (invisible to mkdocs) |

Layers 1-2 (presence and style) are handled by interrogate and ruff.

## Install

```bash
pip install docvet
```

For griffe rendering checks:

```bash
pip install docvet[griffe]
```

## Run

| Command | What it does |
|---------|--------------|
| `docvet check --all` | Run all checks on entire codebase |
| `docvet check` | Run all checks on files changed since last commit |
| `docvet check --staged` | Run checks on staged files only |
| `docvet enrichment` | Check for missing docstring sections |
| `docvet freshness` | Detect stale docstrings via git |
| `docvet coverage` | Find packages invisible to mkdocs |
| `docvet griffe` | Check mkdocs rendering compatibility |

Use `docvet check --all` for broad sweeps. Use `docvet check` or `docvet check --staged` for incremental workflows.

## Configure

Add `[tool.docvet]` to `pyproject.toml`:

```toml
[tool.docvet]
exclude = ["tests", "scripts"]
fail-on = ["enrichment", "freshness", "coverage", "griffe"]

[tool.docvet.freshness]
drift-threshold = 30
age-threshold = 90
```

Key options: `exclude` filters directories, `fail-on` controls which checks cause a non-zero exit code.

## What Each Check Does

- **enrichment** -- Flags functions, classes, and modules missing required docstring sections (Raises, Yields, Receives, Warns, Attributes, Examples, cross-references, and more). 10 rules.
- **freshness** -- Detects docstrings that no longer match the code, using git diff (immediate) and git blame (drift over time). 5 rules.
- **coverage** -- Finds package directories without `__init__.py`, which makes them invisible to mkdocs. 1 rule.
- **griffe** -- Captures griffe parser warnings that would break mkdocs rendering. 3 rules.

## Fixing Findings

Each finding includes a rule ID (e.g., `missing-raises`, `stale-signature`). Look up the rule for explanation and fix guidance:

https://alberto-codes.github.io/docvet/rules/<rule-id>/

General approach by category:

- **enrichment**: Add the missing section to the docstring.
- **freshness**: Update the docstring to match the current code.
- **coverage**: Add an `__init__.py` to the package directory.
- **griffe**: Fix the formatting issue flagged in the warning message.
