# `trivial-docstring`

{{ rule_header() }}

## What it detects

This rule flags docstrings whose summary line trivially restates the symbol name without adding meaningful information. It decomposes the symbol name into words, extracts words from the docstring summary, filters stop words, and checks whether the summary word set is a subset of the name word set.

## Why is this a problem?

A docstring that merely rephrases the function name wastes a reader's time — they already know what `get_user` is called. Good docstrings explain **why** the function exists, **how** it works, or **what constraints** apply. Trivial docstrings create a false sense of documentation completeness while adding no value.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def get_user():
        """Get user."""
        return db.query(User).filter_by(active=True).first()
    ```

=== "Fix"

    ```python
    def get_user():
        """Fetch the active user from the session cache by primary key."""
        return db.query(User).filter_by(active=True).first()
    ```

## Skipped symbols

- **`@property` and `@cached_property`** methods are skipped because PEP 257 and the Google Style Guide prescribe attribute-style docstrings (e.g., `"""The user name."""`) that naturally restate the attribute name.

## Detection algorithm

1. Decompose the symbol name into a word set (`snake_case` splits on `_`, `CamelCase` splits on uppercase boundaries with acronym-aware grouping).
2. Extract words from the docstring's first line, strip the trailing period, and filter stop words (`a`, `an`, `the`, `of`, `for`, `to`, `in`, etc.).
3. If every summary word is also a name word (subset check), the docstring is trivial.

## Configuration

```toml
[tool.docvet.enrichment]
check-trivial-docstrings = false  # default: true
```
