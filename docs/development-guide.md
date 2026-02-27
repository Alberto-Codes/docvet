# docvet — Development Guide

## Prerequisites

- **Python:** >= 3.12
- **uv:** Latest version ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **git:** For freshness checks and development workflow

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd docvet

# Install in development mode with all dev dependencies
uv sync --dev

# With optional griffe support
uv sync --dev --extra griffe

# Verify installation
uv run docvet --help
```

## Running the CLI

```bash
# Run all checks on git diff files (default)
uv run docvet check

# Run on staged files
uv run docvet check --staged

# Run on entire codebase
uv run docvet check --all

# Run on specific files
uv run docvet check foo.py bar.py

# Run individual checks
uv run docvet enrichment
uv run docvet freshness
uv run docvet freshness --mode drift
uv run docvet coverage
uv run docvet griffe

# Global options (must precede subcommand)
uv run docvet --verbose check
uv run docvet --format markdown check
uv run docvet --output report.md check
```

## Quality Gates

All gates must pass before creating a PR:

```bash
# Linting
uv run ruff check .

# Format check
uv run ruff format --check .

# Type checking
uv run ty check

# Tests with coverage
uv run pytest --cov=docvet --cov-report=term-missing --cov-fail-under=85

# Docstring presence (95% threshold)
uv run interrogate -v .

# Auto-fix linting issues
uv run ruff check --fix .

# Auto-format
uv run ruff format .
```

## Testing

### Run Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit

# Integration tests only
uv run pytest tests/integration

# Single test by name
uv run pytest -k test_check_when_invoked_with_no_flags_exits_successfully

# Skip slow tests
uv run pytest -m "not slow"

# With coverage report
uv run pytest --cov=docvet --cov-report=term-missing

# Reproduce random test failure
uv run pytest -p randomly --randomly-seed=XXXXX
```

### Test Organization

- `tests/unit/` mirrors `src/docvet/` layout
- `tests/integration/` for git-dependent tests
- `tests/fixtures/` for sample `.py` files with known docstring issues

### Test Naming Convention

```
test_<what>_<condition>_<expected_result>
```

Examples:
- `test_check_when_invoked_with_no_flags_exits_successfully`
- `test_enrichment_when_invoked_with_staged_and_all_fails_with_error`

### Writing Tests

- One assert per test (recommended)
- Self-contained: `pytest-randomly` randomizes order
- CLI tests: use `typer.testing.CliRunner()` (no kwargs)
- AST tests: prefer source string fixtures over mocking AST nodes
- Mocking: patch where object is USED, not where DEFINED
- No docstrings on test functions (ruff D rules suppressed for tests)
- All markers must be registered in `pyproject.toml` (`--strict-markers`)

### Fixtures

- **Factory pattern:** `parse_source` in `tests/conftest.py` returns a callable
- **Global fixtures:** `tests/conftest.py` (available to all tests)
- **Integration fixtures:** `tests/integration/conftest.py` (git-only, never in root conftest)
- **File fixtures:** `tests/fixtures/*.py` (known docstring issues)

## Code Style

### Required in Every File

```python
from __future__ import annotations
```

### Import Order

1. `from __future__ import annotations`
2. Python stdlib
3. Third-party packages
4. Local application (`from docvet.xxx import ...`)

### Type Hints

- Modern syntax: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- Never import `Optional` from typing
- All function signatures must have type hints

### Strings

- f-strings for formatting
- `%`-formatting for logger calls only

### Docstrings

- Google-style on all public functions/classes
- Sections: Args, Returns, Raises, Yields, Examples
- One-line summary max 80 chars, ends with period
- No docstrings on test functions

### Line Length

- 88 chars soft limit (formatter)
- 100 chars hard limit (linter)

## Git Workflow

### Branching

```
feat/<issue>-<slug>    # New features
fix/<issue>-<slug>     # Bug fixes
```

### Commits

Conventional commits: `type(scope): description`

- **Types:** feat, fix, docs, refactor, test, chore, perf
- **Scopes:** enrichment, freshness, coverage, griffe, cli, config, discovery, ast

### Pull Requests

- Always create as **draft** (`--draft`)
- Target `main` branch
- Title follows conventional commits
- Run `git diff main..HEAD` and `git log --oneline main..HEAD` before writing PR body
- Push with `git push -u origin <branch>` before creating PR

## CI Pipeline

GitHub Actions runs on PRs and pushes to main:

| Job | What It Does |
|-----|-------------|
| lint | `ruff check .` + `ruff format --check .` |
| type-check | `ty check` |
| test | `pytest --cov-fail-under=85` on Python 3.12 + 3.13 |
| interrogate | `interrogate -v .` (95% docstring coverage) |

## Key Constraints

- **Never add runtime dependencies** beyond typer without approval
- **Never use `__main__.py`** — entry point is `[project.scripts]` -> `docvet.cli:app`
- **Never use relative imports** — full package paths only
- **Never mock AST nodes** — use source strings with `ast.parse()`
- **Never put integration fixtures in root conftest**
- **Always target `main` for PRs** — single-branch workflow
