# `missing-attributes`

{{ rule_header() }}

## What it detects

This rule flags classes (dataclasses, NamedTuples, TypedDicts, and classes with `__init__` self-assignments) and `__init__.py` modules that have no `Attributes:` section in their docstring.

## Why is this a problem?

Users can't discover object properties or module-level variables without reading the source code. Documentation generators like mkdocstrings render empty attribute tables when the `Attributes:` section is missing, creating a poor documentation experience for anyone trying to use the class or module.

## Example

=== "Violation"

    ```python
    @dataclass
    class UserProfile:
        """A user's profile information."""

        name: str
        email: str
        role: str = "viewer"
    ```

=== "Fix"

    ```python hl_lines="5 6 7 8"
    @dataclass
    class UserProfile:
        """A user's profile information.

        Attributes:
            name (str): The user's display name.
            email (str): The user's email address.
            role (str): The user's role. Defaults to "viewer".
        """

        name: str
        email: str
        role: str = "viewer"
    ```
