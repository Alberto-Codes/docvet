# `missing-other-parameters`

{{ rule_header() }}

## What it detects

This rule flags functions that accept `**kwargs` in their signature but document it nowhere in their docstring.

The rule is satisfied when either:

- the docstring has an `Other Parameters:` section, or
- the var-keyword parameter is documented under `Args:`, spelled either `**kwargs:` or `kwargs:` (using the parameter's actual name, such as `**options:`).

It fires only when `**kwargs` is documented in neither place.

## Why is this a problem?

Callers must read the source code to discover which keyword arguments are accepted and what they do. When `**kwargs` is undocumented, the function's interface is only partially documented. This is especially problematic for wrapper functions and factory patterns where `**kwargs` carries meaningful configuration.

{{ rule_fix() }}

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

=== "Fix (Args entry)"

    ```python hl_lines="6"
    def create_client(name: str, **kwargs) -> Client:
        """Create a new API client.

        Args:
            name: Client display name.
            **kwargs: Extra options forwarded to ``Client``.

        Returns:
            Configured client instance.
        """
        return Client(name=name, **kwargs)
    ```
