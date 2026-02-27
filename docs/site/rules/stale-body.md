# `stale-body`

{{ rule_header() }}

## What it detects

This rule flags functions whose body was changed in a git diff but whose docstring was not updated in the same diff. This is a medium-severity freshness finding.

## Why is this a problem?

A changed function body means the behavior may have changed — new branches, different return values, or altered side effects. The docstring may now describe outdated behavior, leading to confusion for anyone relying on the documentation to understand what the function does.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    # Body changed to add validation, but docstring still says
    # it returns None on failure (it now raises instead):
    def process_item(item: dict) -> Result:
        """Process a single item.

        Args:
            item: Item data to process.

        Returns:
            Processing result. Returns None if item is invalid.
        """
        if not item.get("id"):
            raise ValueError("Item must have an id")
        return Result(status="ok", data=transform(item))
    ```

=== "Fix"

    ```python hl_lines="7 8 10 11"
    def process_item(item: dict) -> Result:
        """Process a single item.

        Args:
            item: Item data to process.

        Returns:
            Processing result.

        Raises:
            ValueError: If the item has no id field.
        """
        if not item.get("id"):
            raise ValueError("Item must have an id")
        return Result(status="ok", data=transform(item))
    ```
