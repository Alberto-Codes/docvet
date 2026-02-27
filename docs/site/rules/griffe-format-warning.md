# `griffe-format-warning`

{{ rule_header() }}

## What it detects

This rule flags docstrings with formatting issues caught by griffe's parser that would break rendering in mkdocs documentation sites. This includes malformed section headers, incorrect indentation, and other structural problems.

## Why is this a problem?

Formatting issues cause griffe parser warnings during `mkdocs build`, and the resulting documentation renders incorrectly or incompletely. Visitors to your docs site see broken layouts, missing sections, or garbled text instead of clean API documentation.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def transform(data: list[dict]) -> list[dict]:
        """Transform input data.

        Args:
        data: The input data to transform.

        Returns:
            Transformed data.
        """
        ...
    ```

=== "Fix"

    ```python hl_lines="5"
    def transform(data: list[dict]) -> list[dict]:
        """Transform input data.

        Args:
            data: The input data to transform.

        Returns:
            Transformed data.
        """
        ...
    ```
