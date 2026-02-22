# `missing-other-parameters`

{{ rule_header() }}

## What it detects

This rule flags functions that accept `**kwargs` in their signature but have no `Other Parameters:` section in their docstring.

## Why is this a problem?

Callers must read the source code to discover which keyword arguments are accepted and what they do. Without an `Other Parameters:` section, the function's interface is only partially documented. This is especially problematic for wrapper functions and factory patterns where `**kwargs` carries meaningful configuration.

## Example

=== "Violation"

    ```python
    def create_client(name: str, **kwargs) -> Client:
        """Create a new API client.

        Args:
            name: Client display name.

        Returns:
            Configured client instance.
        """
        return Client(name=name, **kwargs)
    ```

=== "Fix"

    ```python hl_lines="7 8 9 10"
    def create_client(name: str, **kwargs) -> Client:
        """Create a new API client.

        Args:
            name: Client display name.

        Other Parameters:
            timeout (int): Request timeout in seconds. Defaults to 30.
            retries (int): Number of retry attempts. Defaults to 3.
            base_url (str): Override the default API base URL.

        Returns:
            Configured client instance.
        """
        return Client(name=name, **kwargs)
    ```
