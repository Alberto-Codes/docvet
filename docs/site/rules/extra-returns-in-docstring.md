# `extra-returns-in-docstring`

{{ rule_header() }}

## What it detects

This rule flags functions and methods that have a `Returns:` section but no meaningful return value in their body. Bare `return` and `return None` are control-flow idioms, not meaningful returns — they do not satisfy the check.

## Why is this a problem?

A `Returns:` section on a function that never returns a value misleads callers into expecting and using a return value. After a refactor that removes the return path, a leftover `Returns:` section creates confusion and may cause `None`-related bugs in calling code.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def save(data: dict) -> None:
        """Save data to disk.

        Returns:
            The saved file path.
        """
        with open("data.json", "w") as f:
            json.dump(data, f)
    ```

=== "Fix"

    ```python
    def save(data: dict) -> None:
        """Save data to disk."""
        with open("data.json", "w") as f:
            json.dump(data, f)
    ```

## Configuration

This rule is controlled by `check-extra-returns` (default: `true`). The forward check (`missing-returns`) is controlled independently by `require-returns`.

```toml
[tool.docvet.enrichment]
check-extra-returns = false
```

## Exceptions

This rule is automatically skipped when:

- The function is `@abstractmethod` (interface contract documentation)
- The function body is a stub (`pass`, `...`, or `raise NotImplementedError`)
- The symbol is a class, module, or other non-function type
- The docstring has no `Returns:` section
