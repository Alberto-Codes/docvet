# `stale-drift`

{{ rule_header() }}

## What it detects

This rule flags symbols where the code was modified more recently than the docstring by more than `drift-threshold` days (default: 30). It uses `git blame` timestamps to compare when code lines and docstring lines were last touched.

## Why is this a problem?

A growing gap between code modification dates and docstring dates means the documentation is gradually falling behind. Even if no single change was large enough to trigger a diff-mode finding, the cumulative drift means the docstring may now describe outdated behavior. Catching drift early prevents documentation from becoming unreliable over time.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    # Code last modified: 2026-01-15
    # Docstring last modified: 2025-11-02 (74 days drift)
    def calculate_score(items: list[Item]) -> float:
        """Calculate the aggregate score for items.

        Args:
            items: List of items to score.

        Returns:
            Aggregate score as a float.
        """
        # Logic changed multiple times since docstring was written
        weights = load_weights()
        return sum(w * i.value for w, i in zip(weights, items))
    ```

=== "Fix"

    ```python hl_lines="2 4 5 11"
    def calculate_score(items: list[Item]) -> float:
        """Calculate the weighted aggregate score for items.

        Uses dynamically loaded weights to compute a weighted sum
        of item values.

        Args:
            items: List of items to score.

        Returns:
            Weighted aggregate score as a float.
        """
        weights = load_weights()
        return sum(w * i.value for w, i in zip(weights, items))
    ```
