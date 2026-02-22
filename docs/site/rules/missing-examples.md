# `missing-examples`

{{ rule_header() }}

## What it detects

This rule flags symbols whose kind appears in the `require-examples` configuration list (default: `class`, `protocol`, `dataclass`, `enum`) but whose docstring has no `Examples:` section.

## Why is this a problem?

Complex types without usage examples force users to reverse-engineer behavior from source code. An `Examples:` section showing instantiation and basic usage is often the fastest way for someone to understand how to use a class, dataclass, or enum correctly.

## Example

=== "Violation"

    ```python
    @dataclass
    class Coordinate:
        """A geographic coordinate.

        Attributes:
            latitude (float): Latitude in decimal degrees.
            longitude (float): Longitude in decimal degrees.
        """

        latitude: float
        longitude: float
    ```

=== "Fix"

    ```python hl_lines="9 10 11 12 13"
    @dataclass
    class Coordinate:
        """A geographic coordinate.

        Attributes:
            latitude (float): Latitude in decimal degrees.
            longitude (float): Longitude in decimal degrees.

        Examples:
            ```python
            coord = Coordinate(latitude=40.7128, longitude=-74.0060)
            print(coord.latitude)  # 40.7128
            ```
        """

        latitude: float
        longitude: float
    ```
