# docvet — Source Tree Analysis

## Project Root

```
docvet/
├── src/docvet/                    # Package source (src-layout)
│   ├── __init__.py                # Package init (docstring only)
│   └── cli.py                     # Typer CLI application (296 lines)
│
├── tests/                         # Test suite
│   ├── conftest.py                # Global fixtures (parse_source factory)
│   ├── __init__.py
│   ├── unit/                      # Unit tests (fast, isolated)
│   │   ├── __init__.py
│   │   ├── test_cli.py            # CLI tests (252 lines, 35 tests)
│   │   └── checks/               # Check-specific unit tests (empty, ready)
│   │       └── __init__.py
│   ├── integration/               # Integration tests (temp git repos)
│   │   ├── __init__.py
│   │   └── conftest.py            # git_repo fixture (tmp_path-based)
│   └── fixtures/                  # Sample .py files with known issues
│       ├── complete_module.py     # Complete docstrings (no findings expected)
│       ├── missing_raises.py      # Function missing Raises section
│       └── missing_yields.py      # Generator missing Yields section
│
├── docs/                          # Documentation
│   └── product-vision.md          # Feature specification (238 lines)
│
├── .github/                       # GitHub configuration
│   ├── workflows/
│   │   └── ci.yml                 # CI pipeline (lint, type-check, test, interrogate)
│   ├── instructions/              # Code generation instructions
│   │   ├── python.instructions.md
│   │   ├── pytest.instructions.md
│   │   └── mermaid.instructions.md
│   ├── ISSUE_TEMPLATE/            # Bug report, enhancement, feature request
│   └── PULL_REQUEST_TEMPLATE.md   # PR template (conventional commits)
│
├── .claude/                       # Claude Code configuration
│   ├── rules/                     # Development rules
│   │   ├── python.md              # Google Python style guide
│   │   ├── pytest.md              # Pytest best practices
│   │   ├── pull-requests.md       # PR creation rules
│   │   ├── pr-review-comments.md  # PR review workflow
│   │   └── mermaid.md             # Diagram guidelines
│   └── commands/                  # Agent workflow commands
│
├── _bmad/                         # BMAD agent framework (workflows)
├── _bmad-output/                  # BMAD generated artifacts
│
├── CLAUDE.md                      # Developer guidance for Claude Code
├── pyproject.toml                 # Project configuration (102 lines)
├── uv.lock                        # Locked dependencies
├── .python-version                # Python 3.12
├── .gitignore                     # VCS ignore rules
└── README.md                      # Project README (empty)
```

## Critical Directories

### src/docvet/ — Package Source

The main package directory using src-layout. Currently contains only `__init__.py` (stub) and `cli.py` (fully implemented CLI scaffold).

**Planned modules:**

| File | Purpose | Status |
|------|---------|--------|
| `__init__.py` | Package initialization | Stub |
| `cli.py` | Typer CLI entry point | Implemented |
| `config.py` | pyproject.toml reader | Planned |
| `discovery.py` | File discovery (git diff/staged/all/files) | Planned |
| `ast_utils.py` | Shared AST helpers | Planned |
| `reporting.py` | Report formatting (terminal/markdown) | Planned |
| `checks/__init__.py` | Checks package | Planned |
| `checks/enrichment.py` | Missing sections detection | Planned |
| `checks/freshness.py` | Stale docstring detection | Planned |
| `checks/coverage.py` | Missing __init__.py detection | Planned |
| `checks/griffe_compat.py` | Griffe warning capture | Planned |

### tests/ — Test Suite

Two-layer testing structure: unit tests (fast, isolated) and integration tests (temp git repos). Test fixtures provide `.py` files with known docstring issues for check validation.

**Fixture hierarchy:**
- `tests/conftest.py` — Global fixtures (available to all tests)
- `tests/integration/conftest.py` — Git-only fixtures (never in root conftest)

### .github/workflows/ — CI/CD Pipeline

Single workflow (`ci.yml`) with 4 jobs: lint (ruff), type-check (ty), test (pytest on 3.12 + 3.13 matrix), interrogate (docstring presence).

### docs/ — Documentation

Project documentation. `product-vision.md` contains the complete feature specification with six-layer model, detection rules, configuration schema, and prior art.

## Entry Points

| Entry Point | Location | Mechanism |
|-------------|----------|-----------|
| CLI | `src/docvet/cli.py:app` | `[project.scripts]` in pyproject.toml |
| Package import | `src/docvet/__init__.py` | Standard Python package |

## File Statistics

| Category | Files | Lines |
|----------|-------|-------|
| Source code | 2 | ~300 |
| Tests | 7 (+ 4 __init__.py) | ~370 |
| Configuration | 2 (pyproject.toml, .python-version) | ~105 |
| CI/CD | 1 | ~78 |
| Documentation | 2 (CLAUDE.md, product-vision.md) | ~376 |
| Dev rules | 5 (.claude/rules/) | ~500 |
| GitHub templates | 5 | ~150 |
