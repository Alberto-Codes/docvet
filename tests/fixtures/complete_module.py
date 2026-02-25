"""Fixture: fully complete docstrings — no findings expected.

Examples:
    Used by the test suite to verify zero-finding output::

        source = Path("tests/fixtures/complete_module.py").read_text()

See Also:
    [`tests.fixtures`][]: Other test fixture modules.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass


def process(value: str) -> int:
    """Process a value and return its length.

    Args:
        value: The string to process.

    Returns:
        The length of the string.

    Raises:
        ValueError: If the value is empty.

    Examples:
        ```python
        result = process("hello")
        assert result == 5
        ```

    See Also:
        [`generate_numbers`][]
    """
    if not value:
        raise ValueError("Value cannot be empty")
    return len(value)


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid (bool): Whether the validation passed.
        message (str): Human-readable description of the result.
        error_count (int): Number of errors found during validation.

    Examples:
        ```python
        result = ValidationResult(is_valid=True, message="OK")
        ```

    See Also:
        [`Connection`][]
    """

    is_valid: bool
    message: str
    error_count: int = 0


class Connection:
    """A database connection wrapper.

    Attributes:
        host (str): The database host address.
        port (int): The port number for the connection.

    Examples:
        ```python
        conn = Connection("localhost", 5432)
        ```

    See Also:
        [`ValidationResult`][]
    """

    def __init__(self, host: str, port: int = 5432):
        """Initialize the connection.

        Args:
            host: The database host address.
            port: The port number for the connection.
        """
        self.host = host
        self.port = port


def generate_numbers(n: int) -> Generator[int, None, None]:
    """Generate numbers from 0 to n-1.

    Args:
        n: Upper bound (exclusive).

    Yields:
        Integers from 0 to n-1.

    Examples:
        ```python
        list(generate_numbers(3))  # [0, 1, 2]
        ```

    See Also:
        [`process`][]
    """
    for i in range(n):
        yield i
