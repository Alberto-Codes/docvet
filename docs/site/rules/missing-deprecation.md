# `missing-deprecation`

{{ rule_header() }}

## What it detects

This rule flags functions that have a deprecation pattern in code but no deprecation notice in their docstring.

It triggers when a function:

- Calls `warnings.warn(..., DeprecationWarning)`, `warnings.warn(..., PendingDeprecationWarning)`, or `warnings.warn(..., FutureWarning)` in its body (at the top scope — not inside nested `def` or `class` blocks), **or**
- Is decorated with `@deprecated`, `@typing_extensions.deprecated`, `@warnings.deprecated`, or any other `@*.deprecated` form

...and the docstring does not contain the word `"deprecated"` (case-insensitive).

## Why is this a problem?

Users reading documentation cannot tell they should migrate away from a deprecated API. This causes continued adoption of code that will be removed in a future version, silent breakage in production when the API is eventually removed, and confusion when runtime warnings appear without any explanation in the documentation.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    import warnings

    def old_api(x):
        """Process x using the old algorithm."""
        warnings.warn("Use new_api instead", DeprecationWarning)
        return x * 2
    ```

=== "Fix"

    ```python hl_lines="5 6"
    import warnings

    def old_api(x):
        """Process x using the old algorithm.

        Deprecated:
            This function is deprecated since v2.0. Use :func:`new_api` instead.
        """
        warnings.warn("Use new_api instead", DeprecationWarning)
        return x * 2
    ```

## Notes

- The check is intentionally loose: "deprecated" anywhere in the docstring (summary line, body paragraph, or a `Deprecated:` section) satisfies the rule.
- The scope-aware walk does not flag the outer function when `warnings.warn` is called inside a nested `def` or `class` — each scope is evaluated independently.
- `@deprecated` matching is decorator-name-based (no import resolution). This covers `@deprecated`, `@typing_extensions.deprecated`, `@warnings.deprecated`, and any other module's `deprecated` decorator.
- This rule works identically in both Google and Sphinx docstring modes because detection uses the code AST (not parsed docstring sections) and a raw string search.

## Configuration

Disable this rule if your project does not use Python deprecation patterns:

```toml
[tool.docvet.enrichment]
require-deprecation-notice = false
```
