# `griffe-unknown-param`

{{ rule_header() }}

## What it detects

This rule flags docstrings that document a parameter which does not exist in the function's actual signature. The check uses griffe's Google-style parser to compare documented parameters against the function definition.

## Why is this a problem?

A documented parameter that doesn't exist in the signature is actively misleading. The parameter may have been renamed or removed during a refactor, leaving stale documentation that confuses callers. This also causes visible rendering errors on mkdocs documentation sites.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def send_request(url: str, retries: int = 3) -> Response:
        """Send an HTTP request.

        Args:
            url: Target URL.
            timeout: Request timeout in seconds.
            retries: Number of retry attempts.

        Returns:
            HTTP response object.
        """
        ...
    ```

=== "Fix"

    ```python hl_lines="4 5 6"
    def send_request(url: str, retries: int = 3) -> Response:
        """Send an HTTP request.

        Args:
            url: Target URL.
            retries: Number of retry attempts.

        Returns:
            HTTP response object.
        """
        ...
    ```
