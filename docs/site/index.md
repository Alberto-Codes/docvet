---
title: Getting Started
---

# The docstring checks that linters miss.

[![PyPI version](https://img.shields.io/pypi/v/docvet)](https://pypi.org/project/docvet/)
[![Python versions](https://img.shields.io/pypi/pyversions/docvet)](https://pypi.org/project/docvet/)
[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/docvet/ci.yml?branch=develop&label=CI)](https://github.com/Alberto-Codes/docvet/actions)
[![License](https://img.shields.io/pypi/l/docvet)](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE)

docvet vets your Python docstrings for **completeness**, **accuracy**, and **rendering compatibility** — the layers beyond style and presence that tools like ruff and interrogate don't cover.

## Quick Start

```bash
pip install docvet && docvet check --all
```

## The Quality Model

Most tools stop at style and presence. docvet picks up where they leave off:

| Layer | Check | What It Catches | Tool |
|:-----:|-------|-----------------|------|
| 1 | Style | Formatting, conventions | ruff D rules |
| 2 | Presence | Missing docstrings | interrogate |
| **3** | **Completeness** | **Missing sections (Raises, Yields, Attributes)** | **docvet enrichment** |
| **4** | **Accuracy** | **Stale docstrings after code changes** | **docvet freshness** |
| **5** | **Rendering** | **Broken mkdocs output** | **docvet griffe** |
| **6** | **Visibility** | **Packages hidden from doc generators** | **docvet coverage** |

## Checks

<div class="grid cards" markdown>

-   :material-check-all:{ .lg .middle } **Enrichment**

    ---

    Detects missing Raises, Yields, Attributes, and Examples sections via AST analysis. 10 rules.

    [:octicons-arrow-right-24: Learn more](checks/enrichment.md)

-   :material-clock-check-outline:{ .lg .middle } **Freshness**

    ---

    Flags code changes without docstring updates using git diff and git blame. 5 rules, two modes.

    [:octicons-arrow-right-24: Learn more](checks/freshness.md)

-   :material-eye-check-outline:{ .lg .middle } **Coverage**

    ---

    Finds missing `__init__.py` files that hide packages from documentation generators.

    [:octicons-arrow-right-24: Learn more](checks/coverage.md)

-   :material-file-document-check-outline:{ .lg .middle } **Griffe**

    ---

    Captures griffe parser warnings that break mkdocs rendering. 3 rules.

    [:octicons-arrow-right-24: Learn more](checks/griffe.md)

</div>

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

## Usage

Run docvet against your entire codebase:

```bash
docvet check --all
```

Or check only files with unstaged changes (the default):

```bash
docvet check
```

Or check only staged files, ideal for pre-commit hooks:

```bash
docvet check --staged
```

Here's what the output looks like:

``` linenums="1"
src/myapp/utils.py:42: missing-raises Function 'parse_config' raises ValueError but Raises section is missing [required]
src/myapp/utils.py:87: stale-signature Function 'validate_input' signature changed without docstring update [required]
src/myapp/models.py:15: missing-attributes Class 'User' has 3 undocumented attributes [required]

3 findings (3 required, 0 recommended)
```

Each finding shows the file, line number, rule name, a human-readable message, and severity.

## What's Next

- Set up [CI Integration](ci-integration.md) with GitHub Actions or pre-commit hooks.
- See the [CLI Reference](cli-reference.md) for full command and option documentation.
- Browse [Configuration](configuration.md) for all `pyproject.toml` options.
