---
project_name: 'docvet'
user_name: 'Alberto-Codes'
date: '2026-02-08'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow', 'critical_rules', 'ast_utilities']
status: 'complete'
rule_count: 73
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python**: >=3.12 | Build: hatchling (PEP 517/518) | Package manager: uv (always `uv run`, never raw `pip` or `python`)
- **Runtime**: typer >=0.9 (only runtime dep) | griffe >=1.0 (optional extra)
- **Testing**: pytest >=9.0 | pytest-cov >=7.0 | pytest-mock >=3.15 | pytest-randomly >=4.0 (test order randomized — no shared state between tests)
- **Quality**: ruff >=0.11 (lint + format) | ty >=0.0.1a33 (type checker) | interrogate >=1.5 (95% docstring coverage threshold)
- **CI gates**: ruff check, ruff format --check, ty check, pytest --cov-fail-under=85, interrogate -v
- **Typer caveats**: Use `list[str]` for repeated options (never `list[Path]` — breaks across versions). `CliRunner` does not support `mix_stderr` in current version. Entry point is `docvet.cli:app` (no `__main__.py`)
- **enum.StrEnum**: Used for CLI-facing enums (Python 3.11+ stdlib). Plain `enum.Enum` for internal-only enums

## Critical Implementation Rules

### Python Language Rules

- **Every file** starts with `from __future__ import annotations` — no exceptions
- **Type hints**: Modern syntax only — `list[str]` not `List[str]`, `X | None` not `Optional[X]`, never import `Optional`
- **Import order**: `__future__` → stdlib → third-party → local (enforced by ruff isort). Full package paths only — no relative imports
- **Strings**: f-strings for formatting, `%`-formatting for logger calls only
- **Line limits**: 88 chars soft (formatter), 100 chars hard (linter)
- **No mutable defaults**: Never use `[]` or `{}` as function default arguments
- **Docstrings**: Google-style on all public functions/classes. Sections: Args, Returns, Raises, Yields. One-line summary ends with period, max 80 chars. Do NOT add docstrings to test functions (suppressed by ruff per-file-ignores)
- **Private functions**: `_leading_underscore` prefix for internal helpers
- **Constants**: `ALL_CAPS_WITH_UNDER` at module level
- **No bare exceptions**: Always catch specific exception types, include context in error messages
- **No new runtime deps**: typer is the only runtime dependency. Use stdlib for everything else unless explicitly approved
- **No `assert` in production code**: `assert` is suppressed (S101) only in tests. Production code must use proper error handling
- **Annotated aliases**: Shared CLI options use `Annotated` type aliases at module level — don't inline `typer.Option()` in function signatures

### Framework Rules (Typer CLI)

- **App structure**: Single `typer.Typer()` app with top-level `@app.command()` — no nested sub-apps
- **Global options**: Defined in `@app.callback(invoke_without_command=True)`. Stored in `ctx.ensure_object(dict)` / `ctx.obj["key"]`. Global options must precede the subcommand: `docvet --verbose check`, NOT `docvet check --verbose`
- **ctx.obj values are raw types**: `ctx.obj["format"]` is a `str` (not `OutputFormat` enum), `ctx.obj["output"]` is a `str` (not `Path`). Compare with string literals, not enum members
- **Discovery flags**: `--staged`, `--all`, `--files` are mutually exclusive, enforced via `_resolve_discovery_mode()` helper raising `typer.BadParameter`. Every subcommand with discovery flags must call this — no exceptions
- **Let BadParameter bubble**: Never catch `typer.BadParameter` in subcommands — typer handles rendering and exit codes
- **Repeated flags**: `--files foo.py --files bar.py` (repeated per value), NOT `--files foo.py bar.py` (space-separated)
- **Stub pattern**: Unimplemented checks print `"<name>: not yet implemented"` — lowercase, colon-separated. Private `_run_*` functions form the internal API boundary
- **Subcommand help**: Typer picks up docstring first line as help text — do not duplicate with explicit `help=` parameter
- **No `__main__.py`**: Entry point wires directly to `docvet.cli:app` via `[project.scripts]`
- **Migration paths**: `_run_*` stubs in `cli.py` will be replaced by imports from `checks/<name>.py`. `DiscoveryMode` enum lives in `discovery.py` (migrated from `cli.py`). `discover_files()` accepts `DocvetConfig` and `DiscoveryMode`, returns `list[Path]`

