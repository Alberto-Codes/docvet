# `griffe-missing-type`

{{ rule_header() }}

## What it detects

This rule flags parameters or return values in docstrings that lack a type annotation. The check uses griffe's Google-style parser to identify entries missing the `name (type): description` format.

## Why is this a problem?

mkdocstrings relies on docstring type annotations to render type information in API documentation. Without the parenthesized type, the generated docs lose type context, forcing users to check the source code or type stubs to understand what types a function expects and returns.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def create_user(name, email, role="viewer"):
        """Create a new user account.

        Args:
            name: The user's display name.
            email: The user's email address.
            role: The user's role.

        Returns:
            The created user object.
        """
        ...
    ```

=== "Fix"

    ```python hl_lines="5 6 7 10"
    def create_user(name, email, role="viewer"):
        """Create a new user account.

        Args:
            name (str): The user's display name.
            email (str): The user's email address.
            role (str): The user's role.

        Returns:
            User: The created user object.
        """
        ...
    ```
