# Changelog

## [1.0.0](https://github.com/Alberto-Codes/docvet/releases/tag/v1.0.0) (2026-02-21)

### Features

* **enrichment:** 10 rules detecting missing docstring sections — Raises, Yields, Receives, Warns, Other Parameters, Attributes, Typed Attributes, Examples, Cross-references, and fenced code blocks
* **freshness:** 5 rules detecting stale docstrings — signature changes (HIGH), body changes (MEDIUM), import changes (LOW), git-blame drift, and age-based staleness
* **coverage:** missing `__init__.py` detection for mkdocs discoverability
* **griffe:** 3 rules capturing griffe parser warnings for mkdocs rendering compatibility
* **reporting:** markdown and terminal output with configurable formats
* **cli:** 5 subcommands (check, enrichment, freshness, coverage, griffe) with `--staged`, `--all`, `--files`, `--format`, and `--output` options
* **integrations:** pre-commit hook and GitHub Action for CI/CD pipelines
* **config:** `[tool.docvet]` section in pyproject.toml with per-check configuration
