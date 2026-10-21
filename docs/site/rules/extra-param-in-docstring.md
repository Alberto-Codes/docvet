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

A documented `*args`/`**kwargs` entry never triggers this rule, whichever spelling it uses (`*args:` or `args:`; Google style recommends `*args:`). A star entry that names no signature parameter is still reported. The `exclude-args-kwargs` option does not affect this rule. It decides only whether an undocumented `*args`/`**kwargs` counts as missing (under `missing-param-in-docstring` and `undocumented-init-params`). Set `exclude-args-kwargs = false` to require their documentation (matches pydoclint's default behavior where `--should-document-star-arguments = true`).

```toml
[tool.docvet.enrichment]
exclude-args-kwargs = false
```

To disable this rule entirely:

```toml
[tool.docvet.enrichment]
require-param-agreement = false
```

## Exceptions

This rule is automatically skipped when:

- The docstring has no `Args:` section (a separate concern)
- The symbol is a class, module, or other non-function type
