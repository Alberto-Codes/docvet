# `missing-init`

{{ rule_header() }}

## What it detects

This rule flags directories in your source tree that contain Python files but lack an `__init__.py` file.

## Why is this a problem?

Without an `__init__.py`, the directory is not recognized as a Python package by documentation generators like mkdocstrings. All Python files in that directory become invisible to your docs site — they won't appear in auto-generated API documentation, even though they may be importable at runtime via implicit namespace packages.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    # Directory structure:
    # src/myapp/helpers/
    #   ├── parsing.py
    #   ├── validation.py
    #   └── (no __init__.py)
    #
    # mkdocstrings cannot discover helpers.parsing
    # or helpers.validation for API docs.
    ```

=== "Fix"

    ```python hl_lines="3 7 8"
    # Add __init__.py to the directory:
    # src/myapp/helpers/
    #   ├── __init__.py
    #   ├── parsing.py
    #   └── validation.py

    # src/myapp/helpers/__init__.py
    """Helper utilities for the myapp package."""
    ```
