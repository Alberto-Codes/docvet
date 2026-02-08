# Feature Brief: docvet

## What It Is

**docvet** — a reusable, project-agnostic Python CLI package for comprehensive docstring
quality vetting. It fills the gap between style linting (ruff D rules) and presence
checking (interrogate) by verifying that docstrings are **complete**, **accurate**, and
**renderable** for mkdocs-material + mkdocstrings workflows.

Publishable to PyPI as `docvet`. Short, memorable, zero-conflict name. "Doc" signals the
domain, "vet" signals thorough examination — vetting your docs for fitness.

```bash
pip install docvet           # install
docvet check                 # CLI
import docvet                # Python
[tool.docvet]                # pyproject.toml config
```

## The Problem

Existing tools check two things: "does a docstring exist?" (interrogate) and "is it
Google-style formatted?" (ruff D rules). But docstrings fail in four ways these tools
miss:

1. **Stale** — code changed, docstring didn't. The Args list describes parameters that
   no longer exist, or misses new ones. This is worse than no docstring because it
   actively misleads.
2. **Incomplete** — a function raises `ValueError` but has no `Raises:` section. A
   Protocol has no `Examples:` showing how to implement it. A dataclass has 8 fields
   but no `Attributes:` section.
3. **Invisible** — a Python file exists but won't appear in mkdocs-generated
   documentation because a parent directory is missing `__init__.py`.
4. **Broken rendering** — docstrings that parse fine as text but produce griffe warnings
   during mkdocs build (missing parameter types in Args, etc.).

No existing off-the-shelf tool addresses problems 1-4. `darglint` (deprecated) partially
covered Args/Returns/Raises alignment but never handled Examples, Attributes, Yields,
Warns, or rendering compatibility. These checks require custom AST analysis combined with
git integration.

## The Six-Layer Docstring Quality Model

This package positions itself within a complete quality stack:

| Layer | Tool | What It Catches |
|-------|------|-----------------|
| **1. Presence** | interrogate | "Does a docstring exist?" |
| **2. Style** | ruff D rules | "Is it Google-style formatted?" |
| **3. Completeness** | docvet enrichment | "Does it have all required sections?" |
| **4. Accuracy** | docvet freshness | "Does it match the current code?" |
| **5. Rendering** | docvet griffe | "Will mkdocs render it correctly?" |
| **6. Visibility** | docvet coverage | "Will mkdocs even see the file?" |

Layers 1-2 are solved by existing tools. This package delivers layers 3-6.

## The Four Checks

### 1. Enrichment (Completeness)

AST-based detection of missing docstring sections based on code structure analysis.

**Detection rules:**

- **Functions/methods with `raise` statements** -> require `Raises:` section
- **Generator functions with `yield`** -> require `Yields:` section
- **Generators using `value = yield` (send pattern)** -> require `Receives:` section
- **Functions calling `warnings.warn()`** -> require `Warns:` section
- **Functions with `**kwargs`** -> require `Other Parameters:` section
- **Public functions/methods with parameters** -> recommend `Examples:` section
- **Classes with `__init__` self-assignments** -> require `Attributes:` section
- **Dataclasses/NamedTuples/TypedDicts with fields** -> require `Attributes:` with types
- **Protocols** -> recommend `Examples:` showing implementation
- **Enums** -> recommend `Examples:` showing value access
- **`__init__.py` modules** -> require `Attributes:` (exports), `Examples:`, `See Also:`
- **`Attributes:` sections** -> should include types in parentheses: `name (type): desc`
- **`See Also:` sections** -> should use cross-reference syntax: `` [`name`][ref] ``
- **`Examples:` sections** -> should use fenced code blocks, not `>>>` doctest format

### 2. Freshness (Accuracy)

Two modes of staleness detection:

**Diff mode (primary, fast):**
- Parses `git diff` (unstaged) or `git diff --cached` (staged) to get changed hunks
- Maps changed lines to AST symbols (functions, classes, modules)
- Flags symbols where **code lines are in the diff but docstring lines are not**
- Severity levels:
  - **HIGH**: Signature changed (args added/removed/renamed) — docstring Args almost
    certainly wrong
  - **MEDIUM**: Body changed (logic modified) — docstring may need updating
  - **LOW**: Only imports/formatting changed — docstring likely fine

**Drift mode (periodic sweep, slower):**
- Uses `git blame --line-porcelain` to get per-line timestamps
- Compares most recent docstring modification date vs most recent code modification date
- Flags when code is newer than docstring by a configurable threshold (default: 30 days)
- Also flags docstrings untouched beyond an age threshold (default: 90 days)
- Useful for codebase-wide audits, not everyday development

### 3. Coverage (Visibility)

Detects Python files that won't appear in mkdocs-generated documentation due to missing
`__init__.py` files in parent directories. Mirrors the import resolution logic that
mkdocstrings uses — if Python can't import it, mkdocstrings can't document it.

### 4. Griffe Compatibility (Rendering)

Uses griffe (the mkdocstrings parser) as a library to parse all docstrings and capture
warnings. Primarily catches missing type annotations in `Args:` / `Other Parameters:`
sections that would produce warnings during `mkdocs build`.

## Prior Art

