# Contributing to docvet

Thanks for your interest in contributing to docvet! This guide covers everything you need to get started. Browse the [documentation site](https://alberto-codes.github.io/docvet/) for detailed references, or see the [Development Guide](docs/development-guide.md) for full coding conventions.

## Reporting Issues

Use the issue templates on the [Issues page](https://github.com/Alberto-Codes/docvet/issues):

- **Bug Report** -- reproduce steps, environment info, and logs
- **Feature Request** -- problem statement, proposed solution, acceptance criteria
- **Enhancement** -- improvements to existing functionality

## Prerequisites

- **Python** >= 3.12
- **uv** -- [install guide](https://docs.astral.sh/uv/getting-started/installation/)
- **git**
- **pre-commit** -- [install guide](https://pre-commit.com/#install)

## Fork and Clone

```bash
# 1. Fork the repo on GitHub (click "Fork" button)
# 2. Clone your fork
git clone https://github.com/<your-username>/docvet.git
cd docvet

# 3. Add the upstream remote
git remote add upstream https://github.com/Alberto-Codes/docvet.git

# 4. Create a feature branch
git checkout -b feat/<scope>-<description>
```

## Development Setup

```bash
# Install in development mode with all dev dependencies
uv sync --dev

# With optional griffe support
uv sync --dev --extra griffe

# Verify installation
uv run docvet --help
```

## Pre-Commit Hooks

docvet uses pre-commit hooks to catch issues before they reach CI. Pre-commit is not a project dependency -- if you don't have it yet, see the [install guide](https://pre-commit.com/#install). Then activate the hooks:

```bash
pre-commit install
```

Seven hooks run automatically on each commit:

| Hook | What it checks |
|------|---------------|
| yamllint | YAML syntax and formatting |
| actionlint | GitHub Actions workflow validity |
| ruff-check | Python linting |
| ruff-format | Python code formatting |
| ty | Type checking |
| pytest | Full test suite |
| docvet | Docstring quality on staged files |

All hooks must pass before the commit succeeds. The docvet hook runs `docvet check --staged` with all four checks enforced, so docvet dogfoods itself on every commit.

## Quality Gates

All six gates must pass before opening a PR. Run them locally:

```bash
uv run ruff check .                  # Linting
uv run ruff format --check .         # Format check
uv run ty check                      # Type checking
uv run pytest                        # Tests (CI enforces 85% coverage)
uv run docvet check --all            # Docstring quality (all 4 checks)
uv run interrogate -v .              # Docstring presence (95% threshold)
```

To auto-fix linting and formatting issues:

```bash
uv run ruff check --fix .
uv run ruff format .
```

## Coding Standards

- `from __future__ import annotations` at the top of every file
- Google-style docstrings on all public functions and classes
- Type hints on all function signatures (`list[str]`, not `List[str]`)
- 88-char soft limit (formatter), 100-char hard limit (linter)

See the [Development Guide](docs/development-guide.md#code-style) for the full style reference.

## Testing

```bash
uv run pytest                  # All tests
uv run pytest tests/unit       # Unit tests only
uv run pytest tests/integration # Integration tests only
uv run pytest -k test_name     # Single test by name
```

Test naming convention: `test_<what>_<condition>_<expected_result>`

See the [Development Guide](docs/development-guide.md#testing) for test organization, fixtures, markers, and writing guidelines.

## Commit Conventions

Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description
```

| Type | Purpose |
|------|---------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation only |
| refactor | Code restructuring |
| test | Adding or updating tests |
| chore | Maintenance tasks |
| perf | Performance improvements |

**Scopes:** enrichment, freshness, coverage, griffe, cli, config, discovery, ast

Do not add `Co-Authored-By` trailers to commits.

## Pull Request Process

1. Push your branch to your fork: `git push -u origin feat/<scope>-<description>`
2. Open a **draft** PR against `upstream/main` (non-draft PRs trigger automated review prematurely)
3. Fill out the [PR template](.github/PULL_REQUEST_TEMPLATE.md) -- remove HTML comments, keep visible content
4. PR title must follow conventional commits format: `type(scope): description`
5. All CI checks must pass before review
6. PRs are squash-merged to keep a linear history

## CI Pipeline

GitHub Actions runs these checks on every PR:

| Job | What it checks |
|-----|---------------|
| lint | `ruff check` + `ruff format --check` |
| type-check | `ty check` |
| test | `pytest` on Python 3.12 + 3.13 (85% coverage) |
| interrogate | Docstring presence (95% threshold) |
| docvet | `docvet check --all` (all 4 checks) |
| CodeQL | Static security analysis |

## Key Constraints

- Never add runtime dependencies beyond `typer` without maintainer approval
- Never use relative imports (full package paths only)
- Never use `__main__.py` (entry point is `[project.scripts]`)
- Never mock AST nodes in tests (use source strings with `ast.parse()`)
- Never put integration fixtures in the root `conftest.py`
- Always target `main` for PRs (single-branch workflow)
