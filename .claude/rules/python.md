---
paths:
  - "**/*.py"
---

# Python Rules

Follow the Google Python Style Guide for all Python code. Style enforcement (imports, formatting, naming, line length, quotes) is handled by ruff and ty — these rules focus on semantic concerns those tools cannot catch.

For domain-specific implementation patterns (AST, regex, cross-rule interactions), see `_bmad-output/project-context.md`.

## Semantic Rules (not enforced by ruff/ty)

- **Every file** starts with `from __future__ import annotations` — no exceptions
- **No mutable defaults**: Never use `[]` or `{}` as function default arguments
- **No bare exceptions**: Always catch specific exception types, include context in error messages
- **No `assert` in production code**: `assert` is for tests only. Production code must use proper error handling
- **No new runtime deps**: typer is the only runtime dependency. Use stdlib for everything else
- **f-strings for formatting**, `%`-formatting for logger calls only
- **Comments explain WHY**, not WHAT — assume reader knows Python

## Docstring Format

Google-style docstrings with triple double-quotes. One-line summary (max 80 chars, ending with period), blank line, then detailed description. Sections when applicable: Args, Returns, Raises, Yields, Examples.

Use "Yields:" instead of "Returns:" for generators. For `@property`, use attribute style ("The table path.") not "Returns the...".

## Module Size Guidance

When a source module exceeds ~500 lines or contains 3+ distinct concerns (parsing, checking, helpers, dispatch), consider extracting into a sub-package:

- Pattern: `checks/enrichment.py` -> `checks/enrichment/` with `__init__.py` re-exporting public API
- Internal modules for distinct concerns (section parsing, check functions, helpers)
- Same principle applies to test files — split by rule or concern into dedicated files
- Apply when natural (during a story that touches the module), not as forced refactoring
