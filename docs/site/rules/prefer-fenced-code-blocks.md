# `prefer-fenced-code-blocks`

{{ rule_header() }}

## What it detects

This rule flags `Examples:` sections that use doctest `>>>` format instead of triple-backtick fenced code blocks with a `python` language marker.

## Why is this a problem?

mkdocs-material renders fenced code blocks with syntax highlighting, copy buttons, and line numbers. Doctest `>>>` format renders as plain, unhighlighted text, resulting in a noticeably worse reading experience on your documentation site. Fenced blocks also support annotations and other material theme features.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def add(a: int, b: int) -> int:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Sum of a and b.

        Examples:
            >>> add(1, 2)
            3
            >>> add(-1, 1)
            0
        """
        return a + b
    ```

=== "Fix"

    ```python hl_lines="12 13 14 15"
    def add(a: int, b: int) -> int:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Sum of a and b.

        Examples:
            ```python
            add(1, 2)  # returns 3
            add(-1, 1)  # returns 0
            ```
        """
        return a + b
    ```
