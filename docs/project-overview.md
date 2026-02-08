# docvet — Project Overview

## Purpose

**docvet** is a Python 3.12+ CLI tool for comprehensive docstring quality vetting. It fills the gap between style linting (ruff D rules) and presence checking (interrogate) by verifying that docstrings are complete, accurate, and renderable for mkdocs-material + mkdocstrings workflows.

Target: PyPI publication as `docvet`.

## Six-Layer Docstring Quality Model

| Layer | Tool | What It Catches |
|-------|------|-----------------|
| 1. Presence | interrogate | "Does a docstring exist?" |
| 2. Style | ruff D rules | "Is it Google-style formatted?" |
| **3. Completeness** | **docvet enrichment** | "Does it have all required sections?" |
| **4. Accuracy** | **docvet freshness** | "Does it match the current code?" |
| **5. Rendering** | **docvet griffe** | "Will mkdocs render it correctly?" |
| **6. Visibility** | **docvet coverage** | "Will mkdocs even see the file?" |

Layers 1-2 are handled by existing tools. docvet delivers layers 3-6.

## Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | >= 3.12 |
| CLI Framework | typer | >= 0.9 |
| Build System | hatchling | PEP 517/518 |
| Package Manager | uv | latest |
| Linter/Formatter | ruff | >= 0.11 |
| Type Checker | ty | >= 0.0.1a33 |
| Docstring Coverage | interrogate | >= 1.5 |
| Testing | pytest | >= 9.0 |
| Optional | griffe | >= 1.0 (rendering check) |

## Repository Structure

- **Type:** Monolith (single Python package)
- **Architecture:** CLI tool with modular check pipeline
- **Entry Point:** `docvet.cli:app` (typer application)
- **Package Layout:** `src/docvet/` (src-layout)

## The Four Checks

1. **Enrichment** — AST-based detection of missing docstring sections (Raises, Yields, Attributes, Examples, etc.)
2. **Freshness** — Git diff (fast) and git blame (sweep) for stale docstrings with severity levels
3. **Coverage** — Missing `__init__.py` detection for mkdocs discoverability
4. **Griffe** — Griffe parser warning capture for mkdocs rendering compatibility

## Current Status

- **Version:** 0.1.0 (early development)
- **Implemented:** CLI scaffold with 5 subcommands, global options, discovery flags, mutual exclusivity validation
- **Pending:** config.py, discovery.py, ast_utils.py, reporting.py, and all four check modules

## Links

- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [Product Vision](./product-vision.md)
