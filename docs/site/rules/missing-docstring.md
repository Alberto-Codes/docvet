# `missing-docstring`

{{ rule_header() }}

## What it detects

This rule flags public symbols — modules, classes, functions, and methods — that lack a docstring. Symbols filtered by `ignore-init`, `ignore-magic`, or `ignore-private` configuration are excluded from checking.

## Why is this a problem?

Docstrings are the primary way both humans and AI agents understand what code does. A missing docstring means documentation generators (mkdocstrings, Sphinx) produce empty entries, and AI coding agents must infer purpose from implementation details alone — leading to lower-quality suggestions and higher error rates.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def parse_config(path: str) -> dict:
        with open(path) as f:
            return json.load(f)


    class UserProfile:
        name: str
        email: str
    ```

=== "Fix"

    ```python hl_lines="1 2 3 4 5 6 7 8 9 10 14 15 16 17 18 19"
    def parse_config(path: str) -> dict:
        """Parse a JSON configuration file.

        Args:
            path: Path to the configuration file.

        Returns:
            Parsed configuration as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        with open(path) as f:
            return json.load(f)


    class UserProfile:
        """User profile with contact information.

        Attributes:
            name (str): The user's display name.
            email (str): The user's email address.
        """

        name: str
        email: str
    ```

## Suppression

To disable the presence check entirely, set `enabled = false`:

```toml
[tool.docvet.presence]
enabled = false
```

To exclude specific symbol types from checking, use the ignore flags:

```toml
[tool.docvet.presence]
ignore-init = true     # skip __init__ methods (default)
ignore-magic = true    # skip __repr__, __str__, etc. (default)
ignore-private = true  # skip _helper, _internal, etc. (default)
```
