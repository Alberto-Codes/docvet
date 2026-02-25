[![PyPI](https://img.shields.io/pypi/v/docvet)](https://pypi.org/project/docvet/)
[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/docvet/ci.yml?branch=main)](https://github.com/Alberto-Codes/docvet/actions)
[![License](https://img.shields.io/pypi/l/docvet)](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/docvet)](https://pypi.org/project/docvet/)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

# docvet

**ruff checks how your docstrings look. interrogate checks if they exist. docvet checks if they're right.**

Existing tools cover presence and style. docvet delivers the layers they miss:

| Layer | Check | ruff | interrogate | pydoclint | **docvet** |
|-------|-------|------|-------------|-----------|------------|
| 1. Presence | "Does a docstring exist?" | -- | Yes | -- | -- |
| 2. Style | "Is it formatted correctly?" | Yes | -- | -- | -- |
| 3. Completeness | "Does it have all required sections?" | -- | -- | Partial | **Yes** |
| 4. Accuracy | "Does it match the current code?" | -- | -- | -- | **Yes** |
| 5. Rendering | "Will mkdocs render it correctly?" | -- | -- | -- | **Yes** |
| 6. Visibility | "Will mkdocs even see the file?" | -- | -- | -- | **Yes** |

**pydoclint** checks Args/Returns/Raises alignment with function signatures (structural completeness). docvet's enrichment covers that plus Yields, Receives, Warns, Attributes, Examples, typed attributes, and cross-references -- 19 rules across 4 checks. docvet also covers freshness (git diff/blame), griffe rendering compatibility, and mkdocs coverage -- territory no other tool touches.

**[Quickstart](#quickstart)** | **[GitHub Action](#github-action)** | **[Pre-commit](#pre-commit)** | **[Configuration](#configuration)** | **[Docs](https://alberto-codes.github.io/docvet/)**

## What It Checks

**Enrichment** (completeness) -- 10 rules:
`missing-raises` `missing-yields` `missing-receives` `missing-warns` `missing-other-parameters` `missing-attributes` `missing-typed-attributes` `missing-examples` `missing-cross-references` `prefer-fenced-code-blocks`

**Freshness** (accuracy) -- 5 rules:
`stale-signature` `stale-body` `stale-import` `stale-drift` `stale-age`

**Griffe** (rendering) -- 3 rules:
`griffe-unknown-param` `griffe-missing-type` `griffe-format-warning`

**Coverage** (visibility) -- 1 rule:
`missing-init`

## Quickstart

```bash
pip install docvet && docvet check --all
```

For optional griffe rendering checks:

```bash
pip install docvet[griffe]
```

Example output:

```
src/mypackage/utils.py:42: missing-raises Function 'parse_config' raises ValueError but has no Raises section
src/mypackage/models.py:15: stale-signature Function 'process' signature changed but docstring not updated
src/mypackage/api.py:1: missing-init Package directory missing __init__.py (invisible to mkdocs)
```

## Configuration

Configure via `[tool.docvet]` in your `pyproject.toml`. All checks run and print findings. Checks listed in `fail-on` cause a non-zero exit code; unlisted checks are treated as warnings.

```toml
[tool.docvet]
exclude = ["tests", "scripts"]
fail-on = ["griffe", "coverage"]

[tool.docvet.freshness]
drift-threshold = 30
age-threshold = 90
```

## Pre-commit

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v1.2.0
    hooks:
      - id: docvet
```

For griffe rendering checks, add the optional dependency:

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v1.2.0
    hooks:
      - id: docvet
        additional_dependencies: [griffe]
```

## GitHub Action

Add docvet to your GitHub Actions workflow:

```yaml
- uses: Alberto-Codes/docvet@v1
```

With version pinning and custom arguments:

```yaml
- uses: Alberto-Codes/docvet@v1
  with:
    version: '1.2.0'
    args: 'check --all'
```

For griffe rendering checks, install griffe before running docvet:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
- run: pip install griffe
- uses: Alberto-Codes/docvet@v1
  with:
    args: 'check --all'
```

## Better Docstrings, Better AI

AI coding agents rely on docstrings as context when generating and modifying code. Research shows stale or incorrect documentation is actively harmful -- worse than no docs at all:

- Incorrect docs [degrade LLM task success by 22.6 percentage points](https://arxiv.org/abs/2404.03114)
- Comment density [improves code generation by 40-54%](https://arxiv.org/abs/2402.13013)
- Misleading comments [reduce LLM fault localization accuracy to 24.55%](https://arxiv.org/abs/2504.04372)
- Performance [drops substantially without docstrings](https://arxiv.org/abs/2508.09537)

As the [2025 DORA report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report) puts it: "AI doesn't fix a team; it amplifies what's already there." The [only signal correlating with AI productivity is code quality](https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory).

docvet's freshness checking catches the accuracy gap that stale docs create, and its enrichment rules ensure the docstring sections that agents use as context are complete. Run `docvet check` in your CI, pre-commit hooks, or agent toolchain.

## Badge

Add a badge to your project to show your docs are vetted:

```markdown
[![docs vetted | docvet](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)
```

## Used By

Are you using docvet? Open a pull request to add your project here.

## License

MIT -- see [LICENSE](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE) for details.
