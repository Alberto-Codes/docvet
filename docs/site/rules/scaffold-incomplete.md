# `scaffold-incomplete`

{{ rule_header() }}

## What it detects

This rule flags docstrings containing unfilled placeholder markers (`[TODO: ...]`) left by `docvet fix`. When the scaffolding engine inserts missing sections, it uses `[TODO: describe]` placeholders that must be replaced with real descriptions before the code is merged.

## Why is this a problem?

Scaffold placeholders are meant to be temporary — they mark sections that need human-authored content. Leaving `[TODO: describe]` markers in production code means the docstring is technically present but still incomplete. This rule ensures scaffolded sections are filled in before CI passes.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def validate(data):
        """Validate input data.

        Args:
            data: The input.

        Raises:
            ValueError: [TODO: describe when this is raised]
        """
        if not data:
            raise ValueError("empty")
    ```

=== "Fix"

    ```python
    def validate(data):
        """Validate input data.

        Args:
            data: The input.

        Raises:
            ValueError: When the input data is empty or None.
        """
        if not data:
            raise ValueError("empty")
    ```

## Finding category

Scaffold-incomplete findings use the **scaffold** category (mapped to medium severity in JSON output, displayed in cyan in terminal output). When `enrichment` is in your `fail-on` list, scaffold findings trigger a non-zero exit code.

## Configuration

```toml
[tool.docvet.enrichment]
scaffold-incomplete = false  # default: true
```
