# `overload-has-docstring`

{{ rule_header() }}

## What it detects

This rule flags `@overload`-decorated functions and methods that contain a docstring. Both the bare `@overload` form (from `typing` or `typing_extensions`) and the attribute-access form (`@typing.overload`, `@typing_extensions.overload`) are detected.

## Why is this a problem?

Python's `help()` function, IDE tooltips, and documentation generators (mkdocstrings, Sphinx) only display the docstring from the **implementation** function — not from `@overload` signatures. A docstring on an overload is invisible to every consumer that matters:

- **`help()`** — shows only the implementation docstring
- **mkdocstrings / Sphinx** — renders the implementation docstring
- **IDE hover** — displays the implementation docstring
- **AI coding agents** — see the implementation docstring via AST parsing

Placing documentation on overloads creates a false sense of coverage while the actual documentation endpoint (the implementation function) may remain undocumented.

!!! note "Equivalent to ruff D418"
    This rule catches the same problem as ruff's [D418](https://docs.astral.sh/ruff/rules/overload-with-docstring/) rule. If you already enforce D418, this rule provides redundant coverage within docvet's unified pipeline.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    from typing import overload

    @overload
    def connect(address: str) -> TCPConnection:
        """Connect using a hostname string."""  # (1)!
        ...

    @overload
    def connect(address: tuple[str, int]) -> TCPConnection:
        """Connect using a (host, port) tuple."""  # (2)!
        ...

    def connect(address: str | tuple[str, int]) -> TCPConnection:
        ...
    ```

    1. This docstring is ignored by `help()`, IDEs, and doc generators.
    2. This one too — only the implementation function's docstring is displayed.

=== "Fix"

    ```python hl_lines="12 13 14 15 16 17 18 19 20"
    from typing import overload

    @overload
    def connect(address: str) -> TCPConnection: ...

    @overload
    def connect(address: tuple[str, int]) -> TCPConnection: ...

    def connect(address: str | tuple[str, int]) -> TCPConnection:
        """Connect to a server.

        Args:
            address: Hostname string or (host, port) tuple.

        Returns:
            An established connection.

        Raises:
            ConnectionError: If the server is unreachable.
        """
        ...
    ```

## Suppression

To disable this rule, set `check-overload-docstrings = false`:

```toml
[tool.docvet.presence]
check-overload-docstrings = false
```
