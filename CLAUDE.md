# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**docvet** is a Python 3.12+ CLI tool for comprehensive docstring quality vetting. It fills the gap between style linting (ruff D rules) and presence checking (interrogate) by verifying docstrings are complete, accurate, and renderable for mkdocs-material + mkdocstrings workflows. Targets PyPI publication as `docvet`.

## Build & Development

Build system: **uv_build** (PEP 517/518). Entry point: `docvet = "docvet:main"` in `src/docvet/__init__.py`. Published to PyPI as `docvet` v1.0.0.

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
uv run pytest tests/unit       # Unit tests only (by directory)
uv run pytest -m unit           # Unit tests only (by marker)
uv run pytest -m integration    # Integration tests only (by marker)
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

### Key Modules

- **`cli.py`** — typer CLI: config loading, file discovery, check dispatch, unified output pipeline (`_output_and_exit`)
- **`config.py`** — reads `[tool.docvet]` from pyproject.toml
- **`discovery.py`** — file discovery via git diff, git diff --cached, --all, positional args, or --files
- **`ast_utils.py`** — shared AST helpers (docstring ranges, node walking, symbol mapping)
- **`reporting.py`** — markdown/terminal/JSON report generation
- **`lsp.py`** — LSP server for real-time editor diagnostics
- **`checks/`** — one module per check layer (enrichment, freshness, coverage, griffe_compat)

### Test Conventions

- Two-layer structure: `tests/unit/` (AST + mocks) and `tests/integration/` (temp git repos)
- Tests are generally organized one file per source module; larger or cross-cutting areas (e.g., the CLI) may use multiple focused test files. Check tests live in `tests/unit/checks/`.
- Fixtures in `tests/fixtures/` — .py files with known docstring issues
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

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

## Branching & Release

- **`main`**: Single default branch — all feature PRs squash-merge here
- **Feature branches**: `feat/<scope>-<description>`, squash-merged to main via PR
- **release-please**: `googleapis/release-please-action@v4` on push to `main`. Config in `release-please-config.json`. Manifest in `.release-please-manifest.json`.
- **Publishing**: OIDC trusted publishing to PyPI (no API tokens). Triggered by `release: [published]` event.
- **Floating tag**: `v1` tag updated on each release for GitHub Action consumers.

## CI/CD Pipeline Lessons

Hard-won lessons from the v1.0.0 launch — reference these when modifying workflows:

- **OIDC token exchange**: Use `uv publish --index testpypi`, NOT `--publish-url`. The `--publish-url` flag only sets the upload endpoint but mints the OIDC token against PyPI (wrong audience for TestPyPI), causing 503 errors.
- **TestPyPI index config**: `uv publish --index` requires the index to be defined in `pyproject.toml` with `publish-url`. Without it, uv doesn't know where to upload.
- **Explicit permissions**: When declaring `permissions:` in a workflow, all unmentioned permissions default to `none`. Always include `contents: read` alongside `id-token: write` or checkout will fail.
- **attest-action version**: `astral-sh/attest-action@v1` does not exist. Pin to a specific version (currently `@v0.0.4`).

## Conventional Commits

PR titles follow: `type(scope): description`

Types: feat | fix | docs | refactor | test | chore | perf

Scopes: enrichment, freshness, coverage, griffe, cli, config, discovery, ast, docs
