# `missing-deprecation`

{{ rule_header() }}

## What it detects

This rule flags functions and methods that use deprecation patterns in their code but have no deprecation notice in their docstring. It detects two families of patterns:

1. **`warnings.warn()` with a deprecation category** — `DeprecationWarning`, `PendingDeprecationWarning`, or `FutureWarning` as the second positional argument or `category` keyword argument.
2. **`@deprecated` decorator** (PEP 702) — from `typing_extensions` or `warnings` (Python 3.13+).

A deprecation notice is satisfied by the word "deprecated" appearing anywhere in the docstring (case-insensitive).

## Why is this a problem?

Users reading the documentation have no way to know the function is deprecated. Without a visible notice in the docstring, callers will continue using the deprecated API, miss migration deadlines, and encounter unexpected breakage when the function is eventually removed.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    import warnings

    def connect(host: str) -> Connection:
        """Connect to the server.

        Args:
            host: The server hostname.

        Returns:
            An established connection.
        """
        warnings.warn(
            "connect() is deprecated, use connect_async()",
            DeprecationWarning,
            stacklevel=2,
        )
        return Connection(host)
    ```

=== "Fix"

    ```python hl_lines="5 6"
    import warnings

    def connect(host: str) -> Connection:
        """Connect to the server.

        Deprecated:
            Use :func:`connect_async` instead. Will be removed in v3.0.

        Args:
            host: The server hostname.

        Returns:
            An established connection.
        """
        warnings.warn(
            "connect() is deprecated, use connect_async()",
            DeprecationWarning,
            stacklevel=2,
        )
        return Connection(host)
    ```

## Configuration

Disable this rule in `pyproject.toml`:

```toml
[tool.docvet.enrichment]
require-deprecation-notice = false
```

## Detected patterns

| Pattern | Example |
|---------|---------|
| `warnings.warn(..., DeprecationWarning)` | `warnings.warn("old", DeprecationWarning)` |
| `warnings.warn(..., PendingDeprecationWarning)` | `warnings.warn("old", PendingDeprecationWarning)` |
| `warnings.warn(..., FutureWarning)` | `warnings.warn("old", FutureWarning)` |
| `warnings.warn(..., category=...)` | `warnings.warn("old", category=DeprecationWarning)` |
| `@deprecated("reason")` | PEP 702 decorator from `typing_extensions` or `warnings` |

Note: `warnings.warn("msg")` with no explicit category defaults to `UserWarning` and is **not** detected by this rule.