Four scripts in the `gepa-adk` project (`scripts/docstring_*.py`) implement these checks
as standalone scripts with hardcoded paths. This package extracts and generalizes that
logic into a reusable, configurable tool. Key improvements over the prior art:

- No hardcoded project paths — everything via `pyproject.toml` configuration
- Diff-mode freshness (the prior art only has drift-mode via git blame)
- Severity levels for diff-mode staleness
- Single unified CLI instead of four separate scripts
- Publishable as a PyPI package

## Package Architecture

```
src/docvet/
├── __init__.py
├── cli.py                # CLI entry points (typer)
├── config.py             # pyproject.toml [tool.docvet] reader
├── discovery.py          # file discovery (git diff, git diff --cached, --all, --files)
├── ast_utils.py          # shared AST helpers (docstring ranges, node walking, symbol mapping)
├── reporting.py          # markdown/terminal report generation
└── checks/
    ├── __init__.py
    ├── enrichment.py     # missing sections detection (AST-based)
    ├── freshness.py      # git-blame drift + git-diff immediate staleness
    ├── coverage.py       # missing __init__.py for mkdocs
    └── griffe_compat.py  # griffe parser warning capture
```

## Implementation Progress

| Module | Status | Notes |
|--------|--------|-------|
| `cli.py` | Implemented | All subcommands scaffolded as stubs |
| `config.py` | Implemented | `[tool.docvet]` reader with full validation |
| `discovery.py` | Implemented | All 4 modes: diff, staged, all, files |
| `ast_utils.py` | Implemented | Symbol dataclass + 5 core functions |
| `reporting.py` | Not started | |
| `checks/` directory | Not started | No directory in `src/docvet/` yet |
| `checks/enrichment.py` | Not started | Depends on `ast_utils.py` |
| `checks/freshness.py` | Not started | Depends on `ast_utils.py` |
| `checks/coverage.py` | Not started | |
| `checks/griffe_compat.py` | Not started | |
| CI workflow | Implemented | lint, format, type-check, test, interrogate |

## Configuration

Via `pyproject.toml`:

```toml
[tool.docvet]
src-root = "src/my_package"
package-name = "my_package"
exclude = ["tests", "scripts"]
fail-on = ["griffe", "coverage"]       # exit 1 (blocking)
warn-on = ["freshness", "enrichment"]  # exit 0 (advisory)

[tool.docvet.freshness]
drift-threshold = 30   # days for drift mode
age-threshold = 90     # days for age detection

[tool.docvet.enrichment]
require-examples = ["class", "protocol", "dataclass", "enum"]
require-raises = true
require-yields = true
require-warns = true
require-receives = true
require-other-parameters = true
require-typed-attributes = true
require-cross-references = true
prefer-fenced-code-blocks = true
```

## CLI Interface

```bash
# Run all checks on git diff files (default workflow)
docvet check

# Run all checks on staged files
docvet check --staged

# Run all checks on entire codebase
docvet check --all

# Run specific checks
docvet enrichment [--all | --files FILE1 FILE2]
docvet freshness [--mode diff|drift] [--all | --files FILE1 FILE2]
docvet coverage [--all | --files FILE1 FILE2]
docvet griffe [--all | --files FILE1 FILE2]

# Common flags
--verbose          # detailed output
--format terminal  # or markdown
--output FILE      # write report to file
```

## Technical Constraints

- Python 3.12+, `from __future__ import annotations`
- Dependencies: typer (CLI), griffe (rendering check only — optional extra)
- No other runtime dependencies — AST parsing and git are stdlib/system
- `griffe` as optional: `pip install docvet[griffe]`
- Google-style docstrings assumed (configurable in future if needed)

## Target Consumers

- **stream-ai-pipeline**: Kafka stream processing project, hexagonal architecture,
  Protocols as port interfaces, Pydantic models, async handlers
- **gepa-adk**: Genetic programming ADK, published to PyPI, mkdocs-material docs
- **Any Python project** using Google-style docstrings, especially those targeting
  mkdocs-material + mkdocstrings for documentation generation

## Testing Strategy

- **Unit tests**: Feed known Python source strings into AST analyzers. Assert expected
  enrichment opportunities and freshness flags. No git, no filesystem.
- **Integration tests**: Create temp git repos with known commit histories, run freshness
  and diff checks, verify results.
- **Fixture-based**: `tests/fixtures/` directory with `.py` files containing known
  docstring issues. Test suite runs checks and asserts expected findings.

## Success Criteria

- All four checks work on both stream-ai-pipeline and gepa-adk without project-specific
  code paths
- Diff-mode freshness correctly identifies signature changes as HIGH severity
- Enrichment check detects all section types listed in detection rules
- Package installable via `pip install docvet` from PyPI
- Configurable via pyproject.toml with sensible defaults
- Integrates into code_quality_check.sh-style workflows as a single CLI call

## References

- ADR-010 (stream-ai-pipeline): Docstring Quality Standards
- docstring-templates.md (stream-ai-pipeline): Google-style section templates
- gepa-adk scripts: `scripts/docstring_freshness.py`, `scripts/docstring_enrichment.py`,
  `scripts/docstring_docs_coverage.py`, `scripts/docstring_griffe_check.py`
- mkdocstrings-python: https://mkdocstrings.github.io/python/
- griffe: https://mkdocstrings.github.io/griffe/
