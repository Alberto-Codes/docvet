# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**docvet** is a Python 3.12+ CLI tool for comprehensive docstring quality vetting. It fills the gap between style linting (ruff D rules) and presence checking (interrogate) by verifying docstrings are complete, accurate, and renderable for mkdocs-material + mkdocstrings workflows. Targets PyPI publication as `docvet`.

## Build & Development

Build system: **hatchling** (PEP 517/518). Entry point: `docvet = "docvet:main"` in `src/docvet/__init__.py`.

```bash
# Install in development mode
pip install -e .

# With optional griffe support
pip install -e ".[griffe]"

# Run the CLI
docvet check
```

Testing and linting tooling are not yet configured. When added, they will likely use pytest and ruff based on the project's conventions.

## Architecture

The product vision (`docs/product-vision.md`) defines the full design. The codebase implements a **six-layer docstring quality model**, delivering layers 3-6 (layers 1-2 are handled by interrogate and ruff):

| Layer | Check | Method |
|-------|-------|--------|
| 3. Completeness | `enrichment` | AST analysis for missing sections (Raises, Yields, Attributes, Examples, etc.) |
| 4. Accuracy | `freshness` | Git diff (fast) and git blame (sweep) for stale docstrings |
| 5. Rendering | `griffe_compat` | Griffe parser warning capture for mkdocs compatibility |
| 6. Visibility | `coverage` | Missing `__init__.py` detection for mkdocs discoverability |

Planned module layout under `src/docvet/`:
- `cli.py` — typer-based CLI entry points
- `config.py` — reads `[tool.docvet]` from pyproject.toml
- `discovery.py` — file discovery via git diff, git diff --cached, --all, or --files
- `ast_utils.py` — shared AST helpers (docstring ranges, node walking, symbol mapping)
- `reporting.py` — markdown/terminal report generation
- `checks/` — one module per check (enrichment, freshness, coverage, griffe_compat)

## Key Design Decisions

- **Google-style docstrings** assumed throughout
- **No runtime deps** except typer (CLI) and optionally griffe; AST parsing and git are stdlib/system
- **Configuration** via `[tool.docvet]` in pyproject.toml with sensible defaults
- **Freshness diff mode** maps git diff hunks to AST symbols, flagging code changes without docstring updates at three severity levels (HIGH: signature change, MEDIUM: body change, LOW: imports/formatting)
- **All files use** `from __future__ import annotations`
