# `extra-yields-in-docstring`

{{ rule_header() }}

## What it detects

This rule flags functions and methods that have a `Yields:` section but no `yield` or `yield from` statements in their body. The check is scope-aware — yields inside nested functions or classes are not counted.

## Why is this a problem?

A `Yields:` section on a non-generator function misleads callers into treating the function as an iterator. After a refactor that replaces `yield` with `return` or removes generator behaviour entirely, a leftover `Yields:` section creates confusion about the function's interface.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def get_items(data: list) -> list:
        """Retrieve items from data.

        Yields:
            str: Each item from the data list.
        """
        return [str(item) for item in data]
    ```

=== "Fix"

    ```python
    def get_items(data: list) -> list:
        """Retrieve items from data.

        Returns:
            A list of stringified items.
        """
        return [str(item) for item in data]
    ```

## Configuration

This rule is gated by `require-yields`, the same toggle that controls `missing-yields`. Disabling it skips both the forward and reverse checks:

```toml
[tool.docvet.enrichment]
require-yields = false
```

## Exceptions

This rule is automatically skipped when:

- The function is `@abstractmethod` (interface contract documentation)
- The function body is a stub (`pass`, `...`, or `raise NotImplementedError`)
- The symbol is a class, module, or other non-function type
- The docstring has no `Yields:` section
