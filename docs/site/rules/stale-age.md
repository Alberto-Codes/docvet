# `stale-age`

{{ rule_header() }}

## What it detects

This rule flags symbols whose docstring has not been touched for more than `age-threshold` days (default: 90), regardless of whether the code changed. It uses `git blame` timestamps to determine the docstring's last modification date.

## Why is this a problem?

Very old docstrings may describe obsolete behavior, outdated APIs, or deprecated patterns — even if the surrounding code hasn't changed much. A periodic review of aging docstrings ensures they remain accurate and relevant as the project evolves.

## Example

=== "Violation"

    ```python
    # Docstring last modified 180 days ago:
    def get_connection() -> Connection:
        """Get a database connection from the pool.

        Returns:
            Active database connection.
        """
        return pool.acquire()
    ```

=== "Fix"

    ```python hl_lines="3 4 5 6 7"
    # Reviewed and updated (resets the age counter):
    def get_connection() -> Connection:
        """Get a database connection from the pool.

        Returns:
            Active database connection.
        """
        return pool.acquire()
    ```
