# `extra-raises-in-docstring`

{{ rule_header() }}

## What it detects

This rule flags functions and methods whose `Raises:` section documents exception types that are not actually raised in the function body. It compares documented exception names against `raise` statements found via scope-aware AST walking.

## Why is this a problem?

Documenting exceptions that are never raised misleads callers into writing unnecessary `try`/`except` blocks. After a refactor that removes or changes exception paths, leftover `Raises:` entries create false expectations about error handling.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def parse(text: str) -> dict:
        """Parse the input text.

        Raises:
            ValueError: If the text is malformed.
            TypeError: If the input is not a string.
        """
        return json.loads(text)
    ```

=== "Fix"

    ```python
    def parse(text: str) -> dict:
        """Parse the input text.

        Raises:
            ValueError: If the text is malformed.
        """
        if not isinstance(text, str):
            raise ValueError("expected string input")
        return json.loads(text)
    ```

## Configuration

This rule is **opt-in** and disabled by default due to false positives on propagated exceptions (exceptions raised by callees but documented in the caller's `Raises:` section). Enable it with:

```toml
[tool.docvet.enrichment]
check-extra-raises = true
```

The forward check (`missing-raises`) is controlled independently by `require-raises` and remains enabled by default.

## Exceptions

This rule is automatically skipped when:

- The function is `@abstractmethod` (interface contract documentation)
- The function body is a stub (`pass`, `...`, or `raise NotImplementedError`)
- The symbol is a class, module, or other non-function type
- The docstring has no `Raises:` section
