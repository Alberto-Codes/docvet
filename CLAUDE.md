# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**docvet** is a Python 3.12+ CLI tool for comprehensive docstring quality vetting. It fills the gap between style linting (ruff D rules) and presence checking (interrogate) by verifying docstrings are complete, accurate, and renderable for mkdocs-material + mkdocstrings workflows. Targets PyPI publication as `docvet`.

## Build & Development

Build system: **hatchling** (PEP 517/518). Entry point: `docvet = "docvet:main"` in `src/docvet/__init__.py`.

```bash
# Install in development mode
uv sync

# With optional griffe support
uv sync --extra griffe

# With dev tools (pytest, ruff, ty)
uv sync --dev

# Run the CLI
docvet check
```

## Commands

```bash
# Linting & formatting
uv run ruff check .            # Lint
uv run ruff check --fix .      # Lint with auto-fix
uv run ruff format .           # Format

# Type checking
uv run ty check

# Tests
uv run pytest                  # All tests
uv run pytest tests/unit       # Unit tests only
uv run pytest -k test_name     # Single test by name
uv run pytest -m "not slow"    # Skip slow tests
uv run pytest --cov=docvet --cov-report=term-missing  # With coverage

# CLI (installed as `docvet` console script)
docvet check                   # Run all checks on git diff files
docvet check --staged          # Run checks on staged files
docvet check --all             # Run checks on entire codebase
docvet enrichment              # Run enrichment check only
docvet freshness               # Run freshness check only
docvet coverage                # Run coverage check only
docvet griffe                  # Run griffe compatibility check only
```

## Architecture

The product vision (`docs/product-vision.md`) defines the full design. The codebase implements a **six-layer docstring quality model**, delivering layers 3-6 (layers 1-2 are handled by interrogate and ruff):

| Layer | Check | Method |
|-------|-------|--------|
| 3. Completeness | `enrichment` | AST analysis for missing sections (Raises, Yields, Attributes, Examples, etc.) |
| 4. Accuracy | `freshness` | Git diff (fast) and git blame (sweep) for stale docstrings |
| 5. Rendering | `griffe_compat` | Griffe parser warning capture for mkdocs compatibility |
| 6. Visibility | `coverage` | Missing `__init__.py` detection for mkdocs discoverability |

### Module Layout

```
src/docvet/
    __init__.py
    cli.py                # typer CLI: config loading, file discovery, check dispatch
    config.py             # reads [tool.docvet] from pyproject.toml
    discovery.py          # file discovery via git diff, git diff --cached, --all, or --files
    ast_utils.py          # shared AST helpers (docstring ranges, node walking, symbol mapping)
    reporting.py          # markdown/terminal report generation
    checks/
        __init__.py
        enrichment.py     # missing sections detection (AST-based)
        freshness.py      # git-blame drift + git-diff immediate staleness
        coverage.py       # missing __init__.py for mkdocs
        griffe_compat.py  # griffe parser warning capture
```

### Test Structure

```
tests/
    conftest.py           # Shared fixtures (source factories, AST helpers)
    unit/
        checks/           # One test file per check module
        test_ast_utils.py
        test_config.py
        test_discovery.py
    integration/
        conftest.py       # Git repo fixtures (tmp_path-based)
        test_freshness_diff.py
        test_freshness_drift.py
    fixtures/             # .py files with known docstring issues
        missing_raises.py
        missing_yields.py
        complete_module.py
```

## Key Design Decisions

- **Google-style docstrings** assumed throughout
- **No runtime deps** except typer (CLI) and optionally griffe; AST parsing and git are stdlib/system
- **Configuration** via `[tool.docvet]` in pyproject.toml with sensible defaults
- **Freshness diff mode** maps git diff hunks to AST symbols, flagging code changes without docstring updates at three severity levels (HIGH: signature change, MEDIUM: body change, LOW: imports/formatting)
- **All files use** `from __future__ import annotations`

## Code Style

- Python 3.12+, `from __future__ import annotations` at top of every file
- 88-char soft limit (formatter), 100-char hard limit (linter)
- Google-style docstrings (see `.github/instructions/python.instructions.md`)
- f-strings for formatting, %-formatting for log messages
- Type hints on all function signatures
- Two-layer testing: unit (AST + mocks) > integration (temp git repos)
- TDD encouraged: write failing test, implement, refactor
- Detailed rules in `.github/instructions/python.instructions.md` and `.github/instructions/pytest.instructions.md`

## Dependencies

Core: `typer` (CLI)

Optional: `griffe` (rendering check — `pip install docvet[griffe]`)

Dev: `pytest`, `pytest-cov`, `pytest-mock`, `pytest-randomly`, `ruff`, `ty`

## Conventional Commits

PR titles follow: `type(scope): description`

Types: feat | fix | docs | refactor | test | chore | perf

Scopes: enrichment, freshness, coverage, griffe, cli, config, discovery, ast
