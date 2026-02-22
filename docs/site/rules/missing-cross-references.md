# `missing-cross-references`

{{ rule_header() }}

## What it detects

This rule flags `__init__.py` module docstrings that are missing a `See Also:` section, or where the `See Also:` section lacks cross-reference syntax (backtick-quoted identifiers or Markdown links).

## Why is this a problem?

Package modules serve as navigation entry points in documentation. Without cross-references, users landing on a package page in mkdocs have no links to related modules or classes. This breaks the discoverability that makes documentation sites useful — readers are left to browse the navigation tree manually.

## Example

=== "Violation"

    ```python
    # myapp/utils/__init__.py
    """Utility functions for the myapp package."""
    ```

=== "Fix"

    ```python hl_lines="4 5 6"
    # myapp/utils/__init__.py
    """Utility functions for the myapp package.

    See Also:
        `myapp.utils.parsing`: String and data parsing helpers.
        `myapp.utils.validation`: Input validation utilities.
    """
    ```
