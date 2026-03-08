# `extra-param-in-docstring`

{{ rule_header() }}

## What it detects

This rule flags functions and methods that have an `Args:` section documenting parameter names that do not exist in the function signature. This catches stale entries left behind after parameter renames or removals.

## Why is this a problem?

Documenting parameters that don't exist misleads callers into passing arguments the function doesn't accept. After a refactor that renames or removes a parameter, leftover `Args:` entries create confusion and may cause runtime errors when callers follow outdated documentation.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def connect(host: str, port: int):
        """Connect to a server.

        Args:
            host: The server hostname.
            port: The server port number.
            timeout: Connection timeout in seconds.
        """
    ```

=== "Fix"

    ```python
    def connect(host: str, port: int):
        """Connect to a server.

        Args:
            host: The server hostname.
            port: The server port number.
        """
    ```

## Configuration

To disable this rule entirely:

```toml
[tool.docvet.enrichment]
require-param-agreement = false
```

## Exceptions

This rule is automatically skipped when:

- The docstring has no `Args:` section (a separate concern)
- The symbol is a class, module, or other non-function type
- The symbol is an `@overload` signature (presence layer handles those)
