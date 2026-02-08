---
applyTo: "**/*.py"
description: "Google Python Style Guide conventions for all Python code"
---

# Google Python Style Guide

Follow the Google Python Style Guide (https://google.github.io/styleguide/pyguide.html) for all Python code generation.

- Follow Google-style docstrings and project conventions.

## Docstring Format

Use Google-style docstrings with triple double-quotes for all public modules, functions, classes, and methods.

Structure docstrings with a one-line summary (max 80 chars, ending with period), followed by a blank line, then detailed description. Include these sections when applicable: Args, Returns, Raises, Yields, Examples.

Example function docstring:
```python
def fetch_data(
    table_handle: Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """Fetches rows from a table.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by table_handle. String keys will be UTF-8 encoded.

    Args:
        table_handle: An open Table instance.
        keys: A sequence of strings representing the key of each table
            row to fetch. String keys will be UTF-8 encoded.
        require_all_keys: If True only rows with values set for all keys
            will be returned.

    Returns:
        A dict mapping keys to the corresponding table row data fetched.
        Each row is represented as a tuple of strings.

    Raises:
        IOError: An error occurred accessing the table.
    """
```

Example class docstring:
```python
class SampleClass:
    """Summary of class here.

    Longer class information providing additional context and details
    about the class purpose and behavior.

    Attributes:
        likes_spam: A boolean indicating if we like SPAM or not.
        eggs: An integer count of the eggs we have laid.
    """

    def __init__(self, likes_spam: bool = False):
        """Initializes the instance based on spam preference.

        Args:
            likes_spam: Defines if instance exhibits this preference.
        """
```

Use "Yields:" section instead of "Returns:" for generator functions. For @property decorators, use attribute style ("The table path.") not "Returns the...".

Reference docstring templates as needed.
docs/contributing/docstring-templates.md

## Naming Conventions

Follow these naming patterns strictly:

- **Functions and variables**: `lower_with_under` (snake_case)
- **Classes**: `CapWords` (PascalCase)
- **Constants**: `CAPS_WITH_UNDER` (all caps with underscores)
- **Module names**: `lower_with_under.py` (never use dashes)
- **Protected members**: prefix with single underscore `_lower_with_under`
- **Exception names**: end with "Error" suffix (e.g., `OutOfCheeseError`)

Avoid single-character names except for: counters/iterators (i, j, k, v), exception identifiers (e), file handles (f), and type variables (_T, _P).

Never use dashes in any package or module names.

## Import Rules

Order imports from most generic to least generic:
1. `from __future__ import annotations` (always first)
2. Python standard library imports
3. Third-party imports
4. Local application/repository imports

Use full package paths and avoid relative imports. Import modules, not individual classes/functions (exception: typing and collections.abc modules). Place imports on separate lines unless from typing/collections.abc.

Example import structure:
```python
from __future__ import annotations

import ast
import json
import sys

import typer

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from docvet.ast_utils import get_docstring_range
```

Never use wildcard imports.

## Formatting Standards

Use maximum line length of **88 characters** (formatter target) with linter threshold of **100 characters**. This provides a "soft" vs "hard" limit: the formatter targets 88 characters while the linter only flags lines exceeding 100 characters.

Use **4 spaces per indentation level**. Never use tabs.

Use implicit line continuation with parentheses, brackets, and braces. Never use backslash for line continuation.

Surround top-level functions and classes with two blank lines. Use one blank line between method definitions.

## Type Hints

Include type hints for all function parameters and return values. Use modern type hint syntax (e.g., `list[str]` instead of `List[str]`).

Use `X | None` syntax for optional types. Always be explicit about None in type hints.

Use `from __future__ import annotations` at the top of every file for forward reference support. Do not annotate `self` or `cls` parameters.

## String Formatting

Use f-strings for string interpolation. Never use `+` operator to build formatted strings.

For logging, use %-formatting with lazy evaluation (not f-strings):
```python
logger.info("Processing file: %s", filename)
```

## Comments and Documentation

Write comments that explain WHY, not WHAT (assume reader knows Python). Use complete sentences with proper punctuation.

For TODO comments, use format: `# TODO: <explanation>`

## Boolean and None Checks

Use implicit boolean evaluation for containers:
```python
if my_list:
    process(my_list)
```

Always use explicit `is` or `is not` for None checks:
```python
if value is None:
    return
```

## Functions and Methods

Keep functions focused and reasonably short (consider breaking up if exceeds ~40 lines).

Never use mutable objects as default arguments.

## File and Resource Management

Always use `with` statements for file and resource management.

## Exception Handling

Use specific exception types. Never use bare `except:` clauses.

Include informative error messages with context:
```python
if not 0 <= probability <= 1:
    raise ValueError(f"Not a probability: {probability=}")
```

## General Principles

Prioritize code readability and clarity over cleverness. Be consistent with existing code style when editing existing files.

Use `from __future__ import annotations` at the top of every file.
