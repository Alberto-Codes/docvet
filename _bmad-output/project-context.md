---
project_name: 'docvet'
user_name: 'Alberto-Codes'
date: '2026-03-08'
sections_completed: ['technology_stack', 'framework_rules', 'ast_utilities', 'domain_patterns', 'critical_rules']
status: 'complete'
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains domain-specific implementation patterns and non-obvious rules that AI agents must follow. Style rules (imports, formatting, naming, line length, quotes) are enforced by ruff and ty — see `.claude/rules/python.md` for semantic rules not covered by tooling._

---

## Technology Stack & Versions

- **Python**: >=3.12 | Build: uv_build (PEP 517/518) | Package manager: uv (always `uv run`, never raw `pip` or `python`)
- **Runtime**: typer >=0.9 (only runtime dep) | griffe >=1.0 (optional extra)
- **Testing**: pytest >=9.0 | pytest-cov >=7.0 | pytest-mock >=3.15 | pytest-randomly >=4.0 (test order randomized — no shared state between tests)
- **Quality**: ruff >=0.11 (lint + format) | ty >=0.0.1a33 (type checker) | docvet check --all (full-strength dogfooding)
- **CI gates**: ruff check, ruff format --check, ty check, pytest --cov-fail-under=85, docvet check --all
- **Typer caveats**: Use `list[str]` for repeated options (never `list[Path]` — breaks across versions). `CliRunner` does not support `mix_stderr` in current version. Entry point is `docvet.cli:app` (no `__main__.py`)
- **enum.StrEnum**: Used for CLI-facing enums (Python 3.11+ stdlib). Plain `enum.Enum` for internal-only enums

## Framework Rules (Typer CLI)

- **App structure**: Single `typer.Typer()` app with top-level `@app.command()` — no nested sub-apps
- **Global options**: Defined in `@app.callback(invoke_without_command=True)`. Stored in `ctx.ensure_object(dict)` / `ctx.obj["key"]`. Global options must precede the subcommand: `docvet --verbose check`, NOT `docvet check --verbose`
- **ctx.obj values are raw types**: `ctx.obj["format"]` is a `str` (not `OutputFormat` enum), `ctx.obj["output"]` is a `str` (not `Path`). `ctx.obj["docvet_config"]` is a `DocvetConfig` instance. Compare with string literals, not enum members
- **Discovery flags**: `--staged`, `--all`, `--files` are mutually exclusive, enforced via `_resolve_discovery_mode()` helper raising `typer.BadParameter`. Every subcommand with discovery flags must call this — no exceptions
- **Let BadParameter bubble**: Never catch `typer.BadParameter` in subcommands — typer handles rendering and exit codes
- **Repeated flags**: `--files foo.py --files bar.py` (repeated per value), NOT `--files foo.py bar.py` (space-separated)
- **Subcommand help**: Typer picks up docstring first line as help text — do not duplicate with explicit `help=` parameter
- **No `__main__.py`**: Entry point wires directly to `docvet.cli:app` via `[project.scripts]`
- **Annotated aliases**: Shared CLI options use `Annotated` type aliases at module level — don't inline `typer.Option()` in function signatures

## AST Utilities Rules (`ast_utils.py`)

- **`Symbol` dataclass** is `frozen=True` with fields: `name`, `kind`, `line`, `end_line`, `definition_start`, `docstring`, `docstring_range`, `signature_range`, `body_range`, `parent`
- **`line`** = `node.lineno` (keyword line, not decorator). **`definition_start`** = first decorator line or `node.lineno`
- **`signature_range`** is `None` for classes and modules — only set for functions/methods
- **Module symbol** uses `name="<module>"`, `line=1`, `definition_start=1`
- **`body_range`** excludes docstring. `start >= end` means effectively empty body
- **`get_documented_symbols`** returns a flat list, not a tree. `parent` = enclosing class name only (not functions)
- **`map_lines_to_symbols`** returns the innermost symbol. Uses `definition_start` through `end_line`
- **Caller handles `SyntaxError`** — `ast_utils` assumes valid AST from `ast.parse()`
- **`Module` lacks `end_lineno`** in Python 3.12+ — `_node_end_line()` derives it from the last body statement
- **`Symbol.kind`** is `Literal["function", "class", "method", "module"]` — no lambda, comprehension, or import nodes

---

## Domain Implementation Patterns

_These patterns address the most common source of bugs in this codebase — correct implementations of incorrect assumptions. Every pattern below was learned from a real bug._

### AST Patterns

