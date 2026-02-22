# `stale-signature`

{{ rule_header() }}

## What it detects

This rule flags functions whose signature (parameters, return type, or decorators) was changed in a git diff but whose docstring was not updated in the same diff. This is the highest-severity freshness finding.

## Why is this a problem?

A changed signature means the function's calling contract has changed. Callers relying on the documented parameters, types, or return values now have wrong information. This is the most impactful form of docstring staleness because it directly misleads anyone reading the docs.

## Example

=== "Violation"

    ```python
    # Before the diff:
    def fetch_data(url: str) -> dict: ...

    # After the diff (parameter added, docstring unchanged):
    def fetch_data(url: str, timeout: int = 30) -> dict:
        """Fetch data from a remote URL.

        Args:
            url: The URL to fetch from.

        Returns:
            Parsed response data.
        """
        ...
    ```

=== "Fix"

    ```python hl_lines="6"
    def fetch_data(url: str, timeout: int = 30) -> dict:
        """Fetch data from a remote URL.

        Args:
            url: The URL to fetch from.
            timeout: Request timeout in seconds. Defaults to 30.

        Returns:
            Parsed response data.
        """
        ...
    ```
