# `stale-drift`

{{ rule_header() }}

## What it detects

This rule flags symbols where the code was modified more recently than the docstring by more than `drift-threshold` days (default: 30). It uses `git blame` timestamps to compare when code lines and docstring lines were last touched.

## Why is this a problem?

A growing gap between code modification dates and docstring dates is a signal to review the docstring for potential staleness. Git blame timestamps show when lines were last touched; they do not establish whether the prose is semantically accurate. Code changes may preserve the documented contract, so even a large timestamp gap does not prove that the documentation is outdated. Review the changes against the docstring before deciding whether it needs an update.

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