- **`node.body` includes the docstring node.** The first element of a function/class body is `Expr(Constant(str))` when a docstring exists. `len(node.body) == 1` means "only a docstring" for documented functions but "one real statement" for undocumented ones. Use `ast.get_docstring(node)` to check for docstring presence, then count non-docstring body elements: `len(node.body) - (1 if ast.get_docstring(node) else 0)`
- **Scope-aware walking vs `ast.walk()`.** `ast.walk()` traverses the entire subtree including nested functions and classes. For body-level inspection (e.g., finding `raise` or `yield` statements), use iterative scope-aware walking that stops at nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef` boundaries
- **Decorator detection requires two forms.** `@overload` is `ast.Name(id="overload")`, but `@typing.overload` is `ast.Attribute(attr="overload")`. Always check both `Name` and `Attribute` forms via a helper like `_has_decorator()`
- **`definition_start` vs `line`.** `definition_start` includes decorators (first `@decorator` line). `line` is the `def`/`class` keyword line. Use `definition_start` for range calculations, `line` for user-facing messages

### Regex Patterns

- **`\s` matches `\n`.** Patterns using `\s` for "some spaces" will also match newlines, causing cross-line matches. Use `[^\S\n]` (or `[ \t]`) for horizontal-only whitespace. This is especially critical for section header patterns where `\s*` between a colon and end-of-line would match into the next line
- **Sort regex alternatives by length descending.** In alternation patterns like `(Raises|Returns|Other Parameters)`, longer alternatives must come first to prevent partial matches. `"Other Parameters"` must precede `"Other"` if both are valid
- **Google vs Sphinx parsing strategies differ.** Google-style uses `SectionName:` headers. Sphinx/RST uses `:directive param:` inline markup. NumPy uses `SectionName\n---------` underline patterns. Each requires its own regex strategy — do not mix parsing approaches

### Cross-Rule Interactions

- **Verify no impossible states when adding rules to existing modules.** Example: `missing-docstring` (presence) says "@overload needs a docstring" while `overload-has-docstring` (presence) says "@overload should NOT have a docstring" — these directly conflict. When adding a rule, check all existing rules in the same module for overlapping symbol sets
- **Presence skip propagation.** If a check is skipped (e.g., `--no-presence`), all downstream consumers must respect the skip: stats, summary percentages, reports, `check_counts`, exit codes. A skipped check must not contribute phantom metrics
- **Enrichment dispatch table pattern.** `_RULE_DISPATCH` maps rule names to `_check_*` functions. Adding a new rule requires: (1) the `_check_*` function, (2) an entry in `_RULE_DISPATCH`, (3) a config key if the rule is optional. Config gating happens in the orchestrator, NOT in `_check_*` functions
- **Style awareness affects rule applicability.** Some enrichment rules only apply to certain docstring styles (Google, Sphinx, NumPy). The `_user_set_keys` mechanism distinguishes "user explicitly enabled this" from "default was on" — explicit user choice beats auto-disable

### CLI Skip Propagation

- **When a check is conditionally skipped, propagate to ALL downstream paths.** This includes: `_output_and_exit()` stats dictionary, `--summary` percentage calculations, JSON output fields, markdown/terminal report sections, `check_counts` for the timing display, and the exit code logic. Missing any one path creates phantom output for skipped checks

---

## Critical Don't-Miss Rules

- **Never add `__main__.py`**: Entry point is `[project.scripts]` → `docvet.cli:app`. No indirection layer
- **Never mock AST nodes**: Use source strings with `ast.parse()` for enrichment/freshness tests
- **Never put integration fixtures in root conftest**: `tests/conftest.py` = global, `tests/integration/conftest.py` = git-only
- **Never add runtime deps without approval**: stdlib + typer only. griffe is optional extra
- **Never create ready PRs**: Always `--draft`. PRs target `main` (trunk-based flow)
- **Never use space-separated `--files`**: Must be `--files a.py --files b.py`
- **Never skip `_resolve_discovery_mode()`**: Every subcommand with discovery flags must call it
- **Multi-style docstrings**: docvet supports Google (default), Sphinx/RST, and NumPy styles. Style auto-detection runs per-file. Some enrichment rules auto-disable for non-Google styles via `_SPHINX_AUTO_DISABLE_RULES`
- **Checks are isolated**: enrichment, freshness, coverage, griffe, presence share no state and must not import from each other. Each must work standalone via `docvet <check>`
- **Git via subprocess only**: Never import gitpython or git libraries. Use `subprocess.run` with `git` commands. Handle non-git directories gracefully (clear error, no traceback)
- **`[tool.docvet]` may not exist**: Config reads from `pyproject.toml`. Missing section = use defaults, not error
- **Reproduce random test failures**: Use `pytest -p randomly --randomly-seed=XXXXX` with the seed from CI output

---

Last Updated: 2026-03-08
