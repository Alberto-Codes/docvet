# `prefer-fenced-code-blocks`

{{ rule_header() }}

## What it detects

This rule flags `Examples:` sections that use doctest `>>>` format or reStructuredText `::` indented code blocks instead of triple-backtick fenced code blocks with a language marker.

## Why is this a problem?

mkdocs-material renders fenced code blocks with syntax highlighting, copy buttons, and line numbers. Doctest `>>>` format and rST `::` indented blocks render as plain, unhighlighted text with no copy button or annotations, resulting in a noticeably worse reading experience on your documentation site. The `::` literal may even render as visible text.

{{ rule_fix() }}

## Examples

### Doctest `>>>` format

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

### rST `::` indented block

=== "Violation"

    ```python
    """Module for data processing.

    Examples:
        Run the processing pipeline::

            $ docvet check --all
    """
    ```

=== "Fix"

    ```python hl_lines="4 5 6 7"
    """Module for data processing.

    Examples:
        Run the processing pipeline:

        ```bash
        $ docvet check --all
        ```
    """
    ```
