# `stale-import`

{{ rule_header() }}

## What it detects

This rule flags functions where only imports or formatting changed in a git diff but the docstring was not updated. This is the lowest-severity freshness finding.

## Why is this a problem?

While import changes are often cosmetic, they can indicate dependency changes that affect documented behavior — for example, switching from one library to another, or adding a new import for functionality that should be documented. This rule serves as a low-priority reminder to review the docstring when the surrounding code context changes.

## Example

=== "Violation"

    ```python
    # Import changed from json to orjson (faster JSON library),
    # but docstring doesn't mention the change in behavior:
    from orjson import loads

    def parse_response(data: bytes) -> dict:
        """Parse a JSON response.

        Args:
            data: Raw response bytes.

        Returns:
            Parsed JSON as a dictionary.
        """
        return loads(data)
    ```

=== "Fix"

    ```python hl_lines="4"
    from orjson import loads

    def parse_response(data: bytes) -> dict:
        """Parse a JSON response using orjson.

        Args:
            data: Raw response bytes.

        Returns:
            Parsed JSON as a dictionary.
        """
        return loads(data)
    ```