### Testing Rules

- **Structure**: `tests/unit/` mirrors `src/docvet/` layout. `tests/integration/` for git-dependent tests. `tests/fixtures/` for sample `.py` files with known docstring issues
- **Naming**: `test_<what>_<condition>_<expected_result>` — maps directly to acceptance criteria. Every AC should trace to at least one test
- **One assert per test**: Recommended. Multiple related asserts acceptable if testing a single logical behavior
- **Self-contained tests**: `pytest-randomly` randomizes order — never depend on test execution order or shared mutable state between tests
- **Fixtures**: Factory pattern in `conftest.py` (e.g., `parse_source` returns a callable). No fixture imports — pytest auto-discovers. Global fixtures in `tests/conftest.py`, integration-only fixtures in `tests/integration/conftest.py` — never mix them
- **AST tests**: Prefer source string fixtures over mocking AST nodes. Use `parse_source` factory or files in `tests/fixtures/`. Mocking AST leads to brittle tests
- **CLI tests**: Use `typer.testing.CliRunner()` (no kwargs). Assert on `result.exit_code` and `result.output`. No filesystem or git in unit tests
- **Mocking**: Patch where object is USED, not where DEFINED — `mocker.patch("docvet.checks.freshness.subprocess.run")` not `mocker.patch("subprocess.run")`
- **Integration tests**: Use `tmp_path` fixture for temp git repos. Real `git init` + `git commit` — no mocking git in integration tests
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`. All markers must be registered in `pyproject.toml` (`--strict-markers` is on — unregistered markers cause errors, not warnings)
- **No docstrings on tests**: Ruff D rules are suppressed for `tests/**/*.py`
- **Coverage**: CI enforces `--cov-fail-under=85`. Run locally with `uv run pytest --cov=docvet --cov-report=term-missing`
- **TDD encouraged**: Write failing test first, implement, refactor

### Code Quality & Style

- **Ruff enforces**: `E501` (line length), `I` (import sorting), `D` (docstrings — Google convention)
- **isort config**: `known-first-party = ["docvet"]` — if adding new packages, update this list
- **Quote style**: Double quotes only (enforced by ruff formatter)
- **Docstring code formatting**: Enabled (`docstring-code-format = true`) — ruff reformats code inside docstring `Examples:` sections. Always run `ruff format` after writing docstrings with code blocks
- **Docstring summary line**: Max 80 chars (stricter than the 88-char line limit). `@property` uses attribute-style: `"The table path."` not `"Returns the table path."`. Generators use `Yields:` not `Returns:`
- **File organization**: `src/docvet/` layout — `cli.py` (entry), `config.py`, `discovery.py`, `ast_utils.py`, `reporting.py`, `checks/*.py`
- **Module docstrings**: Required on all modules (interrogate enforces 95% threshold). Exception: test files (excluded from interrogate and ruff D rules)
- **Naming**: Files are `snake_case.py`. Classes `PascalCase`. Functions/vars `snake_case`. Test files `test_<module>.py`
- **Six-layer model**: docvet implements layers 3-6 only. Layers 1-2 (presence + style) are handled by interrogate and ruff. Do not re-implement presence or style checking

### Development Workflow

- **Branching**: `feat/<issue>-<slug>` or `fix/<issue>-<slug>`. Slug must match tech spec's `slug` field when one exists. Example: `feat/4-cli-scaffold` for `slug: '4-cli-scaffold'`
- **Commits**: Conventional commits — `type(scope): description`. Types: `feat | fix | docs | refactor | test | chore | perf`. Scope is a codebase noun (enrichment, freshness, cli, config, etc.), never an issue number. Breaking changes add `!` after scope
- **PRs**: Always draft (`--draft`) — ready PRs trigger Copilot automated review. Target `develop` branch (never `main` — that's for releases only). Follow `.github/PULL_REQUEST_TEMPLATE.md` exactly. Title follows conventional commits
- **PR body**: Why paragraph → What changed (2-4 bullets, imperative mood) → `Test:` line → `Closes #` trailer → multi-commit footer blocks if needed → `## PR Review` section
- **Before PR**: Run `git diff develop..HEAD` and `git log --oneline develop..HEAD` to understand ALL commits — PR description must cover the full scope, not just the latest commit. Push with `git push -u origin <branch>` (the `-u` sets upstream tracking)
- **Quality before PR**: Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `uv run pytest` locally
- **CI**: Runs on PR and push to develop/main. Gates: lint, format, type-check, test (py3.12 + py3.13), interrogate

### AST Utilities Rules (`ast_utils.py`)

- **`Symbol` dataclass** is `frozen=True` with fields: `name`, `kind`, `line`, `end_line`, `definition_start`, `docstring`, `docstring_range`, `signature_range`, `body_range`, `parent`
- **`line`** = `node.lineno` (keyword line, not decorator). **`definition_start`** = first decorator line or `node.lineno`
- **`signature_range`** is `None` for classes and modules — only set for functions/methods
- **Module symbol** uses `name="<module>"`, `line=1`, `definition_start=1`
- **`body_range`** excludes docstring. `start >= end` means effectively empty body
- **`get_documented_symbols`** returns a flat list, not a tree. `parent` = enclosing class name only (not functions)
- **`map_lines_to_symbols`** returns the innermost symbol. Uses `definition_start` through `end_line`
- **Caller handles `SyntaxError`** — `ast_utils` assumes valid AST from `ast.parse()`
- **`Module` lacks `end_lineno`** in Python 3.12+ — `_node_end_line()` derives it from the last body statement
- **Never mock AST nodes** — use source strings with `parse_source` fixture or fixture files with `Path.read_text()` + `parse_source`
- **`Symbol.kind`** is `Literal["function", "class", "method", "module"]` — no lambda, comprehension, or import nodes

### Critical Don't-Miss Rules

- **Never add `__main__.py`**: Entry point is `[project.scripts]` → `docvet.cli:app`. No indirection layer
- **Never use `List`, `Dict`, `Optional` from typing**: Use `list`, `dict`, `X | None` with `from __future__ import annotations`
- **Never mock AST nodes**: Use source strings with `ast.parse()` for enrichment/freshness tests
- **Never put integration fixtures in root conftest**: `tests/conftest.py` = global, `tests/integration/conftest.py` = git-only
- **Never add runtime deps without approval**: stdlib + typer only. griffe is optional extra
- **Never target `main` for PRs**: Always `develop`
- **Never create ready PRs**: Always `--draft`
- **Never use space-separated `--files`**: Must be `--files a.py --files b.py`
- **Never skip `_resolve_discovery_mode()`**: Every subcommand with discovery flags must call it
- **Google-style docstrings assumed**: The entire tool assumes Google-style. Do not add support for numpy/sphinx style
- **Checks are isolated**: enrichment, freshness, coverage, griffe share no state and must not import from each other. Each must work standalone via `docvet <check>`
- **Git via subprocess only**: Never import gitpython or git libraries. Use `subprocess.run` with `git` commands. Handle non-git directories gracefully (clear error, no traceback)
- **`[tool.docvet]` may not exist**: Config reads from `pyproject.toml`. Missing section = use defaults, not error
- **Reproduce random test failures**: Use `pytest -p randomly --randomly-seed=XXXXX` with the seed from CI output
- **Validate pytest config**: Run `uv run pytest --co` (collect-only) after changing `pyproject.toml` pytest options — `--strict-config` will error on unrecognized options

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-08
