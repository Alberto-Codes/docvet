"""Fixture: function raises but docstring has no Raises section."""

from __future__ import annotations


def validate_input(value: str) -> str:
    """Validate the input string.

    Args:
        value: The string to validate.

    Returns:
        The validated string.
    """
    if not value:
        raise ValueError("Value cannot be empty")
    return value
