# `missing-cross-references`

{{ rule_header() }}

## What it detects

This rule flags module docstrings that are missing a `See Also:` section, or where the `See Also:` section lacks linkable cross-reference syntax (bracket references or Sphinx roles). Plain backtick identifiers (`` `module.name` ``) do not satisfy this rule because they render as inline code without a clickable hyperlink in mkdocstrings.

## Why is this a problem?

Modules serve as navigation entry points in documentation. Without cross-references, users landing on a module page in mkdocs have no links to related modules or classes. This breaks the discoverability that makes documentation sites useful — readers are left to browse the navigation tree manually.

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
        [`myapp.utils.parsing`][]: String and data parsing helpers.
        [`myapp.utils.validation`][]: Input validation utilities.
    """
    ```
