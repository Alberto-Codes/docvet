# `missing-warns`

{{ rule_header() }}

## What it detects

This rule flags functions that call `warnings.warn()` but have no `Warns:` section in their docstring.

## Why is this a problem?

Users of the function don't know which warnings to expect or suppress. Undocumented warnings create noisy log output in production and make it impossible to write targeted warning filters. Callers need to know the warning category and trigger condition to handle them appropriately.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def connect(host: str, timeout: int = 30) -> Connection:
        """Connect to the remote server.

        Args:
            host: Server hostname.
            timeout: Connection timeout in seconds.

        Returns:
            Active connection object.
        """
        if timeout < 5:
            warnings.warn(
                "Very short timeout may cause failures",
                stacklevel=2,
            )
        return Connection(host, timeout)
    ```

=== "Fix"

    ```python hl_lines="11 12"
    def connect(host: str, timeout: int = 30) -> Connection:
        """Connect to the remote server.

        Args:
            host: Server hostname.
            timeout: Connection timeout in seconds.

        Returns:
            Active connection object.

        Warns:
            UserWarning: If timeout is less than 5 seconds.
        """
        if timeout < 5:
            warnings.warn(
                "Very short timeout may cause failures",
                stacklevel=2,
            )
        return Connection(host, timeout)
    ```
