# `missing-receives`

{{ rule_header() }}

## What it detects

This rule flags generator functions that use the send pattern (`value = yield`) but have no `Receives:` section in their docstring.

## Why is this a problem?

Callers using `.send()` on the generator don't know what values it accepts. Without a `Receives:` section, the two-way communication contract is undocumented, making the generator error-prone to use. This is especially problematic for coroutine-style generators where the sent value drives behavior.

{{ rule_fix() }}

## Example

=== "Violation"

    ```python
    def accumulator() -> Generator[float, float, None]:
        """Accumulate values and yield running totals.

        Yields:
            Running total after each value.
        """
        total = 0.0
        while True:
            value = yield total
            total += value
    ```

=== "Fix"

    ```python hl_lines="7 8"
    def accumulator() -> Generator[float, float, None]:
        """Accumulate values and yield running totals.

        Yields:
            Running total after each value.

        Receives:
            Numeric value to add to the running total.
        """
        total = 0.0
        while True:
            value = yield total
            total += value
    ```
