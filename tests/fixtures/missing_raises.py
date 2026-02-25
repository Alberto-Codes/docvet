"""Fixture: function raises but docstring has no Raises section.

Examples:
    Used by the test suite to verify missing-raises detection::

        source = Path("tests/fixtures/missing_raises.py").read_text()

See Also:
    [`tests.fixtures`][]: Other test fixture modules.
"""

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
