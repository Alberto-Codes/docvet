# `missing-typed-attributes`

{{ rule_header() }}

## What it detects

This rule flags `Attributes:` section entries that lack the typed format `name (type): description`. It checks that each attribute entry includes a parenthesized type annotation.

## Why is this a problem?

mkdocstrings relies on the `name (type): description` format to render attribute types in API documentation. Without the type in parentheses, the generated docs lose type information, forcing users to look elsewhere to understand the data types of each attribute.

## Example

=== "Violation"

    ```python
    @dataclass
    class Config:
        """Application configuration.

        Attributes:
            host: The server hostname.
            port: The server port number.
            debug: Whether debug mode is enabled.
        """

        host: str
        port: int
        debug: bool = False
    ```

=== "Fix"

    ```python hl_lines="6 7 8"
    @dataclass
    class Config:
        """Application configuration.

        Attributes:
            host (str): The server hostname.
            port (int): The server port number.
            debug (bool): Whether debug mode is enabled.
        """

        host: str
        port: int
        debug: bool = False
    ```
