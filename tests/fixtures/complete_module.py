"""Fixture: fully complete docstrings — no findings expected."""

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
    """
    if not value:
        raise ValueError("Value cannot be empty")
    return len(value)


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether the validation passed.
        message: Human-readable description of the result.
        error_count: Number of errors found during validation.

    Examples:
        ```python
        result = ValidationResult(is_valid=True, message="OK")
        ```
    """

    is_valid: bool
    message: str
    error_count: int = 0


class Connection:
    """A database connection wrapper.

    Attributes:
        host: The database host address.
        port: The port number for the connection.

    Examples:
        ```python
        conn = Connection("localhost", 5432)
        ```
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
    """
    for i in range(n):
        yield i
