# docvet — Architecture

## Executive Summary

docvet is a CLI tool built on typer that implements a modular check pipeline for docstring quality analysis. Each check operates independently on discovered files, producing findings that are aggregated by a reporting layer. The architecture separates concerns into CLI entry, file discovery, AST analysis, individual checks, and report generation.

## Architecture Pattern

**Pipeline architecture** with these layers:

1. **CLI Layer** (`cli.py`) — Parses commands and flags, resolves discovery mode, delegates to checks
2. **Configuration Layer** (`config.py`) — Reads `[tool.docvet]` from `pyproject.toml`, provides defaults
3. **Discovery Layer** (`discovery.py`) — Resolves which files to check via git diff, staged, all, or explicit paths
4. **Analysis Layer** (`ast_utils.py`) — Shared AST helpers for docstring extraction, line mapping, and symbol resolution
5. **Check Layer** (`checks/*.py`) — Four isolated checks (enrichment, freshness, coverage, griffe)
6. **Reporting Layer** (`reporting.py`) — Formats findings as terminal or markdown output

```
CLI (typer)
  |
  v
Config ─── Discovery ─── AST Utils
                |
       ┌───────┼───────┐───────┐
       v       v       v       v
  enrichment freshness coverage griffe
       |       |       |       |
       └───────┴───────┴───────┘
                |
                v
           Reporting
```

## Module Descriptions

### cli.py (Implemented)

The Typer-based CLI entry point. Contains:

- **Enums:** `OutputFormat` (TERMINAL, MARKDOWN), `FreshnessMode` (DIFF, DRIFT). `DiscoveryMode` lives in `discovery.py`
- **Shared options:** `StagedOption`, `AllOption`, `FilesOption` as `Annotated` type aliases
- **Global options:** `--verbose`, `--format`, `--output` via `@app.callback(invoke_without_command=True)`
- **Subcommands:** `check` (runs all), `enrichment`, `freshness` (with `--mode`), `coverage`, `griffe`
- **Helper:** `_resolve_discovery_mode()` enforces mutual exclusivity of `--staged`, `--all`, `--files`
- **Stubs:** `_run_enrichment()`, `_run_freshness()`, `_run_coverage()`, `_run_griffe()` — placeholders for check modules

### config.py (Implemented)

Reads `[tool.docvet]` from `pyproject.toml`. Missing section defaults to sensible values (not an error). Configuration keys include `src-root`, `package-name`, `exclude`, `fail-on`, `warn-on`, and per-check settings. Validates keys, types, and check names with stderr warnings.

### discovery.py (Implemented)

Contains `DiscoveryMode` enum and `discover_files()` public function. Four modes:

- **DIFF:** `git diff --name-only --diff-filter=ACMR` (unstaged changes) — default mode
- **STAGED:** `git diff --cached --name-only --diff-filter=ACMR` (staged changes)
- **ALL:** `git ls-files` for `.gitignore` respect, `rglob` fallback for non-git directories
- **FILES:** Explicit file list from `--files` flag (bypasses exclude patterns)

Applies `.gitignore`-semantic exclude patterns via `fnmatch`. Returns sorted absolute paths. Uses `subprocess.run` for git operations. Handles non-git directories gracefully (DIFF/STAGED return empty with warning, ALL falls back to `rglob`).

### ast_utils.py (Planned)

Shared AST helpers:

- Docstring range extraction (start/end line for each docstring)
- Node walking with parent tracking
- Symbol mapping (function/class name to line ranges)
- Line-to-symbol resolution for diff hunk mapping

### checks/enrichment.py (Planned)

AST-based detection of missing docstring sections. Rules include: functions with `raise` need Raises, generators need Yields, `**kwargs` needs Other Parameters, classes need Attributes, etc.

### checks/freshness.py (Planned)

Two modes:

- **Diff mode:** Maps git diff hunks to AST symbols, flags code changes without docstring updates. Severity: HIGH (signature), MEDIUM (body), LOW (imports/formatting)
- **Drift mode:** Uses `git blame` to compare modification dates, flags age-based staleness

### checks/coverage.py (Planned)

Detects missing `__init__.py` files that would make Python files invisible to mkdocstrings.

### checks/griffe_compat.py (Planned)

Parses docstrings with griffe library, captures warnings (especially missing type annotations in Args sections).

### reporting.py (Planned)

Formats findings as terminal output (default) or markdown reports. Supports file output via `--output` flag.

## Key Design Decisions

1. **Checks are isolated** — Each check module shares no state with others and must work standalone
2. **Google-style only** — The entire tool assumes Google-style docstrings
3. **Git via subprocess** — No git libraries; uses `subprocess.run` with `git` commands
4. **No runtime deps beyond typer** — AST parsing and git are stdlib/system
5. **`DiscoveryMode` is a plain `enum.Enum`** — Not StrEnum, to avoid typer imports in the enum (migration-friendly)
6. **CLI-facing enums use `enum.StrEnum`** — `OutputFormat` and `FreshnessMode` for direct CLI value mapping
7. **`ctx.obj` stores raw types** — Format is `str`, output is `str`, not enum/Path objects

## Data Flow

```
User invokes CLI
    |
    v
Parse global options (--verbose, --format, --output)
Store in ctx.obj as raw types (str, not enum/Path)
    |
    v
Parse subcommand + discovery flags (--staged, --all, --files)
Call _resolve_discovery_mode() for mutual exclusivity
    |
    v
Load config from pyproject.toml [tool.docvet]
    |
    v
Discover files based on mode
    |
    v
For each check (enrichment, freshness, coverage, griffe):
    Parse files → Analyze → Collect findings
    |
    v
Aggregate findings → Format report → Output
```

## Testing Strategy

- **Unit tests** (`tests/unit/`): Mirror `src/docvet/` layout. Test CLI via `typer.testing.CliRunner`, test checks via source string fixtures and `ast.parse()`
- **Integration tests** (`tests/integration/`): Temp git repos via `tmp_path` fixture. Real `git init` + `git commit` for freshness checks
- **Test fixtures** (`tests/fixtures/`): `.py` files with known docstring issues (complete, missing_raises, missing_yields)
- **Coverage:** CI enforces >= 85% via `pytest-cov`
- **Randomization:** `pytest-randomly` ensures no shared state between tests
