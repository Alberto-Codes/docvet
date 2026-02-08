# docvet — Documentation Index

## Project Overview

- **Type:** Monolith (single Python package)
- **Primary Language:** Python 3.12+
- **Framework:** Typer CLI
- **Architecture:** Pipeline (CLI -> Discovery -> Checks -> Reporting)
- **Build System:** hatchling (PEP 517/518)
- **Package Manager:** uv

## Quick Reference

- **Entry Point:** `docvet.cli:app`
- **Install:** `uv sync --dev`
- **Run:** `uv run docvet check`
- **Test:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Type Check:** `uv run ty check`

## Generated Documentation

- [Project Overview](./project-overview.md) — Purpose, tech stack, status
- [Architecture](./architecture.md) — Module descriptions, data flow, design decisions
- [Source Tree Analysis](./source-tree-analysis.md) — Annotated directory tree, file statistics
- [Development Guide](./development-guide.md) — Setup, commands, testing, code style, workflow

## Existing Documentation

- [Product Vision](./product-vision.md) — Feature specification with six-layer quality model, detection rules, configuration schema
- [CLAUDE.md](../CLAUDE.md) — Developer guidance for Claude Code agents

## Getting Started

1. Install dependencies: `uv sync --dev`
2. Run the CLI: `uv run docvet check`
3. Run tests: `uv run pytest`
4. Read the [Development Guide](./development-guide.md) for coding conventions
5. Read the [Architecture](./architecture.md) for module overview
6. Read the [Product Vision](./product-vision.md) for feature specification
